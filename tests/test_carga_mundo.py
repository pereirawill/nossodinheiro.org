"""Carga no mundo: montagem do JSON a partir das linhas da OCDE, sem rede."""
from etl.carga_mundo import extract


def _linha(iso, nome, ano, valor):
    return {"REF_AREA": iso, "Reference area": nome, "TIME_PERIOD": ano, "OBS_VALUE": valor}


def test_montar_ignora_vazio_separa_media_e_traduz_nome(monkeypatch, tmp_path):
    nomes = tmp_path / "paises_pt.json"
    nomes.write_text('{"BRA": "Brasil"}', encoding="utf-8")
    monkeypatch.setattr(extract, "NOMES_PT", nomes)
    linhas = [_linha("BRA", "Brazil", "2023", "31.66"), _linha("BRA", "Brazil", "2024", "33.68"),
              _linha("BRA", "Brazil", "2025", ""),                      # sem valor: não entra
              _linha("USA", "United States", "2024", "25.62"),
              _linha("OECD_REP", "OECD average country", "2024", "34.06")]
    got = extract.montar(linhas)
    assert got["paises"]["BRA"]["nome"] == "Brasil" and got["paises"]["BRA"]["ultimo_ano"] == "2024"
    assert got["paises"]["BRA"]["ultimo"] == 33.68
    assert got["paises"]["USA"]["nome"] == "United States"         # sem tradução, fica o nome da OCDE
    assert "OECD_REP" not in got["paises"] and got["ocde_media"]["ultimo"] == 34.06
