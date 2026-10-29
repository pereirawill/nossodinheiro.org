"""Preços: leitura das planilhas do SLP da ANP e a conta de minutos de trabalho, sem rede."""
import io

import httpx
import pytest

from etl.precos import extract


def _planilha(titulo: str, notas: list[str], linhas: list[tuple], cabecalho: list[str]) -> bytes:
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = titulo
    ws.append(["AGÊNCIA NACIONAL DO PETRÓLEO"])
    for n in notas:
        ws.append([n])
    ws.append(cabecalho)
    for l in linhas:
        ws.append(list(l))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


CAB_BRASIL = ["MÊS", "PRODUTO", "NÚMERO DE POSTOS PESQUISADOS", "UNIDADE DE MEDIDA",
              "PREÇO MÉDIO REVENDA", "DESVIO PADRÃO REVENDA"]


def test_tabela_acha_o_cabecalho_e_guarda_as_observacoes():
    """O cabeçalho não está numa linha fixa: as duas planilhas têm números diferentes de observações em cima."""
    from datetime import datetime
    conteudo = _planilha("BRASIL", ["Obs: a abrangência foi reduzida", "Não houve pesquisa de preços entre 18/8/20 e 17/10/20."],
                         [(datetime(2026, 9, 1), "GASOLINA COMUM", 19347, "R$/l", 6.54, 0.4)], CAB_BRASIL)
    cab, linhas, notas = extract._tabela(conteudo)
    assert cab[0] == "MES" and len(linhas) == 1
    assert len(notas) == 2 and notas[1].startswith("Não houve pesquisa")
    assert extract._col(cab, "PRECO", "MEDIO", "REVENDA") == 4


def test_produto_casa_sem_acento_entre_as_duas_planilhas(monkeypatch):
    """A planilha antiga escreve 'ÓLEO DIESEL' e a nova 'OLEO DIESEL' — é o mesmo produto."""
    from datetime import datetime
    antiga = _planilha("BRASIL", [], [(datetime(2012, 12, 1), "ÓLEO DIESEL", 100, "R$/l", 2.1, 0.1)], CAB_BRASIL)
    nova = _planilha("BRASIL", [], [(datetime(2026, 9, 1), "OLEO DIESEL", 90, "R$/l", 6.7, 0.3)], CAB_BRASIL)
    monkeypatch.setattr(extract, "_planilha", lambda c, chave: antiga if "2001" in chave else nova)
    serie, _ = extract.combustiveis(httpx.Client())
    assert sorted(serie["diesel"]) == ["2012-12", "2026-09"]
    assert "GASOLINA ADITIVADA" not in serie            # a aditivada só existe depois de 2013: fica fora


def test_minutos_usam_o_salario_minimo_do_proprio_mes():
    """R$ 6,54 o litro com salário mínimo de R$ 1.621 em 220 horas dá 53,3 minutos de trabalho."""
    hora = 1621.0 / extract.HORAS_MES
    assert round(60 * 6.54 / hora, 1) == 53.3


def test_icp_le_a_dimensao_de_classificacao():
    """O ICP vem pela API de fontes do Banco Mundial, com país, série e classificação em dimensões."""
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"pages": 1, "source": {"data": [
            {"variable": [{"concept": "Country", "id": "BRA"}, {"concept": "Series", "id": "1107100"},
                          {"concept": "Classification", "id": "PX.WL"}, {"concept": "Time", "id": "YR2021"}],
             "value": 100.1},
            {"variable": [{"concept": "Country", "id": "USA"}, {"concept": "Series", "id": "1107100"},
                          {"concept": "Classification", "id": "PX.WL"}, {"concept": "Time", "id": "YR2021"}],
             "value": None},
        ]}})

    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        got = extract._icp(c, "PX.WL")
    assert got == {("BRA", "1107100"): 100.1}            # célula sem valor não vira zero
