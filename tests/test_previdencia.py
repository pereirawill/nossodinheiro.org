"""Previdência: leitura das abas do BEPS com uma planilha sintética (sem rede)."""
import io

import pytest
import xlwt

from etl.previdencia.extract import por_especie, por_uf, serie


def _wb():
    wb = xlwt.Workbook()
    s15 = wb.add_sheet("15")
    for r, (nome, qtd, valor, medio) in enumerate([
        ("TOTAL", 42660183, 80348316648.05, 1883.0),
        ("BENEFÍCIOS DO RGPS", 36043553, 70786910973.65, 1964.0),
        ("Aposentadorias", 24659976, 50545793064.31, 2050.0),
        ("Idade", 14130615, 22851137105.0, 1617.0),
        ("BENEFÍCIOS ASSISTENCIAIS ", 6601428, 9502887671.65, 1440.0),
        ("Amparos Assistenciais (LOAS)", 6556650, 9434710082.95, 1439.0),
        ("BENEFÍCIOS DE LEGISLAÇÃO ESPECÍFICA (BLE) (3)", 15202, 58518002.75, 3849.0),
        ("Nota de rodapé qualquer", 0, 0, 0),
    ]):
        s15.write(r, 0, nome); s15.write(r, 4, float(qtd)); s15.write(r, 12, valor); s15.write(r, 20, medio)
    s19 = wb.add_sheet("19")
    for r, (nome, qtd, valor, medio, rural) in enumerate([
        ("BRASIL", 36043545, 70786910973.65, 1964.0, 29.4),          # sem indentação: não é UF
        ("NORTE", 1843712, 2947213965.55, 1598.0, 59.3),
        ("   Rondônia", 258937, 417065543.59, 1610.68, 60.1),
        ("   São Paulo", 7000000, 16000000000.0, 2285.0, 5.0),
    ]):
        s19.write(r, 0, nome); s19.write(r, 4, float(qtd)); s19.write(r, 11, valor); s19.write(r, 18, medio); s19.write(r, 9, rural)
    s13 = wb.add_sheet("13")
    for r, (ano, mes, qtd) in enumerate([(2000, "Dezembro", 19572748), (None, "Janeiro", 19600000),
                                         (2026, "Julho", 42500000), (None, "Agosto", 42660183)]):
        if ano: s13.write(r, 0, float(ano))
        s13.write(r, 1, mes); s13.write(r, 4, float(qtd))
    b = io.BytesIO(); wb.save(b); return b.getvalue()


def test_especies_hierarquia_e_rodape():
    import xlrd
    esp = {e["chave"]: e for e in por_especie(xlrd.open_workbook(file_contents=_wb()))}
    assert esp["total"]["quantidade"] == 42660183 and esp["total"]["nivel"] == 0
    assert esp["aposentadoria_idade"]["nome"] == "por idade" and esp["aposentadoria_idade"]["nivel"] == 4
    assert esp["bpc"]["quantidade"] == 6556650                      # casa mesmo com "(LOAS)" no rótulo
    assert esp["legislacao_especial"]["quantidade"] == 15202        # casa mesmo com "(BLE) (3)" no rótulo
    assert esp["aposentadorias"]["valor"] == 50545793064.31


def test_uf_so_linhas_indentadas():
    import xlrd
    ufs = por_uf(xlrd.open_workbook(file_contents=_wb()))
    assert [u["uf"] for u in ufs] == ["RO", "SP"]                   # BRASIL e NORTE ficam de fora
    assert ufs[0]["pct_rural"] == 60.1 and ufs[1]["valor_medio"] == 2285.0


def test_serie_pega_dezembro_e_ultimo_mes():
    import xlrd
    s = serie(xlrd.open_workbook(file_contents=_wb()))
    assert [(x["ano"], x["mes"]) for x in s] == [(2000, "dezembro"), (2026, "agosto")]
    assert s[-1]["quantidade"] == 42660183
