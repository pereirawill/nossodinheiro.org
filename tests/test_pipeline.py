"""Smoke test do pipeline com fixtures SINTÉTICAS no schema real da API v2.
Não valida números reais — só garante que extract→transform→chart não quebra.

    python -m pytest tests/ -q
"""
import gzip, json, shutil
from datetime import date
from pathlib import Path

import duckdb

FIX = Path(__file__).parent / "fixtures"

DEPUTADOS = [  # schema de GET /deputados?idLegislatura=57
    {"id": 1001, "uri": "", "nome": "DEPUTADO EXEMPLO A", "siglaPartido": "PXA", "uriPartido": "",
     "siglaUf": "RS", "idLegislatura": 57, "urlFoto": "", "email": None},
    {"id": 1002, "uri": "", "nome": "DEPUTADA EXEMPLO B", "siglaPartido": "PXB", "uriPartido": "",
     "siglaUf": "DF", "idLegislatura": 57, "urlFoto": "", "email": None},
    {"id": 1003, "uri": "", "nome": "DEPUTADO EXEMPLO C", "siglaPartido": "PXA", "uriPartido": "",
     "siglaUf": "RR", "idLegislatura": 57, "urlFoto": "", "email": None},
]
DESPESAS = [  # schema de GET /deputados/{id}/despesas  (+ idDeputado injetado pelo extract)
    {"ano": 2026, "mes": 1, "tipoDespesa": "PASSAGEM AÉREA - SIGEPA", "codDocumento": 1, "tipoDocumento": "Nota Fiscal",
     "codTipoDocumento": 0, "dataDocumento": "2026-01-15", "numDocumento": "1", "valorDocumento": 1500.0,
     "urlDocumento": "", "nomeFornecedor": "CIA AÉREA", "cnpjCpfFornecedor": "00000000000191",
     "valorLiquido": 1500.0, "valorGlosa": 0.0, "numRessarcimento": "", "codLote": 1, "parcela": 0, "idDeputado": 1001},
    {"ano": 2026, "mes": 2, "tipoDespesa": "DIVULGAÇÃO DA ATIVIDADE PARLAMENTAR.", "codDocumento": 2, "tipoDocumento": "Nota Fiscal",
     "codTipoDocumento": 0, "dataDocumento": "2026-02-10", "numDocumento": "2", "valorDocumento": 12000.0,
     "urlDocumento": "", "nomeFornecedor": "AGÊNCIA X", "cnpjCpfFornecedor": "00000000000191",
     "valorLiquido": 11000.0, "valorGlosa": 1000.0, "numRessarcimento": "", "codLote": 1, "parcela": 0, "idDeputado": 1001},
    {"ano": 2026, "mes": 1, "tipoDespesa": "COMBUSTÍVEIS E LUBRIFICANTES.", "codDocumento": 3, "tipoDocumento": "Recibo",
     "codTipoDocumento": 1, "dataDocumento": "2026-01-20", "numDocumento": "3", "valorDocumento": 800.0,
     "urlDocumento": "", "nomeFornecedor": "POSTO Y", "cnpjCpfFornecedor": "00000000000191",
     "valorLiquido": 800.0, "valorGlosa": 0.0, "numRessarcimento": "", "codLote": 1, "parcela": 0, "idDeputado": 1003},
]


def _jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def test_pipeline(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _jsonl(Path("data/raw/deputados_leg57.jsonl.gz"), DEPUTADOS)
    _jsonl(Path("data/raw/despesas_api_2026.jsonl.gz"), DESPESAS)

    from etl.camara import transform, chart, config as C
    out = transform.run(2026, "api", hoje=date(2026, 10, 26))
    rows = json.loads(out.read_text(encoding="utf-8"))
    by_id = {r["id_deputado"]: r for r in rows}

    assert len(rows) == 3
    assert by_id[1001]["ceap"] == 12500.0            # líquido, não bruto
    assert by_id[1001]["ceap_glosa"] == 1000.0
    assert by_id[1002]["ceap"] == 0.0                # sem despesa → zero, não NULL
    assert rows[0]["meses_considerados"] == 10
    # subsídio: R$ 46.366,19 desde fev/2025 (DL 172/2022) → 10 meses cheios em 2026
    esperado = 10 * 46366.19 + (C.SUBSIDIOS_POR_ANO - 12) * 46366.19 * 10 / 12
    assert abs(by_id[1001]["subsidio"] - round(esperado, 2)) < 0.01
    assert abs(by_id[1001]["custo_total_estimado"] - (by_id[1001]["subsidio"] + 12500.0 + C.VERBA_GABINETE_TETO_MENSAL * 10)) < 0.01

    # parquet legível e sem coluna de CPF do parlamentar
    cols = [c[0] for c in duckdb.sql("SELECT * FROM 'data/parquet/ceap_2026.parquet'").description]
    assert "cpf" not in cols

    png = chart.render(2026, 20, "deputado")
    assert png.exists() and png.stat().st_size > 10_000
