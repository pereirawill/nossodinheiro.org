"""
Saúde — quem depende do SUS, quem tem plano, e os indicadores de saúde de cada estado.

    python -m etl.saude.extract            # gera data/public/saude.json

O dinheiro gasto em saúde não é baixado aqui: já vem dos ETLs existentes (União pela função 10 do SIOP, em
`poderes_funcao_<ano>.json`; estados e municípios pela DCA do SICONFI, em `estados_<ano>.json` e `municipios_<ano>.json`).
Este extrator busca só o que falta:

- **ANS** (Agência Nacional de Saúde Suplementar), dados abertos, "Taxa de cobertura de planos de saúde" (PDA 047):
  CSV por município × sexo × faixa etária com o número de beneficiários de planos de assistência médica e de planos
  exclusivamente odontológicos. Agregamos por UF e para as capitais. A coluna POPULACAO do próprio arquivo vem zerada
  na maior parte das linhas, por isso a taxa é calculada com a população do IBGE.
- **IBGE**, API SIDRA, indicadores de saúde por estado:
    7362 (Projeção da População): esperança de vida ao nascer e taxa de mortalidade infantil — é **projeção**, rotulada
         como tal na página, porque é a única série por UF que chega ao ano corrente;
    3834: taxa de mortalidade infantil observada, 2000–2016 (série encerrada pelo IBGE);
    6695 (ODS 3.2.1): mortalidade de menores de 5 anos; 6696 (ODS 3.2.2): mortalidade neonatal;
    6694 (ODS 3.1.1): razão de mortalidade materna. As três vêm do Sistema de Informações sobre Mortalidade (SIM) do
    Ministério da Saúde, compiladas pelo IBGE para os Objetivos de Desenvolvimento Sustentável.
- **IBGE**, estimativas de população (SIDRA 6579), por UF e município.

Beneficiário não é pessoa: quem tem dois planos conta duas vezes, e por isso a ANS admite taxa acima de 100% em alguns
municípios. A página diz isso.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import httpx

from etl.ufs import COD_PARA_UF, UF_PARA_NOME, normalizar

log = logging.getLogger("etl.saude")
PUB, RAW = Path("data/public"), Path("data/raw")
ANS = "https://dadosabertos.ans.gov.br/FTP/PDA/taxa_de_cobertura_de_planos_de_saude-047/pda-047-taxa_cobertura.csv"
SIDRA = "https://apisidra.ibge.gov.br/values/t/{t}/{n}/all/v/{v}/p/{p}{c}?formato=json"
SIDRA_POP = "https://apisidra.ibge.gov.br/values/t/6579/{n}/all/v/9324/p/{p}?formato=json"
META = "https://servicodados.ibge.gov.br/api/v3/agregados/{t}/metadados"
UA = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}

# Categorias do "Ano" na tabela 7362 (projeção). Fixas para não depender da API de metadados
# (servicodados.ibge.gov.br), que deu timeout a partir dos runners do GitHub em 27/10/2026. Conferir em
# META.format(t=7362) quando o IBGE publicar uma revisão nova da projeção.
ANOS_7362 = {2020: 49036, 2021: 49037, 2022: 49038, 2023: 49039, 2024: 49040, 2025: 49041, 2026: 49042,
             2027: 49043, 2028: 49044, 2029: 49045, 2030: 49046}

# indicadores das tabelas dos ODS (fonte primária: SIM/Ministério da Saúde, compilado pelo IBGE)
ODS = [
    ("menores5", 6695, 9731, "Mortalidade de menores de 5 anos", "óbitos por mil nascidos vivos"),
    ("neonatal", 6696, 9732, "Mortalidade neonatal (até 27 dias de vida)", "óbitos por mil nascidos vivos"),
    ("materna", 6694, 9730, "Razão de mortalidade materna", "óbitos por 100 mil nascidos vivos"),
]


def _num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def sidra(c: httpx.Client, url: str) -> list[dict]:
    erro = None
    for tentativa in range(3):
        try:
            r = c.get(url); r.raise_for_status()
            return r.json()[1:]
        except (httpx.TransportError, httpx.HTTPStatusError, ValueError) as e:
            erro = e; log.warning("SIDRA tentativa %d (%s): %s", tentativa + 1, url[-60:], e)
    raise erro


def populacao(c: httpx.Client, ano: int) -> tuple[dict, dict, str]:
    """População estimada por UF e município; o ano pedido, ou o último publicado."""
    p = str(ano) if len(sidra(c, SIDRA_POP.format(n="n3", p=ano))) else "last 1"
    ufs = {COD_PARA_UF[int(r["D1C"])]: int(r["V"]) for r in sidra(c, SIDRA_POP.format(n="n3", p=p))}
    linhas = sidra(c, SIDRA_POP.format(n="n6", p=p))
    muns = {int(r["D1C"]): int(r["V"]) for r in linhas}
    return ufs, muns, linhas[0]["D3N"]


def planos(c: httpx.Client, pop_uf: dict, pop_mun: dict, capitais: dict) -> dict:
    """Beneficiários de planos por UF e nas capitais, com a taxa sobre a população do IBGE."""
    RAW.mkdir(parents=True, exist_ok=True)
    destino = RAW / "ans_cobertura.csv"
    r = c.get(ANS); r.raise_for_status()
    destino.write_bytes(r.content)
    con = duckdb.connect()
    con.execute(f"""create view ans as select * from read_csv('{destino}', delim=';', header=true, decimal_separator=',',
                encoding='latin-1', types={{'BENEF_ASSISTENCIA_MEDICA':'BIGINT','BENEF_EXCLUS_ODONTOLOGICO':'BIGINT','CD_MUNICIPIO':'VARCHAR','PERIODO':'VARCHAR'}})""")
    referencia = con.execute("select max(PERIODO) from ans").fetchone()[0]
    por_uf = []
    for uf, med, odo in con.execute("""select SG_UF, sum(BENEF_ASSISTENCIA_MEDICA), sum(BENEF_EXCLUS_ODONTOLOGICO)
                                       from ans where PERIODO = (select max(PERIODO) from ans) group by 1 order by 1""").fetchall():
        pop = pop_uf.get(uf)
        por_uf.append({"uf": uf, "nome": UF_PARA_NOME.get(uf, "Não informado"), "beneficiarios": med, "odontologico": odo,
                       "populacao": pop, "taxa": round(100 * med / pop, 1) if pop else None})
    nao_informado = next((u for u in por_uf if u["uf"] not in UF_PARA_NOME), None)
    por_uf = [u for u in por_uf if u["uf"] in UF_PARA_NOME]
    # a ANS usa o código do município com 6 dígitos (sem o dígito verificador do IBGE)
    cap6 = {cod // 10: m for cod, m in capitais.items()}
    pop6 = {cod // 10: v for cod, v in pop_mun.items()}
    caps = []
    for cod, med in con.execute("""select CD_MUNICIPIO, sum(BENEF_ASSISTENCIA_MEDICA) from ans
                                  where PERIODO = (select max(PERIODO) from ans) group by 1""").fetchall():
        c_int = int(cod) if cod.isdigit() else -1
        if c_int in cap6:
            pop = pop6.get(c_int)
            caps.append({"cod_ibge": cap6[c_int]["cod_ibge"], "nome": cap6[c_int]["nome"], "uf": cap6[c_int]["uf"], "beneficiarios": med,
                         "populacao": pop, "taxa": round(100 * med / pop, 1) if pop else None})
    med_br = sum(u["beneficiarios"] for u in por_uf) + (nao_informado["beneficiarios"] if nao_informado else 0)
    odo_br = sum(u["odontologico"] for u in por_uf) + (nao_informado["odontologico"] if nao_informado else 0)
    pop_br = sum(p for p in pop_uf.values())
    return {"referencia": referencia, "brasil": {"beneficiarios": med_br, "odontologico": odo_br, "populacao": pop_br,
                                                 "taxa": round(100 * med_br / pop_br, 1)},
            "sem_municipio_informado": nao_informado["beneficiarios"] if nao_informado else 0,
            "por_uf": sorted(por_uf, key=lambda u: u["uf"]), "capitais": sorted(caps, key=lambda m: -(m["taxa"] or 0))}


def indicadores(c: httpx.Client) -> dict:
    out: dict = {}
    # projeção: esperança de vida e mortalidade infantil, ano mais recente até o atual
    ano_proj = max(a for a in ANOS_7362 if a <= datetime.now().year)
    cat = ANOS_7362[ano_proj]
    br = {r["D2N"]: _num(r["V"]) for r in sidra(c, SIDRA.format(t=7362, n="n1", v="2503,1940", p="all", c=f"/c2/6794/c1933/{cat}"))}
    uf_ev = {r["D1N"]: _num(r["V"]) for r in sidra(c, SIDRA.format(t=7362, n="n3", v=2503, p="all", c=f"/c2/6794/c1933/{cat}"))}
    uf_mi = {r["D1N"]: _num(r["V"]) for r in sidra(c, SIDRA.format(t=7362, n="n3", v=1940, p="all", c=f"/c2/6794/c1933/{cat}"))}
    out["projecao"] = {"ano": ano_proj, "esperanca_vida_brasil": next((v for k, v in br.items() if "Esperança" in k), None),
                       "mortalidade_infantil_brasil": next((v for k, v in br.items() if "mortalidade" in k), None),
                       "esperanca_vida_uf": uf_ev, "mortalidade_infantil_uf": uf_mi}
    # mortalidade infantil observada (série encerrada em 2016)
    serie = {r["D3N"]: _num(r["V"]) for r in sidra(c, SIDRA.format(t=3834, n="n1", v=1940, p="all", c=""))}
    out["mortalidade_infantil_observada"] = {"serie_brasil": {k: v for k, v in serie.items() if v is not None}}
    for chave, t, var, nome, unidade in ODS:
        br_serie = {r["D3N"]: _num(r["V"]) for r in sidra(c, SIDRA.format(t=t, n="n1", v=var, p="all", c=""))}
        br_serie = {k: v for k, v in br_serie.items() if v is not None}
        ano = max(br_serie) if br_serie else None
        ufs = {r["D1N"]: _num(r["V"]) for r in sidra(c, SIDRA.format(t=t, n="n3", v=var, p=ano or "last 1", c=""))}
        out[chave] = {"nome": nome, "unidade": unidade, "ano": int(ano) if ano else None, "brasil": br_serie.get(ano),
                      "serie_brasil": br_serie, "por_uf": {k: v for k, v in ufs.items() if v is not None}}
        log.info("%s: Brasil %.1f em %s (%d UFs)", chave, out[chave]["brasil"] or 0, ano, len(out[chave]["por_uf"]))
    return out


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    capitais = {m["cod_ibge"]: m for m in json.loads((PUB / "municipios_2025.json").read_text(encoding="utf-8")) if m.get("capital")} \
        if (PUB / "municipios_2025.json").exists() else {}
    with httpx.Client(headers=UA, timeout=600, follow_redirects=True) as c:
        ind = indicadores(c)
        pop_uf, pop_mun, ano_pop = populacao(c, datetime.now().year)
        pl = planos(c, pop_uf, pop_mun, capitais)
    dados = {"gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"), "ano_populacao": ano_pop,
             "planos": pl, "indicadores": ind, "populacao_uf": pop_uf,
             "fontes": {"ans": f"ANS, dados abertos, taxa de cobertura de planos de saúde (PDA 047), competência {pl['referencia']}",
                        "ibge_pop": f"IBGE, estimativas de população {ano_pop} (SIDRA 6579)",
                        "ibge_projecao": "IBGE, Projeção da População (SIDRA 7362): esperança de vida e mortalidade infantil — projeção",
                        "ibge_ods": "IBGE, indicadores dos Objetivos de Desenvolvimento Sustentável (SIDRA 6694, 6695, 6696), a partir do SIM/Ministério da Saúde",
                        "ibge_mi": "IBGE, taxa de mortalidade infantil observada (SIDRA 3834), série encerrada em 2016"}}
    out = PUB / "saude.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    log.info("planos %s: %.1f mi de beneficiários (%.1f%% da população); esperança de vida %.1f anos (projeção %d); %d capitais",
             pl["referencia"], pl["brasil"]["beneficiarios"] / 1e6, pl["brasil"]["taxa"], ind["projecao"]["esperanca_vida_brasil"] or 0,
             ind["projecao"]["ano"], len(pl["capitais"]))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
