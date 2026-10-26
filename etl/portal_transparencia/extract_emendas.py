"""
Extração — Emendas parlamentares via API de Dados do Portal da Transparência (CGU).

Pré-requisito: chave gratuita em https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email
    export PORTAL_TRANSPARENCIA_KEY=...

Uso:
    python -m etl.portal_transparencia.extract_emendas inspect --ano 2025      # imprime campos reais da 1ª página
    python -m etl.portal_transparencia.extract_emendas emendas --ano 2025      # todas as emendas do ano
    python -m etl.portal_transparencia.extract_emendas documentos --ano 2025   # documentos de despesa de cada emenda

Saída: data/raw/emendas_<ano>.jsonl.gz, data/raw/emendas_documentos_<ano>.jsonl.gz

Fatos verificados (26/10/2026):
- Base: https://api.portaldatransparencia.gov.br/api-de-dados ; header `chave-api-dados`.
- Limite: 400 req/min (700 entre 00h-06h); estourar suspende a chave por 8h.
  Por isso o cliente usa um token bucket conservador (default 300/min) — e o
  job no Actions pode ser agendado na madrugada.
- Paginação: `pagina=N`; página vazia = fim. Tamanho de página fixo pelo servidor.
- Spec OpenAPI: https://api.portaldatransparencia.gov.br/v2/api-docs (confirme campos).

Schema esperado (confirmar com `inspect` antes de ajustar transform_emendas.py):
  /emendas: codigoEmenda, ano, tipoEmenda, autor, nomeAutor, numeroEmenda,
            localidadeDoGasto, funcao, subfuncao, valorEmpenhado, valorLiquidado,
            valorPago, valorRestoInscrito, valorRestoCancelado, valorRestoPago
            (valores em string pt-BR: "1.234.567,89")
  /emendas/documentos?codigoEmenda=: documentos de empenho/liquidação/pagamento,
            com fase, data, valor e favorecido — é daí que sai o "para onde foi".
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Iterator

import httpx

log = logging.getLogger("etl.portal.emendas")
BASE = "https://api.portaldatransparencia.gov.br/api-de-dados"
RAW = Path("data/raw")


class Client:
    def __init__(self, key: str, rpm: int = 300, max_retries: int = 6):
        self.http = httpx.Client(base_url=BASE, timeout=60, headers={
            "chave-api-dados": key, "accept": "application/json",
            "user-agent": "transparencia-br-etl/0.1",
        })
        self.min_interval = 60.0 / rpm
        self._last = 0.0
        self.max_retries = max_retries

    def get(self, path: str, params: dict) -> list[dict]:
        delay = 2.0
        for attempt in range(1, self.max_retries + 1):
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            r = self.http.get(path, params=params)
            if r.status_code == 200:
                return r.json()
            if r.status_code == 429:
                # NÃO insistir: 429 repetido vira suspensão de 8h. Espera longa.
                log.warning("429 em %s — pausando 120s (tentativa %d)", r.url, attempt)
                time.sleep(120)
                continue
            if r.status_code == 403:
                r.raise_for_status()  # restrito: não adianta repetir
            if r.status_code >= 500:
                log.warning("HTTP %s em %s — %.0fs", r.status_code, r.url, delay)
                time.sleep(delay); delay = min(delay * 2, 60)
                continue
            r.raise_for_status()
        raise RuntimeError(f"falha após {self.max_retries} tentativas: {path} {params}")

    def paginate(self, path: str, params: dict, max_pages: int = 100_000) -> Iterator[dict]:
        for pagina in range(1, max_pages + 1):
            rows = self.get(path, {**params, "pagina": pagina})
            if not rows:
                return
            yield from rows


def write_jsonl(path: Path, rows: Iterator[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n"); n += 1
    log.info("%s: %d registros", path, n)
    return n


def cmd_inspect(c: Client, ano: int) -> None:
    rows = c.get("/emendas", {"ano": ano, "pagina": 1})
    print(f"/emendas ano={ano}: {len(rows)} itens na página 1")
    if rows:
        print("campos:", sorted(rows[0].keys()))
        print("exemplo:", json.dumps(rows[0], ensure_ascii=False, indent=2))
        cod = rows[0].get("codigoEmenda")
        if cod:
            try:
                docs = c.get("/emendas/documentos", {"codigoEmenda": cod, "pagina": 1})
                print(f"/emendas/documentos codigoEmenda={cod}: {len(docs)} itens")
                if docs:
                    print("campos:", sorted(docs[0].keys()))
                    print("exemplo:", json.dumps(docs[0], ensure_ascii=False, indent=2))
            except httpx.HTTPStatusError as e:
                print(f"/emendas/documentos → HTTP {e.response.status_code}: endpoint restrito para esta chave "
                      f"(26/10/2026). Destino por município/favorecido via CSV 'Emendas parlamentares' do "
                      f"download-de-dados ou TransfereGov.")


def cmd_emendas(c: Client, ano: int) -> None:
    write_jsonl(RAW / f"emendas_{ano}.jsonl.gz", c.paginate("/emendas", {"ano": ano}))


def cmd_documentos(c: Client, ano: int) -> None:
    src = RAW / f"emendas_{ano}.jsonl.gz"
    if not src.exists():
        cmd_emendas(c, ano)
    with gzip.open(src, "rt", encoding="utf-8") as f:
        codigos = [json.loads(l)["codigoEmenda"] for l in f]
    log.info("%d emendas → buscando documentos (pode levar horas; respeita %.0f req/min)",
             len(codigos), 60 / c.min_interval)

    def gen() -> Iterator[dict]:
        for i, cod in enumerate(codigos, 1):
            for d in c.paginate("/emendas/documentos", {"codigoEmenda": cod}):
                d["codigoEmenda"] = cod
                yield d
            if i % 200 == 0:
                log.info("documentos: %d/%d emendas", i, len(codigos))

    write_jsonl(RAW / f"emendas_documentos_{ano}.jsonl.gz", gen())


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    key = os.environ.get("PORTAL_TRANSPARENCIA_KEY")
    if not key:
        sys.exit("defina PORTAL_TRANSPARENCIA_KEY (cadastro gratuito no Portal da Transparência)")
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["inspect", "emendas", "documentos"])
    ap.add_argument("--ano", type=int, required=True)
    ap.add_argument("--rpm", type=int, default=300)
    a = ap.parse_args(argv)
    c = Client(key, rpm=a.rpm)
    {"inspect": cmd_inspect, "emendas": cmd_emendas, "documentos": cmd_documentos}[a.cmd](c, a.ano)


if __name__ == "__main__":
    main(sys.argv[1:])
