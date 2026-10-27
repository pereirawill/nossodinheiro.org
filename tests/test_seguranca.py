"""Segurança: agregação do VDE com um xlsx sintético e taxa por 100 mil (sem rede)."""
import io
from datetime import datetime
import openpyxl

from etl.seguranca.extract import ler, taxa

HDR = ["uf", "municipio", "evento", "data_referencia", "agente", "arma", "faixa_etaria", "feminino", "masculino", "nao_informado", "total_vitima", "total", "total_peso", "abrangencia"]


def _linha(uf, mun, ev, mes, vit=None, tot=None, abr="Estadual"):
    return [uf, mun, ev, datetime(2025, mes, 1), None, None, None, 0, 0, 0, vit, tot, None, abr]


def test_ler_agrega_por_uf_e_municipio():
    wb = openpyxl.Workbook(); ws = wb.active; ws.append(HDR)
    for l in [_linha("SP", "SÃO PAULO", "Homicídio doloso", 1, vit=3), _linha("SP", "SÃO PAULO", "Homicídio doloso", 2, vit=2),
              _linha("SP", "CAMPINAS", "Homicídio doloso", 1, vit=1), _linha("SP", "NÃO INFORMADO", "Homicídio doloso", 1, vit=4),
              _linha("SP", "NÃO INFORMADO", "Roubo de veículo", 1, tot=50), _linha("SP", "SÃO PAULO", "Mandado de prisão cumprido", 1, tot=9),
              _linha("SP", "SÃO PAULO", "Homicídio doloso", 3, vit=7, abr="Polícia Federal")]:
        ws.append(l)
    b = io.BytesIO(); wb.save(b)
    por_uf, por_mun, nomes, meses = ler(b.getvalue())
    assert por_uf["SP"]["homicidio_doloso"] == 3 + 2 + 1 + 4        # PF fora; NÃO INFORMADO entra na UF
    assert por_uf["SP"]["roubo_veiculo"] == 50 and "mandado" not in str(por_uf["SP"])
    assert por_mun[("SP", "SAOPAULO")]["homicidio_doloso"] == 5 and por_mun[("SP", "CAMPINAS")]["homicidio_doloso"] == 1
    assert ("SP", "NAOINFORMADO") not in por_mun and nomes[("SP", "SAOPAULO")] == "SÃO PAULO"
    assert meses == {"SP": 2}


def test_taxa():
    assert taxa(10, 200_000) == 5.0 and taxa(0, 100) == 0.0 and taxa(3, 0) is None
