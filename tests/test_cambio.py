"""Câmbio: leitura das séries do Banco Central com respostas sintéticas (sem rede)."""
from datetime import date

import httpx
import pytest

from etl.cambio import extract as cambio


def _transport(rotas: dict[str, object]):
    def handler(request: httpx.Request) -> httpx.Response:
        for trecho, payload in rotas.items():
            if trecho in str(request.url):
                return httpx.Response(200, json=payload)
        return httpx.Response(404, json={})
    return httpx.MockTransport(handler)


def test_sgs_converte_data_para_aaaamm():
    c = httpx.Client(transport=_transport({"bcdata.sgs.3698": [
        {"data": "01/07/1994", "valor": "0.9333"}, {"data": "01/08/1994", "valor": "0.8986"}, {"data": "01/09/1994", "valor": ""}]}))
    assert cambio._sgs(c, 3698, "01/07/1994") == {"199407": 0.9333, "199408": 0.8986}


def test_ptax_pega_fechamento_mais_recente():
    c = httpx.Client(transport=_transport({"CotacaoMoedaPeriodoFechamento": {"value": [
        {"cotacaoCompra": 5.3340, "cotacaoVenda": 5.3346, "dataHoraCotacao": "2026-10-27 13:05:26"}]}}))
    assert cambio._ptax(c, "USD", date(2026, 10, 27)) == 5.3346


def test_ptax_sem_cotacao_devolve_none():
    c = httpx.Client(transport=_transport({"CotacaoMoedaPeriodoFechamento": {"value": []}}))
    assert cambio._ptax(c, "CNY", date(2026, 10, 27)) is None
