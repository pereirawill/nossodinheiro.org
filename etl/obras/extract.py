"""
Obras — o cadastro federal de obras e projetos de investimento: quantas estão paradas, onde, e quanto já foi empenhado.

    python -m etl.obras.extract                 # baixa tudo (≈1.000 requisições, ~10 min) e gera data/public/obras.json
    python -m etl.obras.extract --so-transformar  # só reprocessa o que já está em data/raw

Fonte: **Obrasgov/CIPI** (Cadastro Integrado de Projetos de Investimento), API pública do Ministério da Gestão, sem chave:
- `https://api.obrasgov.gestao.gov.br/obrasgov/api/projeto-investimento` — um registro por obra: nome, situação, UF, espécie,
  datas prevista e efetiva, eixo/tipo, executores e `fontesDeRecurso` com o valor **previsto** de investimento.
- `https://api.obrasgov.gestao.gov.br/obrasgov/api/execucao-financeira` — empenhos federais por obra (`idProjetoInvestimento`,
  `valorEmpenho`), que somamos por obra para ter quanto o Orçamento da União já comprometeu.

Limites da API (medidos em 27/10/2026): página de no máximo 50 (100+ devolve HTTP 500); `totalElements` do endpoint de obras é
falso (repete o que já foi servido), então andamos as páginas até vir uma incompleta; filtros por `uf` e `situacao` devolvem 500.
O host antigo `api-publica.obrasgov.gestao.gov.br` saiu do ar — o que responde é `api.obrasgov.gestao.gov.br`.

O que o cadastro é: obras com participação de recurso federal, declaradas pelos órgãos. Não é o conjunto de todas as obras
públicas do país, e "valor previsto" não é valor gasto — por isso o painel mostra as duas colunas separadas.
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path

import time

import httpx

from etl.ufs import UF_PARA_NOME

log = logging.getLogger("etl.obras")
PUB, RAW = Path("data/public"), Path("data/raw")
API = "https://api.obrasgov.gestao.gov.br/obrasgov/api/{recurso}"
UA = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
PAGINA = 50
WORKERS = 6           # o Obrasgov leva ~80 s por requisição e devolve 429 se pedirmos rápido demais
PARADAS = {"Paralisada", "Inacabada"}          # situações que o CIPI usa para obra interrompida
TOPO = 40


def _pagina(c: httpx.Client, recurso: str, n: int) -> list[dict] | None:
    """Uma página, com espera crescente. HTTP 429 = estamos pedindo rápido demais; aí a espera é bem maior."""
    for tentativa in range(5):
        try:
            r = c.get(API.format(recurso=recurso), params={"pagina": n, "tamanhoDaPagina": PAGINA})
            if r.status_code == 200:
                return r.json().get("content", [])
            if r.status_code == 429:
                time.sleep(30 * (tentativa + 1))
            else:
                time.sleep(2 * (tentativa + 1))
            log.debug("%s página %d: HTTP %d", recurso, n, r.status_code)
        except httpx.HTTPError as e:
            log.debug("%s página %d: %s", recurso, n, e)
            time.sleep(2 * (tentativa + 1))
    log.warning("%s página %d falhou nas tentativas", recurso, n)
    return None


def _ler(arquivo: Path) -> list[dict]:
    with gzip.open(arquivo, "rt", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def baixar(recurso: str, arquivo: Path, paginas_conhecidas: int | None = None) -> tuple[list[dict], int]:
    """
    Anda as páginas em paralelo e grava um jsonl.gz **a cada bloco**, com um arquivo `.pagina` ao lado: se o servidor derrubar a
    coleta no meio (acontece: o Obrasgov devolve 500 e 524 com frequência), é só rodar de novo que continua de onde parou.
    Só paramos quando um bloco inteiro responde 200 com lista vazia — bloco que só deu erro é tentado de novo, para não truncar
    a base por causa de instabilidade. Devolve (registros, páginas que falharam).
    """
    if arquivo.exists():
        linhas = _ler(arquivo)
        log.info("%s: %d registros do cache (%s)", recurso, len(linhas), arquivo.name)
        return linhas, 0
    RAW.mkdir(parents=True, exist_ok=True)
    parcial, marca = arquivo.with_suffix(".parcial.gz"), arquivo.with_suffix(".pagina")
    buracos = arquivo.with_suffix(".falhas")          # páginas que não responderam, para uma segunda passada no fim
    registros: list[dict] = _ler(parcial) if parcial.exists() else []
    pagina = int(marca.read_text()) if marca.exists() else 0
    falhas_pendentes: set[int] = set(json.loads(buracos.read_text())) if buracos.exists() else set()
    if pagina:
        log.info("%s: retomando da página %d com %d registros já baixados", recurso, pagina, len(registros))
    falhas, bloco, vazios_seguidos, ultima_com_dado, bloqueios = 0, WORKERS * 2, 0, -1, 0   # bloco curto = progresso salvo com frequência
    with httpx.Client(headers=UA, timeout=180, follow_redirects=True) as c:
        while True:
            faixa = range(pagina, pagina + bloco)
            with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                paginas = list(ex.map(lambda n: _pagina(c, recurso, n), faixa))
            obtidos = [r for p in paginas if p for r in p]
            erros = sum(1 for p in paginas if p is None)
            falhas += erros
            falhas_pendentes |= {n for n, p in zip(faixa, paginas) if p is None}
            falhas_pendentes -= {n for n, p in zip(faixa, paginas) if p is not None}
            registros += obtidos
            with gzip.open(parcial, "at", encoding="utf-8") as f:
                for r in obtidos:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            pagina += bloco
            marca.write_text(str(pagina))
            buracos.write_text(json.dumps(sorted(falhas_pendentes)))
            if obtidos:
                ultima_com_dado = max(n for n, p in zip(faixa, paginas) if p)
            log.info("%s: páginas %d–%d → %d registros (%d erros); total %d", recurso, faixa.start, faixa.stop - 1, len(obtidos), erros, len(registros))
            # Fim de verdade: DOIS blocos seguidos respondendo 200 com lista vazia. Um só não basta — o Obrasgov, sob carga,
            # devolve 200 com content vazio em vez de erro, e pararíamos no meio da base achando que acabou.
            vazios_seguidos = vazios_seguidos + 1 if (not obtidos and erros == 0) else 0
            # bloco inteiro com erro, várias vezes seguidas: o servidor nos barrou (429) ou caiu — paramos e avisamos
            bloqueios = bloqueios + 1 if erros == len(paginas) else 0
            if bloqueios >= 3:
                log.warning("%s: 3 blocos seguidos sem nenhuma resposta na página %d — servidor barrando; pare e rode de novo mais tarde", recurso, pagina)
                break
            if vazios_seguidos >= 2 or (paginas_conhecidas and pagina >= paginas_conhecidas):
                break
        # segunda passada: tenta de novo as páginas que falharam no caminho
        if falhas_pendentes and bloqueios < 3:
            pendentes = sorted(falhas_pendentes)
            log.info("%s: repescagem de %d páginas que falharam", recurso, len(pendentes))
            for i in range(0, len(pendentes), WORKERS):
                lote = pendentes[i:i + WORKERS]
                with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                    res = list(ex.map(lambda n: _pagina(c, recurso, n), lote))
                recuperados = [r for p in res if p for r in p]
                registros += recuperados
                falhas_pendentes -= {n for n, p in zip(lote, res) if p is not None}
                if recuperados:
                    with gzip.open(parcial, "at", encoding="utf-8") as f:
                        for r in recuperados:
                            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            buracos.write_text(json.dumps(sorted(falhas_pendentes)))
            log.info("%s: após a repescagem restam %d páginas sem resposta", recurso, len(falhas_pendentes))
    falhas = len(falhas_pendentes)
    if bloqueios >= 3:
        raise SystemExit(f"{recurso}: servidor parou de responder (HTTP 429/500 em bloco). O que já foi baixado está em "
                         f"{parcial.name}; rode de novo mais tarde que ele continua de onde parou.")
    parcial.replace(arquivo)
    marca.unlink(missing_ok=True)
    buracos.unlink(missing_ok=True)
    log.info("%s: %d registros, última página com dado: %d, %d páginas sem resposta", recurso, len(registros), ultima_com_dado, falhas)
    return registros, falhas


def _previsto(o: dict) -> float:
    return round(sum(float(f.get("valorInvestimentoPrevisto") or 0) for f in (o.get("fontesDeRecurso") or [])), 2)


def _anos_desde(iso: str | None) -> float | None:
    """Anos entre a data e hoje (negativo se a data ainda não chegou)."""
    if not iso:
        return None
    try:
        d = date.fromisoformat(str(iso)[:10])
    except ValueError:
        return None
    return round((date.today() - d).days / 365.25, 1)


def transformar(obras: list[dict], empenhos: list[dict]) -> dict:
    por_obra_empenho: dict[str, float] = defaultdict(float)
    for e in empenhos:
        idp = e.get("idProjetoInvestimento")
        if idp:
            por_obra_empenho[idp] += float(e.get("valorEmpenho") or 0)

    situacao: dict[str, dict] = defaultdict(lambda: {"n": 0, "previsto": 0.0, "empenhado": 0.0})
    ufs: dict[str, dict] = defaultdict(lambda: {"n": 0, "paradas": 0, "previsto": 0.0, "previsto_paradas": 0.0, "empenhado_paradas": 0.0})
    eixos: dict[str, dict] = defaultdict(lambda: {"n": 0, "previsto": 0.0, "paradas": 0})
    tipos: dict[str, dict] = defaultdict(lambda: {"n": 0, "previsto": 0.0, "paradas": 0})
    paradas: list[dict] = []
    for o in obras:
        s = (o.get("situacao") or "Sem informação").strip()
        prev, emp = _previsto(o), round(por_obra_empenho.get(o.get("idUnico", ""), 0.0), 2)
        parada = s in PARADAS
        situacao[s]["n"] += 1; situacao[s]["previsto"] += prev; situacao[s]["empenhado"] += emp
        uf = (o.get("uf") or "").strip().upper()
        if uf in UF_PARA_NOME:
            d = ufs[uf]; d["n"] += 1; d["previsto"] += prev
            if parada:
                d["paradas"] += 1; d["previsto_paradas"] += prev; d["empenhado_paradas"] += emp
        for lista, destino in ((o.get("eixos") or [], eixos), (o.get("tipos") or [], tipos)):
            for item in lista[:1]:                       # o CIPI traz um eixo/tipo principal por obra
                k = (item.get("descricao") or "Sem informação").strip()
                destino[k]["n"] += 1; destino[k]["previsto"] += prev
                if parada:
                    destino[k]["paradas"] += 1
        if parada:
            paradas.append({"id": o.get("idUnico"), "nome": (o.get("nome") or "").strip(), "uf": uf, "situacao": s,
                            "especie": (o.get("especie") or "").strip(), "previsto": prev, "empenhado": emp,
                            # dataSituacao = quando o órgão atualizou o status pela última vez, não quando a obra parou
                            "situacao_desde": str(o.get("dataSituacao") or "")[:10], "anos_sem_atualizacao": _anos_desde(o.get("dataSituacao")),
                            "fim_previsto": str(o.get("dataFinalPrevista") or "")[:10], "anos_de_atraso": _anos_desde(o.get("dataFinalPrevista")),
                            "executor": ((o.get("executores") or [{}])[0].get("nome") or "").strip()})
    anos = [p["anos_sem_atualizacao"] for p in paradas if p["anos_sem_atualizacao"] is not None]
    atrasos = [p["anos_de_atraso"] for p in paradas if (p["anos_de_atraso"] or 0) > 0]
    return {
        "total": len(obras), "obras_com_empenho": len(por_obra_empenho),
        "por_situacao": sorted(({"situacao": k, **{x: round(v, 2) for x, v in d.items()}} for k, d in situacao.items()), key=lambda d: -d["n"]),
        "por_uf": sorted(({"uf": k, "nome": UF_PARA_NOME[k], **{x: round(v, 2) for x, v in d.items()}} for k, d in ufs.items()), key=lambda d: d["uf"]),
        "por_eixo": sorted(({"nome": k, **{x: round(v, 2) for x, v in d.items()}} for k, d in eixos.items()), key=lambda d: -d["n"]),
        "por_tipo": sorted(({"nome": k, **{x: round(v, 2) for x, v in d.items()}} for k, d in tipos.items()), key=lambda d: -d["n"])[:15],
        "paradas": {"n": len(paradas), "previsto": round(sum(p["previsto"] for p in paradas), 2),
                    "empenhado": round(sum(p["empenhado"] for p in paradas), 2),
                    "anos_sem_atualizacao_mediana": round(sorted(anos)[len(anos) // 2], 1) if anos else None,
                    "com_prazo_vencido": len(atrasos),
                    "anos_de_atraso_mediana": round(sorted(atrasos)[len(atrasos) // 2], 1) if atrasos else None,
                    "maiores": sorted(paradas, key=lambda p: -p["previsto"])[:TOPO]},
    }


def run(so_transformar: bool = False) -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    arq_obras, arq_emp = RAW / "obrasgov_projetos.jsonl.gz", RAW / "obrasgov_empenhos.jsonl.gz"
    if so_transformar and not (arq_obras.exists() and arq_emp.exists()):
        raise SystemExit("sem cache completo em data/raw: rode sem --so-transformar")
    obras, falhas_obras = baixar("projeto-investimento", arq_obras)
    empenhos, falhas_emp = baixar("execucao-financeira", arq_emp, paginas_conhecidas=420)
    if len(obras) < 15_000:
        raise SystemExit(f"só {len(obras)} obras coletadas: o cadastro tem ~25 mil (TCU 2025), então a coleta truncou. "
                         f"Apague data/raw/obrasgov_projetos.jsonl.gz e rode de novo.")
    dados = {"gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
             "paginas_sem_resposta": {"obras": falhas_obras, "empenhos": falhas_emp}, **transformar(obras, empenhos),
             "fontes": {"obras": "Obrasgov/CIPI, API pública do Ministério da Gestão: projetos de investimento com recurso federal",
                        "empenhos": "Obrasgov/CIPI, execução financeira: empenhos federais por obra"}}
    out = PUB / "obras.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    log.info("%d obras; %d paradas (R$ %.1f bi previstos, R$ %.1f bi empenhados); situações: %s", dados["total"], dados["paradas"]["n"],
             dados["paradas"]["previsto"] / 1e9, dados["paradas"]["empenhado"] / 1e9,
             ", ".join(f"{s['situacao']} {s['n']}" for s in dados["por_situacao"][:5]))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    ap = argparse.ArgumentParser(); ap.add_argument("--so-transformar", action="store_true")
    run(ap.parse_args().so_transformar)
