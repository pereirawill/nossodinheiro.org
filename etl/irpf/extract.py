"""
Imposto de Renda — o que os brasileiros declararam ganhar, quanto pagaram e quanto da renda do topo é isenta.

    python -m etl.irpf.extract            # gera data/public/irpf.json

Fonte única: **Receita Federal, "Grandes Números do IRPF"**, planilha anual de tabelas (~19 MB, sem chave). A página-índice
lista uma edição por ano; pegamos sempre a mais recente pelo link `grandes-numeros-do-irpf-<edição>-ano-calendario-<ano>-tabelas`
(o slug varia: a edição 2024 termina em `-tabelas-1`, por isso não dá para montar a URL por template).

Tabelas usadas (das 22 da planilha):
- **Tab8**  declarações por faixa de rendimento total (tributável + tributação exclusiva + isentos) em salários mínimos, UF e
            tipo de formulário. É a base da curva de alíquota efetiva e da composição da renda isenta.
- **Tab15** declarações por **natureza da ocupação** (servidor público das três esferas, empregado do setor privado,
            proprietário de empresa, capitalista, aposentado, MEI…).
- **Tab16** declarações por **ocupação principal** (134 categorias: médico, advogado, membro do Poder Judiciário, titular de
            cartório…). A categoria `NULL` entra como "não informada" — são 6,6 milhões de declarantes, não podem sumir.

Salário mínimo do ano-calendário: **Banco Central, SGS série 1619** (o valor de dezembro). A planilha publica as faixas em
salários mínimos e não em reais; a conversão é nossa e está conferida contra a tabela 5 (a base de cálculo média de cada faixa
cai dentro dos limites convertidos). Está declarado na metodologia.

Regras:
- `x` na planilha = célula suprimida por sigilo (poucos contribuintes). Lemos como zero e contamos quantas foram, em
  `celulas_suprimidas`. **Nunca** reconstruímos uma célula suprimida subtraindo do total: o controle é deliberado da Receita.
- Renda = tributável + tributação exclusiva + isentos e não tributáveis, como a própria faixa da Tab8 define.
- Alíquota efetiva = imposto devido total ÷ renda. Não é a alíquota da tabela do IR: o denominador inclui renda isenta e,
  no topo, herança recebida, que não é renda recorrente. A página mostra a composição ao lado para o leitor ver isso.
- Comparação com o subsídio do deputado usa o subsídio **em vigor no ano-calendário** (etl/camara/config.py), 13 + 1/3 por ano.
- Universo: só quem declara (41,7 milhões em 2024). Não é a população, e nenhum percentual daqui é "dos brasileiros".
"""

from __future__ import annotations

import io
import json
import logging
import re
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import httpx

from etl.camara.config import SUBSIDIOS_POR_ANO, subsidio_mensal_em

log = logging.getLogger("etl.irpf")
PUB = Path("data/public")
RAW = Path("data/raw")
INDICE = ("https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/estudos/imposto-de-renda/"
          "estudos-por-ano/grandes-numeros-do-IRPF-2008-a-2025")
SGS_SALARIO_MINIMO = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1619/dados?formato=json&dataInicial=01/01/{ano}"
UA = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}

# Faixas da planilha, em salários mínimos anuais (piso, teto). A ordem é a da Receita; o Excel traz as linhas em ordem alfabética.
FAIXAS: list[tuple[str, float, float | None]] = [
    ("Até 1/2", 0, 0.5), ("De 1/2 a 1", 0.5, 1), ("De 1 a 2", 1, 2), ("De 2 a 3", 2, 3), ("De 3 a 5", 3, 5),
    ("De 5 a 7", 5, 7), ("De 7 a 10", 7, 10), ("De 10 a 15", 10, 15), ("De 15 a 20", 15, 20), ("De 20 a 30", 20, 30),
    ("De 30 a 40", 30, 40), ("De 40 a 60", 40, 60), ("De 60 a 80", 60, 80), ("De 80 a 160", 80, 160),
    ("De 160 a 240", 160, 240), ("De 240 a 320", 240, 320), ("Mais de 320", 320, None),
]
FAIXA_COL = "faixa_de_rendim_tributavel_mais_trib_exclusiva_mais_isentos_em_sal_minimos"
RENDA_COLS = ("rendimento_tributavel_total", "rend_sujeitos_a_tribut_exclusiva", "rend_isentos_e_nao_tributaveis")
# Componentes da renda isenta (a planilha detalha 9; mantemos todos, com rótulo legível).
ISENTOS = {
    "rend_isentos_lucros_dividendos": "Lucros e dividendos",
    "rend_isentos_socio_me_simples": "Rendimento de sócio ou titular de microempresa",
    "rend_isentos_transf_heranca": "Herança, doação e meação",
    "rend_isentos_aposentadoria_65": "Parcela isenta da aposentadoria (65 anos ou mais)",
    "rend_isentos_atividade_rural": "Atividade rural",
    "rend_isentos_indenizacao_fgts": "Indenização e FGTS",
    "rend_isentos_poupanca": "Caderneta de poupança e letras isentas",
    "rend_isentos_incorp_res_cap_bonif_acao": "Incorporação de reservas e bonificação em ações",
    "rend_isentos_outros": "Outros rendimentos isentos",
}
# Grupo da natureza da ocupação: usado só para ordenar e colorir a tabela da página. A classificação é nossa e está
# na metodologia; os rótulos originais da Receita ficam intactos no JSON.
GRUPOS_NATUREZA = [
    (r"^Membro ou servidor público|^Servidor público|^Militar$", "Setor público"),
    (r"^Empregado de empresa pública|^Empregado de instituições financeiras", "Estatais e bancos"),
    (r"^Empregado de empresa do setor privado|^Empregado ou contratado de organismo", "Setor privado"),
    (r"^Proprietário de empresa|^Microempreendedor", "Donos de negócio"),
    (r"^Capitalista", "Capital"),
    (r"^Profissional liberal", "Autônomos"),
    (r"^Aposentado|^Beneficiário de pensão", "Aposentados e pensionistas"),
]


def _n(v) -> float:
    """Número da célula; 'x' (sigilo) e vazio viram zero."""
    return float(v) if isinstance(v, (int, float)) else 0.0


def _suprimida(v) -> bool:
    return isinstance(v, str) and v.strip().lower() == "x"


def planilha(c: httpx.Client) -> tuple[bytes, int, int, str]:
    """Baixa a planilha de tabelas da edição mais recente. Devolve (conteúdo, edição, ano-calendário, url)."""
    r = c.get(INDICE); r.raise_for_status()
    achados = re.findall(r'href="([^"]*grandes-numeros-do-irpf-(\d{4})-ano-calendario-(\d{4})[^"]*tabelas[^"]*)"', r.text, re.I)
    if not achados:
        raise SystemExit("índice dos Grandes Números do IRPF não lista nenhuma planilha de tabelas")
    url, edicao, ano = max(achados, key=lambda t: (int(t[1]), int(t[2])))
    url = url.rstrip("/")
    if not url.endswith("@@download/file"):
        url = url.removesuffix("/view") + "/@@download/file"
    cache = RAW / f"gn_irpf_ac{ano}.xlsx"
    if cache.exists() and cache.stat().st_size > 1_000_000:
        log.info("planilha em cache: %s (%.1f MB)", cache, cache.stat().st_size / 1e6)
        return cache.read_bytes(), int(edicao), int(ano), url
    log.info("baixando %s", url)
    with c.stream("GET", url) as resp:
        resp.raise_for_status()
        conteudo = b"".join(resp.iter_bytes(1 << 20))
    if conteudo[:2] != b"PK":
        raise SystemExit(f"resposta não é xlsx: {url}")
    RAW.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(conteudo)
    log.info("planilha %s: %.1f MB (edição %s, ano-calendário %s)", cache.name, len(conteudo) / 1e6, edicao, ano)
    return conteudo, int(edicao), int(ano), url


def tabela(wb, nome: str):
    """Linhas da aba como dicionários. A primeira linha é o título da tabela; a segunda, o cabeçalho."""
    it = wb[nome].iter_rows(values_only=True)
    next(it)
    cab = [c for c in next(it) if c]
    for linha in it:
        if linha[0] is None:
            continue
        yield dict(zip(cab, linha))


def salario_minimo(c: httpx.Client, ano: int) -> float:
    """Salário mínimo mensal vigente em dezembro do ano-calendário (Banco Central, SGS 1619)."""
    r = c.get(SGS_SALARIO_MINIMO.format(ano=ano)); r.raise_for_status()
    do_ano = [float(d["valor"]) for d in r.json() if d["data"].endswith(f"/{ano}")]
    if not do_ano:
        raise SystemExit(f"SGS 1619 não tem salário mínimo de {ano}")
    return do_ano[-1]


def subsidio_do_ano(ano: int) -> dict:
    """Quanto um deputado federal recebeu de subsídio no ano-calendário (13 + 1/3, pelo valor de cada mês)."""
    mensais = [subsidio_mensal_em(date(ano, m, 1)) for m in range(1, 13)]
    extras = (SUBSIDIOS_POR_ANO - 12) * mensais[-1]          # 13º + 1/3 de férias, pelo valor de dezembro
    return {"ano": ano, "mensal_dezembro": mensais[-1], "anual": round(sum(mensais) + extras, 2)}


def montar(conteudo: bytes, c: httpx.Client, edicao: int, ano: int, url: str) -> dict:
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(conteudo), read_only=True, data_only=True)
    sm = salario_minimo(c, ano)
    sm_anual = sm * 12
    suprimidas = 0

    # --- Tab8: faixas de renda ------------------------------------------------------------------------------------
    agg: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for d in tabela(wb, "Tab8"):
        f = str(d[FAIXA_COL]).strip()
        suprimidas += sum(1 for v in d.values() if _suprimida(v))
        agg[f]["contribuintes"] += _n(d["qtde_contribuintes"])
        agg[f]["imposto"] += _n(d["imposto_devido_total"])
        agg[f]["bens"] += _n(d["bens_e_direitos"])
        for col in RENDA_COLS:
            agg[f][col] += _n(d[col])
        for col in ISENTOS:
            agg[f][col] += _n(d[col])

    declarantes = sum(v["contribuintes"] for v in agg.values())
    renda_total = sum(sum(v[c2] for c2 in RENDA_COLS) for v in agg.values())
    imposto_total = sum(v["imposto"] for v in agg.values())

    faixas = []
    for rotulo, piso, teto in FAIXAS:
        v = agg.get(rotulo)
        if not v:
            log.warning("faixa ausente na planilha: %s", rotulo)
            continue
        renda = sum(v[c2] for c2 in RENDA_COLS)
        q = v["contribuintes"]
        faixas.append({
            "faixa": rotulo, "piso_sm": piso, "teto_sm": teto,
            "piso_anual": round(piso * sm_anual, 2), "teto_anual": round(teto * sm_anual, 2) if teto else None,
            "contribuintes": int(q), "renda": round(renda, 2),
            "renda_media_mensal": round(renda / q / 12, 2) if q else None,
            "tributavel": round(v["rendimento_tributavel_total"], 2),
            "exclusiva": round(v["rend_sujeitos_a_tribut_exclusiva"], 2),
            "isenta": round(v["rend_isentos_e_nao_tributaveis"], 2),
            "pct_isenta": round(v["rend_isentos_e_nao_tributaveis"] / renda, 4) if renda else None,
            "imposto": round(v["imposto"], 2),
            "aliquota_efetiva": round(v["imposto"] / renda, 4) if renda else None,
            "pct_do_imposto": round(v["imposto"] / imposto_total, 4) if imposto_total else None,
            "pct_da_renda": round(renda / renda_total, 4) if renda_total else None,
            "pct_dos_declarantes": round(q / declarantes, 4) if declarantes else None,
            "bens": round(v["bens"], 2),
            "isentos": {rot: round(v[col], 2) for col, rot in ISENTOS.items()},
        })

    # --- Tab15 e Tab16: ocupação ----------------------------------------------------------------------------------
    def por_categoria(aba: str, coluna: str) -> list[dict]:
        nonlocal suprimidas
        ag: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for d in tabela(wb, aba):
            k = "Não informada" if d[coluna] in (None, "NULL") else str(d[coluna]).strip()
            suprimidas += sum(1 for v in d.values() if _suprimida(v))
            ag[k]["contribuintes"] += _n(d["qtde_contribuintes"])
            ag[k]["imposto"] += _n(d["imposto_devido_total"])
            for col in RENDA_COLS:
                ag[k][col] += _n(d[col])
            ag[k]["dividendos"] += _n(d["rend_isentos_lucros_dividendos"]) + _n(d["rend_isentos_socio_me_simples"])
        saida = []
        for k, v in ag.items():
            renda = sum(v[c2] for c2 in RENDA_COLS)
            q = v["contribuintes"]
            item = {"nome": k, "contribuintes": int(q), "renda": round(renda, 2),
                    "renda_media_mensal": round(renda / q / 12, 2) if q else None,
                    "pct_isenta": round(v["rend_isentos_e_nao_tributaveis"] / renda, 4) if renda else None,
                    "pct_dividendos": round(v["dividendos"] / renda, 4) if renda else None,
                    "aliquota_efetiva": round(v["imposto"] / renda, 4) if renda else None}
            if coluna == "natureza_da_ocupacao":
                item["grupo"] = next((g for padrao, g in GRUPOS_NATUREZA if re.search(padrao, k)), "Outros")
            saida.append(item)
        return sorted(saida, key=lambda i: -i["contribuintes"])

    natureza = por_categoria("Tab15", "natureza_da_ocupacao")
    ocupacoes = por_categoria("Tab16", "ocupacao_principal")

    # --- invariantes ---------------------------------------------------------------------------------------------
    totais = {"Tab8": declarantes, "Tab15": sum(i["contribuintes"] for i in natureza),
              "Tab16": sum(i["contribuintes"] for i in ocupacoes)}
    if not 30e6 < declarantes < 80e6:
        raise SystemExit(f"{declarantes:.0f} declarantes: planilha ou coluna mudou?")
    if max(totais.values()) - min(totais.values()) > declarantes * 0.001:
        raise SystemExit(f"totais divergem entre abas: {totais}")
    if imposto_total < 50e9:
        raise SystemExit(f"imposto devido total R$ {imposto_total:.0f}: unidade mudou?")

    # --- comparação com o subsídio do deputado -------------------------------------------------------------------
    sub = subsidio_do_ano(ano)
    sub["em_sm"] = round(sub["anual"] / sm_anual, 1)
    faixa_corte = next((f for f in faixas if f["piso_sm"] <= sub["em_sm"] and (f["teto_sm"] is None or sub["em_sm"] < f["teto_sm"])), None)
    acima = [f for f in faixas if f["piso_sm"] >= (faixa_corte["teto_sm"] if faixa_corte else 0)]
    sub["faixa"] = faixa_corte["faixa"] if faixa_corte else None
    sub["contribuintes_na_faixa"] = faixa_corte["contribuintes"] if faixa_corte else None
    sub["contribuintes_acima_da_faixa"] = sum(f["contribuintes"] for f in acima)
    sub["pct_acima_da_faixa"] = round(sub["contribuintes_acima_da_faixa"] / declarantes, 4)

    return {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "edicao": edicao, "ano_calendario": ano,
        "fonte": f"Receita Federal, Grandes Números do IRPF {edicao} (ano-calendário {ano}) — tabelas 8, 15 e 16",
        "url": url,
        "salario_minimo": {"mensal": sm, "anual": round(sm_anual, 2), "ano": ano,
                           "fonte": "Banco Central, SGS série 1619 (salário mínimo mensal), valor de dezembro"},
        "declarantes": int(declarantes), "renda_total": round(renda_total, 2),
        "imposto_devido_total": round(imposto_total, 2),
        "aliquota_media": round(imposto_total / renda_total, 4),
        "bens_e_direitos": round(sum(f["bens"] for f in faixas), 2),
        "celulas_suprimidas": suprimidas,
        "faixas": faixas, "natureza_ocupacao": natureza, "ocupacoes": ocupacoes,
        "subsidio_deputado": sub,
    }


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers=UA, timeout=600, follow_redirects=True) as c:
        conteudo, edicao, ano, url = planilha(c)
        dados = montar(conteudo, c, edicao, ano, url)
    out = PUB / "irpf.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    topo = dados["faixas"][-1]
    log.info("ano-calendário %d: %.1f mi de declarantes, renda R$ %.3f tri, imposto devido R$ %.1f bi (alíquota média %.1f%%); "
             "topo: %d contribuintes, %.1f%% de alíquota e %.1f%% de renda isenta; %d células suprimidas",
             ano, dados["declarantes"] / 1e6, dados["renda_total"] / 1e12, dados["imposto_devido_total"] / 1e9,
             100 * dados["aliquota_media"], topo["contribuintes"], 100 * topo["aliquota_efetiva"],
             100 * topo["pct_isenta"], dados["celulas_suprimidas"])
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
