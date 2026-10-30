"""Smoke test do painel Bancos com fixtures SINTÉTICAS no schema do IF.data.

Não valida números reais. Garante as regras que, se quebrarem, publicam número errado em silêncio:
lucro do ano = junho + dezembro (acumulação semestral), saldo de dezembro para patrimônio e ativo,
chave de grupo estável no tempo sem atribuição retroativa, dedupe de linha repetida e o invariante
da razão entre trimestres.
"""
import pytest

from etl.bancos.extract import _chaves, _conferir_semestre, consolidar, resumo


def _linha(cod, campo, valor, anomes="202512"):
    coluna = {"lucro": "Lucro Líquido", "pl": "Patrimônio Líquido", "ativo": "Ativo Total",
              "credito": "Carteira de Crédito"}[campo]
    conta = {"lucro": "140210", "pl": "140205", "ativo": "140201", "credito": "140202"}[campo]
    return {"TipoInstituicao": 2, "CodInst": cod, "AnoMes": anomes, "NomeRelatorio": "Resumo",
            "NumeroRelatorio": "1", "Grupo": None, "Conta": conta, "NomeColuna": coluna + " \n(a)",
            "DescricaoColuna": "[x]", "Saldo": valor}


def _resumo_de(linhas, monkeypatch):
    monkeypatch.setattr("etl.bancos.extract._cache", lambda c, nome, url, ano=None: linhas)
    return resumo(None, 202512)


def test_dedupe_de_linha_repetida(monkeypatch):
    # o trimestre mais recente volta com cada valor três vezes
    r = _resumo_de([_linha("A", "lucro", 100.0)] * 3, monkeypatch)
    assert r["A"]["lucro"] == 100.0


def test_valor_conflitante_falha(monkeypatch):
    with pytest.raises(RuntimeError, match="conflitantes"):
        _resumo_de([_linha("A", "lucro", 100.0), _linha("A", "lucro", 999.0)], monkeypatch)


def test_instituicao_sem_codigo_fica_fora(monkeypatch):
    r = _resumo_de([_linha("A", "lucro", 100.0), _linha(None, "lucro", 50.0)], monkeypatch)
    assert list(r) == ["A"]


def test_invariante_da_acumulacao_semestral():
    # 20 instituições em que junho vale o dobro de março: dentro da regra
    t1 = {f"I{i}": {"lucro": 10e6, "ativo": 1e9} for i in range(20)}
    s1 = {f"I{i}": {"lucro": 20e6, "ativo": 1e9} for i in range(20)}
    _conferir_semestre(t1, s1, {}, {}, 2025)
    # se junho passar a valer o mesmo que março, o BC mudou a forma de acumular
    with pytest.raises(RuntimeError, match="acumular por semestre"):
        _conferir_semestre(t1, {k: {"lucro": 10e6, "ativo": 1e9} for k in t1}, {}, {}, 2025)


def _ano(ano, inst, cadastro, parcial=False):
    return {"ano": ano, "parcial": parcial, "periodos": [ano * 100 + 6] + ([] if parcial else [ano * 100 + 12]),
            "inst": inst, "cadastro": cadastro}


def test_grupo_estavel_sem_atribuicao_retroativa():
    """Banco publicado como instituição e depois como conglomerado = uma série; corretora comprada só entra no ano
    da compra."""
    cad_sem = {"BANCO": {"nome": "BANCO X", "tcb": "B1", "prudencial": None, "uf": "SP"},
               "CORRETORA": {"nome": "CORRETORA Y", "tcb": "N2", "prudencial": None, "uf": "SP"}}
    cad_com = {"BANCO": {"nome": "BANCO X", "tcb": "B1", "prudencial": "PRUD", "uf": "SP"},
               "CORRETORA": {"nome": "CORRETORA Y", "tcb": "N2", "prudencial": "OUTRO", "uf": "SP"}}
    cad_pos = {"BANCO": {"nome": "BANCO X", "tcb": "B1", "prudencial": "PRUD", "uf": "SP"},
               "CORRETORA": {"nome": "CORRETORA Y", "tcb": "N2", "prudencial": "PRUD", "uf": "SP"}}
    v_banco = {"lucro": 100e6, "pl": 500e6, "ativo": 10e9, "credito": 5e9}
    v_corr = {"lucro": 1e6, "pl": 10e6, "ativo": 20e6, "credito": 0.0}
    dados = [_ano(2000, {"BANCO": dict(v_banco), "CORRETORA": dict(v_corr)}, cad_sem),
             _ano(2015, {"BANCO": dict(v_banco), "CORRETORA": dict(v_corr)}, cad_com),
             _ano(2025, {"BANCO": dict(v_banco), "CORRETORA": dict(v_corr)}, cad_pos)]
    ch = _chaves(dados)
    assert ch[(2000, "BANCO")] == ch[(2015, "BANCO")] == ch[(2025, "BANCO")] == "BANCO"
    assert ch.get((2015, "CORRETORA")) != "BANCO"          # antes da compra, série própria
    assert ch[(2025, "CORRETORA")] == "BANCO"              # depois da compra, no grupo

    anos, series, ultimo = consolidar(dados)
    assert ultimo == 2025
    assert series["BANCO"]["serie"]["2000"]["lucro"] == 100e6          # sem a corretora
    assert series["BANCO"]["serie"]["2025"]["lucro"] == 101e6          # com a corretora
    # o segmento do grupo é o do maior membro: banco, e não a corretora
    assert anos[-1]["segmentos"]["bancos"]["lucro"] == 101e6
    assert anos[-1]["segmentos"]["nao_bancarias"]["lucro"] == 0.0      # em 2025 ela está dentro do grupo do banco
    assert anos[0]["segmentos"]["nao_bancarias"]["lucro"] == 1e6       # em 2000 ela é independente


def test_nome_do_banco_que_sai_do_cadastro():
    """Banco que é comprado tem resultado no último ano mas já não está no cadastro: o nome não pode virar código."""
    cad = {"X": {"nome": "BANCO VELHO", "tcb": "B1", "prudencial": None, "uf": "SP"}}
    v = {"lucro": 10e6, "pl": 100e6, "ativo": 1e9, "credito": 0.0}
    _anos, series, _u = consolidar([_ano(2007, {"X": dict(v)}, cad), _ano(2008, {"X": dict(v)}, {})])
    assert series["X"]["nome"] == "BANCO VELHO"
    assert series["X"]["segmento"] == "bancos"


# ---------------------------------------------------------------- balancetes do Cosif (1994–1999)

CABECALHO = "DATA;COD.CONGLOMERADO;NOME CONGLOMERADO;ATRIBUTO;DOCUMENTO;CONTA;NOME CONTA;SALDO"


def _balancete(linhas):
    return ["Consolidado Financeiro (doc 4040)", "Data de geração", "Fonte", CABECALHO] + linhas


def _l(cod, nome, conta, saldo):
    return f"199512;{cod};{nome};G;4040;{conta};NOME;{saldo:.2f}".replace(".", ",")


def _ler(monkeypatch, linhas):
    from etl.bancos import cosif
    monkeypatch.setattr(cosif, "_csv", lambda c, anomes, url: _balancete(linhas))
    return cosif.lucro_por_grupo(None, 199512, "")


def test_cosif_balancete_aberto(monkeypatch):
    """Caso normal (dez/1995 em diante): o lucro é a soma das contas de resultado."""
    lucro, nomes, sem = _ler(monkeypatch, [_l("00010069", "ITAU", "0070000009", 500e6),
                                           _l("00010069", "ITAU", "0080000006", -380e6)])
    assert lucro == {"C0010069": 120e6}
    assert nomes["C0010069"] == "ITAU" and sem == []


def test_cosif_balancete_encerrado(monkeypatch):
    """Até jun/1995 as contas de resultado vêm zeradas e o lucro está na apuração, com sinal trocado."""
    lucro, _n, sem = _ler(monkeypatch, [_l("00010045", "BRADESCO", "0070000009", 900e6),
                                        _l("00010045", "BRADESCO", "0080000006", -900e6),
                                        _l("00010045", "BRADESCO", "0089100000", -186.8e6)])
    assert round(lucro["C0010045"]) == round(186.8e6)
    assert sem == []


def test_cosif_ambiguo_fica_sem_valor(monkeypatch):
    """Resultado e apuração preenchidos ao mesmo tempo: não dá para saber se somam ou se repetem."""
    lucro, _n, sem = _ler(monkeypatch, [_l("00010014", "BAMERINDUS", "0070000009", 100e6),
                                        _l("00010014", "BAMERINDUS", "0080000006", -165.6e6),
                                        _l("00010014", "BAMERINDUS", "0089100000", -179.1e6)])
    assert sem == ["C0010014"] and lucro == {}


def test_cosif_so_o_documento_4040(monkeypatch):
    """O arquivo traz também o balanço semestral (4046); somar os dois contaria o grupo duas vezes."""
    linhas = [_l("00049906", "BB", "0070000009", 300e6), _l("00049906", "BB", "0080000006", -200e6),
              "199512;00049906;BB;G;4046;0070000009;NOME;999999999,00"]
    lucro, _n, _s = _ler(monkeypatch, linhas)
    assert lucro == {"C0049906": 100e6}


def test_cosif_codigo_vira_o_do_ifdata(monkeypatch):
    """O formato antigo usa 00010069 e o IF.data usa C0010069 — é o mesmo grupo."""
    lucro, _n, _s = _ler(monkeypatch, [_l("00010069", "ITAU", "0070000009", 10e6),
                                       _l("00010069", "ITAU", "0080000006", -4e6)])
    assert list(lucro) == ["C0010069"]
