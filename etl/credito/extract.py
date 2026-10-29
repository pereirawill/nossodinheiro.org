"""
Inadimplência — crédito em atraso por estado, tipo de cliente, modalidade e faixa de renda (Banco Central, SCR.data).

    python -m etl.credito.extract            # gera data/public/credito.json

Fonte: Banco Central do Brasil, SCR.data (dados agregados do Sistema de Informações de Crédito), arquivo anual
https://www.bcb.gov.br/pda/desig/scrdata_<ano>.zip com um CSV por mês (uf; segmento; cliente PF/PJ; cnae_ocupacao; porte;
modalidade; submodalidade; …; carteira_ativa; carteira_inadimplencia; ativo_problematico). Valores em R$.
Baixamos os zips do ano corrente e do anterior, lemos todos os meses com DuckDB (série) e publicamos o último mês em detalhe.

Definições do BCB (metodologia SCR.data v2):
- carteira_ativa = tudo que está emprestado (a vencer + vencido);
- carteira_inadimplencia = parcelas vencidas há mais de 90 dias ("inadimplência", a medida padrão do BCB);
- taxa = carteira_inadimplencia ÷ carteira_ativa, em %. É inadimplência em VALOR (R$ atrasado / R$ emprestado), não em
  número de pessoas: o BCB não publica "quantas pessoas estão negativadas" (isso é dado de birôs privados).
- numero_de_operacoes = −1 quando há menos de 15 operações no agrupamento (sigilo); por isso não somamos operações.
Além do SCR, o painel publica as duas séries agregadas que o próprio BC usa no Relatório de Estabilidade Financeira:
- **SGS 29034**, comprometimento de renda das famílias: serviço da dívida mensal ÷ renda disponível bruta das famílias;
- **SGS 29037**, endividamento das famílias: estoque da dívida ÷ renda dos últimos doze meses.
São de março e janeiro de 2005 em diante, mensais. Não se somam à inadimplência do SCR: uma mede o que está atrasado,
as outras medem o peso da dívida de quem está em dia.

Granularidade: a UF é o menor recorte geográfico do SCR.data. O BCB também publica "SCR por sub-região" (105 áreas, sem nome
legível) — não há dado por município.
"""

from __future__ import annotations

import json
import logging
import re
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import httpx

from etl.ufs import UF_PARA_NOME

log = logging.getLogger("etl.credito")
PUB, RAW = Path("data/public"), Path("data/raw/scr")
ZIP = "https://www.bcb.gov.br/pda/desig/scrdata_{ano}.zip"
UA = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{c}/dados?formato=json"
SERIES_BCB = {"comprometimento": 29034, "endividamento": 29037}
TIPOS = {"carteira_ativa": "DOUBLE", "carteira_inadimplencia": "DOUBLE", "ativo_problematico": "DOUBLE", "numero_de_operacoes": "BIGINT"}


def baixar(c: httpx.Client) -> list[Path]:
    """CSVs mensais do ano corrente e do anterior (série de até 24 meses); o último mês é o publicado."""
    RAW.mkdir(parents=True, exist_ok=True)
    csvs: list[Path] = []
    for ano in (datetime.now().year, datetime.now().year - 1):
        z = RAW / f"scrdata_{ano}.zip"
        if not z.exists():
            r = c.get(ZIP.format(ano=ano))
            if r.status_code == 404:
                log.info("scrdata_%d.zip ainda não existe", ano); continue
            r.raise_for_status(); z.write_bytes(r.content)
        with zipfile.ZipFile(z) as zf:
            nomes = sorted(n for n in zf.namelist() if re.fullmatch(r"scrdata_\d{6}\.csv", n))
            for n in nomes:
                if not (RAW / n).exists():
                    zf.extract(n, RAW)
        log.info("scrdata_%d.zip: %d meses (%s … %s)", ano, len(nomes), nomes[0], nomes[-1])
        csvs += [RAW / n for n in nomes]
    if not csvs:
        raise RuntimeError("nenhum zip do SCR.data disponível")
    return sorted(csvs)


def agregar(csvs: list[Path]) -> dict:
    con = duckdb.connect()
    con.execute(f"""create view scr as select * from read_csv({[str(p) for p in csvs]!r}, delim=';', header=true, decimal_separator=',',
                    types={TIPOS!r}, encoding='utf-8', union_by_name=true)""")
    ult = con.execute("select max(data_base) from scr").fetchone()[0]
    ult_s = str(ult)[:10]
    def q(sql: str) -> list[tuple]:
        return con.execute(sql.replace("{ult}", f"'{ult_s}'")).fetchall()
    pct = "round(100*sum(carteira_inadimplencia)/nullif(sum(carteira_ativa),0), 2)"
    brasil = {cli: {"carteira": round(ca, 2), "inadimplencia": round(ci, 2), "pct": p}
              for cli, ca, ci, p in q(f"select cliente, sum(carteira_ativa), sum(carteira_inadimplencia), {pct} from scr where data_base={{ult}} group by 1")}
    por_uf = {}
    for uf, cli, ca, ci, p in q(f"select uf, cliente, sum(carteira_ativa), sum(carteira_inadimplencia), {pct} from scr where data_base={{ult}} group by 1,2"):
        d = por_uf.setdefault(uf, {"uf": uf, "nome": UF_PARA_NOME.get(uf, uf)})
        d[f"carteira_{cli.lower()}"] = round(ca, 2); d[f"pct_{cli.lower()}"] = p
    modalidades = [{"cliente": cli, "modalidade": m.strip(), "carteira": round(ca, 2), "pct": p}
                   for cli, m, ca, p in q(f"select cliente, modalidade, sum(carteira_ativa), {pct} from scr where data_base={{ult}} group by 1,2 order by 1, 3 desc")]
    porte = [{"cliente": cli, "porte": po.strip(), "carteira": round(ca, 2), "pct": p}
             for cli, po, ca, p in q(f"select cliente, porte, sum(carteira_ativa), {pct} from scr where data_base={{ult}} group by 1,2 order by 1, 3 desc")]
    # ocupação só existe para pessoa física (na PJ a mesma coluna traz o CNAE). O SCR não publica faixa etária;
    # "Aposentado/pensionista" é o recorte mais próximo de idade que o Banco Central divulga.
    ocupacao = [{"ocupacao": oc.strip(), "carteira": round(ca, 2), "pct": p, "operacoes": None}
                for oc, ca, p in q(f"select cnae_ocupacao, sum(carteira_ativa), {pct} from scr where data_base={{ult}} and cliente='PF' group by 1 order by 2 desc")]
    serie = [{"mes": str(m)[:7], "pct_pf": pf, "pct_pj": pj} for m, pf, pj in
             q("select data_base, round(100*sum(carteira_inadimplencia) filter (where cliente='PF')/nullif(sum(carteira_ativa) filter (where cliente='PF'),0), 2),"
               " round(100*sum(carteira_inadimplencia) filter (where cliente='PJ')/nullif(sum(carteira_ativa) filter (where cliente='PJ'),0), 2) from scr group by 1 order by 1")]
    return {"referencia": ult_s[:7], "brasil": brasil, "por_uf": sorted(por_uf.values(), key=lambda d: d["uf"]), "modalidades": modalidades,
            "porte": porte, "ocupacao": ocupacao, "serie": serie}


def series_familias(c: httpx.Client) -> dict:
    """Comprometimento (29034) e endividamento (29037) das famílias, do SGS. O serviço devolve 502 ou HTML com
    status 200 de forma intermitente, como no painel de Economia — por isso a repetição."""
    saida: dict[str, dict] = {}
    for chave, serie in SERIES_BCB.items():
        for tentativa in range(4):
            r = c.get(SGS.format(c=serie), headers={"User-Agent": "nossodinheiro.org"})
            if r.status_code == 200 and "json" in (r.headers.get("content-type") or ""):
                pontos = {}
                for x in r.json():
                    d, m, a = x["data"].split("/")
                    try:
                        pontos[f"{a}-{m}"] = float(x["valor"])
                    except (TypeError, ValueError):
                        continue
                if pontos:
                    saida[chave] = {"serie": serie, "pontos": dict(sorted(pontos.items()))}
                break
            log.info("SGS %s, tentativa %d: HTTP %s", serie, tentativa + 1, r.status_code)
            time.sleep(2 * (tentativa + 1))
        else:
            log.warning("SGS %s: desisti depois de 4 tentativas", serie)
    return saida


def run() -> Path:
    PUB.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers=UA, timeout=900, follow_redirects=True) as c:
        csvs = baixar(c)
        familias = series_familias(c)
    dados = {"gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="minutes"), **agregar(csvs),
             "familias": familias,
             "fontes": {"bcb": "Banco Central do Brasil, SCR.data (dados abertos), carteira ativa e carteira em inadimplência (>90 dias) por UF, cliente, modalidade e porte",
                        "familias": "Banco Central, SGS séries 29034 (comprometimento de renda das famílias) e 29037 "
                                    "(endividamento das famílias), medidas agregadas contra a renda disponível bruta das famílias"}}
    out = PUB / "credito.json"
    out.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    log.info("SCR %s: PF %.2f%% (R$ %.1f tri), PJ %.2f%%; %d UFs; %d meses", dados["referencia"], dados["brasil"]["PF"]["pct"], dados["brasil"]["PF"]["carteira"] / 1e12,
             dados["brasil"]["PJ"]["pct"], len(dados["por_uf"]), len(dados["serie"]))
    return out


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    run()
