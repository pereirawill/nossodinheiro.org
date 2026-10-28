"""
Tribunais superiores — folha de pagamento mensal, um adaptador por tribunal (ver `fontes.py`).

    python -m etl.tribunais.extract --tribunal tst --ano 2026
    python -m etl.tribunais.extract --tribunal tst --ano 2026 --mes 9

Cada adaptador busca os meses do ano que o tribunal já publicou (nenhuma tentativa às cegas). Saída:
`data/raw/folha_<sigla>_<ano>.jsonl.gz`, uma linha por pessoa × mês, já normalizada. Nenhuma coluna de CPF é gravada.

Os portais dos tribunais podem recusar IPs fora do Brasil (o do STF recusa). Se o Actions falhar, rode localmente
(`make tribunais TRIBUNAL=tst ANO=2026`) e comite o JSON, como já fazemos com o STF e o INEP.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import httpx

from ..portal_transparencia.extract_emendas import write_jsonl
from .fontes import TRIBUNAIS, UA

log = logging.getLogger("etl.tribunais.extract")
RAW = Path("data/raw")


def cmd_folha(sigla: str, ano: int, meses: list[int] | None = None) -> Path:
    t = TRIBUNAIS[sigla]

    def gen():
        with httpx.Client(headers=UA, timeout=600, follow_redirects=True) as c:
            linhas = t.baixar(c, ano, meses)
            meses_vindos = sorted({l["mes"] for l in linhas})
            log.info("%s %d: %d registros, meses %s", t.sigla, ano, len(linhas), meses_vindos or "nenhum")
            yield from linhas

    RAW.mkdir(parents=True, exist_ok=True)
    destino = RAW / f"folha_{sigla}_{ano}.jsonl.gz"
    n = write_jsonl(destino, gen())
    log.info("%s: %d registros em %s", destino.name, n, destino)
    if n == 0:
        raise SystemExit(f"{t.sigla}: nenhuma folha de {ano} foi baixada — portal fora do ar, formato mudou ou IP bloqueado?")
    return destino


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tribunal", required=True, choices=sorted(TRIBUNAIS), help="sigla do tribunal")
    ap.add_argument("--ano", type=int, required=True)
    ap.add_argument("--mes", type=int, action="append", help="um ou mais meses (padrão: o ano inteiro)")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    cmd_folha(a.tribunal, a.ano, a.mes)


if __name__ == "__main__":
    main()
