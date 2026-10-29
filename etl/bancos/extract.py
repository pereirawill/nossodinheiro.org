"""
Lucro dos bancos no Brasil — série por ano e por instituição.

    python -m etl.bancos.extract            # gera data/public/bancos.json

Fonte: **Banco Central, IF.data** (API Olinda, sem chave), relatório **1 — Resumo**, que traz por instituição
o Lucro Líquido, o Patrimônio Líquido, o Ativo Total e a Carteira de Crédito.

Três decisões que definem o painel:

1. **Não existe 1988.** O IF.data começa em **março de 2000** (conferido: 1993 a 1999 devolvem zero linhas) e os
   arquivos CSV do Cosif só estão publicados a partir dos anos recentes. Além disso, antes do Plano Real o lucro
   nominal não significa nada (cinco trocas de moeda) — a mesma armadilha do painel da indústria.
2. **O lucro do IF.data é acumulado no semestre, não no ano.** Março = jan–mar, junho = jan–jun, setembro =
   jul–set, dezembro = jul–dez. Conferido em 2025: o Itaú aparece com R$ 10,9 bi em março, R$ 22,3 bi em junho e
   R$ 12,0 bi em setembro. Logo, **lucro do ano = junho + dezembro**; somar os quatro trimestres contaria o
   primeiro semestre duas vezes. Há invariante no código (`_conferir_semestre`).
3. **Universo = conglomerado financeiro (`TipoInstituicao=2`)**, o único que alcança 2000. O conglomerado
   *prudencial* (tipo 1), que reúne também as não financeiras do grupo, só existe depois de 2014 e é usado aqui
   como conferência do último ano fechado (a diferença vai para o JSON). Quando o BC informa o conglomerado
   prudencial, as linhas do mesmo grupo são somadas — é o que junta as duas metades do Nubank ("NUBANK" e
   "NU PAGAMENTOS", que no universo financeiro são independentes entre si).

Estoque × fluxo: Lucro Líquido é fluxo (soma dos dois semestres); Patrimônio Líquido, Ativo e Carteira de Crédito
são saldos e ficam com a **posição de dezembro**.

Valores NOMINAIS no JSON, mais `deflator[ano]` pelo IPCA (SIDRA 1737, índice de dezembro) para o site mostrar em
reais do último ano fechado — como no painel Histórico.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import logging
import re
import statistics
import time
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import httpx

from etl.estatais.extract import DFP, _baixar as _baixar_dfp, _e_linha_do_lucro, _num as _num_cvm

log = logging.getLogger("etl.bancos")
PUB, RAW = Path("data/public"), Path("data/raw")
OLINDA = "https://olinda.bcb.gov.br/olinda/servico/IFDATA/versao/v1/odata/"
SIDRA_IPCA = "https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/all?formato=json"
ANO_INICIO = 2000
TIPO_FINANCEIRO, TIPO_PRUDENCIAL = 2, 1

# Tipo de consolidado bancário do BC (campo Tcb do cadastro). b1/b2/b4 = bancos; b3 = cooperativas de crédito;
# n* = instituições não bancárias (financeiras, corretoras, instituições de pagamento).
SEGMENTO = {
    "B1": ("bancos", "Banco comercial, múltiplo com carteira comercial ou caixa econômica"),
    "B2": ("bancos", "Banco múltiplo sem carteira comercial, de investimento ou de câmbio"),
    "B4": ("bancos", "Banco de desenvolvimento"),
    "B3S": ("cooperativas", "Cooperativa de crédito singular"),
    "B3C": ("cooperativas", "Cooperativa de crédito central"),
    "N1": ("nao_bancarias", "Instituição não bancária de crédito"),
    "N2": ("nao_bancarias", "Instituição não bancária no mercado de capitais"),
    "N3": ("nao_bancarias", "Instituição não bancária — outras"),
    "N4": ("nao_bancarias", "Instituição de pagamento"),
}
# Bancos de capital aberto, para conferir o IF.data contra o balanço que eles entregam à CVM.
# CNPJ (8 dígitos) → (nome do grupo no IF.data, nome da companhia na CVM).
CVM_BANCOS = {
    "60872504": ("ITAU", "Itaú Unibanco Holding S.A."),
    "60746948": ("BRADESCO", "Banco Bradesco S.A."),
    "00000000": ("BB", "Banco do Brasil S.A."),
    "90400888": ("SANTANDER", "Banco Santander (Brasil) S.A."),
    "92702067": ("BANRISUL", "Banco do Estado do Rio Grande do Sul S.A."),
}
COLUNAS = {"Lucro Líquido": "lucro", "Patrimônio Líquido": "pl", "Ativo Total": "ativo",
           "Carteira de Crédito": "credito", "Carteira de Crédito Classificada": "credito"}
TOP = 15


def _get(c: httpx.Client, url: str, tentativas: int = 4) -> list[dict]:
    """O Olinda devolve 502/504 e HTML com status 200 de vez em quando — mesma armadilha do SGS."""
    for i in range(tentativas):
        try:
            r = c.get(url, timeout=300.0)
            if r.status_code == 200 and "json" in r.headers.get("content-type", ""):
                return r.json()["value"]
            log.warning("IF.data devolveu %s (%s)", r.status_code, r.headers.get("content-type"))
        except httpx.HTTPError as e:
            log.warning("IF.data falhou: %s", e)
        time.sleep(5 * (i + 1))
    raise RuntimeError(f"IF.data não respondeu: {url}")


def _cache(c: httpx.Client, nome: str, url: str) -> list[dict]:
    arq = RAW / "ifdata" / f"{nome}.json.gz"
    if arq.exists():
        with gzip.open(arq, "rt", encoding="utf-8") as f:
            return json.load(f)
    v = _get(c, url)
    arq.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(arq, "wt", encoding="utf-8") as f:
        json.dump(v, f)
    return v


def cadastro(c: httpx.Client, anomes: int) -> dict[str, dict]:
    url = f"{OLINDA}IfDataCadastro(AnoMes=@AnoMes)?@AnoMes={anomes}&$format=json"
    out = {}
    for x in _cache(c, f"cadastro_{anomes}", url):
        out[x["CodInst"]] = {"nome": (x.get("NomeInstituicao") or "").strip(),
                             "tcb": (x.get("Tcb") or "").strip().upper(),
                             "prudencial": x.get("CodConglomeradoPrudencial"),
                             "uf": x.get("Uf")}
    return out


def resumo(c: httpx.Client, anomes: int, tipo: int = TIPO_FINANCEIRO) -> dict[str, dict]:
    """Relatório Resumo de um trimestre. Devolve {CodInst: {lucro, pl, ativo, credito}}, em reais."""
    url = (f"{OLINDA}IfDataValores(AnoMes=@AnoMes,TipoInstituicao=@TipoInstituicao,Relatorio=@Relatorio)"
           f"?@AnoMes={anomes}&@TipoInstituicao={tipo}&@Relatorio='1'&$format=json")
    bruto: dict[tuple, float] = {}
    sem_codigo = 0
    for x in _cache(c, f"resumo_{tipo}_{anomes}", url):
        campo = COLUNAS.get((x.get("NomeColuna") or "").split("\n")[0].strip())
        if campo is None:
            continue
        if x["CodInst"] is None:
            # Em 200006 duas instituições vêm sem código e sem nome; não há como identificá-las.
            sem_codigo += campo == "lucro"
            continue
        chave = (x["CodInst"], x["Conta"], campo)
        valor = float(x["Saldo"] or 0.0)
        # O trimestre mais recente volta com as linhas repetidas; igual é dedupe, diferente é erro de leitura.
        if chave in bruto and abs(bruto[chave] - valor) > 0.01:
            raise RuntimeError(f"IF.data {anomes}: valores conflitantes para {chave}")
        bruto[chave] = valor
    if sem_codigo:
        log.warning("IF.data %s: %d instituições sem código, fora da conta", anomes, sem_codigo)
    out: dict[str, dict] = defaultdict(dict)
    for (cod, _conta, campo), valor in bruto.items():
        out[cod][campo] = out[cod].get(campo, 0.0) + valor
    return dict(out)


def _razao_mediana(a: dict[str, dict], b: dict[str, dict]) -> float | None:
    """Mediana de lucro(b)/lucro(a) entre as 40 maiores por ativo, só com lucro positivo acima de R$ 1 milhão."""
    grandes = sorted(b, key=lambda k: -(b[k].get("ativo") or 0))[:40]
    razoes = [(b[k].get("lucro") or 0) / (a.get(k, {}).get("lucro") or 0) for k in grandes
              if (a.get(k, {}).get("lucro") or 0) > 1e6 and (b[k].get("lucro") or 0) > 0]
    return statistics.median(razoes) if len(razoes) >= 10 else None


def _conferir_semestre(t1: dict[str, dict], s1: dict[str, dict], t3: dict[str, dict],
                       s2: dict[str, dict], ano: int) -> None:
    """
    Invariante da regra "lucro do ano = junho + dezembro": como o valor acumula dentro do semestre, o segundo
    trimestre de cada semestre tem de valer cerca de **duas vezes** o primeiro. Conferido em 2000–2026: a mediana
    fica entre 1,65 e 2,50 em todos os anos. Sair dessa faixa significa que o BC mudou a forma de acumular.
    """
    for nome, r in (("jun/mar", _razao_mediana(t1, s1)), ("dez/set", _razao_mediana(t3, s2) if s2 else None)):
        if r is not None and not 1.5 <= r <= 2.6:
            raise RuntimeError(f"{ano}: mediana {nome} = {r:.2f}, fora de [1,5; 2,6] — o lucro do IF.data "
                               "deixou de acumular por semestre, revisar a regra do painel")


def ipca(c: httpx.Client) -> dict[int, float]:
    d = c.get(SIDRA_IPCA, timeout=120.0).json()
    out = {}
    for r in d[1:]:
        p = r.get("D3C") or ""                       # AAAAMM
        if len(p) == 6 and p.endswith("12"):
            out[int(p[:4])] = float(r["V"])
    return out


def ler_anos(c: httpx.Client) -> list[dict]:
    """Um registro por ano: os saldos de dezembro, o lucro dos dois semestres e o cadastro do último período."""
    hoje = datetime.now(timezone.utc)
    out = []
    for ano in range(ANO_INICIO, hoje.year + 1):
        s1, s2 = resumo(c, ano * 100 + 6), resumo(c, ano * 100 + 12)
        if not s1:
            # Ano em curso sem o 1º semestre fechado: fica só com o 1º trimestre, rotulado como parcial.
            s1 = resumo(c, ano * 100 + 3)
            if not s1:
                log.info("%d sem dado no IF.data", ano)
                continue
            periodos = [ano * 100 + 3]
        else:
            periodos = [ano * 100 + 6] + ([ano * 100 + 12] if s2 else [])
        _conferir_semestre(resumo(c, ano * 100 + 3), s1, resumo(c, ano * 100 + 9), s2, ano)
        inst = {}
        for cod in set(s1) | set(s2):
            fim = s2.get(cod) or s1.get(cod) or {}
            inst[cod] = {"lucro": (s1.get(cod, {}).get("lucro") or 0.0) + (s2.get(cod, {}).get("lucro") or 0.0),
                         "pl": fim.get("pl") or 0.0, "ativo": fim.get("ativo") or 0.0,
                         "credito": fim.get("credito") or 0.0}
        out.append({"ano": ano, "parcial": not s2, "periodos": periodos,
                    "inst": inst, "cadastro": cadastro(c, periodos[-1])})
    return out


def _chaves(dados: list[dict]) -> dict[tuple[int, str], str]:
    """
    Chave do grupo, por ano. O conglomerado prudencial só existe a partir de 2014; usá-lo direto como chave
    partiria cada banco em duas séries (uma até 2013, outra de 2014 em diante). Então cada conglomerado
    prudencial é apelidado pelo **código do seu maior membro** — no Itaú é o próprio conglomerado financeiro, que
    não mudou desde 2000, e assim a série fica inteira; no Nubank é o que junta "NUBANK" e "NU PAGAMENTOS",
    publicados como independentes entre si no universo financeiro.

    O apelido vale **só nos anos em que a instituição estava no grupo**. É o que impede que a compra da
    Easynvest, em 2021, jogue para a conta do Nubank o lucro que a corretora teve nos vinte anos anteriores.
    """
    ativo_max: dict[str, float] = defaultdict(float)
    prudencial_de: dict[tuple[int, str], str] = {}
    membros: dict[str, set[str]] = defaultdict(set)
    estreia: dict[str, tuple[int, str]] = {}
    anos_de: dict[str, list[int]] = defaultdict(list)
    for d in dados:
        for cod, v in d["inst"].items():
            ativo_max[cod] = max(ativo_max[cod], v["ativo"])
            anos_de[cod].append(d["ano"])
            prud = d["cadastro"].get(cod, {}).get("prudencial")
            if prud:
                prudencial_de[(d["ano"], cod)] = prud
                membros[prud].add(cod)
                estreia.setdefault(cod, (d["ano"], prud))
    rep = {p: max(cods, key=lambda c: (ativo_max[c], c)) for p, cods in membros.items()}
    chaves = {chave: rep[p] for chave, p in prudencial_de.items()}
    # Antes de 2014 não havia conglomerado prudencial: os anos anteriores à estreia da instituição em um grupo
    # vão para o mesmo grupo. É o que mantém inteira a série da Caixa, que até 2021 era publicada como
    # instituição (00360305) e depois como conglomerado financeiro (C0051626), os dois no mesmo prudencial.
    for cod, (ano_estreia, prud) in estreia.items():
        for ano in anos_de[cod]:
            if ano < ano_estreia:
                chaves[(ano, cod)] = rep[prud]
    return chaves


def consolidar(dados: list[dict]) -> tuple[list[dict], dict[str, dict], int]:
    chaves = _chaves(dados)
    anos: list[dict] = []
    series: dict[str, dict] = defaultdict(lambda: {"serie": {}, "nome": None, "tcb": ""})
    ultimo_fechado = 0
    for d in dados:
        ano = d["ano"]
        if not d["parcial"]:
            ultimo_fechado = ano
        reg: dict[str, dict] = {}
        for cod, v in d["inst"].items():
            g = chaves.get((ano, cod), cod)
            r = reg.setdefault(g, {"lucro": 0.0, "pl": 0.0, "ativo": 0.0, "credito": 0.0, "n": 0,
                                   "nome": None, "tcb": "", "_ativo": -1.0})
            for campo in ("lucro", "pl", "ativo", "credito"):
                r[campo] += v[campo]
            r["n"] += 1
            info = d["cadastro"].get(cod, {})
            if info.get("nome") and v["ativo"] >= r["_ativo"]:     # nome e tipo vêm da líder do grupo no ano
                r["_ativo"], r["nome"], r["tcb"] = v["ativo"], info["nome"], info.get("tcb", "")
        seg = {k: {"lucro": 0.0, "pl": 0.0, "n": 0} for k in ("bancos", "cooperativas", "nao_bancarias")}
        for g, r in reg.items():
            ser = series[g]
            # Banco que sai do cadastro (fusão) mantém o último nome conhecido: o Unibanco não aparece no
            # cadastro de dez/2008, mas tem resultado no ano.
            if r["nome"]:
                ser["nome"], ser["tcb"] = r["nome"], r["tcb"]
            tcb = r["tcb"] or ser["tcb"]
            s = SEGMENTO.get(tcb, (None, ""))[0]
            ser["segmento"], ser["tcb"] = s, tcb
            if s:
                seg[s]["lucro"] += r["lucro"]
                seg[s]["pl"] += r["pl"]
                seg[s]["n"] += 1
            ser["serie"][str(ano)] = {k: round(r[k], 2) for k in ("lucro", "pl", "ativo", "credito")}
        anos.append({"ano": ano, "parcial": d["parcial"], "periodos": d["periodos"],
                     "segmentos": {k: {"lucro": round(v["lucro"], 2), "pl": round(v["pl"], 2), "n": v["n"]}
                                   for k, v in seg.items()},
                     "total": {"lucro": round(sum(r["lucro"] for r in reg.values()), 2), "n": len(reg)}})
        log.info("%d: %sbancos R$ %.1f bi (%d grupos)", ano, "parcial " if d["parcial"] else "",
                 seg["bancos"]["lucro"] / 1e9, len(reg))
    for g, s in series.items():
        s["nome"] = s["nome"] or g
    return anos, dict(series), ultimo_fechado


def conferencia_prudencial(c: httpx.Client, ano: int) -> dict:
    """Mesmo ano pelo conglomerado prudencial (tipo 1), que só existe depois de 2014."""
    try:
        s1, s2 = resumo(c, ano * 100 + 6, TIPO_PRUDENCIAL), resumo(c, ano * 100 + 12, TIPO_PRUDENCIAL)
    except RuntimeError:
        return {}
    if not s1 or not s2:
        return {}
    cad = cadastro(c, ano * 100 + 12)
    bancos = 0.0
    for cod in set(s1) | set(s2):
        if SEGMENTO.get(cad.get(cod, {}).get("tcb", ""), (None,))[0] == "bancos":
            bancos += (s1.get(cod, {}).get("lucro") or 0.0) + (s2.get(cod, {}).get("lucro") or 0.0)
    return {"ano": ano, "lucro_bancos": round(bancos, 2)}


def conferencia_cvm(c: httpx.Client, ano: int, series: dict[str, dict]) -> dict:
    """
    Outra fonte, outro perímetro: o lucro consolidado que os bancos de capital aberto declaram à CVM (DFP).
    Não tem de bater com o IF.data e a diferença é o próprio recado — a holding na CVM inclui as empresas não
    financeiras do grupo e as operações no exterior; o IF.data mede o conglomerado financeiro no Brasil.
    """
    conteudo = _baixar_dfp(c, DFP.format(ano=ano), RAW / f"dfp_cia_aberta_{ano}.zip")
    if conteudo is None:
        return {}
    por_nome = {s["nome"]: s for s in series.values()}
    achados: dict[str, dict] = {}
    with zipfile.ZipFile(io.BytesIO(conteudo)) as zf:
        nomes = [n for n in zf.namelist() if "DRE_con" in n]
        if not nomes:
            return {}
        for linha in csv.DictReader(io.StringIO(zf.read(nomes[0]).decode("latin-1")), delimiter=";"):
            cnpj = re.sub(r"\D", "", linha["CNPJ_CIA"])[:8]
            alvo = CVM_BANCOS.get(cnpj)
            if not alvo or linha["ORDEM_EXERC"] != "ÚLTIMO":
                continue
            cd, valor = linha["CD_CONTA"], _num_cvm(linha["VL_CONTA"])
            if valor is None or not _e_linha_do_lucro(cd, linha["DS_CONTA"]):
                continue
            escala = 1000 if (linha.get("ESCALA_MOEDA") or "").upper().startswith("MIL") else 1
            reg = achados.setdefault(alvo[0], {"nome": alvo[1], "conta": ""})
            if cd >= reg["conta"]:                      # a de código maior é a que está mais embaixo na DRE
                reg.update(conta=cd, conta_ds=linha["DS_CONTA"], cvm=round(valor * escala, 2))
    saida = []
    for chave, reg in achados.items():
        ifd = (por_nome.get(chave, {}).get("serie") or {}).get(str(ano), {}).get("lucro")
        if ifd:
            saida.append({**reg, "ifdata": ifd,
                          "dif_pct": round(100 * (reg["cvm"] - ifd) / ifd, 1)})
    return {"ano": ano, "bancos": sorted(saida, key=lambda b: -b["ifdata"])} if saida else {}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    with httpx.Client(follow_redirects=True) as c:
        anos, series, ultimo_fechado = consolidar(ler_anos(c))
        indices = ipca(c)
        prudencial = conferencia_prudencial(c, ultimo_fechado)
        cvm = conferencia_cvm(c, ultimo_fechado, series)
    if not anos or ultimo_fechado < 2024:
        raise SystemExit(f"IF.data incompleto (último ano fechado: {ultimo_fechado})")
    base = ultimo_fechado
    deflator = {a: round(indices[base] / v, 6) for a, v in indices.items() if v and a <= base}

    fechados = [a["ano"] for a in anos if not a["parcial"]]
    for cod, s in series.items():
        s["lucro_real_acumulado"] = round(sum(v["lucro"] * deflator.get(int(a), 1.0)
                                              for a, v in s["serie"].items() if int(a) in fechados), 2)
        s["lucro_ultimo"] = s["serie"].get(str(base), {}).get("lucro", 0.0)
        s["anos"] = sorted(int(a) for a in s["serie"])
    maiores = sorted(series.items(), key=lambda kv: -kv[1]["lucro_real_acumulado"])[:TOP]

    # Concentração: fatia dos cinco maiores bancos do ano no lucro do segmento bancário. Em ano de prejuízo
    # grande o denominador encolhe e a fatia passa de 100% (2001 dá 10.651%) — a conta é uma divisão, não uma
    # medida de mercado. Esses anos ficam marcados e a página não os mostra.
    concentracao = []
    for a in anos:
        lucros = sorted((s["serie"][str(a["ano"])]["lucro"] for s in series.values()
                         if s.get("segmento") == "bancos" and str(a["ano"]) in s["serie"]), reverse=True)
        total = a["segmentos"]["bancos"]["lucro"]
        if total > 0 and len(lucros) >= 5:
            p = round(100 * sum(lucros[:5]) / total, 1)
            concentracao.append({"ano": a["ano"], "pct_cinco_maiores": p, **({"sem_sentido": True} if p > 100 else {})})

    out = {
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ano_base": base, "ano_inicio": ANO_INICIO,
        "deflator": {str(a): v for a, v in sorted(deflator.items())},
        "anos": anos,
        "concentracao": concentracao,
        "maiores": [{"cod": cod, "nome": s["nome"], "tcb": s["tcb"], "segmento": s.get("segmento"),
                     "tipo": SEGMENTO.get(s["tcb"], (None, ""))[1],
                     "lucro_real_acumulado": s["lucro_real_acumulado"], "lucro_ultimo": s["lucro_ultimo"],
                     "anos": s["anos"], "serie": s["serie"]} for cod, s in maiores],
        "conferencia_prudencial": prudencial,
        "conferencia_cvm": cvm,
        "fonte": {
            "ifdata": "Banco Central do Brasil, IF.data (API Olinda), relatório 1 — Resumo, conglomerado financeiro e instituições independentes",
            "ifdata_url": "https://www3.bcb.gov.br/ifdata/",
            "ipca": "IBGE, IPCA (SIDRA 1737), índice de dezembro de cada ano",
            "regra_lucro": "Lucro Líquido do IF.data acumula no semestre: lucro do ano = junho (jan–jun) + dezembro (jul–dez)",
            "regra_saldo": "Patrimônio Líquido, Ativo e Carteira de Crédito são saldos de 31 de dezembro",
            "limite_inicio": "O IF.data começa em março de 2000; não há série aberta de lucro por banco em 1988",
        },
    }
    PUB.mkdir(parents=True, exist_ok=True)
    (PUB / "bancos.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    log.info("bancos.json: %d anos, %d grupos no ranking, base %d", len(anos), len(out["maiores"]), base)


if __name__ == "__main__":
    main()
