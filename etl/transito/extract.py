"""
Trânsito — quantas pessoas morrem em acidente de trânsito no Brasil, desde 2000.

    python -m etl.transito.extract            # gera data/public/transito.json

**Duas contagens oficiais, que não batem** — e a diferença é o ponto:

1. **Sistema de Informações sobre Mortalidade (SIM)**, do Ministério da Saúde, publicado pelo IBGE como indicador
   **ODS 3.6.1** (SIDRA, tabela **4408**): conta **atestados de óbito** com causa de trânsito, por ano, sexo, faixa
   etária e estado, **desde 2000**. É a contagem mais completa: alcança quem morre dias depois, no hospital.
2. **Sinesp VDE**, do Ministério da Justiça: conta as mortes **registradas pelas polícias** estaduais. É o mesmo
   arquivo do painel de Segurança, e chega mais rápido — mas registra menos.

Em 2024 o SIM contou 37.150 mortes; o Sinesp, 25.074 em 2025. A página mostra as duas, com a diferença declarada.

A comparação internacional usa a estimativa da **OMS** publicada pelo Banco Mundial (indicador SH.STA.TRAF.P5, já
coletado em `etl/rankings`), que corrige o sub-registro de cada país — por isso não coincide com nenhuma das duas
contagens nacionais, e a página diz isso.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx

from etl.ufs import UFS

log = logging.getLogger("etl.transito")
PUB = Path("data/public")
SIDRA = "https://apisidra.ibge.gov.br/values/t/4408/{n}/all/v/{v}/p/{p}/c2/{sexo}/c58/{idade}?formato=json"
PERIODOS = "https://servicodados.ibge.gov.br/api/v3/agregados/4408/periodos"
V_OBITOS, V_TAXA = "11728", "9734"
TOTAL_SEXO, TOTAL_IDADE = "6794", "95253"
SEXOS = {"4": "homens", "5": "mulheres"}
POR_UF = {str(cod): {"sigla": s, "nome": n} for cod, s, n, _ in UFS}


def _num(v) -> float | None:
    try:
        f = float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return None if f < 0 else f


def _linhas(c: httpx.Client, nivel: str, var: str, periodo: str, sexo: str, idade: str) -> list[dict]:
    r = c.get(SIDRA.format(n=nivel, v=var, p=periodo, sexo=sexo, idade=idade))
    if r.status_code != 200:
        log.warning("SIDRA 4408 (%s, v%s, p%s) respondeu HTTP %s", nivel, var, periodo, r.status_code)
        return []
    d = r.json()
    if len(d) < 2:
        return []
    cab = d[0]
    return [{cab[k]: l[k] for k in l} for l in d[1:]]


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=180, follow_redirects=True) as c:
        anos = [p["id"] for p in c.get(PERIODOS).json()]
        ult = anos[-1]

        serie = {}
        for var, chave in ((V_OBITOS, "obitos"), (V_TAXA, "taxa")):
            for l in _linhas(c, "n1", var, "all", TOTAL_SEXO, TOTAL_IDADE):
                v = _num(l.get("Valor"))
                if v is not None:
                    serie.setdefault(l["Ano"], {})[chave] = v

        estados = {}
        for var, chave in ((V_OBITOS, "obitos"), (V_TAXA, "taxa")):
            for l in _linhas(c, "n3", var, ult, TOTAL_SEXO, TOTAL_IDADE):
                cod = l.get("Unidade da Federação (Código)")
                v = _num(l.get("Valor"))
                if cod in POR_UF and v is not None:
                    estados.setdefault(cod, {**POR_UF[cod]})[chave] = v

        por_sexo = {}
        for cod, rotulo in SEXOS.items():
            for l in _linhas(c, "n1", V_OBITOS, ult, cod, TOTAL_IDADE):
                v = _num(l.get("Valor"))
                if v is not None:
                    por_sexo[rotulo] = v

        idades = {}
        for l in _linhas(c, "n1", V_OBITOS, ult, TOTAL_SEXO, "all"):
            faixa = next((v for k, v in l.items() if k.startswith("Grupo de idade") and not k.endswith("(Código)")), "")
            v = _num(l.get("Valor"))
            if v is not None and faixa and faixa != "Total":
                idades[faixa] = v

    if not serie:
        raise SystemExit("SIDRA 4408 não devolveu a série — o layout mudou?")
    anos_serie = sorted(serie)
    dados = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "ultimo_ano": int(ult), "anos": anos_serie,
        "serie": {a: serie[a] for a in anos_serie},
        "estados": sorted(estados.values(), key=lambda x: -(x.get("taxa") or 0)),
        "por_sexo": por_sexo, "por_idade": idades,
        "fonte": "IBGE, indicador ODS 3.6.1 (tabela 4408 do SIDRA), a partir do Sistema de Informações sobre "
                 "Mortalidade (SIM) do Ministério da Saúde",
        "url": "https://sidra.ibge.gov.br/tabela/4408",
    }
    out = PUB / "transito.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    log.info("trânsito %s–%s: %s = %.0f mortes (%.1f por 100 mil); %d estados",
             anos_serie[0], ult, ult, serie[ult]["obitos"], serie[ult].get("taxa", 0), len(estados))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
