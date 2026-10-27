"""Saúde: agregação da cobertura da ANS com CSV sintético no layout do PDA 047 (sem rede)."""
from pathlib import Path

import pytest

from etl.saude.extract import planos

HDR = ("PERIODO;CD_MUNICIPIO;NM_MUNICIPIO;CD_UF;SG_UF;CD_RM;NM_RM;SEXO;FAIXA_ETARIA;BENEF_ASSISTENCIA_MEDICA;"
       "BENEF_EXCLUS_ODONTOLOGICO;BENEF_TOTAL;POPULACAO;TX_COBERT_ASSISTENCIA_MEDICA;TX_COBERT_EXCLUSIVAMENTE_ODONTOLOGICO;TX_COBERT_TOTAL")


class _Resposta:
    def __init__(self, conteudo: bytes):
        self.content = conteudo

    def raise_for_status(self):
        return None


class _Cliente:
    """Cliente falso: devolve o CSV sintético no lugar do arquivo da ANS."""

    def __init__(self, conteudo: bytes):
        self._c = conteudo

    def get(self, url, **kw):
        return _Resposta(self._c)


def _linha(periodo, cod, uf, med, odo):
    return f'"{periodo}";"{cod}";"X";"35";"{uf}";"00000";"Y";"FEMININO";"1 a 4 anos";"{med}";"{odo}";"0";"0";0,0;0,0;0,0'


def test_planos_agrega_por_uf_e_capital(tmp_path, monkeypatch):
    monkeypatch.setattr("etl.saude.extract.RAW", tmp_path)
    csv = "\n".join([HDR,
                     _linha("2026-08", "355030", "SP", 100, 10),   # São Paulo (capital, 6 dígitos)
                     _linha("2026-08", "350950", "SP", 50, 5),     # outro município de SP
                     _linha("2026-08", "330455", "RJ", 30, 3),
                     _linha("2026-07", "355030", "SP", 999, 999),  # competência antiga: ignorada
                     ]).encode("latin-1")
    pop_uf = {"SP": 1000, "RJ": 300}
    pop_mun = {3550308: 500}                                        # 7 dígitos, como no IBGE
    capitais = {3550308: {"cod_ibge": 3550308, "nome": "São Paulo", "uf": "SP"}}
    d = planos(_Cliente(csv), pop_uf, pop_mun, capitais)

    assert d["referencia"] == "2026-08"
    sp = next(u for u in d["por_uf"] if u["uf"] == "SP")
    assert sp["beneficiarios"] == 150 and sp["odontologico"] == 15 and sp["taxa"] == 15.0
    assert d["brasil"] == {"beneficiarios": 180, "odontologico": 18, "populacao": 1300, "taxa": 13.8}
    assert d["capitais"] == [{"cod_ibge": 3550308, "nome": "São Paulo", "uf": "SP", "beneficiarios": 100, "populacao": 500, "taxa": 20.0}]


def test_planos_descarta_uf_nao_informada(tmp_path, monkeypatch):
    monkeypatch.setattr("etl.saude.extract.RAW", tmp_path)
    csv = "\n".join([HDR, _linha("2026-08", "355030", "SP", 100, 0), _linha("2026-08", "-1", "XX", 7, 0)]).encode("latin-1")
    d = planos(_Cliente(csv), {"SP": 1000}, {}, {})
    assert [u["uf"] for u in d["por_uf"]] == ["SP"]
    assert d["sem_municipio_informado"] == 7 and d["brasil"]["beneficiarios"] == 107
