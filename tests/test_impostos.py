"""Testes do ETL de impostos: parser de números do CSV da Receita, deduplicação de famílias e agregação (sem rede)."""
from etl.impostos.extract import _brl, carregar, agregar

CABECALHO = "Ano;Mês;UF;IRPF;COFINS;COFINS - FINANCEIRAS;COFINS - DEMAIS;RECEITA PREVIDENCIÁRIA;IPI - OUTROS;PAGAMENTO UNIFICADO"


def test_brl_formatos_misturados():
    casos = {"65512,84": 65512.84, "8762245,567": 8762245.567, "1,006,523,961": 1006523961.0, "47.953.915": 47953915.0,
             "1.234,56": 1234.56, "1,234.56": 1234.56, "292096": 292096.0, "12.5": 12.5, "1.234": 1234.0, "": 0.0, "-": 0.0}
    for s, v in casos.items():
        assert abs(_brl(s) - v) < 1e-6, (s, _brl(s))


def test_sem_duplicidade_e_agregacao():
    csv = "\n".join([CABECALHO,
        "2001;Janeiro;SP;100;1,000;;;500;50;",             # ano antigo: COFINS agregado preenchido, detalhadas vazias
        "2026;Janeiro;SP;200;;10,5;300;700,25;60;40",      # ano novo: agregado vazio, detalhadas preenchidas
        "2026;Fevereiro;RJ;20;;1;30;70;6;4",
    ])
    linhas = carregar(csv)
    assert linhas[0]["valores"]["COFINS"] == 1000.0 and linhas[0]["valores"]["COFINS - DEMAIS"] == 0.0
    assert linhas[1]["valores"]["COFINS"] == 0.0 and linhas[1]["valores"]["COFINS - DEMAIS"] == 300.0
    d = agregar(linhas)
    assert d["ultimo_mes"] == {"ano": 2026, "mes": 2}
    a2026 = d["anual"][-1]
    assert a2026["meses"] == 2
    assert a2026["total"] == 200 + 10.5 + 300 + 700.25 + 60 + 40 + 20 + 1 + 30 + 70 + 6 + 4
    assert a2026["bases"]["consumo"] == 10.5 + 300 + 60 + 1 + 30 + 6
    assert a2026["bases"]["folha"] == 770.25 and a2026["bases"]["renda_trabalho"] == 220.0
    assert d["por_uf"][0]["uf"] == "SP" and len(d["mensal"]) == 3
    assert d["tributos_ultimo_ano"][0]["tributo"] == "Contribuição previdenciária (INSS)"
