"""
Câmbio — quanto o real vale frente ao dólar e às outras moedas, desde que a moeda foi criada.

    python -m etl.cambio.extract            # gera data/public/cambio.json

Fontes (Banco Central do Brasil, sem chave):
- **SGS série 3698**: taxa de câmbio livre, dólar americano (venda), **média mensal**, desde julho de 1994 — o mês em que o real
  entrou em circulação. É a série que mostra a trajetória inteira da moeda.
- **SGS série 11752**: índice da **taxa de câmbio efetiva real** (deflacionada pelo IPCA), que compara o real com uma cesta de moedas
  dos principais parceiros comerciais já descontando a inflação dos dois lados. É a medida com a qual se pode dizer se o real está
  "caro" ou "barato" — a cotação nominal sozinha mistura a inflação brasileira com a de fora.
- **PTAX** (`olinda.bcb.gov.br/olinda/servico/PTAX`): cotação de fechamento de cada moeda em reais, usada para o retrato de hoje e
  as comparações com 1, 5 e 10 anos atrás.

O que esta base **não** é: medida de perda de poder de compra. Câmbio é preço relativo entre moedas; a inflação de cada país é outra
coisa, e o próprio dólar perde valor com o tempo. As duas aparecem juntas na página, separadas e explicadas.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx

log = logging.getLogger("etl.cambio")
PUB = Path("data/public")
SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados?formato=json&dataInicial={inicio}"
PTAX = ("https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
        "CotacaoMoedaPeriodoFechamento(codigoMoeda=@codigoMoeda,dataInicialCotacao=@dataInicialCotacao,dataFinalCotacao=@dataFinalCotacao)"
        "?@codigoMoeda='{moeda}'&@dataInicialCotacao='{ini}'&@dataFinalCotacao='{fim}'&$format=json&$orderby=dataHoraCotacao desc&$top=1")
UA = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
REAL = "01/07/1994"                     # mês em que o real entrou em circulação
# O PTAX só cobre dez moedas (AUD, CAD, CHF, DKK, EUR, GBP, JPY, NOK, SEK, USD). Yuan e peso argentino não estão lá,
# apesar de China e Argentina serem parceiros comerciais grandes — fica declarado na página e na metodologia.
MOEDAS = {"USD": "Dólar dos Estados Unidos", "EUR": "Euro", "GBP": "Libra esterlina", "CHF": "Franco suíço",
          "JPY": "Iene japonês", "CAD": "Dólar canadense", "AUD": "Dólar australiano"}


def _sgs(c: httpx.Client, serie: int, inicio: str) -> dict[str, float]:
    """Série do SGS como {AAAAMM: valor} (as mensais vêm com dia 01)."""
    erro = None
    for _ in range(3):
        try:
            r = c.get(SGS.format(serie=serie, inicio=inicio)); r.raise_for_status()
            return {f"{d['data'][6:10]}{d['data'][3:5]}": float(d["valor"]) for d in r.json() if d.get("valor") not in (None, "")}
        except (httpx.HTTPError, ValueError) as e:
            erro = e; log.warning("SGS %d: %s", serie, e)
    raise erro


def _ptax(c: httpx.Client, moeda: str, dia: date) -> float | None:
    """Cotação de venda do fechamento mais recente até `dia` (procura 12 dias para trás por causa de feriados)."""
    ini = (dia - timedelta(days=12)).strftime("%m-%d-%Y")
    try:
        r = c.get(PTAX.format(moeda=moeda, ini=ini, fim=dia.strftime("%m-%d-%Y")))
        if r.status_code != 200:
            return None
        v = r.json().get("value") or []
        return round(float(v[0]["cotacaoVenda"]), 6) if v else None
    except (httpx.HTTPError, ValueError, KeyError, IndexError) as e:
        log.warning("PTAX %s em %s: %s", moeda, dia, e)
        return None


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    hoje = date.today()
    marcos = {"hoje": hoje, "um_ano": hoje.replace(year=hoje.year - 1), "cinco_anos": hoje.replace(year=hoje.year - 5),
              "dez_anos": hoje.replace(year=hoje.year - 10)}
    with httpx.Client(headers=UA, timeout=180, follow_redirects=True) as c:
        usd = _sgs(c, 3698, REAL)
        efetiva = _sgs(c, 11752, REAL)
        moedas = []
        for simbolo, nome in MOEDAS.items():
            cot = {k: _ptax(c, simbolo, d) for k, d in marcos.items()}
            if cot.get("hoje") is None:
                log.warning("sem cotação de %s hoje; moeda fica de fora", simbolo)
                continue
            moedas.append({"simbolo": simbolo, "nome": nome, **cot,
                           "var_1_ano": round(100 * (cot["hoje"] / cot["um_ano"] - 1), 1) if cot.get("um_ano") else None,
                           "var_5_anos": round(100 * (cot["hoje"] / cot["cinco_anos"] - 1), 1) if cot.get("cinco_anos") else None,
                           "var_10_anos": round(100 * (cot["hoje"] / cot["dez_anos"] - 1), 1) if cot.get("dez_anos") else None})
    primeiro, ultimo = min(usd), max(usd)
    dados = {"gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
             "usd_mensal": usd, "usd_primeiro_mes": primeiro, "usd_ultimo_mes": ultimo,
             "efetiva_real": efetiva, "moedas": sorted(moedas, key=lambda m: list(MOEDAS).index(m["simbolo"])),
             "fontes": {"usd": "Banco Central, SGS série 3698 — dólar (venda), média mensal, desde julho de 1994",
                        "efetiva": "Banco Central, SGS série 11752 — índice da taxa de câmbio efetiva real (deflacionada pelo IPCA)",
                        "ptax": "Banco Central, PTAX — cotação de fechamento de cada moeda em reais"}}
    out = PUB / "cambio.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    log.info("dólar %s: R$ %.4f → %s: R$ %.4f (%.0f%%); %d moedas; efetiva real %s = %.1f",
             primeiro, usd[primeiro], ultimo, usd[ultimo], 100 * (usd[ultimo] / usd[primeiro] - 1), len(moedas),
             max(efetiva), efetiva[max(efetiva)])
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
