"""Renda: mapeamento de códigos SIDRA e parsing de valores (sem rede)."""
from etl.renda.extract import POSICOES, CLASSES, _num


def test_codigos_posicao_cobrem_publico_e_privado():
    chaves = set(POSICOES.values())
    assert {"total", "publico", "publico_estatutario_militar", "privado_com_carteira", "privado_sem_carteira", "conta_propria", "empregador"} <= chaves
    assert len(POSICOES) == len(chaves)  # sem chave duplicada


def test_classes_percentil():
    assert CLASSES["Maior que o P99"] == "p99_mais" and CLASSES["Até o P10"] == "ate_p10"
    assert _num("3447") == 3447.0 and _num("...") is None and _num("-") is None and _num(None) is None
