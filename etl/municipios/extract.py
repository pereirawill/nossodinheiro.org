"""
Municípios e estados — despesa por função (SICONFI/Tesouro, API pública sem chave) e nº de vereadores (TSE).

    python -m etl.municipios.extract entes                 # lista de entes com população (SICONFI)
    python -m etl.municipios.extract dca --ano 2025        # despesa por função de cada município e estado (5.597 chamadas, ~25 min; mais de 2 em paralelo dá HTTP 429)
    python -m etl.municipios.extract vagas --ano 2024      # vagas de vereador por município (TSE, eleição de 2024)

Fontes:
- SICONFI, API Tesouro Transparente: `https://apidatalake.tesouro.gov.br/ords/siconfi/tt/entes` (cod_ibge, ente, uf, esfera,
  populacao, capital) e `.../tt/dca?an_exercicio=AAAA&no_anexo=DCA-Anexo I-E&id_ente=<cod_ibge>` (Declaração de Contas
  Anuais, anexo I-E = despesas por função). A API exige um ente por chamada. Guardamos só o nível "função" (01 Legislativa,
  02 Judiciária, 04 Administração, 10 Saúde, 12 Educação…) e o total, nas colunas empenhada, liquidada e paga.
- TSE, dados abertos "Consulta vagas": `https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_vagas/consulta_vagas_AAAA.zip`
  (CSV por UF; CD_CARGO 13 = vereador; SG_UE é o código TSE, não IBGE — casamos por UF + nome normalizado).

Saídas: data/raw/siconfi_entes.jsonl.gz; data/raw/siconfi_dca_<ano>.jsonl.gz (1 linha por ente × coluna × função;
retomável — entes já gravados são pulados); data/raw/tse_vagas_<ano>.jsonl.gz.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import logging
import re
import time
import unicodedata
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

from ..portal_transparencia.extract_emendas import write_jsonl

log = logging.getLogger("etl.municipios")
RAW = Path("data/raw")
API = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"
TSE_VAGAS = "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_vagas/consulta_vagas_{ano}.zip"
HEADERS = {"user-agent": "nossodinheiro-etl/0.1 (+https://nossodinheiro.org)", "accept": "application/json"}
ANEXO = "DCA-Anexo I-E"
COLUNAS = ("Despesas Empenhadas", "Despesas Liquidadas", "Despesas Pagas")


def normalizar(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9 ]+", " ", s).strip()


def cmd_entes() -> list[dict]:
    r = httpx.get(f"{API}/entes", headers=HEADERS, timeout=120); r.raise_for_status()
    entes = [{"cod_ibge": int(e["cod_ibge"]), "ente": e["ente"], "uf": e["uf"], "esfera": e["esfera"].strip(), "capital": str(e.get("capital", "")).strip() == "1",
              "regiao": e.get("regiao"), "populacao": e.get("populacao")} for e in r.json()["items"] if e["esfera"].strip() in ("M", "E", "D")]
    write_jsonl(RAW / "siconfi_entes.jsonl.gz", iter(entes))
    log.info("%d municípios, %d estados, %d DF", sum(e["esfera"] == "M" for e in entes), sum(e["esfera"] == "E" for e in entes), sum(e["esfera"] == "D" for e in entes))
    return entes


def _ler(path: Path) -> list[dict]:
    """Lê jsonl.gz; se o arquivo foi interrompido no meio (processo morto), aproveita as linhas completas."""
    out = []
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            for l in f:
                try:
                    out.append(json.loads(l))
                except json.JSONDecodeError:
                    break
    except EOFError:
        log.warning("%s truncado: %d linhas aproveitadas", path, len(out))
    return out


def _dca_ente(c: httpx.Client, ano: int, e: dict) -> list[dict]:
    for tentativa in range(1, 4):
        try:
            r = c.get(f"{API}/dca", params={"an_exercicio": ano, "no_anexo": ANEXO, "id_ente": e["cod_ibge"]})
            if r.status_code == 200:
                break
            log.warning("HTTP %s para %s (%s), tentativa %d", r.status_code, e["ente"], e["cod_ibge"], tentativa)
        except httpx.HTTPError as ex:
            log.warning("%s (%s): %s, tentativa %d", e["ente"], e["cod_ibge"], ex, tentativa)
        time.sleep(3 * tentativa)
    else:
        return [{"cod_ibge": e["cod_ibge"], "erro": "sem resposta"}]
    out = []
    for i in r.json().get("items", []):
        if i.get("rotulo") != "Total Geral da Despesa por Função" or i.get("coluna") not in COLUNAS:
            continue
        conta = i.get("conta", "")
        m = re.match(r"^(\d{2}) - (.+)$", conta)
        if i.get("cod_conta") == "TotalDespesas" and (m or conta.startswith("Despesas Exceto")):
            out.append({"cod_ibge": e["cod_ibge"], "ente": e["ente"], "uf": e["uf"], "esfera": e["esfera"], "populacao": i.get("populacao") or e.get("populacao"),
                        "exercicio": ano, "coluna": i["coluna"], "funcao_cod": m.group(1) if m else "00", "funcao": m.group(2) if m else "Total",
                        "valor": float(i.get("valor") or 0)})
    if not out:
        out.append({"cod_ibge": e["cod_ibge"], "erro": "sem DCA"})
    return out


def cmd_dca(ano: int, workers: int = 4) -> None:
    entes_path = RAW / "siconfi_entes.jsonl.gz"
    entes = _ler(entes_path) if entes_path.exists() else cmd_entes()
    out = RAW / f"siconfi_dca_{ano}.jsonl.gz"
    anteriores = _ler(out) if out.exists() else []
    feitos = {l["cod_ibge"] for l in anteriores}
    pendentes = [e for e in entes if e["cod_ibge"] not in feitos]
    log.info("%d entes; %d já gravados; %d a consultar", len(entes), len(feitos), len(pendentes))
    n_ok = n_vazio = 0
    with gzip.open(out, "wt", encoding="utf-8") as f, httpx.Client(headers=HEADERS, timeout=60) as c, ThreadPoolExecutor(max_workers=workers) as ex:
        for l in anteriores:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
        futs = {ex.submit(_dca_ente, c, ano, e): e for e in pendentes}
        for k, fut in enumerate(as_completed(futs), 1):
            linhas = fut.result()
            for l in linhas:
                f.write(json.dumps(l, ensure_ascii=False) + "\n")
            if "erro" in linhas[0]:
                n_vazio += 1
            else:
                n_ok += 1
            if k % 100 == 0:
                f.flush(); log.info("%d/%d consultados (%d com DCA, %d sem)", k, len(pendentes), n_ok, n_vazio)
    log.info("concluído: %d com DCA, %d sem DCA em %d → %s", n_ok, n_vazio, ano, out)


def cmd_vagas(ano: int) -> None:
    r = httpx.get(TSE_VAGAS.format(ano=ano), headers={"user-agent": HEADERS["user-agent"]}, timeout=300, follow_redirects=True); r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))

    def gen():
        for nome in z.namelist():
            if not nome.lower().endswith(".csv"):
                continue
            for row in csv.DictReader(io.StringIO(z.read(nome).decode("latin-1")), delimiter=";"):
                if row.get("DS_CARGO", "").strip().lower() == "vereador":
                    yield {"ano": ano, "uf": row["SG_UF"], "cod_tse": row["SG_UE"], "municipio": row["NM_UE"], "municipio_norm": normalizar(row["NM_UE"]), "vagas": int(row["QT_VAGA"])}

    write_jsonl(RAW / f"tse_vagas_{ano}.jsonl.gz", gen())


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("entes")
    s = sub.add_parser("dca"); s.add_argument("--ano", type=int, required=True); s.add_argument("--workers", type=int, default=2)  # 4+ provoca HTTP 429 na API do Tesouro
    s = sub.add_parser("vagas"); s.add_argument("--ano", type=int, default=2024)
    a = ap.parse_args(argv)
    if a.cmd == "entes":
        cmd_entes()
    elif a.cmd == "dca":
        cmd_dca(a.ano, a.workers)
    elif a.cmd == "vagas":
        cmd_vagas(a.ano)


if __name__ == "__main__":
    main()
