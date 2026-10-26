"""
STF — folha de pagamento de ministros e dos gabinetes (Portal da Transparência do STF, sem chave).

    python -m etl.stf.extract folha --ano 2026

Fonte: formulário "Remuneração" do STF, exportação CSV:
    GET https://egesp-portal.stf.jus.br/transparencia/rendimento_folha
        ?q[ano_eq]=AAAA&q[mes_eq]=M&q[cdg_cargo_efetivo_in][]=55&tipo_relatorio=CSV      (cargo 55 = MINISTRO)
        ?q[ano_eq]=AAAA&q[mes_eq]=M&q[cdg_unidade_in][]=<id da lotação>&tipo_relatorio=CSV (folha de um gabinete)
Colunas: Matrícula, Nome, Cargo Efetivo, Cargo Comissionado, Nome da Função, Nome da Unidade, Situação Funcional,
         "Remuneração Bruta após o teto constitucional somada com outras verbas", "Remuneração Liquida".
Os ids das lotações vêm do próprio formulário (select q[cdg_unidade_in][]), lido uma vez por execução.

Saída: data/raw/stf_folha_<ano>.jsonl.gz — 1 linha por pessoa × mês, com `origem` = "ministros" (consulta
por cargo) ou "gabinete" (consulta por lotação) e `unidade_id`.
Só o que o STF publica; nenhuma coluna de CPF existe na fonte.
"""

from __future__ import annotations

import argparse
import csv
import io
import logging
import re
import time
from pathlib import Path

import httpx

from ..portal_transparencia.extract_emendas import write_jsonl

log = logging.getLogger("etl.stf")
RAW = Path("data/raw")
URL = "https://egesp-portal.stf.jus.br/transparencia/rendimento_folha"
HEADERS = {"user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
           "accept": "text/csv,text/html;q=0.9,*/*;q=0.8", "accept-language": "pt-BR,pt;q=0.9"}
CARGO_MINISTRO = "55"
COL_BRUTO = "Remuneração Bruta após o teto constitucional somada com outras verbas"
COL_LIQUIDO = "Remuneração Liquida"


def _get(c: httpx.Client, params: list[tuple[str, str]]) -> list[dict]:
    for tentativa in range(1, 5):
        r = c.get(URL, params=params + [("tipo_relatorio", "CSV")])
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("text/csv"):
            rows = list(csv.DictReader(io.StringIO(r.content.decode("utf-8-sig"))))
            return [row for row in rows if row.get("Nome")]
        log.warning("HTTP %s (%s) em %s — tentativa %d", r.status_code, r.headers.get("content-type"), params, tentativa)
        time.sleep(5 * tentativa)
    raise RuntimeError(f"STF não respondeu CSV para {params} — se for HTTP 403, o portal bloqueia IPs fora do Brasil "
                       "(GitHub Actions); rode `make stf` numa máquina no Brasil")


def _unidades(c: httpx.Client) -> dict[str, str]:
    """Nome da lotação → id, lido do select do formulário."""
    html = c.get(URL).text
    pares = re.findall(r'<option value="([0-9.]+)">([^<]+)</option>', html)
    return {nome.strip(): val for val, nome in pares if val and nome.strip()}


def cmd_folha(ano: int, meses: list[int] | None = None) -> None:
    def gen():
        with httpx.Client(headers=HEADERS, timeout=120, follow_redirects=True) as c:
            unidades = _unidades(c)
            log.info("%d lotações no formulário", len(unidades))
            vazios = 0
            for mes in meses or range(1, 13):
                base = [("q[ano_eq]", str(ano)), ("q[mes_eq]", str(mes))]
                ministros = _get(c, base + [("q[cdg_cargo_efetivo_in][]", CARGO_MINISTRO)])
                if not ministros:
                    vazios += 1
                    log.info("%d-%02d: folha ainda não publicada", ano, mes)
                    if vazios >= 2:
                        break
                    continue
                vazios = 0
                for r in ministros:
                    yield {**r, "ano": ano, "mes": mes, "origem": "ministros", "unidade_id": unidades.get(r.get("Nome da Unidade", "").strip())}
                ativos = [r for r in ministros if r.get("Situação Funcional", "").strip().upper() == "MINISTRO"]
                for r in ativos:
                    nome_unid = r.get("Nome da Unidade", "").strip()
                    uid = unidades.get(nome_unid)
                    if not uid:
                        log.warning("%d-%02d: lotação %r do ministro %s não está no formulário — gabinete sem folha", ano, mes, nome_unid, r["Nome"]); continue
                    for g in _get(c, base + [("q[cdg_unidade_in][]", uid)]):
                        yield {**g, "ano": ano, "mes": mes, "origem": "gabinete", "unidade_id": uid}
                    time.sleep(0.5)
                log.info("%d-%02d: %d ministros (%d ativos)", ano, mes, len(ministros), len(ativos))

    n = write_jsonl(RAW / f"stf_folha_{ano}.jsonl.gz", gen())
    if n == 0:
        raise SystemExit(f"nenhuma linha de folha do STF em {ano} — fonte mudou?")


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("folha"); s.add_argument("--ano", type=int, required=True); s.add_argument("--meses", type=int, nargs="*")
    a = ap.parse_args(argv)
    if a.cmd == "folha":
        cmd_folha(a.ano, a.meses)


if __name__ == "__main__":
    main()
