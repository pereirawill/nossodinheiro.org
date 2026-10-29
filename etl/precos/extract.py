"""
Preços e tempo de trabalho — quanto custa, em minutos de trabalho, o que a família compra todo mês; e como o
nível de preços do Brasil se compara com o de outros países, categoria por categoria.

    python -m etl.precos.extract            # gera data/public/precos.json

Quatro fontes, todas públicas e sem chave:

- **ANP, Sistema de Levantamento de Preços (SLP)** — preço médio de revenda, média mensal, de duas planilhas
  oficiais que não se sobrepõem: `mensal-brasil-2001-a-2012.xlsx` (jul/2001 a dez/2012) e
  `mensal-brasil-desde-jan2013.xlsx` (jan/2013 em diante), mais `mensal-estados-desde-jan2013.xlsx` para o
  recorte por estado. São vintages diferentes do mesmo relatório, com a mesma definição de coluna, e os períodos
  são contíguos — por isso a série é uma só, sem emenda de metodologia.
- **Banco Central, SGS série 1619** — salário mínimo mensal, de julho de 1994 (Plano Real) em diante. É valor de lei, exato para cada
  mês, e por isso serve de denominador para a série longa: a hora no salário mínimo é o salário dividido por
  **220 horas**, o divisor mensal da jornada de 44 horas semanais (CLT, art. 58 e 64).
- **IBGE, PNAD Contínua trimestral** — rendimento médio habitual de todos os trabalhos (tabela **5436**,
  variável 5933) e média de horas habitualmente trabalhadas em todos os trabalhos (tabela **6371**, variável
  8190). Mesmo universo nas duas, então a divisão dá a hora do trabalhador médio. O rendimento dessa tabela é
  **real, a preços do último trimestre** — por isso ele só é usado no retrato atual, nunca na série longa.
- **IBGE, números-índice do IPCA (SIDRA 1737) e do INPC (SIDRA 1736)** — servem para a conferência cruzada: o IPCA
  mede a cesta de quem ganha de 1 a 40 salários mínimos e o INPC a de quem ganha até 5. Se as duas cestas dão a mesma
  resposta sobre o salário mínimo, a resposta não depende de qual cesta se escolhe.
- **Banco Mundial, International Comparison Program (ICP) 2021** — índice de nível de preços por categoria de
  consumo (classificação `PX.WL`, mundo = 100), ano de referência **2021**, publicado em 2024. É a única fonte
  pública que compara o preço de categorias de produto entre países com a mesma cesta. O ICP 2017 publica os
  mesmos anos com outro vintage e números um pouco diferentes: não juntamos as rodadas.

O que este painel **não** faz: afirmar causa. Ele publica o preço, o tempo de trabalho e a composição da carga
tributária lado a lado; não escreve que o imposto explica a diferença.
"""

from __future__ import annotations

import io
import json
import logging
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import httpx
import openpyxl

from etl.ufs import NOME_PARA_UF, normalizar

log = logging.getLogger("etl.precos")
PUB = Path("data/public")
RAW = Path("data/raw")
UA = {"User-Agent": "Mozilla/5.0 (compatible; nossodinheiro-etl/0.1; +https://nossodinheiro.org)"}

ANP = ("https://www.gov.br/anp/pt-br/assuntos/precos-e-defesa-da-concorrencia/precos/"
       "precos-revenda-e-de-distribuicao-combustiveis/shlp/")
PLANILHAS = {
    "brasil_2001_2012": ANP + "2001-2012/mensal-brasil-2001-a-2012.xlsx",
    "brasil_2013": ANP + "mensal/mensal-brasil-desde-jan2013.xlsx",
    "estados_2013": ANP + "mensal/mensal-estados-desde-jan2013.xlsx",
}
# Nomes do produto na planilha → chave nossa. A grafia muda entre as duas planilhas ("ÓLEO DIESEL" × "OLEO
# DIESEL"), então o casamento é feito sem acento. A gasolina aditivada só existe a partir de 2013 e fica fora:
# a série comparável é a da gasolina comum.
PRODUTOS = {
    "GASOLINACOMUM": ("gasolina", "Gasolina comum"),
    "ETANOLHIDRATADO": ("etanol", "Etanol"),
    "OLEODIESEL": ("diesel", "Óleo diesel"),
    "OLEODIESELS10": ("diesel_s10", "Óleo diesel S10"),
    "GLP": ("glp", "Gás de cozinha (botijão de 13 kg)"),
    "GNV": ("gnv", "Gás natural veicular"),
}
HORAS_MES = 220  # divisor mensal da jornada de 44 h semanais (CLT, art. 58 e 64)
SEMANAS_MES = 4.345  # 52 semanas ÷ 12 meses

SGS_SM = ("https://api.bcb.gov.br/dados/serie/bcdata.sgs.1619/dados?formato=json"
          "&dataInicial=01/07/1994&dataFinal=31/12/{ate}")
SIDRA = "https://apisidra.ibge.gov.br/values/t/{t}/n{n}/all/v/{v}/p/{p}?formato=json"
# números-índice para a conferência cruzada: IPCA (cesta de 1 a 40 s.m.) e INPC (até 5 s.m.)
INDICES = {"ipca": (1737, "2266"), "inpc": (1736, "2289")}

WB = "https://api.worldbank.org/v2"
ICP_FONTE = 90  # ICP 2021
ICP_ANO = "YR2021"
# A lista de países é a mesma declarada em /comparacao/: vizinhos, ricos de referência e os grandes emergentes.
REF = ["BRA", "ARG", "CHL", "COL", "MEX", "URY", "USA", "CAN", "GBR", "FRA", "DEU", "ITA", "ESP", "PRT",
       "SWE", "JPN", "KOR", "CHN", "IND", "ZAF", "AUS"]
# Categorias do ICP (código da classificação de despesa) e o nome que usamos na página.
CATEGORIAS = [
    ("1000000", "Economia inteira (PIB)"),
    ("9020000", "Tudo que a família consome"),
    ("1101100", "Comida"),
    ("1102100", "Bebida alcoólica"),
    ("1103000", "Roupa e calçado"),
    ("1105000", "Móvel e eletrodoméstico"),
    ("9060000", "Moradia, água, luz e gás"),
    ("9080000", "Saúde"),
    ("1107100", "Compra de veículo"),
    ("1107300", "Transporte (passagem)"),
    ("1108000", "Telefone e internet"),
    ("9110000", "Lazer e cultura (TV, celular, computador)"),
    ("9120000", "Educação"),
    ("1111000", "Restaurante e hotel"),
    ("1501100", "Máquina e equipamento"),
    ("1501200", "Construção"),
]
CLASSIFICACOES = {
    "nivel_precos": "PX.WL",           # índice de nível de preços, mundo = 100
    "consumo_por_pessoa": "PCAP.CD.IX.US",  # despesa por habitante, câmbio de mercado, EUA = 100
}


def _sem_acento(s: str) -> str:
    return unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode()


def _planilha(c: httpx.Client, chave: str) -> bytes:
    """Baixa (e guarda em data/raw) uma planilha do SLP da ANP."""
    RAW.mkdir(parents=True, exist_ok=True)
    destino = RAW / f"anp_{chave}.xlsx"
    r = c.get(PLANILHAS[chave], headers=UA)
    if r.status_code == 200 and len(r.content) > 20_000:
        destino.write_bytes(r.content)
        return r.content
    if destino.exists():
        log.warning("ANP %s respondeu HTTP %s — usando o arquivo em cache", chave, r.status_code)
        return destino.read_bytes()
    raise SystemExit(f"ANP {chave}: HTTP {r.status_code} e sem cache em {destino}")


def _tabela(conteudo: bytes) -> tuple[list[str], list[tuple], list[str]]:
    """Cabeçalho, linhas de dado e as observações que a ANP escreve acima do cabeçalho."""
    ws = openpyxl.load_workbook(io.BytesIO(conteudo), read_only=True, data_only=True).worksheets[0]
    linhas = list(ws.iter_rows(values_only=True))
    pos = next((i for i, l in enumerate(linhas) if l and str(l[0] or "").strip().upper() == "MÊS"), None)
    if pos is None:
        raise SystemExit("planilha da ANP sem a linha de cabeçalho 'MÊS' — o formato mudou")
    cab = [_sem_acento(str(v or "")).strip().upper() for v in linhas[pos]]
    notas = [str(l[0]).strip() for l in linhas[:pos]
             if l and l[0] and str(l[0]).startswith(("Obs", "Entre", "Não", "Os preços", "A partir", "Atualmente"))]
    return cab, [l for l in linhas[pos + 1:] if l and l[0]], notas


def _col(cab: list[str], *pedacos: str) -> int:
    for i, nome in enumerate(cab):
        if all(p in nome for p in pedacos):
            return i
    raise SystemExit(f"coluna {pedacos} não achada em {cab}")


def _mes(v) -> str | None:
    if isinstance(v, datetime):
        return f"{v.year:04d}-{v.month:02d}"
    return None


def combustiveis(c: httpx.Client) -> tuple[dict, list[str]]:
    """Preço médio de revenda por mês e produto, no Brasil, de jul/2001 ao último mês publicado."""
    serie: dict[str, dict[str, dict]] = {}
    notas: list[str] = []
    for chave in ("brasil_2001_2012", "brasil_2013"):
        cab, linhas, obs = _tabela(_planilha(c, chave))
        notas += [n for n in obs if n not in notas]
        i_prod, i_un = _col(cab, "PRODUTO"), _col(cab, "UNIDADE")
        i_preco, i_postos = _col(cab, "PRECO", "MEDIO", "REVENDA"), _col(cab, "POSTOS")
        for l in linhas:
            mes, prod = _mes(l[0]), PRODUTOS.get(normalizar(str(l[i_prod])))
            if not mes or not prod or not isinstance(l[i_preco], (int, float)):
                continue
            serie.setdefault(prod[0], {})[mes] = {
                "preco": round(float(l[i_preco]), 4),
                "unidade": str(l[i_un] or "").strip(),
                "postos": int(l[i_postos]) if isinstance(l[i_postos], (int, float)) else None,
            }
    return serie, notas


def combustiveis_ufs(c: httpx.Client, mes: str) -> dict[str, dict]:
    """Preço médio de revenda por estado, no mês pedido."""
    cab, linhas, _ = _tabela(_planilha(c, "estados_2013"))
    i_prod, i_uf = _col(cab, "PRODUTO"), _col(cab, "ESTADO")
    i_preco, i_un = _col(cab, "PRECO", "MEDIO", "REVENDA"), _col(cab, "UNIDADE")
    # os nomes de estado vêm sem acento na planilha ("AMAPA"), então o casamento é por nome normalizado
    por_nome = {normalizar(n): s for n, s in NOME_PARA_UF.items()}
    saida: dict[str, dict] = {}
    for l in linhas:
        if _mes(l[0]) != mes or not isinstance(l[i_preco], (int, float)):
            continue
        prod = PRODUTOS.get(normalizar(str(l[i_prod])))
        uf = por_nome.get(normalizar(str(l[i_uf])))
        if prod and uf:
            saida.setdefault(uf, {})[prod[0]] = {"preco": round(float(l[i_preco]), 4),
                                                 "unidade": str(l[i_un] or "").strip()}
    return saida


def salario_minimo(c: httpx.Client) -> dict[str, float]:
    """Salário mínimo mensal, da série 1619 do SGS."""
    r = c.get(SGS_SM.format(ate=datetime.now().year), headers=UA)
    if r.status_code != 200 or "json" not in (r.headers.get("content-type") or ""):
        raise SystemExit(f"SGS 1619 (salário mínimo): HTTP {r.status_code}")
    saida = {}
    for x in r.json():
        d, m, a = x["data"].split("/")
        saida[f"{a}-{m}"] = float(x["valor"])
    return saida


def _sidra(c: httpx.Client, t: int, v: str, p: str, n: int = 1) -> list[dict]:
    r = c.get(SIDRA.format(t=t, v=v, p=p, n=n))
    if r.status_code != 200:
        log.warning("SIDRA t%s v%s n%s: HTTP %s", t, v, n, r.status_code)
        return []
    d = r.json()
    return [{d[0][k]: l[k] for k in l} for l in d[1:]] if len(d) > 1 else []


def _valor(linha: dict) -> float | None:
    try:
        return float(str(linha.get("Valor")).replace(",", "."))
    except (TypeError, ValueError):
        return None


def rendimento(c: httpx.Client) -> dict:
    """Rendimento habitual e horas habituais do trabalhador médio: Brasil por trimestre, estados no último."""
    brasil: dict[str, dict] = {}
    for chave, t, v in (("rendimento", 5436, "5933"), ("horas", 6371, "8190")):
        for l in _sidra(c, t, v, "all"):
            periodo = l.get("Trimestre (Código)") or l.get("Trimestre")
            val = _valor(l)
            if periodo and val is not None:
                brasil.setdefault(str(periodo), {})[chave] = val
    completos = {p: d for p, d in brasil.items() if {"rendimento", "horas"} <= set(d)}
    ultimo = max(completos) if completos else None
    ufs: dict[str, dict] = {}
    if ultimo:
        for chave, t, v in (("rendimento", 5436, "5933"), ("horas", 6371, "8190")):
            for l in _sidra(c, t, v, ultimo, n=3):
                uf = NOME_PARA_UF.get(str(l.get("Unidade da Federação") or "").strip())
                val = _valor(l)
                if uf and val is not None:
                    ufs.setdefault(uf, {})[chave] = val
    for d in list(completos.values()) + list(ufs.values()):
        if d.get("horas"):
            d["por_hora"] = round(d["rendimento"] / (d["horas"] * SEMANAS_MES), 4)
    return {"trimestre": ultimo, "brasil": dict(sorted(completos.items())), "ufs": ufs}


def indices_de_preco(c: httpx.Client) -> dict:
    """Números-índice do IPCA e do INPC, mês a mês. Servem para medir o salário mínimo nas duas cestas."""
    saida: dict[str, dict[str, float]] = {}
    for chave, (tabela, var) in INDICES.items():
        pontos = {}
        for l in _sidra(c, tabela, var, "all"):
            periodo = l.get("Mês (Código)") or l.get("Mês")
            try:
                valor = float(str(l.get("Valor")).replace(",", "."))
            except (TypeError, ValueError):
                continue
            if periodo and len(str(periodo)) == 6:
                pontos[f"{str(periodo)[:4]}-{str(periodo)[4:]}"] = valor
        if pontos:
            saida[chave] = dict(sorted(pontos.items()))
    return saida


def _icp(c: httpx.Client, classificacao: str) -> dict[tuple[str, str], float]:
    """Uma classificação do ICP 2021, para os países e categorias escolhidos, no ano de referência."""
    paises, series = ";".join(REF), ";".join(cod for cod, _ in CATEGORIAS)
    url = (f"{WB}/sources/{ICP_FONTE}/Country/{paises}/Series/{series}"
           f"/Classification/{classificacao}/Time/{ICP_ANO}/data")
    saida: dict[tuple[str, str], float] = {}
    pagina = 1
    while True:
        r = c.get(url, params={"format": "json", "per_page": "1000", "page": str(pagina)}, headers=UA)
        if r.status_code != 200:
            log.warning("ICP %s: HTTP %s", classificacao, r.status_code)
            break
        corpo = r.json()
        for x in corpo.get("source", {}).get("data", []):
            dim = {y["concept"]: y["id"] for y in x["variable"]}
            if x["value"] is not None:
                saida[(dim["Country"], dim["Series"])] = float(x["value"])
        if pagina >= int(corpo.get("pages") or 1):
            break
        pagina += 1
    return saida


def precos_internacionais(c: httpx.Client) -> dict:
    """Índice de nível de preços por categoria (mundo = 100) e consumo por habitante (EUA = 100)."""
    nivel = _icp(c, CLASSIFICACOES["nivel_precos"])
    consumo = _icp(c, CLASSIFICACOES["consumo_por_pessoa"])
    categorias = []
    for cod, nome in CATEGORIAS:
        linha = {"codigo": cod, "nome": nome,
                 "paises": {p: round(nivel[(p, cod)], 1) for p in REF if (p, cod) in nivel}}
        if linha["paises"]:
            categorias.append(linha)
    return {
        "ano": int(ICP_ANO[2:]), "rodada": "ICP 2021", "base": "mundo = 100",
        "categorias": categorias,
        "consumo_por_pessoa": {p: round(consumo[(p, "9020000")], 1) for p in REF if (p, "9020000") in consumo},
    }


def _wb_serie(c: httpx.Client, indicador: str) -> dict[str, dict[str, float]]:
    r = c.get(f"{WB}/country/{';'.join(REF)}/indicator/{indicador}",
              params={"format": "json", "per_page": "20000", "mrv": "30"}, headers=UA)
    d = r.json()
    if not isinstance(d, list) or len(d) < 2:
        log.warning("Banco Mundial %s não respondeu série", indicador)
        return {}
    saida: dict[str, dict[str, float]] = {}
    for x in d[1]:
        if x["value"] is not None:
            saida.setdefault(x["countryiso3code"] or x["country"]["id"], {})[x["date"]] = float(x["value"])
    return saida


def nivel_de_precos(c: httpx.Client) -> dict:
    """Nível geral de preços de cada país em relação aos EUA, pela razão entre PPP e câmbio de mercado."""
    ppp, cambio = _wb_serie(c, "PA.NUS.PPP"), _wb_serie(c, "PA.NUS.FCRF")
    saida: dict[str, dict[str, float]] = {}
    for pais, serie in ppp.items():
        for ano, v in serie.items():
            taxa = (cambio.get(pais) or {}).get(ano)
            if taxa:
                saida.setdefault(pais, {})[ano] = round(100 * v / taxa, 1)
    # os EUA são a base por construção (PPP = câmbio = 1), então a razão vira 100
    return saida


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=300, follow_redirects=True) as c:
        serie, notas = combustiveis(c)
        sm = salario_minimo(c)
        ultimo_mes = max(serie["gasolina"])
        ufs = combustiveis_ufs(c, ultimo_mes)
        trabalho = rendimento(c)
        internacional = precos_internacionais(c)
        nivel = nivel_de_precos(c)
        indices = indices_de_preco(c)

    if "gasolina" not in serie or len(serie["gasolina"]) < 200:
        raise SystemExit("série da gasolina veio curta — a planilha da ANP mudou?")
    if not ufs:
        raise SystemExit(f"nenhum estado com preço em {ultimo_mes} na planilha de estados da ANP")

    # minutos de trabalho por unidade, no salário mínimo do próprio mês (220 h por mês)
    combustiveis_saida = {}
    for prod_chave, nome in PRODUTOS.values():
        pontos = serie.get(prod_chave) or {}
        if not pontos:
            continue
        linhas = []
        for mes in sorted(pontos):
            d = dict(pontos[mes])
            hora = (sm.get(mes) or 0) / HORAS_MES
            d["mes"] = mes
            d["minutos_sm"] = round(60 * d["preco"] / hora, 1) if hora else None
            linhas.append(d)
        combustiveis_saida[prod_chave] = {"nome": nome, "unidade": linhas[-1]["unidade"], "serie": linhas}

    hora_media = (trabalho["brasil"].get(trabalho["trimestre"]) or {}).get("por_hora")
    for uf, d in ufs.items():
        hora_uf = (trabalho["ufs"].get(uf) or {}).get("por_hora")
        for prod, v in d.items():
            v["minutos_sm"] = round(60 * v["preco"] / (sm.get(ultimo_mes, 0) / HORAS_MES), 1) if sm.get(ultimo_mes) else None
            v["minutos_medio"] = round(60 * v["preco"] / hora_uf, 1) if hora_uf else None

    dados = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "mes": ultimo_mes,
        "combustiveis": combustiveis_saida,
        "ufs": ufs,
        "salario_minimo": dict(sorted(sm.items())),
        "horas_mes": HORAS_MES,
        "trabalho": trabalho,
        "hora_media": hora_media,
        "internacional": internacional,
        "nivel_precos": nivel,
        "indices": indices,
        "notas_anp": notas,
        "fontes": {
            "combustiveis": "ANP, Sistema de Levantamento de Preços — preço médio de revenda, média mensal "
                            "(planilhas mensal-brasil-2001-a-2012, mensal-brasil-desde-jan2013 e "
                            "mensal-estados-desde-jan2013)",
            "salario_minimo": "Banco Central, SGS série 1619 — salário mínimo mensal",
            "trabalho": "IBGE, PNAD Contínua trimestral: rendimento médio habitual de todos os trabalhos "
                        "(tabela 5436, variável 5933) e horas habitualmente trabalhadas em todos os trabalhos "
                        "(tabela 6371, variável 8190)",
            "internacional": "Banco Mundial, International Comparison Program (ICP) 2021 — índice de nível de "
                             "preços por categoria de despesa, ano de referência 2021 (mundo = 100)",
            "indices": "IBGE, número-índice do IPCA (SIDRA 1737) e do INPC (SIDRA 1736) — o INPC é a cesta de "
                       "quem ganha até 5 salários mínimos",
            "nivel_precos": "Banco Mundial, séries PA.NUS.PPP (fator de conversão de paridade) e PA.NUS.FCRF "
                            "(câmbio oficial); a razão entre as duas é o nível de preços em relação aos EUA",
        },
        "regras": [
            f"A hora no salário mínimo é o salário do mês dividido por {HORAS_MES} horas, o divisor mensal da "
            "jornada de 44 horas semanais (CLT, art. 58 e 64). É valor de lei, exato para cada mês.",
            "A hora do trabalhador médio é o rendimento habitual de todos os trabalhos dividido pelas horas "
            "habituais da mesma pesquisa. O rendimento da PNAD Contínua é real, a preços do último trimestre, "
            "então essa conta só vale para o retrato atual — a série longa usa o salário mínimo.",
            "O preço é o de revenda ao consumidor, média do mês, como a ANP publica. Não é o preço de um dia "
            "nem o de um posto.",
            "O ICP compara a mesma cesta entre países. O índice é de nível de preços, não de preço de um "
            "produto: diz se a categoria é cara ou barata no país, não quanto custa a geladeira.",
        ],
    }
    out = PUB / "precos.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    log.info("precos: %s produtos, %s–%s; %d estados em %s; ICP %s com %d categorias; hora média R$ %s",
             len(combustiveis_saida), min(combustiveis_saida["gasolina"]["serie"], key=lambda x: x["mes"])["mes"],
             ultimo_mes, len(ufs), ultimo_mes, internacional["ano"], len(internacional["categorias"]), hora_media)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
