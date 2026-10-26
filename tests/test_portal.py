"""Smoke test dos transforms do Portal/SIOP com fixtures SINTÉTICAS no schema real.
Não valida números reais — garante que raw → json não quebra e que a classificação por Poder
e o fallback de `deputados` (sem o CSV da CEAP) funcionam.
"""
import gzip, json
from pathlib import Path

DEPUTADOS = [
    {"id": 1001, "uri": "", "nome": "Deputado Exemplo A", "siglaPartido": "PXA", "uriPartido": "",
     "siglaUf": "RS", "idLegislatura": 57, "urlFoto": "", "email": None},
    {"id": 1002, "uri": "", "nome": "Deputada Exemplo B", "siglaPartido": "PXB", "uriPartido": "",
     "siglaUf": "DF", "idLegislatura": 57, "urlFoto": "", "email": None},
]
SENADORES = [{"id": 5001, "nome": "Senador Exemplo", "nome_completo": "Senador Exemplo da Silva", "partido": "PXC", "uf": "GO", "url_foto": ""}]
EMENDAS = [  # schema de GET /emendas?ano=  (valores em string pt-BR)
    {"codigoEmenda": "202512340001", "ano": 2025, "tipoEmenda": "Emenda Individual - Transferências com Finalidade Definida",
     "autor": "1234", "nomeAutor": "DEPUTADO EXEMPLO A", "numeroEmenda": "0001", "localidadeDoGasto": "PORTO ALEGRE - RS",
     "funcao": "Saúde", "subfuncao": "Atenção básica", "valorEmpenhado": "1.000.000,00", "valorLiquidado": "800.000,00",
     "valorPago": "750.000,50", "valorRestoInscrito": "0,00", "valorRestoCancelado": "0,00", "valorRestoPago": "0,00"},
    {"codigoEmenda": "202556780002", "ano": 2025, "tipoEmenda": "Emenda Individual - Transferências com Finalidade Definida",
     "autor": "5678", "nomeAutor": "SENADOR EXEMPLO (EX-PARLAMENTAR 2023)", "numeroEmenda": "0002", "localidadeDoGasto": "BRASIL",
     "funcao": "Educação", "subfuncao": "Ensino fundamental", "valorEmpenhado": "500.000,00", "valorLiquidado": "0,00",
     "valorPago": "0,00", "valorRestoInscrito": "0,00", "valorRestoCancelado": "0,00", "valorRestoPago": "0,00"},
]
DESPESAS_ORGAO = [  # schema de extract_poderes (SIOP): órgão × UO × GND, valores numéricos
    {"cod_superior": "01000", "orgao_superior": "Camara dos Deputados", "cod_orgao": "01101", "orgao": "Câmara dos Deputados",
     "gnd": "1", "gnd_nome": "Pessoal e Encargos Sociais", "programa": "0034", "programa_nome": "Programa de Gestão e Manutenção do Poder Legislativo",
     "acao": "20TP", "acao_nome": "Ativos Civis da União", "empenhado": 5.8e9, "liquidado": 5.7e9, "pago": 5.6e9, "dotacao": 6.5e9,
     "ano": 2025, "poder": "Legislativo", "categoria": "Manter a máquina", "subcategoria": "Pessoal ativo e encargos"},
    {"cod_superior": "01000", "orgao_superior": "Camara dos Deputados", "cod_orgao": "01101", "orgao": "Câmara dos Deputados",
     "gnd": "3", "gnd_nome": "Outras Despesas Correntes", "programa": "0034", "programa_nome": "Programa de Gestão e Manutenção do Poder Legislativo",
     "acao": "20TP", "acao_nome": "Ativos Civis da União", "empenhado": 1.5e9, "liquidado": 1.4e9, "pago": 1.3e9, "dotacao": 1.9e9,
     "ano": 2025, "poder": "Legislativo", "categoria": "Manter a máquina", "subcategoria": "Custeio"},
    {"cod_superior": "10000", "orgao_superior": "Supremo Tribunal Federal", "cod_orgao": "10101", "orgao": "Supremo Tribunal Federal",
     "gnd": "1", "gnd_nome": "Pessoal e Encargos Sociais", "programa": "0033", "programa_nome": "Programa de Gestão e Manutenção do Poder Judiciário",
     "acao": "0181", "acao_nome": "Aposentadorias e Pensões Civis da União", "empenhado": 9e8, "liquidado": 8.5e8, "pago": 8e8, "dotacao": 9.1e8,
     "ano": 2025, "poder": "Judiciário", "categoria": "Manter a máquina", "subcategoria": "Aposentados e pensionistas"},
    {"cod_superior": "75000", "orgao_superior": "Dívida Pública Federal", "cod_orgao": "75101", "orgao": "Recursos sob Supervisão do MF",
     "gnd": "6", "gnd_nome": "Amortização da Dívida", "programa": "0906", "programa_nome": "Operações Especiais: Serviço da Dívida",
     "acao": "0455", "acao_nome": "Amortização", "empenhado": 2e12, "liquidado": 2e12, "pago": 2e12, "dotacao": 2.5e12,
     "ano": 2025, "poder": "Dívida/Transferências", "categoria": "Dívida/Transferências", "subcategoria": "Amortização da Dívida"},
]


def _jsonl(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def test_classificar():
    from etl.portal_transparencia.extract_poderes import classificar
    assert classificar("01000") == "Legislativo"
    assert classificar("1000") == "Legislativo"       # sem zero à esquerda
    assert classificar("15000") == "Judiciário"
    assert classificar("34000") == "Funções essenciais"
    assert classificar("26000") == "Executivo"
    assert classificar("25000") == "Executivo"        # Fazenda é ministério; dívida está em 71000–75000
    assert classificar("75000") == "Dívida/Transferências"


def test_categorizar():
    from etl.portal_transparencia.extract_poderes import categorizar
    base = {"poder": "Judiciário", "gnd": "1", "gnd_nome": "Pessoal", "programa": "0033", "programa_nome": "Gestão", "acao_nome": "Ativos Civis"}
    assert categorizar(base) == ("Manter a máquina", "Pessoal ativo e encargos")
    assert categorizar({**base, "acao_nome": "Aposentadorias e Pensões Civis"}) == ("Manter a máquina", "Aposentados e pensionistas")
    assert categorizar({**base, "gnd": "3"}) == ("Manter a máquina", "Custeio")
    assert categorizar({**base, "gnd": "4"}) == ("Manter a máquina", "Investimento")
    assert categorizar({**base, "poder": "Executivo", "programa": "5111", "programa_nome": "Educação Básica"}) == ("Políticas públicas", "Educação Básica")
    assert categorizar({**base, "programa": "0901", "programa_nome": "Sentenças Judiciais"}) == ("Encargos especiais", "Sentenças Judiciais")
    assert categorizar({**base, "poder": "Dívida/Transferências", "gnd_nome": "Juros"}) == ("Dívida/Transferências", "Juros")


def test_transform_poderes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _jsonl(Path("data/raw/despesas_orgao_2025.jsonl.gz"), DESPESAS_ORGAO)
    from etl.portal_transparencia import transform_poderes
    transform_poderes.run(2025, populacao=200_000_000)

    poderes = {r["poder"]: r for r in json.loads(Path("data/public/poderes_2025.json").read_text(encoding="utf-8"))}
    assert poderes["Legislativo"]["pago"] == 6.9e9
    assert poderes["Legislativo"]["orgaos"] == 1
    assert poderes["Judiciário"]["pago_por_habitante"] == 4.0
    orgaos = json.loads(Path("data/public/poderes_orgaos_2025.json").read_text(encoding="utf-8"))
    assert len(orgaos) == 3                             # UO somada sobre os GNDs
    gnd = json.loads(Path("data/public/poderes_gnd_2025.json").read_text(encoding="utf-8"))
    assert {(g["poder"], g["gnd"]) for g in gnd} >= {("Legislativo", "1"), ("Legislativo", "3"), ("Dívida/Transferências", "6")}
    cat = json.loads(Path("data/public/poderes_categoria_2025.json").read_text(encoding="utf-8"))
    leg = {c["subcategoria"]: c["pago"] for c in cat if c["poder"] == "Legislativo" and c["categoria"] == "Manter a máquina"}
    assert leg == {"Pessoal ativo e encargos": 5.6e9, "Custeio": 1.3e9}


def test_transform_emendas_sem_parquet(tmp_path, monkeypatch):
    """Só a lista bruta de deputados (sem CEAP/parquet) basta para o join por nome."""
    monkeypatch.chdir(tmp_path)
    _jsonl(Path("data/raw/deputados_leg57.jsonl.gz"), DEPUTADOS)
    _jsonl(Path("data/raw/emendas_2025.jsonl.gz"), EMENDAS)
    _jsonl(Path("data/raw/senadores_atual.jsonl.gz"), SENADORES)
    from etl.portal_transparencia import transform_emendas
    transform_emendas.run(2025)

    autores = {r["autor"]: r for r in json.loads(Path("data/public/emendas_por_autor_2025.json").read_text(encoding="utf-8"))}
    a = autores["DEPUTADO EXEMPLO A"]
    assert a["match_deputado"] is True and a["id_deputado"] == 1001 and a["uf"] == "RS" and a["casa"] == "Câmara"
    assert a["empenhado"] == 1_000_000.0 and a["pago"] == 750_000.5
    s = autores["SENADOR EXEMPLO"]                      # sufixo "(EX-PARLAMENTAR …)" cortado; casa pela lista do Senado
    assert s["match_deputado"] is True and s["casa"] == "Senado" and s["uf"] == "GO"
