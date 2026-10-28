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
- Censo 2022, tabelas 10292 e 10296: distribuição por classes de **salário mínimo** (a PNAD Contínua não publica assim),
  para ocupados (rendimento do trabalho) e para todos os moradores (rendimento domiciliar per capita).

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


VARIAVEIS = {7527: 10826, 7530: 10826, 7533: 10816, 7438: 10769, 7535: 10842, 7435: 10681}  # variável de valor de cada tabela
# (a segunda variável de cada tabela é o coeficiente de variação). Fixas para não depender de servicodados.ibge.gov.br
# (API de metadados), que deu timeout a partir dos runners do GitHub em 27/10/2026; conferir em META quando mudar.


def sidra(c: httpx.Client, t: int, n: str, v: int, p: str = "last 1", c_: str = "") -> list[dict]:
    erro = None
    for tentativa in range(3):
        try:
            r = c.get(SIDRA.format(t=t, n=n, v=v, p=p, c=c_)); r.raise_for_status()
            return r.json()[1:]
        except (httpx.TransportError, httpx.HTTPStatusError) as e:
            erro = e; log.warning("SIDRA t%s tentativa %d: %s", t, tentativa + 1, e)
    raise erro


def _uf(nome: str) -> str | None:
    return NOME_PARA_UF.get(nome.strip())


# --- Censo 2022: quantos ganham até um salário mínimo ------------------------------------------------------------
# A PNAD Contínua publica rendimento em reais (médias e percentis), não em classes de salário mínimo. Quem publica
# a distribuição por classes de salário mínimo é o CENSO DEMOGRÁFICO: tabela 10292 (ocupados, pelo rendimento de
# todos os trabalhos) e 10296 (todos os moradores, pelo rendimento domiciliar per capita). É de 2022 e vale o
# salário mínimo daquele ano — está rotulado na página.
CENSO = {"ocupados": (10292, 4090, 11915, "/c2/6794"), "moradores": (10296, 13604, 386, "/c2/6794/c86/0")}
CLASSES_SM = {  # rótulo do IBGE → (chave, teto em salários mínimos; None = classe aberta ou sem rendimento)
    "Até 1/4 de salário mínimo": ("ate_1_4", 0.25), "Mais de 1/4 a 1/2 salário mínimo": ("de_1_4_a_1_2", 0.5),
    "Mais de 1/2 a 1 salário mínimo": ("de_1_2_a_1", 1), "Mais de 1 a 2 salários mínimos": ("de_1_a_2", 2),
    "Mais de 2 a 3 salários mínimos": ("de_2_a_3", 3), "Mais de 3 a 5 salários mínimos": ("de_3_a_5", 5),
    "Mais de 5 a 10 salários mínimos": ("de_5_a_10", 10), "Mais de 10 a 15 salários mínimos": ("de_10_a_15", 15),
    "Mais de 15 a 20 salários mínimos": ("de_15_a_20", 20), "Mais de 20 salários mínimos": ("mais_de_20", None),
    "Sem rendimento": ("sem_rendimento", None),
}
SGS_SALARIO_MINIMO = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1619/dados?formato=json&dataInicial=01/01/{ano}"


def _censo_tabela(c: httpx.Client, chave: str, nivel: str) -> dict[str, dict]:
    """Classes de rendimento em salários mínimos por território (nivel n1 = Brasil, n3 = UFs)."""
    t, v, cl, filtros = CENSO[chave]
    linhas = sidra(c, t, nivel, v, p="2022", c_=f"/c{cl}/all{filtros}")
    saida: dict[str, dict] = {}
    for l in linhas:
        rotulo = (l.get("D4N") or "").strip()
        valor = _num(l.get("V"))
        if valor is None:
            continue
        local = (l.get("D1N") or "Brasil").strip()
        d = saida.setdefault(local, {"total": 0.0, "classes": {}})
        if rotulo == "Total":
            d["total"] = valor
        elif rotulo in CLASSES_SM:
            d["classes"][CLASSES_SM[rotulo][0]] = valor
        else:
            log.warning("classe de rendimento desconhecida na tabela %d: %r", t, rotulo)
    return saida


def censo_salario_minimo(c: httpx.Client) -> dict:
    """Quantos ocupados e quantos moradores vivem com até um salário mínimo, pelo Censo 2022 (Brasil e UFs)."""
    r = c.get(SGS_SALARIO_MINIMO.format(ano=2022)); r.raise_for_status()
    sm = [float(x["valor"]) for x in r.json() if x["data"].endswith("/2022")][-1]

    LIMITES = (1, 2, 3, 5, 10)      # "até N salários mínimos", acumulado; "sem rendimento" fica fora da soma

    def _ate(classes: dict[str, float], limite: float) -> float:
        return sum(v for ch, v in classes.items()
                   for teto in [next((t for _, (c2, t) in CLASSES_SM.items() if c2 == ch), None)]
                   if teto is not None and teto <= limite)

    def _bloco(d: dict) -> dict:
        total = d["total"] or sum(d["classes"].values())
        acum = {n: _ate(d["classes"], n) for n in LIMITES}
        return {"total": int(total),
                "classes": [{"chave": ch, "rotulo": rot, "teto_sm": teto, "pessoas": int(d["classes"].get(ch, 0)),
                             "pct": round(d["classes"].get(ch, 0) / total, 4) if total else None}
                            for rot, (ch, teto) in CLASSES_SM.items()],
                "acumulado": [{"teto_sm": n, "pessoas": int(acum[n]), "pct": round(acum[n] / total, 4) if total else None}
                              for n in LIMITES],
                "ate_1_sm": int(acum[1]), "pct_ate_1_sm": round(acum[1] / total, 4) if total else None,
                "ate_3_sm": int(acum[3]), "pct_ate_3_sm": round(acum[3] / total, 4) if total else None}

    brasil = {k: _bloco(_censo_tabela(c, k, "n1")["Brasil"]) for k in CENSO}
    por_uf: dict[str, dict] = {}
    for chave in CENSO:
        for nome, d in _censo_tabela(c, chave, "n3").items():
            uf = _uf(nome)
            if not uf:
                continue
            b = _bloco(d)
            por_uf.setdefault(uf, {"uf": uf, "nome": nome})[f"{chave}_pct_ate_1_sm"] = b["pct_ate_1_sm"]
            por_uf[uf][f"{chave}_ate_1_sm"] = b["ate_1_sm"]
            por_uf[uf][f"{chave}_pct_ate_3_sm"] = b["pct_ate_3_sm"]
            por_uf[uf][f"{chave}_ate_3_sm"] = b["ate_3_sm"]
            por_uf[uf][f"{chave}_total"] = b["total"]
    log.info("Censo 2022 (SM R$ %.2f): até 1 SM %.1f%% dos ocupados e %.1f%% dos moradores; até 3 SM %.1f%% e %.1f%%; %d UFs",
             sm, 100 * brasil["ocupados"]["pct_ate_1_sm"], 100 * brasil["moradores"]["pct_ate_1_sm"],
             100 * brasil["ocupados"]["pct_ate_3_sm"], 100 * brasil["moradores"]["pct_ate_3_sm"], len(por_uf))
    return {"ano": 2022, "salario_minimo": sm, **brasil, "por_uf": sorted(por_uf.values(), key=lambda d: d["uf"]),
            "fonte": "IBGE, Censo Demográfico 2022, tabelas 10292 (ocupados, rendimento de todos os trabalhos) e "
                     "10296 (moradores, rendimento domiciliar per capita), em classes de salário mínimo",
            "salario_minimo_fonte": "Banco Central, SGS série 1619 — salário mínimo mensal vigente em 2022"}


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
        v7527, v7530, v7533, v7438, v7535, v7435 = (VARIAVEIS[t] for t in (7527, 7530, 7533, 7438, 7535, 7435))
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
        censo = censo_salario_minimo(c)      # Censo 2022: classes de salário mínimo (a PNAD não publica assim)
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
        "censo_sm": censo,
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
