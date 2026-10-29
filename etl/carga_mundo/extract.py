"""
Carga tributária no mundo — quantos dias do ano cada país trabalha para pagar tributos.

    python -m etl.carga_mundo.extract            # gera data/public/carga_mundo.json

Fonte única: **OCDE, Global Revenue Statistics** (dataflow `DSD_REV_COMP_GLOBAL@DF_RSGLOBAL`, API SDMX pública),
série "Tax revenue, General government, Total tax revenue, % of GDP" — governo geral (todos os níveis) com previdência,
que é a definição comparável entre países. O Brasil está na base pela edição latino-americana da mesma publicação.

Por que não o Banco Mundial: a série dele (`GC.TAX.TOTL.GD.ZS`) é só do governo central e dá 15% para o Brasil — o
erro de construção que já está explicado em /comparacao/. Aqui todos os países são medidos pela mesma régua.

**Atenção à diferença de método para o Brasil**: a OCDE calcula 33,7% para 2024; o Tesouro, 32,22%; a Receita, 32,20%.
A diferença vem do que entra como "tributo" (a OCDE inclui contribuições que as fontes brasileiras classificam de outro
modo). A página de Impostos usa o número brasileiro no destaque e o da OCDE na comparação — e diz isso.
"""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

log = logging.getLogger("etl.carga_mundo")
PUB = Path("data/public")
UA = {"User-Agent": "nossodinheiro-etl/0.1 (+https://nossodinheiro.org)"}
# chave SDMX: REF_AREA.MEASURE.SECTOR.STANDARD_REVENUE.CTRY_SPECIFIC_REVENUE.UNIT_MEASURE.FREQ
# (todos os países) . receita tributária . governo geral . total . total . % do PIB . anual
SDMX = ("https://sdmx.oecd.org/public/rest/data/OECD.CTP.TPS,DSD_REV_COMP_GLOBAL@DF_RSGLOBAL,2.1/"
        ".TAX_REV.S13._T._T.PT_B1GQ.A")
NOMES_PT = Path("etl/rankings/paises_pt.json")
MEDIA_OCDE = "OECD_REP"


def baixar(c: httpx.Client) -> list[dict]:
    r = c.get(SDMX, params={"startPeriod": "2000", "dimensionAtObservation": "AllDimensions",
                            "format": "csvfilewithlabels"}, headers=UA)
    if r.status_code != 200 or not r.text.startswith("STRUCTURE"):
        raise SystemExit(f"OCDE SDMX: HTTP {r.status_code} — {r.text[:120]!r}")
    return list(csv.DictReader(io.StringIO(r.text)))


def montar(linhas: list[dict]) -> dict:
    nomes_pt = json.loads(NOMES_PT.read_text(encoding="utf-8")) if NOMES_PT.exists() else {}
    paises: dict[str, dict] = {}
    for x in linhas:
        if not x.get("OBS_VALUE"):
            continue
        iso = x["REF_AREA"]
        p = paises.setdefault(iso, {"nome": nomes_pt.get(iso) or x["Reference area"], "serie": {}})
        p["serie"][x["TIME_PERIOD"]] = round(float(x["OBS_VALUE"]), 2)
    for iso, p in paises.items():
        p["serie"] = dict(sorted(p["serie"].items()))
        p["ultimo_ano"] = max(p["serie"])
        p["ultimo"] = p["serie"][p["ultimo_ano"]]
    media = paises.pop(MEDIA_OCDE, None)
    if media:
        media["nome"] = "Média da OCDE"
    return {"paises": paises, "ocde_media": media}


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=300, follow_redirects=True) as c:
        linhas = baixar(c)
    dados = montar(linhas)
    if "BRA" not in dados["paises"] or len(dados["paises"]) < 100:
        raise SystemExit(f"OCDE: vieram {len(dados['paises'])} países, sem Brasil? — a chave SDMX mudou?")
    dados.update({
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "fonte": "OCDE, Global Revenue Statistics — receita tributária do governo geral (todos os níveis, com "
                 "previdência) em % do PIB; API SDMX pública, dataflow DSD_REV_COMP_GLOBAL@DF_RSGLOBAL",
        "url": "https://data-explorer.oecd.org/?lc=en&fs[0]=Topic%2C1%7CTaxation%23TAX%23%7CTax%20revenue%23TAX_REV%23",
        "nota": "Para o Brasil, a OCDE calcula um valor maior que o do Tesouro e o da Receita (diferença de método no que "
                "conta como tributo). Na comparação entre países usa-se a OCDE para todos, pela mesma régua.",
    })
    out = PUB / "carga_mundo.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    br = dados["paises"]["BRA"]
    log.info("carga no mundo: %d países; Brasil %s%% em %s; média OCDE %s%%", len(dados["paises"]), br["ultimo"],
             br["ultimo_ano"], (dados["ocde_media"] or {}).get("ultimo"))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
