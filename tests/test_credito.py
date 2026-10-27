"""Inadimplência: agregação do SCR.data com CSVs sintéticos no layout do BCB (sem rede)."""
from pathlib import Path

from etl.credito.extract import agregar

HDR = "data_base;uf;segmento;cliente;cnae_ocupacao;porte;modalidade;submodalidade;origem;indexador;numero_de_operacoes;carteira_ativa;carteira_inadimplencia;ativo_problematico"


def _csv(path: Path, mes: str, linhas: list[str]):
    path.write_text("\n".join([HDR] + [f'"{mes}";' + l for l in linhas]) + "\n", encoding="utf-8")


def test_agregar(tmp_path):
    a = tmp_path / "scrdata_202507.csv"; b = tmp_path / "scrdata_202508.csv"
    _csv(a, "2025-07-31", ['"SP";"Bancário";"PF";"x";"Até 1 salário mínimo";"Empréstimos";"s";"o";"i";"10";"1000,00";"100,00";"0,00"',
                            '"SP";"Bancário";"PJ";"x";"Micro";"Capital de giro";"s";"o";"i";"-1";"2000,00";"20,00";"0,00"'])
    _csv(b, "2025-08-31", ['"SP";"Bancário";"PF";"x";"Até 1 salário mínimo";"Empréstimos";"s";"o";"i";"10";"1000,00";"120,00";"0,00"',
                            '"RJ";"Bancário";"PF";"x";"Acima de 20 salários mínimos";"Financiamentos imobiliários";"s";"o";"i";"10";"3000,00";"30,00";"0,00"',
                            '"SP";"Bancário";"PJ";"x";"Micro";"Capital de giro";"s";"o";"i";"-1";"2000,00";"40,00";"0,00"'])
    d = agregar([a, b])
    assert d["referencia"] == "2025-08"
    assert d["brasil"]["PF"] == {"carteira": 4000.0, "inadimplencia": 150.0, "pct": 3.75} and d["brasil"]["PJ"]["pct"] == 2.0
    sp = next(u for u in d["por_uf"] if u["uf"] == "SP")
    assert sp["pct_pf"] == 12.0 and sp["carteira_pj"] == 2000.0 and sp["nome"] == "São Paulo"
    assert {m["modalidade"]: m["pct"] for m in d["modalidades"] if m["cliente"] == "PF"} == {"Empréstimos": 12.0, "Financiamentos imobiliários": 1.0}
    assert d["serie"] == [{"mes": "2025-07", "pct_pf": 10.0, "pct_pj": 1.0}, {"mes": "2025-08", "pct_pf": 3.75, "pct_pj": 2.0}]
