"""
Indústria — o Brasil está se industrializando ou perdendo indústria?

    python -m etl.industria.extract            # gera data/public/industria.json

Quatro medidas, de propósito, porque nenhuma sozinha responde:

- **Peso da indústria de transformação no valor adicionado** (Banco Mundial, `NV.IND.MANF.ZS`), com os pares
  agropecuária, indústria total e serviços. **Só de 1995 em diante.** A série existe desde os anos 1960, mas é
  calculada a **preços correntes**, e sob hiperinflação a participação de um setor oscila com o preço relativo e não
  com a produção: ela dá 46,1% em 1979, 22,0% em 1980 e 32,4% em 1985. Isso não é desindustrialização e
  reindustrialização em seis anos — é ruído de preço. O arquivo guarda a série inteira e marca onde ela passa a
  servir, para quem quiser conferir.
- **Participação dos manufaturados nas exportações** (`TX.VAL.MANF.ZS.UN`), de 1962 em diante. É razão entre valores
  em dólar no comércio exterior, muito menos sensível à inflação doméstica — é a série longa que dá o arco inteiro.
- **Emprego na indústria** (`SL.IND.EMPL.ZS`, estimativa da OIT), de 1991 em diante: quanta gente trabalha nela.
- **Produção física industrial** (IBGE, PIM-PF, SIDRA **8888**, número-índice 2022 = 100, de 2002 em diante): o
  volume produzido, sem preço nenhum na conta. Responde "produzimos mais ou menos coisa que antes".

Mais o **conteúdo tecnológico** (`NV.MNF.TECH.ZS.UN`, média e alta tecnologia no valor adicionado industrial) e a
comparação com os agregados que o próprio Banco Mundial publica (mundo, renda alta, renda média e baixa, América
Latina), para separar o que é trajetória do Brasil do que é tendência mundial.

O que este painel **não** faz: dizer se desindustrializar é bom ou ruim, nem apontar causa. Publica as quatro séries
e a comparação internacional.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

log = logging.getLogger("etl.industria")
PUB = Path("data/public")
WB = "https://api.worldbank.org/v2"
SIDRA = "https://apisidra.ibge.gov.br/values/t/{t}/n1/all/v/{v}/p/all/c544/{c}?formato=json"
UA = {"user-agent": "nossodinheiro-etl/0.1 (+https://nossodinheiro.org)"}

# Ano a partir do qual a participação setorial a preços correntes é utilizável: depois do Plano Real, quando a
# inflação deixa de embaralhar os preços relativos de um ano para o outro.
ANO_CONFIAVEL = 1995

INDICADORES = {
    "transformacao_pct_va": ("NV.IND.MANF.ZS", "Indústria de transformação", "% do valor adicionado", True),
    "industria_pct_va": ("NV.IND.TOTL.ZS", "Indústria total (com extrativa e construção)", "% do valor adicionado", True),
    "agro_pct_va": ("NV.AGR.TOTL.ZS", "Agropecuária", "% do valor adicionado", True),
    "servicos_pct_va": ("NV.SRV.TOTL.ZS", "Serviços", "% do valor adicionado", True),
    "manufaturados_pct_exp": ("TX.VAL.MANF.ZS.UN", "Manufaturados nas exportações", "% das exportações de bens", False),
    "emprego_industria_pct": ("SL.IND.EMPL.ZS", "Emprego na indústria", "% das pessoas ocupadas", False),
    "tecnologia_pct_va_ind": ("NV.MNF.TECH.ZS.UN", "Média e alta tecnologia", "% do valor adicionado industrial", False),
}
# agregados publicados pelo próprio Banco Mundial; o de renda alta volta com iso3 vazio e casa pelo country.id
AGREGADOS = {"1W": "WLD", "XD": "HIC", "XO": "LMY", "ZJ": "LCN"}
NOME_AGREGADO = {"WLD": "Mundo", "HIC": "Países de renda alta", "LMY": "Renda média e baixa",
                 "LCN": "América Latina e Caribe"}
# PIM-PF: índice (2022=100) da indústria geral, da extrativa e da transformação
PIM = {"129314": "Indústria geral", "129315": "Indústrias extrativas", "129316": "Indústrias de transformação"}


def _wb(c: httpx.Client, indicador: str, paises: str) -> dict[str, dict[str, float]]:
    r = c.get(f"{WB}/country/{paises}/indicator/{indicador}", params={"format": "json", "per_page": "20000"})
    d = r.json()
    if not isinstance(d, list) or len(d) < 2:
        log.warning("Banco Mundial %s não respondeu série", indicador)
        return {}
    saida: dict[str, dict[str, float]] = {}
    for x in d[1]:
        if x["value"] is None:
            continue
        iso = x["countryiso3code"] or AGREGADOS.get(x["country"]["id"], "")
        if iso:
            saida.setdefault(iso, {})[x["date"]] = round(float(x["value"]), 3)
    return saida


def series(c: httpx.Client) -> dict:
    """As séries do Brasil e dos agregados, indicador por indicador."""
    paises = "BRA;" + ";".join(AGREGADOS)
    saida = {}
    for chave, (cod, nome, unidade, precos_correntes) in INDICADORES.items():
        bruto = _wb(c, cod, paises)
        brasil = bruto.get("BRA", {})
        # o Banco Mundial publica 0,00 onde não há dado nos primeiros anos; zero não é participação setorial
        brasil = {a: v for a, v in brasil.items() if v > 0.01}
        if not brasil:
            continue
        anos = sorted(brasil)
        saida[chave] = {
            "codigo": cod, "nome": nome, "unidade": unidade,
            "precos_correntes": precos_correntes,
            "desde": anos[0], "ate": anos[-1],
            "brasil": {a: brasil[a] for a in anos},
            "agregados": {NOME_AGREGADO[i]: {a: v for a, v in sorted(s.items()) if v > 0.01}
                          for i, s in bruto.items() if i in NOME_AGREGADO},
        }
    return saida


def producao_fisica(c: httpx.Client) -> dict:
    """Número-índice da produção física (PIM-PF), média anual, de 2002 em diante."""
    r = c.get(SIDRA.format(t=8888, v=12606, c=",".join(PIM)), headers=UA)
    if r.status_code != 200:
        log.warning("SIDRA 8888: HTTP %s", r.status_code)
        return {}
    por_ano: dict[str, dict[str, list[float]]] = {}
    for l in r.json()[1:]:
        cod, mes = str(l.get("D4C") or ""), str(l.get("D3C") or "")
        try:
            v = float(str(l.get("V")).replace(",", "."))
        except (TypeError, ValueError):
            continue
        if cod in PIM and len(mes) == 6:
            por_ano.setdefault(cod, {}).setdefault(mes[:4], []).append(v)
    saida = {}
    for cod, anos in por_ano.items():
        # só anos completos entram na média; o ano em curso fica de fora para não comparar 8 meses com 12
        medias = {a: round(sum(vs) / len(vs), 2) for a, vs in sorted(anos.items()) if len(vs) == 12}
        if medias:
            saida[cod] = {"nome": PIM[cod], "anual": medias,
                          "parcial": {a: round(sum(vs) / len(vs), 2) for a, vs in sorted(anos.items()) if len(vs) != 12}}
    return saida


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=240, follow_redirects=True, headers=UA) as c:
        indicadores = series(c)
        pim = producao_fisica(c)

    if "transformacao_pct_va" not in indicadores or not pim:
        raise SystemExit("faltou a série da indústria de transformação ou a produção física — fonte mudou?")

    dados = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "ano_confiavel": ANO_CONFIAVEL,
        "indicadores": indicadores,
        "producao_fisica": pim,
        "fontes": {
            "banco_mundial": "Banco Mundial, World Development Indicators: valor adicionado por setor "
                             "(NV.IND.MANF.ZS, NV.IND.TOTL.ZS, NV.AGR.TOTL.ZS, NV.SRV.TOTL.ZS), manufaturados nas "
                             "exportações (TX.VAL.MANF.ZS.UN), emprego na indústria (SL.IND.EMPL.ZS, estimativa da "
                             "OIT) e conteúdo tecnológico (NV.MNF.TECH.ZS.UN)",
            "pim": "IBGE, Pesquisa Industrial Mensal — Produção Física (SIDRA 8888), número-índice 2022 = 100",
        },
        "regras": [
            f"A participação setorial é medida a preços correntes. Antes de {ANO_CONFIAVEL} a inflação embaralha os "
            "preços relativos e a série oscila sem que a produção mude — por isso os gráficos de participação "
            "começam depois do Plano Real, e a série inteira fica no arquivo para conferência.",
            "A participação dos manufaturados nas exportações é razão entre valores em dólar e sofre muito menos com "
            "a inflação interna: é ela que dá o arco longo, de 1962 em diante.",
            "A produção física não tem preço na conta: é volume produzido, com 2022 = 100. O ano em curso fica fora "
            "da média anual, em campo separado.",
            "Perder participação não é o mesmo que produzir menos: um setor pode crescer e ainda assim encolher "
            "como fatia, se os outros crescerem mais. As quatro medidas estão juntas por isso.",
        ],
    }
    out = PUB / "industria.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    t = indicadores["transformacao_pct_va"]
    log.info("indústria: transformação %s%% em %s (série de %s a %s); PIM com %d recortes",
             t["brasil"][t["ate"]], t["ate"], t["desde"], t["ate"], len(pim))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
