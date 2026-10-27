"""
Previdência — o que o INSS paga, por tipo de benefício e por estado, e a série desde 2000.

    python -m etl.previdencia.extract            # gera data/public/previdencia.json

Fonte: Ministério da Previdência Social, **Boletim Estatístico da Previdência Social (BEPS)**, última edição (.xls), abas:
- **15**: benefícios emitidos no mês por grupo e espécie — quantidade, valor pago e valor médio. É daqui que sai a divisão entre
  aposentadorias (idade, invalidez, tempo de contribuição), pensões por morte, auxílios, salário-maternidade, os acidentários,
  o BPC/LOAS (idoso e pessoa com deficiência) e as rendas mensais vitalícias.
- **19**: benefícios do RGPS por estado — quantidade, valor e valor médio, com a divisão entre clientela urbana e rural.
- **13**: evolução mensal da quantidade de benefícios emitidos desde 2000 (dezembro de cada ano e o último mês publicado).

O que o INSS paga é o **RGPS**, o regime de quem contribui como empregado, autônomo ou contribuinte individual, mais o **BPC**,
que é assistência social (não exige contribuição). Servidores públicos têm regime próprio (RPPS), que não está no BEPS: o dinheiro
do RPPS aparece no painel de Aposentadoria, vindo do orçamento da União (SIOP) e das contas de estados (SICONFI).
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import httpx
import xlrd

from etl.ufs import NOME_PARA_UF

log = logging.getLogger("etl.previdencia")
PUB = Path("data/public")
BEPS = "https://www.gov.br/previdencia/pt-br/assuntos/previdencia-social/Dados-estatisticos-previdencia-social-e-inss/boletins-da-previdencia-social"
UA = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
MESES = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro")

# Aba 15: nome como vem na planilha → (chave, nível na hierarquia, rótulo em português claro).
# Nível 0 = total, 1 = grande grupo, 2 = subgrupo, 3 = espécie.
GRUPOS_15 = {
    "TOTAL": ("total", 0, "Todos os benefícios do INSS"),
    "BENEFÍCIOS DO RGPS": ("rgps", 1, "Quem contribuiu (RGPS)"),
    "Previdenciários": ("previdenciarios", 2, "Previdenciários"),
    "Aposentadorias": ("aposentadorias", 3, "Aposentadorias"),
    "Idade": ("aposentadoria_idade", 4, "por idade"),
    "Invalidez": ("aposentadoria_invalidez", 4, "por invalidez"),
    "Tempo de Contribuição": ("aposentadoria_tempo", 4, "por tempo de contribuição"),
    "Pensões por Morte": ("pensoes", 3, "Pensões por morte"),
    "Auxílios": ("auxilios", 3, "Auxílios"),
    "Doença": ("auxilio_doenca", 4, "auxílio por incapacidade (doença)"),
    "Acidente": ("auxilio_acidente", 4, "auxílio-acidente"),
    "Reclusão": ("auxilio_reclusao", 4, "auxílio-reclusão"),
    "Salário-Maternidade": ("salario_maternidade", 3, "Salário-maternidade"),
    "Acidentários": ("acidentarios", 2, "Acidentários (acidente de trabalho)"),
    "BENEFÍCIOS ASSISTENCIAIS": ("assistenciais", 1, "Assistência social, sem contribuição (BPC/LOAS)"),
    "Amparos Assistenciais (LOAS)": ("bpc", 2, "BPC: um salário mínimo"),
    "Idoso": ("bpc_idoso", 3, "a idosos de 65 anos ou mais"),
    "Portador de Deficiência": ("bpc_deficiencia", 3, "a pessoas com deficiência"),
    "Rendas Mensais Vitalícias": ("rmv", 2, "Rendas mensais vitalícias (extintas em 1995)"),
    "BENEFÍCIOS DE LEGISLAÇÃO ESPECÍFICA": ("legislacao_especial", 1, "Legislação específica (anistiados, hanseníase, talidomida)"),
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s).strip().upper()


def baixar(c: httpx.Client) -> tuple[bytes, str]:
    html = c.get(BEPS).text
    links = sorted(set(re.findall(r'href="([^"]+beps(\d{2})(\d{4})_final\.xlsx?)"', html, flags=re.I)))
    if not links:
        raise SystemExit("nenhum BEPS encontrado na página do Ministério da Previdência")
    url, mes, ano = sorted(links, key=lambda t: t[2] + t[1])[-1]
    if url.startswith("/"):
        url = "https://www.gov.br" + url
    log.info("BEPS %s/%s: %s", mes, ano, url.rsplit("/", 1)[-1])
    return c.get(url).content, f"{ano}-{mes}"


def por_especie(wb) -> list[dict]:
    """Aba 15: quantidade (col 4), valor (col 12) e valor médio (col 20) por grupo de espécies."""
    sh = wb.sheet_by_name("15")
    chaves = {re.sub(r"\s*\(.*$", "", _norm(k)).strip(): v for k, v in GRUPOS_15.items()}
    out = []
    for r in range(sh.nrows):
        # a planilha põe notas de rodapé no próprio rótulo ("… (BLE) (3)"); cortamos antes de casar
        nome = re.sub(r"\s*\(.*$", "", _norm(sh.cell_value(r, 0))).strip()
        alvo = chaves.get(nome)
        if not alvo:
            continue
        qtd, valor, medio = (sh.cell_value(r, c) for c in (4, 12, 20))
        if not isinstance(qtd, float) or qtd <= 0:
            continue
        chave, nivel, rotulo = alvo
        if any(o["chave"] == chave for o in out):        # "Idade" e "Invalidez" se repetem nas rendas vitalícias
            continue
        out.append({"chave": chave, "nivel": nivel, "nome": rotulo, "quantidade": int(qtd),
                    "valor": round(float(valor or 0), 2), "valor_medio": round(float(medio or 0), 2)})
    return out


def por_uf(wb) -> list[dict]:
    """Aba 19: benefícios do RGPS por estado — quantidade (col 4), valor (col 11), médio (col 18) e clientela rural (col 9)."""
    sh = wb.sheet_by_name("19")
    out = []
    for r in range(sh.nrows):
        bruto = str(sh.cell_value(r, 0))
        nome = bruto.strip()
        uf = NOME_PARA_UF.get(nome)
        if not uf or not bruto.startswith(" "):           # UFs vêm indentadas; regiões e BRASIL, não
            continue
        qtd, valor, medio, rural = (sh.cell_value(r, c) for c in (4, 11, 18, 9))
        out.append({"uf": uf, "nome": nome, "quantidade": int(qtd or 0), "valor": round(float(valor or 0), 2),
                    "valor_medio": round(float(medio or 0), 2), "pct_rural": round(float(rural or 0), 1)})
    return out


def serie(wb) -> list[dict]:
    """Aba 13: quantidade de benefícios emitidos — dezembro de cada ano e o último mês publicado."""
    sh = wb.sheet_by_name("13")
    ano, linhas = None, []
    for r in range(sh.nrows):
        a0 = str(sh.cell_value(r, 0)).strip().replace(".0", "")
        if a0.isdigit() and 1990 <= int(a0) <= datetime.now().year:
            ano = int(a0)
        mes = str(sh.cell_value(r, 1)).strip().lower()
        qtd = sh.cell_value(r, 4)
        if ano and mes in MESES and isinstance(qtd, float) and qtd > 0:
            linhas.append({"ano": ano, "mes": mes, "quantidade": int(qtd)})
    por_ano: dict[int, dict] = {}
    for l in linhas:
        if l["mes"] == "dezembro" or l["ano"] not in por_ano or por_ano[l["ano"]]["mes"] != "dezembro":
            por_ano[l["ano"]] = l
    return [por_ano[a] for a in sorted(por_ano)]


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers=UA, timeout=600, follow_redirects=True) as c:
        conteudo, competencia = baixar(c)
    wb = xlrd.open_workbook(file_contents=conteudo)
    especies, ufs, historico = por_especie(wb), por_uf(wb), serie(wb)
    total = next(e for e in especies if e["chave"] == "total")
    if total["quantidade"] < 30e6 or len(ufs) != 27:
        raise SystemExit(f"BEPS mudou de formato? total {total['quantidade']}, {len(ufs)} UFs")
    dados = {"gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"), "competencia": competencia,
             "especies": especies, "por_uf": ufs, "serie": historico,
             "fontes": {"beps": f"Ministério da Previdência Social, Boletim Estatístico da Previdência Social, competência {competencia} (abas 13, 15 e 19)"}}
    out = PUB / "previdencia.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    log.info("INSS %s: %.1f mi de benefícios, R$ %.1f bi no mês; %d espécies; %d UFs; série de %d anos", competencia,
             total["quantidade"] / 1e6, total["valor"] / 1e9, len(especies), len(ufs), len(historico))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
