"""Economia: leitura do PIB (SIDRA), da Selic (SGS, em fatias) e do RTN, sem rede."""
import io

import httpx
import pytest

from etl.economia import extract


def test_sgs_janela_repete_quando_vem_html(monkeypatch):
    """O SGS devolve 502, ou HTML com status 200, de forma intermitente: a coleta tem de insistir."""
    chamadas = {"n": 0}

    def handler(req: httpx.Request) -> httpx.Response:
        chamadas["n"] += 1
        if chamadas["n"] < 3:
            return httpx.Response(200, text="<html>erro</html>", headers={"content-type": "text/html"})
        return httpx.Response(200, json=[{"data": "01/01/2020", "valor": "4.50"}])

    monkeypatch.setattr(extract.time, "sleep", lambda s: None)
    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        got = extract._sgs_janela(c, 432, 2015, 2023)
    assert got == [{"data": "01/01/2020", "valor": "4.50"}] and chamadas["n"] == 3


def test_selic_guarda_so_as_mudancas(monkeypatch):
    dias = [{"data": f"0{i}/01/2020", "valor": "4.50"} for i in range(1, 5)] + \
           [{"data": "05/01/2020", "valor": "3.75"}, {"data": "06/01/2020", "valor": "3.75"}]
    monkeypatch.setattr(extract, "_sgs_janela", lambda c, s, de, ate: dias if de == 1996 else [])
    got = extract.selic(httpx.Client())
    assert [p["valor"] for p in got] == [4.5, 3.75]          # a série diária é repetitiva; só as mudanças entram


def test_resultado_governo_le_primario_abaixo_da_linha_e_nominal(monkeypatch):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "2.1"
    ws.append(["Tabela 2.1"])
    ws.append(["R$ Milhões"])
    ws.append(["Discriminação", 2024, 2025])
    ws.append(["5. RESULTADO PRIMÁRIO GOVERNO CENTRAL - ACIMA DA LINHA", -42923.7, -61694.3])
    ws.append(["7. DISCREPÂNCIA ESTATÍSTICA", -2012.2, 1967.3])
    ws.append(["8. RESULTADO PRIMÁRIO DO GOVERNO CENTRAL - ABAIXO DA LINHA", -45364.3, -58687.1])
    ws.append(["10. RESULTADO NOMINAL DO GOVERNO CENTRAL", -900570.7, -950567.0])
    buf = io.BytesIO()
    wb.save(buf)
    monkeypatch.setattr(extract, "_planilha_rtn", lambda c: buf.getvalue())
    got = extract.resultado_governo(httpx.Client())
    # é a linha 8 que vale, não a 5 (outra medição) nem a 7 (discrepância estatística)
    assert got["2025"]["primario"] == -58_687_100_000.0
    assert got["2025"]["nominal"] == -950_567_000_000.0
