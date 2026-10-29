"""Dívida: leitura da linha de juros nominais do RTN e agregação do estoque da DPF, sem rede."""
import io
import zipfile

import httpx
import pytest

from etl.divida import extract


def test_estoque_agrega_por_mes_indexador_e_vencimento(tmp_path, monkeypatch):
    monkeypatch.setattr(extract, "RAW", tmp_path)
    linhas = [
        "Titulo/Contrato;Vencimento do Titulo/Contrato;Valor do Estoque;Quantidade do Estoque;Mes do Estoque;"
        "Classe da Carteira;Tipo de Divida",
        "LFT 010327;01/03/2027;1.000.000,00;10,00;07/2026;Mercado;Dívida Interna",
        "LFT 010327;01/03/2027;2.000.000,00;20,00;08/2026;Mercado;Dívida Interna",
        "NTN-B 150535;15/05/2035;3.000.000,00;30,00;08/2026;Mercado;Dívida Interna",
        "LTN 010128;01/01/2028;1.500.000,00;15,00;08/2026;Mercado;Dívida Interna",
        "Global 2030;15/01/2030;500.000,00;5,00;08/2026;Mercado;Dívida Externa",
    ]
    (tmp_path / "estoque_dpf.csv").write_text("\n".join(linhas), encoding="utf-8")
    # o arquivo em cache precisa passar do tamanho mínimo para não ser rebaixado
    monkeypatch.setattr(extract.Path, "stat", lambda self: type("S", (), {"st_size": 2_000_000})())
    with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(404))) as c:
        got = extract.estoque(c)
    assert got["ultimo_mes"] == "08/2026" and got["ultimo_ano"] == 2026
    assert got["meses"][-1]["total"] == 7_000_000 and got["meses"][-1]["externa"] == 500_000
    assert got["por_indexador"]["Selic (pós-fixado)"] == 2_000_000
    assert got["por_indexador"]["IPCA"] == 3_000_000
    assert got["por_indexador"]["Prefixado"] == 1_500_000
    assert got["por_indexador"]["Câmbio (dívida externa)"] == 500_000
    # vence até o fim do ano seguinte: só a LFT de 2027
    assert got["vence_ate_o_fim_do_ano_que_vem"] == 2_000_000


def test_juros_nominais_le_a_linha_certa_e_tira_o_sinal(monkeypatch):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "2.1"
    ws.append(["Tabela 2.1"])
    ws.append(["R$ Milhões"])
    ws.append(["Discriminação", 1997, 1998])
    ws.append(["8. RESULTADO PRIMÁRIO", 100.0, 200.0])
    ws.append(["9. JUROS NOMINAIS 7/", -18_900.0, -20_000.0])
    ws.append(["10. RESULTADO NOMINAL", -18_800.0, -19_800.0])
    buf = io.BytesIO()
    wb.save(buf)
    monkeypatch.setattr(extract, "_planilha_rtn", lambda c: buf.getvalue())
    got = extract.juros_nominais(httpx.Client())
    assert got == {"1997": 18_900e6, "1998": 20_000e6}      # despesa vem negativa na planilha
