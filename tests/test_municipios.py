"""Smoke test do transform de municípios com fixtures SINTÉTICAS no schema do extrator (sem rede)."""
import gzip, json
from pathlib import Path

from etl.municipios.extract import normalizar


def _jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _dca(cod, ente, uf, esfera, pop, funcoes: dict):
    out = []
    for coluna, mult in (("Despesas Pagas", 1.0), ("Despesas Empenhadas", 1.1)):
        out.append({"cod_ibge": cod, "ente": ente, "uf": uf, "esfera": esfera, "populacao": pop, "exercicio": 2025, "coluna": coluna,
                    "funcao_cod": "00", "funcao": "Total", "valor": sum(v for _, v in funcoes.values()) * mult})
        for c, (nome, v) in funcoes.items():
            out.append({"cod_ibge": cod, "ente": ente, "uf": uf, "esfera": esfera, "populacao": pop, "exercicio": 2025, "coluna": coluna,
                        "funcao_cod": c, "funcao": nome, "valor": v * mult})
    return out


def test_normalizar():
    assert normalizar("São João d'Aliança") == "SAO JOAO D ALIANCA"


def test_transform(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _jsonl(Path("data/raw/siconfi_entes.jsonl.gz"), [
        {"cod_ibge": 1, "ente": "Cidade Grande", "uf": "XX", "esfera": "M", "capital": True, "regiao": "SU", "populacao": 100_000},
        {"cod_ibge": 2, "ente": "Vila Pequena", "uf": "XX", "esfera": "M", "capital": False, "regiao": "SU", "populacao": 5_000},
        {"cod_ibge": 3, "ente": "Sem Contas", "uf": "XX", "esfera": "M", "capital": False, "regiao": "SU", "populacao": 8_000},
        {"cod_ibge": 99, "ente": "Estado XX", "uf": "XX", "esfera": "E", "capital": False, "regiao": "SU", "populacao": 1_000_000},
    ])
    f1 = {"01": ("Legislativa", 2_000_000.0), "10": ("Saúde", 30_000_000.0), "12": ("Educação", 25_000_000.0), "04": ("Administração", 10_000_000.0)}
    f2 = {"01": ("Legislativa", 400_000.0), "10": ("Saúde", 3_000_000.0)}
    fe = {"01": ("Legislativa", 90_000_000.0), "02": ("Judiciária", 300_000_000.0), "10": ("Saúde", 500_000_000.0)}
    _jsonl(Path("data/raw/siconfi_dca_2025.jsonl.gz"), _dca(1, "Cidade Grande", "XX", "M", 100_000, f1) + _dca(2, "Vila Pequena", "XX", "M", 5_000, f2)
           + [{"cod_ibge": 3, "erro": "sem DCA"}] + _dca(99, "Estado XX", "XX", "E", 1_000_000, fe))
    _jsonl(Path("data/raw/tse_vagas_2024.jsonl.gz"), [{"ano": 2024, "uf": "XX", "cod_tse": "1", "municipio": "CIDADE GRANDE", "municipio_norm": "CIDADE GRANDE", "vagas": 20},
                                                       {"ano": 2024, "uf": "XX", "cod_tse": "2", "municipio": "VILA PEQUENA", "municipio_norm": "VILA PEQUENA", "vagas": 9}])
    from etl.municipios import transform
    transform.run(2025, 2024)
    mun = {m["cod_ibge"]: m for m in json.loads(Path("data/public/municipios_2025.json").read_text(encoding="utf-8"))}
    assert set(mun) == {1, 2}                                   # sem DCA fica fora, não zero
    g = mun[1]
    assert g["pago_legislativo"] == 2_000_000.0 and g["pago_total"] == 67_000_000.0 and g["empenhado_total"] == 73_700_000.0
    assert g["por_hab_legislativo"] == 20.0 and g["por_vereador_legislativo"] == 100_000.0 and g["vereadores"] == 20
    assert abs(g["pct_legislativo"] - 2_000_000 / 67_000_000) < 1e-4   # arredondado a 4 casas and g["faixa"] == "50 a 100 mil" and g["capital"] is True
    assert mun[2]["por_hab_legislativo"] == 80.0 and mun[2]["faixa"] == "até 10 mil"
    est = json.loads(Path("data/public/estados_2025.json").read_text(encoding="utf-8"))
    assert len(est) == 1 and est[0]["pago_legislativa"] == 90_000_000.0 and est[0]["por_hab_judiciaria"] == 300.0
    meta = json.loads(Path("data/public/municipios_meta_2025.json").read_text(encoding="utf-8"))
    assert meta["municipios_total"] == 3 and meta["municipios_com_dca"] == 2 and meta["totais"]["vereadores"] == 29
    assert meta["medianas_por_faixa"]["até 10 mil"]["por_hab_legislativo"] == 80.0
