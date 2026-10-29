"""
Desenvolvimento por estado — quais estados mudaram mais, e desde quando dá para medir isso.

    python -m etl.desenvolvimento.extract        # gera data/public/desenvolvimento.json

Só entra aqui o que tem **série estadual comparável ao longo do tempo**, que é mais raro do que parece:

- **Educação** (IBGE, Censo Demográfico): percentual das pessoas de 25 anos ou mais com **ensino médio completo ou
  mais**, por UF, em 1991, 2000, 2010 e 2022. Mesma ressalva do painel de Educação: 1991 e 2000 publicam *anos de
  estudo* e 2010 e 2022 publicam *nível de instrução*; a equivalência da época (médio = 11 anos) é decisão nossa.
- **Segurança** (IBGE, indicador ODS 16.1.1, a partir do SIM/Ministério da Saúde): vítimas de homicídio por 100 mil
  habitantes, por UF, **de 2000 a 2024**. Não há série estadual comparável antes de 2000 nessa base.

O que **não** entra, e por quê:
- **Renda desde 1991**: o Censo de 1991 publica rendimento em **cruzeiro**, e entre lá e hoje houve cinco trocas de
  moeda e mudanças de metodologia. Comparar exigiria uma cadeia de conversões que não é dado, é estimativa.
- **Emprego formal por estado**: RAIS e CAGED têm quebras de série e mudanças de regra de declaração.
- **Saúde por estado antes de 2000**: o indicador de mortalidade infantil por UF do IBGE começa em 2000.

O saneamento por estado (esgoto na rede, 1991→2022) já é coletado em `etl/saneamento` e a página o lê de lá.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

from etl.ufs import UFS

log = logging.getLogger("etl.desenvolvimento")
PUB = Path("data/public")
SIDRA = "https://apisidra.ibge.gov.br/values/t/{t}/n3/all/v/{v}/p/{p}{c}?formato=json"
POR_UF = {str(cod): {"uf": sigla, "nome": nome} for cod, sigla, nome, _ in UFS}

# 25 anos ou mais com ensino médio completo ou mais, nos quatro Censos. As categorias mudam de régua no meio:
# 1991/2000 por anos de estudo (11 a 14 e 15 ou mais), 2010/2022 por nível de instrução.
IDADES_25 = {"1991": "1145,1146,1147,1148,1149,1150,1151,1152,1153,1154,1155,2503",
             "2000": "1145,3299,3300,3301,3302"}
CENSOS = [
    {"ano": "1991", "t": 142, "v": 138, "parte": f"/c58/{IDADES_25['1991']}/c71/1133,1137",
     "total": f"/c58/{IDADES_25['1991']}/c71/0", "regua": "anos de estudo"},
    {"ano": "2000", "t": 1974, "v": 138, "parte": f"/c58/{IDADES_25['2000']}/c71/1133,1137",
     "total": f"/c58/{IDADES_25['2000']}/c71/0", "regua": "anos de estudo"},
    {"ano": "2010", "t": 3547, "v": 1643, "parte": "/c2/0/c1568/9495,99713", "total": "/c2/0/c1568/0",
     "regua": "nível de instrução"},
    {"ano": "2022", "t": 10141, "v": 1643, "parte": "/c2/6794/c839/46583/c1568/9495,99713",
     "total": "/c2/6794/c839/46583/c1568/120704", "regua": "nível de instrução"},
]
HOMICIDIOS = {"t": 6606, "v": "all", "primeiro": "2000"}


def _num(v) -> float | None:
    try:
        f = float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return None if f < 0 else f


def _por_uf(c: httpx.Client, t: int, v, p: str, filtro: str) -> dict[str, float]:
    """Soma o valor por UF (a consulta pode trazer várias categorias; aqui elas se somam)."""
    r = c.get(SIDRA.format(t=t, v=v, p=p, c=filtro))
    if r.status_code != 200:
        log.warning("SIDRA t%s p%s respondeu HTTP %s", t, p, r.status_code)
        return {}
    d = r.json()
    if len(d) < 2:
        return {}
    cab, saida = d[0], {}
    for linha in d[1:]:
        reg = {cab[k]: linha[k] for k in linha}
        cod = reg.get("Unidade da Federação (Código)")
        valor = _num(reg.get("Valor"))
        if cod in POR_UF and valor is not None:
            saida[cod] = saida.get(cod, 0.0) + valor
    return saida


def educacao_por_uf(c: httpx.Client) -> dict:
    anos = {}
    for conf in CENSOS:
        parte = _por_uf(c, conf["t"], conf["v"], conf["ano"], conf["parte"])
        total = _por_uf(c, conf["t"], conf["v"], conf["ano"], conf["total"])
        linhas = {}
        for cod, t in total.items():
            if t and cod in parte:
                linhas[POR_UF[cod]["uf"]] = round(100 * parte[cod] / t, 2)
        if linhas:
            anos[conf["ano"]] = linhas
            log.info("Censo %s (%s): %d UFs, médio completo ou mais vai de %.1f%% a %.1f%%", conf["ano"],
                     conf["regua"], len(linhas), min(linhas.values()), max(linhas.values()))
    return anos


def homicidios_por_uf(c: httpx.Client) -> dict:
    periodos = c.get(f"https://servicodados.ibge.gov.br/api/v3/agregados/{HOMICIDIOS['t']}/periodos")
    anos = [p["id"] for p in periodos.json()] if periodos.status_code == 200 else []
    if not anos:
        return {}
    saida = {}
    for ano in (anos[0], anos[-1]):
        # a tabela publica a taxa por 100 mil; não somamos nada, cada UF tem uma linha
        linhas = _por_uf(c, HOMICIDIOS["t"], "13532", ano, "")   # taxa por 100 mil habitantes
        if linhas:
            saida[ano] = {POR_UF[cod]["uf"]: round(v, 2) for cod, v in linhas.items()}
            log.info("Homicídios %s: %d UFs, de %.1f a %.1f por 100 mil", ano, len(saida[ano]),
                     min(saida[ano].values()), max(saida[ano].values()))
    return saida


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=240, follow_redirects=True) as c:
        educacao = educacao_por_uf(c)
        homicidios = homicidios_por_uf(c)
    if not educacao:
        raise SystemExit("educação por UF não veio — o layout das tabelas do Censo mudou?")

    dados = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "educacao": {"anos": sorted(educacao), "por_uf": educacao,
                     "o_que_e": "% das pessoas de 25 anos ou mais com ensino médio completo ou mais",
                     "fonte": "IBGE, Censo Demográfico: tabelas 142 (1991), 1974 (2000), 3547 (2010) e 10141 (2022)",
                     "ressalva": "1991 e 2000 publicam anos de estudo; 2010 e 2022, nível de instrução. A "
                                 "equivalência (médio = 11 anos de estudo) é decisão nossa, não do IBGE."},
        "homicidios": {"anos": sorted(homicidios), "por_uf": homicidios,
                       "o_que_e": "vítimas de homicídio intencional por 100 mil habitantes",
                       "fonte": "IBGE, indicador ODS 16.1.1 (tabela 6606), a partir do Sistema de Informações sobre "
                                "Mortalidade do Ministério da Saúde",
                       "ressalva": "Não há série estadual comparável antes de 2000 nesta base."},
        "fora": [
            "Renda desde 1991: o Censo daquele ano publica rendimento em cruzeiro, e entre lá e hoje houve cinco "
            "trocas de moeda. A conversão seria estimativa nossa, não dado.",
            "Emprego formal por estado: RAIS e CAGED mudaram regra de declaração e têm quebras de série.",
            "Saúde por estado antes de 2000: o indicador de mortalidade infantil por UF do IBGE começa em 2000.",
        ],
    }
    out = PUB / "desenvolvimento.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    log.info("desenvolvimento por UF: educação %s; homicídios %s", sorted(educacao), sorted(homicidios))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
