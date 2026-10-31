#!/usr/bin/env python3
"""
Checagem do site em tela de celular — o que o `checar_site.py` não enxerga, porque exige um motor de layout.

    make site                                 # precisa do build em site/dist
    python tools/checar_celular.py            # 390×844, todas as páginas de primeiro nível + uma de cada molde
    python tools/checar_celular.py --largura 360 --paginas / /renda/ /impostos/
    python tools/checar_celular.py --json
    make checar-celular

Abre cada página num Chromium sem janela (Playwright), no tamanho de um celular, e MEDE o DOM. Nasceu em
31/10/2026, quando o dono abriu a home no celular e viu "o gráfico enorme" e "tabelas que rolam para o lado": eram
uma rosca de 680×680 px numa tela de 390, uma regra de celular anulada por outra que vinha depois no CSS, e 125 px
de vazamento invisível causado pelas dicas ⓘ. Nenhum dos três aparecia no checador estático.

O que mede, e o nível de cada achado:

- **vazamento** (ERRO): elemento que passa da borda direita da tela sem estar dentro de um cartão que rola nem ser
  fixo. É latente — `overflow-x: clip` no body esconde, mas é bug e volta quando a regra mudar.
- **rolagem da página** (ERRO): a página inteira rola na horizontal.
- **gráfico gigante** (ERRO): SVG renderizado com mais de 1,5× a largura do próprio viewBox (uma rosca desenhada em
  200 unidades e exibida com 680 px foi esticada por CSS; um gráfico de 920 exibido com 600 está encolhido, e tudo
  bem), ou mais largo que 1,7× a tela (os gráficos largos rolam dentro do cartão até 600 px; acima disso algo forçou).
- **tabela rolando**: quanto a tabela excede o cartão. AVISO quando tem até 4 colunas e excede mais de 1/4 da
  tela (dava para caber), ou quando excede mais que uma tela inteira seja qual for o número de colunas; NOTA acima
  de 8 px. Tabela de 7 colunas por estado rola mesmo — é inerente.
- **cartão alto demais** (AVISO): `.stat` mais alto que a largura da tela — é o `<b>` dentro do `<span>` do cartão
  herdando a fonte-herói e virando texto gigante (armadilha já registrada no CLAUDE.md).
- **gráfico rolando** (NOTA): só a contagem de cartões que rolam por causa de um SVG largo, para acompanhar.
- **coluna desalinhada** (ERRO): número de cabeçalhos visíveis diferente do número de células da primeira linha —
  é o erro que `.oculta-m` cria quando vai no `th` e não no `td` (ou o contrário).

Sai com código 1 se houver ERRO. Formato de saída igual ao do `checar_site.py`.
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import threading
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIST = RAIZ / "site/dist"
ERRO, AVISO, NOTA = "ERRO", "aviso", "nota"

# Além de todas as páginas de primeiro nível, uma página de cada molde gerado em massa (filtro por UF/partido,
# município, tribunal). Só a primeira de cada grupo: as outras são o mesmo template com outros números.
MOLDES_EXTRAS = ["deputados/partido/", "senadores/partido/", "municipios/uf/", "judiciario/"]

# Roda dentro da página. Devolve só números e rótulos curtos — nunca o DOM inteiro.
MEDIR_JS = r"""
() => {
  const W = document.documentElement.clientWidth;
  const rolavel = (e) => { for (let p = e.parentElement; p && p !== document.body; p = p.parentElement) {
      const o = getComputedStyle(p).overflowX; if (o === 'auto' || o === 'scroll' || o === 'hidden' || o === 'clip') return true; }
    return false; };
  const rotulo = (e) => (e.tagName.toLowerCase() + (e.className && typeof e.className === 'string' ? '.' + e.className.split(' ')[0] : '')
      + ' "' + (e.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 40) + '"');
  const vazam = [];
  for (const e of document.querySelectorAll('body *')) {
    if (e.closest('svg') && e.tagName.toLowerCase() !== 'svg') continue;      // filhos de SVG não contam
    const cs = getComputedStyle(e);
    if (cs.position === 'fixed' || cs.display === 'none') continue;
    const r = e.getBoundingClientRect();
    if (r.width === 0 || r.right <= W + 2 || rolavel(e)) continue;
    vazam.push({ r: Math.round(r.right), t: rotulo(e) });
  }
  vazam.sort((a, b) => b.r - a.r);
  const svgs = [...document.querySelectorAll('svg[role="img"]')].map((s) => { const r = s.getBoundingClientRect();
    const vbw = parseFloat(((s.getAttribute('viewBox') || '').split(/\s+/)[2]) || '0');
    return { w: Math.round(r.width), h: Math.round(r.height), vbw, vb: (s.getAttribute('viewBox') || '').slice(0, 14),
             t: (s.getAttribute('aria-label') || '').slice(0, 50) }; });
  const vis = (els) => [...els].filter((e) => getComputedStyle(e).display !== 'none').reduce((n, e) => n + (e.colSpan || 1), 0);
  const tabelas = [...document.querySelectorAll('table')].map((t) => { const tr = t.querySelector('tbody tr');
    return { over: t.scrollWidth - t.clientWidth, cab: ((t.querySelector('th') || {}).textContent || '').trim().slice(0, 24),
      cols: vis(t.querySelectorAll('thead th')), tds: tr ? vis(tr.querySelectorAll(':scope > td')) : null }; });
  const stats = [...document.querySelectorAll('.stat')].map((s) => ({ h: Math.round(s.getBoundingClientRect().height),
    t: ((s.querySelector('b') || {}).textContent || '').trim().slice(0, 24) }));
  const cartoesRolando = [...document.querySelectorAll('.card')].filter((c) => c.scrollWidth > c.clientWidth + 4 && c.querySelector(':scope > svg')).length;
  return { W, docOver: document.documentElement.scrollWidth - W, vazam: vazam.slice(0, 3), nVazam: vazam.length,
           svgs, tabelas, stats, cartoesRolando };
}
"""


class Achados:
    def __init__(self) -> None:
        self.itens: list[dict] = []

    def add(self, nivel: str, regra: str, onde: str, o_que: str, fazer: str = "") -> None:
        self.itens.append({"nivel": nivel, "regra": regra, "onde": onde, "o_que": o_que, "fazer": fazer})

    @property
    def erros(self) -> int:
        return sum(1 for i in self.itens if i["nivel"] == ERRO)


def paginas_padrao() -> list[str]:
    """Todas as rotas de primeiro nível mais uma página de cada molde em massa."""
    rotas = ["/"] + sorted(f"/{p.parent.name}/" for p in DIST.glob("*/index.html"))
    for molde in MOLDES_EXTRAS:
        achadas = sorted(DIST.glob(f"{molde}*/index.html"))
        if achadas:
            rel = achadas[0].parent.relative_to(DIST).as_posix()
            rotas.append(f"/{rel}/")
    # um município: molde de /municipios/<uf>/<slug>/
    muni = sorted(DIST.glob("municipios/*/*/index.html"))
    if muni:
        rotas.append("/" + muni[0].parent.relative_to(DIST).as_posix() + "/")
    return rotas


class _Quieto(SimpleHTTPRequestHandler):
    def log_message(self, *a, **k) -> None:                        # sem log de acesso no terminal
        pass


def servidor_local() -> tuple[ThreadingHTTPServer, int]:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]
    handler = partial(_Quieto, directory=str(DIST))
    srv = ThreadingHTTPServer(("127.0.0.1", porta), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, porta


def avaliar(a: Achados, rota: str, m: dict) -> None:
    W = m["W"]
    if m["docOver"] > 2:
        a.add(ERRO, "rolagem da página", rota, f"a página rola {m['docOver']} px na horizontal numa tela de {W} px",
              "achar o elemento largo: normalmente um SVG fora de .card ou um bloco com largura fixa")
    if m["nVazam"]:
        culpados = "; ".join(f"{v['t']} até x={v['r']}" for v in m["vazam"])
        a.add(ERRO, "vazamento", rota,
              f"{m['nVazam']} elemento(s) passam da borda direita ({W} px) sem estar num cartão que rola: {culpados}",
              "é latente — o overflow-x: clip do body esconde, mas volta se a regra mudar; conferir o elemento apontado")
    for s in m["svgs"]:
        esticado = s["vbw"] > 0 and s["w"] > 1.5 * s["vbw"]
        if esticado or s["w"] > 1.7 * W:
            a.add(ERRO, "gráfico gigante", rota,
                  f"SVG de {s['w']}×{s['h']} px numa tela de {W} (viewBox {s['vb']!r}, "
                  f"{s['w'] / s['vbw']:.1f}× o desenho; {s['t']!r})" if s["vbw"] else f"SVG de {s['w']}×{s['h']} px",
                  "rosca ou gráfico pequeno pegou a regra de min-width dos gráficos largos; ver .card > svg em Base.astro")
    for t in m["tabelas"]:
        if t["tds"] is not None and t["cols"] and t["tds"] != t["cols"]:
            a.add(ERRO, "coluna desalinhada", rota,
                  f"tabela '{t['cab']}': {t['cols']} cabeçalhos visíveis e {t['tds']} células na primeira linha",
                  "um .oculta-m (ou .desc) está no th sem o td correspondente, ou vice-versa")
        if (t["cols"] <= 4 and t["over"] > W / 4) or t["over"] > W:
            a.add(AVISO, "tabela rolando", rota,
                  f"tabela '{t['cab']}' ({t['cols']} colunas) excede o cartão em {t['over']} px",
                  "marcar coluna secundária com .oculta-m, ou deixar o cabeçalho/rótulo quebrar linha")
        elif t["over"] > 8:
            a.add(NOTA, "tabela rolando", rota, f"tabela '{t['cab']}' ({t['cols']} colunas) excede o cartão em {t['over']} px")
    for s in m["stats"]:
        if s["h"] > W:
            a.add(AVISO, "cartão alto demais", rota, f".stat '{s['t']}' tem {s['h']} px de altura",
                  "provável <b> dentro do <span> herdando a fonte-herói; usar texto puro")
    if m["cartoesRolando"]:
        a.add(NOTA, "gráfico rolando", rota, f"{m['cartoesRolando']} cartão(ões) rolam por causa de um SVG largo")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--largura", type=int, default=390)
    p.add_argument("--altura", type=int, default=844)
    p.add_argument("--paginas", nargs="*", help="rotas a testar (padrão: primeiro nível + um de cada molde)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--nivel", choices=[ERRO, AVISO, NOTA], default=NOTA)
    args = p.parse_args()

    if not (DIST / "index.html").exists():
        print("site/dist não existe: rode `make site` antes.", file=sys.stderr)
        return 2
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright não instalado: pip install playwright && python -m playwright install chromium", file=sys.stderr)
        return 2

    rotas = args.paginas or paginas_padrao()
    a = Achados()
    srv, porta = servidor_local()
    try:
        with sync_playwright() as pw:
            nav = pw.chromium.launch()
            ctx = nav.new_context(viewport={"width": args.largura, "height": args.altura}, device_scale_factor=2,
                                  is_mobile=True, has_touch=True)
            pag = ctx.new_page()
            for rota in rotas:
                try:
                    pag.goto(f"http://127.0.0.1:{porta}{rota}", wait_until="load", timeout=30_000)
                    pag.wait_for_timeout(150)                        # fontes e layout assentam
                    avaliar(a, rota, pag.evaluate(MEDIR_JS))
                except Exception as e:                               # uma página quebrada não derruba as outras
                    a.add(ERRO, "checador", rota, f"não consegui medir: {e!r}", "abrir a página e ver o que falhou")
            nav.close()
    finally:
        srv.shutdown()

    ordem = {ERRO: 0, AVISO: 1, NOTA: 2}
    itens = sorted(a.itens, key=lambda i: (ordem[i["nivel"]], i["regra"], i["onde"]))
    itens = [i for i in itens if ordem[i["nivel"]] <= ordem[args.nivel]]
    if args.json:
        print(json.dumps({"gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                          "viewport": [args.largura, args.altura], "paginas": rotas, "achados": itens},
                         ensure_ascii=False, indent=1))
        return 1 if a.erros else 0

    por_regra: dict[str, list[dict]] = {}
    for i in itens:
        por_regra.setdefault(i["regra"], []).append(i)
    for regra, lista in por_regra.items():
        print(f"\n## {regra} ({len(lista)})")
        for i in lista:
            print(f"  [{i['nivel']}] {i['onde']}\n      {i['o_que']}" + (f"\n      → {i['fazer']}" if i["fazer"] else ""))
    avisos = sum(1 for i in a.itens if i["nivel"] == AVISO)
    print(f"\n{len(rotas)} página(s) a {args.largura}×{args.altura}: {a.erros} erro(s), {avisos} aviso(s), "
          f"{len(a.itens) - a.erros - avisos} nota(s).")
    return 1 if a.erros else 0


if __name__ == "__main__":
    sys.exit(main())
