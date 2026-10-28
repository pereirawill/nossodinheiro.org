"""Estatais: leitura dos arquivos da CVM (DFP e formulário de referência), do microdado da SEST e da série do
Tesouro — tudo com fixtura sintética, sem rede."""
import csv
import io
import zipfile

import httpx
import pytest

from etl.estatais import dividendos, extract, sest


# ── CVM: a última linha da DRE muda de código entre planos de contas ──────────────────────────────────────────────
def test_acha_a_linha_do_lucro_nos_dois_planos():
    assert extract._e_linha_do_lucro("3.11", "Lucro ou Prejuízo Líquido Consolidado do Período")
    assert extract._e_linha_do_lucro("3.09", "Lucro/Prejuízo Consolidado do Período")   # plano antigo dos bancos
    assert extract._e_linha_do_lucro("3.11", "Lucro/Prejuízo do Período")               # demonstração individual
    assert not extract._e_linha_do_lucro("3.09", "Lucro ou Prejuízo antes das Participações")
    assert not extract._e_linha_do_lucro("3.99", "Lucro por Ação - (R$ / Ação)")
    assert not extract._e_linha_do_lucro("3.11.01", "Atribuído aos Sócios da Empresa Controladora")


def _zip_dfp(ano, linhas, sufixos=("DRE_con", "DRE_ind")):
    cab = ["CNPJ_CIA", "DT_FIM_EXERC", "ORDEM_EXERC", "CD_CONTA", "DS_CONTA", "VL_CONTA", "ESCALA_MOEDA", "DENOM_CIA"]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for sufixo in sufixos:
            saida = io.StringIO()
            w = csv.writer(saida, delimiter=";")
            w.writerow(cab)
            for l in linhas.get(sufixo, []):
                w.writerow(l)
            zf.writestr(f"dfp_cia_aberta_{sufixo}_{ano}.csv", saida.getvalue().encode("latin-1"))
    return buf.getvalue()


def _zip_fre(ano, linhas):
    cab = ["CNPJ_Companhia", "Data_Referencia", "Acionista", "CPF_CNPJ_Acionista", "Acionista_Relacionado",
           "Percentual_Acao_Ordinaria_Circulacao", "Percentual_Total_Acoes_Circulacao", "Acionista_Controlador"]
    saida = io.StringIO()
    w = csv.writer(saida, delimiter=";")
    w.writerow(cab)
    for l in linhas:
        w.writerow(l)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(f"fre_cia_aberta_posicao_acionaria_{ano}.csv", saida.getvalue().encode("latin-1"))
    return buf.getvalue()


PETRO, BB, BBSEG, SANEPAR = "33.000.167/0001-01", "00.000.000/0001-91", "17.344.597/0001-94", "76.484.013/0001-45"


def _cliente(respostas):
    def handler(req: httpx.Request) -> httpx.Response:
        for pedaco, conteudo in respostas.items():
            if pedaco in str(req.url):
                return httpx.Response(200, content=conteudo)
        return httpx.Response(404)
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_ler_lucro_prefere_consolidado_e_cai_no_individual(tmp_path, monkeypatch):
    monkeypatch.setattr(extract, "RAW", tmp_path)
    dfp = _zip_dfp(2025, {
        "DRE_con": [[PETRO, "2025-12-31", "ÚLTIMO", "3.11", "Lucro ou Prejuízo Consolidado do Período", "100000",
                     "MIL", "PETROBRAS"],
                    [PETRO, "2025-12-31", "ÚLTIMO", "3.11.01", "Atribuído aos Sócios da Empresa Controladora",
                     "90000", "MIL", "PETROBRAS"],
                    [PETRO, "2024-12-31", "PENÚLTIMO", "3.11", "Lucro ou Prejuízo Consolidado do Período", "1",
                     "MIL", "PETROBRAS"],
                    [BB, "2025-12-31", "ÚLTIMO", "3.09", "Lucro/Prejuízo Consolidado do Período", "50000", "MIL",
                     "BCO BRASIL"]],
        # a Sanepar só publica individual: precisa entrar, e todas as linhas dela precisam ser lidas
        "DRE_ind": [[SANEPAR, "2025-12-31", "ÚLTIMO", "3.01", "Receita de Venda", "9999", "MIL", "SANEPAR"],
                    [SANEPAR, "2025-12-31", "ÚLTIMO", "3.11", "Lucro/Prejuízo do Período", "2000", "MIL", "SANEPAR"],
                    [PETRO, "2025-12-31", "ÚLTIMO", "3.11", "Lucro/Prejuízo do Período", "7", "MIL", "PETROBRAS"]],
    })
    with _cliente({"dfp_cia_aberta_2025": dfp}) as c:
        got = extract.ler_lucro(c, 2025)
    assert got[PETRO]["lucro"] == 100_000_000 and got[PETRO]["controlador"] == 90_000_000
    assert got[PETRO]["demonstracao"] == "DRE_con"          # o individual não sobrescreve o consolidado
    assert got[BB]["lucro"] == 50_000_000 and got[BB]["conta"] == "3.09"
    assert got[SANEPAR]["lucro"] == 2_000_000 and got[SANEPAR]["demonstracao"] == "DRE_ind"


def test_controle_direto_indireto_e_falso_positivo(tmp_path, monkeypatch):
    monkeypatch.setattr(extract, "RAW", tmp_path)
    fre = _zip_fre(2025, [
        [PETRO, "2025-12-31", "União Federal", "00.394.460/0001-41", "", "50.26", "29.02", "S"],
        [PETRO, "2025-12-31", "BNDES", "33.657.248/0001-89", "União Federal", "100", "100", "S"],   # cadeia: ignorar
        [BB, "2025-12-31", "Secretaria do Tesouro Nacional", "00.394.460/0001-41", "", "50.0", "50.0", "S"],
        [BBSEG, "2025-12-31", "BANCO DO BRASIL S.A.", BB, "", "68.25", "66.25", "S"],               # indireto
        # a Sabesp tem "do Estado de São Paulo" no nome, mas é empresa, não ente público
        [SANEPAR, "2025-12-31", "CIA SANEAMENTO BASICO DO ESTADO DE SAO PAULO - SABESP",
         "43.776.517/0001-80", "", "98.97", "98.97", "S"],
    ])
    with _cliente({"fre_cia_aberta_2025": fre}) as c:
        got = extract.ler_controle(c, 2025)
    assert got[PETRO]["tipo"] == "direto" and got[PETRO]["on"] == 50.26
    assert got[BB]["on"] == 50.0                                  # exatamente no piso ainda é controle
    assert got[BBSEG]["tipo"] == "indireto" and got[BBSEG]["via"] == "Banco do Brasil"
    assert SANEPAR not in got


def test_run_preenche_ano_sem_formulario_e_nao_soma_subsidiaria(tmp_path, monkeypatch):
    monkeypatch.setattr(extract, "RAW", tmp_path / "raw")
    monkeypatch.setattr(extract, "PUB", tmp_path / "pub")
    monkeypatch.setattr(extract, "ANO_INICIAL", 2023)
    monkeypatch.setattr(extract.sest, "coletar", lambda c: {})
    monkeypatch.setattr(extract.dividendos, "coletar", lambda c: {})
    lucro = {"DRE_con": [[PETRO, "", "ÚLTIMO", "3.11", "Lucro ou Prejuízo Consolidado do Período", "10", "MIL", "P"],
                         [BBSEG, "", "ÚLTIMO", "3.11", "Lucro ou Prejuízo Consolidado do Período", "4", "MIL", "B"]]}
    publico = [[PETRO, "", "União Federal", "00.394.460/0001-41", "", "50.26", "29", "S"]]
    indireto = [[BBSEG, "", "BANCO DO BRASIL S.A.", BB, "", "68", "66", "S"]]
    respostas = {
        "dfp_cia_aberta_2023": _zip_dfp(2023, lucro), "dfp_cia_aberta_2024": _zip_dfp(2024, lucro),
        "dfp_cia_aberta_2025": _zip_dfp(2025, lucro), "dfp_cia_aberta_2026": b"", "fre_cia_aberta_2026": b"",
        "fre_cia_aberta_2023": _zip_fre(2023, publico + indireto),
        "fre_cia_aberta_2024": _zip_fre(2024, indireto),      # a Petrobras não aparece: ano sem formulário
        "fre_cia_aberta_2025": _zip_fre(2025, publico + indireto),
    }
    pronto = _cliente(respostas)          # criado antes do monkeypatch, senão _cliente chamaria a si mesmo
    monkeypatch.setattr(extract.httpx, "Client", lambda **kw: pronto)
    out = extract.run()
    import json
    dados = json.loads(out.read_text(encoding="utf-8"))
    petro = next(e for e in dados["empresas"] if e["nome"] == "Petrobras")
    assert petro["estatal"] == {"2023": True, "2024": True, "2025": True}
    assert petro["estatal_origem"]["2024"] == "interpolado"     # buraco entre dois anos confirmados
    # a BB Seguridade é estatal, mas está dentro do consolidado do Banco do Brasil: não soma no agregado
    assert dados["agregado"]["2024"] == 10_000 and dados["empresas_no_agregado"]["2024"] == 1


# ── SEST: três armadilhas do microdado ────────────────────────────────────────────────────────────────────────────
def _zip_sest_ident():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        def grava(nome, cab, linhas):
            saida = io.StringIO()
            w = csv.writer(saida, delimiter=";")
            w.writerow(cab)
            for l in linhas:
                w.writerow(l)
            zf.writestr(f"sest-identificacao/{nome}", saida.getvalue().encode("latin-1"))
        cab = ["codigo_siest", "sigla", "nome", "dependencia", "setor", "segmento", "capital_aberto_fechado",
               "cnpj", "ministerio_supervisor", "controle_acionario"]
        grava("sest-identificacao-empresas-ativas.csv", cab, [
            ["1", "PETROBRAS", "Petróleo Brasileiro S.A.", "Não dependente do Tesouro Nacional", "Produtivo",
             "Petróleo", "Capital Aberto", "33.000.167/0001-01", "Minas e Energia", "Controle direto"],
            ["2", "ECT", "Correios", "Não dependente do Tesouro Nacional", "Produtivo", "Postal",
             "Capital Fechado", "34.028.316/0001-03", "Comunicações", "Controle direto"],
            ["3", "EMBRAPA", "Empresa Brasileira de Pesquisa Agropecuária", "Dependente do Tesouro Nacional",
             "Produtivo", "Pesquisa", "Capital Fechado", "00.348.003/0001-10", "Agricultura", "Controle direto"],
            ["4", "SUBSID", "Subsidiária qualquer", "Não dependente do Tesouro Nacional", "Produtivo", "Outro",
             "Capital Fechado", "11.111.111/0001-11", "Fazenda", "Controle indireto"],
        ])
        grava("sest-identificacao-empresas-inativas.csv", cab + ["data_inativacao"], [
            ["5", "ELETROBRAS", "Centrais Elétricas Brasileiras", "Não dependente do Tesouro Nacional", "Produtivo",
             "Energia", "Capital Aberto", "00.001.180/0001-26", "Minas e Energia", "Controle direto", "17/06/2022"],
        ])
        grava("sest-identificacao-grupos.csv", ["codigo_siest", "sigla", "nome"], [["99", "GR. PETROBRAS", "Grupo"]])
    return buf.getvalue()


def _zip_sest_fin(linhas):
    cab = ["exercicio", "periodicidade", "codigo_siest", "empresa", "demonstrativo", "rubrica_codigo",
           "rubrica_nome", "valor"]
    saida = io.StringIO()
    w = csv.writer(saida, delimiter=";")
    w.writerow(cab)
    for l in linhas:
        w.writerow(l)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("sest-dadosfinanceiros-demonstracoes.csv", saida.getvalue().encode("latin-1"))
    return buf.getvalue()


def test_sest_descarta_ano_com_poucas_empresas(tmp_path, monkeypatch):
    """O arquivo do ano recém-aberto traz meia dúzia de empresas: não pode virar o ano de referência da página."""
    monkeypatch.setattr(sest, "RAW", tmp_path)
    linhas = [["2024", "Anual", c, s_, "DRE", "500000", "LUCRO OU PREJUÍZO LÍQUIDO DO EXERCÍCIO", "1.000.000"]
              for c, s_ in (("1", "PETROBRAS"), ("2", "ECT"), ("3", "EMBRAPA"))]
    linhas.append(["2025", "4º Trimestre", "1", "PETROBRAS", "DRE", "290000000", "LUCRO/PREJUÍZO LÍQUIDO", "9.000.000"])

    def handler(req):
        if "sestidentificacao" in str(req.url):
            return httpx.Response(200, content=_zip_sest_ident())
        return httpx.Response(200, content=_zip_sest_fin(linhas))
    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        got = sest.coletar(c)
    assert got["anos"] == ["2024"] and "2025" not in got["agregado"]


def test_sest_filtra_dre_grupos_e_usa_trimestre_acumulado(tmp_path, monkeypatch):
    monkeypatch.setattr(sest, "RAW", tmp_path)
    linhas = [
        ["2021", "Anual", "1", "PETROBRAS", "DRE", "500000", "LUCRO OU PREJUÍZO LÍQUIDO DO EXERCÍCIO", "100.000.000"],
        ["2021", "Anual", "1", "PETROBRAS", "Balanço", "500000", "OUTRA COISA COM O MESMO CÓDIGO", "999.999.999"],
        ["2021", "Anual", "99", "GR. PETROBRAS", "DRE", "500000", "LUCRO OU PREJUÍZO LÍQUIDO DO EXERCÍCIO",
         "100.000.000"],
        ["2021", "Anual", "5", "ELETROBRAS", "DRE", "500000", "LUCRO OU PREJUÍZO LÍQUIDO DO EXERCÍCIO", "7.000.000"],
        ["2021", "Anual", "4", "SUBSID", "DRE", "500000", "LUCRO OU PREJUÍZO LÍQUIDO DO EXERCÍCIO", "5.000.000"],
        ["2021", "Anual", "2", "ECT", "DRE", "290000000", "LUCRO/PREJUÍZO LÍQUIDO", "-3.000.000"],
        ["2021", "Anual", "3", "EMBRAPA", "DRE", "500000", "LUCRO OU PREJUÍZO LÍQUIDO DO EXERCÍCIO", "-1.000.000"],
        ["2022", "3º Trimestre", "1", "PETROBRAS", "DRE", "290000000", "LUCRO/PREJUÍZO LÍQUIDO", "60.000.000"],
        ["2022", "4º Trimestre", "1", "PETROBRAS", "DRE", "290000000", "LUCRO/PREJUÍZO LÍQUIDO", "80.000.000"],
        ["2022", "4º Trimestre", "2", "ECT", "DRE", "290000000", "LUCRO/PREJUÍZO LÍQUIDO", "-5.000.000"],
    ]
    def handler(req):
        if "sestidentificacao" in str(req.url):
            return httpx.Response(200, content=_zip_sest_ident())
        return httpx.Response(200, content=_zip_sest_fin(linhas))
    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        got = sest.coletar(c)
    assert got["agregado"]["2021"] == 96_000_000                  # Petrobras 100 mi − Correios 3 mi − Embrapa 1 mi
    assert got["agregado_com_inativas"]["2021"] == 103_000_000    # + Eletrobras, que era estatal naquele ano
    assert got["agregado"]["2022"] == 75_000_000 and "4º trimestre" in got["periodicidade"]["2022"]
    assert got["controle_direto"] == 3 and got["total_dependentes"] == 1
    assert got["dependentes_do_tesouro"] == ["EMBRAPA"]


# ── Tesouro: dividendos ───────────────────────────────────────────────────────────────────────────────────────────
def test_dividendos_le_tabela_22(tmp_path, monkeypatch):
    openpyxl = pytest.importorskip("openpyxl")
    monkeypatch.setattr(dividendos, "RAW", tmp_path)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "2.2"
    ws.append(["Tabela 2.2 Resultado Primário"])
    ws.append(["R$ Milhões - Valores Correntes"])
    ws.append(["Discriminação", 1997, 1998])
    ws.append(["1.4.1  Concessões e Permissões", 1517.19, 9357.71])
    ws.append(["1.4.2  Dividendos e Participações", 822.34, 2370.55])
    ws.append(["1.4.2.1  Banco do Brasil", 0, 100.0])
    ws.append(["1.4.2.8  Petrobras", 800.0, 1200.0])
    ws.append(["1.5 Outra coisa", 1, 2])
    buf = io.BytesIO()
    wb.save(buf)
    pacote = ('{"result": {"resources": [{"format": "XLSX", "url": '
              '"https://x/download/seriehistoricajul26.xlsx"}]}}')

    def handler(req):
        if "package_show" in str(req.url):
            return httpx.Response(200, content=pacote, headers={"content-type": "application/json"})
        return httpx.Response(200, content=buf.getvalue())
    with httpx.Client(transport=httpx.MockTransport(handler)) as c:
        got = dividendos.coletar(c)
    assert got["anos"] == ["1997", "1998"]
    assert got["total"]["1997"] == 822_340_000.0                  # a planilha está em R$ milhões
    assert got["por_empresa"]["Petrobras"]["1998"] == 1_200_000_000.0
    assert "Concessões e Permissões" not in got["por_empresa"]    # 1.4.1 não é dividendo
