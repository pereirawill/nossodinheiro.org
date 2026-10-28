"""Saneamento: leitura das tabelas do SIDRA (Censo e PNAD Contínua), sem rede."""
import httpx

from etl.saneamento import extract


def _resposta(colunas: dict, linhas: list[dict]) -> list[dict]:
    """Formato do SIDRA: a primeira linha é o cabeçalho (código da coluna → nome)."""
    return [colunas] + linhas


CAB_CENSO = {"NC": "Nível Territorial (Código)", "MN": "Unidade de Medida", "V": "Valor",
             "D1C": "Brasil (Código)", "D1N": "Brasil", "D2C": "Variável (Código)", "D3N": "Ano",
             "D4C": "Tipo de esgotamento sanitário (Código)", "D4N": "Tipo de esgotamento sanitário",
             "D5C": "Situação do domicílio (Código)", "D5N": "Situação do domicílio"}


def _linha_censo(valor, cat_cod, cat_nome, sit="Total"):
    return {"NC": "1", "MN": "Unidades", "V": valor, "D1C": "1", "D1N": "Brasil", "D2C": "96", "D3N": "2022",
            "D4C": cat_cod, "D4N": cat_nome, "D5C": "0", "D5N": sit}


def test_censo_soma_so_as_categorias_pedidas_com_as_outras_no_total(monkeypatch):
    linhas = _resposta(CAB_CENSO, [
        _linha_censo("1000", "0", "Total"),
        _linha_censo("600", "92855", "Rede geral de esgoto ou pluvial"),
        _linha_censo("300", "92856", "Fossa séptica"),
        # a mesma categoria repartida por outra classificação não pode somar duas vezes
        _linha_censo("400", "92855", "Rede geral de esgoto ou pluvial", sit="Urbana"),
    ])
    c = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=linhas)))
    with c:
        got = extract._censo_tabela(c, 1444, 11558, "96", "2022", ["92855"], "n1")
    assert got["1"] == {"total": 1000.0, "rede": 600.0}


def test_censo_soma_duas_categorias_quando_a_pesquisa_separa(monkeypatch):
    """Em 1991 a rede geral aparece em duas linhas (instalação exclusiva e compartilhada)."""
    linhas = _resposta(CAB_CENSO, [
        _linha_censo("1000", "0", "Total"),
        _linha_censo("300", "120451", "Só do domicílio com rede geral"),
        _linha_censo("50", "120460", "Comum a mais de um domicílio com rede geral"),
        _linha_censo("650", "120468", "Não tem instalação sanitária"),
    ])
    c = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, json=linhas)))
    with c:
        got = extract._censo_tabela(c, 180, 1612, "96", "1991", ["120451", "120460"], "n1")
    assert got["1"]["rede"] == 350.0 and got["1"]["total"] == 1000.0


def test_pnadc_converte_mil_unidades_e_pula_valor_ausente():
    linha = {"Unidade de Medida": "Mil unidades", "Valor": "57196"}
    assert extract._em_unidades(linha, 57196.0) == 57_196_000
    assert extract._em_unidades({"Unidade de Medida": "Unidades"}, 10.0) == 10.0
    assert extract._num("-") is None and extract._num("...") is None and extract._num("-1") is None
    assert extract._num("12,5") == 12.5


def test_coluna_nao_pega_a_de_codigo():
    l = {"Situação do domicílio (Código)": "6795", "Situação do domicílio": "Total", "Ano": "2022"}
    assert extract._coluna(l, "situação do domicílio") == "Total"
    assert extract._codigo(l, "situação do domicílio") == "6795"


def test_categorias_ignora_colunas_estruturais():
    l = {"Nível Territorial (Código)": "1", "Brasil (Código)": "1", "Variável (Código)": "96",
         "Ano (Código)": "2022", "Unidade de Medida (Código)": "1020",
         "Tipo de esgotamento sanitário (Código)": "92855", "Tipo de esgotamento sanitário": "Rede geral"}
    assert extract._categorias(l) == [("92855", "Rede geral")]
