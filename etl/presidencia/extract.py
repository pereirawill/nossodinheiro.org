"""
Presidência da República — cartão corporativo (CPGF) e viagens, do Portal da Transparência (download-de-dados, sem chave).

    python -m etl.presidencia.extract cpgf --ano 2026       # 12 CSVs mensais (meses ainda não publicados dão 403 e são pulados)
    python -m etl.presidencia.extract viagens --ano 2026    # ZIP anual (~90 MB), só os registros do órgão superior 20000

Fonte CPGF: https://portaldatransparencia.gov.br/download-de-dados/cpgf/AAAAMM (ZIP com AAAAMM_CPGF.csv, latin-1, ';').
Colunas: CÓDIGO/NOME ÓRGÃO SUPERIOR, CÓDIGO/NOME ÓRGÃO, CÓDIGO/NOME UNIDADE GESTORA, ANO/MÊS EXTRATO, CPF PORTADOR
(já mascarado pelo Portal), NOME PORTADOR, CNPJ OU CPF FAVORECIDO, NOME FAVORECIDO, TRANSAÇÃO, DATA TRANSAÇÃO, VALOR TRANSAÇÃO.
Transações de segurança da Presidência vêm como "Sigiloso" / "Informações protegidas por sigilo" (LAI, art. 23).

Saída: data/raw/presidencia_cpgf_<ano>.jsonl.gz — 1 linha por transação do órgão superior 20000 (Presidência,
Vice-Presidência, Imprensa Nacional, EBC…), mais 1 linha por mês com o total de todo o governo (`origem` = "total_governo").
Privacidade: o CPF do portador já vem mascarado; CPF de favorecido pessoa física (11 dígitos) é mascarado aqui
(***.xxx.xxx-**). Nome de favorecido e de portador são dados públicos do Portal e ficam no raw; o site só publica
agregados e favorecidos pessoa jurídica.
"""

from __future__ import annotations

import argparse
import csv
import io
import logging
import re
import zipfile
from pathlib import Path

import httpx

from ..portal_transparencia.extract_emendas import write_jsonl

log = logging.getLogger("etl.presidencia")
RAW = Path("data/raw")
BASE = "https://portaldatransparencia.gov.br/download-de-dados"
HEADERS = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
           "accept": "*/*", "referer": "https://portaldatransparencia.gov.br/download-de-dados/cpgf"}
ORGAO_SUPERIOR_PRESIDENCIA = "20000"


def _brl(s: str) -> float:
    return float(s.replace(".", "").replace(",", ".")) if s else 0.0


def _mascara_cpf(doc: str) -> str:
    d = re.sub(r"\D", "", doc or "")
    return f"***.{d[3:6]}.{d[6:9]}-**" if len(d) == 11 else (doc or "")


def _csv_do_zip(conteudo: bytes) -> list[dict]:
    z = zipfile.ZipFile(io.BytesIO(conteudo))
    nome = next(n for n in z.namelist() if n.lower().endswith(".csv"))
    txt = z.read(nome).decode("latin-1")
    return list(csv.DictReader(io.StringIO(txt), delimiter=";"))


def cmd_cpgf(ano: int) -> None:
    def gen():
        with httpx.Client(headers=HEADERS, timeout=180, follow_redirects=True) as c:
            for mes in range(1, 13):
                r = c.get(f"{BASE}/cpgf/{ano}{mes:02d}")
                if r.status_code != 200 or "zip" not in r.headers.get("content-type", ""):
                    log.info("%d-%02d: CPGF ainda não publicado (HTTP %s)", ano, mes, r.status_code); continue
                rows = _csv_do_zip(r.content)
                total = sum(_brl(x["VALOR TRANSAÇÃO"]) for x in rows)
                n = 0
                for x in rows:
                    if x["CÓDIGO ÓRGÃO SUPERIOR"] != ORGAO_SUPERIOR_PRESIDENCIA:
                        continue
                    n += 1
                    yield {"origem": "presidencia", "ano": int(x["ANO EXTRATO"]), "mes": int(x["MÊS EXTRATO"]),
                           "cod_orgao": x["CÓDIGO ÓRGÃO"], "orgao": x["NOME ÓRGÃO"], "cod_ug": x["CÓDIGO UNIDADE GESTORA"], "ug": x["NOME UNIDADE GESTORA"],
                           "portador": x["NOME PORTADOR"], "favorecido_doc": _mascara_cpf(x["CNPJ OU CPF FAVORECIDO"]), "favorecido": x["NOME FAVORECIDO"],
                           "transacao": x["TRANSAÇÃO"], "data": x["DATA TRANSAÇÃO"], "valor": _brl(x["VALOR TRANSAÇÃO"]),
                           "sigiloso": x["NOME PORTADOR"].strip().lower() == "sigiloso" or "sigilo" in x["TRANSAÇÃO"].lower()}
                yield {"origem": "total_governo", "ano": ano, "mes": mes, "valor": round(total, 2), "transacoes": len(rows)}
                log.info("%d-%02d: %d transações da Presidência; governo R$ %.2f", ano, mes, n, total)

    n = write_jsonl(RAW / f"presidencia_cpgf_{ano}.jsonl.gz", gen())
    if n == 0:
        raise SystemExit(f"nenhum mês de CPGF em {ano} — fonte mudou?")


def cmd_viagens(ano: int) -> None:
    """ZIP anual com vários CSVs (viagem, pagamento, passagem, trecho). Guarda só o órgão superior 20000."""
    with httpx.Client(headers={**HEADERS, "referer": f"{BASE}/viagens"}, timeout=600, follow_redirects=True) as c:
        r = c.get(f"{BASE}/viagens/{ano}")
        r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    destino = RAW / "viagens"; destino.mkdir(parents=True, exist_ok=True)
    for nome in z.namelist():
        if not nome.lower().endswith(".csv"):
            continue
        txt = z.read(nome).decode("latin-1")
        rows = list(csv.DictReader(io.StringIO(txt), delimiter=";"))
        col = next((k for k in rows[0].keys() if "ÓRGÃO SUPERIOR" in k.upper() and "CÓDIGO" in k.upper()), None) if rows else None
        sel = [x for x in rows if col and x[col] == ORGAO_SUPERIOR_PRESIDENCIA] if col else rows
        out = destino / f"{ano}_{Path(nome).stem}_presidencia.jsonl.gz"
        write_jsonl(out, iter(sel))
        log.info("%s: %d linhas (%d da Presidência) → %s", nome, len(rows), len(sel), out)


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    for nome in ("cpgf", "viagens"):
        s = sub.add_parser(nome); s.add_argument("--ano", type=int, required=True)
    a = ap.parse_args(argv)
    {"cpgf": cmd_cpgf, "viagens": cmd_viagens}[a.cmd](a.ano)


if __name__ == "__main__":
    main()
