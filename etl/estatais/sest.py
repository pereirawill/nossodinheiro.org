"""
Estatais federais — lucro ou prejuízo agregado pelo microdado da SEST (Secretaria de Coordenação e Governança das
Empresas Estatais, Ministério da Gestão).

Duas fontes, as duas em ZIP no gov.br (sem chave, mas o servidor exige user-agent de navegador e Referer):
- `.../assuntos/estatais/transparencia/sestidentificacao.zip` — quem são as estatais federais: 117 ativas, com
  `controle_acionario` (direto ou indireto), `dependencia` (dependente ou não do Tesouro), setor e CNPJ; mais as
  inativas, com a data em que saíram.
- `.../assuntos/estatais/transparencia/sestdadosfinanceiros.zip` — demonstrações de cada uma, linha a linha
  (`exercicio;periodicidade;codigo_siest;empresa;demonstrativo;rubrica_codigo;rubrica_nome;valor`), em R$ 1,00.

O agregado soma só as **empresas de controle direto** (44 ativas), que é o universo que o Ministério da Gestão usa
quando divulga "o lucro das estatais federais": as de controle indireto são subsidiárias, e o lucro delas já está no
consolidado da mãe. Três armadilhas do arquivo, todas tratadas aqui:
- a conta do lucro líquido tem **dois códigos** (`500000` no plano antigo, `290000000` no atual);
- o mesmo código `500000` aparece em outros demonstrativos, então é obrigatório filtrar `demonstrativo == "DRE"`;
- os **grupos econômicos** ("GR. PETROBRAS") vêm junto com as empresas e precisam ser excluídos, senão o lucro conta
  duas vezes; e o ano corrente não tem linha `Anual` — vem no `4º Trimestre`, que é acumulado no ano.

Empresa que saiu do grupo (a Eletrobras saiu em 17/06/2022) fica no arquivo de inativas. Por isso o JSON traz duas
somas: `agregado` só com as 44 de hoje e `agregado_com_inativas` incluindo quem era estatal naquele ano — em 2016 a
diferença inverte o sinal (de −1,4 bi para +2,0 bi), quase tudo Eletrobras.
"""

from __future__ import annotations

import csv
import io
import logging
import zipfile
from collections import defaultdict
from pathlib import Path

import httpx

log = logging.getLogger("etl.estatais.sest")
RAW = Path("data/raw")
BASE = "https://www.gov.br/gestao/pt-br/assuntos/estatais/transparencia/{arquivo}.zip"
REFERER = "https://www.gov.br/gestao/pt-br/assuntos/estatais/transparencia"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/131.0.0.0 Safari/537.36")
CONTAS_LUCRO = {"500000", "290000000"}   # plano antigo e plano atual
# Divulgação oficial, para conferência (nota do Ministério da Gestão de 02/07/2026).
OFICIAL = {
    "2025": 169.4e9,
    "2024": 116.5e9,
    "url": "https://www.gov.br/gestao/pt-br/assuntos/noticias/2026/julho/"
           "estatais-federais-lucram-r-169-4-bilhoes-em-2025-aumento-de-45-sobre-2024",
    "nota": "nota do Ministério da Gestão de 02/07/2026, sobre as 44 empresas de controle direto",
}


def _num(v: str) -> float | None:
    v = (v or "").strip().replace(".", "").replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return None


def _zip(c: httpx.Client, arquivo: str) -> zipfile.ZipFile | None:
    destino = RAW / f"{arquivo}.zip"
    if not (destino.exists() and destino.stat().st_size > 50_000):
        r = c.get(BASE.format(arquivo=arquivo), headers={"User-Agent": UA, "Referer": REFERER})
        if r.status_code != 200 or r.content[:2] != b"PK":
            log.warning("SEST %s não baixou (HTTP %s)", arquivo, r.status_code)
            return None
        RAW.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(r.content)
    return zipfile.ZipFile(destino)


def _csv(zf: zipfile.ZipFile, pedaco: str) -> list[dict]:
    nomes = [n for n in zf.namelist() if pedaco in n and n.endswith(".csv")]
    if not nomes:
        return []
    return list(csv.DictReader(io.StringIO(zf.read(nomes[0]).decode("latin-1")), delimiter=";"))


def coletar(c: httpx.Client) -> dict:
    ident = _zip(c, "sestidentificacao")
    fin = _zip(c, "sestdadosfinanceiros")
    if not ident or not fin:
        return {}
    with ident:
        ativas = _csv(ident, "empresas-ativas")
        inativas = _csv(ident, "empresas-inativas")
        grupos = {x["codigo_siest"] for x in _csv(ident, "grupos")}
    with fin:
        linhas = _csv(fin, "dadosfinanceiros-demonstracoes")
    if not ativas or not linhas:
        return {}

    diretas = {x["codigo_siest"]: x for x in ativas if x["controle_acionario"] == "Controle direto"}
    saiu = {x["codigo_siest"]: x for x in inativas if x.get("controle_acionario") == "Controle direto"}

    # lucro por ano e empresa; o ano sem linha "Anual" (o corrente) vem do 4º trimestre, que é acumulado
    bruto: dict[str, dict[str, dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
    for x in linhas:
        if x["demonstrativo"] != "DRE" or x["rubrica_codigo"] not in CONTAS_LUCRO or x["codigo_siest"] in grupos:
            continue
        valor = _num(x["valor"])
        if valor is None:
            continue
        bruto[x["exercicio"]][x["periodicidade"]][x["codigo_siest"]] = valor

    anos = sorted(bruto)
    por_ano, periodicidade = {}, {}
    for a in anos:
        if bruto[a].get("Anual"):
            por_ano[a], periodicidade[a] = bruto[a]["Anual"], "exercício fechado"
        elif bruto[a].get("4º Trimestre"):
            por_ano[a], periodicidade[a] = bruto[a]["4º Trimestre"], "4º trimestre, acumulado no ano"
        else:
            ultimo = max(bruto[a], key=lambda p: ("1º", "2º", "3º", "4º").index(p[:2]) if p[:2] in
                         ("1º", "2º", "3º", "4º") else -1)
            por_ano[a], periodicidade[a] = bruto[a][ultimo], f"{ultimo.lower()}, acumulado no ano"

    agregado = {a: round(sum(v for cod, v in por_ano[a].items() if cod in diretas), 2) for a in anos}
    com_inativas = {a: round(sum(v for cod, v in por_ano[a].items() if cod in diretas or cod in saiu), 2)
                    for a in anos}
    quantas = {a: sum(1 for cod in por_ano[a] if cod in diretas) for a in anos}
    quantas_fora = {a: sum(1 for cod in por_ano[a] if cod in saiu) for a in anos}

    def ficha(cod: str, reg: dict, ativa: bool) -> dict:
        serie = {a: round(por_ano[a][cod], 2) for a in anos if cod in por_ano[a]}
        return {"sigla": reg.get("sigla", ""), "nome": reg.get("nome", ""), "setor": reg.get("setor", ""),
                "segmento": reg.get("segmento", ""), "dependente": reg.get("dependencia", "").startswith("Dependente"),
                "capital": reg.get("capital_aberto_fechado", ""), "cnpj": reg.get("cnpj", ""),
                "ministerio": reg.get("ministerio_supervisor", ""), "ativa": ativa,
                "saiu_em": reg.get("data_inativacao") or None, "serie": serie,
                "ultimo_ano": max(serie) if serie else None,
                "ultimo_lucro": serie[max(serie)] if serie else None}

    empresas = [ficha(cod, reg, True) for cod, reg in diretas.items()]
    empresas += [ficha(cod, reg, False) for cod, reg in saiu.items()]
    empresas = [e for e in empresas if e["serie"]]
    empresas.sort(key=lambda e: -(e["ultimo_lucro"] or 0))

    dependentes = sorted((e for e in empresas if e["dependente"]), key=lambda e: e["ultimo_lucro"] or 0)
    ult = anos[-1]
    log.info("SEST %s–%s: %d empresas de controle direto no último ano; lucro %s = R$ %.1f bi (%s)",
             anos[0], ult, quantas[ult], ult, agregado[ult] / 1e9, periodicidade[ult])
    return {
        "anos": anos, "agregado": agregado, "agregado_com_inativas": com_inativas,
        "empresas_no_agregado": quantas, "empresas_que_sairam": quantas_fora,
        "periodicidade": periodicidade, "empresas": empresas,
        "dependentes_do_tesouro": [e["sigla"] for e in dependentes],
        "total_ativas": len(ativas), "controle_direto": len(diretas),
        "controle_indireto": sum(1 for x in ativas if x["controle_acionario"] == "Controle indireto"),
        "total_dependentes": sum(1 for x in ativas if x["dependencia"].startswith("Dependente")),
        "oficial": OFICIAL,
        "fonte": "Ministério da Gestão, SEST, dados abertos: identificação das estatais federais e demonstrações "
                 "financeiras (lucro ou prejuízo líquido da DRE das empresas de controle direto)",
        "url": "https://dados.gov.br/dados/conjuntos-dados/empresas-estatais-federais---dados-financeiros",
    }
