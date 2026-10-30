"""
Carga tributária no mundo — quantos dias do ano cada país trabalha para pagar tributos.

    python -m etl.carga_mundo.extract            # gera data/public/carga_mundo.json

Fonte única: **OCDE, Global Revenue Statistics** (dataflow `DSD_REV_COMP_GLOBAL@DF_RSGLOBAL`, API SDMX pública),
série "Tax revenue, General government, Total tax revenue, % of GDP" — governo geral (todos os níveis) com previdência,
que é a definição comparável entre países. O Brasil está na base pela edição latino-americana da mesma publicação.

Por que não o Banco Mundial: a série dele (`GC.TAX.TOTL.GD.ZS`) é só do governo central e dá 15% para o Brasil — o
erro de construção que já está explicado em /comparacao/. Aqui todos os países são medidos pela mesma régua.

O mesmo dataflow traz o Brasil **por categoria de tributo desde 1990**, no governo geral — é a única série longa com
régua constante para os três níveis (a Receita publica por base, mas só a edição mais recente de cada ano, e cada
edição republica a série com PIB revisado). Dela sai o bloco `brasil_por_base`.

**Duas armadilhas dessa série, tratadas no código:**

1. **Quebra em 2002.** Até 2001 a OCDE deixa a maior parte do imposto sobre renda em "não alocável" (T_1300) e quase
   nada em pessoa física (T_1100 = 0,28% do PIB em 2001, 1,85% em 2002); o mesmo vale para a previdência (T_2400 cai
   de 5,41 para 0,03 e T_2200 sobe de 1,60 para 5,52). Não é política, é reclassificação. Por isso a série longa só
   publica os **seis agregados** (T_1000, T_2000, T_3000, T_4000, T_5000, T_6000), que atravessam a quebra; a
   abertura pessoa física × empresa vai separada, começando em 2002.
2. **Hiperinflação até 1994.** Como no painel de indústria, os anos anteriores ao Real medem outra coisa: 1994 dá
   29,10% do PIB e 1995, 26,77%. A série inteira fica no JSON e `ano_confiavel` marca onde o gráfico deve começar.

Conferência que o próprio dado oferece: a CPMF (1997–2007) aparece e some na linha de transações financeiras
(T_4400): 0,42% do PIB em 1996, 1,21% em 1997, 1,75% em 2007, 0,82% em 2008.

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
# Brasil por categoria de tributo, governo geral, % do PIB, desde 1990. O CTRY_SPECIFIC_REVENUE precisa ficar VAZIO:
# com `_T` nessa posição a API devolve NoResultsFound para as categorias (testado em 30/10/2026).
SDMX_BR = ("https://sdmx.oecd.org/public/rest/data/OECD.CTP.TPS,DSD_REV_COMP_GLOBAL@DF_RSGLOBAL,2.1/"
           "BRA.TAX_REV.S13.....A")
# Só os seis agregados atravessam a reclassificação de 2002 (ver cabeçalho).
AGREGADOS = {
    "T_1000": "Renda, lucro e ganho de capital",
    "T_2000": "Previdência (contribuições sociais)",
    "T_3000": "Folha de salários",
    "T_4000": "Propriedade",
    "T_5000": "Bens e serviços",
    "T_6000": "Outros tributos",
}
# Abertura que só existe depois da reclassificação — série própria, nunca no mesmo eixo da de cima.
DETALHE_POS_2002 = {
    "T_1100": "Renda de pessoas físicas",
    "T_1200": "Renda de empresas",
    "T_1300": "Renda não alocável entre pessoas e empresas",
}
CPMF = "T_4400"                 # transações financeiras: a CPMF entra em 1997 e sai em 2008 — serve de conferência
ANO_CONFIAVEL = 1995            # antes do Real a razão sobre o PIB mede preço relativo, não arrecadação
ANO_QUEBRA = 2002               # início do trecho em que a abertura por tipo de renda é comparável


def baixar(c: httpx.Client) -> list[dict]:
    r = c.get(SDMX, params={"startPeriod": "2000", "dimensionAtObservation": "AllDimensions",
                            "format": "csvfilewithlabels"}, headers=UA)
    if r.status_code != 200 or not r.text.startswith("STRUCTURE"):
        raise SystemExit(f"OCDE SDMX: HTTP {r.status_code} — {r.text[:120]!r}")
    return list(csv.DictReader(io.StringIO(r.text)))


def baixar_brasil(c: httpx.Client) -> list[dict]:
    r = c.get(SDMX_BR, params={"startPeriod": "1990", "dimensionAtObservation": "AllDimensions",
                               "format": "csvfilewithlabels"}, headers=UA)
    if r.status_code != 200 or not r.text.startswith("STRUCTURE"):
        raise SystemExit(f"OCDE SDMX (Brasil por base): HTTP {r.status_code} — {r.text[:120]!r}")
    return list(csv.DictReader(io.StringIO(r.text)))


def montar_brasil(linhas: list[dict]) -> dict:
    """Série do Brasil por categoria de tributo, em % do PIB, governo geral."""
    serie: dict[str, dict[int, float]] = {}
    for x in linhas:
        if x.get("UNIT_MEASURE") != "PT_B1GQ" or x.get("CTRY_SPECIFIC_REVENUE") != "_T" or not x.get("OBS_VALUE"):
            continue
        serie.setdefault(x["STANDARD_REVENUE"], {})[int(x["TIME_PERIOD"])] = round(float(x["OBS_VALUE"]), 2)
    if "_T" not in serie or not all(k in serie for k in AGREGADOS):
        raise SystemExit(f"OCDE: faltam categorias do Brasil — vieram {sorted(serie)[:8]}…")
    anos = sorted(serie["_T"])
    saida = {
        "anos": anos, "ano_confiavel": ANO_CONFIAVEL, "ano_quebra": ANO_QUEBRA,
        "total": {str(a): serie["_T"][a] for a in anos},
        "bases": [{"codigo": k, "nome": n, "serie": {str(a): serie[k][a] for a in anos if a in serie[k]}}
                  for k, n in AGREGADOS.items()],
        "tipos_de_renda": [{"codigo": k, "nome": n,
                            "serie": {str(a): serie[k][a] for a in anos if a in serie[k] and a >= ANO_QUEBRA}}
                           for k, n in DETALHE_POS_2002.items() if k in serie],
        "transacoes_financeiras": {str(a): serie[CPMF][a] for a in anos if a in serie.get(CPMF, {})},
    }
    # invariante: as partes têm de somar o total, senão a lista de agregados está incompleta
    for a in (ANO_CONFIAVEL, anos[-1]):
        partes = sum(serie[k].get(a, 0.0) for k in AGREGADOS)
        if abs(partes - serie["_T"][a]) > 0.05:
            raise SystemExit(f"OCDE Brasil {a}: partes somam {partes:.2f} e o total é {serie['_T'][a]:.2f}")
    return saida


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
        linhas_br = baixar_brasil(c)
    dados = montar(linhas)
    dados["brasil_por_base"] = montar_brasil(linhas_br)
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
    pb = dados["brasil_por_base"]
    log.info("carga no mundo: %d países; Brasil %s%% em %s; média OCDE %s%%", len(dados["paises"]), br["ultimo"],
             br["ultimo_ano"], (dados["ocde_media"] or {}).get("ultimo"))
    log.info("Brasil por base: %d anos (%d–%d), %d agregados", len(pb["anos"]), pb["anos"][0], pb["anos"][-1],
             len(pb["bases"]))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
