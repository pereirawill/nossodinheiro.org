"""
Presidência — agregação do cartão corporativo (CPGF).

    python -m etl.presidencia.transform --ano 2026

Entrada: data/raw/presidencia_cpgf_<ano>.jsonl.gz
Saída:   data/public/presidencia_cpgf_<ano>.json
  { ano, meses:[{mes, presidencia, sigiloso, governo, transacoes}], por_orgao:[{cod_orgao, orgao, valor, transacoes, sigiloso}],
    por_tipo:[{tipo, valor, transacoes}], favorecidos:[{favorecido, doc, valor, transacoes, atividade, cnae}]  (só PJ, top 25),
    por_atividade:[{atividade, valor, transacoes, fornecedores}]  (PJ identificados, classificados pelo CNAE da Receita — ver cnae.py),
    portadores: n (quantos portadores identificados), totais:{presidencia, sigiloso, pct_sigiloso, governo, meses_publicados} }
Regras: "sigiloso" = linha que o Portal publica sem portador/favorecido ("Informações protegidas por sigilo"); são as
despesas de segurança da Presidência (LAI art. 23). Favorecidos pessoa física não aparecem no site (só o total).
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import duckdb

from .cnae import cnae_de, categoria_de

log = logging.getLogger("etl.presidencia.transform")
RAW, PUB = Path("data/raw"), Path("data/public")

SQL = """
CREATE OR REPLACE TABLE t AS SELECT * FROM read_json_auto('{raw}', format='newline_delimited', union_by_name=true);
CREATE OR REPLACE TABLE p AS SELECT * FROM t WHERE origem = 'presidencia';
"""


def run(ano: int) -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(SQL.format(raw=RAW / f"presidencia_cpgf_{ano}.jsonl.gz"))
    q = lambda sql: [dict(zip([d[0] for d in con.description], r)) for r in con.execute(sql).fetchall()]
    meses = q("""SELECT g.mes, round(coalesce(sum(p.valor),0),2) AS presidencia, round(coalesce(sum(p.valor) FILTER (WHERE p.sigiloso),0),2) AS sigiloso,
                        any_value(g.valor) AS governo, count(p.valor) AS transacoes
                 FROM (SELECT mes, valor FROM t WHERE origem='total_governo') g LEFT JOIN p USING (mes) GROUP BY g.mes ORDER BY g.mes""")
    por_orgao = q("""SELECT cod_orgao, orgao, round(sum(valor),2) AS valor, count(*) AS transacoes, round(sum(valor) FILTER (WHERE sigiloso),2) AS sigiloso
                     FROM p GROUP BY ALL ORDER BY valor DESC""")
    por_tipo = q("""SELECT CASE WHEN sigiloso THEN 'Sob sigilo' WHEN transacao ILIKE 'SAQUE%' THEN 'Saque em dinheiro'
                               WHEN transacao ILIKE '%INT$%' THEN 'Compra no exterior' ELSE 'Compra' END AS tipo,
                           round(sum(valor),2) AS valor, count(*) AS transacoes FROM p GROUP BY ALL ORDER BY valor DESC""")
    favorecidos = q("""SELECT favorecido, favorecido_doc AS doc, round(sum(valor),2) AS valor, count(*) AS transacoes
                       FROM p WHERE NOT sigiloso AND length(regexp_replace(favorecido_doc, '\\D', '', 'g')) = 14
                       GROUP BY ALL ORDER BY valor DESC LIMIT 25""")
    # Tipo de serviço pelo CNAE (atividade principal na Receita) de cada CNPJ identificado — nada é adivinhado pelo nome
    pj = q("""SELECT regexp_replace(favorecido_doc, '\\D', '', 'g') AS cnpj, round(sum(valor),2) AS valor, count(*) AS transacoes
              FROM p WHERE NOT sigiloso AND length(regexp_replace(favorecido_doc, '\\D', '', 'g')) = 14 GROUP BY ALL""")
    info = cnae_de([x["cnpj"] for x in pj])
    por_atividade: dict[str, dict] = {}
    for x in pj:
        i = info.get(x["cnpj"], {}); cat = categoria_de(i.get("cnae", ""))
        a = por_atividade.setdefault(cat, {"atividade": cat, "valor": 0.0, "transacoes": 0, "fornecedores": 0, "exemplo_cnae": i.get("descricao", "")})
        a["valor"] = round(a["valor"] + x["valor"], 2); a["transacoes"] += x["transacoes"]; a["fornecedores"] += 1
    por_atividade = sorted(por_atividade.values(), key=lambda a: -a["valor"])
    for f in favorecidos:
        i = info.get(__import__("re").sub(r"\D", "", f["doc"]), {}); f["atividade"] = categoria_de(i.get("cnae", "")); f["cnae"] = i.get("descricao", "")
    portadores = con.execute("SELECT count(DISTINCT portador) FROM p WHERE NOT sigiloso").fetchone()[0]
    tot_p, tot_s, tot_g, n_meses = con.execute("""SELECT round(sum(valor),2), round(sum(valor) FILTER (WHERE sigiloso),2),
        (SELECT round(sum(valor),2) FROM t WHERE origem='total_governo'), (SELECT count(*) FROM t WHERE origem='total_governo') FROM p""").fetchone()
    out = {"ano": ano, "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
           "fonte": "Portal da Transparência (CGU), download de dados — Cartões de Pagamento do Governo Federal (CPGF)",
           "meses": meses, "por_orgao": por_orgao, "por_tipo": por_tipo, "favorecidos": favorecidos, "por_atividade": por_atividade, "portadores": portadores,
           "totais": {"presidencia": tot_p, "sigiloso": tot_s, "pct_sigiloso": round(tot_s / tot_p, 4) if tot_p else None, "governo": tot_g, "meses_publicados": n_meses}}
    path = PUB / f"presidencia_cpgf_{ano}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, default=str), encoding="utf-8")
    log.info("%d: Presidência R$ %.2f mi em %d meses (%.0f%% sob sigilo); governo R$ %.2f mi", ano, tot_p / 1e6, n_meses, 100 * (tot_s / tot_p if tot_p else 0), tot_g / 1e6)
    return path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(); ap.add_argument("--ano", type=int, required=True)
    run(ap.parse_args().ano)
