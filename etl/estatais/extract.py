"""
Estatais — lucro ou prejuízo anual das empresas controladas pelo poder público que entregam demonstrações à CVM.

    python -m etl.estatais.extract            # gera data/public/estatais.json

Três fontes:

**A. CVM, dados abertos** — empresa por empresa, as três esferas, desde 2010:

1. **DFP** (Demonstrações Financeiras Padronizadas), `dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/`, um zip por
   ano. O arquivo `DRE_con` (consolidado) traz a última linha da demonstração do resultado — *Lucro ou Prejuízo
   Consolidado do Período* — e, abaixo, a parte dela atribuída aos sócios da controladora. Quem não publica
   consolidado (empresa sem controladas) entra pelo `DRE_ind`. O código dessa linha muda conforme o plano de contas
   (3.11 nas empresas não financeiras, 3.09 nos bancos até 2019), então ela é achada pela descrição e o código que
   vier fica gravado no JSON. Valores em milhares de reais (coluna ESCALA_MOEDA).

2. **FRE** (Formulário de Referência), `.../FRE/DADOS/`, arquivo `posicao_acionaria`. É daí que sai **quem controlava
   a empresa em cada ano** — em vez de cravarmos à mão a data de cada privatização. Só as linhas de posição direta
   contam (as de cadeia de controle vêm com `Acionista_Relacionado` preenchido). A empresa é tratada como estatal
   naquele ano quando um ente público aparece com **pelo menos 50% das ações ordinárias**, ou quando a própria
   companhia o marca como **acionista controlador** com pelo menos 20%. Controle indireto conta: se quem controla é
   outra estatal (Petrobras na antiga BR Distribuidora, Banco do Brasil na BB Seguridade, Caixa na Caixa Seguridade),
   a empresa é estatal — e nesse caso fica fora do agregado, porque o lucro dela já está dentro do consolidado da mãe.

**B. SEST (Ministério da Gestão)** — agregado das estatais **federais**, inclusive as fechadas (Caixa, Correios,
BNDES), desde 2016. Ver `etl/estatais/sest.py`.

**C. Tesouro Nacional (RTN)** — **dividendos** que a União recebeu das estatais, desde 1997. Ver
`etl/estatais/dividendos.py`.

Limites da parte da CVM, que estão escritos na página:
- **Só entra quem entrega DFP à CVM** — ou seja, quem tem ações em bolsa ou dívida registrada. Caixa, Correios,
  BNDES, Infraero, Serpro, Dataprev, Emgepron e as demais estatais fechadas não aparecem aqui.
- **A série começa em 2010**, primeiro ano do arquivo aberto da CVM. Não há como chegar a 1988 por esta fonte.
- **O conjunto de empresas muda de ano para ano** (o Metrô de São Paulo só passa a publicar em 2022, a Caixa
  Seguridade em 2015), então o agregado não é série comparável ano a ano — a página mostra quantas empresas entraram
  em cada ano.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import re
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

from . import dividendos, sest

log = logging.getLogger("etl.estatais")
PUB, RAW = Path("data/public"), Path("data/raw")
DFP = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_{ano}.zip"
FRE = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_{ano}.zip"
ANO_INICIAL = 2010
NIVEL_2 = re.compile(r"^3\.\d\d$")

# Empresas acompanhadas, por CNPJ (o nome muda — a Eletrobras virou Axia Energia em 2025 —, o CNPJ não). A lista saiu
# de uma varredura da posição acionária do FRE em busca de acionista que é ente público, conferida caso a caso; o que
# foi descartado e por quê está em docs/metodologia/painel-estatais.md. `dentro_de` = o lucro já está no consolidado
# daquela outra empresa da lista, então não soma no agregado. Em que ano cada uma era estatal NÃO está aqui: vem do FRE.
EMPRESAS = [
    {"cnpj": "33.000.167/0001-01", "nome": "Petrobras", "esfera": "federal", "setor": "Petróleo e gás"},
    {"cnpj": "00.000.000/0001-91", "nome": "Banco do Brasil", "esfera": "federal", "setor": "Banco"},
    {"cnpj": "07.237.373/0001-20", "nome": "Banco do Nordeste", "esfera": "federal", "setor": "Banco"},
    {"cnpj": "04.902.979/0001-44", "nome": "Banco da Amazônia", "esfera": "federal", "setor": "Banco"},
    {"cnpj": "17.344.597/0001-94", "nome": "BB Seguridade", "esfera": "federal", "setor": "Seguros",
     "dentro_de": "Banco do Brasil"},
    {"cnpj": "22.543.331/0001-00", "nome": "Caixa Seguridade", "esfera": "federal", "setor": "Seguros"},
    {"cnpj": "00.336.701/0001-04", "nome": "Telebras", "esfera": "federal", "setor": "Telecomunicações"},
    {"cnpj": "00.001.180/0001-26", "nome": "Eletrobras (hoje Axia Energia)", "esfera": "federal", "setor": "Energia"},
    {"cnpj": "34.274.233/0001-02", "nome": "BR Distribuidora (hoje Vibra)", "esfera": "federal",
     "setor": "Combustíveis", "dentro_de": "Petrobras"},
    {"cnpj": "92.702.067/0001-96", "nome": "Banrisul", "esfera": "estadual (RS)", "setor": "Banco"},
    {"cnpj": "28.127.603/0001-78", "nome": "Banestes", "esfera": "estadual (ES)", "setor": "Banco"},
    {"cnpj": "13.009.717/0001-46", "nome": "Banese", "esfera": "estadual (SE)", "setor": "Banco"},
    {"cnpj": "04.913.711/0001-08", "nome": "Banpará", "esfera": "estadual (PA)", "setor": "Banco"},
    {"cnpj": "17.155.730/0001-64", "nome": "Cemig", "esfera": "estadual (MG)", "setor": "Energia"},
    {"cnpj": "06.981.180/0001-16", "nome": "Cemig Distribuição", "esfera": "estadual (MG)", "setor": "Energia",
     "dentro_de": "Cemig"},
    {"cnpj": "06.981.176/0001-58", "nome": "Cemig Geração e Transmissão", "esfera": "estadual (MG)",
     "setor": "Energia", "dentro_de": "Cemig"},
    {"cnpj": "83.878.892/0001-55", "nome": "Celesc", "esfera": "estadual (SC)", "setor": "Energia"},
    {"cnpj": "76.483.817/0001-20", "nome": "Copel", "esfera": "estadual (PR)", "setor": "Energia"},
    {"cnpj": "00.070.698/0001-11", "nome": "CEB", "esfera": "estadual (DF)", "setor": "Energia"},
    {"cnpj": "60.933.603/0001-78", "nome": "Cesp", "esfera": "estadual (SP)", "setor": "Energia"},
    {"cnpj": "02.302.101/0001-42", "nome": "Emae", "esfera": "estadual (SP)", "setor": "Energia"},
    {"cnpj": "08.560.444/0001-93", "nome": "Celgpar", "esfera": "estadual (GO)", "setor": "Energia"},
    {"cnpj": "43.776.517/0001-80", "nome": "Sabesp", "esfera": "estadual (SP)", "setor": "Saneamento"},
    {"cnpj": "17.281.106/0001-03", "nome": "Copasa", "esfera": "estadual (MG)", "setor": "Saneamento"},
    {"cnpj": "76.484.013/0001-45", "nome": "Sanepar", "esfera": "estadual (PR)", "setor": "Saneamento"},
    {"cnpj": "82.508.433/0001-17", "nome": "Casan", "esfera": "estadual (SC)", "setor": "Saneamento"},
    {"cnpj": "01.616.929/0001-02", "nome": "Saneago", "esfera": "estadual (GO)", "setor": "Saneamento"},
    {"cnpj": "92.802.784/0001-90", "nome": "Corsan", "esfera": "estadual (RS)", "setor": "Saneamento"},
    {"cnpj": "07.040.108/0001-57", "nome": "Cagece", "esfera": "estadual (CE)", "setor": "Saneamento"},
    {"cnpj": "33.352.394/0001-04", "nome": "Cedae", "esfera": "estadual (RJ)", "setor": "Saneamento"},
    {"cnpj": "62.070.362/0001-06", "nome": "Metrô de São Paulo", "esfera": "estadual (SP)", "setor": "Transporte"},
    {"cnpj": "46.119.855/0001-37", "nome": "Sanasa (Campinas)", "esfera": "municipal", "setor": "Saneamento"},
    {"cnpj": "62.002.886/0001-60", "nome": "São Paulo Turismo", "esfera": "municipal", "setor": "Turismo e eventos"},
]
POR_CNPJ = {e["cnpj"]: e for e in EMPRESAS}

# Ente público como acionista, pelo nome que aparece na posição acionária. A linha precisa ter CNPJ brasileiro, para
# não confundir com governo estrangeiro ("Governo Francês", "Município de Medellin" também estão no arquivo).
ENTE_PUBLICO = re.compile(
    r"\buniao\b|uniao federal|tesouro nacional|ministerio da (fazenda|economia)|secretaria do tesouro"
    r"|\bestado d|\bgoverno d|fazenda d|secretaria d|distrito federal|prefeitura|municipio d"
)
# ...mas não é ente público quem só tem "do Estado de" no nome por ser empresa estadual: a Sabesp ("Cia de Saneamento
# Básico do Estado de São Paulo"), já privatizada, comprou a Emae em 2026 e passava por governo de São Paulo aqui.
NAO_E_ENTE = re.compile(r"\bs[\./]?a\b|\bltda\b|\bcia\b|companhia|participacoes|\bbanco\b|\bbco\b|\bfundo\b")
# Estatal sem ações em bolsa (por isso fora da lista de empresas) que controla empresa que está na lista.
CONTROLADORAS_PUBLICAS = {
    "00.360.305/0001-04": "Caixa Econômica Federal",
    "33.657.248/0001-89": "BNDES",
    "00.383.281/0001-09": "BNDES Participações (BNDESPar)",
}
PISO_ON = 50.0       # % de ações ordinárias de ente público que caracteriza controle
PISO_MARCADO = 20.0  # % quando a própria companhia marca o ente como acionista controlador


def _ch(v: str) -> str:
    """Minúsculas sem acento, para comparar texto do arquivo."""
    return unicodedata.normalize("NFKD", (v or "").lower()).encode("ascii", "ignore").decode()


def _num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _e_linha_do_lucro(cd: str, ds: str) -> bool:
    if not NIVEL_2.match(cd or ""):
        return False
    t = _ch(ds)
    return "lucro" in t and "periodo" in t and "antes" not in t and "acao" not in t


def _baixar(c: httpx.Client, url: str, destino: Path) -> bytes | None:
    if destino.exists() and destino.stat().st_size > 100_000:
        return destino.read_bytes()
    r = c.get(url)
    if r.status_code != 200 or r.content[:2] != b"PK":
        log.info("%s ainda não publicado (HTTP %s)", destino.name, r.status_code)
        return None
    RAW.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(r.content)
    return r.content


def ler_lucro(c: httpx.Client, ano: int) -> dict[str, dict]:
    """Lucro de cada empresa da lista no exercício fechado daquele arquivo. Devolve {cnpj: {lucro, conta, ...}}."""
    conteudo = _baixar(c, DFP.format(ano=ano), RAW / f"dfp_cia_aberta_{ano}.zip")
    if conteudo is None:
        return {}
    saida: dict[str, dict] = {}
    with zipfile.ZipFile(io.BytesIO(conteudo)) as zf:
        for sufixo in ("DRE_con", "DRE_ind"):
            nomes = [n for n in zf.namelist() if sufixo in n]
            if not nomes:
                continue
            # quem já veio do consolidado não é relido no individual (a comparação é feita ANTES de ler o arquivo,
            # senão a primeira linha da própria empresa já a excluiria das linhas seguintes)
            ja_tem = set(saida) if sufixo == "DRE_ind" else set()
            for linha in csv.DictReader(io.StringIO(zf.read(nomes[0]).decode("latin-1")), delimiter=";"):
                cnpj = linha["CNPJ_CIA"]
                if cnpj not in POR_CNPJ or linha["ORDEM_EXERC"] != "ÚLTIMO" or cnpj in ja_tem:
                    continue
                cd, ds = linha["CD_CONTA"], linha["DS_CONTA"]
                valor = _num(linha["VL_CONTA"])
                if valor is None:
                    continue
                escala = 1000 if (linha.get("ESCALA_MOEDA") or "").upper().startswith("MIL") else 1
                reg = saida.setdefault(cnpj, {"fim": linha["DT_FIM_EXERC"], "demonstracao": sufixo})
                if _e_linha_do_lucro(cd, ds):
                    # se houver mais de uma candidata, vale a de código maior (a que está mais embaixo na DRE)
                    if cd >= reg.get("conta", ""):
                        reg.update(lucro=round(valor * escala, 2), conta=cd, conta_ds=ds)
                        reg.pop("controlador", None)  # trocou a linha do lucro: o "atribuído ao controlador" é outro
                elif reg.get("conta") and cd == reg["conta"] + ".01" and "controlador" in _ch(ds):
                    reg["controlador"] = round(valor * escala, 2)
    return {k: v for k, v in saida.items() if "lucro" in v}


def ler_controle(c: httpx.Client, ano: int) -> dict[str, dict]:
    """Quem controlava cada empresa da lista naquele ano, pela posição acionária do formulário de referência."""
    conteudo = _baixar(c, FRE.format(ano=ano), RAW / f"fre_cia_aberta_{ano}.zip")
    if conteudo is None:
        return {}
    with zipfile.ZipFile(io.BytesIO(conteudo)) as zf:
        nomes = [n for n in zf.namelist() if "posicao_acionaria" in n and "classe" not in n]
        if not nomes:
            return {}
        linhas = list(csv.DictReader(io.StringIO(zf.read(nomes[0]).decode("latin-1")), delimiter=";"))

    publico: dict[str, dict] = {}                                  # controle direto por ente público
    candidatos: dict[str, list[dict]] = {}                         # controlador que é empresa (pode ser estatal)
    for l in linhas:
        cia = l["CNPJ_Companhia"]
        if cia not in POR_CNPJ or (l["Acionista_Relacionado"] or "").strip():
            continue                                               # só posição direta; o resto é cadeia de controle
        on = _num(l["Percentual_Acao_Ordinaria_Circulacao"]) or 0.0
        marcado = (l["Acionista_Controlador"] or "").strip().upper() == "S"
        cnpj_ac, nome_ac = (l["CPF_CNPJ_Acionista"] or "").strip(), (l["Acionista"] or "").strip()
        if not cnpj_ac or cnpj_ac.startswith("00.000.000/0000"):
            continue                                               # sem CNPJ não se sabe se é ente público brasileiro
        if not (on >= PISO_ON or (marcado and on >= PISO_MARCADO)):
            continue
        reg = {"ente": nome_ac, "cnpj_ente": cnpj_ac, "on": round(on, 3), "marcado": marcado,
               "ref": l["Data_Referencia"]}
        if ENTE_PUBLICO.search(_ch(nome_ac)) and not NAO_E_ENTE.search(_ch(nome_ac)):
            if cia not in publico or on > publico[cia]["on"]:
                publico[cia] = {**reg, "tipo": "direto"}
        else:
            candidatos.setdefault(cia, []).append(reg)

    # controle indireto: quem controla é outra estatal da lista, ou a Caixa (que não tem ações em bolsa). Duas voltas
    # resolvem as cadeias que existem aqui (União → Petrobras → BR Distribuidora).
    for _ in range(2):
        for cia, regs in candidatos.items():
            if cia in publico:
                continue
            for reg in regs:
                via = CONTROLADORAS_PUBLICAS.get(reg["cnpj_ente"])
                if not via and reg["cnpj_ente"] in publico:
                    via = POR_CNPJ[reg["cnpj_ente"]]["nome"]
                if via:
                    publico[cia] = {**reg, "tipo": "indireto", "via": via}
                    break
    return publico


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    out = PUB / "estatais.json"
    antigo = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    lucro: dict[str, dict[str, float]] = {k: dict(v) for k, v in (antigo.get("lucro") or {}).items()}
    controlador: dict[str, dict[str, float]] = {k: dict(v) for k, v in (antigo.get("controlador") or {}).items()}
    controle: dict[str, dict[str, dict]] = {k: dict(v) for k, v in (antigo.get("controle") or {}).items()}
    demonstracao: dict[str, dict[str, str]] = {k: dict(v) for k, v in (antigo.get("demonstracao") or {}).items()}

    hoje = datetime.now().year
    # anos já fechados no JSON não são baixados de novo; os dois últimos sempre são (podem ser republicados)
    conhecidos = {int(a) for v in lucro.values() for a in v}
    faltando = [a for a in range(ANO_INICIAL, hoje + 1) if a not in conhecidos or a >= hoje - 1]
    log.info("anos a buscar na CVM: %s", faltando or "nenhum")
    with httpx.Client(timeout=600, follow_redirects=True) as c:
        for ano in faltando:
            dados, quem = ler_lucro(c, ano), ler_controle(c, ano)
            for cnpj, reg in dados.items():
                nome = POR_CNPJ[cnpj]["nome"]
                lucro.setdefault(nome, {})[str(ano)] = reg["lucro"]
                demonstracao.setdefault(nome, {})[str(ano)] = reg["demonstracao"]
                if "controlador" in reg:
                    controlador.setdefault(nome, {})[str(ano)] = reg["controlador"]
            for cnpj, reg in quem.items():
                controle.setdefault(POR_CNPJ[cnpj]["nome"], {})[str(ano)] = reg
            if dados:
                log.info("DFP %d: %d empresas da lista; FRE: %d com controle público", ano, len(dados), len(quem))
        # as duas outras fontes são um arquivo só cada uma, então são relidas em toda execução
        federais, divid = sest.coletar(c), dividendos.coletar(c)

    anos = sorted({a for v in lucro.values() for a in v})
    if not anos:
        raise SystemExit("nenhum ano lido da CVM — o layout do arquivo mudou?")
    # A CVM abre o arquivo do ano novo com um punhado de empresas, muito antes de a maioria entregar. Um ano assim
    # viraria "o último ano" da página inteira, com uma tabela quase vazia. Então só entra o ano que tem pelo menos
    # metade das empresas do ano mais cheio.
    quantas_por_ano = {a: sum(1 for v in lucro.values() if a in v) for a in anos}
    piso = max(quantas_por_ano.values()) / 2
    magros = [a for a in anos if quantas_por_ano[a] < piso]
    for a in magros:
        log.info("ano %s fica de fora: só %d empresas entregaram (piso: %.0f)", a, quantas_por_ano[a], piso)
    anos = [a for a in anos if a not in magros]

    empresas = []
    for e in EMPRESAS:
        s = lucro.get(e["nome"], {})
        if not s:
            log.warning("sem lucro publicado para %s (não entrega DFP?)", e["nome"])
            continue
        ctrl = controle.get(e["nome"], {})
        if not ctrl:
            log.warning("sem controle público em nenhum ano para %s — fica fora do agregado", e["nome"])
        # Estatal no ano = o formulário daquele ano aponta ente público no controle. Ano sem formulário (acontece:
        # o Banco da Amazônia não tem posição em 2012–2013) é preenchido entre dois anos confirmados, e os anos
        # anteriores ao primeiro formulário também contam — nunca os posteriores ao último, que é justamente o que
        # marca a privatização. Todas as empresas da lista nasceram estatais, então estender para trás é seguro.
        confirmados = sorted(a for a in ctrl if a in anos)   # o formulário do ano corrente, sem DFP ainda, não conta
        estatal, origem = {}, {}
        for a in anos:
            if a in ctrl:
                estatal[a], origem[a] = True, "formulario"
            elif confirmados and a < confirmados[0]:
                estatal[a], origem[a] = True, "antes do primeiro formulario"
            elif confirmados and confirmados[0] < a < confirmados[-1]:
                estatal[a], origem[a] = True, "interpolado"
            else:
                estatal[a], origem[a] = False, "sem controle publico no formulario"
        anos_estatal = [a for a in anos if estatal[a] and a in s]
        if anos_estatal and anos_estatal[-1] != anos[-1] and anos[-1] in s:
            # a empresa continua publicando demonstração, mas saiu do controle público: privatização ou falha do
            # formulário. Fica no log para conferência — é a única forma de a regra errar sem aparecer na página.
            log.info("%s deixou de ter controle público em %s e segue publicando DFP (conferir se foi venda)",
                     e["nome"], int(anos_estatal[-1]) + 1)
        empresas.append({**e, "serie": dict(sorted(s.items())),
                         "serie_controlador": dict(sorted(controlador.get(e["nome"], {}).items())),
                         "demonstracao": demonstracao.get(e["nome"], {}),
                         "controle": dict(sorted(ctrl.items())), "estatal": estatal, "estatal_origem": origem,
                         "ultimo_ano": max(s), "ultimo_lucro": s[max(s)],
                         "estatal_hoje": bool(estatal.get(anos[-1])),
                         "primeiro_ano_estatal": anos_estatal[0] if anos_estatal else None,
                         "ultimo_ano_estatal": anos_estatal[-1] if anos_estatal else None})

    def entra(e: dict, ano: str) -> bool:
        return ano in e["serie"] and e["estatal"].get(ano, False) and "dentro_de" not in e

    def soma(ano: str, esfera: str | None = None) -> float:
        return round(sum(e["serie"][ano] for e in empresas if entra(e, ano)
                         and (esfera is None or e["esfera"].startswith(esfera))), 2)

    agregado = {a: soma(a) for a in anos}
    quantas = {a: sum(1 for e in empresas if entra(e, a)) for a in anos}
    dados = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "anos": anos, "empresas": empresas,
        "lucro": {e["nome"]: e["serie"] for e in empresas},
        "controlador": {e["nome"]: e["serie_controlador"] for e in empresas},
        "controle": {e["nome"]: e["controle"] for e in empresas},
        "demonstracao": {e["nome"]: e["demonstracao"] for e in empresas},
        "sest": federais or (antigo.get("sest") or {}),
        "dividendos": divid or (antigo.get("dividendos") or {}),
        "agregado": agregado, "empresas_no_agregado": quantas,
        "agregado_federais": {a: soma(a, "federal") for a in anos},
        "agregado_estaduais": {a: soma(a, "estadual") for a in anos},
        "agregado_municipais": {a: soma(a, "municipal") for a in anos},
        "fonte": "CVM, dados abertos: DFP (última linha da demonstração do resultado — Lucro ou Prejuízo Consolidado "
                 "do Período, convertido de milhares para reais) e FRE (posição acionária, para saber quem controlava "
                 "a empresa em cada ano)",
        "regra_controle": f"ente público com pelo menos {PISO_ON:.0f}% das ações ordinárias em posição direta, ou "
                          f"marcado pela companhia como acionista controlador com pelo menos {PISO_MARCADO:.0f}%; "
                          "controle indireto por outra estatal também conta. Ano sem formulário é preenchido entre "
                          "dois anos confirmados e antes do primeiro, nunca depois do último",
        "url": "https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp",
        "url_fre": "https://dados.cvm.gov.br/dataset/cia_aberta-doc-fre",
    }
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    ult = anos[-1]
    log.info("estatais %s–%s: %d empresas (%d no agregado de %s); lucro somado de %s = R$ %.1f bi",
             anos[0], ult, len(empresas), quantas[ult], ult, ult, agregado[ult] / 1e9)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
