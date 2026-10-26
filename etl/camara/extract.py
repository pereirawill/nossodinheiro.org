"""
Extração — API de Dados Abertos da Câmara (v2) e CSV anual da CEAP.

Uso:
    python -m etl.camara.extract deputados            # lista da legislatura atual
    python -m etl.camara.extract despesas --ano 2026  # via API (paginada, lenta)
    python -m etl.camara.extract ceap-bulk --ano 2026 # via CSV anual (rápido)

Saída: data/raw/<recurso>_<ano>.jsonl.gz  (uma linha por registro, sem transformação)

Decisões:
- API v2: paginação via `links[rel=next]`; `itens` máximo prático = 100.
- Retry exponencial em 429/5xx; respeita Retry-After.
- Sem cache esperto: cada execução é idempotente e sobrescreve o raw do ano.
  Rodar no Actions semanalmente é barato (513 deputados × ~5 páginas).
- Para séries históricas completas use `ceap-bulk` (um ZIP por ano).
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import logging
import sys
import time
import zipfile
from pathlib import Path
from typing import Iterator

import httpx

from .config import API_BASE, CEAP_BULK_CSV, LEGISLATURA_ATUAL

log = logging.getLogger("etl.camara.extract")
RAW = Path("data/raw")

HEADERS = {
    "accept": "application/json",
    "user-agent": "transparencia-br-etl/0.1 (+https://github.com/SEU_USUARIO/transparencia-br)",
}


class Client:
    def __init__(self, timeout: float = 60.0, max_retries: int = 6):
        self.http = httpx.Client(headers=HEADERS, timeout=timeout, follow_redirects=True)
        self.max_retries = max_retries

    def get_json(self, url: str, params: dict | None = None) -> dict:
        delay = 1.0
        for attempt in range(1, self.max_retries + 1):
            r = self.http.get(url, params=params)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                wait = float(r.headers.get("retry-after", delay))
                log.warning("HTTP %s em %s (tentativa %d) — aguardando %.1fs", r.status_code, r.url, attempt, wait)
                time.sleep(wait)
                delay = min(delay * 2, 60)
                continue
            r.raise_for_status()
        raise RuntimeError(f"Falha após {self.max_retries} tentativas: {url}")

    def paginate(self, path: str, params: dict) -> Iterator[dict]:
        """Itera sobre todas as páginas seguindo links[rel=next]."""
        url: str | None = f"{API_BASE}{path}"
        p: dict | None = {**params, "itens": 100, "pagina": 1}
        while url:
            body = self.get_json(url, p)
            yield from body.get("dados", [])
            nxt = next((l["href"] for l in body.get("links", []) if l.get("rel") == "next"), None)
            url, p = nxt, None  # o href do next já carrega os parâmetros


def write_jsonl(path: Path, rows: Iterator[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    log.info("%s: %d registros", path, n)
    return n


# --- comandos ---------------------------------------------------------------

def cmd_deputados(c: Client, legislatura: int) -> None:
    vistos: set[int] = set()

    def gen() -> Iterator[dict]:
        for row in c.paginate("/deputados", {"idLegislatura": legislatura, "ordem": "ASC", "ordenarPor": "nome"}):
            if row["id"] in vistos:   # a API repete o deputado a cada mudança de status/partido
                continue
            vistos.add(row["id"]); yield row

    write_jsonl(RAW / f"deputados_leg{legislatura}.jsonl.gz", gen())


def cmd_despesas(c: Client, ano: int, legislatura: int) -> None:
    dep_path = RAW / f"deputados_leg{legislatura}.jsonl.gz"
    if not dep_path.exists():
        cmd_deputados(c, legislatura)
    with gzip.open(dep_path, "rt", encoding="utf-8") as f:
        ids = [json.loads(l)["id"] for l in f]

    # sonda: resposta crua do primeiro deputado, para diagnóstico no log do Actions
    probe = c.get_json(f"{API_BASE}/deputados/{ids[0]}/despesas", {"ano": ano, "itens": 2})
    log.info("sonda despesas dep=%s ano=%s → %d itens; links=%s; exemplo=%s",
             ids[0], ano, len(probe.get("dados", [])), [l.get("rel") for l in probe.get("links", [])],
             json.dumps(probe.get("dados", [None])[0], ensure_ascii=False)[:300])

    def gen() -> Iterator[dict]:
        for i, dep_id in enumerate(ids, 1):
            for row in c.paginate(f"/deputados/{dep_id}/despesas", {"ano": ano, "ordem": "ASC", "ordenarPor": "mes"}):
                row["idDeputado"] = dep_id
                yield row
            if i % 25 == 0:
                log.info("despesas %d: %d/%d deputados", ano, i, len(ids))

    n = write_jsonl(RAW / f"despesas_api_{ano}.jsonl.gz", gen())
    if n == 0:
        raise SystemExit(f"nenhuma despesa retornada para {ano} — veja a sonda acima; "
                         f"se a API não tem {ano} ainda, rode com --ano {ano - 1}")


def cmd_ceap_bulk(c: Client, ano: int) -> None:
    """Baixa o CSV anual (Ano-YYYY.csv.zip) e converte para JSONL com os mesmos
    nomes de campo da API quando houver equivalente (ver transform.py)."""
    url = CEAP_BULK_CSV.format(ano=ano)
    log.info("baixando %s", url)
    r = c.http.get(url, headers={"accept": "*/*"})
    r.raise_for_status()
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
    with zf.open(name) as fh:
        text = io.TextIOWrapper(fh, encoding="utf-8-sig", newline="")
        reader = csv.DictReader(text, delimiter=";")

        def gen() -> Iterator[dict]:
            for row in reader:
                yield {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}

        write_jsonl(RAW / f"ceap_bulk_{ano}.jsonl.gz", gen())


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("deputados"); s.add_argument("--legislatura", type=int, default=LEGISLATURA_ATUAL)
    s = sub.add_parser("despesas"); s.add_argument("--ano", type=int, required=True); s.add_argument("--legislatura", type=int, default=LEGISLATURA_ATUAL)
    s = sub.add_parser("ceap-bulk"); s.add_argument("--ano", type=int, required=True)
    a = ap.parse_args(argv)

    c = Client()
    if a.cmd == "deputados":
        cmd_deputados(c, a.legislatura)
    elif a.cmd == "despesas":
        cmd_despesas(c, a.ano, a.legislatura)
    elif a.cmd == "ceap-bulk":
        cmd_ceap_bulk(c, a.ano)


if __name__ == "__main__":
    main(sys.argv[1:])
