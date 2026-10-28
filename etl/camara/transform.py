"""
Transformação — DuckDB sobre o raw, saída em Parquet + JSON para o site.

    python -m etl.camara.transform --ano 2026 [--fonte api|bulk]

Produz:
  data/parquet/deputados.parquet
  data/parquet/ceap_<ano>.parquet          (1 linha por documento, schema único)
  data/parquet/custo_deputado_<ano>.parquet (1 linha por deputado)
  data/public/custo_deputado_<ano>.json     (consumido pelo site)
  data/public/meta_<ano>.json               (constantes/premissas usadas)

Schema único `ceap` (independente da fonte):
  id_deputado, ano, mes, tipo_despesa, fornecedor, cnpj_cpf_fornecedor,
  data_documento, valor_documento, valor_glosa, valor_liquido, url_documento
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb

from . import config as C

log = logging.getLogger("etl.camara.transform")
RAW, PQ, PUB = Path("data/raw"), Path("data/parquet"), Path("data/public")

SQL_DEPUTADOS = """
CREATE OR REPLACE TABLE deputados AS
SELECT TRY_CAST(id AS INTEGER) AS id_deputado, nome::VARCHAR AS nome, siglaPartido::VARCHAR AS partido,
       siglaUf::VARCHAR AS uf, TRY_CAST(idLegislatura AS INTEGER) AS legislatura,
       urlFoto::VARCHAR AS url_foto, email::VARCHAR AS email
FROM read_json('{raw}', format='newline_delimited', columns={{
    'id':'VARCHAR','nome':'VARCHAR','siglaPartido':'VARCHAR','siglaUf':'VARCHAR',
    'idLegislatura':'VARCHAR','urlFoto':'VARCHAR','email':'VARCHAR'}}, ignore_errors=true);
"""

# Status atual (GET /deputados/{id} → ultimoStatus). Só "Exercício" entra no painel;
# suplentes que já devolveram o mandato, licenciados e afastados ficam fora do custo.
SQL_STATUS = """
CREATE OR REPLACE TABLE status AS
SELECT TRY_CAST(id AS INTEGER) AS id_deputado, situacao::VARCHAR AS situacao,
       condicao_eleitoral::VARCHAR AS condicao_eleitoral,
       TRY_CAST(left(data_status::VARCHAR, 10) AS DATE) AS data_status
FROM read_json('{raw}', format='newline_delimited', columns={{
    'id':'VARCHAR','situacao':'VARCHAR','condicao_eleitoral':'VARCHAR','data_status':'VARCHAR',
    'nome_eleitoral':'VARCHAR','partido':'VARCHAR','uf':'VARCHAR'}}, ignore_errors=true);
CREATE OR REPLACE TABLE deputados AS
SELECT d.*, s.situacao, s.condicao_eleitoral, s.data_status
FROM deputados d LEFT JOIN status s USING (id_deputado);
"""

# A API devolve valores já numéricos; o CSV anual usa string (às vezes com vírgula).
SQL_CEAP_API = """
CREATE OR REPLACE TABLE ceap AS
SELECT TRY_CAST(idDeputado AS INTEGER) AS id_deputado, TRY_CAST(ano AS INTEGER) AS ano,
       TRY_CAST(mes AS INTEGER) AS mes,
       tipoDespesa::VARCHAR AS tipo_despesa, nomeFornecedor::VARCHAR AS fornecedor,
       cnpjCpfFornecedor::VARCHAR AS cnpj_cpf_fornecedor,
       TRY_CAST(left(dataDocumento::VARCHAR, 10) AS DATE) AS data_documento,
       TRY_CAST(valorDocumento AS DOUBLE) AS valor_documento,
       TRY_CAST(valorGlosa AS DOUBLE)     AS valor_glosa,
       TRY_CAST(valorLiquido AS DOUBLE)   AS valor_liquido,
       urlDocumento::VARCHAR AS url_documento
FROM read_json('{raw}', format='newline_delimited', columns={{
    'idDeputado':'VARCHAR','ano':'VARCHAR','mes':'VARCHAR','tipoDespesa':'VARCHAR',
    'nomeFornecedor':'VARCHAR','cnpjCpfFornecedor':'VARCHAR','dataDocumento':'VARCHAR',
    'valorDocumento':'VARCHAR','valorGlosa':'VARCHAR','valorLiquido':'VARCHAR','urlDocumento':'VARCHAR'}},
    ignore_errors=true);
"""

SQL_CEAP_BULK = """
CREATE OR REPLACE TABLE ceap AS
SELECT TRY_CAST(ideCadastro AS INTEGER) AS id_deputado, TRY_CAST(numAno AS INTEGER) AS ano,
       TRY_CAST(numMes AS INTEGER) AS mes,
       txtDescricao AS tipo_despesa, txtFornecedor AS fornecedor,
       regexp_replace(txtCNPJCPF, '[^0-9]', '', 'g') AS cnpj_cpf_fornecedor,
       TRY_CAST(left(datEmissao, 10) AS DATE) AS data_documento,
       TRY_CAST(replace(vlrDocumento, ',', '.') AS DOUBLE) AS valor_documento,
       TRY_CAST(replace(vlrGlosa, ',', '.') AS DOUBLE)     AS valor_glosa,
       TRY_CAST(replace(vlrLiquido, ',', '.') AS DOUBLE)   AS valor_liquido,
       urlDocumento AS url_documento
FROM read_json('{raw}', format='newline_delimited', columns={{
    'ideCadastro':'VARCHAR','numAno':'VARCHAR','numMes':'VARCHAR','txtDescricao':'VARCHAR',
    'txtFornecedor':'VARCHAR','txtCNPJCPF':'VARCHAR','datEmissao':'VARCHAR','vlrDocumento':'VARCHAR',
    'vlrGlosa':'VARCHAR','vlrLiquido':'VARCHAR','urlDocumento':'VARCHAR'}}, ignore_errors=true)
WHERE ideCadastro IS NOT NULL AND ideCadastro <> '';
-- Linhas sem ideCadastro são lideranças partidárias/do governo (cota coletiva): ficam fora
-- do custo individual. O CSV traz a coluna `cpf` do parlamentar; ela NÃO é carregada.
"""

# Custo por deputado no ano = subsídio (fixo, 12 meses + 13º + 1/3 férias)
#                           + CEAP (gasto real, líquido de glosas)
#                           + verba de gabinete (TETO; estimativa superior)
# Auxílio-moradia e cotas do teto da CEAP ficam em colunas separadas.
SQL_CUSTO = """
CREATE OR REPLACE TABLE custo AS
WITH ceap_agg AS (
  SELECT id_deputado,
         SUM(valor_liquido)  AS ceap_liquido,
         SUM(valor_glosa)    AS ceap_glosa,
         COUNT(*)            AS ceap_documentos,
         COUNT(DISTINCT mes) AS meses_com_ceap
  FROM ceap WHERE ano = {ano} GROUP BY id_deputado
)
SELECT d.id_deputado, d.nome, d.partido, d.uf, d.url_foto,
       {ano}::INTEGER                     AS ano,
       {meses}::INTEGER                   AS meses_considerados,
       {subsidio_ano}::DOUBLE             AS subsidio,
       COALESCE(c.ceap_liquido, 0)        AS ceap,
       COALESCE(c.ceap_glosa, 0)          AS ceap_glosa,
       COALESCE(c.ceap_documentos, 0)     AS ceap_documentos,
       COALESCE(c.meses_com_ceap, 0)      AS meses_com_ceap,
       {gabinete_ano}::DOUBLE             AS verba_gabinete_teto,
       {moradia_ano}::DOUBLE              AS auxilio_moradia_max,
       {subsidio_ano} + COALESCE(c.ceap_liquido, 0) + {gabinete_ano} AS custo_total_estimado,
       round(({subsidio_ano} + COALESCE(c.ceap_liquido, 0) + {gabinete_ano}) / {meses}, 2) AS custo_mensal_medio,
       -- Anual: subsídio e gabinete são contratuais (12 meses cheios + 13º/férias);
       -- a cota é extrapolada pela média mensal observada. Para anos fechados = custo_total_estimado.
       round({subsidio_12} + COALESCE(c.ceap_liquido, 0) * 12.0 / {meses} + {gabinete_12}, 2) AS custo_anual_projetado
FROM deputados d LEFT JOIN ceap_agg c USING (id_deputado)
WHERE d.situacao = 'Exercício' OR d.situacao IS NULL
ORDER BY custo_total_estimado DESC;
"""

# Detalhe "no que gastou": por categoria e por fornecedor (com link para a NF).
SQL_DETALHE = """
CREATE OR REPLACE TABLE ceap_categoria AS
SELECT id_deputado, tipo_despesa, round(sum(valor_liquido),2) AS valor, count(*) AS documentos
FROM ceap WHERE ano = {ano} GROUP BY ALL ORDER BY id_deputado, valor DESC;

CREATE OR REPLACE TABLE ceap_fornecedor AS
SELECT id_deputado, cnpj_cpf_fornecedor AS cnpj_cpf, any_value(fornecedor) AS fornecedor,
       round(sum(valor_liquido),2) AS valor, count(*) AS documentos,
       any_value(url_documento) AS exemplo_nota
FROM ceap WHERE ano = {ano} GROUP BY ALL ORDER BY id_deputado, valor DESC;

-- Fornecedores que atendem muitos deputados: ponto de partida para cruzamentos.
CREATE OR REPLACE TABLE fornecedor_rede AS
SELECT cnpj_cpf_fornecedor AS cnpj_cpf, any_value(fornecedor) AS fornecedor,
       count(DISTINCT id_deputado) AS deputados, round(sum(valor_liquido),2) AS valor
FROM ceap WHERE ano = {ano} GROUP BY ALL HAVING deputados >= 5 ORDER BY valor DESC;
"""


def meses_no_ano(ano: int, hoje: date) -> int:
    """Meses decorridos do ano (para anos passados, 12)."""
    if ano < hoje.year:
        return 12
    return hoje.month  # mês corrente conta parcialmente — ver metodologia §4


def subsidio_no_ano(ano: int, meses: int) -> float:
    """Soma do subsídio mês a mês (o valor muda em fevereiro) + proporcional de 13º/férias."""
    total = sum(C.subsidio_mensal_em(date(ano, m, 1)) for m in range(1, meses + 1))
    extra = (C.SUBSIDIOS_POR_ANO - 12) * C.subsidio_mensal_em(date(ano, 12, 1)) * meses / 12
    return round(total + extra, 2)


def run(ano: int, fonte: str, legislatura: int = C.LEGISLATURA_ATUAL, hoje: date | None = None) -> Path:
    hoje = hoje or date.today()
    PQ.mkdir(parents=True, exist_ok=True); PUB.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()

    con.execute(SQL_DEPUTADOS.format(raw=RAW / f"deputados_leg{legislatura}.jsonl.gz"))
    status_raw = RAW / f"deputados_status_leg{legislatura}.jsonl.gz"
    if status_raw.exists():
        con.execute(SQL_STATUS.format(raw=status_raw))
    else:
        log.warning("sem deputados_status: todos os %s da legislatura entram (inclui suplentes)",
                    con.execute("SELECT count(*) FROM deputados").fetchone()[0])
        con.execute("ALTER TABLE deputados ADD COLUMN situacao VARCHAR; "
                    "ALTER TABLE deputados ADD COLUMN condicao_eleitoral VARCHAR; "
                    "ALTER TABLE deputados ADD COLUMN data_status DATE")
    if fonte == "api":
        con.execute(SQL_CEAP_API.format(raw=RAW / f"despesas_api_{ano}.jsonl.gz"))
    else:
        con.execute(SQL_CEAP_BULK.format(raw=RAW / f"ceap_bulk_{ano}.jsonl.gz"))

    meses = meses_no_ano(ano, hoje)
    params = dict(
        ano=ano, meses=meses,
        subsidio_ano=subsidio_no_ano(ano, meses),
        subsidio_12=subsidio_no_ano(ano, 12),
        gabinete_ano=round(C.VERBA_GABINETE_TETO_MENSAL * meses, 2),
        gabinete_12=round(C.VERBA_GABINETE_TETO_MENSAL * 12, 2),
        moradia_ano=round(C.AUXILIO_MORADIA_MENSAL * meses, 2),
    )
    con.execute(SQL_CUSTO.format(**params))

    con.execute(f"COPY deputados TO '{PQ / 'deputados.parquet'}' (FORMAT PARQUET)")
    con.execute(f"COPY ceap TO '{PQ / f'ceap_{ano}.parquet'}' (FORMAT PARQUET)")
    con.execute(f"COPY custo TO '{PQ / f'custo_deputado_{ano}.parquet'}' (FORMAT PARQUET)")

    con.execute(SQL_DETALHE.format(ano=ano))
    for t in ("ceap_categoria", "ceap_fornecedor", "fornecedor_rede"):
        con.execute(f"COPY {t} TO '{PQ / f'{t}_{ano}.parquet'}' (FORMAT PARQUET)")
        rows_t = con.execute(f"SELECT * FROM {t}").fetchall(); cols_t = [d[0] for d in con.description]
        (PUB / f"{t}_{ano}.json").write_text(json.dumps([dict(zip(cols_t, r)) for r in rows_t], ensure_ascii=False, default=str), encoding="utf-8")

    rows = con.execute("SELECT * FROM custo").fetchall()
    cols = [d[0] for d in con.description]
    out = PUB / f"custo_deputado_{ano}.json"
    out.write_text(json.dumps([dict(zip(cols, r)) for r in rows], ensure_ascii=False, default=str), encoding="utf-8")

    meta = {
        "ano": ano, "fonte_ceap": fonte, "gerado_em": hoje.isoformat(),
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "meses_considerados": meses, "deputados": len(rows),
        "deputados_na_legislatura": con.execute("SELECT count(*) FROM deputados").fetchone()[0],
        "filtro_situacao": "Exercício" if status_raw.exists() else None,
        "premissas": {
            "subsidio_mensal_vigente": C.subsidio_mensal_em(hoje),
            "subsidios_por_ano": C.SUBSIDIOS_POR_ANO,
            "verba_gabinete_teto_mensal": C.VERBA_GABINETE_TETO_MENSAL,
            "verba_gabinete_verificada_em": C.VERBA_GABINETE_VERIFICADA_EM.isoformat(),
            "auxilio_moradia_mensal": C.AUXILIO_MORADIA_MENSAL,
            "auxilio_moradia_no_total": C.INCLUIR_AUXILIO_MORADIA_NO_TOTAL,
        },
        "totais": con.execute(
            "SELECT round(sum(ceap),2), round(sum(custo_total_estimado),2) FROM custo"
        ).fetchone(),
        "custo_mensal_medio_por_deputado": con.execute("SELECT round(avg(custo_mensal_medio),2) FROM custo").fetchone()[0],
        "custo_anual_projetado_total": con.execute("SELECT round(sum(custo_anual_projetado),2) FROM custo").fetchone()[0],
        "anual_e_projecao": meses < 12,
    }
    (PUB / f"meta_{ano}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("custo_deputado_%d: %d deputados; CEAP total R$ %.2f", ano, len(rows), meta["totais"][0])
    return out


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, required=True)
    ap.add_argument("--fonte", choices=["api", "bulk"], default="api")
    ap.add_argument("--legislatura", type=int, default=C.LEGISLATURA_ATUAL)
    a = ap.parse_args()
    run(a.ano, a.fonte, a.legislatura)


if __name__ == "__main__":
    main()
