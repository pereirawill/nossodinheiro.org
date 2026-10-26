"""
Senado Federal — senadores (Dados Abertos do Senado, sem chave).

    python -m etl.senado.extract senadores                  # em exercício hoje
    python -m etl.senado.extract legislatura [--numero 57]  # todos que passaram pela legislatura (titulares e suplentes)
    python -m etl.senado.extract recursos --ano 2026        # "Recursos utilizados" de cada senador em exercício

Fontes: GET https://legis.senado.leg.br/dadosabertos/senador/lista/atual
        GET https://legis.senado.leg.br/dadosabertos/senador/lista/legislatura/{n}
        GET https://adm.senado.gov.br/adm-dadosabertos/api/v1/senadores/{id}/recursos-utilizados?ano=AAAA&formato=json
        (é o JSON que alimenta a página "Transparência → Senadores → Recursos utilizados"; sem chave)
Saídas: data/raw/senadores_atual.jsonl.gz, data/raw/senadores_leg{n}.jsonl.gz
        — id, nome (parlamentar), nome_completo, partido, uf, url_foto, participacao.
        data/raw/senadores_recursos_<ano>.jsonl.gz — 1 linha por senador: CEAPS por categoria (valor reembolsado),
        gastos não inclusos na cota (diárias, passagens aéreas, correios, material, redes sociais), benefícios
        (auxílio-moradia, imóvel funcional) e quantidade de pessoal por vínculo.
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
RECURSOS = "https://adm.senado.gov.br/adm-dadosabertos/api/v1/senadores/{id}/recursos-utilizados"
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


def cmd_recursos(ano: int) -> None:
    import gzip, json, time
    lista = RAW / "senadores_atual.jsonl.gz"
    if not lista.exists():
        cmd_senadores()
    with gzip.open(lista, "rt", encoding="utf-8") as f:
        senadores = [json.loads(l) for l in f]

    def gen():
        with httpx.Client(headers=HEADERS, timeout=60) as c:
            for i, s in enumerate(senadores, 1):
                for tentativa in range(1, 4):
                    r = c.get(RECURSOS.format(id=s["id"]), params={"ano": ano, "formato": "json"})
                    if r.status_code == 200:
                        break
                    log.warning("HTTP %s para senador %s (tentativa %d)", r.status_code, s["id"], tentativa); time.sleep(5 * tentativa)
                r.raise_for_status()
                dados = r.json().get("data") or []
                if not dados:
                    log.warning("senador %s (%s): sem dados em %d", s["id"], s["nome"], ano); continue
                d = dados[0]
                yield {"id": s["id"], "nome": s["nome"], "partido": s["partido"], "uf": s["uf"], "url_foto": s["url_foto"], "ano": ano,
                       "ceaps": d.get("cotas", {}).get("despesas", []), "ceaps_total": d.get("cotas", {}).get("totalValor"),
                       "nao_inclusos": d.get("gastosNaoInclusos", {}).get("despesas", []),
                       "nao_inclusos_total": d.get("gastosNaoInclusos", {}).get("totalValor"),
                       "beneficios": d.get("beneficios", []), "pessoal": d.get("pessoal", [])}
                if i % 20 == 0:
                    log.info("recursos %d: %d/%d", ano, i, len(senadores))
                time.sleep(0.3)

    n = write_jsonl(RAW / f"senadores_recursos_{ano}.jsonl.gz", gen())
    if n < 0.9 * len(senadores):
        raise SystemExit(f"só {n} de {len(senadores)} senadores com recursos em {ano} — fonte mudou?")


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("senadores")
    s = sub.add_parser("legislatura"); s.add_argument("--numero", type=int, default=57)
    s = sub.add_parser("recursos"); s.add_argument("--ano", type=int, required=True)
    a = ap.parse_args(argv)
    if a.cmd == "senadores":
        cmd_senadores()
    elif a.cmd == "legislatura":
        cmd_legislatura(a.numero)
    elif a.cmd == "recursos":
        cmd_recursos(a.ano)


if __name__ == "__main__":
    main()
