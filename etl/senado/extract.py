"""
Senado Federal — lista de senadores em exercício (Dados Abertos do Senado, sem chave).

    python -m etl.senado.extract senadores

Fonte: GET https://legis.senado.leg.br/dadosabertos/senador/lista/atual (JSON)
Saída: data/raw/senadores_atual.jsonl.gz — id, nome (parlamentar), nome_completo, partido, uf, url_foto.
Uso atual: join autor→parlamentar nas emendas (senadores também têm emenda individual).
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import httpx

from ..portal_transparencia.extract_emendas import write_jsonl

log = logging.getLogger("etl.senado")
RAW = Path("data/raw")
URL = "https://legis.senado.leg.br/dadosabertos/senador/lista/atual"


def cmd_senadores() -> None:
    r = httpx.get(URL, headers={"accept": "application/json", "user-agent": "nossodinheiro-etl/0.1"}, timeout=60)
    r.raise_for_status()
    lista = r.json()["ListaParlamentarEmExercicio"]["Parlamentares"]["Parlamentar"]

    def gen():
        for p in lista:
            i = p["IdentificacaoParlamentar"]
            yield {"id": int(i["CodigoParlamentar"]), "nome": i["NomeParlamentar"],
                   "nome_completo": i.get("NomeCompletoParlamentar"), "partido": i.get("SiglaPartidoParlamentar"),
                   "uf": i.get("UfParlamentar"), "url_foto": i.get("UrlFotoParlamentar")}

    n = write_jsonl(RAW / "senadores_atual.jsonl.gz", gen())
    if not 70 <= n <= 81:
        raise SystemExit(f"{n} senadores em exercício — esperado entre 70 e 81; fonte mudou?")


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("senadores")
    a = ap.parse_args(argv)
    if a.cmd == "senadores":
        cmd_senadores()


if __name__ == "__main__":
    main()
