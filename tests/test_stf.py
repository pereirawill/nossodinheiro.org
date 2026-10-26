"""Smoke test do transform do STF com fixture SINTÉTICA no schema do CSV de remuneração."""
import gzip, json
from datetime import date
from pathlib import Path

COL = "Remuneração Bruta após o teto constitucional somada com outras verbas"


def _linha(nome, mat, unidade, situacao, bruto, mes, origem, cargo="ANALISTA JUDICIÁRIO"):
    return {"Matrícula": mat, "Nome": nome, "Cargo Efetivo": cargo, "Cargo Comissionado": "", "Nome da Função": "",
            "Nome da Unidade": unidade, "Situação Funcional": situacao, COL: str(bruto), "Remuneração Liquida": str(bruto * 0.7),
            "ano": 2026, "mes": mes, "origem": origem, "unidade_id": "1"}


FOLHA = []
for mes in (1, 2):
    FOLHA += [
        _linha("MINISTRA EXEMPLO", "1", "GABINETE MINISTRA EXEMPLO", "MINISTRO", 50000.0, mes, "ministros", "MINISTRO"),
        _linha("MINISTRO APOSENTADO", "2", "", "APOSENTADO MINISTRO", 60000.0, mes, "ministros", "MINISTRO"),
        _linha("MINISTRA EXEMPLO", "1", "GABINETE MINISTRA EXEMPLO", "MINISTRO", 50000.0, mes, "gabinete", "MINISTRO"),  # ministro também vem na lotação
        _linha("SERVIDOR A", "10", "GABINETE MINISTRA EXEMPLO", "EFETIVO", 20000.0, mes, "gabinete"),
        _linha("SERVIDOR B", "11", "GABINETE MINISTRA EXEMPLO", "SEM VINCULO EFETIVO", 10000.0 if mes == 1 else 0.0, mes, "gabinete"),
    ]


def test_transform_stf(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p = Path("data/raw/stf_folha_2026.jsonl.gz"); p.parent.mkdir(parents=True)
    with gzip.open(p, "wt", encoding="utf-8") as f:
        for r in FOLHA:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    from etl.stf import transform
    out = transform.run(2026, hoje=date(2026, 10, 26))
    rows = json.loads(out.read_text(encoding="utf-8"))
    assert len(rows) == 1                       # aposentado não vira linha
    r = rows[0]
    assert r["meses_com_folha"] == 2
    assert r["remuneracao_bruta"] == 100000.0 and r["remuneracao_mensal_media"] == 50000.0
    assert r["gabinete"] == 50000.0             # 20k+10k (jan) + 20k+0 (fev); o ministro não é contado no gabinete
    assert r["gabinete_pessoas_media"] == 2.0
    assert r["custo_total_estimado"] == 150000.0 and r["custo_mensal_medio"] == 75000.0
    assert r["custo_anual_projetado"] == 900000.0
    meta = json.loads(Path("data/public/meta_stf_2026.json").read_text(encoding="utf-8"))
    assert meta["aposentados"] == {"quantidade_ultimo_mes": 1, "bruto_ultimo_mes": 60000.0, "bruto_acumulado": 120000.0}
    assert meta["ultimo_mes"] == 2 and meta["anual_e_projecao"] is True
