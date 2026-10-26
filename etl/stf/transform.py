"""
Transformação — Custo por ministro do STF (folha publicada pelo próprio STF).

    python -m etl.stf.transform --ano 2026

Entrada: data/raw/stf_folha_<ano>.jsonl.gz (extract folha: ministros por cargo + folha de cada gabinete, por mês)
Saídas:  data/public/custo_ministro_stf_<ano>.json  (1 linha por ministro em atividade)
         data/public/meta_stf_<ano>.json             (meses, totais, aposentados)

Fórmula (ver docs/metodologia/painel-stf.md):
  remuneracao  = soma mensal da "Remuneração Bruta após o teto constitucional somada com outras verbas"
                 do ministro (é o rótulo do STF: subsídio limitado ao teto + verbas indenizatórias e eventuais)
  gabinete     = soma mensal da mesma coluna para todas as pessoas lotadas no gabinete do ministro,
                 exceto ele próprio (servidores efetivos, cedidos, sem vínculo, juízes auxiliares)
  custo_total_estimado = remuneracao + gabinete        (só meses com folha publicada)
  custo_mensal_medio   = custo_total_estimado / meses_com_folha
  custo_anual_projetado = custo_mensal_medio × 12       (ano corrente = projeção)
  Aposentados: total mensal pago a ministros aposentados, como estatística separada (não entra no custo
  de ninguém em atividade).
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

log = logging.getLogger("etl.stf.transform")
RAW, PUB = Path("data/raw"), Path("data/public")
COL_BRUTO = "Remuneração Bruta após o teto constitucional somada com outras verbas"
COL_LIQUIDO = "Remuneração Liquida"


def _f(v) -> float:
    try:
        return float(str(v).replace(",", ".")) if v not in (None, "") else 0.0
    except ValueError:
        return 0.0


def run(ano: int, hoje: date | None = None) -> Path:
    hoje = hoje or date.today()
    PUB.mkdir(parents=True, exist_ok=True)
    with gzip.open(RAW / f"stf_folha_{ano}.jsonl.gz", "rt", encoding="utf-8") as f:
        rows = [json.loads(l) for l in f]

    ministros = [r for r in rows if r["origem"] == "ministros"]
    gabinete = [r for r in rows if r["origem"] == "gabinete"]
    meses = sorted({r["mes"] for r in ministros})
    if not meses:
        raise SystemExit(f"sem folha de ministros em {ano}")

    ativos: dict[str, dict] = {}
    for r in ministros:
        if r["Situação Funcional"].strip().upper() != "MINISTRO":
            continue
        m = ativos.setdefault(r["Matrícula"], {"matricula": r["Matrícula"], "nome": r["Nome"], "unidade": r["Nome da Unidade"].strip(),
                                                "unidade_id": r.get("unidade_id"), "meses": set(), "remuneracao": 0.0, "liquido": 0.0})
        m["meses"].add(r["mes"]); m["remuneracao"] += _f(r[COL_BRUTO]); m["liquido"] += _f(r[COL_LIQUIDO])

    gab_total: dict[str, float] = defaultdict(float)      # unidade → soma bruta (sem o ministro)
    gab_pessoas: dict[str, dict[int, set]] = defaultdict(lambda: defaultdict(set))
    gab_vinculos: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    matriculas_ministros = set(ativos)
    for r in gabinete:
        if r["Matrícula"] in matriculas_ministros:
            continue
        u = r["Nome da Unidade"].strip()
        gab_total[u] += _f(r[COL_BRUTO])
        gab_pessoas[u][r["mes"]].add(r["Matrícula"])
        gab_vinculos[u][r["Situação Funcional"].strip()] += 1

    out_rows = []
    for m in ativos.values():
        n_meses = len(m["meses"])
        u = m["unidade"]
        pessoas_mes = [len(s) for s in gab_pessoas[u].values()] or [0]
        gab = round(gab_total.get(u, 0.0), 2)
        total = round(m["remuneracao"] + gab, 2)
        out_rows.append({
            "matricula": m["matricula"], "nome": m["nome"], "unidade": u, "ano": ano, "meses_com_folha": n_meses,
            "remuneracao_bruta": round(m["remuneracao"], 2), "remuneracao_liquida": round(m["liquido"], 2),
            "remuneracao_mensal_media": round(m["remuneracao"] / n_meses, 2),
            "gabinete": gab, "gabinete_mensal_medio": round(gab / n_meses, 2),
            "gabinete_pessoas_media": round(sum(pessoas_mes) / len(pessoas_mes), 1),
            "gabinete_vinculos": {k: round(v / n_meses, 1) for k, v in gab_vinculos[u].items()},
            "custo_total_estimado": total, "custo_mensal_medio": round(total / n_meses, 2),
            "custo_anual_projetado": round(total / n_meses * 12, 2),
            "observacao": "Presidente do STF: a lotação publicada é o Gabinete da Presidência, não um gabinete de ministro" if "PRESID" in u.upper() else None,
        })
    out_rows.sort(key=lambda x: -x["custo_total_estimado"])

    apos = [r for r in ministros if r["Situação Funcional"].strip().upper().startswith("APOSENTADO")]
    apos_por_mes = defaultdict(float); apos_n = defaultdict(set)
    for r in apos:
        apos_por_mes[r["mes"]] += _f(r[COL_BRUTO]); apos_n[r["mes"]].add(r["Matrícula"])
    ultimo = max(meses)

    out = PUB / f"custo_ministro_stf_{ano}.json"
    out.write_text(json.dumps(out_rows, ensure_ascii=False), encoding="utf-8")
    meta = {
        "ano": ano, "meses_com_folha": meses, "ultimo_mes": ultimo, "ministros_ativos": len(out_rows),
        "gerado_em": hoje.isoformat(), "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "anual_e_projecao": ano >= hoje.year,
        "fonte": "STF — Portal da Transparência, Remuneração (egesp-portal.stf.jus.br/transparencia/rendimento_folha), exportação CSV",
        "coluna_valor": COL_BRUTO,
        "aposentados": {"quantidade_ultimo_mes": len(apos_n[ultimo]), "bruto_ultimo_mes": round(apos_por_mes[ultimo], 2),
                        "bruto_acumulado": round(sum(apos_por_mes.values()), 2)},
        "totais": {"remuneracao_bruta": round(sum(r["remuneracao_bruta"] for r in out_rows), 2),
                   "gabinetes": round(sum(r["gabinete"] for r in out_rows), 2),
                   "custo_total_estimado": round(sum(r["custo_total_estimado"] for r in out_rows), 2)},
    }
    (PUB / f"meta_stf_{ano}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    log.info("%d ministros ativos, meses %s; remuneração R$ %.2f mi; gabinetes R$ %.2f mi; %d aposentados (R$ %.2f mi no mês %d)",
             len(out_rows), meses, meta["totais"]["remuneracao_bruta"] / 1e6, meta["totais"]["gabinetes"] / 1e6,
             meta["aposentados"]["quantidade_ultimo_mes"], meta["aposentados"]["bruto_ultimo_mes"] / 1e6, ultimo)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(); ap.add_argument("--ano", type=int, required=True)
    run(ap.parse_args().ano)
