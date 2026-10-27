"""
Gera o mapa do Brasil por estado em SVG, usado pelo componente `MapaBrasil.astro`.

    python -m etl.mapa.gerar            # escreve site/src/lib/mapa-uf.ts

Fonte: IBGE, malhas territoriais, API v2 (`servicodados.ibge.gov.br/api/v2/malhas/BR?resolucao=2&formato=application/vnd.geo+json`),
que devolve um polígono por UF com `codarea` = código do IBGE. Projeção equirretangular simples com correção de longitude pelo
cosseno da latitude média do país — suficiente para um mapa de referência; não serve para medir distância ou área.
Simplificamos os contornos (distância mínima entre pontos e descarte de ilhas pequenas) para o arquivo caber no site sem JS.
Rodar de novo só quando o IBGE publicar uma malha nova (mudança de limite municipal/estadual é rara).
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path

import httpx

from etl.ufs import COD_PARA_UF, UF_PARA_NOME

log = logging.getLogger("etl.mapa")
MALHA = "https://servicodados.ibge.gov.br/api/v2/malhas/BR?resolucao=2&formato=application/vnd.geo+json"
SAIDA = Path("site/src/lib/mapa-uf.ts")
LARGURA = 1000.0
TOLERANCIA = 0.06      # graus: distância mínima entre pontos mantidos
AREA_MINIMA = 0.02     # graus²: descarta ilhas e recortes muito pequenos


def _aneis(geom: dict) -> list[list]:
    if geom["type"] == "Polygon":
        return [geom["coordinates"][0]]
    return [p[0] for p in geom["coordinates"]]


def _area(pontos: list) -> float:
    s = 0.0
    for (x1, y1), (x2, y2) in zip(pontos, pontos[1:] + pontos[:1]):
        s += x1 * y2 - x2 * y1
    return abs(s) / 2


def _simplificar(pontos: list) -> list:
    saida = [pontos[0]]
    for p in pontos[1:]:
        ax, ay = saida[-1]
        if math.hypot(p[0] - ax, p[1] - ay) >= TOLERANCIA:
            saida.append(p)
    if len(saida) > 2 and saida[0] != saida[-1]:
        saida.append(saida[0])
    return saida


def run() -> Path:
    with httpx.Client(timeout=300, follow_redirects=True) as c:
        r = c.get(MALHA); r.raise_for_status()
        geo = r.json()
    poligonos: dict[str, list[list]] = {}
    centroides: dict[str, tuple[float, float]] = {}
    for f in geo["features"]:
        uf = COD_PARA_UF.get(int(f["properties"]["codarea"]))
        if not uf:
            continue
        poligonos[uf] = [a for a in (_simplificar(anel) for anel in _aneis(f["geometry"])) if len(a) > 3 and _area(a) >= AREA_MINIMA]
        centroides[uf] = tuple(f["properties"]["centroide"])            # o IBGE já publica o centroide de cada UF
    todos = [p for aneis in poligonos.values() for anel in aneis for p in anel]
    minx, maxx = min(p[0] for p in todos), max(p[0] for p in todos)
    miny, maxy = min(p[1] for p in todos), max(p[1] for p in todos)
    k = math.cos(math.radians((miny + maxy) / 2))                      # achata a longitude como numa equirretangular
    escala = LARGURA / ((maxx - minx) * k)
    altura = round((maxy - miny) * escala, 1)

    def proj(p):
        return (round((p[0] - minx) * k * escala, 1), round((maxy - p[1]) * escala, 1))

    linhas = []
    for uf in sorted(poligonos):
        d = " ".join("M" + " L".join(f"{x},{y}" for x, y in (proj(p) for p in anel)) + " Z" for anel in poligonos[uf])
        cx, cy = proj(centroides[uf])
        linhas.append(f'  {{ uf: "{uf}", nome: "{UF_PARA_NOME[uf]}", cx: {cx}, cy: {cy}, d: "{d}" }},')
    conteudo = f'''/**
 * Mapa do Brasil por estado, em coordenadas de SVG. Gerado por `python -m etl.mapa.gerar` a partir das malhas
 * territoriais do IBGE (API v2, resolução 2), com projeção equirretangular e contornos simplificados.
 * Mapa de referência: não serve para medir distância nem área. Regerar só quando o IBGE publicar malha nova.
 */
export const MAPA_VIEWBOX = "0 0 {LARGURA:.0f} {altura}";

export const MAPA_UF: {{ uf: string; nome: string; cx: number; cy: number; d: string }}[] = [
{chr(10).join(linhas)}
];
'''
    SAIDA.write_text(conteudo, encoding="utf-8")
    log.info("mapa: %d estados, viewBox 0 0 %.0f %.1f, %.0f KB", len(poligonos), LARGURA, altura, len(conteudo) / 1024)
    return SAIDA


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
