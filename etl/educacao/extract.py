"""
Educação — IDEB (Índice de Desenvolvimento da Educação Básica) por estado e município, última edição publicada pelo INEP.

    python -m etl.educacao.extract [--ano 2023]      # gera data/public/educacao.json

Fonte: INEP, planilhas de divulgação do IDEB (download.inep.gov.br/ideb/resultados/):
- divulgacao_brasil_ideb_<ano>.zip e divulgacao_regioes_ufs_ideb_<ano>.zip — 3 abas (anos iniciais, anos finais, ensino médio), por região/UF e rede
  (Total, Pública, Privada, Estadual, Municipal, Federal), com o IDEB observado de todas as edições (2005 → <ano>).
- divulgacao_{anos_iniciais,anos_finais,ensino_medio}_municipios_<ano>.zip — 1 linha por município × rede.
Cada zip traz o md5 do xlsx; conferimos.

IDEB = fluxo (taxa de aprovação) × desempenho (Saeb, português e matemática), escala 0–10. Bienal; o INEP divulga ~1 ano depois.
Município: usamos a rede PÚBLICA (estadual + municipal); escolas privadas não entram no IDEB municipal.
TLS: o certificado de download.inep.gov.br não fecha a cadeia em algumas máquinas; tentamos verificar e, se falhar, baixamos sem
verificação e conferimos o md5 publicado dentro do zip.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import httpx
import openpyxl

from etl.ufs import NOME_PARA_UF

log = logging.getLogger("etl.educacao")
PUB = Path("data/public")
BASE = "https://download.inep.gov.br/ideb/resultados/"
UA = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
ETAPAS = {"anos_iniciais": "ai", "anos_finais": "af", "ensino_medio": "em"}
ABREV = {"M. G. do Sul": "Mato Grosso do Sul", "R. G. do Norte": "Rio Grande do Norte", "R. G. do Sul": "Rio Grande do Sul"}  # como o INEP abrevia
REDES = {"Total": "total", "Pública": "publica", "Privada": "privada", "Estadual": "estadual", "Municipal": "municipal", "Federal": "federal"}


def baixar(c: httpx.Client, nome: str) -> bytes:
    url = BASE + nome
    try:
        r = c.get(url); r.raise_for_status(); return r.content
    except httpx.ConnectError as e:
        if "CERTIFICATE_VERIFY_FAILED" not in str(e):
            raise
        log.warning("TLS do INEP não verificou (%s); baixando sem verificação e conferindo md5", nome)
        with httpx.Client(headers=UA, timeout=600, follow_redirects=True, verify=False) as c2:
            r = c2.get(url); r.raise_for_status(); return r.content


def xlsx_do_zip(conteudo: bytes) -> bytes:
    z = zipfile.ZipFile(io.BytesIO(conteudo))
    xlsx = next(n for n in z.namelist() if n.endswith(".xlsx"))
    md5 = next((n for n in z.namelist() if n.startswith(("md5", xlsx.rsplit("/", 1)[0] + "/md5"))), None)
    dados = z.read(xlsx)
    if md5:
        esperado = re.search(r"[0-9a-f]{32}", z.read(md5).decode("utf-8", "ignore"))
        if esperado and hashlib.md5(dados).hexdigest() != esperado.group(0):
            raise RuntimeError(f"md5 divergente em {xlsx}")
    return dados


def _rede(s) -> str | None:
    return REDES.get(re.sub(r"\s*\(\d\)", "", str(s or "")).strip())


def _val(v):
    try:
        return round(float(v), 1)
    except (TypeError, ValueError):
        return None


def ler_ufs(xlsx: bytes) -> tuple[dict, dict, dict]:
    """Devolve (estados, regioes, brasil): uf → {etapa: {rede: {ano: ideb}}}."""
    wb = openpyxl.load_workbook(io.BytesIO(xlsx), read_only=True)
    estados: dict[str, dict] = {}; regioes: dict[str, dict] = {}; brasil: dict = {}
    for ws, etapa in zip(wb.worksheets, ETAPAS.values()):
        rows = ws.iter_rows(values_only=True)
        codigos = None
        for r in rows:
            if r and any(str(x).startswith("VL_OBSERVADO_") for x in r):
                codigos = [str(x) for x in r]; break
        obs = {i: int(m.group(1)) for i, c in enumerate(codigos) if (m := re.fullmatch(r"VL_OBSERVADO_(\d{4})", c))}
        for r in rows:
            if not r or not r[0]:
                continue
            nome, rede = ABREV.get(str(r[0]).strip(), str(r[0]).strip()), _rede(r[1])
            if not rede:
                continue
            serie = {str(a): _val(r[i]) for i, a in obs.items() if i < len(r) and _val(r[i]) is not None}
            if nome == "Brasil":
                alvo = brasil
            elif nome in NOME_PARA_UF:
                alvo = estados.setdefault(NOME_PARA_UF[nome], {"uf": NOME_PARA_UF[nome], "nome": nome})
            elif nome in ("Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"):
                alvo = regioes.setdefault(nome, {"nome": nome})
            else:
                continue
            alvo.setdefault(etapa, {})[rede] = serie
    return estados, regioes, brasil


def ler_municipios(xlsx: bytes, etapa: str, ano: int, acc: dict) -> None:
    wb = openpyxl.load_workbook(io.BytesIO(xlsx), read_only=True)
    rows = wb.worksheets[0].iter_rows(values_only=True)
    codigos = None
    for r in rows:
        if r and "SG_UF" in [str(x) for x in r]:
            codigos = [str(x) for x in r]; break
    i_uf, i_cod, i_nome, i_rede = (codigos.index(k) for k in ("SG_UF", "CO_MUNICIPIO", "NO_MUNICIPIO", "REDE"))
    i_obs = codigos.index(f"VL_OBSERVADO_{ano}")
    for r in rows:
        if not r or _rede(r[i_rede]) != "publica" or len(r) <= i_obs:
            continue
        v = _val(r[i_obs])
        if v is None:
            continue
        cod = int(float(r[i_cod]))
        m = acc.setdefault(cod, {"cod_ibge": cod, "nome": str(r[i_nome]).strip(), "uf": str(r[i_uf]).strip()})
        m[etapa] = v


def run(ano: int) -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers=UA, timeout=600, follow_redirects=True) as c:
        estados, regioes, _ = ler_ufs(xlsx_do_zip(baixar(c, f"divulgacao_regioes_ufs_ideb_{ano}.zip")))
        _, _, brasil = ler_ufs(xlsx_do_zip(baixar(c, f"divulgacao_brasil_ideb_{ano}.zip")))
        municipios: dict[int, dict] = {}
        for nome, etapa in ETAPAS.items():
            ler_municipios(xlsx_do_zip(baixar(c, f"divulgacao_{nome}_municipios_{ano}.zip")), etapa, ano, municipios)
            log.info("%s: %d municípios com IDEB público", nome, sum(1 for m in municipios.values() if etapa in m))
    dados = {"gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"), "ano": ano,
             "brasil": brasil, "regioes": list(regioes.values()), "estados": sorted(estados.values(), key=lambda e: e["uf"]),
             "municipios": sorted(municipios.values(), key=lambda m: m["cod_ibge"]),
             "fontes": {"inep": f"INEP, IDEB {ano}, planilhas de divulgação por região/UF e por município (rede pública)", "url": BASE}}
    out = PUB / "educacao.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    log.info("IDEB %d: Brasil AI %s, AF %s, EM %s; %d UFs; %d municípios", ano, brasil.get("ai", {}).get("total", {}).get(str(ano)),
             brasil.get("af", {}).get("total", {}).get(str(ano)), brasil.get("em", {}).get("total", {}).get(str(ano)), len(estados), len(municipios))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    ap = argparse.ArgumentParser(); ap.add_argument("--ano", type=int, default=2023)
    run(ap.parse_args().ano)
