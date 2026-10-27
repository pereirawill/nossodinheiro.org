"""
Trabalho e empresas — quantos trabalham, com carteira ou não, por conta própria, empregadores, servidores, desempregados;
quantas empresas e MEIs existem; quantos benefícios o INSS paga. Tudo de fontes oficiais, sem chave.

    python -m etl.trabalho.extract            # gera data/public/trabalho.json

Fontes:
- IBGE, PNAD Contínua trimestral, API SIDRA (`apisidra.ibge.gov.br`):
    tabela 6318 (pessoas de 14+ por condição na força de trabalho: total, força de trabalho, ocupada, desocupada, fora),
    tabela 4097 (ocupados por posição na ocupação: empregado privado com/sem carteira, doméstico, setor público, militar/
    estatutário, empregador, conta própria, familiar auxiliar), tabela 6381 (taxa de desocupação). Valores em mil pessoas.
- IBGE, Cadastro Central de Empresas (CEMPRE), tabela 7528 do SIDRA: quantas empresas há em cada faixa de pessoal ocupado
  (de 0 a 4 até 500 ou mais), quanta gente trabalha em cada faixa e o salário médio mensal de cada uma. É anual, com ~2 anos de
  defasagem, e conta empresas formais (CNPJ) e outras organizações, inclusive administração pública e entidades sem fins lucrativos.
- Governo federal (MEMP/DREI), Mapa de Empresas, planilha mensal aberta (gov.br/memp): empresas ativas por natureza jurídica
  e porte (MEI, microempresa, EPP, demais), última edição publicada.
- Ministério da Previdência, Boletim Estatístico da Previdência Social (BEPS), tabela 14 (benefícios emitidos por grandes
  grupos: RGPS, assistencial/BPC, benefícios de legislação especial), última edição (.xls).

Saída: data/public/trabalho.json — {gerado_em_utc, pnad:{periodo, mil:{...}}, empresas:{referencia, ativas, mei, ...},
inss:{mes, total, rgps, assistencial, ble}, pendentes:[...]}.
"""

from __future__ import annotations

import io
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx

log = logging.getLogger("etl.trabalho")
PUB = Path("data/public")
UA = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
SIDRA = "https://apisidra.ibge.gov.br/values/t/{t}/n1/all/v/{v}/p/last%201{extra}?formato=json"
SIDRA_POP = "https://apisidra.ibge.gov.br/values/t/6579/n1/all/v/9324/p/last%201?formato=json"  # população total estimada
# CEMPRE (Cadastro Central de Empresas), tabela 7528: empresas, pessoal ocupado e salário médio por faixa de pessoal ocupado
SIDRA_CEMPRE = "https://apisidra.ibge.gov.br/values/t/7528/n1/all/v/{v}/p/last%201/c319/all/c12762/0/c2703/0?formato=json"
MEMP = "https://www.gov.br/memp/pt-br/acesso-a-informacao/dados-abertos/repositorio-de-dados-abertos"
BEPS = "https://www.gov.br/previdencia/pt-br/assuntos/previdencia-social/Dados-estatisticos-previdencia-social-e-inss/boletins-da-previdencia-social"

CHAVES_4097 = {
    "Total": "ocupados",
    "Empregado no setor privado, exclusive trabalhador doméstico - com carteira de trabalho assinada": "privado_com_carteira",
    "Empregado no setor privado, exclusive trabalhador doméstico - sem carteira de trabalho assinada": "privado_sem_carteira",
    "Trabalhador doméstico - com carteira de trabalho assinada": "domestico_com_carteira",
    "Trabalhador doméstico - sem carteira de trabalho assinada": "domestico_sem_carteira",
    "Empregado no setor público": "setor_publico",
    "Empregado no setor público - militar e funcionário público estatutário": "publico_estatutario_militar",
    "Empregador": "empregador",
    "Conta própria": "conta_propria",
    "Trabalhador familiar auxiliar": "familiar_auxiliar",
}
CHAVES_6318 = {"Total": "pop_14_mais", "Força de trabalho": "forca_trabalho", "Força de trabalho - ocupada": "ocupada", "Força de trabalho - desocupada": "desocupada", "Fora da força de trabalho": "fora_forca"}


def populacao_total(c: httpx.Client) -> dict:
    """População total estimada pelo IBGE — a PNAD só conta quem tem 14 anos ou mais."""
    r = c.get(SIDRA_POP).json()[1]
    return {"ano": r["D3N"], "pessoas": int(r["V"])}


def cempre(c: httpx.Client) -> dict:
    """Quantas empresas há em cada faixa de tamanho e quanta gente trabalha em cada uma (IBGE, CEMPRE, tabela 7528)."""
    faixas: dict[str, dict] = {}
    ano = None
    for chave, var in (("empresas", 2585), ("pessoas", 707), ("assalariados", 708), ("salario_medio", 10143)):
        for r in c.get(SIDRA_CEMPRE.format(v=var)).json()[1:]:
            faixa, valor = r["D4N"].strip(), r["V"]
            ano = r["D3N"]
            try:
                faixas.setdefault(faixa, {"faixa": faixa})[chave] = float(valor)
            except (TypeError, ValueError):
                faixas.setdefault(faixa, {"faixa": faixa})[chave] = None
    ordem = ["0 a 4", "5 a 9", "10 a 19", "20 a 29", "30 a 49", "50 a 99", "100 a 249", "250 a 499", "500 ou mais"]
    total = faixas.get("Total", {})
    return {"ano": ano, "total": total, "faixas": [faixas[f] for f in ordem if f in faixas],
            "fonte": "IBGE, Cadastro Central de Empresas (CEMPRE), tabela 7528 do SIDRA"}


def pnad(c: httpx.Client) -> dict:
    out: dict = {"mil": {}}
    d = c.get(SIDRA.format(t=4097, v=4090, extra="/c11913/all")).json()
    for r in d[1:]:
        k = CHAVES_4097.get(r["D4N"].strip())
        if k:
            out["mil"][k] = float(r["V"]); out["periodo"] = r["D3N"]
    d = c.get(SIDRA.format(t=6318, v=1641, extra="/c629/all")).json()
    for r in d[1:]:
        k = CHAVES_6318.get(r["D4N"].strip())
        if k:
            out["mil"][k] = float(r["V"]); out["periodo_movel"] = r["D3N"]
    d = c.get(SIDRA.format(t=6381, v=4099, extra="")).json()
    out["taxa_desocupacao"] = float(d[1]["V"])
    out["fonte"] = "IBGE, PNAD Contínua (tabelas SIDRA 4097, 6318, 6381)"
    return out


def _xlsx_rows(conteudo: bytes, sheet: str) -> list[list]:
    from ..rankings.extract import _xlsx_rows as rows
    return rows(conteudo, sheet)


def mapa_empresas(c: httpx.Client) -> dict:
    html = c.get(MEMP).text
    links = re.findall(r'href="([^"]+mapa-de-empresas[^"]*\.xlsx[^"]*)"', html, flags=re.I)
    if not links:
        raise RuntimeError("Mapa de Empresas: nenhum xlsx no repositório")
    # nomes: 08_arquivodados_ago26-mapa-de-empresas.xlsx → ordena pelo prefixo numérico e ano
    def chave(u: str):
        m = re.search(r"(\d{2})_arquivodados_([a-z]{3})(\d{2})", u)
        return (int(m.group(3)), int(m.group(1))) if m else (0, 0)
    url = sorted(links, key=chave)[-1]
    if url.startswith("/"):
        url = "https://www.gov.br" + url
    xlsx = c.get(url).content
    linhas = _xlsx_rows(xlsx, "xl/worksheets/sheet3.xml")
    cab = linhas[0]; i_nj, i_porte, i_qt = cab.index("Natureza Jurídica"), cab.index("Porte da Empresa"), cab.index("Empresas Ativas")
    tot = mei = me_epp = 0.0
    por_nj: dict[str, float] = {}
    for l in linhas[1:]:
        if len(l) <= i_qt or not isinstance(l[i_qt], float):
            continue
        nj, porte, q = str(l[i_nj]), str(l[i_porte]), l[i_qt]
        tot += q; por_nj[nj] = por_nj.get(nj, 0) + q
        if "(MEI)" in nj:
            mei += q
        elif porte.startswith(("Microempresa", "Empresa de pequeno porte")):
            me_epp += q
    ref = re.search(r"arquivodados_([a-z]{3}\d{2})", url)
    return {"fonte": "Governo federal (MEMP/DREI), Mapa de Empresas — dados abertos", "url": url, "referencia": ref.group(1) if ref else None,
            "ativas": tot, "mei": mei, "micro_e_pequenas_nao_mei": me_epp, "demais": tot - mei - me_epp,
            "por_natureza": sorted(({"natureza": k, "ativas": v} for k, v in por_nj.items()), key=lambda x: -x["ativas"])[:8]}


def beps(c: httpx.Client) -> dict:
    import xlrd
    html = c.get(BEPS).text
    links = sorted(set(re.findall(r'href="([^"]+beps\d{6}_final\.xlsx?)"', html, flags=re.I)))
    if not links:
        raise RuntimeError("BEPS: nenhum xls no portal")
    url = sorted(links, key=lambda u: re.search(r"beps(\d{2})(\d{4})", u).group(2) + re.search(r"beps(\d{2})(\d{4})", u).group(1))[-1]
    if url.startswith("/"):
        url = "https://www.gov.br" + url
    wb = xlrd.open_workbook(file_contents=c.get(url).content)
    sh = wb.sheet_by_name("14")
    ult, ano = None, None
    MESES = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro")
    for r in range(sh.nrows):
        row = [sh.cell_value(r, cc) for cc in range(sh.ncols)]
        a0 = str(row[0]).strip().replace(".0", "")
        if a0.isdigit() and int(a0) >= 2000:
            ano = int(a0)                           # o ano só aparece na primeira linha de cada bloco (número até 2015, texto depois)
        nums = [v for v in row[2:] if isinstance(v, float)]          # células mescladas deslocam as colunas
        if ano and isinstance(row[1], str) and row[1].strip().lower() in MESES and len(nums) >= 3 and nums[0] > 0:
            ult = [float(ano), row[1]] + nums
    if not ult:
        raise RuntimeError("BEPS tabela 14: linha de dados não encontrada")
    m = re.search(r"beps(\d{2})(\d{4})", url)
    return {"fonte": "Ministério da Previdência, Boletim Estatístico da Previdência Social (tabela 14, benefícios emitidos)", "url": url,
            "edicao": f"{m.group(2)}-{m.group(1)}" if m else None, "ano": int(ult[0]), "mes": str(ult[1]).strip(),
            "total": float(ult[2]), "rgps": float(ult[3]), "assistencial": float(ult[4]), "ble": float(ult[5]) if len(ult) > 5 else None}


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers=UA, timeout=180, follow_redirects=True) as c:
        dados = {"gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"), "populacao": populacao_total(c),
                 "pnad": pnad(c), "empresas": mapa_empresas(c), "cempre": cempre(c), "inss": beps(c),
                 "pendentes": ["Bolsa Família (famílias e valor por mês): API do Portal da Transparência por município, ainda não carregada",
                               "Optantes do Simples Nacional (ME/EPP): sem arquivo aberto localizado na Receita; o Mapa de Empresas traz o porte, não a opção"]}
    for k, mn in (("ocupados", 50_000), ("pop_14_mais", 100_000)):
        if dados["pnad"]["mil"].get(k, 0) < mn:
            raise SystemExit(f"PNAD {k} = {dados['pnad']['mil'].get(k)} mil: fonte mudou?")
    if dados["empresas"]["ativas"] < 10e6 or dados["inss"]["total"] < 30e6:
        raise SystemExit("Mapa de Empresas ou BEPS fora da ordem de grandeza esperada")
    out = PUB / "trabalho.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    p, e, i = dados["pnad"]["mil"], dados["empresas"], dados["inss"]
    log.info("PNAD %s: ocupados %.1f mi (carteira privada %.1f, sem carteira %.1f, conta própria %.1f, público %.1f), desocupados %.1f mi (%.1f%%)",
             dados["pnad"]["periodo"], p["ocupados"] / 1e3, p["privado_com_carteira"] / 1e3, p["privado_sem_carteira"] / 1e3, p["conta_propria"] / 1e3, p["setor_publico"] / 1e3, p["desocupada"] / 1e3, dados["pnad"]["taxa_desocupacao"])
    log.info("Empresas %s: %.1f mi ativas, %.1f mi MEI | INSS %s/%s: %.1f mi benefícios (RGPS %.1f, BPC %.1f)", e["referencia"], e["ativas"] / 1e6, e["mei"] / 1e6, i["mes"], i["ano"], i["total"] / 1e6, i["rgps"] / 1e6, i["assistencial"] / 1e6)
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
