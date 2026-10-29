"""
Economia — o tamanho da economia, o quanto ela cresce, o juro básico e o resultado das contas públicas.

    python -m etl.economia.extract            # gera data/public/economia.json

Quatro fontes, todas sem chave:

- **IBGE, Contas Nacionais Anuais** (SIDRA, tabela **6784**): PIB em valores correntes, PIB por habitante, população e
  variação em volume, de 1996 ao último ano fechado. É a medida oficial do tamanho da economia.
- **IBGE, Contas Nacionais Trimestrais** (tabela **5932**): variação do PIB a preços de mercado, trimestre a
  trimestre, desde 1996 — tanto contra o mesmo trimestre do ano anterior quanto acumulada em quatro trimestres.
- **Banco Central, SGS série 432**: a **meta da taxa Selic definida pelo Copom**. A taxa efetiva (séries 1178 e 4189)
  fica um pouco abaixo da meta; a página usa a meta e diz isso.
- **Tesouro Nacional, RTN — Série Histórica** (aba 2.1): resultado **primário** e **nominal** do Governo Central,
  desde 1997, em R$ milhões correntes. É o mesmo arquivo usado nos painéis de Dívida e Estatais.

O que esta página **não** inventa: previsão. Nada aqui projeta crescimento, juro ou resultado futuro — o site publica
o que já aconteceu e está registrado.
"""

from __future__ import annotations

import io
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import openpyxl

from etl.estatais.dividendos import _planilha as _planilha_rtn

log = logging.getLogger("etl.economia")
PUB = Path("data/public")
SIDRA = "https://apisidra.ibge.gov.br/values/t/{t}/n1/all/v/{v}/p/{p}{c}?formato=json"
# O SGS recusa (HTTP 406) qualquer janela maior que 10 anos em série diária, então a coleta vai em fatias.
SGS = ("https://api.bcb.gov.br/dados/serie/bcdata.sgs.{c}/dados?formato=json"
       "&dataInicial=01/01/{de}&dataFinal=31/12/{ate}")
PIB_ANUAL = {"t": 6784, "correntes": "9808", "volume": "9810", "per_capita": "9812", "populacao": "9813"}
PIB_TRIM = {"t": 5932, "cat": "90707", "trimestral": "6561", "quatro_trim": "6562", "no_ano": "6563"}
SELIC_META = 432
# Na aba 2.1 o resultado primário "abaixo da linha" é a linha 8 (a 5 é "acima da linha", medida de outro jeito) e o
# nominal é a 10. A 7 é discrepância estatística — foi o erro da primeira versão.
RTN_LINHAS = {"primario": re.compile(r"^\s*8\.\s*RESULTADO PRIM", re.I),
              "nominal": re.compile(r"^\s*10\.\s*RESULTADO NOMINAL", re.I)}


def _num(v) -> float | None:
    try:
        f = float(str(v).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return None if f <= -999999 else f


def _sidra(c: httpx.Client, t: int, v: str, p: str, cl: str = "") -> list[dict]:
    r = c.get(SIDRA.format(t=t, v=v, p=p, c=cl))
    if r.status_code != 200:
        log.warning("SIDRA t%s v%s respondeu HTTP %s", t, v, r.status_code)
        return []
    d = r.json()
    if len(d) < 2:
        return []
    cab = d[0]
    return [{cab[k]: l[k] for k in l} for l in d[1:]]


def pib_anual(c: httpx.Client) -> list[dict]:
    """PIB em valores correntes, por habitante e variação em volume, por ano."""
    campos = {}
    for chave, var in (("correntes", PIB_ANUAL["correntes"]), ("volume", PIB_ANUAL["volume"]),
                       ("per_capita", PIB_ANUAL["per_capita"]), ("populacao", PIB_ANUAL["populacao"])):
        for linha in _sidra(c, PIB_ANUAL["t"], var, "all"):
            valor = _num(linha.get("Valor"))
            if valor is not None:
                campos.setdefault(linha["Ano"], {})[chave] = valor
    anos = sorted(campos)
    # valores correntes vêm em milhões de reais
    return [{"ano": int(a), **{k: (v * 1e6 if k in ("correntes",) else v) for k, v in campos[a].items()}}
            for a in anos]


def pib_trimestral(c: httpx.Client) -> list[dict]:
    """Variação do PIB a preços de mercado, por trimestre."""
    campos = {}
    for chave, var in (("trimestral", PIB_TRIM["trimestral"]), ("quatro_trimestres", PIB_TRIM["quatro_trim"]),
                       ("no_ano", PIB_TRIM["no_ano"])):
        for linha in _sidra(c, PIB_TRIM["t"], var, "all", f"/c11255/{PIB_TRIM['cat']}"):
            valor = _num(linha.get("Valor"))
            periodo = linha.get("Trimestre (Código)") or linha.get("Trimestre")
            if valor is not None and periodo:
                campos.setdefault(str(periodo), {})[chave] = valor
    return [{"periodo": p, **campos[p]} for p in sorted(campos)]


def _sgs_janela(c: httpx.Client, serie: int, de: int, ate: int) -> list[dict]:
    """Uma janela do SGS, com repetição: o serviço devolve 502, ou HTML com status 200, de forma intermitente."""
    for tentativa in range(4):
        r = c.get(SGS.format(c=serie, de=de, ate=ate), headers={"User-Agent": "nossodinheiro.org"})
        if r.status_code == 200 and "json" in (r.headers.get("content-type") or ""):
            return r.json()
        log.info("SGS %s (%s–%s), tentativa %d: HTTP %s %s", serie, de, ate, tentativa + 1, r.status_code,
                 (r.headers.get("content-type") or "")[:24])
        time.sleep(2 * (tentativa + 1))
    log.warning("SGS %s (%s–%s): desisti depois de 4 tentativas", serie, de, ate)
    return []


def selic(c: httpx.Client) -> list[dict]:
    """Meta da Selic definida pelo Copom, um ponto por mudança, desde 1996."""
    hoje = datetime.now().year
    pontos, anterior = [], None
    for inicio in range(1996, hoje + 1, 9):
        fim = min(inicio + 8, hoje)
        for x in _sgs_janela(c, SELIC_META, inicio, fim):
            v = _num(x.get("valor"))
            if v is None:
                continue
            if v != anterior:                  # só os dias em que a meta mudou: a série diária é repetitiva
                pontos.append({"data": x["data"], "valor": v})
                anterior = v
    return pontos


def resultado_governo(c: httpx.Client) -> dict:
    """Resultado primário e nominal do Governo Central, por ano, do RTN."""
    conteudo = _planilha_rtn(c)
    if conteudo is None:
        return {}
    wb = openpyxl.load_workbook(io.BytesIO(conteudo), data_only=True, read_only=True)
    if "2.1" not in wb.sheetnames:
        return {}
    linhas = list(wb["2.1"].iter_rows(values_only=True))
    anos = []
    for row in linhas[:12]:
        if str(row[0] or "").strip().lower().startswith("discrimina"):
            anos = [str(int(v)) for v in row[1:] if isinstance(v, (int, float)) and 1990 < v < 2100]
            break
    saida: dict[str, dict] = {}
    for row in linhas:
        rotulo = str(row[0] or "")
        for chave, padrao in RTN_LINHAS.items():
            if padrao.match(rotulo):
                for i, ano in enumerate(anos, start=1):
                    if i < len(row) and isinstance(row[i], (int, float)):
                        saida.setdefault(ano, {})[chave] = round(row[i] * 1e6, 2)
    return saida


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=240, follow_redirects=True) as c:
        anual = pib_anual(c)
        trimestral = pib_trimestral(c)
        juros = selic(c)
        contas = resultado_governo(c)
    if not anual or not trimestral:
        raise SystemExit("PIB não veio do SIDRA — tabela 6784 ou 5932 mudou?")

    dados = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "pib_anual": anual, "pib_trimestral": trimestral, "selic": juros, "resultado_governo": contas,
        "fontes": {
            "pib": "IBGE, Contas Nacionais Anuais (SIDRA 6784) e Trimestrais (SIDRA 5932, PIB a preços de mercado)",
            "selic": f"Banco Central, SGS série {SELIC_META} — meta da Selic definida pelo Copom (a taxa efetiva "
                     "fica um pouco abaixo da meta)",
            "contas": "Tesouro Nacional, Resultado do Tesouro Nacional — Série Histórica, tabela 2.1, resultado "
                      "primário e nominal do Governo Central, em valores correntes",
        },
        "nota": "Nada aqui é previsão: só o que já aconteceu e está registrado pelas fontes oficiais.",
    }
    out = PUB / "economia.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    log.info("economia: PIB anual %s–%s; trimestres %s–%s; Selic %d mudanças; contas %s–%s",
             anual[0]["ano"], anual[-1]["ano"], trimestral[0]["periodo"], trimestral[-1]["periodo"],
             len(juros), min(contas) if contas else "—", max(contas) if contas else "—")
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
