"""Renda: mapeamento de códigos SIDRA e parsing de valores (sem rede)."""
from etl.renda.extract import POSICOES, CLASSES, _num


def test_codigos_posicao_cobrem_publico_e_privado():
    chaves = set(POSICOES.values())
    assert {"total", "publico", "publico_estatutario_militar", "privado_com_carteira", "privado_sem_carteira", "conta_propria", "empregador"} <= chaves
    assert len(POSICOES) == len(chaves)  # sem chave duplicada


def test_classes_percentil():
    assert CLASSES["Maior que o P99"] == "p99_mais" and CLASSES["Até o P10"] == "ate_p10"
    assert _num("3447") == 3447.0 and _num("...") is None and _num("-") is None and _num(None) is None


def test_classes_de_salario_minimo_do_censo_cobrem_a_faixa_ate_um_minimo():
    from etl.renda.extract import CLASSES_SM
    chaves = {ch for ch, _ in CLASSES_SM.values()}
    assert {"ate_1_4", "de_1_4_a_1_2", "de_1_2_a_1", "mais_de_20", "sem_rendimento"} <= chaves
    assert len(CLASSES_SM) == len(chaves)                       # sem chave duplicada
    tetos = [t for _, t in CLASSES_SM.values() if t is not None]
    assert tetos == sorted(tetos)                               # classes em ordem crescente


def test_censo_soma_as_tres_primeiras_classes_como_ate_um_minimo():
    import httpx
    from etl.renda import extract as renda

    def handler(request: httpx.Request) -> httpx.Response:
        u = str(request.url)
        if "bcdata.sgs.1619" in u:
            return httpx.Response(200, json=[{"data": "01/12/2022", "valor": "1212.00"}])
        linhas = [{"V": "Valor", "D1N": "x", "D4N": "y"}]
        for rotulo, v in [("Total", "1000"), ("Até 1/4 de salário mínimo", "100"),
                          ("Mais de 1/4 a 1/2 salário mínimo", "150"), ("Mais de 1/2 a 1 salário mínimo", "250"),
                          ("Mais de 1 a 2 salários mínimos", "500")]:
            linhas.append({"V": v, "D1N": "Brasil" if "/n1/" in u else "Ceará", "D4N": rotulo})
        return httpx.Response(200, json=linhas)

    d = renda.censo_salario_minimo(httpx.Client(transport=httpx.MockTransport(handler)))
    assert d["salario_minimo"] == 1212.0 and d["ano"] == 2022
    assert d["ocupados"]["ate_1_sm"] == 500 and d["ocupados"]["pct_ate_1_sm"] == 0.5
    assert d["moradores"]["total"] == 1000
    ce = next(u for u in d["por_uf"] if u["uf"] == "CE")
    assert ce["moradores_pct_ate_1_sm"] == 0.5 and ce["ocupados_ate_1_sm"] == 500
