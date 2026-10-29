"""Desenvolvimento por estado: leitura das tabelas do Censo e do ODS por UF, sem rede."""
import json

import httpx

from etl.desenvolvimento import extract


CAB = {"NC": "Nível Territorial (Código)", "V": "Valor", "MN": "Unidade de Medida",
       "D1C": "Unidade da Federação (Código)", "D1N": "Unidade da Federação",
       "D2C": "Variável (Código)", "D3N": "Ano"}


def _linha(uf, valor):
    return {"NC": "3", "V": valor, "MN": "Pessoas", "D1C": uf, "D1N": "UF", "D2C": "138", "D3N": "1991"}


def test_por_uf_soma_categorias_da_mesma_consulta():
    # a consulta de "médio completo ou mais" traz duas categorias por UF; elas se somam
    corpo = [CAB, _linha("35", "100"), _linha("35", "50"), _linha("33", "40"), _linha("99", "999")]
    c = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=corpo)))
    with c:
        got = extract._por_uf(c, 142, 138, "1991", "/c71/1133,1137")
    assert got == {"35": 150.0, "33": 40.0}          # o código 99 não é UF e fica fora


def test_educacao_por_uf_vira_percentual(monkeypatch):
    def handler(req: httpx.Request) -> httpx.Response:
        parte = "1133,1137" in str(req.url) or "9495,99713" in str(req.url)
        valor = "30" if parte else "100"
        return httpx.Response(200, json=[CAB, _linha("35", valor), _linha("33", valor)])
    c = httpx.Client(transport=httpx.MockTransport(handler))
    with c:
        got = extract.educacao_por_uf(c)
    assert got["1991"] == {"SP": 30.0, "RJ": 30.0}
    assert set(got) == {"1991", "2000", "2010", "2022"}


def test_run_escreve_json_com_as_duas_dimensoes(tmp_path, monkeypatch):
    monkeypatch.setattr(extract, "PUB", tmp_path)

    def handler(req: httpx.Request) -> httpx.Response:
        u = str(req.url)
        if "periodos" in u:
            return httpx.Response(200, json=[{"id": "2000"}, {"id": "2024"}])
        if "/t/6606/" in u:
            return httpx.Response(200, json=[CAB, _linha("35", "41.0"), _linha("33", "25.5")])
        parte = "1133,1137" in u or "9495,99713" in u
        return httpx.Response(200, json=[CAB, _linha("35", "30" if parte else "100")])
    pronto = httpx.Client(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(extract.httpx, "Client", lambda **kw: pronto)
    dados = json.loads(extract.run().read_text(encoding="utf-8"))
    assert dados["educacao"]["anos"] == ["1991", "2000", "2010", "2022"]
    assert dados["homicidios"]["por_uf"]["2000"]["SP"] == 41.0
    assert len(dados["fora"]) >= 3                    # o que não dá para medir fica escrito
