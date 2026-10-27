"""
Segurança — ocorrências registradas pelas polícias, por estado e município, com taxa por 100 mil habitantes.

    python -m etl.seguranca.extract [--ano 2025] [--serie-desde 2015]      # gera data/public/seguranca.json

Fonte: Ministério da Justiça e Segurança Pública, Sinesp VDE (Validador de Dados Estatísticos), "Base de Dados dos Gestores
Estaduais" — um xlsx por ano (bancovde-<ano>.xlsx, gov.br/mj), 1 linha por UF × município × evento × mês, colunas
feminino/masculino/nao_informado/total_vitima (vítimas) e total (ocorrências), e abrangência (Estadual, Polícia Federal, PRF).
População: IBGE, estimativas (SIDRA tabela 6579) por UF e município, do mesmo ano dos eventos (ou a última publicada).

Regras:
- Só abrangência "Estadual" (polícias civis e militares); PF e PRF ficam fora para não somar bases diferentes.
- Mortes (homicídio doloso, feminicídio, latrocínio, lesão seguida de morte, intervenção de agente do Estado, trânsito, suicídio)
  contadas em VÍTIMAS; roubos, furtos e estupros em OCORRÊNCIAS (campo `total`) quando não há vítimas informadas.
- Não inventamos "mortes violentas intencionais": cada evento é mostrado separado, como o MJ publica.
- Município: só o que o estado registrou por município; "NÃO INFORMADO" entra no total da UF e não no ranking municipal.
  Roubos e furtos de veículo só vêm por UF.
- Taxa = eventos no ano ÷ população estimada × 100 mil. Para municípios, listamos os com 100 mil habitantes ou mais (e todas as
  capitais): abaixo disso, um evento a mais ou a menos muda muito a taxa.
- São registros policiais: dependem de a vítima registrar e de cada estado alimentar o Sinesp; o próprio MJ avisa que os números
  podem mudar depois da publicação.
"""

from __future__ import annotations

import argparse
import io
import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import httpx
import openpyxl

from etl.ufs import COD_PARA_UF, UF_PARA_NOME, normalizar

log = logging.getLogger("etl.seguranca")
PUB, RAW = Path("data/public"), Path("data/raw")
VDE = "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados/bancovde-{ano}.xlsx/@@download/file"
UA = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
SIDRA_POP = "https://apisidra.ibge.gov.br/values/t/6579/{n}/all/v/9324/p/{p}?formato=json"
EVENTOS = {  # nome no VDE → chave, conta vítimas?
    "Homicídio doloso": ("homicidio_doloso", True), "Feminicídio": ("feminicidio", True), "Roubo seguido de morte (latrocínio)": ("latrocinio", True),
    "Lesão corporal seguida de morte": ("lesao_morte", True), "Morte por intervenção de Agente do Estado": ("intervencao_estado", True),
    "Morte no trânsito ou em decorrência dele (exceto homicídio doloso)": ("transito", True), "Suicídio": ("suicidio", True),
    "Tentativa de homicídio": ("tentativa_homicidio", True), "Estupro": ("estupro", False), "Estupro de vulnerável": ("estupro_vulneravel", False),
    "Roubo de veículo": ("roubo_veiculo", False), "Furto de veículo": ("furto_veiculo", False), "Roubo de carga": ("roubo_carga", False),
}
POP_MIN_MUNICIPIO = 100_000


def baixar(c: httpx.Client, ano: int) -> bytes:
    RAW.mkdir(parents=True, exist_ok=True)
    cache = RAW / f"bancovde-{ano}.xlsx"
    if cache.exists() and ano < datetime.now().year:
        return cache.read_bytes()
    erro = None
    for tentativa in range(4):  # o servidor do gov.br costuma cortar downloads grandes no meio
        try:
            r = c.get(VDE.format(ano=ano)); r.raise_for_status()
            cache.write_bytes(r.content)
            return r.content
        except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ReadTimeout) as e:
            erro = e; log.warning("VDE %d, tentativa %d: %s", ano, tentativa + 1, e)
    raise erro


def ler(xlsx: bytes) -> tuple[dict, dict, dict, set]:
    """Agrega o ano: (por_uf[uf][chave], por_mun[(uf, nome_norm)][chave], nomes[(uf, norm)] = nome, meses[uf])."""
    wb = openpyxl.load_workbook(io.BytesIO(xlsx), read_only=True)
    rows = wb.worksheets[0].iter_rows(values_only=True)
    hdr = [str(h) for h in next(rows)]
    i = {k: hdr.index(k) for k in ("uf", "municipio", "evento", "data_referencia", "total_vitima", "total", "abrangencia")}
    por_uf: dict = defaultdict(lambda: defaultdict(int)); por_mun: dict = defaultdict(lambda: defaultdict(int)); nomes = {}
    meses: dict = defaultdict(set)
    for r in rows:
        if r[i["abrangencia"]] != "Estadual":
            continue
        ev = EVENTOS.get(r[i["evento"]])
        if not ev:
            continue
        chave, vitimas = ev
        v = r[i["total_vitima"]] if vitimas else r[i["total"]]
        if v is None:
            v = r[i["total"]] if vitimas else r[i["total_vitima"]]
        v = int(v or 0)
        uf, mun = r[i["uf"]], str(r[i["municipio"]] or "").strip()
        por_uf[uf][chave] += v
        if chave == "homicidio_doloso" and r[i["data_referencia"]] is not None:
            meses[uf].add(str(r[i["data_referencia"]])[:7])
        if mun and mun != "NÃO INFORMADO":
            k = (uf, normalizar(mun)); por_mun[k][chave] += v; nomes[k] = mun
    return por_uf, por_mun, nomes, {u: len(m) for u, m in meses.items()}


def populacao(c: httpx.Client, ano: int) -> tuple[dict, dict, str]:
    """Estimativa do mesmo ano dos eventos; se o IBGE ainda não publicou, a última disponível."""
    d = c.get(SIDRA_POP.format(n="n3", p=ano)).json()
    p = str(ano) if len(d) > 1 else "last 1"
    ufs = {COD_PARA_UF[int(r["D1C"])]: int(r["V"]) for r in c.get(SIDRA_POP.format(n="n3", p=p)).json()[1:]}
    d = c.get(SIDRA_POP.format(n="n6", p=p)).json()
    muns = {}
    for r in d[1:]:
        nome, uf = r["D1N"].rsplit(" - ", 1)
        muns[(uf, normalizar(nome))] = {"cod_ibge": int(r["D1C"]), "nome": nome, "uf": uf, "populacao": int(r["V"])}
    return ufs, muns, d[1]["D3N"]


def taxa(n: int, pop: int) -> float | None:
    return round(n / pop * 100_000, 1) if pop else None


def run(ano: int, serie_desde: int | None) -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers=UA, timeout=600, follow_redirects=True) as c:
        pop_uf, pop_mun, ano_pop = populacao(c, ano)
        por_uf, por_mun, nomes, meses = ler(baixar(c, ano))
        serie = {}
        if serie_desde:
            for a in range(serie_desde, ano + 1):
                try:
                    pu = por_uf if a == ano else ler(baixar(c, a))[0]
                except httpx.HTTPError as e:
                    log.warning("VDE %d: %s", a, e); continue
                serie[str(a)] = {u: {"homicidio_doloso": d["homicidio_doloso"], "feminicidio": d.get("feminicidio", 0), "roubo_veiculo": d.get("roubo_veiculo", 0)} for u, d in pu.items()}
                log.info("VDE %d: %d homicídios dolosos", a, sum(d["homicidio_doloso"] for d in pu.values()))
    capitais = {m["cod_ibge"] for m in json.loads((PUB / "municipios_2025.json").read_text(encoding="utf-8")) if m.get("capital")} if (PUB / "municipios_2025.json").exists() else set()
    estados = []
    for uf in sorted(por_uf):
        d = dict(por_uf[uf]); p = pop_uf.get(uf)
        estados.append({"uf": uf, "nome": UF_PARA_NOME[uf], "populacao": p, "meses": meses.get(uf, 0), **d,
                        "taxa_homicidio": taxa(d.get("homicidio_doloso", 0), p), "taxa_feminicidio_100k": taxa(d.get("feminicidio", 0), p),
                        "taxa_roubo_veiculo": taxa(d.get("roubo_veiculo", 0), p)})
    municipios, sem_pop = [], 0
    for k, d in por_mun.items():
        m = pop_mun.get(k)
        if not m:
            sem_pop += 1; continue
        if m["populacao"] >= POP_MIN_MUNICIPIO or m["cod_ibge"] in capitais:
            h = d.get("homicidio_doloso", 0)
            municipios.append({**m, "capital": m["cod_ibge"] in capitais, "homicidio_doloso": h, "feminicidio": d.get("feminicidio", 0),
                               "latrocinio": d.get("latrocinio", 0), "lesao_morte": d.get("lesao_morte", 0), "transito": d.get("transito", 0),
                               "taxa_homicidio": taxa(h, m["populacao"])})
    municipios.sort(key=lambda m: (m["taxa_homicidio"] is None, m["taxa_homicidio"]))
    brasil = defaultdict(int)
    for d in por_uf.values():
        for k, v in d.items():
            brasil[k] += v
    pop_br = sum(pop_uf.values())
    dados = {"gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"), "ano": ano, "ano_populacao": ano_pop, "pop_min_municipio": POP_MIN_MUNICIPIO,
             "brasil": {**brasil, "populacao": pop_br, "taxa_homicidio": taxa(brasil["homicidio_doloso"], pop_br)},
             "estados": estados, "municipios": municipios, "municipios_sem_populacao": sem_pop, "serie_uf": serie,
             "fontes": {"mj": f"Ministério da Justiça e Segurança Pública, Sinesp VDE, base dos gestores estaduais {ano} (abrangência estadual)",
                        "ibge": f"IBGE, estimativas de população {ano_pop} (SIDRA 6579)"}}
    out = PUB / "seguranca.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    log.info("%d: %d homicídios dolosos (%.1f/100 mil); %d UFs; %d municípios ≥%d hab ou capitais; %d nomes sem população", ano, brasil["homicidio_doloso"],
             dados["brasil"]["taxa_homicidio"], len(estados), len(municipios), POP_MIN_MUNICIPIO, sem_pop)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    ap = argparse.ArgumentParser(); ap.add_argument("--ano", type=int, default=datetime.now().year - 1); ap.add_argument("--serie-desde", type=int, default=2015)
    a = ap.parse_args(); run(a.ano, a.serie_desde)
