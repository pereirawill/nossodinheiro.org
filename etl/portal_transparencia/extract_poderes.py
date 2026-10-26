"""
Painel 5 — Quanto custa cada Poder (Legislativo, Judiciário, Executivo) — União.

Fonte A (MVP, poucas linhas): API do Portal da Transparência
    GET /api-de-dados/despesas/por-orgao?ano=YYYY&pagina=N
    → por órgão superior/órgão: empenhado, liquidado, pago (strings pt-BR).
    Cobre 2011+ e dá o "quanto custa" por órgão. NÃO traz GND.

Fonte B (v2, separar "custo de funcionar" de "políticas"): CSV mensal de execução
    https://portaldatransparencia.gov.br/download-de-dados/despesas-execucao/YYYYMM
    → traz Função, GND (1 Pessoal, 3 Outras Correntes, 4 Investimentos, 2 Juros,
      6 Amortização), Órgão. Arquivos grandes (centenas de MB/mês) — DuckDB lê o
      ZIP direto; rodar só para anos fechados, 1x.

Uso:
    python -m etl.portal_transparencia.extract_poderes --ano 2025      # Fonte A
    python -m etl.portal_transparencia.extract_poderes --ano 2025 --gnd # + Fonte B (lento)

Saída: data/raw/despesas_orgao_<ano>.jsonl.gz ; data/raw/execucao/<ano><mm>.zip
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import os
import sys
from pathlib import Path

import httpx

from .extract_emendas import Client, write_jsonl  # mesmo cliente com throttle/429

log = logging.getLogger("etl.portal.poderes")
RAW = Path("data/raw")
EXEC_URL = "https://portaldatransparencia.gov.br/download-de-dados/despesas-execucao/{ano}{mes:02d}"

# Código do órgão superior → Poder. Fonte: estrutura orçamentária da União (LOA).
PODER_POR_ORGAO_SUPERIOR = {
    "01000": "Legislativo",  # Câmara dos Deputados
    "02000": "Legislativo",  # Senado Federal
    "03000": "Legislativo",  # TCU (controle externo, vinculado ao Legislativo)
    "10000": "Judiciário",   # STF
    "11000": "Judiciário",   # STJ
    "12000": "Judiciário",   # Justiça Federal (CJF + TRFs)
    "13000": "Judiciário",   # Justiça Militar da União
    "14000": "Judiciário",   # Justiça Eleitoral (TSE + TREs)
    "15000": "Judiciário",   # Justiça do Trabalho (TST + TRTs)
    "16000": "Judiciário",   # TJDFT
    "17000": "Judiciário",   # CNJ
    "34000": "Funções essenciais",  # MPU
    "29000": "Funções essenciais",  # DPU
}
# Qualquer outro código (20000+) = Executivo. Encargos Financeiros da União (71000),
# Transferências (73000), Refinanciamento (75000), Operações Oficiais (74000) e
# Reserva (90000) NÃO são "custo de um Poder" — ficam em "Dívida/Transferências".
NAO_PODER = {"71000", "73000", "74000", "75000", "90000"}


# Unidades por onde roda o serviço da dívida e as transferências obrigatórias, mesmo
# dentro de um ministério: sem separação por GND, não dá para chamar isso de custo.
ORGAOS_DIVIDA = {"25000"}  # Ministério da Fazenda (juros, amortização, refinanciamento, FPM/FPE…)


def classificar(cod_superior: str) -> str:
    cod = str(cod_superior).zfill(5)
    if cod in PODER_POR_ORGAO_SUPERIOR:
        return PODER_POR_ORGAO_SUPERIOR[cod]
    if cod in NAO_PODER or cod in ORGAOS_DIVIDA:
        return "Dívida/Transferências"
    return "Executivo"


# Órgãos superiores da União (códigos SIAFI). A API exige um filtro além do ano,
# então iteramos por orgaoSuperior. Lista cobre os 3 Poderes + MPU/DPU + encargos.
ORGAOS_SUPERIORES = [
    "01000", "02000", "03000",                                   # Legislativo
    "10000", "11000", "12000", "13000", "14000", "15000", "16000", "17000",  # Judiciário
    "20000", "22000", "24000", "25000", "26000", "28000", "30000", "32000", "33000", "35000",
    "36000", "37000", "38000", "39000", "41000", "42000", "44000", "49000", "51000", "52000",
    "53000", "54000", "55000", "56000", "57000", "58000", "59000", "60000", "61000", "62000",
    "63000", "64000", "65000", "66000", "67000", "68000", "69000", "70000",  # Executivo
    "29000", "34000",                                            # DPU, MPU
    "71000", "73000", "74000", "75000", "90000",                 # dívida/transferências/reserva
]


def extrair_por_orgao(c: Client, ano: int, inspect: bool = False) -> None:
    def gen():
        for cod in ORGAOS_SUPERIORES:
            n = 0
            # A API aceita o código com ou sem zeros à esquerda dependendo do órgão;
            # tenta "01000" e, se vier vazio, "1000".
            for variante in dict.fromkeys([cod, cod.lstrip("0")]):
                for row in c.paginate("/despesas/por-orgao", {"ano": ano, "orgaoSuperior": variante}):
                    row["poder"] = classificar(row.get("codigoOrgaoSuperior") or cod)
                    n += 1
                    if inspect and n == 1:
                        print("campos:", sorted(row.keys())); print(json.dumps(row, ensure_ascii=False, indent=2))
                    yield row
                if n:
                    break
            log.info("orgaoSuperior=%s: %d linhas", cod, n)
            if n == 0:
                log.warning("orgaoSuperior=%s sem retorno (nenhuma variante) — conferir código", cod)
            if inspect and n:
                return
    write_jsonl(RAW / f"despesas_orgao_{ano}.jsonl.gz", gen())


def baixar_execucao(ano: int) -> None:
    out = RAW / "execucao"; out.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=600, follow_redirects=True) as h:
        for mes in range(1, 13):
            dst = out / f"{ano}{mes:02d}.zip"
            if dst.exists():
                continue
            url = EXEC_URL.format(ano=ano, mes=mes)
            log.info("baixando %s", url)
            with h.stream("GET", url) as r:
                if r.status_code == 404:
                    log.warning("mês %02d/%d ainda não publicado", mes, ano); break
                r.raise_for_status()
                with open(dst, "wb") as f:
                    for chunk in r.iter_bytes(1 << 20):
                        f.write(chunk)


def main(argv=None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, required=True)
    ap.add_argument("--gnd", action="store_true", help="também baixa os CSVs mensais de execução (GND)")
    ap.add_argument("--inspect", action="store_true", help="só imprime os campos da 1ª linha")
    a = ap.parse_args(argv)
    key = os.environ.get("PORTAL_TRANSPARENCIA_KEY") or sys.exit("defina PORTAL_TRANSPARENCIA_KEY")
    extrair_por_orgao(Client(key), a.ano, inspect=a.inspect)
    if a.gnd:
        baixar_execucao(a.ano)


if __name__ == "__main__":
    main()
