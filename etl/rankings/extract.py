"""
Rankings internacionais — posição do Brasil em índices publicados por organismos oficiais e, quando
explicitado, por ONGs. Tudo sem chave.

    python -m etl.rankings.extract            # baixa e gera data/public/rankings.json

Fontes:
- Banco Mundial, API v2 (`api.worldbank.org/v2/country/all/indicator/<código>?format=json&mrv=6`):
  PIB, PIB per capita, expectativa de vida, Gini, despesa pública em educação, homicídios (dado da UNODC).
  Países = entradas cuja região não é "Aggregates" (217). Valor = ano mais recente disponível por país.
- PNUD, Relatório de Desenvolvimento Humano 2025: CSV `HDR25_Composite_indices_complete_time_series.csv`
  (IDH 2023 e posição oficial `hdi_rank_2023`).
- Transparência Internacional (ONG), Índice de Percepção da Corrupção 2025: `CPI2025_Results.xlsx`.
- Nomes em português: IBGE, API de localidades (`/api/v1/localidades/paises?lang=PT`, ISO-3166-3).

Saída: data/public/rankings.json — [{id, titulo, descricao, fonte, fonte_tipo, url, unidade, maior_melhor,
ano_referencia, paises:[{iso3, pais, valor, ano, posicao}], brasil:{posicao, valor, ano, total},
serie:[{ano, valor, posicao, total}]}]. A série (1985+ no Banco Mundial, 1990+ no IDH, 2012+ no CPI) traz a posição
do Brasil calculada ano a ano entre os países com dado naquele ano.
Posição: 1 = melhor segundo `maior_melhor` (para homicídios e Gini, menor é melhor).
"""

from __future__ import annotations

import csv
import io
import json
import logging
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

log = logging.getLogger("etl.rankings")
PUB = Path("data/public")
HEADERS = {"user-agent": "nossodinheiro-etl/0.1 (+https://nossodinheiro.org)"}

WB = "https://api.worldbank.org/v2"
INDICADORES_WB = [
    # id, código, título, descrição curta, unidade, maior_melhor
    ("pib", "NY.GDP.MKTP.CD", "PIB", "Produto Interno Bruto, em dólares correntes", "US$", True),
    ("pib_per_capita", "NY.GDP.PCAP.CD", "PIB per capita", "PIB dividido pela população, em dólares correntes", "US$ por pessoa", True),
    ("pib_per_capita_ppp", "NY.GDP.PCAP.PP.CD", "PIB per capita (poder de compra)", "Quanto cada habitante produz por ano, em dólares ajustados pelo custo de vida local (PPP)", "US$ PPP por pessoa", True),
    ("produtividade", "SL.GDP.PCAP.EM.KD", "Produtividade do trabalho", "PIB por pessoa empregada: quanto cada trabalhador produz por ano, em dólares de 2021 ajustados pelo poder de compra (PPP)", "US$ PPP por trabalhador", True),
    ("expectativa_vida", "SP.DYN.LE00.IN", "Expectativa de vida", "Anos de vida esperados ao nascer", "anos", True),
    ("gini", "SI.POV.GINI", "Desigualdade (Gini)", "Índice de Gini da renda: 0 = todos iguais, 100 = um só tem tudo", "índice (menor é mais igual)", False),
    ("educacao_pct_pib", "SE.XPD.TOTL.GD.ZS", "Gasto público em educação", "Despesa pública em educação como % do PIB", "% do PIB", True),
    ("homicidios", "VC.IHR.PSRC.P5", "Homicídios", "Homicídios intencionais por 100 mil habitantes (dado da UNODC, via Banco Mundial)", "por 100 mil hab. (menor é melhor)", False),
]
HDR_CSV = "https://hdr.undp.org/sites/default/files/2025_HDR/HDR25_Composite_indices_complete_time_series.csv"
CPI_XLSX = "https://files.transparencycdn.org/images/CPI2025_Results.xlsx"
IBGE_PAISES = "https://servicodados.ibge.gov.br/api/v1/localidades/paises?lang=PT"


def _get(c: httpx.Client, url: str, **kw) -> httpx.Response:
    r = c.get(url, **kw); r.raise_for_status(); return r


def nomes_pt(c: httpx.Client) -> dict[str, str]:
    d = _get(c, IBGE_PAISES).json()
    return {p["id"]["ISO-ALPHA-3"]: p["nome"] for p in d if p.get("id", {}).get("ISO-ALPHA-3")}


def paises_wb(c: httpx.Client) -> dict[str, str]:
    """iso3 → nome (inglês) só para países (sem agregados)."""
    d = _get(c, f"{WB}/country", params={"format": "json", "per_page": 400}).json()
    return {x["id"]: x["name"] for x in d[1] if x["region"]["value"] != "Aggregates"}


def indicador_wb(c: httpx.Client, codigo: str, paises: dict[str, str]) -> list[dict]:
    d = _get(c, f"{WB}/country/all/indicator/{codigo}", params={"format": "json", "mrv": 6, "per_page": 2000}).json()
    melhor: dict[str, tuple[int, float]] = {}
    for x in d[1]:
        iso, v = x.get("countryiso3code"), x.get("value")
        if iso not in paises or v is None:
            continue
        ano = int(x["date"])
        if iso not in melhor or ano > melhor[iso][0]:
            melhor[iso] = (ano, float(v))
    return [{"iso3": iso, "valor": v, "ano": ano} for iso, (ano, v) in melhor.items()]


ANO_INICIO = 1985


MIN_PAISES_SERIE = 50   # ano só entra na série se houver pelo menos tantos países com dado
JANELA_ANOS = 3         # indicadores esparsos (Gini, homicídios): usa o dado mais recente até 2 anos antes


def serie_de(valores_por_ano: dict[int, dict[str, float]], maior_melhor: bool, iso: str = "BRA",
             janela: int = 1, minimo: int = MIN_PAISES_SERIE) -> list[dict]:
    """{ano: {iso3: valor}} → série do país: [{ano, valor, posicao, total}], posição calculada entre os países com
    dado no ano (ou, com `janela` > 1, com o dado mais recente dentro da janela que termina no ano)."""
    out = []
    anos = sorted(valores_por_ano)
    for ano in anos:
        vals: dict[str, float] = {}
        for a in range(ano - janela + 1, ano + 1):
            vals.update(valores_por_ano.get(a, {}))      # ano mais recente sobrescreve
        if iso not in vals or len(vals) < minimo:
            continue
        ordem = sorted(vals.items(), key=lambda kv: -kv[1] if maior_melhor else kv[1])
        pos = next(i for i, (k, _) in enumerate(ordem, 1) if k == iso)
        out.append({"ano": ano, "valor": round(vals[iso], 4), "posicao": pos, "total": len(vals)})
    return out


def serie_wb(c: httpx.Client, codigo: str, paises: dict[str, str], maior_melhor: bool) -> list[dict]:
    d = _get(c, f"{WB}/country/all/indicator/{codigo}", params={"format": "json", "date": f"{ANO_INICIO}:2030", "per_page": 20000}).json()
    por_ano: dict[int, dict[str, float]] = {}
    for x in d[1]:
        iso, v = x.get("countryiso3code"), x.get("value")
        if iso in paises and v is not None:
            por_ano.setdefault(int(x["date"]), {})[iso] = float(v)
    return serie_de(por_ano, maior_melhor, janela=JANELA_ANOS)


def idh(c: httpx.Client) -> tuple[list[dict], list[dict]]:
    """→ (linhas 2023 com posição oficial, série do Brasil 1990–2023 com posição calculada por ano)."""
    txt = _get(c, HDR_CSV).content.decode("utf-8-sig", "ignore")
    rows = list(csv.DictReader(io.StringIO(txt)))
    out, por_ano = [], {}
    for r in rows:
        if not r.get("iso3") or len(r["iso3"]) != 3:
            continue
        v = r.get("hdi_2023")
        if v not in (None, ""):
            out.append({"iso3": r["iso3"], "valor": float(v), "ano": 2023, "posicao_oficial": int(float(r["hdi_rank_2023"])) if r.get("hdi_rank_2023") else None})
        for k, val in r.items():
            if k.startswith("hdi_") and k[4:].isdigit() and val not in (None, ""):
                por_ano.setdefault(int(k[4:]), {})[r["iso3"]] = float(val)
    return out, serie_de(por_ano, True)


def _xlsx_rows(conteudo: bytes, sheet: str = "xl/worksheets/sheet1.xml") -> list[list]:
    """Leitor mínimo de xlsx (sem dependências): devolve linhas como listas de valores."""
    z = zipfile.ZipFile(io.BytesIO(conteudo))
    ss = [re.sub(r"<[^>]+>", "", m) for m in re.findall(r"<si>(.*?)</si>", z.read("xl/sharedStrings.xml").decode("utf-8", "ignore"), flags=re.S)]
    xml = z.read(sheet).decode("utf-8", "ignore")
    linhas = []
    for row in re.findall(r"<row[^>]*>(.*?)</row>", xml, flags=re.S):
        cells = {}
        for ref, tipo, inner in re.findall(r'<c r="([A-Z]+)\d+"(?:[^>]*t="([^"]*)")?[^>]*>(.*?)</c>', row, flags=re.S):
            m = re.search(r"<v>(.*?)</v>", inner, flags=re.S)
            if not m:
                continue
            val = m.group(1)
            cells[ref] = ss[int(val)] if tipo == "s" else (float(val) if re.match(r"^-?\d+(\.\d+)?(E-?\d+)?$", val) else val)
        if cells:
            cols = sorted(cells, key=lambda k: (len(k), k))
            linhas.append([cells[k] for k in cols])
    return linhas


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def cpi(c: httpx.Client) -> tuple[list[dict], list[dict]]:
    """Planilha oficial CPI2025_Results.xlsx. Aba 1 = resultado 2025 (com posição oficial); aba 2 = série 2012–2025
    ("CPI score AAAA" / "Rank AAAA"), de onde sai a série do Brasil com a posição oficial de cada ano."""
    conteudo = _get(c, CPI_XLSX, headers={**HEADERS, "accept": "*/*"}).content
    linhas = _xlsx_rows(conteudo, "xl/worksheets/sheet2.xml")
    cab = next(i for i, l in enumerate(linhas) if any(isinstance(x, str) and x.strip().upper() == "ISO3" for x in l))
    h = [str(x).strip() for x in linhas[cab]]
    i_iso = next(i for i, x in enumerate(h) if x.upper() == "ISO3")
    col_score = {int(re.search(r"(\d{4})", x).group(1)): i for i, x in enumerate(h) if x.lower().startswith("cpi score") and re.search(r"\d{4}", x)}
    col_rank = {int(re.search(r"(\d{4})", x).group(1)): i for i, x in enumerate(h) if x.lower().startswith("rank") and re.search(r"\d{4}", x)}
    por_ano: dict[int, dict[str, float]] = {}
    rank_br: dict[int, int] = {}
    for l in linhas[cab + 1:]:
        if len(l) <= i_iso or not isinstance(l[i_iso], str) or len(l[i_iso].strip()) != 3:
            continue
        iso = l[i_iso].strip()
        for ano, i in col_score.items():
            v = _num(l[i]) if len(l) > i else None
            if v is not None:
                por_ano.setdefault(ano, {})[iso] = v
                if iso == "BRA" and ano in col_rank and len(l) > col_rank[ano] and _num(l[col_rank[ano]]) is not None:
                    rank_br[ano] = int(_num(l[col_rank[ano]]))
    ultimo = max(por_ano)
    atual = [{"iso3": iso, "valor": v, "ano": ultimo} for iso, v in por_ano[ultimo].items()]
    # posição oficial do último ano para todos os países
    for l in linhas[cab + 1:]:
        if len(l) > i_iso and isinstance(l[i_iso], str) and ultimo in col_rank and len(l) > col_rank[ultimo]:
            r = _num(l[col_rank[ultimo]])
            for a in atual:
                if a["iso3"] == l[i_iso].strip() and r is not None:
                    a["posicao_oficial"] = int(r)
    serie = serie_de(por_ano, True, minimo=20)
    for ponto in serie:                               # posição oficial da TI prevalece sobre a calculada
        if ponto["ano"] in rank_br:
            ponto["posicao"] = rank_br[ponto["ano"]]
    return atual, serie


def montar(id_: str, titulo: str, descricao: str, fonte: str, fonte_tipo: str, url: str, unidade: str,
           maior_melhor: bool, linhas: list[dict], nomes: dict[str, str], nomes_en: dict[str, str], serie: list[dict] | None = None) -> dict:
    linhas = [l for l in linhas if l["iso3"] in nomes or l["iso3"] in nomes_en]
    linhas.sort(key=lambda l: -l["valor"] if maior_melhor else l["valor"])
    paises = []
    for pos, l in enumerate(linhas, 1):
        paises.append({"iso3": l["iso3"], "pais": nomes.get(l["iso3"]) or nomes_en.get(l["iso3"], l["iso3"]), "valor": round(l["valor"], 4),
                       "ano": l["ano"], "posicao": l.get("posicao_oficial") or pos})
    br = next((p for p in paises if p["iso3"] == "BRA"), None)
    anos = sorted({p["ano"] for p in paises})
    return {"id": id_, "titulo": titulo, "descricao": descricao, "fonte": fonte, "fonte_tipo": fonte_tipo, "url": url,
            "unidade": unidade, "maior_melhor": maior_melhor, "ano_referencia": anos[-1] if anos else None,
            "anos_misturados": len(anos) > 1, "total": len(paises),
            "brasil": {"posicao": br["posicao"], "valor": br["valor"], "ano": br["ano"], "total": len(paises)} if br else None,
            "serie": serie or [], "paises": paises}


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers=HEADERS, timeout=120, follow_redirects=True) as c:
        nomes = nomes_pt(c); nomes_en = paises_wb(c)
        indices = []
        for id_, cod, tit, desc, unid, maior in INDICADORES_WB:
            linhas = indicador_wb(c, cod, nomes_en)
            serie = serie_wb(c, cod, nomes_en, maior)
            indices.append(montar(id_, tit, desc, "Banco Mundial (dados abertos)" + (" / UNODC" if id_ == "homicidios" else ""), "organismo oficial",
                                  f"https://data.worldbank.org/indicator/{cod}", unid, maior, linhas, nomes, nomes_en, serie))
            log.info("%s: %d países; série %d anos", tit, len(linhas), len(serie))
        linhas, serie = idh(c)
        indices.append(montar("idh", "Desenvolvimento humano (IDH)", "Índice de Desenvolvimento Humano 2023: renda, educação e expectativa de vida, de 0 a 1",
                              "PNUD, Relatório de Desenvolvimento Humano 2025", "organismo oficial", "https://hdr.undp.org/data-center", "índice 0–1", True, linhas, nomes, nomes_en, serie))
        linhas, serie = cpi(c)
        indices.append(montar("corrupcao", "Percepção da corrupção (CPI)", "Índice de Percepção da Corrupção 2025 no setor público: 0 = muito corrupto, 100 = muito íntegro",
                              "Transparência Internacional", "ONG", "https://www.transparency.org/en/cpi/2025", "pontos 0–100", True, linhas, nomes, nomes_en, serie))
        # título do CPI com o ano lido

    for i in indices:
        if not i["brasil"]:
            raise SystemExit(f"Brasil ausente em {i['id']} — fonte mudou?")
    out = PUB / "rankings.json"
    out.write_text(json.dumps({"gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"), "indices": indices}, ensure_ascii=False), encoding="utf-8")
    for i in indices:
        b = i["brasil"]; log.info("%-32s Brasil %3dº de %3d (%s, %s)", i["titulo"], b["posicao"], b["total"], b["valor"], b["ano"])
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run()
