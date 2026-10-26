"""
Painel 5 — Quanto custa cada Poder (Legislativo, Judiciário, Executivo) — União.

Fonte: SIOP (Sistema Integrado de Planejamento e Orçamento, Ministério do Planejamento e
Orçamento), dados abertos da LOA e da execução orçamentária, endpoint SPARQL público:
    https://www1.siop.planejamento.gov.br/sparql/   (grafo <http://orcamento.dados.gov.br/<ano>/>)
    documentação: https://www1.siop.planejamento.gov.br/siopdoc/doku.php/acesso_publico:dados_abertos
Sem chave. Uma consulta agregada por órgão × unidade orçamentária × GND devolve ~1.300 linhas
com dotação (lei + créditos), empenhado, liquidado e pago. Cobre TODOS os Poderes.

Por que não a API do Portal da Transparência: `/despesas/por-orgao` é documentada como
"Consulta as despesas dos órgãos do Poder Executivo Federal" (OpenAPI, 2026-10-26) — Câmara,
Senado, TCU, tribunais, MPU e DPU nunca aparecem lá, com qualquer código. O CSV anual
"Orçamento da Despesa" do Portal tem a mesma cobertura.

Uso:
    python -m etl.portal_transparencia.extract_poderes --ano 2025 [--inspect]

Saída: data/raw/despesas_orgao_<ano>.jsonl.gz
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path

import httpx

from .extract_emendas import write_jsonl

log = logging.getLogger("etl.portal.poderes")
RAW = Path("data/raw")
SPARQL = "https://www1.siop.planejamento.gov.br/sparql/"

# Código do órgão orçamentário (LOA) → Poder.
PODER_POR_ORGAO_SUPERIOR = {
    "01000": "Legislativo",  # Câmara dos Deputados
    "02000": "Legislativo",  # Senado Federal
    "03000": "Legislativo",  # TCU (controle externo, vinculado ao Legislativo)
    "10000": "Judiciário",   # STF
    "11000": "Judiciário",   # STJ
    "12000": "Judiciário",   # Justiça Federal (CJF + TRFs)
    "13000": "Judiciário",   # Justiça Militar da União
    "14000": "Judiciário",   # Justiça Eleitoral (TSE + TREs)
    "15000": "Judiciário",   # Justiça do Trabalho (TST + TRTs)
    "16000": "Judiciário",   # TJDFT
    "17000": "Judiciário",   # CNJ
    "29000": "Funções essenciais",  # DPU
    "34000": "Funções essenciais",  # MPU
    "59000": "Funções essenciais",  # CNMP
}
# Qualquer outro código = Executivo, exceto os órgãos "sem Poder": Encargos Financeiros
# (71000), Encargos Previdenciários (72000), Transferências a estados/municípios (73000),
# Operações Oficiais de Crédito (74000), Dívida Pública Federal (75000), Reserva (90000).
# Não são "custo de um Poder" — ficam em "Dívida/Transferências".
NAO_PODER = {"71000", "72000", "73000", "74000", "75000", "90000"}


def classificar(cod_superior: str) -> str:
    cod = str(cod_superior).zfill(5)
    if cod in PODER_POR_ORGAO_SUPERIOR:
        return PODER_POR_ORGAO_SUPERIOR[cod]
    if cod in NAO_PODER:
        return "Dívida/Transferências"
    return "Executivo"


QUERY = """
PREFIX loa: <http://vocab.e.gov.br/2013/09/loa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?cod_superior ?orgao_superior ?cod_orgao ?orgao ?gnd ?gnd_nome ?programa ?programa_nome ?acao ?acao_nome ?funcao ?funcao_nome
       (SUM(?emp) AS ?empenhado) (SUM(?liq) AS ?liquidado) (SUM(?pag) AS ?pago) (SUM(?dot) AS ?dotacao)
FROM <http://orcamento.dados.gov.br/{ano}/>
WHERE {{
  ?i a loa:ItemDespesa ; loa:temUnidadeOrcamentaria ?u ; loa:temGND ?g ; loa:temPrograma ?p ; loa:temAcao ?a ; loa:temFuncao ?f ;
     loa:valorEmpenhado ?emp ; loa:valorLiquidado ?liq ; loa:valorPago ?pag ; loa:valorLeiMaisCredito ?dot .
  ?u loa:codigo ?cod_orgao ; rdfs:label ?orgao ; loa:temOrgao ?o .
  ?o loa:codigo ?cod_superior ; rdfs:label ?orgao_superior .
  ?g loa:codigo ?gnd ; rdfs:label ?gnd_nome .
  ?p loa:codigo ?programa ; rdfs:label ?programa_nome .
  ?a loa:codigo ?acao ; rdfs:label ?acao_nome .
  ?f loa:codigo ?funcao ; rdfs:label ?funcao_nome .
}}
GROUP BY ?cod_superior ?orgao_superior ?cod_orgao ?orgao ?gnd ?gnd_nome ?programa ?programa_nome ?acao ?acao_nome ?funcao ?funcao_nome
ORDER BY ?cod_superior ?cod_orgao ?gnd ?programa ?acao ?funcao
"""
NUMERICOS = ("empenhado", "liquidado", "pago", "dotacao")

# "Manter a máquina" = Programas de Gestão e Manutenção da LOA (um por Poder): pessoal ativo,
# aposentados e pensionistas do órgão, custeio, prédios, TI. Tudo fora deles é programa
# finalístico (política pública) ou operação especial (09xx: sentenças judiciais, encargos).
PROGRAMAS_GESTAO = {"0031", "0032", "0033", "0034", "0035"}  # MPU, Executivo, Judiciário, Legislativo, estatais
INATIVOS = re.compile(r"aposentad|pens[õo]es|inativos|benef[ií]cio especial", re.I)


def categorizar(row: dict) -> tuple[str, str]:
    """→ (categoria, subcategoria). Categoria compara Poderes; subcategoria detalha a máquina."""
    if row["poder"] == "Dívida/Transferências":
        return "Dívida/Transferências", row["gnd_nome"]
    prog = str(row["programa"]).zfill(4)
    if prog in PROGRAMAS_GESTAO:
        gnd = str(row["gnd"])
        if gnd == "1":
            sub = "Aposentados e pensionistas" if INATIVOS.search(row.get("acao_nome", "")) else "Pessoal ativo e encargos"
        elif gnd == "3":
            sub = "Custeio"
        elif gnd in ("4", "5"):
            sub = "Investimento"
        else:
            sub = "Outros"
        return "Manter a máquina", sub
    if prog.startswith("09"):
        return "Encargos especiais", row["programa_nome"]
    return "Políticas públicas", row["programa_nome"]


def consultar(ano: int) -> list[dict]:
    r = httpx.get(SPARQL, params={"query": QUERY.format(ano=ano)},
                  headers={"accept": "application/sparql-results+json",
                           "user-agent": "nossodinheiro-etl/0.1"}, timeout=180)
    r.raise_for_status()
    rows = []
    for b in r.json()["results"]["bindings"]:
        row = {k: v["value"] for k, v in b.items()}
        for k in NUMERICOS:
            row[k] = float(row.get(k, 0) or 0)
        row["ano"] = ano
        row["poder"] = classificar(row["cod_superior"])
        row["categoria"], row["subcategoria"] = categorizar(row)
        rows.append(row)
    return rows


def extrair(ano: int, inspect: bool = False) -> None:
    rows = consultar(ano)
    if not rows:
        raise SystemExit(f"SIOP devolveu 0 linhas para {ano} — grafo ainda não publicado?")
    if inspect:
        print("campos:", sorted(rows[0].keys())); print(json.dumps(rows[0], ensure_ascii=False, indent=2))
    por_poder: dict[str, float] = {}
    for row in rows:
        por_poder[row["poder"]] = por_poder.get(row["poder"], 0) + row["pago"]
    for poder, pago in sorted(por_poder.items(), key=lambda kv: -kv[1]):
        log.info("%-22s pago R$ %10.2f bi", poder, pago / 1e9)
    for poder in ("Legislativo", "Judiciário"):
        if por_poder.get(poder, 0) <= 0:
            raise SystemExit(f"{poder} sem despesa paga em {ano} — fonte mudou? Não gravar.")
    write_jsonl(RAW / f"despesas_orgao_{ano}.jsonl.gz", iter(rows))


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, required=True)
    ap.add_argument("--inspect", action="store_true", help="imprime a primeira linha")
    a = ap.parse_args(argv)
    extrair(a.ano, a.inspect)


if __name__ == "__main__":
    main()
