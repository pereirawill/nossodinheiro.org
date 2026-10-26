"""
Gráfico — Top N deputados por custo estimado no ano (PNG 1080×1350 p/ Instagram).

    python -m etl.camara.chart --ano 2026 [--top 20] [--por partido|deputado]

Lê data/public/custo_deputado_<ano>.json; escreve data/public/custo_top<N>_<ano>.png
Barras horizontais empilhadas: subsídio | CEAP (real) | verba de gabinete (teto).
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

PUB = Path("data/public")
COLORS = {"subsidio": "#2a78d6", "ceap": "#eb6834", "verba_gabinete_teto": "#1baf7a"}
LABELS = {"subsidio": "Subsídio (salário)", "ceap": "Cota parlamentar (gasto real)",
          "verba_gabinete_teto": "Verba de gabinete (teto)"}
INK, INK2, GRID = "#1a1a19", "#5f5e58", "#e6e4df"


def brl(v: float, _pos=None) -> str:
    if v >= 1_000_000:
        return f"R$ {v/1e6:.1f} mi".replace(".", ",")
    return f"R$ {v/1e3:.0f} mil"


def render(ano: int, top: int, por: str) -> Path:
    rows = json.loads((PUB / f"custo_deputado_{ano}.json").read_text(encoding="utf-8"))
    meta = json.loads((PUB / f"meta_{ano}.json").read_text(encoding="utf-8"))

    if por == "partido":
        agg: dict[str, dict] = defaultdict(lambda: {"subsidio": 0, "ceap": 0, "verba_gabinete_teto": 0, "n": 0})
        for r in rows:
            a = agg[r["partido"]]
            for k in ("subsidio", "ceap", "verba_gabinete_teto"):
                a[k] += r[k]
            a["n"] += 1
        items = [{"label": f"{p} ({a['n']})", **a} for p, a in agg.items()]
        titulo = f"Custo estimado da Câmara por partido — {ano}"
    else:
        items = [{"label": f"{r['nome']} ({r['partido']}-{r['uf']})", **r} for r in rows]
        titulo = f"Os {top} deputados federais mais caros — {ano}"

    items.sort(key=lambda r: r["subsidio"] + r["ceap"] + r["verba_gabinete_teto"], reverse=True)
    items = items[:top][::-1]  # maior no topo

    fig, ax = plt.subplots(figsize=(10.8, 13.5), dpi=100)
    fig.patch.set_facecolor("white")
    y = range(len(items))
    left = [0.0] * len(items)
    for key in ("subsidio", "ceap", "verba_gabinete_teto"):
        vals = [it[key] for it in items]
        ax.barh(y, vals, left=left, color=COLORS[key], label=LABELS[key], height=0.62,
                edgecolor="white", linewidth=2)
        left = [l + v for l, v in zip(left, vals)]
    for yi, tot in zip(y, left):
        ax.text(tot + max(left) * 0.01, yi, brl(tot), va="center", fontsize=10, color=INK)

    ax.set_yticks(list(y)); ax.set_yticklabels([it["label"] for it in items], fontsize=10, color=INK)
    ax.xaxis.set_major_formatter(FuncFormatter(brl))
    ax.tick_params(axis="x", colors=INK2, labelsize=9)
    ax.set_xlim(0, max(left) * 1.14)
    for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.grid(axis="x", color=GRID, linewidth=0.8); ax.set_axisbelow(True)
    ax.legend(loc="lower right", frameon=False, fontsize=10)

    meses = meta["meses_considerados"]
    fig.suptitle(titulo, x=0.03, ha="left", fontsize=20, fontweight="bold", color=INK, y=0.975)
    ax.set_title(f"{meses} meses de {ano} · subsídio + cota parlamentar (gasto real) + verba de gabinete (teto, não o gasto real)",
                 loc="left", fontsize=10.5, color=INK2, pad=14)
    fig.text(0.03, 0.012,
             f"Fonte: API de Dados Abertos da Câmara (CEAP) e camara.leg.br/transparencia. "
             f"Gerado em {meta['gerado_em']}. Metodologia completa no site.",
             fontsize=8.5, color=INK2)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    out = PUB / f"custo_top{top}_{por}_{ano}.png"
    fig.savefig(out, dpi=100)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano", type=int, required=True)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--por", choices=["deputado", "partido"], default="deputado")
    a = ap.parse_args()
    print(render(a.ano, a.top, a.por))
