"""Indústria: leitura das séries do Banco Mundial e da produção física do IBGE, sem rede."""
import httpx

from etl.industria import extract


def test_agregado_de_renda_alta_casa_pelo_id_do_pais():
    """O Banco Mundial devolve countryiso3code vazio no grupo de renda alta; sem isso o grupo some em silêncio."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"page": 1}, [
            {"countryiso3code": "BRA", "country": {"id": "BR"}, "date": "2024", "value": 12.1},
            {"countryiso3code": "", "country": {"id": "XD"}, "date": "2024", "value": 12.0},
            {"countryiso3code": "", "country": {"id": "ZZ"}, "date": "2024", "value": 9.9},
        ]])

    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        got = extract._wb(c, "NV.IND.MANF.ZS", "BRA;XD")
    assert got["BRA"]["2024"] == 12.1 and got["HIC"]["2024"] == 12.0
    assert "ZZ" not in got                     # grupo que não está no mapa não entra


def test_zero_dos_primeiros_anos_nao_vira_participacao(monkeypatch):
    """Nos anos sem dado o Banco Mundial publica 0,00 — e participação setorial zero não existe."""
    monkeypatch.setattr(extract, "_wb", lambda c, cod, paises: {
        "BRA": {"1962": 0.0, "1979": 46.13, "1995": 14.54, "2025": 11.77}, "WLD": {"2025": 14.9}})
    got = extract.series(httpx.Client())
    anos = got["transformacao_pct_va"]["brasil"]
    assert "1962" not in anos and anos["1979"] == 46.13       # o zero sai, o ruído de preço fica no arquivo
    assert got["transformacao_pct_va"]["precos_correntes"] is True


def test_producao_fisica_so_usa_ano_com_doze_meses():
    """O ano em curso tem menos meses; entrar na média anual compararia 8 meses com 12."""
    linhas = [{"D4C": "129316", "D3C": f"2024{m:02d}", "V": "100"} for m in range(1, 13)]
    linhas += [{"D4C": "129316", "D3C": f"2025{m:02d}", "V": "110"} for m in range(1, 9)]

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"D1C": "cab"}, *linhas])

    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        got = extract.producao_fisica(c)
    assert got["129316"]["anual"] == {"2024": 100.0}
    assert got["129316"]["parcial"] == {"2025": 110.0}
