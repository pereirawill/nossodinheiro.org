"""
Renda — quem ganha quanto: setor público × privado, por posição na ocupação, e a distribuição (10% e 1% mais ricos).
Fonte única: IBGE, PNAD Contínua anual (API SIDRA, sem chave), valores a preços médios do último ano.

    python -m etl.renda.extract            # gera data/public/renda.json

Tabelas (todas 2012 → último ano):
- 4659  rendimento médio mensal real habitual do trabalho principal, por posição na ocupação e categoria do emprego
        (empregado privado com/sem carteira, doméstico, setor público — celetista, estatutário/militar —, empregador, conta própria).
        Brasil (série) e por UF (último ano).
- 7527  distribuição da massa de rendimento domiciliar per capita por classes de percentual (quanto da renda total fica com
        cada faixa: até o P10 … acima do P99). Brasil (série) e por UF (último ano, P90+ e P99+).
- 7530  idem, classes acumuladas (até o P50 = metade mais pobre).
- 7533  rendimento médio domiciliar per capita por classe de percentual (último ano).
- 7438  limites superiores das classes (quanto é preciso ter para entrar nos 10%, 5%, 1% mais ricos).
- 7535  rendimento médio dos ocupados por classes de percentual (o 1% dos trabalhadores que mais ganha).
- 7435  índice de Gini do rendimento domiciliar per capita, Brasil (série) e UF.

"Setor público" na PNAD inclui servidores estatutários, militares e celetistas de órgãos públicos das três esferas; "setor privado"
exclui trabalhadores domésticos (classe própria). Rendimento = o que a pessoa diz receber habitualmente, líquido de nada: é bruto.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

from etl.ufs import NOME_PARA_UF

log = logging.getLogger("etl.renda")
PUB = Path("data/public")
SIDRA = "https://apisidra.ibge.gov.br/values/t/{t}/{n}/all/v/{v}/p/{p}{c}?formato=json"
META = "https://servicodados.ibge.gov.br/api/v3/agregados/{t}/metadados"

POSICOES = {  # código da classificação 11913 → chave
    96165: "total", 31722: "privado_com_carteira", 31723: "privado_sem_carteira", 31724: "domestico", 31727: "publico",
    31728: "publico_celetista_com_carteira", 31729: "publico_sem_carteira", 31730: "publico_estatutario_militar",
    96170: "empregador", 45934: "empregador_cnpj", 45935: "empregador_sem_cnpj", 96171: "conta_propria", 45936: "conta_propria_cnpj", 45937: "conta_propria_sem_cnpj",
}
CLASSES = {"Total": "total", "Até o P10": "ate_p10", "Maior que o P10 até o P20": "p10_p20", "Maior que o P20 até o P30": "p20_p30", "Maior que o P30 até o P40": "p30_p40",
           "Maior que o P40 até o P50": "p40_p50", "Maior que o P50 até o P60": "p50_p60", "Maior que o P60 até o P70": "p60_p70", "Maior que o P70 até o P80": "p70_p80",
           "Maior que o P80 até o P90": "p80_p90", "Maior que o P90": "p90_mais", "Maior que o P90 até o P95": "p90_p95", "Maior que o P95 até o P99": "p95_p99", "Maior que o P99": "p99_mais"}


def _num(v: str) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _var(c: httpx.Client, t: int) -> int:
    """Primeira variável (a de valor; a segunda é o coeficiente de variação)."""
    return c.get(META.format(t=t)).json()["variaveis"][0]["id"]


def sidra(c: httpx.Client, t: int, n: str, v: int, p: str = "last 1", c_: str = "") -> list[dict]:
    r = c.get(SIDRA.format(t=t, n=n, v=v, p=p, c=c_)); r.raise_for_status()
    return r.json()[1:]


def _uf(nome: str) -> str | None:
    return NOME_PARA_UF.get(nome.strip())


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=180) as c:
        # 1. posição na ocupação — Brasil, série
        pos_serie: dict[str, dict[str, float]] = {k: {} for k in POSICOES.values()}
        nomes = {}
        for r in sidra(c, 4659, "n1", 5932, "all", "/c11913/all"):
            k = POSICOES.get(int(r["D4C"]))
            if k and _num(r["V"]) is not None:
                pos_serie[k][r["D3N"]] = _num(r["V"]); nomes[k] = r["D4N"]
        ano = max(pos_serie["total"])
        # por UF, último ano
        por_uf: dict[str, dict] = {}
        for r in sidra(c, 4659, "n3", 5932, "last 1", "/c11913/all"):
            k, uf = POSICOES.get(int(r["D4C"])), _uf(r["D1N"])
            if k and uf and _num(r["V"]) is not None:
                por_uf.setdefault(uf, {"uf": uf, "nome": r["D1N"]})[k] = _num(r["V"])
        # 2. distribuição da renda domiciliar per capita
        v7527, v7530, v7533, v7438, v7535, v7435 = (_var(c, t) for t in (7527, 7530, 7533, 7438, 7535, 7435))
        massa_serie: dict[str, dict[str, float]] = {}
        for r in sidra(c, 7527, "n1", v7527, "all", "/c1019/all"):
            k = CLASSES.get(r["D4N"].strip())
            if k and _num(r["V"]) is not None:
                massa_serie.setdefault(k, {})[r["D3N"]] = _num(r["V"])
        metade = {r["D3N"]: _num(r["V"]) for r in sidra(c, 7530, "n1", v7530, "all", "/c1042/49276") if _num(r["V"]) is not None}  # até o P50
        ano_d = max(massa_serie["p99_mais"])
        classes = []
        media = {CLASSES.get(r["D4N"].strip()): _num(r["V"]) for r in sidra(c, 7533, "n1", v7533, "last 1", "/c1019/all")}
        for nome, k in CLASSES.items():
            if k != "total" and k in massa_serie:
                classes.append({"classe": k, "nome": nome, "massa_pct": massa_serie[k].get(ano_d), "renda_media": media.get(k)})
        limites = {r["D4N"].strip(): _num(r["V"]) for r in sidra(c, 7438, "n1", v7438, "last 1", "/c1019/all") if _num(r["V"]) is not None}
        ocupados = {}
        for r in sidra(c, 7535, "n1", v7535, "last 1", "/c1043/all"):
            k = CLASSES.get(r["D4N"].strip())
            if k and _num(r["V"]) is not None:
                ocupados[k] = _num(r["V"])
        gini_serie = {r["D3N"]: _num(r["V"]) for r in sidra(c, 7435, "n1", v7435, "all") if _num(r["V"]) is not None}
        gini_uf = {_uf(r["D1N"]): _num(r["V"]) for r in sidra(c, 7435, "n3", v7435, "last 1") if _uf(r["D1N"]) and _num(r["V"]) is not None}
        massa_uf: dict[str, dict] = {}
        for r in sidra(c, 7527, "n3", v7527, "last 1", "/c1019/49255,49258,49246"):
            uf, k = _uf(r["D1N"]), CLASSES.get(r["D4N"].strip())
            if uf and k and _num(r["V"]) is not None:
                massa_uf.setdefault(uf, {})[k] = _num(r["V"])
        renda_media_uf = {_uf(r["D1N"]): _num(r["V"]) for r in sidra(c, 7533, "n3", v7533, "last 1", "/c1019/49243") if _uf(r["D1N"])}
    for uf, d in por_uf.items():
        d["gini"] = gini_uf.get(uf); d["renda_domiciliar_pc"] = renda_media_uf.get(uf)
        d["massa_p90_mais"] = massa_uf.get(uf, {}).get("p90_mais"); d["massa_p99_mais"] = massa_uf.get(uf, {}).get("p99_mais"); d["massa_ate_p10"] = massa_uf.get(uf, {}).get("ate_p10")
    dados = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"), "ano": ano, "ano_distribuicao": ano_d,
        "posicoes": [{"chave": k, "nome": nomes.get(k), "valor": s.get(ano), "serie": s} for k, s in pos_serie.items() if s],
        "por_uf": sorted(por_uf.values(), key=lambda d: d["uf"]),
        "distribuicao": {"classes": classes, "massa_serie": {k: massa_serie[k] for k in ("ate_p10", "p90_mais", "p99_mais") if k in massa_serie},
                         "metade_mais_pobre_serie": metade, "limites": limites, "ocupados_por_classe": ocupados,
                         "gini": {"brasil": gini_serie.get(ano_d), "serie": gini_serie}},
        "fontes": {"ibge": "IBGE, PNAD Contínua anual (SIDRA): tabelas 4659, 7527, 7530, 7533, 7438, 7535, 7435; valores a preços médios do último ano"},
    }
    out = PUB / "renda.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    log.info("renda %s: público R$ %.0f × privado c/ carteira R$ %.0f; 1%% mais rico com %.1f%% da renda (%s); %d UFs", ano, pos_serie["publico"].get(ano, 0),
             pos_serie["privado_com_carteira"].get(ano, 0), massa_serie["p99_mais"].get(ano_d, 0), ano_d, len(por_uf))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
