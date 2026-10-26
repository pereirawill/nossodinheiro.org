"""
CNAE do fornecedor (atividade principal registrada na Receita Federal) para classificar o cartão corporativo por tipo
de serviço sem adivinhar pelo nome. Consulta pública por CNPJ (BrasilAPI, com minhareceita.org de reserva), com cache
versionado em data/cnae_cache.json (poucas centenas de CNPJs; dado público cadastral, sem pessoa física).

    from etl.presidencia.cnae import cnae_de, categoria_de
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

import httpx

log = logging.getLogger("etl.presidencia.cnae")
CACHE = Path("data/cnae_cache.json")
FONTES = ["https://brasilapi.com.br/api/cnpj/v1/{cnpj}", "https://minhareceita.org/{cnpj}"]

# Divisão (2 dígitos) ou classe (4 dígitos) do CNAE → rótulo legível. Primeiro o mais específico.
CATEGORIAS = [
    (r"^4731", "Combustível (postos)"),
    (r"^4732", "Combustível (lubrificantes)"),
    (r"^55", "Hospedagem"),
    (r"^56", "Alimentação (restaurantes, lanchonetes)"),
    (r"^51", "Transporte aéreo"),
    (r"^49", "Transporte terrestre (táxi, ônibus, locação com motorista)"),
    (r"^77", "Aluguel de veículos e equipamentos"),
    (r"^45", "Veículos: peças e manutenção"),
    (r"^(62|63|61)", "Tecnologia e telecomunicações"),
    (r"^4751", "Informática (lojas)"),
    (r"^(4771|4772|8[6-9]|21)", "Saúde e farmácia"),
    (r"^(4741|4744|4742|4743)", "Material de construção e tintas"),
    (r"^(4761|4789|4759|4763|4762|4753|4754|4755|4756|4757|4781|4782|4783|4784|4785)", "Lojas e material diverso"),
    (r"^(471|4711|4712|4721|4722|4723|4724|4729)", "Supermercados e alimentos"),
    (r"^(73|59|18|58)", "Comunicação, gráfica e publicidade"),
    (r"^95", "Reparos e manutenção"),
    (r"^(80|81)", "Segurança e serviços prediais"),
    (r"^(68|41|42|43)", "Imóveis e obras"),
    (r"^(69|70|71|72|74|78|82)", "Serviços profissionais e administrativos"),
    (r"^(90|91|92|93)", "Cultura, esporte e lazer"),
    (r"^(46)", "Atacado"),
    (r"^(10|11|12|13|14|15|16|17|19|20|22|23|24|25|26|27|28|29|30|31|32|33)", "Indústria"),
    (r"^(64|65|66)", "Serviços financeiros"),
    (r"^(84)", "Administração pública"),
]


def _carregar() -> dict:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    except json.JSONDecodeError:
        return {}


def cnae_de(cnpjs: list[str]) -> dict[str, dict]:
    """cnpj (14 dígitos) → {cnae, descricao, razao_social}. Consulta só o que não está no cache."""
    cache = _carregar()
    faltam = [c for c in dict.fromkeys(cnpjs) if c not in cache]
    if faltam:
        log.info("CNAE: %d CNPJs em cache, %d a consultar", len(cache), len(faltam))
        with httpx.Client(timeout=30, headers={"user-agent": "nossodinheiro-etl/0.1 (+https://nossodinheiro.org)"}) as c:
            for i, cnpj in enumerate(faltam, 1):
                for url in FONTES:
                    try:
                        r = c.get(url.format(cnpj=cnpj))
                        if r.status_code == 200:
                            d = r.json()
                            cache[cnpj] = {"cnae": str(d.get("cnae_fiscal") or ""), "descricao": d.get("cnae_fiscal_descricao") or "", "razao_social": d.get("razao_social") or ""}
                            break
                        if r.status_code == 404:
                            cache[cnpj] = {"cnae": "", "descricao": "", "razao_social": ""}; break
                    except httpx.HTTPError as e:
                        log.warning("CNAE %s em %s: %s", cnpj, url, e)
                else:
                    cache.setdefault(cnpj, {"cnae": "", "descricao": "", "razao_social": ""})
                time.sleep(0.4)
                if i % 25 == 0:
                    CACHE.parent.mkdir(parents=True, exist_ok=True); CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
    return {c: cache[c] for c in cnpjs if c in cache}


def categoria_de(cnae: str) -> str:
    d = re.sub(r"\D", "", cnae or "")
    if not d:
        return "Sem CNAE identificado"
    for padrao, rotulo in CATEGORIAS:
        if re.match(padrao, d):
            return rotulo
    return "Outros serviços"
