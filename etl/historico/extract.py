"""
Histórico — séries longas, do primeiro ano que cada fonte oferece em formato aberto, corrigidas pelo IPCA.

    python -m etl.historico.extract            # gera data/public/historico.json

Fontes:
- SIOP (SPARQL público), grafos <http://orcamento.dados.gov.br/<ano>/> de 2000 ao último publicado: despesa paga e empenhada
  da União por função (01 Legislativa … 28 Encargos Especiais), um grafo por ano (26 consultas, ~10 s cada).
- Receita Federal, arrecadação por estado (já em data/public/impostos.json): total e bases por ano, 2000+.
- Ministério da Previdência, BEPS tabela 14: benefícios emitidos em dezembro de cada ano (2000+) e o último mês.
- IBGE, IPCA (SIDRA tabela 1737, variável 2266, número-índice dez/1993 = 100), índice de dezembro de cada ano, para
  converter tudo a "reais do último ano fechado".

Saída: data/public/historico.json — {gerado_em_utc, ano_base, ipca:{ano: indice_dez}, deflator:{ano: fator_para_ano_base},
  uniao:[{ano, total, encargos, funcoes:{cod:{nome, pago}}}], receita:[{ano, meses, total, bases}], inss:[{ano, mes, total, rgps, assistencial}]}
Valores NOMINAIS; o site aplica `deflator[ano]` para mostrar em reais do ano-base.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx

log = logging.getLogger("etl.historico")
PUB = Path("data/public")
SPARQL = "https://www1.siop.planejamento.gov.br/sparql/"
Q_FUNCAO = """
PREFIX loa: <http://vocab.e.gov.br/2013/09/loa#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?funcao ?funcao_nome (SUM(?pag) AS ?pago) (SUM(?emp) AS ?empenhado)
FROM <http://orcamento.dados.gov.br/{ano}/>
WHERE {{ ?i a loa:ItemDespesa ; loa:temFuncao ?f ; loa:valorPago ?pag ; loa:valorEmpenhado ?emp . ?f loa:codigo ?funcao ; rdfs:label ?funcao_nome . }}
GROUP BY ?funcao ?funcao_nome ORDER BY ?funcao
"""
SIDRA_IPCA = "https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/all?formato=json"
BEPS = "https://www.gov.br/previdencia/pt-br/assuntos/previdencia-social/Dados-estatisticos-previdencia-social-e-inss/boletins-da-previdencia-social"
UA = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
ANO_INICIO = 2000


def siop(c: httpx.Client, ano: int) -> dict | None:
    r = c.get(SPARQL, params={"query": Q_FUNCAO.format(ano=ano)}, headers={"accept": "application/sparql-results+json"})
    r.raise_for_status()
    funcoes = {}
    for b in r.json()["results"]["bindings"]:
        pago = float(b["pago"]["value"] or 0); emp = float(b["empenhado"]["value"] or 0)
        funcoes[b["funcao"]["value"]] = {"nome": b["funcao_nome"]["value"], "pago": round(pago, 2), "empenhado": round(emp, 2)}
    if not funcoes or sum(f["pago"] for f in funcoes.values()) <= 0:
        return None
    total = round(sum(f["pago"] for f in funcoes.values()), 2)
    return {"ano": ano, "total": total, "encargos": funcoes.get("28", {}).get("pago", 0.0), "funcoes": funcoes}


def ipca(c: httpx.Client) -> dict[int, float]:
    d = c.get(SIDRA_IPCA).json()
    out = {}
    for r in d[1:]:
        p = r.get("D3C") or ""          # AAAAMM
        if len(p) == 6 and p.endswith("12"):
            out[int(p[:4])] = float(r["V"])
    ultimo = max(int(r["D3C"][:4]) for r in d[1:] if (r.get("D3C") or "").isdigit())
    # ano corrente: último mês disponível
    ult_mes = max(r["D3C"] for r in d[1:] if (r.get("D3C") or "").startswith(str(ultimo)))
    out[ultimo] = float(next(r["V"] for r in d[1:] if r.get("D3C") == ult_mes))
    return out


def inss(c: httpx.Client) -> list[dict]:
    import xlrd
    html = c.get(BEPS).text
    links = sorted(set(re.findall(r'href="([^"]+beps\d{6}_final\.xlsx?)"', html, flags=re.I)))
    url = sorted(links, key=lambda u: re.search(r"beps(\d{2})(\d{4})", u).group(2) + re.search(r"beps(\d{2})(\d{4})", u).group(1))[-1]
    if url.startswith("/"):
        url = "https://www.gov.br" + url
    sh = xlrd.open_workbook(file_contents=c.get(url).content).sheet_by_name("14")
    MESES = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro")
    ano, linhas = None, []
    for r in range(sh.nrows):
        row = [sh.cell_value(r, cc) for cc in range(sh.ncols)]
        a0 = str(row[0]).strip().replace(".0", "")
        if a0.isdigit() and int(a0) >= 2000:
            ano = int(a0)
        nums = [v for v in row[2:] if isinstance(v, float)]
        if ano and isinstance(row[1], str) and row[1].strip().lower() in MESES and len(nums) >= 3 and nums[0] > 0:
            linhas.append({"ano": ano, "mes": row[1].strip(), "total": nums[0], "rgps": nums[1], "assistencial": nums[2]})
    # dezembro de cada ano + último mês disponível
    por_ano = {}
    for l in linhas:
        if l["mes"].lower() == "dezembro" or l["ano"] not in por_ano:
            por_ano[l["ano"]] = l
        elif por_ano[l["ano"]]["mes"].lower() != "dezembro":
            por_ano[l["ano"]] = l
    return [por_ano[a] for a in sorted(por_ano)]


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers=UA, timeout=240, follow_redirects=True) as c:
        indices = ipca(c)
        ano_base = max(a for a in indices if a < datetime.now().year) if any(a < datetime.now().year for a in indices) else max(indices)
        uniao = []
        for ano in range(ANO_INICIO, datetime.now().year + 1):
            try:
                u = siop(c, ano)
            except httpx.HTTPError as e:
                log.warning("SIOP %d: %s", ano, e); u = None
            if u:
                uniao.append(u); log.info("SIOP %d: total R$ %.1f bi (%d funções)", ano, u["total"] / 1e9, len(u["funcoes"]))
        receita = json.loads((PUB / "impostos.json").read_text(encoding="utf-8"))["anual"] if (PUB / "impostos.json").exists() else []
        beneficios = inss(c)
    deflator = {a: round(indices[ano_base] / v, 6) for a, v in indices.items() if v}
    dados = {"gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"), "ano_base": ano_base,
             "ipca": {str(a): v for a, v in sorted(indices.items())}, "deflator": {str(a): v for a, v in sorted(deflator.items())},
             "uniao": uniao, "receita": [{k: r[k] for k in ("ano", "meses", "total", "bases")} for r in receita], "inss": beneficios,
             "fontes": {"uniao": "SIOP, execução orçamentária por função (grafos anuais)", "receita": "Receita Federal, arrecadação por estado",
                        "inss": "Ministério da Previdência, BEPS tabela 14 (dezembro de cada ano; último mês no ano corrente)", "ipca": "IBGE, IPCA (SIDRA 1737), índice de dezembro"}}
    out = PUB / "historico.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    log.info("ano-base %d; União %d anos; receita %d anos; INSS %d anos; IPCA %d anos", ano_base, len(uniao), len(receita), len(beneficios), len(indices))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
