"""Punições: agregações dos cadastros do Portal da Transparência (sem rede)."""
from etl.corrupcao.extract import _ano, _brl, _por_ano, _por_uf, empresas, expulsoes, leniencia


def test_parsers():
    assert _ano("19/10/2023") == "2023" and _ano("") is None and _ano("2023") is None
    assert _brl("6000,00") == 6000.0 and _brl("1.234.567,89") == 1234567.89 and _brl("") == 0.0


def test_empresas_agrega_uf_categoria_e_multa():
    linhas = [
        {"UF ÓRGÃO SANCIONADOR": "SP", "CATEGORIA DA SANÇÃO": "Suspensão", "ESFERA ÓRGÃO SANCIONADOR": "ESTADUAL",
         "ÓRGÃO SANCIONADOR": "Governo do Estado de São Paulo", "TIPO DE PESSOA": "J", "DATA INÍCIO SANÇÃO": "19/10/2023", "VALOR DA MULTA": "1.000,00"},
        {"UF ÓRGÃO SANCIONADOR": "SP", "CATEGORIA DA SANÇÃO": "Suspensão", "ESFERA ÓRGÃO SANCIONADOR": "ESTADUAL",
         "ÓRGÃO SANCIONADOR": "Governo do Estado de São Paulo", "TIPO DE PESSOA": "F", "DATA INÍCIO SANÇÃO": "01/02/2024", "VALOR DA MULTA": ""},
        {"UF ÓRGÃO SANCIONADOR": "", "CATEGORIA DA SANÇÃO": "Multa", "ESFERA ÓRGÃO SANCIONADOR": "FEDERAL",
         "ÓRGÃO SANCIONADOR": "CGU", "TIPO DE PESSOA": "J", "DATA INÍCIO SANÇÃO": "05/05/2024", "VALOR DA MULTA": "2.500,50"},
    ]
    d = empresas(linhas, "cnep")
    assert d["registros"] == 3 and d["pessoa_juridica"] == 2 and d["sem_uf"] == 1
    assert d["por_uf"] == [{"uf": "SP", "nome": "São Paulo", "n": 2}]
    assert d["por_ano"] == {"2023": 1, "2024": 2}
    assert d["por_categoria"][0] == {"nome": "Suspensão", "n": 2}
    assert d["multas"] == {"registros_com_multa": 2, "total": 3500.5}


def test_expulsoes_conta_artigos_sobrepostos():
    base = {"CATEGORIA DA SANÇÃO": "Demissão", "ÓRGÃO DE LOTAÇÃO": "INSS", "UF ÓRGÃO SANCIONADOR": "DF", "DATA INÍCIO SANÇÃO": "09/05/2022"}
    linhas = [
        {**base, "FUNDAMENTAÇÃO LEGAL": "ART. 132, XI - CORRUPÇÃO;ART. 132, IV - IMPROBIDADE ADMINISTRATIVA"},
        {**base, "CATEGORIA DA SANÇÃO": "Cassação de aposentadoria", "FUNDAMENTAÇÃO LEGAL": "ART. 132, II - ABANDONO DE CARGO"},
    ]
    d = expulsoes(linhas)
    motivos = {m["nome"]: m["n"] for m in d["motivos"]}
    assert motivos["Corrupção"] == 1 and motivos["Improbidade administrativa"] == 1 and motivos["Abandono de cargo ou inassiduidade"] == 1
    assert sum(motivos.values()) > d["registros"]           # os fundamentos se sobrepõem, de propósito
    assert d["por_categoria"][0]["nome"] == "Demissão" and d["por_uf"] == [{"uf": "DF", "nome": "Distrito Federal", "n": 2}]


def test_leniencia_usa_razao_social():
    linhas = [{"RAZÃO SOCIAL - CADASTRO RECEITA": "EMPRESA X LTDA", "NOME FANTASIA - CADASTRO RECEITA": "",
               "DATA DE INÍCIO DO ACORDO": "14/08/2017", "DATA DE FIM DO ACORDO": "31/12/2019",
               "SITUAÇÃO DO ACORDO DE LENIÊNICA": "Cumprido", "ÓRGÃO SANCIONADOR": "CGU"}]
    d = leniencia(linhas)
    assert d["registros"] == 1 and d["acordos"][0]["empresa"] == "EMPRESA X LTDA"
    assert d["por_situacao"] == [{"nome": "Cumprido", "n": 1}] and d["por_ano"] == {"2017": 1}
