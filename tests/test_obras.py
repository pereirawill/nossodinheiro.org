"""Obras: agregação do cadastro do Obrasgov (sem rede)."""
from datetime import date, timedelta

from etl.obras.extract import _anos_desde, _previsto, transformar


def _obra(idu, uf, situacao, previsto, *, situacao_desde=None, fim=None, eixo="Social", tipo="Creche", executor="PREFEITURA"):
    return {"idUnico": idu, "nome": f"Obra {idu}", "uf": uf, "situacao": situacao, "especie": "Construção",
            "dataSituacao": situacao_desde, "dataFinalPrevista": fim,
            "fontesDeRecurso": [{"origem": "Federal", "valorInvestimentoPrevisto": previsto}],
            "eixos": [{"descricao": eixo}], "tipos": [{"descricao": tipo}], "executores": [{"nome": executor}]}


def test_previsto_soma_fontes():
    o = {"fontesDeRecurso": [{"valorInvestimentoPrevisto": 10.5}, {"valorInvestimentoPrevisto": 4.5}]}
    assert _previsto(o) == 15.0 and _previsto({"fontesDeRecurso": None}) == 0


def test_anos_desde():
    assert _anos_desde(None) is None and _anos_desde("sem data") is None
    assert _anos_desde((date.today() - timedelta(days=730)).isoformat()) == 2.0


def test_transformar_separa_paradas_e_soma_empenhos():
    ontem = (date.today() - timedelta(days=365)).isoformat()
    obras = [
        _obra("1", "SP", "Paralisada", 1000.0, situacao_desde=ontem, fim=ontem),
        _obra("2", "SP", "Em execução", 500.0),
        _obra("3", "BA", "Inacabada", 2000.0, situacao_desde=ontem, fim=(date.today() + timedelta(days=365)).isoformat()),
        _obra("4", "XX", "Concluída", 300.0),                      # UF inválida: fora do recorte por estado
    ]
    empenhos = [{"idProjetoInvestimento": "1", "valorEmpenho": 400.0}, {"idProjetoInvestimento": "1", "valorEmpenho": 100.0},
                {"idProjetoInvestimento": "3", "valorEmpenho": 50.0}, {"idProjetoInvestimento": None, "valorEmpenho": 999.0}]
    d = transformar(obras, empenhos)

    assert d["total"] == 4 and d["obras_com_empenho"] == 2
    assert d["paradas"]["n"] == 2 and d["paradas"]["previsto"] == 3000.0 and d["paradas"]["empenhado"] == 550.0
    assert d["paradas"]["com_prazo_vencido"] == 1                   # só a obra 1 passou do prazo
    assert d["paradas"]["anos_sem_atualizacao_mediana"] == 1.0
    sp = next(u for u in d["por_uf"] if u["uf"] == "SP")
    assert sp["n"] == 2 and sp["paradas"] == 1 and sp["empenhado_paradas"] == 500.0
    assert [u["uf"] for u in d["por_uf"]] == ["BA", "SP"]           # XX fora
    assert {s["situacao"]: s["n"] for s in d["por_situacao"]} == {"Paralisada": 1, "Em execução": 1, "Inacabada": 1, "Concluída": 1}
    assert d["por_eixo"][0]["nome"] == "Social" and d["por_eixo"][0]["paradas"] == 2
    assert d["paradas"]["maiores"][0]["id"] == "3"                  # ordenado por valor previsto
