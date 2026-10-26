"""Smoke test do transform do Senado com fixture SINTÉTICA no schema real do JSON 'recursos utilizados'."""
import gzip, json
from datetime import date
from pathlib import Path

RECURSOS = [
    {"id": 5001, "nome": "Senador Exemplo", "partido": "PXC", "uf": "GO", "url_foto": "", "ano": 2026,
     "ceaps": [{"recurso": "Aluguel de imóveis para escritório político", "valor": 10000.0},
               {"recurso": "Divulgação da atividade parlamentar", "valor": 5000.5},
               {"recurso": "Categoria Nova Inventada", "valor": 1.0}],
     "ceaps_total": 15001.5,
     "nao_inclusos": [{"recurso": "Viagens Oficiais - Diárias", "valor": 2000.0}, {"recurso": "Correios", "valor": 500.0}],
     "nao_inclusos_total": 2500.0,
     "beneficios": [{"beneficio": "Auxílio-Moradia", "utilizacao": "Utilizou"}, {"beneficio": "Imóvel Funcional", "utilizacao": "Não utilizou"}],
     "pessoal": [{"local": "Gabinete", "quantidade": 12, "vinculos": []}, {"local": "Escritório(s) de Apoio", "quantidade": 3, "vinculos": []}]},
]


def test_transform_senado(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p = Path("data/raw/senadores_recursos_2026.jsonl.gz"); p.parent.mkdir(parents=True)
    with gzip.open(p, "wt", encoding="utf-8") as f:
        for r in RECURSOS:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    from etl.senado import transform
    from etl.camara.transform import subsidio_no_ano
    out = transform.run(2026, hoje=date(2026, 10, 26))
    rows = json.loads(out.read_text(encoding="utf-8"))
    assert len(rows) == 1
    r = rows[0]
    assert r["meses_considerados"] == 10
    assert r["subsidio"] == subsidio_no_ano(2026, 10)          # mesmo subsídio dos deputados
    assert r["ceaps"] == 15001.5 and r["nao_inclusos"] == 2500.0
    assert r["ceaps_categorias"]["aluguel_escritorio"] == 10000.0
    assert r["ceaps_categorias"]["Categoria Nova Inventada"] == 1.0   # categoria desconhecida mantém o rótulo
    assert r["auxilio_moradia_utilizou"] is True and r["imovel_funcional_utilizou"] is False
    assert r["pessoal_gabinete"] == 12 and r["pessoal_escritorios"] == 3
    assert r["custo_total_estimado"] == round(r["subsidio"] + 15001.5 + 2500.0, 2)
    assert r["custo_anual_projetado"] == round(subsidio_no_ano(2026, 12) + 17501.5 * 12 / 10, 2)
    meta = json.loads(Path("data/public/meta_senado_2026.json").read_text(encoding="utf-8"))
    assert meta["premissas"]["inclui_pessoal_gabinete"] is False and meta["anual_e_projecao"] is True
