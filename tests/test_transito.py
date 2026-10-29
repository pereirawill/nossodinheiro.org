"""Trânsito: leitura da tabela 4408 do SIDRA (indicador ODS 3.6.1), sem rede."""
import httpx

from etl.transito import extract


CAB = {"NC": "Nível Territorial (Código)", "MN": "Unidade de Medida", "V": "Valor",
       "D1C": "Brasil (Código)", "D1N": "Brasil", "D2C": "Variável (Código)", "D2N": "Variável",
       "D3C": "Ano (Código)", "D3N": "Ano", "D4C": "Sexo (Código)", "D4N": "Sexo",
       "D5C": "Grupo de idade (Código)", "D5N": "Grupo de idade"}


def _linha(valor, ano="2024", var="11728", sexo="Total", idade="Total", uf=None):
    l = {"NC": "1", "MN": "Óbitos", "V": valor, "D1C": "1", "D1N": "Brasil", "D2C": var,
         "D2N": "Óbitos por lesões de trânsito", "D3C": ano, "D3N": ano, "D4C": "6794", "D4N": sexo,
         "D5C": "95253", "D5N": idade}
    if uf:
        l = {**l, "D1C": uf, "D1N": "UF"}
    return l


def test_num_descarta_marcadores_de_ausencia():
    assert extract._num("37150") == 37150.0 and extract._num("17,5") == 17.5
    assert extract._num("-") is None and extract._num("...") is None and extract._num("-1") is None


def test_run_monta_serie_estados_sexo_e_idade(tmp_path, monkeypatch):
    monkeypatch.setattr(extract, "PUB", tmp_path)

    def handler(req: httpx.Request) -> httpx.Response:
        u = str(req.url)
        if "periodos" in u:
            return httpx.Response(200, json=[{"id": "2023"}, {"id": "2024"}])
        cab = dict(CAB)
        if "/n3/" in u:                                   # estados
            cab["D1C"], cab["D1N"] = "Unidade da Federação (Código)", "Unidade da Federação"
            v = "9734" if "9734" in u else "11728"
            linhas = [_linha("1000" if v == "11728" else "20,5", var=v, uf="35"),
                      _linha("500" if v == "11728" else "10,2", var=v, uf="33")]
            return httpx.Response(200, json=[cab] + linhas)
        if "/c58/all" in u:                               # faixas de idade
            return httpx.Response(200, json=[cab, _linha("4110", idade="20 a 24 anos"),
                                             _linha("37150", idade="Total")])
        if "/c2/4/" in u:
            return httpx.Response(200, json=[cab, _linha("30602", sexo="Homens")])
        if "/c2/5/" in u:
            return httpx.Response(200, json=[cab, _linha("6539", sexo="Mulheres")])
        v = "9734" if "9734" in u else "11728"            # série do Brasil
        return httpx.Response(200, json=[cab,
                                         _linha("28995" if v == "11728" else "16,6", ano="2023", var=v),
                                         _linha("37150" if v == "11728" else "17,5", ano="2024", var=v)])

    pronto = httpx.Client(transport=httpx.MockTransport(handler))   # criado antes do patch, senão chama a si mesmo
    monkeypatch.setattr(extract.httpx, "Client", lambda **kw: pronto)
    import json
    dados = json.loads(extract.run().read_text(encoding="utf-8"))
    assert dados["ultimo_ano"] == 2024
    assert dados["serie"]["2024"] == {"obitos": 37150.0, "taxa": 17.5}
    assert dados["por_sexo"] == {"homens": 30602.0, "mulheres": 6539.0}
    assert dados["por_idade"] == {"20 a 24 anos": 4110.0}      # a linha "Total" não vira faixa
    assert [e["sigla"] for e in dados["estados"]] == ["SP", "RJ"]   # ordenado pela taxa, maior primeiro
    assert dados["estados"][0]["obitos"] == 1000.0 and dados["estados"][0]["taxa"] == 20.5
