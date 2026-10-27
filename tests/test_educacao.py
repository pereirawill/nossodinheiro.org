"""Educação: leitura de planilhas do IDEB com um xlsx sintético no layout do INEP (sem rede)."""
import io
import openpyxl

from etl.educacao.extract import ler_ufs, ler_municipios, _rede, ABREV


def _xlsx(abas):
    wb = openpyxl.Workbook(); wb.remove(wb.active)
    for titulo, linhas in abas:
        ws = wb.create_sheet(titulo)
        for l in linhas:
            ws.append(l)
    b = io.BytesIO(); wb.save(b); return b.getvalue()


def test_rede_ignora_notas_de_rodape():
    assert _rede("Total (3)(4)") == "total" and _rede("Pública (4)") == "publica" and _rede("Privada (1)") == "privada" and _rede("xx") is None
    assert ABREV["R. G. do Sul"] == "Rio Grande do Sul"


def test_ler_ufs_e_brasil():
    cab = [None, None, "VL_APROVACAO_2021_SI", "VL_OBSERVADO_2021", "VL_PROJECAO_2023", "VL_OBSERVADO_2023"]
    aba = [["Região/UF", "Rede", "x", "y", "z", "w"], cab,
           ["Brasil", "Total", 90.1, 5.8, 6.0, 6.0], ["Brasil", "Pública", 90.0, 5.5, 5.8, 5.7],
           ["R. G. do Sul", "Total (4)", 91.0, 5.9, 6.1, 6.2], ["Norte", "Privada (1)", 95.0, 7.0, 7.2, 7.1],
           ["Fonte: MEC/Inep.", None, None, None, None, None]]
    estados, regioes, brasil = ler_ufs(_xlsx([("AI", aba), ("AF", aba), ("EM", aba)]))
    assert brasil["ai"]["total"] == {"2021": 5.8, "2023": 6.0} and brasil["em"]["publica"]["2023"] == 5.7
    assert estados["RS"]["nome"] == "Rio Grande do Sul" and estados["RS"]["af"]["total"]["2023"] == 6.2
    assert regioes["Norte"]["ai"]["privada"]["2021"] == 7.0


def test_ler_municipios_so_rede_publica():
    linhas = [["Sigla da UF", "Código", "Nome", "Rede", "a", "b"], ["SG_UF", "CO_MUNICIPIO", "NO_MUNICIPIO", "REDE", "VL_OBSERVADO_2021", "VL_OBSERVADO_2023"],
              ["SP", 3550308.0, "São Paulo", "Pública", 5.9, "6.1"], ["SP", 3550308.0, "São Paulo", "Municipal", 5.8, 6.0], ["CE", 2312908.0, "Sobral", "Pública", 8.0, "-"]]
    acc = {}
    ler_municipios(_xlsx([("M", linhas)]), "ai", 2023, acc)
    assert acc == {3550308: {"cod_ibge": 3550308, "nome": "São Paulo", "uf": "SP", "ai": 6.1}}
