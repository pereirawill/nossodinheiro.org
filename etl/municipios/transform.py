"""
Municípios e estados — agregação da despesa por função (SICONFI DCA) com população e vagas de vereador (TSE).

    python -m etl.municipios.transform --ano 2025 [--vagas 2024]

Entradas: data/raw/siconfi_dca_<ano>.jsonl.gz, data/raw/siconfi_entes.jsonl.gz, data/raw/tse_vagas_<vagas>.jsonl.gz
Saídas:   data/public/municipios_<ano>.json  — 1 linha por município com DCA: cod_ibge, nome, uf, capital, populacao, vereadores,
            pago_total, pago_legislativo, pago_saude, pago_educacao, pago_administracao, por_hab_total, por_hab_legislativo,
            por_vereador_legislativo, pct_legislativo, empenhado_total
          data/public/estados_<ano>.json     — 1 linha por estado/DF: funções principais (Legislativa, Judiciária, Essencial à Justiça,
            Administração, Segurança, Saúde, Educação, Previdência, Encargos) pagas, total, por habitante
          data/public/municipios_meta_<ano>.json — totais, cobertura (quantos municípios entregaram a DCA), medianas por faixa de população

Regras:
- Valor = DESPESA PAGA no exercício (coluna "Despesas Pagas" do anexo I-E); empenhado fica como coluna.
- "Custo da Câmara" = função 01 Legislativa da prefeitura (é a Câmara Municipal: vereadores, servidores, prédio). No DF e nos
  estados, 01 Legislativa = Assembleia/Câmara Legislativa + Tribunal de Contas.
- Vereadores = vagas da eleição de 2024 (TSE), casadas por UF + nome normalizado; municípios sem casamento ficam sem "por vereador".
- Cobertura: nem toda prefeitura entrega a DCA no prazo; o meta diz quantas há. Sem DCA = fora do ranking, não zero.
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import unicodedata
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

log = logging.getLogger("etl.municipios.transform")
RAW, PUB = Path("data/raw"), Path("data/public")
FUNCOES_ESTADO = {"01": "legislativa", "02": "judiciaria", "03": "essencial_justica", "04": "administracao", "06": "seguranca", "09": "previdencia",
                  "10": "saude", "12": "educacao", "17": "saneamento", "28": "encargos"}


def normalizar(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9 ]+", " ", s).strip()


def _ler(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(l) for l in f]


def faixa(pop: int | None) -> str:
    if not pop:
        return "sem população"
    for lim, rot in ((10_000, "até 10 mil"), (50_000, "10 a 50 mil"), (100_000, "50 a 100 mil"), (500_000, "100 a 500 mil")):
        if pop <= lim:
            return rot
    return "mais de 500 mil"


def run(ano: int, ano_vagas: int = 2024) -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    entes = {e["cod_ibge"]: e for e in _ler(RAW / "siconfi_entes.jsonl.gz")}
    dca = [l for l in _ler(RAW / f"siconfi_dca_{ano}.jsonl.gz") if "erro" not in l]
    vagas_path = RAW / f"tse_vagas_{ano_vagas}.jsonl.gz"
    vagas = {(v["uf"], v["municipio_norm"]): v["vagas"] for v in _ler(vagas_path)} if vagas_path.exists() else {}

    por_ente: dict[int, dict] = defaultdict(lambda: {"pago": defaultdict(float), "empenhado": defaultdict(float)})
    for l in dca:
        chave = "pago" if l["coluna"] == "Despesas Pagas" else "empenhado" if l["coluna"] == "Despesas Empenhadas" else None
        if chave:
            por_ente[l["cod_ibge"]][chave][l["funcao_cod"]] += l["valor"]
            por_ente[l["cod_ibge"]]["populacao"] = l.get("populacao") or entes.get(l["cod_ibge"], {}).get("populacao")

    # A lista de entes traz uf="BR" para estados; derivamos a UF pelo prefixo IBGE (2 dígitos) a partir dos municípios
    uf_por_prefixo = {str(e["cod_ibge"])[:2]: e["uf"] for e in entes.values() if e["esfera"] == "M"}
    municipios, estados = [], []
    for cod, d in por_ente.items():
        e = entes.get(cod)
        if not e:
            continue
        pop = d.get("populacao") or e.get("populacao")
        pago, emp = d["pago"], d["empenhado"]
        total = pago.get("00", 0.0) or sum(v for k, v in pago.items() if k != "00")
        if e["esfera"] == "M":
            leg = pago.get("01", 0.0)
            ver = vagas.get((e["uf"], normalizar(e["ente"])))
            municipios.append({
                "cod_ibge": cod, "nome": e["ente"], "uf": e["uf"], "capital": e.get("capital", False), "regiao": e.get("regiao"), "populacao": pop, "faixa": faixa(pop),
                "vereadores": ver, "pago_total": round(total, 2), "empenhado_total": round(emp.get("00", 0.0), 2),
                "pago_legislativo": round(leg, 2), "pago_saude": round(pago.get("10", 0.0), 2), "pago_educacao": round(pago.get("12", 0.0), 2),
                "pago_administracao": round(pago.get("04", 0.0), 2), "pago_saneamento": round(pago.get("17", 0.0), 2),
                "por_hab_total": round(total / pop, 2) if pop else None, "por_hab_legislativo": round(leg / pop, 2) if pop else None,
                "por_vereador_legislativo": round(leg / ver, 2) if ver else None, "pct_legislativo": round(leg / total, 4) if total else None,
            })
        else:
            funcs = {rot: round(pago.get(c, 0.0), 2) for c, rot in FUNCOES_ESTADO.items()}
            uf = e["uf"] if len(e["uf"]) == 2 and e["uf"] != "BR" else uf_por_prefixo.get(str(cod)[:2], e["uf"])
            estados.append({"cod_ibge": cod, "nome": e["ente"], "uf": uf, "esfera": e["esfera"], "populacao": pop, "pago_total": round(total, 2),
                            "empenhado_total": round(emp.get("00", 0.0), 2), **{f"pago_{k}": v for k, v in funcs.items()},
                            "por_hab_total": round(total / pop, 2) if pop else None,
                            **{f"por_hab_{k}": round(v / pop, 2) if pop else None for k, v in funcs.items()},
                            "pct_legislativa": round(funcs["legislativa"] / total, 4) if total else None,
                            "pct_judiciaria": round(funcs["judiciaria"] / total, 4) if total else None})
    municipios.sort(key=lambda m: -(m["por_hab_legislativo"] or 0))
    estados.sort(key=lambda s: -s["pago_total"])

    total_mun = sum(e["esfera"] == "M" for e in entes.values())
    medianas = {}
    for fx in ("até 10 mil", "10 a 50 mil", "50 a 100 mil", "100 a 500 mil", "mais de 500 mil"):
        g = [m for m in municipios if m["faixa"] == fx and m["por_hab_legislativo"]]
        if g:
            medianas[fx] = {"municipios": len(g), "por_hab_legislativo": round(median(m["por_hab_legislativo"] for m in g), 2),
                            "pct_legislativo": round(median(m["pct_legislativo"] for m in g if m["pct_legislativo"] is not None), 4),
                            "por_vereador": round(median(m["por_vereador_legislativo"] for m in g if m["por_vereador_legislativo"]), 2) if any(m["por_vereador_legislativo"] for m in g) else None}
    meta = {"ano": ano, "ano_vagas": ano_vagas, "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
            "fonte": "SICONFI/Tesouro Nacional, Declaração de Contas Anuais (DCA), anexo I-E; TSE (vagas de vereador)",
            "municipios_total": total_mun, "municipios_com_dca": len(municipios), "municipios_com_vereadores": sum(1 for m in municipios if m["vereadores"]),
            "estados": len(estados),
            "totais": {"pago_total": round(sum(m["pago_total"] for m in municipios), 2), "pago_legislativo": round(sum(m["pago_legislativo"] for m in municipios), 2),
                       "populacao_coberta": sum(m["populacao"] or 0 for m in municipios), "vereadores": sum(m["vereadores"] or 0 for m in municipios)},
            "medianas_por_faixa": medianas}
    (PUB / f"municipios_{ano}.json").write_text(json.dumps(municipios, ensure_ascii=False), encoding="utf-8")
    (PUB / f"estados_{ano}.json").write_text(json.dumps(estados, ensure_ascii=False), encoding="utf-8")
    out = PUB / f"municipios_meta_{ano}.json"
    out.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    log.info("%d de %d municípios com DCA %d (%d com nº de vereadores); câmaras R$ %.2f bi pagos; %d estados",
             len(municipios), total_mun, ano, meta["municipios_com_vereadores"], meta["totais"]["pago_legislativo"] / 1e9, len(estados))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser(); ap.add_argument("--ano", type=int, required=True); ap.add_argument("--vagas", type=int, default=2024)
    a = ap.parse_args(); run(a.ano, a.vagas)
