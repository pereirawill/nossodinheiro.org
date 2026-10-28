"""Tribunais superiores: leitura da folha e custo por magistrado, com respostas sintéticas (sem rede)."""
import gzip
import json

import httpx
import pytest

from etl.tribunais import fontes, transform
from etl.tribunais.fontes import brl

CSV_TST = (
    "Data de Publicação;;08/10/2026;;;;;;;;;;;;;;\r\n"
    "Mês/Ano de Referência;;set/26;;;;;;;;;;;;;;\r\n"
    ";;;;;;;;;;;;;;;;\r\n"
    "Nome;Cargo;Lotação;Remuneração Paradigma(1);Vantagens Pessoais(2);Subsídio;Indenizações(3);Vantagens Eventuais(4);"
    "Total de Rendimentos(5);Previdência Pública(6);Imposto de Renda(7);Descontos Diversos(8);"
    "Retenção por Teto Constitucional(9);Total de Descontos(10);Rendimento Líquido(11);"
    "Remuneração do órgão de origem(12);Diárias(13)\r\n"
    # ministro no gabinete próprio: 100.000 - 10.000 de indenização - 5.000 de teto = 85.000
    "MARIA DA SILVA;MINISTRO;Gabinete da Ministra Maria da Silva;0;0;0;10.000,00;0;100.000,00;0;0;0;-5.000,00;0;60.000,00;0;0\r\n"
    # servidora do gabinete dela
    "JOANA SOUZA;ANALISTA JUDICIÁRIO;Gabinete da Ministra Maria da Silva;0;0;0;1.000,00;0;21.000,00;0;0;0;0;0;15.000,00;3.000,00;0\r\n"
    # ministro aposentado: lotação INATIVO, não tem gabinete
    "PEDRO ANTIGO;MINISTRO;INATIVO;0;0;0;0;0;60.000,00;0;0;0;0;0;45.000,00;0;0\r\n"
    # juiz convocado DENTRO do gabinete de um titular: conta como pessoal, não como centro de custo
    "CARLOS AUXILIAR;MAGISTRADO CONVOCADO AUXILIAR;Gabinete da Ministra Maria da Silva;0;0;0;0;0;40.000,00;0;0;0;0;0;30.000,00;0;0\r\n"
    # pseudo-lotação: não é gabinete
    "ANA CEDIDA;MINISTRO;À DISPOSIÇÃO DE OUTRO ÓRGÃO;0;0;0;0;0;500,00;0;0;0;0;0;400,00;0;0\r\n"
)


def _cliente_tst() -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        u = str(request.url)
        if u.endswith("/arquivos"):
            return httpx.Response(200, json={"2026-09-completo": "2026/09 - CSV", "2026-08-todos": "2026/08 - PDF",
                                             "2025-09-completo": "2025/09 - CSV"})
        if "/arquivo" in u and "2026-09-completo" in u:
            return httpx.Response(200, content=CSV_TST.encode("latin-1"), headers={"content-type": "text/csv"})
        return httpx.Response(404)
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_brl_aceita_formatos_misturados():
    assert brl("95.068,85") == 95068.85
    assert brl("-2.086,47") == -2086.47
    assert brl("0") == 0.0 and brl("") == 0.0 and brl(None) == 0.0


def test_tst_le_so_os_meses_em_csv_do_ano_pedido():
    linhas = fontes.tst(_cliente_tst(), 2026)
    assert {l["mes"] for l in linhas} == {9}          # o mês só em PDF fica de fora, e 2025 não é do ano pedido
    assert len(linhas) == 5


def test_bruto_exclui_indenizacao_e_desconta_o_teto():
    linhas = fontes.tst(_cliente_tst(), 2026)
    ministra = next(l for l in linhas if l["nome"] == "MARIA DA SILVA")
    assert ministra["bruto"] == 85_000.0            # 100.000 - 10.000 de indenização - 5.000 de teto
    assert ministra["indenizacoes"] == 10_000.0
    servidora = next(l for l in linhas if l["nome"] == "JOANA SOUZA")
    assert servidora["bruto"] == 20_000.0
    assert servidora["origem_outro_orgao"] == 3_000.0


def _gerar(tmp_path, monkeypatch, linhas: list[dict], sigla: str = "tst") -> tuple[list, dict]:
    monkeypatch.setattr(transform, "RAW", tmp_path)
    monkeypatch.setattr(transform, "PUB", tmp_path)
    with gzip.open(tmp_path / f"folha_{sigla}_2026.jsonl.gz", "wt", encoding="utf-8") as f:
        for l in linhas:
            f.write(json.dumps(l) + "\n")
    f1, f2 = transform.run(sigla, 2026)
    return json.loads(f1.read_text(encoding="utf-8")), json.loads(f2.read_text(encoding="utf-8"))


def test_custo_soma_o_gabinete_sem_o_proprio_ministro(tmp_path, monkeypatch):
    rows, meta = _gerar(tmp_path, monkeypatch, fontes.tst(_cliente_tst(), 2026))
    assert len(rows) == 1 and rows[0]["nome_curto"] == "Maria da Silva"
    r = rows[0]
    # gabinete = servidora (20.000) + juiz convocado que está dentro do gabinete (40.000); a ministra não entra
    assert r["gabinete"] == 60_000.0
    assert r["remuneracao_bruta"] == 85_000.0
    assert r["custo_ultimo_mes"] == 145_000.0
    assert r["gabinete_pessoas_ultimo_mes"] == 2
    assert meta["magistrados_em_exercicio"] == 1 and meta["convocados_no_ano"] == 0


def test_aposentado_e_cedido_ficam_fora_do_custo(tmp_path, monkeypatch):
    rows, meta = _gerar(tmp_path, monkeypatch, fontes.tst(_cliente_tst(), 2026))
    assert {r["nome"] for r in rows} == {"MARIA DA SILVA"}
    assert meta["aposentados"]["quantidade_ultimo_mes"] == 2        # o inativo e a cedida
    assert meta["aposentados"]["bruto_ultimo_mes"] == 60_500.0


def test_convocado_com_gabinete_proprio_ganha_linha(tmp_path, monkeypatch):
    linhas = fontes.tst(_cliente_tst(), 2026)
    linhas += [{"nome": "LUCIA CONVOCADA", "cargo": "MAGISTRADO CONVOCADO AUXILIAR",
                "lotacao": "Gabinete da Desembargadora Convocada Lucia Convocada", "bruto": 70_000.0,
                "indenizacoes": 0.0, "liquido": 50_000.0, "origem_outro_orgao": 0.0, "ano": 2026, "mes": 9},
               {"nome": "AJUDANTE X", "cargo": "TÉCNICO JUDICIÁRIO",
                "lotacao": "Gabinete da Desembargadora Convocada Lucia Convocada", "bruto": 10_000.0,
                "indenizacoes": 0.0, "liquido": 8_000.0, "origem_outro_orgao": 0.0, "ano": 2026, "mes": 9}]
    rows, meta = _gerar(tmp_path, monkeypatch, linhas)
    conv = next(r for r in rows if r["convocado"])
    assert conv["nome_curto"] == "Lucia Convocada" and conv["gabinete"] == 10_000.0
    assert meta["convocados_no_ano"] == 1
    assert meta["magistrados_em_exercicio"] == 1          # convocado não entra na composição


def test_mais_magistrados_que_a_composicao_no_mesmo_mes_derruba_o_run(tmp_path, monkeypatch):
    linhas = fontes.tst(_cliente_tst(), 2026)
    for i in range(27):
        linhas.append({"nome": f"MINISTRO {i}", "cargo": "MINISTRO", "lotacao": f"Gabinete do Ministro {i}",
                       "bruto": 50_000.0, "indenizacoes": 0.0, "liquido": 40_000.0, "origem_outro_orgao": 0.0,
                       "ano": 2026, "mes": 9})
    with pytest.raises(SystemExit, match="composição legal"):
        _gerar(tmp_path, monkeypatch, linhas)


def test_sem_detalhe_de_verbas_o_json_declara(tmp_path, monkeypatch):
    linhas = [{"nome": "MIN STM", "cargo": "MINISTRO DO SUPERIOR TRIBUNAL MILITAR", "lotacao": "GAB MIN STM",
               "bruto": 88_000.0, "indenizacoes": None, "liquido": 67_000.0, "origem_outro_orgao": 0.0,
               "ano": 2026, "mes": 9},
              {"nome": "ASSESSOR", "cargo": "ANALISTA", "lotacao": "GAB MIN STM", "bruto": 20_000.0,
               "indenizacoes": None, "liquido": 15_000.0, "origem_outro_orgao": 0.0, "ano": 2026, "mes": 9}]
    rows, meta = _gerar(tmp_path, monkeypatch, linhas, sigla="stm")
    assert meta["detalha_verbas"] is False and rows[0]["indenizacoes"] is None
    assert rows[0]["nome_curto"] == "Stm" and rows[0]["gabinete"] == 20_000.0
