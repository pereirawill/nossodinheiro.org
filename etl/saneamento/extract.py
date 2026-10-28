"""
Saneamento — quantos domicílios têm água da rede, esgoto ligado à rede e lixo coletado, desde 1991.

    python -m etl.saneamento.extract            # gera data/public/saneamento.json

Fonte única: **IBGE, via API SIDRA, sem chave**. Duas pesquisas diferentes, nunca emendadas numa linha só:

- **Censo Demográfico** (1991, 2000, 2010, 2022): recenseia todos os domicílios. É a régua longa.
- **PNAD Contínua anual** (2016→): amostra, com margem de erro publicada pelo próprio IBGE (coeficiente de variação).
  **Não há 2020 nem 2021** — a pesquisa domiciliar foi interrompida na pandemia; o gráfico mostra o buraco.

**Por que não dá para começar em 1988**: o Censo mais próximo é o de 1991. A PNAD antiga (até 2015) perguntava de
outro jeito e não está no mesmo recorte. Mesmo entre os Censos a pergunta mudou — em 1991 era "instalação sanitária"
e o que se media era o escoadouro; em 2022 o IBGE separa "rede geral" de "fossa ligada à rede". Por isso cada
pesquisa aparece com a sua cor e o seu rótulo, e o JSON guarda a categoria exata usada em cada ano.

**O que esta fonte NÃO mede**: se o esgoto coletado é tratado antes de voltar ao rio. Isso é declarado pelo prestador
do serviço ao SNIS (Ministério das Cidades), que é outra base, com outro método — e, por enquanto, não está aqui.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

from etl.ufs import UFS

log = logging.getLogger("etl.saneamento")
PUB = Path("data/public")
SIDRA = "https://apisidra.ibge.gov.br/values/t/{t}/{n}/all/v/{v}/p/{p}{c}?formato=json"
# colunas que o SIDRA devolve em toda consulta e que não são categoria da classificação pedida
ESTRUTURAIS = ("nível territorial", "unidade de medida", "brasil", "unidade da federação", "variável", "ano",
               "município", "valor")

# Para cada Censo, a tabela, a classificação e as categorias que somam "ligado à rede". Os códigos estão escritos
# aqui com o rótulo que o IBGE usa, porque mudam de um Censo para o outro — é a premissa mais importante do painel.
CENSO = {
    "1991": {"var": "96",
             "agua": (179, 61, ["1033", "1035"], "rede geral (com e sem canalização interna)"),
             "esgoto": (180, 1612, ["120451", "120460"], "rede geral (instalação exclusiva ou compartilhada)"),
             "lixo": (182, 67, ["2520"], "lixo coletado")},
    "2000": {"var": "96",
             "agua": (1442, 61, ["92853"], "rede geral"),
             "esgoto": (1444, 11558, ["92855"], "rede geral de esgoto ou pluvial"),
             "lixo": (1447, 67, ["2520"], "lixo coletado")},
    "2010": {"var": "96",
             "agua": (3391, 471, ["12214", "12217"], "água canalizada vinda da rede geral"),
             "esgoto": (1394, 11558, ["92855"], "rede geral de esgoto ou pluvial"),
             "lixo": None},
    "2022": {"var": "381",
             "agua": (6804, 301, ["31471"], "rede geral de distribuição"),
             "esgoto": (6805, 11558, ["72110"], "rede geral ou rede pluvial"),
             "lixo": (6892, 67, ["2520"], "lixo coletado")},
}
# PNAD Contínua: tabela, variável da contagem, variável do percentual, variável do coeficiente de variação
PNADC_AGUA = (9468, "9974", "12953", "12954")
PNADC_ESGOTO = (7192, 11558, "47930", "9986")
PNADC_TOTAL = (6731, "162", 825, "47937")
POR_UF = {str(cod): {"sigla": sigla, "nome": nome} for cod, sigla, nome, _ in UFS}


def _num(v) -> float | None:
    try:
        f = float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return None if f < 0 else f                      # o SIDRA usa negativos como marcador de ausência


def _sidra(c: httpx.Client, t: int, n: str, v: str, p: str, cl: int | None) -> list[dict]:
    r = c.get(SIDRA.format(t=t, n=n, v=v, p=p, c=f"/c{cl}/all" if cl else ""))
    if r.status_code != 200:
        log.warning("SIDRA tabela %s nível %s respondeu HTTP %s", t, n, r.status_code)
        return []
    dados = r.json()
    if len(dados) < 2:
        return []
    cab = dados[0]
    linhas = []
    for l in dados[1:]:
        linhas.append({cab[k]: l[k] for k in l})
    return linhas


def _coluna(linha: dict, pedaco: str) -> str:
    """Valor da coluna com aquele nome — sem pegar a coluna de código, que tem o mesmo prefixo."""
    for k, v in linha.items():
        if k.lower().startswith(pedaco) and not k.endswith("(Código)"):
            return v
    return ""


def _codigo(linha: dict, pedaco: str) -> str:
    for k, v in linha.items():
        if k.lower().startswith(pedaco) and k.endswith("(Código)"):
            return v
    return ""


def _em_unidades(linha: dict, valor: float) -> float:
    """A PNAD Contínua publica em mil unidades; o Censo, em unidades."""
    return valor * 1000 if "mil" in (linha.get("Unidade de Medida") or "").lower() else valor


def _categorias(linha: dict) -> list[tuple[str, str]]:
    """As colunas de categoria da linha, como (código, rótulo) — as outras são sempre as mesmas do SIDRA."""
    fora = tuple(ESTRUTURAIS)
    return [(v, linha.get(k[: -len(" (Código)")], "")) for k, v in linha.items()
            if k.endswith("(Código)") and not k.lower().startswith(fora)]


def _censo_tabela(c: httpx.Client, t: int, cl: int, var: str, ano: str, cats: list[str], nivel: str) -> dict:
    """Devolve {codigo_local: {"total": n, "rede": n}} para uma tabela de Censo. A tabela pode ter mais de uma
    classificação (tipo do domicílio, situação, canalização); só interessa a linha em que as outras estão no Total."""
    saida: dict[str, dict[str, float]] = {}
    for linha in _sidra(c, t, nivel, var, ano, cl):
        valor = _num(linha.get("Valor"))
        if valor is None:
            continue
        local = linha.get("Unidade da Federação (Código)") or linha.get("Brasil (Código)") or "1"
        cat = _categorias(linha)
        reg = saida.setdefault(local, {"total": 0.0, "rede": 0.0})
        if all(rot.strip().lower() == "total" for _, rot in cat):
            reg["total"] = valor
            continue
        escolhidas = [cod for cod, _ in cat if cod in cats]
        outras_no_total = all(rot.strip().lower() == "total" for cod, rot in cat if cod not in cats)
        if escolhidas and outras_no_total:
            reg["rede"] += valor
    return saida


def coletar_censo(c: httpx.Client) -> tuple[dict, dict]:
    brasil: dict[str, dict] = {}
    por_uf: dict[str, list] = {}
    for ano, conf in CENSO.items():
        reg: dict = {"ano": int(ano)}
        ufs: dict[str, dict] = {}
        for tema in ("agua", "esgoto", "lixo"):
            if not conf.get(tema):
                reg[tema] = None
                continue
            t, cl, cats, rotulo = conf[tema]
            n1 = _censo_tabela(c, t, cl, conf["var"], ano, cats, "n1")
            if not n1:
                log.warning("Censo %s: tabela %s de %s não veio", ano, t, tema)
                reg[tema] = None
                continue
            dado = next(iter(n1.values()))
            reg[tema] = {"total": dado["total"], "rede": dado["rede"],
                         "pct": round(100 * dado["rede"] / dado["total"], 2) if dado["total"] else None,
                         "categoria": rotulo, "tabela": t}
            for cod, d in _censo_tabela(c, t, cl, conf["var"], ano, cats, "n3").items():
                if cod in POR_UF and d["total"]:
                    ufs.setdefault(cod, {"uf": POR_UF[cod]["sigla"], "nome": POR_UF[cod]["nome"]})[tema] = \
                        round(100 * d["rede"] / d["total"], 2)
        brasil[ano] = reg
        por_uf[ano] = sorted(ufs.values(), key=lambda x: x["uf"])
        log.info("Censo %s: água %s%%, esgoto %s%%", ano,
                 (reg.get("agua") or {}).get("pct"), (reg.get("esgoto") or {}).get("pct"))
    return brasil, por_uf


def coletar_pnadc(c: httpx.Client) -> tuple[list, dict]:
    t_ag, v_ag, v_pct, v_cv = PNADC_AGUA
    t_es, cl_es, cat_es, v_es = PNADC_ESGOTO
    t_tot, v_tot, cl_tot, cat_tot = PNADC_TOTAL

    def mapa(linhas: list[dict], filtro_cat: str | None, cl_nome: str | None) -> dict[tuple[str, str], float]:
        saida = {}
        for l in linhas:
            valor = _num(l.get("Valor"))
            if valor is None:
                continue
            if filtro_cat is not None and _codigo(l, cl_nome or "") != filtro_cat:
                continue
            if (_coluna(l, "situação do domicílio") or "Total") != "Total":
                continue
            local = l.get("Unidade da Federação (Código)") or l.get("Brasil (Código)") or "1"
            saida[(local, _coluna(l, "ano"))] = _em_unidades(l, valor)
        return saida

    serie, por_uf = [], {}
    for nivel in ("n1", "n3"):
        agua = mapa(_sidra(c, t_ag, nivel, v_ag, "all", None), None, None)
        pct = mapa(_sidra(c, t_ag, nivel, v_pct, "all", None), None, None)
        cv = mapa(_sidra(c, t_ag, nivel, v_cv, "all", None), None, None)
        esgoto = mapa(_sidra(c, t_es, nivel, v_es, "all", cl_es), cat_es, "tipo de esgotamento")
        total = mapa(_sidra(c, t_tot, nivel, v_tot, "all", cl_tot), cat_tot, "principal fonte")
        for (local, ano), tot in sorted(total.items(), key=lambda x: (x[0][1], x[0][0])):
            if not tot:
                continue
            reg = {"ano": int(ano), "domicilios": tot,
                   "agua_rede": agua.get((local, ano)), "agua_pct": pct.get((local, ano)),
                   "agua_cv": cv.get((local, ano)),
                   "esgoto_rede": esgoto.get((local, ano)),
                   "esgoto_pct": round(100 * esgoto[(local, ano)] / tot, 2) if esgoto.get((local, ano)) else None}
            if nivel == "n1":
                serie.append(reg)
            elif local in POR_UF:
                por_uf.setdefault(ano, []).append({**reg, "uf": POR_UF[local]["sigla"],
                                                   "nome": POR_UF[local]["nome"]})
    serie.sort(key=lambda x: x["ano"])
    log.info("PNAD Contínua: %s anos (%s→%s), sem %s", len(serie), serie[0]["ano"], serie[-1]["ano"],
             sorted({2016 + i for i in range(serie[-1]["ano"] - 2015)} - {x["ano"] for x in serie}))
    return serie, por_uf


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=180, follow_redirects=True) as c:
        censo, censo_uf = coletar_censo(c)
        pnadc, pnadc_uf = coletar_pnadc(c)

    # A conferência que a página usa para responder "e se o dado for maquiado?": o mesmo ano medido por dois
    # instrumentos diferentes do mesmo instituto — o Censo recenseia todo mundo, a PNAD é amostra com margem de erro.
    comparacao = {}
    p22 = next((x for x in pnadc if x["ano"] == 2022), None)
    if p22 and censo.get("2022"):
        for tema, chave in (("agua", "agua_pct"), ("esgoto", "esgoto_pct")):
            c22 = (censo["2022"].get(tema) or {}).get("pct")
            if c22 is not None and p22.get(chave) is not None:
                comparacao[tema] = {"censo": c22, "pnadc": p22[chave], "diferenca_pp": round(p22[chave] - c22, 2),
                                    "cv_pnadc": p22.get("agua_cv") if tema == "agua" else None}

    dados = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "censo": censo, "censo_uf": censo_uf, "pnadc": pnadc, "pnadc_uf": pnadc_uf,
        "comparacao_2022": comparacao,
        "fonte": "IBGE: Censo Demográfico (1991, 2000, 2010 e 2022) e PNAD Contínua anual, pela API SIDRA",
        "url": "https://sidra.ibge.gov.br/",
        "nota_categorias": "A categoria somada como 'ligado à rede' muda de um Censo para o outro e está gravada em "
                           "censo.<ano>.<tema>.categoria; por isso as pesquisas não são emendadas numa série só.",
    }
    out = PUB / "saneamento.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    log.info("saneamento: Censo %s→%s, PNADC %s→%s", min(censo), max(censo), pnadc[0]["ano"], pnadc[-1]["ano"])
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
