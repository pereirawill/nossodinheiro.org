"""
Inflação — IPCA desde 1979, por grupo de gasto e por região, com a meta do Banco Central.

    python -m etl.inflacao.extract            # gera data/public/inflacao.json

Fontes (sem chave):
- IBGE, SIDRA tabela 1737 (IPCA, série histórica): número-índice (base dez/1993 = 100), variação mensal, acumulada no ano e
  acumulada em 12 meses, de dezembro de 1979 ao último mês publicado.
- IBGE, SIDRA tabela 7060 (IPCA por grupo, subgrupo, item e subitem), desde janeiro de 2020: usamos os 9 grupos
  (alimentação, habitação, artigos de residência, vestuário, transportes, saúde, despesas pessoais, educação, comunicação),
  com variação no mês, acumulada no ano, em 12 meses e o peso de cada grupo na cesta.
- IBGE, SIDRA tabela 7060 por região: 10 regiões metropolitanas (nível N7) e 6 municípios (N6) que compõem o IPCA.
- IBGE, SIDRA tabelas 655, 2938, 1419 e 7060 (IPCA por grupo e por item): a variação mensal de cada grupo e de onze itens
  do dia a dia, encadeada de agosto de 1999 em diante. As quatro tabelas se sucedem sem se sobrepor — cada uma vale enquanto
  vale a estrutura de pesos de uma POF —, e o que encadeamos é a VARIAÇÃO medida em cada período, não números-índice de
  pesquisas diferentes. O código interno do SIDRA muda entre as tabelas; o código do IBGE, que vem no rótulo
  ("1112015.Pão francês"), é estável, e é por ele que a cadeia é montada.
- IBGE, SIDRA tabela 7063 (INPC), o índice geral e o peso de cada grupo, para comparar a cesta de quem ganha até 5 salários
  mínimos com a do IPCA (1 a 40).
- Banco Central, SGS série 13521: meta de inflação definida pelo Conselho Monetário Nacional para cada ano.

O IPCA mede a variação de preços para famílias com renda de 1 a 40 salários mínimos nas 16 áreas pesquisadas; o INPC, de 1 a 5
salários mínimos. Nenhum dos dois é "a inflação de uma pessoa": cada família tem sua própria cesta.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx

log = logging.getLogger("etl.inflacao")
PUB = Path("data/public")
SIDRA = "https://apisidra.ibge.gov.br/values/t/{t}/{n}/all/v/{v}/p/{p}{c}?formato=json"
SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{s}/dados?formato=json&dataInicial=01/01/1999"
UA = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
# Grupos do IPCA na classificação 315 da tabela 7060 (nível 1). Fixos para não depender da API de metadados do IBGE,
# que deu timeout a partir dos runners do GitHub; conferir em /api/v3/agregados/7060/metadados quando o IBGE mudar a cesta.
GRUPOS = {7170: "Alimentação e bebidas", 7445: "Habitação", 7486: "Artigos de residência", 7558: "Vestuário",
          7625: "Transportes", 7660: "Saúde e cuidados pessoais", 7712: "Despesas pessoais", 7766: "Educação", 7786: "Comunicação"}
VAR = {"mes": 63, "ano": 69, "doze": 2265, "indice": 2266, "peso": 66}


def _num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def sidra(cli: httpx.Client, **kw) -> list[dict]:
    url = SIDRA.format(**{"n": "n1", "p": "all", "c": "", **kw})
    erro = None
    for tentativa in range(3):
        try:
            r = cli.get(url); r.raise_for_status()
            return r.json()[1:]
        except (httpx.TransportError, httpx.HTTPStatusError, ValueError) as e:
            erro = e; log.warning("SIDRA tentativa %d (t%s): %s", tentativa + 1, kw.get("t"), e)
    raise erro


def serie_historica(c: httpx.Client) -> dict:
    """IPCA mês a mês desde dez/1979: índice e variação em 12 meses; e o acumulado de cada ano fechado."""
    indice = {r["D3C"]: _num(r["V"]) for r in sidra(c, t=1737, v=VAR["indice"]) if _num(r["V"]) is not None}
    doze = {r["D3C"]: _num(r["V"]) for r in sidra(c, t=1737, v=VAR["doze"]) if _num(r["V"]) is not None}
    mes = {r["D3C"]: _num(r["V"]) for r in sidra(c, t=1737, v=VAR["mes"]) if _num(r["V"]) is not None}
    ano = {r["D3C"]: _num(r["V"]) for r in sidra(c, t=1737, v=VAR["ano"]) if _num(r["V"]) is not None}
    ultimo = max(indice)
    anual = {p[:4]: v for p, v in sorted(ano.items()) if p.endswith("12")}      # dezembro = acumulado do ano fechado
    if not ultimo.endswith("12"):
        anual[ultimo[:4]] = ano.get(ultimo)                                     # ano corrente: parcial
    return {"ultimo_mes": ultimo, "indice": indice, "doze_meses": doze, "mensal": mes, "anual": anual,
            "parcial_ano_corrente": not ultimo.endswith("12")}


def grupos(c: httpx.Client) -> list[dict]:
    codigos = ",".join(str(k) for k in GRUPOS)
    out: dict[int, dict] = {}
    for chave, v in (("mes", VAR["mes"]), ("ano", VAR["ano"]), ("doze", VAR["doze"]), ("peso", VAR["peso"])):
        for r in sidra(c, t=7060, v=v, p="last 1", c=f"/c315/{codigos}"):
            cod = int(r["D4C"])
            out.setdefault(cod, {"codigo": cod, "nome": GRUPOS[cod]})[chave] = _num(r["V"])
            out[cod]["mes_referencia"] = r["D3C"]
    return [out[k] for k in GRUPOS if k in out]


def regioes(c: httpx.Client) -> list[dict]:
    out: dict[str, dict] = {}
    for nivel in ("n7", "n6"):
        for chave, v in (("ano", VAR["ano"]), ("doze", VAR["doze"])):
            for r in sidra(c, t=7060, n=nivel, v=v, p="last 1", c="/c315/7169"):
                d = out.setdefault(r["D1C"], {"codigo": r["D1C"], "nome": r["D1N"], "tipo": "região metropolitana" if nivel == "n7" else "município"})
                d[chave] = _num(r["V"])
    return sorted(out.values(), key=lambda d: -(d.get("doze") or 0))


def meta_bcb(c: httpx.Client) -> dict:
    r = c.get(SGS.format(s=13521)); r.raise_for_status()
    return {x["data"][-4:]: float(x["valor"]) for x in r.json()}


# ---------------------------------------------------------------------------
# Série longa por grupo e por item, e o peso de cada grupo nas duas cestas.
#
# O IBGE publica a variação mensal por grupo/item em tabelas que se sucedem sem se sobrepor — cada uma vale
# enquanto vale a estrutura de pesos de uma POF. Encadear a VARIAÇÃO de um mesmo item entre elas é legítimo
# (é a variação medida em cada período), diferente de emendar números-índice de pesquisas diferentes. O que
# muda entre as tabelas é o código interno do SIDRA; o código do IBGE, que vem no começo do rótulo
# ("1112015.Pão francês"), é estável — e é por ele que a cadeia é montada.
CADEIA = [(655, "199908-200606"), (2938, "200607-201112"), (1419, "201201-201912"), (7060, "202001-{fim}")]
# grupos (código do IBGE de um dígito) e os itens do dia a dia que a página mostra
GRUPOS_IBGE = {"1": "Alimentação e bebidas", "2": "Habitação", "3": "Artigos de residência", "4": "Vestuário",
               "5": "Transportes", "6": "Saúde e cuidados pessoais", "7": "Despesas pessoais",
               "8": "Educação", "9": "Comunicação"}
ITENS_IBGE = {"1112015": "Pão francês", "1101002": "Arroz", "1101073": "Feijão (carioca)",
              "1111004": "Leite longa vida", "1110044": "Ovo de galinha", "1201001": "Refeição fora de casa",
              "2101001": "Aluguel residencial", "2202003": "Energia elétrica", "5104001": "Gasolina",
              "5102001": "Automóvel novo", "6203001": "Plano de saúde"}
GERAL_IBGE = "0"   # o rótulo do índice geral não tem prefixo numérico; tratado à parte


def _rotulo(nome: str) -> tuple[str, str]:
    """'1112015.Pão francês' → ('1112015', 'Pão francês'); 'Índice geral' → ('0', 'Índice geral')."""
    m = re.match(r"\s*(\d+)\.\s*(.+)", nome or "")
    return (m.group(1), m.group(2).strip()) if m else (GERAL_IBGE, (nome or "").strip())


def _codigos_da_tabela(c: httpx.Client, tabela: int, mes: str) -> dict[str, str]:
    """Mapa código do IBGE → código do SIDRA, lido de um mês qualquer da tabela."""
    linhas = sidra(c, t=tabela, v="63", p=mes, c="/c315/all")
    saida = {}
    for l in linhas:
        cod_sidra = l.get("D4C")
        ibge, _ = _rotulo(l.get("D4N") or "")
        if cod_sidra and ibge not in saida:
            saida[ibge] = str(cod_sidra)
    return saida


def grupos_e_itens(c: httpx.Client, ultimo: str) -> dict:
    """Número-índice por grupo e por item, encadeando a variação mensal das quatro tabelas."""
    desejados = {GERAL_IBGE, *GRUPOS_IBGE, *ITENS_IBGE}
    variacoes: dict[str, dict[str, float]] = {}
    nomes: dict[str, str] = {}
    for tabela, periodo in CADEIA:
        periodo = periodo.format(fim=ultimo)
        mapa = _codigos_da_tabela(c, tabela, periodo.split("-")[0])
        codigos = sorted({mapa[k] for k in desejados if k in mapa})
        if not codigos:
            log.warning("tabela %s não trouxe nenhum dos códigos pedidos", tabela)
            continue
        for l in sidra(c, t=tabela, v="63", p=periodo, c="/c315/" + ",".join(codigos)):
            ibge, nome = _rotulo(l.get("D4N") or "")
            mes = str(l.get("D3C") or "")
            try:
                v = float(str(l.get("V")).replace(",", "."))
            except (TypeError, ValueError):
                continue
            if ibge in desejados and len(mes) == 6:
                variacoes.setdefault(ibge, {})[f"{mes[:4]}-{mes[4:]}"] = v
                nomes[ibge] = nome
    # da variação mensal para o número-índice, base 100 no primeiro mês de todos
    saida = {}
    for ibge, pontos in variacoes.items():
        meses = sorted(pontos)
        indice, valor = {}, 100.0
        for m in meses:
            valor *= 1 + pontos[m] / 100
            indice[m] = round(valor, 4)
        saida[ibge] = {"nome": nomes.get(ibge, ibge), "indice": indice,
                       "tipo": "geral" if ibge == GERAL_IBGE else ("grupo" if len(ibge) == 1 else "item")}
    return saida


def pesos(c: httpx.Client, ultimo: str) -> dict:
    """Peso de cada grupo nas duas cestas: IPCA (1 a 40 salários mínimos) e INPC (até 5)."""
    saida: dict[str, dict] = {}
    for cesta, (tabela, var) in (("ipca", (7060, "66")), ("inpc", (7063, "45"))):
        for l in sidra(c, t=tabela, v=var, p=ultimo, c="/c315/all"):
            ibge, nome = _rotulo(l.get("D4N") or "")
            if ibge not in GRUPOS_IBGE:
                continue
            try:
                saida.setdefault(ibge, {"nome": nome})[cesta] = float(str(l.get("V")).replace(",", "."))
            except (TypeError, ValueError):
                continue
    return saida


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers=UA, timeout=240, follow_redirects=True) as c:
        hist = serie_historica(c)
        g = grupos(c)
        reg = regioes(c)
        inpc = {r["D3C"]: _num(r["V"]) for r in sidra(c, t=7063, v=2292, p="last 13", c="/c315/7169") if _num(r["V"]) is not None}
        metas = meta_bcb(c)
        longo = grupos_e_itens(c, hist["ultimo_mes"].replace("-", ""))
        peso_cestas = pesos(c, hist["ultimo_mes"].replace("-", ""))
    dados = {"gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"), **hist,
             "grupos": g, "regioes": reg, "inpc_doze_meses": inpc, "meta_bcb": metas,
             "longo": longo, "pesos_cestas": peso_cestas,
             "fontes": {"ipca": "IBGE, IPCA (SIDRA 1737, série desde dez/1979; e 7060 por grupo e por região, desde jan/2020)",
                        "inpc": "IBGE, INPC (SIDRA 7063)",
                        "longo": "IBGE, variação mensal do IPCA por grupo e por item, encadeada das tabelas 655, "
                                 "2938, 1419 e 7060 do SIDRA (agosto de 1999 em diante)",
                        "pesos": "IBGE, peso de cada grupo na cesta do IPCA (SIDRA 7060) e do INPC (SIDRA 7063)",
                        "meta": "Banco Central, SGS série 13521 — meta de inflação definida pelo Conselho Monetário Nacional"}}
    out = PUB / "inflacao.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    log.info("IPCA %s: %.2f%% em 12 meses, %.2f%% no ano; meta %s = %s%%; %d grupos; %d regiões; série com %d meses",
             hist["ultimo_mes"], hist["doze_meses"][hist["ultimo_mes"]], hist["anual"][hist["ultimo_mes"][:4]],
             hist["ultimo_mes"][:4], metas.get(hist["ultimo_mes"][:4]), len(g), len(reg), len(hist["indice"]))
    log.info("série longa: %d grupos e itens desde ago/1999; pesos de %d grupos nas duas cestas", len(longo), len(peso_cestas))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
