"""
Punições e sanções — o que o poder público registrou como punido: empresas sancionadas, acordos de leniência e servidores
federais expulsos. Por estado do órgão que puniu, por categoria, por ano e por órgão.

    python -m etl.corrupcao.extract            # gera data/public/corrupcao.json

Fontes (Portal da Transparência, dados abertos, sem chave; um ZIP com CSV em latin-1, datado):
- **CEIS** — Cadastro de Empresas Inidôneas e Suspensas: sanções que impedem contratar com o poder público (Lei 8.666/14.133,
  Lei 8.429 de improbidade, Lei 10.520 do pregão). Vem de órgãos das três esferas, não só federais.
- **CNEP** — Cadastro Nacional de Empresas Punidas: sanções da Lei Anticorrupção (12.846/2013), inclusive multas com valor.
- **CEAF** — Cadastro de Expulsões da Administração Federal: demissões, cassações de aposentadoria e destituições de servidores
  federais, com o fundamento legal e o órgão de lotação.
- **Acordos de leniência** celebrados pela CGU com empresas (Lei 12.846/2013).

Privacidade: o CEIS e o CNEP trazem o CPF de pessoas físicas sancionadas em claro. **Nada disso é persistido**: este extrator
publica só contagens e somas. De nomes, saem apenas os de órgãos públicos e, nos acordos de leniência, a razão social das
empresas — que é o objeto do acordo e é publicada pela CGU.

O que estes números são: punições **registradas**, com a data em que a sanção começou. O que não são: medida de corrupção.
Um estado com mais sanções pode ter mais fiscalização, não mais crime; e o cadastro depende de cada órgão alimentar o sistema.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import re
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

from etl.ufs import UF_PARA_NOME

log = logging.getLogger("etl.corrupcao")
PUB = Path("data/public")
BASE = "https://portaldatransparencia.gov.br/download-de-dados/{cadastro}/{data}"
UA = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
TOPO = 15
# palavras do campo "FUNDAMENTAÇÃO LEGAL" do CEAF. Uma decisão cita vários artigos ("ART. 132, XI - CORRUPÇÃO;ART. 132, IV -
# IMPROBIDADE ADMINISTRATIVA"), então as contagens se sobrepõem: somam mais que o total de expulsões.
MOTIVOS = {
    "Corrupção": r"\bCORRUP",
    "Improbidade administrativa": r"IMPROBIDADE",
    "Valer-se do cargo em proveito próprio": r"VALER-SE DO CARGO",
    "Abandono de cargo ou inassiduidade": r"ABANDONO DE CARGO|INASSIDUIDADE",
    "Acumulação ilegal de cargos": r"ACUMULA",
    "Advocacia administrativa": r"ADVOCACIA ADMINISTRATIVA",
    "Aplicação irregular de dinheiro público": r"APLICA..O IRREGULAR",
    "Lesão aos cofres públicos ou dilapidação": r"LES.O AOS COFRES|DILAPIDA",
}


def _ano(data: str) -> str | None:
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", (data or "").strip())
    return m.group(3) if m else None


def _brl(v: str) -> float:
    v = (v or "").strip().replace(".", "").replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return 0.0


def baixar(c: httpx.Client, cadastro: str, arquivo: str | None = None) -> list[dict[str, str]]:
    """Baixa o ZIP mais recente do cadastro (o Portal publica por data; tentamos alguns dias para trás).
    `arquivo` escolhe qual CSV ler quando o ZIP tem mais de um (o de leniência traz Acordos.csv e Efeitos.csv)."""
    hoje = datetime.now()
    for dias in range(0, 8):
        data = (hoje - timedelta(days=dias)).strftime("%Y%m%d")
        r = c.get(BASE.format(cadastro=cadastro, data=data), headers={"referer": f"https://portaldatransparencia.gov.br/download-de-dados/{cadastro}"})
        if r.status_code != 200 or not r.content.startswith(b"PK"):
            continue
        z = zipfile.ZipFile(io.BytesIO(r.content))
        nomes = [n for n in z.namelist() if n.lower().endswith(".csv")]
        nome = next((n for n in nomes if arquivo and arquivo.lower() in n.lower()), None) or max(nomes, key=lambda n: z.getinfo(n).file_size)
        bruto = csv.DictReader(io.StringIO(z.read(nome).decode("latin-1", "ignore")), delimiter=";")
        # os cabeçalhos trazem travessão em cp1252 (\x96) e espaços duplos; normalizamos para poder referenciar a coluna
        linhas = [{re.sub(r"\s+", " ", (k or "").replace("\x96", "-")).strip(): v for k, v in r.items()} for r in bruto]
        log.info("%s %s: %d registros (%s)", cadastro, data, len(linhas), nome)
        return linhas
    raise RuntimeError(f"nenhum arquivo do cadastro {cadastro} nos últimos 8 dias")


def _contar(linhas: list[dict], coluna: str, limite: int | None = None) -> list[dict]:
    cnt = Counter((r.get(coluna) or "Sem informação").strip() or "Sem informação" for r in linhas)
    itens = [{"nome": k, "n": v} for k, v in cnt.most_common(limite)]
    return itens


def _por_ano(linhas: list[dict], coluna: str = "DATA INÍCIO SANÇÃO") -> dict[str, int]:
    cnt = Counter(a for a in (_ano(r.get(coluna, "")) for r in linhas) if a and "1990" <= a <= str(datetime.now().year))
    return dict(sorted(cnt.items()))


def _por_uf(linhas: list[dict]) -> list[dict]:
    cnt = Counter((r.get("UF ÓRGÃO SANCIONADOR") or "").strip() for r in linhas)
    return sorted(({"uf": uf, "nome": UF_PARA_NOME[uf], "n": n} for uf, n in cnt.items() if uf in UF_PARA_NOME), key=lambda d: d["uf"])


def _vigente(fim: str) -> bool:
    """Sem data final = sanção por prazo indeterminado (segue valendo); com data, vale até ela."""
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", (fim or "").strip())
    if not m:
        return True
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" >= datetime.now().strftime("%Y-%m-%d")


def empresas(linhas: list[dict], cadastro: str) -> dict:
    vigentes = [r for r in linhas if _vigente(r.get("DATA FINAL SANÇÃO", ""))]
    d = {"registros": len(linhas), "vigentes": len(vigentes), "encerradas": len(linhas) - len(vigentes),
         "vigentes_sem_prazo": sum(1 for r in vigentes if not (r.get("DATA FINAL SANÇÃO") or "").strip()), "por_uf": _por_uf(linhas), "por_ano": _por_ano(linhas),
         "por_categoria": _contar(linhas, "CATEGORIA DA SANÇÃO"), "por_esfera": _contar(linhas, "ESFERA ÓRGÃO SANCIONADOR"),
         "orgaos": _contar(linhas, "ÓRGÃO SANCIONADOR", TOPO),
         "pessoa_juridica": sum(1 for r in linhas if (r.get("TIPO DE PESSOA") or "").strip() == "J"),
         "sem_uf": sum(1 for r in linhas if (r.get("UF ÓRGÃO SANCIONADOR") or "").strip() not in UF_PARA_NOME)}
    if cadastro == "cnep":
        multas = [_brl(r.get("VALOR DA MULTA", "")) for r in linhas]
        d["multas"] = {"registros_com_multa": sum(1 for m in multas if m > 0), "total": round(sum(multas), 2)}
    return d


def expulsoes(linhas: list[dict]) -> dict:
    motivos = []
    for rotulo, padrao in MOTIVOS.items():
        n = sum(1 for r in linhas if re.search(padrao, (r.get("FUNDAMENTAÇÃO LEGAL") or "").upper()))
        if n:
            motivos.append({"nome": rotulo, "n": n})
    return {"registros": len(linhas), "por_ano": _por_ano(linhas), "por_categoria": _contar(linhas, "CATEGORIA DA SANÇÃO"),
            "por_orgao_lotacao": _contar(linhas, "ÓRGÃO DE LOTAÇÃO", TOPO), "por_uf": _por_uf(linhas),
            "motivos": sorted(motivos, key=lambda m: -m["n"])}


def leniencia(linhas: list[dict]) -> dict:
    acordos = [{"empresa": (r.get("RAZÃO SOCIAL - CADASTRO RECEITA") or r.get("NOME FANTASIA - CADASTRO RECEITA") or "Não informado").strip(),
                "inicio": (r.get("DATA DE INÍCIO DO ACORDO") or "").strip(), "fim": (r.get("DATA DE FIM DO ACORDO") or "").strip(),
                "situacao": (r.get("SITUAÇÃO DO ACORDO DE LENIÊNICA") or "Sem informação").strip(),
                "orgao": (r.get("ÓRGÃO SANCIONADOR") or "").strip()} for r in linhas]
    return {"registros": len(acordos), "por_situacao": _contar(linhas, "SITUAÇÃO DO ACORDO DE LENIÊNICA"),
            "por_ano": _por_ano(linhas, "DATA DE INÍCIO DO ACORDO"), "acordos": sorted(acordos, key=lambda a: a["inicio"][-4:] + a["inicio"][:5], reverse=True)}


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers=UA, timeout=300, follow_redirects=True) as c:
        ceis = empresas(baixar(c, "ceis"), "ceis")
        cnep = empresas(baixar(c, "cnep"), "cnep")
        ceaf = expulsoes(baixar(c, "ceaf"))
        len_ = leniencia(baixar(c, "acordos-leniencia", arquivo="Acordos"))
    dados = {"gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"),
             "ceis": ceis, "cnep": cnep, "ceaf": ceaf, "leniencia": len_,
             "fontes": {"ceis": "Portal da Transparência, Cadastro de Empresas Inidôneas e Suspensas (CEIS)",
                        "cnep": "Portal da Transparência, Cadastro Nacional de Empresas Punidas (CNEP), Lei 12.846/2013",
                        "ceaf": "Portal da Transparência, Cadastro de Expulsões da Administração Federal (CEAF)",
                        "leniencia": "Portal da Transparência / CGU, acordos de leniência",
                        "cpi": "Transparência Internacional, Índice de Percepção da Corrupção (no painel Rankings; é uma ONG, não órgão público)"}}
    out = PUB / "corrupcao.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    log.info("CEIS %d sanções, CNEP %d (R$ %.1f mi em multas), CEAF %d expulsões, %d acordos de leniência",
             ceis["registros"], cnep["registros"], cnep["multas"]["total"] / 1e6, ceaf["registros"], len_["registros"])
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
