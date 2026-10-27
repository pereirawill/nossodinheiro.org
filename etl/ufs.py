"""Tabela fixa das 27 unidades da federação (código IBGE, sigla, nome, região) e normalização de nomes para casamento."""

from __future__ import annotations

import re
import unicodedata

UFS = [
    (11, "RO", "Rondônia", "N"), (12, "AC", "Acre", "N"), (13, "AM", "Amazonas", "N"), (14, "RR", "Roraima", "N"), (15, "PA", "Pará", "N"),
    (16, "AP", "Amapá", "N"), (17, "TO", "Tocantins", "N"), (21, "MA", "Maranhão", "NE"), (22, "PI", "Piauí", "NE"), (23, "CE", "Ceará", "NE"),
    (24, "RN", "Rio Grande do Norte", "NE"), (25, "PB", "Paraíba", "NE"), (26, "PE", "Pernambuco", "NE"), (27, "AL", "Alagoas", "NE"),
    (28, "SE", "Sergipe", "NE"), (29, "BA", "Bahia", "NE"), (31, "MG", "Minas Gerais", "SE"), (32, "ES", "Espírito Santo", "SE"),
    (33, "RJ", "Rio de Janeiro", "SE"), (35, "SP", "São Paulo", "SE"), (41, "PR", "Paraná", "S"), (42, "SC", "Santa Catarina", "S"),
    (43, "RS", "Rio Grande do Sul", "S"), (50, "MS", "Mato Grosso do Sul", "CO"), (51, "MT", "Mato Grosso", "CO"), (52, "GO", "Goiás", "CO"),
    (53, "DF", "Distrito Federal", "CO"),
]
COD_PARA_UF = {c: s for c, s, _, _ in UFS}
UF_PARA_NOME = {s: n for _, s, n, _ in UFS}
NOME_PARA_UF = {n: s for _, s, n, _ in UFS}


def normalizar(s: str) -> str:
    """Maiúsculas, sem acento, só letras e dígitos — para casar nomes de municípios entre fontes."""
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]", "", s)
