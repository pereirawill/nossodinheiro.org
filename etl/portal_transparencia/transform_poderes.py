"""
Painel 5 — agregação por Poder, por órgão/unidade orçamentária e por GND (SIOP).

    python -m etl.portal_transparencia.transform_poderes --ano 2025 [--populacao 212600000]

Entrada: data/raw/despesas_orgao_<ano>.jsonl.gz (extract_poderes: 1 linha por órgão × UO × GND)
Saídas: data/public/poderes_<ano>.json         (por Poder)
        data/public/poderes_orgaos_<ano>.json  (por unidade orçamentária)
        data/public/poderes_gnd_<ano>.json     (por Poder × grupo de natureza da despesa)
        data/public/poderes_categoria_<ano>.json (por Poder × "Manter a máquina" | "Políticas públicas" |
                                                  "Encargos especiais" × subcategoria)
        data/public/poderes_funcao_<ano>.json  (por função da LOA: Previdência, Saúde, Educação, Encargos Especiais…)

Metodologia (resumo):
- Valor = PAGO no ano (caixa). Dotação, empenhado e liquidado ficam como colunas.
- "Manter a máquina" = Programa de Gestão e Manutenção do Poder (classificação da própria LOA),
  detalhado em pessoal ativo, aposentados/pensionistas, custeio e investimento (ver extract_poderes).
- Per capita: população IBGE do ano (passar via --populacao; não inventar).
- Judiciário ESTADUAL (TJs) não está aqui: é orçamento estadual (SICONFI, função 02). v2.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import duckdb

log = logging.getLogger("etl.portal.poderes.transform")
RAW, PQ, PUB = Path("data/raw"), Path("data/parquet"), Path("data/public")

SQL_ITENS = """
CREATE OR REPLACE TABLE itens AS
SELECT poder, cod_superior::VARCHAR AS cod_superior, orgao_superior, cod_orgao::VARCHAR AS cod_orgao, orgao,
       gnd::VARCHAR AS gnd, gnd_nome, programa::VARCHAR AS programa, categoria, subcategoria,
       coalesce(funcao::VARCHAR, '') AS funcao, coalesce(funcao_nome, '') AS funcao_nome, ano::INTEGER AS ano,
       dotacao::DOUBLE AS dotacao, empenhado::DOUBLE AS empenhado, liquidado::DOUBLE AS liquidado, pago::DOUBLE AS pago
FROM read_json_auto('{raw}', format='newline_delimited');
"""
SQL_FUNCOES = """
CREATE OR REPLACE TABLE funcoes AS
SELECT funcao, funcao_nome, round(sum(pago),2) AS pago, round(sum(empenhado),2) AS empenhado,
       round(coalesce(sum(pago) FILTER (WHERE poder = 'Dívida/Transferências'), 0),2) AS pago_divida_transferencias
FROM itens GROUP BY ALL ORDER BY pago DESC;
"""
SQL_CATEGORIAS = """
CREATE OR REPLACE TABLE categorias AS
SELECT poder, categoria, subcategoria, round(sum(pago),2) AS pago, round(sum(empenhado),2) AS empenhado
FROM itens GROUP BY ALL ORDER BY poder, categoria, pago DESC;
"""
SQL_ORGAOS = """
CREATE OR REPLACE TABLE orgaos AS
SELECT poder, cod_superior, orgao_superior, cod_orgao, orgao, ano,
       round(sum(dotacao),2) AS dotacao, round(sum(empenhado),2) AS empenhado,
       round(sum(liquidado),2) AS liquidado, round(sum(pago),2) AS pago
FROM itens GROUP BY ALL ORDER BY pago DESC;
"""
SQL_PODERES = """
CREATE OR REPLACE TABLE poderes AS
SELECT poder, round(sum(pago),2) AS pago, round(sum(empenhado),2) AS empenhado,
       count(DISTINCT cod_orgao) AS orgaos,
       CASE WHEN {pop} > 0 THEN round(sum(pago)/{pop}, 2) END AS pago_por_habitante
FROM orgaos GROUP BY poder ORDER BY pago DESC;
"""
SQL_GND = """
CREATE OR REPLACE TABLE gnd AS
SELECT poder, gnd, gnd_nome, round(sum(pago),2) AS pago, round(sum(empenhado),2) AS empenhado
FROM itens GROUP BY ALL ORDER BY poder, gnd;
"""


def run(ano: int, populacao: int = 0) -> None:
    PUB.mkdir(parents=True, exist_ok=True); PQ.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(SQL_ITENS.format(raw=RAW / f"despesas_orgao_{ano}.jsonl.gz"))
    con.execute(SQL_ORGAOS)
    con.execute(SQL_PODERES.format(pop=populacao))
    con.execute(SQL_GND)
    con.execute(SQL_CATEGORIAS)
    con.execute(SQL_FUNCOES)
    _dump(con, "funcoes", PUB / f"poderes_funcao_{ano}.json")
    _dump(con, "poderes", PUB / f"poderes_{ano}.json")
    _dump(con, "orgaos", PUB / f"poderes_orgaos_{ano}.json")
    _dump(con, "gnd", PUB / f"poderes_gnd_{ano}.json")
    _dump(con, "categorias", PUB / f"poderes_categoria_{ano}.json")
    con.execute(f"COPY orgaos TO '{PQ / f'poderes_orgaos_{ano}.parquet'}' (FORMAT PARQUET)")

    for p, pago in con.execute("SELECT poder, pago FROM poderes").fetchall():
        log.info("%-22s R$ %14.2f bi", p, pago / 1e9)


def _dump(con, table, out: Path) -> None:
    rows = con.execute(f"SELECT * FROM {table}").fetchall(); cols = [d[0] for d in con.description]
    out.write_text(json.dumps([dict(zip(cols, r)) for r in rows], ensure_ascii=False, default=str), encoding="utf-8")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, required=True)
    ap.add_argument("--populacao", type=int, default=0, help="população IBGE do ano, p/ per capita")
    a = ap.parse_args(); run(a.ano, a.populacao)
