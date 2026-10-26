"""
Painel 5 — agregação por Poder e por órgão (Fonte A) e por GND (Fonte B, se baixada).

    python -m etl.portal_transparencia.transform_poderes --ano 2025 [--populacao 212600000]

Saídas: data/public/poderes_<ano>.json (por Poder), data/public/poderes_orgaos_<ano>.json (por órgão),
        data/public/poderes_gnd_<ano>.json (se data/raw/execucao/<ano>*.zip existir)

Metodologia (resumo):
- Valor = PAGO no ano (caixa). Empenhado e liquidado ficam como colunas.
- "Custo de funcionar" (GND 1 Pessoal + GND 3 Outras despesas correntes + GND 4 Investimentos)
  vs. "Políticas/transferências" (benefícios, transferências a estados/municípios) vs. "Dívida"
  (GND 2 Juros + GND 6 Amortização) — só com a Fonte B.
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
BRL = "TRY_CAST(replace(replace({col}::VARCHAR, '.', ''), ',', '.') AS DOUBLE)"

SQL_ORGAOS = f"""
CREATE OR REPLACE TABLE orgaos AS
SELECT poder, codigoOrgaoSuperior::VARCHAR AS cod_superior, orgaoSuperior AS orgao_superior,
       codigoOrgao::VARCHAR AS cod_orgao, orgao, ano::INTEGER AS ano,
       {BRL.format(col='empenhado')} AS empenhado, {BRL.format(col='liquidado')} AS liquidado,
       {BRL.format(col='pago')} AS pago
FROM read_json_auto('{{raw}}', format='newline_delimited');
"""
SQL_PODERES = """
CREATE OR REPLACE TABLE poderes AS
SELECT poder, round(sum(pago),2) AS pago, round(sum(empenhado),2) AS empenhado,
       count(DISTINCT cod_orgao) AS orgaos,
       CASE WHEN {pop} > 0 THEN round(sum(pago)/{pop}, 2) END AS pago_por_habitante
FROM orgaos GROUP BY poder ORDER BY pago DESC;
"""
# Fonte B: CSV mensal (dentro do ZIP) com colunas como "Código Órgão Superior",
# "Grupo de Despesa (GND)" ... Nomes variam por versão → confirmar no primeiro run.
SQL_GND = """
CREATE OR REPLACE TABLE gnd AS
SELECT "Código Órgão Superior" AS cod_superior, "Nome Órgão Superior" AS orgao_superior,
       "Código Grupo de Despesa" AS gnd, "Grupo de Despesa" AS gnd_nome,
       sum(TRY_CAST(replace(replace("Valor Pago (R$)"::VARCHAR,'.',''),',','.') AS DOUBLE)) AS pago
FROM read_csv('{glob}', delim=';', header=true, encoding='latin-1', ignore_errors=true, union_by_name=true)
GROUP BY ALL;
"""


def run(ano: int, populacao: int = 0) -> None:
    PUB.mkdir(parents=True, exist_ok=True); PQ.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(SQL_ORGAOS.format(raw=RAW / f"despesas_orgao_{ano}.jsonl.gz"))
    con.execute(SQL_PODERES.format(pop=populacao))
    _dump(con, "poderes", PUB / f"poderes_{ano}.json")
    _dump(con, "orgaos", PUB / f"poderes_orgaos_{ano}.json")
    con.execute(f"COPY orgaos TO '{PQ / f'poderes_orgaos_{ano}.parquet'}' (FORMAT PARQUET)")

    zips = sorted((RAW / "execucao").glob(f"{ano}*.zip")) if (RAW / "execucao").exists() else []
    if zips:
        con.execute(SQL_GND.format(glob=str(RAW / "execucao" / f"{ano}*.zip")))
        _dump(con, "gnd", PUB / f"poderes_gnd_{ano}.json")

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
