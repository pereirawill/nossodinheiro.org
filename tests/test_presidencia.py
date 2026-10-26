"""Smoke test do transform do cartão corporativo da Presidência com fixture sintética no schema do extrator."""
import gzip, json
from pathlib import Path

from etl.presidencia.extract import _mascara_cpf, _brl

LINHAS = [
    {"origem": "presidencia", "ano": 2026, "mes": 1, "cod_orgao": "20101", "orgao": "Presidência da República", "cod_ug": "1", "ug": "GAB",
     "portador": "Sigiloso", "favorecido_doc": "-11", "favorecido": "Sigiloso", "transacao": "Informações protegidas por sigilo", "data": "", "valor": 1000.0, "sigiloso": True},
    {"origem": "presidencia", "ano": 2026, "mes": 1, "cod_orgao": "20101", "orgao": "Presidência da República", "cod_ug": "1", "ug": "GAB",
     "portador": "FULANO", "favorecido_doc": "12345678000199", "favorecido": "POSTO X LTDA", "transacao": "COMPRA A/V - R$ - APRES", "data": "02/01/2026", "valor": 200.0, "sigiloso": False},
    {"origem": "presidencia", "ano": 2026, "mes": 1, "cod_orgao": "60000", "orgao": "Gabinete da Vice-Presidência", "cod_ug": "2", "ug": "VICE",
     "portador": "BELTRANO", "favorecido_doc": "***.456.789-**", "favorecido": "JOSE DA SILVA", "transacao": "SAQUE - R$", "data": "03/01/2026", "valor": 50.0, "sigiloso": False},
    {"origem": "total_governo", "ano": 2026, "mes": 1, "valor": 5000.0, "transacoes": 40},
]


def test_mascaras():
    assert _mascara_cpf("29669642191") == "***.696.421-**"
    assert _mascara_cpf("19406819000181") == "19406819000181"      # CNPJ fica inteiro
    assert _brl("1.234,56") == 1234.56 and _brl("") == 0.0


def test_transform(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p = Path("data/raw/presidencia_cpgf_2026.jsonl.gz"); p.parent.mkdir(parents=True)
    with gzip.open(p, "wt", encoding="utf-8") as f:
        for l in LINHAS:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
    from etl.presidencia import transform
    out = json.loads(transform.run(2026).read_text(encoding="utf-8"))
    assert out["totais"] == {"presidencia": 1250.0, "sigiloso": 1000.0, "pct_sigiloso": 0.8, "governo": 5000.0, "meses_publicados": 1}
    assert out["meses"][0]["transacoes"] == 3 and out["meses"][0]["governo"] == 5000.0
    assert [f["favorecido"] for f in out["favorecidos"]] == ["POSTO X LTDA"]   # pessoa física não entra
    assert out["portadores"] == 2
    tipos = {x["tipo"]: x["valor"] for x in out["por_tipo"]}
    assert tipos == {"Sob sigilo": 1000.0, "Compra": 200.0, "Saque em dinheiro": 50.0}
