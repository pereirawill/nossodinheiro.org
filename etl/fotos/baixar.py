"""
Fotos oficiais de deputados e senadores, baixadas uma vez e servidas pelo próprio site.

    python -m etl.fotos.baixar              # só o que falta
    python -m etl.fotos.baixar --forcar     # rebaixa tudo

**Por que não apontar direto para o site da Câmara e do Senado** (era o que fazíamos, e quebrou):
- a Câmara responde **HTTP 503** quando um navegador pede as 513 fotos de uma vez — isoladamente a mesma URL
  responde 200, então o erro só aparece na página montada;
- a URL que o Senado publica na API é **http**, e o navegador bloqueia conteúdo http dentro de uma página https.

As fotos são reduzidas para 96 px de largura (o site mostra 36 px) e ficam em `site/public/fotos/<casa>/<id>.jpg`.
O manifesto `site/public/data/fotos.json` diz quais ids têm foto — a página usa isso para não gerar `<img>` quebrada.
Crédito nas páginas: Câmara dos Deputados e Senado Federal.
"""

from __future__ import annotations

import argparse
import html
import json
import logging
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image

log = logging.getLogger("etl.fotos")
PUB, FOTOS = Path("site/public/data"), Path("site/public/fotos")
LARGURA = 96          # o site mostra 36 px; 96 cobre tela retina sem pesar
QUALIDADE = 82
CASAS = {"camara": ("custo_deputado_*.json", "id_deputado"), "senado": ("custo_senador_*.json", "id_senador")}
# O STF não publica a foto numa API: ela está na página "Composição Atual" da Biblioteca, numa tabela em que a linha
# das imagens é seguida pela linha dos nomes, coluna a coluna. O par é lido dali — chutar pelas iniciais do arquivo
# trocaria Alexandre de Moraes (adm) por André Mendonça (alm).
STF_PAGINA = ("https://portal.stf.jus.br/textos/verTexto.asp"
              "?servico=bibliotecaConsultaProdutoBibliotecaPastaMinistro&pagina=ComposicaoAtual")
SEM_PESO = {"de", "da", "do", "dos", "das", "e", "ministro", "ministra"}


def _mais_novo(padrao: str) -> Path | None:
    arquivos = sorted(PUB.glob(padrao))
    return arquivos[-1] if arquivos else None


def _baixar_uma(c: httpx.Client, url: str, destino: Path) -> bool:
    try:
        r = c.get(url.replace("http://", "https://"), timeout=60)
        if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image"):
            log.warning("%s: HTTP %s", destino.name, r.status_code)
            return False
        img = Image.open(BytesIO(r.content)).convert("RGB")
        if img.width > LARGURA:
            img = img.resize((LARGURA, round(img.height * LARGURA / img.width)), Image.LANCZOS)
        destino.parent.mkdir(parents=True, exist_ok=True)
        img.save(destino, "JPEG", quality=QUALIDADE, optimize=True)
        return True
    except Exception as e:                                   # rede, imagem corrompida, formato inesperado
        log.warning("%s: %s", destino.name, e)
        return False


def _chave(v: str) -> set[str]:
    t = unicodedata.normalize("NFKD", (v or "").lower()).encode("ascii", "ignore").decode()
    return {p for p in re.split(r"[^a-z]+", t) if p and p not in SEM_PESO}


def fotos_do_stf(c: httpx.Client) -> dict[str, str]:
    """{nome do ministro: url da foto}, da página "Composição Atual" da Biblioteca do STF.

    O par sai do atributo `title` da própria imagem (`title="Ministro Edson Fachin"`). Tentar parear pela posição
    na tabela não funciona — parte das fotos está dentro de tabelas aninhadas — e parear pelas iniciais do arquivo
    trocaria Alexandre de Moraes (`foto_adm`) por André Mendonça (`foto_alm`).
    """
    r = c.get(STF_PAGINA, timeout=90)
    if r.status_code != 200:
        log.warning("página de composição do STF respondeu HTTP %s", r.status_code)
        return {}
    pares: dict[str, str] = {}
    for tag in re.findall(r"<img[^>]+>", r.text, re.I):
        src = re.search(r'src="\s*([^"]*?foto_[^"]*?\.jpg)\s*"', tag, re.I)
        titulo = re.search(r'title="([^"]+)"', tag, re.I)
        if not src or not titulo:
            continue
        nome = re.sub(r"\(.*?\)", "", html.unescape(titulo.group(1))).strip()
        if "ministr" in nome.lower():
            pares[nome] = src.group(1).strip()
    log.info("STF: %d fotos na página de composição", len(pares))
    return pares


def run(forcar: bool = False) -> Path:
    manifesto: dict[str, list[int]] = {}
    with httpx.Client(follow_redirects=True, headers={"User-Agent": "nossodinheiro.org (coleta de fotos oficiais)"}) as c:
        for casa, (padrao, chave) in CASAS.items():
            arq = _mais_novo(padrao)
            if not arq:
                log.warning("sem arquivo %s — rode o ETL da casa antes", padrao)
                continue
            pessoas = [p for p in json.loads(arq.read_text(encoding="utf-8")) if p.get("url_foto") and p.get(chave)]
            faltando = [p for p in pessoas if forcar or not (FOTOS / casa / f"{p[chave]}.jpg").exists()]
            log.info("%s: %d pessoas, %d foto(s) a baixar", casa, len(pessoas), len(faltando))
            if faltando:
                # 4 por vez: o servidor da Câmara derruba quem pede centenas de uma vez (foi o bug que isso corrige)
                with ThreadPoolExecutor(max_workers=4) as ex:
                    list(ex.map(lambda p: _baixar_uma(c, p["url_foto"], FOTOS / casa / f"{p[chave]}.jpg"), faltando))
            manifesto[casa] = sorted(p[chave] for p in pessoas if (FOTOS / casa / f"{p[chave]}.jpg").exists())
            log.info("%s: %d de %d com foto local", casa, len(manifesto[casa]), len(pessoas))

        # STF: casa o nome curto da página com o nome completo da folha, por tokens do sobrenome
        arq = _mais_novo("custo_ministro_stf_*.json")
        if arq:
            ministros = json.loads(arq.read_text(encoding="utf-8"))
            pares = fotos_do_stf(c)
            casados: list[str] = []
            for nome_pagina, url in pares.items():
                alvo = _chave(nome_pagina)
                achados = [m for m in ministros if alvo and alvo <= _chave(m["nome"])]
                if len(achados) != 1:
                    log.warning("STF: %r casou com %d ministros — foto não usada", nome_pagina, len(achados))
                    continue
                m = achados[0]
                destino = FOTOS / "stf" / f"{m['matricula']}.jpg"
                if forcar or not destino.exists():
                    _baixar_uma(c, url, destino)
                if destino.exists():
                    casados.append(str(m["matricula"]))
            manifesto["stf"] = sorted(set(casados))
            log.info("stf: %d de %d com foto local", len(manifesto["stf"]), len(ministros))

    saida = PUB / "fotos.json"
    saida.write_text(json.dumps({
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "largura_px": LARGURA, **manifesto,
        "fonte": "Fotos oficiais publicadas pela Câmara dos Deputados e pelo Senado Federal, reduzidas e servidas "
                 "por este site para não depender da disponibilidade dos servidores de origem",
    }, ensure_ascii=False), encoding="utf-8")
    return saida


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    ap = argparse.ArgumentParser()
    ap.add_argument("--forcar", action="store_true")
    run(**vars(ap.parse_args()))
