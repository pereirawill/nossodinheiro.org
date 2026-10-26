"""
Senado Federal — senadores (Dados Abertos do Senado, sem chave).

    python -m etl.senado.extract senadores                  # em exercício hoje
    python -m etl.senado.extract legislatura [--numero 57]  # todos que passaram pela legislatura (titulares e suplentes)

Fontes: GET https://legis.senado.leg.br/dadosabertos/senador/lista/atual
        GET https://legis.senado.leg.br/dadosabertos/senador/lista/legislatura/{n}
Saídas: data/raw/senadores_atual.jsonl.gz, data/raw/senadores_leg{n}.jsonl.gz
        — id, nome (parlamentar), nome_completo, partido, uf, url_foto, participacao.
Uso atual: join autor→parlamentar nas emendas (senadores também têm emenda individual; quem saiu
do mandato só aparece na lista da legislatura).
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import httpx

from ..portal_transparencia.extract_emendas import write_jsonl

log = logging.getLogger("etl.senado")
RAW = Path("data/raw")
BASE = "https://legis.senado.leg.br/dadosabertos/senador/lista"
HEADERS = {"accept": "application/json", "user-agent": "nossodinheiro-etl/0.1"}


def _parlamentares(url: str) -> list[dict]:
    r = httpx.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    raiz = next(iter(r.json().values()))
    return raiz["Parlamentares"]["Parlamentar"]


def _linha(p: dict) -> dict:
    i = p["IdentificacaoParlamentar"]
    mandatos = p.get("Mandatos", {}).get("Mandato") or p.get("Mandato") or {}
    if isinstance(mandatos, list):
        mandatos = mandatos[-1] if mandatos else {}
    return {"id": int(i["CodigoParlamentar"]), "nome": i["NomeParlamentar"],
            "nome_completo": i.get("NomeCompletoParlamentar"), "partido": i.get("SiglaPartidoParlamentar"),
            "uf": i.get("UfParlamentar") or mandatos.get("UfParlamentar"), "url_foto": i.get("UrlFotoParlamentar"),
            "participacao": mandatos.get("DescricaoParticipacao")}


def cmd_senadores() -> None:
    n = write_jsonl(RAW / "senadores_atual.jsonl.gz", (_linha(p) for p in _parlamentares(f"{BASE}/atual")))
    if not 70 <= n <= 81:
        raise SystemExit(f"{n} senadores em exercício — esperado entre 70 e 81; fonte mudou?")


def cmd_legislatura(numero: int) -> None:
    n = write_jsonl(RAW / f"senadores_leg{numero}.jsonl.gz", (_linha(p) for p in _parlamentares(f"{BASE}/legislatura/{numero}")))
    if n < 81:
        raise SystemExit(f"{n} senadores na legislatura {numero} — esperado ≥ 81 (titulares + suplentes); fonte mudou?")


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("senadores")
    s = sub.add_parser("legislatura"); s.add_argument("--numero", type=int, default=57)
    a = ap.parse_args(argv)
    if a.cmd == "senadores":
        cmd_senadores()
    elif a.cmd == "legislatura":
        cmd_legislatura(a.numero)


if __name__ == "__main__":
    main()
