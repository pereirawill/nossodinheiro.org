"""
Casamento de nomes: autor da emenda (nome na LOA, ex. "DR. DANIEL SORANZ", "FAUSTO SANTOS JR.")
→ parlamentar das listas oficiais (nome parlamentar, ex. "Daniel Soranz", "Fausto Jr.").

1. Exato: nome normalizado igual (sem acento, maiúsculo, sem pontos).
2. Aproximado: tokens significativos (sem títulos como DR/PROFESSORA/TENENTE e sem JR/NETO/FILHO/PAI,
   letras dobradas reduzidas: FOLLETTO → FOLETO). Aceita só se o conjunto menor estiver contido no maior
   e houver UM único candidato. Toda aproximação é registrada (`match_tipo = 'aproximado'`) para revisão.
Prioridade: quem está em exercício antes de quem já saiu.
"""

from __future__ import annotations

import re
import unicodedata

TITULOS = {"DR", "DRA", "PROF", "PROFESSOR", "PROFESSORA", "PASTOR", "PASTORA", "PADRE", "BISPO", "CAPITAO", "CAPITA",
           "CORONEL", "TENENTE", "SARGENTO", "SOLDADO", "CABO", "DELEGADO", "DELEGADA", "GENERAL", "MAJOR", "DEPUTADO",
           "DEPUTADA", "SENADOR", "SENADORA", "VEREADOR", "PREFEITO", "DOUTOR", "DOUTORA", "ENFERMEIRA", "ENFERMEIRO"}
SUFIXOS = {"JR", "JUNIOR", "NETO", "FILHO", "PAI", "SOBRINHO", "SEGUNDO"}
PARTICULAS = {"DA", "DE", "DO", "DAS", "DOS", "E", "DI", "DEL"}


def normalizar(s: str | None) -> str:
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s.upper().replace(".", " ")).strip()


def tokens(s: str | None) -> frozenset[str]:
    out = []
    for t in normalizar(s).split():
        if t in TITULOS or t in SUFIXOS or t in PARTICULAS:
            continue
        out.append(re.sub(r"(.)\1+", r"\1", t))  # letras dobradas: FOLLETTO → FOLETO
    return frozenset(out)


def casar(autores: list[str], parlamentares: list[dict]) -> dict[str, tuple[dict, str]]:
    """parlamentares: dicts com nome, em_exercicio (bool|None) e o que mais se quiser devolver.
    → {autor: (parlamentar, 'exato'|'aproximado')}; autores sem casamento ficam fora."""
    ordem = sorted(parlamentares, key=lambda p: not p.get("em_exercicio"))  # em exercício primeiro
    exato: dict[str, dict] = {}
    for p in ordem:
        exato.setdefault(normalizar(p["nome"]), p)
    toks = [(tokens(p["nome"]), p) for p in ordem]
    out: dict[str, tuple[dict, str]] = {}
    for autor in autores:
        chave = normalizar(autor)
        if chave in exato:
            out[autor] = (exato[chave], "exato"); continue
        ta = tokens(autor)
        if not ta:
            continue
        # candidatos: um conjunto de tokens contido no outro; vence o de maior interseção, se for único
        cands = [(len(ta & tp), p) for tp, p in toks if tp and (ta <= tp or tp <= ta)]
        if not cands:
            continue
        melhor = max(n for n, _ in cands)
        ids = {(p.get("casa"), p.get("id")) for n, p in cands if n == melhor}
        if len(ids) == 1:
            out[autor] = (next(p for n, p in cands if n == melhor), "aproximado")
    return out
