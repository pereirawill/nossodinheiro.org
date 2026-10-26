"""
Transformação — Custo por senador (Senado Federal, "Recursos utilizados" por senador).

    python -m etl.senado.transform --ano 2026

Entrada: data/raw/senadores_recursos_<ano>.jsonl.gz (extract recursos)
Saídas:  data/public/custo_senador_<ano>.json (1 linha por senador em exercício)
         data/public/meta_senado_<ano>.json

Fórmula (ver docs/metodologia/painel-senadores.md):
  custo_total_estimado = subsídio (DL 172/2022, 13 + 1/3 por ano, mesmo dos deputados)
                       + CEAPS (cota, valor reembolsado — gasto real)
                       + gastos não inclusos na cota (diárias, passagens aéreas, correios, material,
                         impulsionamento em mídias sociais — gasto real, publicado pelo Senado)
  NÃO inclui o pessoal do gabinete (o Senado publica a quantidade de servidores por gabinete, mas
  não o custo; fica como próximo passo) nem auxílio-moradia (só "utilizou/não utilizou").
  Projeção anual: subsídio contratual + (CEAPS + não inclusos) extrapolados pela média mensal.
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
from datetime import date, datetime, timezone
from pathlib import Path

from ..camara import config as C
from ..camara.transform import meses_no_ano, subsidio_no_ano

log = logging.getLogger("etl.senado.transform")
RAW, PUB = Path("data/raw"), Path("data/public")

# Rótulos curtos para as categorias publicadas pelo Senado (chaves estáveis no JSON do site).
CEAPS_CHAVES = {
    "Aluguel de imóveis para escritório político": "aluguel_escritorio",
    "Aquisição de material de consumo": "material",
    "Locomoção, hospedagem, alimentação e combustíveis": "locomocao_hospedagem",
    "Contratação de serviços de apoio ao parlamentar": "servicos_apoio",
    "Divulgação da atividade parlamentar": "divulgacao",
    "Passagens aéreas, aquáticas e terrestres nacionais": "passagens_cota",
    "Serviços de Segurança Privada": "seguranca",
}
NAO_INCLUSOS_CHAVES = {
    "Viagens Oficiais - Diárias": "diarias",
    "Viagens Oficiais - Ressarcimento de Passagens": "ressarcimento_passagens",
    "Consumo de Material - Outros materiais": "material_outros",
    "Correios": "correios",
    "Cotas para Impulsionamento em Mídias Sociais": "midias_sociais",
    "Aquisição de passagens aéreas (ATC 2/2023)": "passagens_aereas",
}


def _chave(mapa: dict[str, str], rotulo: str) -> str:
    if rotulo not in mapa:
        log.warning("categoria nova no Senado: %r — mantida com rótulo original", rotulo)
    return mapa.get(rotulo, rotulo)


def _utilizou(beneficios: list[dict], nome: str) -> bool | None:
    for b in beneficios:
        if b.get("beneficio") == nome:
            return str(b.get("utilizacao", "")).strip().lower().startswith("utilizou")
    return None


def run(ano: int, hoje: date | None = None) -> Path:
    hoje = hoje or date.today()
    meses = meses_no_ano(ano, hoje)
    subsidio = subsidio_no_ano(ano, meses)
    subsidio_12 = subsidio_no_ano(ano, 12)
    PUB.mkdir(parents=True, exist_ok=True)

    with gzip.open(RAW / f"senadores_recursos_{ano}.jsonl.gz", "rt", encoding="utf-8") as f:
        brutos = [json.loads(l) for l in f]

    rows = []
    for r in brutos:
        ceaps = {_chave(CEAPS_CHAVES, d["recurso"]): float(d.get("valor") or 0) for d in r.get("ceaps", [])}
        nao = {_chave(NAO_INCLUSOS_CHAVES, d["recurso"]): float(d.get("valor") or 0) for d in r.get("nao_inclusos", [])}
        ceaps_total = round(sum(ceaps.values()), 2)
        nao_total = round(sum(nao.values()), 2)
        pessoal = {p.get("local"): int(p.get("quantidade") or 0) for p in r.get("pessoal", [])}
        total = round(subsidio + ceaps_total + nao_total, 2)
        rows.append({
            "id_senador": r["id"], "nome": r["nome"], "partido": r["partido"], "uf": r["uf"], "url_foto": r.get("url_foto"),
            "ano": ano, "meses_considerados": meses,
            "subsidio": subsidio, "ceaps": ceaps_total, "nao_inclusos": nao_total,
            "ceaps_categorias": ceaps, "nao_inclusos_itens": nao,
            "auxilio_moradia_utilizou": _utilizou(r.get("beneficios", []), "Auxílio-Moradia"),
            "imovel_funcional_utilizou": _utilizou(r.get("beneficios", []), "Imóvel Funcional"),
            "pessoal_gabinete": pessoal.get("Gabinete"), "pessoal_escritorios": pessoal.get("Escritório(s) de Apoio"),
            "custo_total_estimado": total,
            "custo_mensal_medio": round(total / meses, 2),
            "custo_anual_projetado": round(subsidio_12 + (ceaps_total + nao_total) * 12.0 / meses, 2),
        })
    rows.sort(key=lambda x: -x["custo_total_estimado"])

    out = PUB / f"custo_senador_{ano}.json"
    out.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    meta = {
        "ano": ano, "meses_considerados": meses, "senadores": len(rows),
        "gerado_em": hoje.isoformat(), "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "anual_e_projecao": ano >= hoje.year,
        "fonte": "Senado Federal — Transparência, Recursos utilizados por senador (adm.senado.gov.br/adm-dadosabertos)",
        "premissas": {"subsidio_mensal_dez": C.subsidio_mensal_em(date(ano, 12, 1)), "subsidios_por_ano": C.SUBSIDIOS_POR_ANO,
                      "inclui_pessoal_gabinete": False, "inclui_auxilio_moradia": False},
        "totais": {"ceaps": round(sum(r["ceaps"] for r in rows), 2), "nao_inclusos": round(sum(r["nao_inclusos"] for r in rows), 2),
                   "custo_total_estimado": round(sum(r["custo_total_estimado"] for r in rows), 2)},
    }
    (PUB / f"meta_senado_{ano}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    log.info("%d senadores em %d (%d meses); CEAPS R$ %.2f mi; não inclusos R$ %.2f mi; total R$ %.2f mi",
             len(rows), ano, meses, meta["totais"]["ceaps"] / 1e6, meta["totais"]["nao_inclusos"] / 1e6, meta["totais"]["custo_total_estimado"] / 1e6)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(); ap.add_argument("--ano", type=int, required=True)
    run(ap.parse_args().ano)
