"""
Tribunais superiores — custo por magistrado (ele mais o gabinete), no mesmo molde do painel do STF.

    python -m etl.tribunais.transform --tribunal tst --ano 2026

Entrada: `data/raw/folha_<sigla>_<ano>.jsonl.gz` (ver extract.py).
Saídas:  `data/public/custo_magistrado_<sigla>_<ano>.json` e `data/public/meta_<sigla>_<ano>.json`.

Regras (as mesmas do STF, para os números serem comparáveis):
- **Custo** = remuneração bruta do magistrado após o teto + a soma da mesma coluna de todas as pessoas lotadas no
  gabinete dele, **sem** contar o próprio magistrado.
- Quem está lotado como inativo não tem gabinete e entra como estatística separada (aposentados e pensionistas).
- Gabinetes institucionais (Presidência, Vice, Corregedoria) ficam de fora do custo por magistrado: quem ocupa o
  cargo acumula o próprio gabinete, e somar os dois contaria pessoal duas vezes. O JSON os lista em `gabinetes_institucionais`.
- A parcela paga pelo **órgão de origem** de requisitados não entra no custo do tribunal, mas vai no JSON.
- Ano corrente é parcial: `meses_com_folha` diz quantos meses entraram, e a projeção anual é média × 12, rotulada.
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import re
import unicodedata
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

from .fontes import TRIBUNAIS

log = logging.getLogger("etl.tribunais.transform")
RAW, PUB = Path("data/raw"), Path("data/public")
INSTITUCIONAIS = ("PRESIDÊNCIA", "PRESIDENCIA", "VICE-PRESIDÊNCIA", "VICE-PRESIDENCIA", "CORREGEDORIA", "OUVIDORIA",
                  "CONSELHO SUPERIOR", "ESCOLA NACIONAL", "ENAMAT")


def _norm(t: str) -> str:
    """Maiúsculas sem acento, para comparar nomes de lotação entre tribunais."""
    return "".join(c for c in unicodedata.normalize("NFD", (t or "").upper()) if unicodedata.category(c) != "Mn").strip()


def nome_curto(nome: str, lotacao: str) -> str:
    """'Gabinete do Ministro Alberto Bastos Balazeiro' → 'Bastos Balazeiro'; sem gabinete, dois últimos nomes."""
    base = lotacao
    for prefixo in ("GABINETE DO MINISTRO ", "GABINETE DA MINISTRA ", "GABINETE MINISTRO ", "GABINETE MINISTRA ",
                    "GABINETE DO DESEMBARGADOR CONVOCADO ", "GABINETE DA DESEMBARGADORA CONVOCADA ",
                    "GABINETE DO DESEMBARGADOR ", "GABINETE DA DESEMBARGADORA ", "GABINETE DO CONSELHEIRO ",
                    "GABINETE DA CONSELHEIRA ", "GABINETE DO JUIZ ", "GABINETE DA JUÍZA ",
                    "GABINETE DO MINISTRO CONVOCADO ", "GABINETE DA MINISTRA CONVOCADA ",
                    "GAB MIN ", "GAB. MIN. "):
        if lotacao.upper().startswith(prefixo):
            base = lotacao[len(prefixo):]
            break
    else:
        base = " ".join(nome.split()[-2:])
    particulas = ("de", "da", "do", "dos", "das", "e", "e.")
    return " ".join(p.lower() if p.lower() in particulas else p.capitalize() for p in base.split())


def institucional(lotacao: str) -> bool:
    return any(p in lotacao.upper() for p in INSTITUCIONAIS)


def run(sigla: str, ano: int) -> tuple[Path, Path]:
    t = TRIBUNAIS[sigla]
    bruto = RAW / f"folha_{sigla}_{ano}.jsonl.gz"
    if not bruto.exists():
        raise SystemExit(f"{bruto} não existe — rode `python -m etl.tribunais.extract --tribunal {sigla} --ano {ano}`")
    with gzip.open(bruto, "rt", encoding="utf-8") as f:
        linhas = [json.loads(l) for l in f]

    meses = sorted({l["mes"] for l in linhas})
    ultimo_mes = max(meses) if meses else 0
    cargos_mag = {c.upper() for c in t.cargos_do_magistrado}
    cargos_mag_inativo = cargos_mag | {c.upper() for c in t.cargos_do_magistrado_inativo}
    cargos_conv = {_norm(c) for c in t.cargos_do_magistrado_convocado}
    cargos_com_gabinete = cargos_mag | cargos_conv
    fora = {_norm(x) for x in t.lotacao_fora_de_exercicio}
    gabinete_re = re.compile(t.padrao_gabinete)

    def em_exercicio(linha: dict) -> bool:
        """Tem gabinete próprio: a lotação não é pseudo-unidade (inativo, cedido, exonerado) e parece um gabinete."""
        n = _norm(linha.get("lotacao", ""))
        if _norm(linha.get("situacao", "")) in fora:
            return False
        return bool(n) and n not in fora and bool(gabinete_re.search(n))

    # --- magistrados em exercício (têm gabinete) e aposentados ---------------------------------------------------
    mag: dict[str, dict] = {}
    por_mes: dict[int, set] = defaultdict(set)
    aposentados: dict[int, dict] = defaultdict(lambda: {"pessoas": set(), "bruto": 0.0})
    # Lotações chefiadas por um magistrado titular. Um magistrado CONVOCADO só ganha linha própria se o gabinete em
    # que está não tem titular: no STJ ele substitui um ministro afastado e chefia a equipe inteira; no TST ele é juiz
    # auxiliar DENTRO do gabinete de um ministro, e nesse caso entra como pessoal do gabinete, não como centro de custo.
    lotacoes_titulares = {l["lotacao"] for l in linhas
                          if _norm(l["cargo"]) in cargos_mag and em_exercicio(l)}

    def _acumular(l: dict, convocado: bool) -> None:
        # A grafia do nome varia de um mês para o outro em alguns tribunais; a matrícula, quando existe, é estável.
        chave = l.get("matricula") or l["nome"]
        m = mag.setdefault(chave, {"nome": l["nome"], "lotacao": l["lotacao"], "meses": set(),
                                   "bruto": 0.0, "liquido": 0.0, "indenizacoes": 0.0, "detalha_verbas": True,
                                   "convocado": convocado, "por_mes": {}})
        m["meses"].add(l["mes"]); m["bruto"] += l["bruto"]; m["liquido"] += l["liquido"]
        if l.get("indenizacoes") is None:
            m["detalha_verbas"] = False
        else:
            m["indenizacoes"] += l["indenizacoes"]
        m["por_mes"][l["mes"]] = m["por_mes"].get(l["mes"], 0.0) + l["bruto"]
        m["lotacao"] = l["lotacao"]; m["nome"] = l["nome"]
        if not convocado:
            por_mes[l["mes"]].add(chave)

    for l in linhas:
        cargo = _norm(l["cargo"])
        titular = cargo in cargos_mag
        convocado = cargo in cargos_conv
        if not titular and not convocado and cargo not in cargos_mag_inativo:
            continue
        if convocado:
            if em_exercicio(l) and l["lotacao"] not in lotacoes_titulares:
                _acumular(l, True)
            continue                      # dentro do gabinete de um titular: conta como pessoal, não como gabinete próprio
        if not titular or not em_exercicio(l):
            a = aposentados[l["mes"]]
            a["pessoas"].add(l.get("matricula") or l["nome"]); a["bruto"] += l["bruto"]
            continue
        _acumular(l, False)

    # --- folha de cada gabinete, sem o magistrado -----------------------------------------------------------------
    chaves_mag = set(mag)
    gab_total: dict[str, float] = defaultdict(float)
    gab_origem: dict[str, float] = defaultdict(float)
    gab_pessoas: dict[str, dict[int, set]] = defaultdict(lambda: defaultdict(set))
    gab_cargos: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    gab_mes_total: dict[str, dict[int, float]] = defaultdict(lambda: defaultdict(float))
    for l in linhas:
        lot = l["lotacao"]
        if not lot or _norm(lot) in fora or not gabinete_re.search(_norm(lot)):
            continue
        if (l.get("matricula") or l["nome"]) in chaves_mag:          # o próprio magistrado não entra no gabinete dele
            continue
        gab_total[lot] += l["bruto"]; gab_origem[lot] += l.get("origem_outro_orgao", 0.0)
        gab_mes_total[lot][l["mes"]] += l["bruto"]
        gab_pessoas[lot][l["mes"]].add(l["nome"])
        gab_cargos[lot][l["cargo"] or "sem cargo informado"] += 1

    saida = []
    for m in sorted(mag.values(), key=lambda x: nome_curto(x["nome"], x["lotacao"])):
        n = len(m["meses"]) or 1
        lot = m["lotacao"]
        pessoas_mes = [len(s) for s in gab_pessoas[lot].values()] or [0]
        gab = round(gab_total.get(lot, 0.0), 2)
        n_gab = len(gab_pessoas[lot]) or 1          # meses em que o gabinete teve folha
        gab_mes = round(gab / n_gab, 2)
        total_mes = round(m["bruto"] / n + gab_mes, 2)
        saida.append({
            "nome": m["nome"], "nome_curto": nome_curto(m["nome"], lot), "unidade": lot, "ano": ano,
            "meses_com_folha": len(m["meses"]),
            "remuneracao_bruta": round(m["bruto"], 2), "remuneracao_liquida": round(m["liquido"], 2),
            "indenizacoes": round(m["indenizacoes"], 2) if m["detalha_verbas"] else None,
            "remuneracao_mensal_media": round(m["bruto"] / n, 2),
            "gabinete": gab, "gabinete_mensal_medio": gab_mes, "gabinete_meses": n_gab,
            "gabinete_pessoas_media": round(sum(pessoas_mes) / len(pessoas_mes), 1),
            "gabinete_pessoas_ultimo_mes": len(gab_pessoas[lot].get(ultimo_mes, set())),
            "gabinete_composicao": {k: v for k, v in sorted(gab_cargos[lot].items(), key=lambda kv: -kv[1])},
            "gabinete_pago_por_outro_orgao": round(gab_origem.get(lot, 0.0), 2),
            "custo_total_estimado": round(m["bruto"] + gab, 2), "custo_mensal_medio": total_mes,
            "custo_anual_projetado": round(total_mes * 12, 2),
            "institucional": institucional(lot),
            "convocado": bool(m.get("convocado")),
            "no_ultimo_mes": ultimo_mes in m["meses"],
            "gabinete_no_ultimo_mes": bool(gab_pessoas[lot].get(ultimo_mes)),
            "remuneracao_ultimo_mes": round(m["por_mes"].get(ultimo_mes, 0.0), 2),
            "gabinete_ultimo_mes": round(gab_mes_total[lot].get(ultimo_mes, 0.0), 2),
            "custo_ultimo_mes": round(m["por_mes"].get(ultimo_mes, 0.0) + gab_mes_total[lot].get(ultimo_mes, 0.0), 2),
        })

    # Resumo do último mês publicado: base dos destaques da página, para não misturar períodos diferentes.
    titulares_um = [x for x in saida if not x["convocado"] and x["no_ultimo_mes"] and x["gabinete_no_ultimo_mes"]]
    resumo_ultimo = {
        "mes": ultimo_mes, "magistrados": len(titulares_um),
        "remuneracao": round(sum(x["remuneracao_ultimo_mes"] for x in titulares_um), 2),
        "gabinetes": round(sum(x["gabinete_ultimo_mes"] for x in titulares_um), 2),
        "custo_total": round(sum(x["custo_ultimo_mes"] for x in titulares_um), 2),
        "custo_medio": round(sum(x["custo_ultimo_mes"] for x in titulares_um) / max(len(titulares_um), 1), 2),
        "pessoas_nos_gabinetes": sum(x["gabinete_pessoas_ultimo_mes"] for x in titulares_um),
        "fora_do_resumo": [{"nome_curto": x["nome_curto"], "motivo": "sem folha no último mês" if not x["no_ultimo_mes"]
                            else "o gabinete não aparece com pessoal próprio no mês"}
                           for x in saida if not x["convocado"] and not (x["no_ultimo_mes"] and x["gabinete_no_ultimo_mes"])],
    }

    inst = [{"unidade": lot, "bruto": round(v, 2), "pessoas_ultimo_mes": len(gab_pessoas[lot].get(max(meses), set()))}
            for lot, v in sorted(gab_total.items(), key=lambda kv: -kv[1])
            if institucional(lot) and lot not in {s["unidade"] for s in saida}]

    ultimo = ultimo_mes
    ap_ultimo = aposentados.get(ultimo, {"pessoas": set(), "bruto": 0.0})
    meta = {
        "tribunal": t.sigla, "nome": t.nome, "rotulo_magistrado": t.rotulo_magistrado, "ano": ano,
        "meses_com_folha": meses, "ultimo_mes": ultimo,
        "magistrados_em_exercicio": len(por_mes.get(ultimo_mes, ())),
        "magistrados_no_ano": sum(1 for x in saida if not x["convocado"]),
        "convocados_no_ano": sum(1 for x in saida if x["convocado"]),
        "ultimo_mes_resumo": resumo_ultimo,
        "composicao_legal": t.composicao,
        "magistrados_por_mes": {str(m): len(v) for m, v in sorted(por_mes.items())},
        "gerado_em": date.today().isoformat(),
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "anual_e_projecao": True, "fonte": t.fonte, "url": t.url, "coluna_valor": t.coluna_valor,
        "observacao": t.observacao,
        "aposentados": {"quantidade_ultimo_mes": len(ap_ultimo["pessoas"]),
                        "bruto_ultimo_mes": round(ap_ultimo["bruto"], 2),
                        "bruto_acumulado": round(sum(a["bruto"] for a in aposentados.values()), 2)},
        "gabinetes_institucionais": inst,
        "detalha_verbas": all(x.get("indenizacoes") is not None for x in saida),
        "totais": {"remuneracao_bruta": round(sum(s["remuneracao_bruta"] for s in saida), 2),
                   "gabinetes": round(sum(s["gabinete"] for s in saida), 2),
                   "custo_total_estimado": round(sum(s["custo_total_estimado"] for s in saida), 2),
                   "folha_inteira": round(sum(l["bruto"] for l in linhas), 2),
                   "pessoas_ultimo_mes": len({l["nome"] for l in linhas if l["mes"] == ultimo})},
    }
    pico = max((len(v) for v in por_mes.values()), default=0)
    if t.composicao and pico > t.composicao:
        raise SystemExit(f"{t.sigla}: {pico} magistrados com gabinete em um mesmo mês, mais que a composição legal "
                         f"({t.composicao}) — a coluna Cargo ou a lotação mudaram?")
    if len(saida) > (t.composicao or 0) and t.composicao:
        log.info("%s: %d magistrados no ano para %d cargos — há troca no meio do ano (quem entrou ou saiu aparece com "
                 "menos meses em `meses_com_folha`)", t.sigla, len(saida), t.composicao)
    if not saida:
        raise SystemExit(f"{t.sigla}: nenhum magistrado em exercício identificado — a coluna Cargo mudou?")

    PUB.mkdir(parents=True, exist_ok=True)
    f1 = PUB / f"custo_magistrado_{sigla}_{ano}.json"
    f2 = PUB / f"meta_{sigla}_{ano}.json"
    f1.write_text(json.dumps(saida, ensure_ascii=False), encoding="utf-8")
    f2.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    media = meta["totais"]["custo_total_estimado"] / max(len(saida), 1) / max(len(meses), 1)
    log.info("%s %d: %d %ss no último mês (composição legal %s), %d meses; custo médio R$ %.0f/mês; "
             "folha inteira R$ %.1f mi; %d aposentados no último mês",
             t.sigla, ano, meta["magistrados_em_exercicio"], t.rotulo_magistrado, t.composicao, len(meses), media,
             meta["totais"]["folha_inteira"] / 1e6, meta["aposentados"]["quantidade_ultimo_mes"])
    return f1, f2


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tribunal", required=True, choices=sorted(TRIBUNAIS))
    ap.add_argument("--ano", type=int, required=True)
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run(a.tribunal, a.ano)


if __name__ == "__main__":
    main()
