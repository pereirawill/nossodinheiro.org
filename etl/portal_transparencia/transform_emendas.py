"""
Transformação — Emendas parlamentares (Portal da Transparência) → DuckDB → Parquet/JSON.

    python -m etl.portal_transparencia.transform_emendas --ano 2025

Entradas: data/raw/emendas_<ano>.jsonl.gz, [data/raw/emendas_documentos_<ano>.jsonl.gz],
          data/parquet/deputados.parquet (do ETL da Câmara, para o join autor→deputado)
Saídas:   data/parquet/emendas_<ano>.parquet
          data/public/emendas_por_autor_<ano>.json
          data/public/emendas_por_destino_<ano>.json   (se houver documentos)

Metodologia (resumo — detalhar em docs/metodologia/painel-1b-emendas.md):
- Três valores por emenda: EMPENHADO (reservado), LIQUIDADO (serviço atestado),
  PAGO (saiu do caixa). "Quanto recebeu" = PAGO; "quanto conseguiu alocar" = EMPENHADO.
  Restos a pagar (valorRestoPago) são pagamentos de anos anteriores — somar à parte.
- Tipos: individual (RP6), bancada (RP7), comissão (RP8), relator (RP9, extinta 2023).
  Para "por deputado" só RP6 tem autor individual; bancada/comissão são coletivas.
- Join autor→deputado por nome normalizado (sem acento, maiúsculo). Homônimos e
  senadores (autores também) exigem revisão manual: a saída traz `match_deputado`.
- Emendas não entram no "custo do deputado" (painel 1). São outro painel.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import duckdb

from ..camara import config as C
from ..camara.transform import SQL_DEPUTADOS

log = logging.getLogger("etl.portal.emendas.transform")
RAW, PQ, PUB = Path("data/raw"), Path("data/parquet"), Path("data/public")

BRL = "TRY_CAST(replace(replace({col}::VARCHAR, '.', ''), ',', '.') AS DOUBLE)"

SQL_EMENDAS = f"""
CREATE OR REPLACE TABLE emendas AS
SELECT codigoEmenda::VARCHAR AS codigo, ano::INTEGER AS ano, tipoEmenda AS tipo,
       autor AS autor_codigo,
       upper(strip_accents(trim(regexp_replace(nomeAutor::VARCHAR, '\\s*\\(.*$', '')))) AS autor,
       nomeAutor::VARCHAR AS autor_original,
       numeroEmenda AS numero, localidadeDoGasto AS localidade,
       funcao, subfuncao,
       {BRL.format(col='valorEmpenhado')}      AS empenhado,
       {BRL.format(col='valorLiquidado')}      AS liquidado,
       {BRL.format(col='valorPago')}           AS pago,
       {BRL.format(col='valorRestoInscrito')}  AS rp_inscrito,
       {BRL.format(col='valorRestoCancelado')} AS rp_cancelado,
       {BRL.format(col='valorRestoPago')}      AS rp_pago
FROM read_json_auto('{{raw}}', format='newline_delimited');
"""

SQL_POR_AUTOR = """
CREATE OR REPLACE TABLE por_autor AS
WITH dep AS (
  SELECT casa, id_parlamentar, nome, partido, uf, upper(strip_accents(nome)) AS nome_norm
  FROM parlamentares
)
SELECT e.autor, e.tipo,
       any_value(d.id_parlamentar) AS id_deputado, any_value(d.partido) AS partido, any_value(d.uf) AS uf,
       any_value(d.casa) AS casa,
       count(DISTINCT d.id_parlamentar) > 0 AS match_deputado,
       count(DISTINCT d.id_parlamentar) > 1 AS homonimo,
       count(*) AS emendas,
       round(sum(empenhado), 2) AS empenhado, round(sum(liquidado), 2) AS liquidado,
       round(sum(pago), 2) AS pago, round(sum(rp_pago), 2) AS rp_pago,
       round(sum(pago) / nullif(sum(empenhado), 0), 4) AS pct_pago
FROM emendas e LEFT JOIN dep d ON d.nome_norm = e.autor
GROUP BY e.autor, e.tipo
ORDER BY empenhado DESC;
"""

# Documentos: só se o extract de documentos rodou. Campos a confirmar com `inspect`;
# o mapeamento abaixo é o esperado e falha explicitamente se o campo não existir.
SQL_DOCS = f"""
CREATE OR REPLACE TABLE docs AS
SELECT codigoEmenda::VARCHAR AS codigo, fase, TRY_CAST(strptime(data, '%d/%m/%Y') AS DATE) AS data,
       favorecido, upper(strip_accents(coalesce(municipio, ''))) AS municipio, uf,
       {BRL.format(col='valor')} AS valor
FROM read_json_auto('{{raw}}', format='newline_delimited');
"""
SQL_POR_DESTINO = """
CREATE OR REPLACE TABLE por_destino AS
SELECT e.autor, e.funcao, d.uf, d.municipio, d.favorecido,
       round(sum(CASE WHEN upper(d.fase) LIKE 'PAG%' THEN d.valor END), 2) AS pago,
       count(*) AS documentos
FROM docs d JOIN emendas e USING (codigo)
GROUP BY ALL ORDER BY pago DESC NULLS LAST;
"""


def run(ano: int) -> None:
    PQ.mkdir(parents=True, exist_ok=True); PUB.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(SQL_EMENDAS.format(raw=RAW / f"emendas_{ano}.jsonl.gz"))
    _carregar_deputados(con)
    con.execute(SQL_POR_AUTOR)
    con.execute(f"COPY emendas TO '{PQ / f'emendas_{ano}.parquet'}' (FORMAT PARQUET)")
    _dump(con, "por_autor", PUB / f"emendas_por_autor_{ano}.json")

    docs = RAW / f"emendas_documentos_{ano}.jsonl.gz"
    if docs.exists():
        con.execute(SQL_DOCS.format(raw=docs))
        con.execute(SQL_POR_DESTINO)
        _dump(con, "por_destino", PUB / f"emendas_por_destino_{ano}.json")

    n, emp, pago, nomatch = con.execute(
        "SELECT count(*), round(sum(empenhado)/1e9,2), round(sum(pago)/1e9,2), "
        "count(*) FILTER (WHERE NOT match_deputado AND tipo ILIKE '%individual%') FROM por_autor").fetchone()
    log.info("%d autores; empenhado R$ %.2f bi; pago R$ %.2f bi; %d autores individuais sem match com deputado/senador (ex-parlamentares/homônimos?)",
             n, emp, pago, nomatch)


def _carregar_deputados(con: duckdb.DuckDBPyConnection) -> None:
    """Tabela `parlamentares` (casa, id_parlamentar, nome, partido, uf) para o join por nome.
    Deputados: parquet do ETL da Câmara se existir, senão a lista bruta da legislatura (`extract deputados`,
    sem CEAP). Senadores: `data/raw/senadores_atual.jsonl.gz` (`etl.senado.extract senadores`), se existir —
    senadores também têm emenda individual e, com cota maior, lideram a lista."""
    pq = PQ / "deputados.parquet"
    raw = RAW / f"deputados_leg{C.LEGISLATURA_ATUAL}.jsonl.gz"
    if pq.exists():
        con.execute(f"CREATE OR REPLACE TABLE deputados AS SELECT * FROM read_parquet('{pq}')")
    elif raw.exists():
        con.execute(SQL_DEPUTADOS.format(raw=raw))
    else:
        raise SystemExit(f"faltam {pq} e {raw}: rode `python -m etl.camara.extract deputados` antes")
    con.execute("CREATE OR REPLACE TABLE parlamentares AS "
                "SELECT 'Câmara' AS casa, id_deputado AS id_parlamentar, nome, partido, uf FROM deputados")
    sen = RAW / "senadores_atual.jsonl.gz"
    if sen.exists():
        con.execute(f"""INSERT INTO parlamentares
            SELECT 'Senado', TRY_CAST(id AS INTEGER), nome::VARCHAR, partido::VARCHAR, uf::VARCHAR
            FROM read_json('{sen}', format='newline_delimited', columns={{
                'id':'VARCHAR','nome':'VARCHAR','nome_completo':'VARCHAR','partido':'VARCHAR','uf':'VARCHAR','url_foto':'VARCHAR'}},
                ignore_errors=true)""")
    else:
        log.warning("%s ausente: senadores ficarão sem partido/UF nas emendas", sen)


def _dump(con: duckdb.DuckDBPyConnection, table: str, out: Path) -> None:
    rows = con.execute(f"SELECT * FROM {table}").fetchall()
    cols = [d[0] for d in con.description]
    out.write_text(json.dumps([dict(zip(cols, r)) for r in rows], ensure_ascii=False, default=str), encoding="utf-8")
    log.info("%s: %d linhas", out, len(rows))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(); ap.add_argument("--ano", type=int, required=True)
    run(ap.parse_args().ano)
