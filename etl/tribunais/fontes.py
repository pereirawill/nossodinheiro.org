"""
Fontes de folha de pagamento dos tribunais superiores, uma função por tribunal.

Todos os tribunais publicam remuneração por pessoa (Resolução CNJ 102/2009), cada um no seu portal e no seu formato.
Cada adaptador aqui baixa **o ano inteiro** (só os meses já publicados) e devolve a MESMA lista de dicionários,
para o transform ser único:

    {"nome", "cargo", "lotacao", "bruto", "liquido", "origem_outro_orgao", "ano", "mes", "gabinete"}

- `bruto` = remuneração paga pelo tribunal **após a retenção do teto constitucional** e **sem indenizações**. É o mesmo
  conceito da coluna que o STF publica pronta ("Remuneração Bruta após o teto constitucional somada com outras verbas");
  nos tribunais que publicam o total antes do teto, somamos a retenção do teto (que vem negativa).
- `indenizacoes` = auxílio-alimentação, saúde, moradia, ajuda de custo e afins, que a Resolução CNJ 102/2009 manda
  publicar em coluna própria. **Fora do `bruto`**, porque a coluna que o STF publica não as inclui e somá-las em um
  tribunal e não no outro inviabilizaria a comparação (num mês de 2026 um ministro do STJ teve R$ 30,8 mil só aqui).
  Vão no JSON em campo separado e aparecem na página como linha própria.
- `origem_outro_orgao` = parcela paga pelo órgão de origem de quem é requisitado/cedido. **Não entra no custo do
  tribunal**, mas fica registrada para a página poder dizer quanto do gabinete é pago por fora.
- Nenhum adaptador guarda CPF: ou a fonte não publica, ou a coluna é descartada aqui.
"""

from __future__ import annotations

import csv
import io
import logging
import re
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import httpx

log = logging.getLogger("etl.tribunais")
UA = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
      "accept-language": "pt-BR,pt;q=0.9"}


def brl(v: str | None) -> float:
    """'95.068,85' → 95068.85; '-2.086,47' → -2086.47; vazio ou '0' → 0.0."""
    if not v:
        return 0.0
    t = re.sub(r"[^\d,\-.]", "", str(v)).strip()
    if not t or t in ("-", "."):
        return 0.0
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return 0.0


def _tentar(c: httpx.Client, url: str, **kw) -> httpx.Response | None:
    """GET com 3 tentativas; devolve None em 404 (mês não publicado)."""
    for tentativa in range(1, 4):
        r = c.get(url, **kw)
        if r.status_code == 200:
            return r
        if r.status_code == 404:
            return None
        log.warning("HTTP %s em %s (tentativa %d)", r.status_code, url, tentativa)
        time.sleep(4 * tentativa)
    return None


# --- TST ----------------------------------------------------------------------------------------------------------
# Portal próprio: `arquivos` lista as chaves disponíveis (JSON {chave: rótulo}); a chave "<ano>-<mês>-completo" devolve
# CSV (latin-1, ';'), com 3 linhas de cabeçalho antes da linha de colunas. O rótulo diz se é CSV ou PDF.
TST_LISTA = "https://transparencia-remuneracao.tst.jus.br/arquivos"
TST_ARQUIVO = "https://transparencia-remuneracao.tst.jus.br/arquivo"
TST_TOTAL = "Total de Rendimentos(5)"
TST_INDENIZ = "Indenizações(3)"
TST_TETO = "Retenção por Teto Constitucional(9)"
TST_LIQUIDO = "Rendimento Líquido(11)"
TST_ORIGEM = "Remuneração do órgão de origem(12)"


def tst(c: httpx.Client, ano: int, meses: list[int] | None = None) -> list[dict]:
    """Um CSV por mês; a lista `arquivos` já diz quais meses existem, então não há tentativa às cegas."""
    lista = _tentar(c, TST_LISTA)
    if lista is None:
        return []
    disponiveis = sorted(k for k in lista.json() if k.startswith(f"{ano}-") and k.endswith("-completo"))
    saida: list[dict] = []
    for chave in disponiveis:
        mes = int(chave.split("-")[1])
        if meses and mes not in meses:
            continue
        r = _tentar(c, TST_ARQUIVO, params={"data-referencia": chave})
        if r is None or not r.headers.get("content-type", "").startswith("text/csv"):
            log.warning("TST %s: resposta não é CSV", chave)
            continue
        linhas = r.content.decode("latin-1").splitlines()
        inicio = next((i for i, l in enumerate(linhas) if l.startswith("Nome;")), None)
        if inicio is None:
            log.warning("TST %s: CSV sem linha de cabeçalho", chave)
            continue
        n0 = len(saida)
        for row in csv.DictReader(io.StringIO("\n".join(linhas[inicio:])), delimiter=";"):
            nome = (row.get("Nome") or "").strip()
            if not nome:
                continue
            # o teto vem como desconto (negativo); o bruto após o teto é o total somado a ele
            saida.append({"nome": nome, "cargo": (row.get("Cargo") or "").strip(),
                          "lotacao": (row.get("Lotação") or "").strip(),
                          "bruto": round(brl(row.get(TST_TOTAL)) - brl(row.get(TST_INDENIZ))
                                         + min(0.0, brl(row.get(TST_TETO))), 2),
                          "indenizacoes": brl(row.get(TST_INDENIZ)),
                          "liquido": brl(row.get(TST_LIQUIDO)),
                          "origem_outro_orgao": brl(row.get(TST_ORIGEM)),
                          "ano": ano, "mes": mes})
        log.info("TST %d-%02d: %d pessoas na folha", ano, mes, len(saida) - n0)
    return saida


# --- STJ ----------------------------------------------------------------------------------------------------------
# Dados abertos (CKAN): UM CSV cumulativo com todos os meses desde jan/2020 (~107 MB), filtrado por AnoReferencia.
# O id do recurso muda se o STJ substituir o arquivo, então resolvemos pelo nome do pacote a cada execução.
# Layout do Anexo I da Resolução CNJ 215/2015. Não há coluna "após o teto": o equivalente ao número do STF é
# `Total de Créditos` + `Retenção por Teto Constitucional` (que vem negativa) — conferido: todo ministro com
# retenção cai exatamente no teto constitucional.
STJ_PACOTE = "https://dadosabertos.web.stj.jus.br/api/3/action/package_show?id=folha-de-pagamento-de-pessoal"
STJ_CACHE = Path("data/raw/stj_folha_pagamento.csv")


def _stj_csv(c: httpx.Client) -> Path:
    """Baixa o CSV cumulativo do STJ, reaproveitando o cache quando o arquivo publicado não mudou."""
    r = _tentar(c, STJ_PACOTE)
    if r is None:
        raise RuntimeError("STJ: catálogo de dados abertos não respondeu")
    recursos = r.json()["result"]["resources"]
    alvo = next((x for x in recursos if "folhadepagamento" in (x.get("name", "") + x.get("url", "")).lower()
                 and "dicion" not in x.get("name", "").lower()), None)
    if not alvo:
        raise RuntimeError("STJ: recurso FolhaDePagamento.csv não está no catálogo")
    marca = STJ_CACHE.with_suffix(".publicado")
    publicado = str(alvo.get("last_modified") or "")
    if STJ_CACHE.exists() and marca.exists() and marca.read_text(encoding="utf-8").strip() == publicado:
        log.info("STJ: cache em %s (publicado em %s)", STJ_CACHE, publicado)
        return STJ_CACHE
    STJ_CACHE.parent.mkdir(parents=True, exist_ok=True)
    log.info("STJ: baixando %s (publicado em %s)", alvo["url"], publicado)
    with c.stream("GET", alvo["url"]) as resp:
        resp.raise_for_status()
        with open(STJ_CACHE, "wb") as f:
            for pedaco in resp.iter_bytes(1 << 20):
                f.write(pedaco)
    marca.write_text(publicado, encoding="utf-8")
    log.info("STJ: %.1f MB em %s", STJ_CACHE.stat().st_size / 1e6, STJ_CACHE.name)
    return STJ_CACHE


STJ_CREDITOS = "Total de Créditos"
STJ_INDENIZ = "Indenizações"
STJ_TETO = "Retenção por Teto Constitucional"
STJ_LIQUIDO = "Rendimento Líquido"
STJ_ORIGEM = "Remuneração do Órgão de Origem"


def stj(c: httpx.Client, ano: int, meses: list[int] | None = None) -> list[dict]:
    caminho = _stj_csv(c)
    saida: list[dict] = []
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f, delimiter=","):
            if (row.get("AnoReferencia") or "").strip() != str(ano):
                continue
            mes = int((row.get("MesReferencia") or "0").strip() or 0)
            if not mes or (meses and mes not in meses):
                continue
            # Pensionistas são particulares (familiares) e não entram em nenhum número do painel: não guardamos o nome.
            vinculo = (row.get("CategoriaVinculo") or "").strip()
            if vinculo.lower().startswith("pensionista"):
                continue
            nome = (row.get("Nome") or "").strip()
            if not nome:
                continue
            saida.append({"nome": nome, "cargo": vinculo, "lotacao": (row.get("Lotação") or "").strip(),
                          "bruto": round(brl(row.get(STJ_CREDITOS)) - brl(row.get(STJ_INDENIZ))
                                         + min(0.0, brl(row.get(STJ_TETO))), 2),
                          "indenizacoes": brl(row.get(STJ_INDENIZ)),
                          "liquido": brl(row.get(STJ_LIQUIDO)),
                          "origem_outro_orgao": brl(row.get(STJ_ORIGEM)),
                          "matricula": (row.get("cd_matricula") or "").strip(),
                          "situacao": (row.get("Situacao") or "").strip(),
                          "ano": ano, "mes": mes})
    for mes in sorted({l["mes"] for l in saida}):
        log.info("STJ %d-%02d: %d pessoas na folha", ano, mes, sum(1 for l in saida if l["mes"] == mes))
    return saida


# --- STM ----------------------------------------------------------------------------------------------------------
# Formulário CodeIgniter: é preciso um GET antes para pegar cookie de sessão e o token CSRF (o NOME do campo é fixo,
# o valor rotaciona). O botão "Gerar CSV" devolve o mês inteiro em uma requisição. O CSV traz `Bruto` ANTES da
# retenção do teto constitucional, e a retenção não está no arquivo — está declarado em `coluna_valor` e na página.
STM_FORM = "https://www2.stm.jus.br/rem_web/index.php/ctrl_remuneracao"
STM_PESQUISA = STM_FORM + "/pesquisa/0"


def stm(c: httpx.Client, ano: int, meses: list[int] | None = None) -> list[dict]:
    r = _tentar(c, STM_FORM)
    if r is None:
        return []
    token = re.search(r'<input type="hidden"[^>]*name="([^"]+)"[^>]*value="([0-9a-f]{32})"', r.text)
    if not token:
        log.warning("STM: token CSRF não encontrado no formulário")
        return []
    saida: list[dict] = []
    for mes in meses or range(1, 13):
        dados = {"mes": str(mes), "ano": str(ano), "nome": "", "ctrl_input": "1", "de_tipo": "", "de_situacao": "",
                 "gerar_csv": "Gerar CSV", token.group(1): token.group(2)}
        resp = c.post(STM_PESQUISA, data=dados, headers={"referer": STM_FORM})
        if resp.status_code != 200 or "csv" not in resp.headers.get("content-type", ""):
            log.warning("STM %d-%02d: resposta %s (%s)", ano, mes, resp.status_code, resp.headers.get("content-type"))
            continue
        linhas = resp.content.decode("latin-1").splitlines()
        if len(linhas) < 2:
            log.info("STM %d-%02d: folha ainda não publicada", ano, mes)
            continue
        n0 = len(saida)
        for row in csv.DictReader(io.StringIO("\n".join(linhas)), delimiter=";"):
            nome = (row.get("Nome") or "").strip()
            if not nome:
                continue
            saida.append({"nome": nome, "cargo": (row.get("Cargo") or "").strip(),
                          "lotacao": (row.get("Lotação") or "").strip(),
                          "bruto": brl(row.get("Bruto")), "liquido": brl(row.get("Liquido")),
                          "indenizacoes": None,          # o CSV do STM não detalha as verbas
                          "origem_outro_orgao": 0.0, "ano": ano, "mes": mes})
        log.info("STM %d-%02d: %d pessoas na folha", ano, mes, len(saida) - n0)
    return saida


# --- TRF6 ---------------------------------------------------------------------------------------------------------
# XML do Anexo VIII (Oracle Reports), um por mês, listado na página de transparência. Não há template de URL: o mês
# vem do NOME do arquivo (o diretório é o do upload, e dois links do índice apontam para o mês errado). O desembargador
# aparece com lotação genérica "Tribunal Regional Federal da Sexta Região"; o gabinete existe só na lotação dos
# servidores, com o nome dele dentro da string e nem sempre igual — o casamento é por tokens do nome.
TRF6_INDICE = "https://portal.trf6.jus.br/institucional/transparencia/relatorios-cnj/anexo-viii/anexo-viii-trf6/"
MESES_PT = {"janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3, "abril": 4, "maio": 5, "junho": 6, "julho": 7,
            "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12}
PARTICULAS = {"de", "da", "do", "dos", "das", "e", "des", "desa", "gabinete", "junior", "filho", "neto", "sobrinho"}


def _tokens(nome: str) -> set[str]:
    sem_acento = "".join(ch for ch in unicodedata.normalize("NFD", nome.upper()) if unicodedata.category(ch) != "Mn")
    return {t for t in re.split(r"[^A-Z]+", sem_acento) if len(t) >= 3 and t.lower() not in PARTICULAS}


def casar_gabinete(nome: str, candidatos: dict[set, str] | list[tuple[set, str]]) -> str | None:
    """Gabinete cujo nome compartilha mais sobrenomes com o do magistrado. Exige 2 tokens (ou 1 com 6+ letras) e
    aceita diferença de grafia no fim da palavra (KUSCHEL × KUSCHELL), que acontece na fonte."""
    meus = _tokens(nome)
    melhor, placar = None, 0
    for toks, unidade in candidatos:
        pontos = 0
        for t in meus:
            if t in toks:
                pontos += 2
            elif any(o.startswith(t[:5]) or t.startswith(o[:5]) for o in toks if len(o) >= 5 and len(t) >= 5):
                pontos += 1
        if pontos > placar:
            melhor, placar = unidade, pontos
    return melhor if placar >= 3 else None


def trf6(c: httpx.Client, ano: int, meses: list[int] | None = None) -> list[dict]:
    import xml.etree.ElementTree as ET

    r = _tentar(c, TRF6_INDICE)
    if r is None:
        return []
    saida: list[dict] = []
    vistos: set[int] = set()
    for url in sorted(set(re.findall(r'href="([^"]+\.xml)"', r.text, re.I))):
        arquivo = url.rsplit("/", 1)[-1].lower()
        achado = re.search(r"(" + "|".join(MESES_PT) + r")[-_ ]*(\d{4})", arquivo)
        if not achado or int(achado.group(2)) != ano:
            continue
        mes = MESES_PT[achado.group(1)]
        if (meses and mes not in meses) or mes in vistos:
            continue
        resp = _tentar(c, url)
        if resp is None:
            continue
        try:
            raiz = ET.fromstring(resp.content)
        except ET.ParseError as e:
            log.warning("TRF6 %s: XML inválido (%s)", arquivo, e)
            continue
        pessoas = []
        for pessoa in raiz.iter("G_NOME"):
            d = {ch.tag: (ch.text or "").strip() for ch in pessoa}
            lot = next((v for k, v in d.items() if k.startswith("DECODE")), "")
            pessoas.append((d, lot))
        if not pessoas:
            continue
        # gabinetes dos desembargadores (os institucionais ficam de fora do casamento por nome)
        candidatos = [(_tokens(lot), lot) for _, lot in {(None, l) for _, l in pessoas}
                      if "GABINETE" in lot.upper() and _tokens(lot)]
        candidatos = [(t, l) for t, l in {(frozenset(t), l) for t, l in candidatos}]
        for d, lot in pessoas:
            cargo = d.get("CARGO", "")
            gabinete = None
            if "DESEMBARGADOR" in cargo.upper():
                gabinete = casar_gabinete(d.get("NOME", ""), candidatos)
                if not gabinete:
                    log.info("TRF6 %d-%02d: sem gabinete próprio na folha: %s", ano, mes, d.get("NOME"))
            total, teto, indeniz = brl(d.get("TOTAL")), brl(d.get("RETENCAOTETO")), brl(d.get("INDENIZACAO"))
            saida.append({"nome": d.get("NOME", "").strip(), "cargo": cargo, "lotacao": lot,
                          "gabinete": gabinete,
                          "bruto": round(total + min(0.0, teto) - indeniz, 2), "indenizacoes": indeniz,
                          "liquido": brl(d.get("RENDIMENTO_LIQUIDO")),
                          "origem_outro_orgao": brl(d.get("REMUNERACAOORIGEM")),
                          "ano": ano, "mes": mes})
        vistos.add(mes)
        log.info("TRF6 %d-%02d: %d pessoas na folha", ano, mes, len(pessoas))
    return saida


# --- TRF4 ---------------------------------------------------------------------------------------------------------
# Formulário do sistema interno (SEI/Infra): POST devolve 50 pessoas por página, com as verbas em linhas de detalhe.
# A paginação repete o POST com `hdnInfraPaginaAtual` (0 = primeira) e o hash dos critérios, sem o botão.
# O "Total de Créditos" do TRF4 **já vem abatido o teto constitucional** (conferido na página: a linha eventual soma
# 68.701,42 e o total mostra 55.710,49, exatamente a retenção a menos), então aqui só subtraímos as indenizações.
# O gabinete é identificado pelo CÓDIGO da lotação (`TRF4/GLIPPEL`), que o desembargador e a equipe dele compartilham.
TRF4_URL = "https://www.trf4.jus.br/trf4/controlador.php?acao=contracheque_transparencia"
TRF4_MESES = 4          # meses buscados (cada mês custa ~24 requisições por causa da paginação)


def _trf4_celulas(tr: str) -> list[str]:
    return [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", x)).replace("\xa0", " ").strip()
            for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]


def _trf4_chave(lotacao: str) -> str | None:
    """'TRF4/GLIPPEL/GGLIPPEL - Gabinete …' → 'TRF4/GLIPPEL' (o código que o desembargador e a equipe compartilham)."""
    codigo = lotacao.split(" - ")[0].strip()
    partes = [x for x in codigo.split("/") if x]
    return "/".join(partes[:2]) if len(partes) >= 2 else None


def _trf4_pagina(html: str) -> list[dict]:
    pessoas: list[dict] = []
    atual: dict | None = None
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S):
        cel = _trf4_celulas(tr)
        if len(cel) == 4 and cel[0] and "RENDIMENTOS" not in cel[0] and "(R$)" not in cel[0]:
            atual = {"nome": cel[0], "cargo": cel[1], "lotacao": cel[2], "creditos": 0.0, "indenizacoes": 0.0,
                     "liquido": 0.0}
            pessoas.append(atual)
        elif atual and len(cel) == 8 and cel[0] in ("Remuneração Mensal", "Pagamentos Eventuais"):
            atual["indenizacoes"] += brl(cel[4])
            atual["creditos"] += brl(cel[7])
        elif atual and len(cel) == 2 and cel[0].startswith("Total Recebido"):
            atual["liquido"] += brl(cel[1])
    return pessoas


def _trf4_consulta(c: httpx.Client, tipo: str, mes_str: str) -> list[dict]:
    base = {"selOrgao": "1", "selTipo": tipo, "selMesAno": mes_str}
    cab = {"referer": TRF4_URL, "content-type": "application/x-www-form-urlencoded"}
    r = c.post(TRF4_URL, data={**base, "btnPesquisar": " Pesquisar "}, headers=cab)
    if r.status_code != 200:
        log.warning("TRF4 %s tipo %s: HTTP %s", mes_str, tipo, r.status_code)
        return []
    pessoas = _trf4_pagina(r.text)
    if not pessoas:
        return []
    achado = re.search(r"([\d.]+)\s*registros", r.text)
    total = int(achado.group(1).replace(".", "")) if achado else len(pessoas)
    hash_ = re.search(r'name="hdnInfraHashCriterios"\s+value="([^"]+)"', r.text)
    paginas = -(-total // 50)
    if hash_ and paginas > 1:
        for pg in range(1, paginas):
            rp = c.post(TRF4_URL, data={**base, "hdnInfraPaginaAtual": str(pg),
                                        "hdnInfraHashCriterios": hash_.group(1)}, headers=cab)
            if rp.status_code != 200:
                log.warning("TRF4 %s tipo %s página %d: HTTP %s", mes_str, tipo, pg, rp.status_code)
                continue
            pessoas += _trf4_pagina(rp.text)
    if len(pessoas) < total * 0.95:
        log.warning("TRF4 %s tipo %s: %d de %d registros — paginação incompleta", mes_str, tipo, len(pessoas), total)
    return pessoas


def trf4(c: httpx.Client, ano: int, meses: list[int] | None = None) -> list[dict]:
    r = _tentar(c, TRF4_URL)
    if r is None:
        return []
    disponiveis = [m for m in re.findall(r'<option value="(\d{1,2}/\d{4})"', r.text) if m.endswith(f"/{ano}")]
    disponiveis.sort(key=lambda m: int(m.split("/")[0]), reverse=True)
    saida: list[dict] = []
    buscados = 0
    for mes_str in disponiveis:
        mes = int(mes_str.split("/")[0])
        if meses and mes not in meses:
            continue
        if buscados >= TRF4_MESES:
            break
        magistrados = _trf4_consulta(c, "3", mes_str)
        if not any("DESEMBARGADOR" in (p["cargo"] or "").upper() for p in magistrados):
            log.info("TRF4 %s: sem desembargador na folha de magistrados", mes_str)
            continue
        pessoas = magistrados + _trf4_consulta(c, "1", mes_str)
        for p in pessoas:
            saida.append({"nome": p["nome"], "cargo": p["cargo"], "lotacao": p["lotacao"],
                          "gabinete": _trf4_chave(p["lotacao"]),
                          "bruto": round(p["creditos"] - p["indenizacoes"], 2),
                          "indenizacoes": round(p["indenizacoes"], 2), "liquido": round(p["liquido"], 2),
                          "origem_outro_orgao": 0.0, "ano": ano, "mes": mes})
        buscados += 1
        log.info("TRF4 %d-%02d: %d pessoas na folha (%d magistrados)", ano, mes, len(pessoas), len(magistrados))
    return saida


@dataclass
class Tribunal:
    sigla: str
    nome: str
    baixar: Callable[..., list[dict]]          # (cliente, ano, meses|None) → linhas normalizadas
    cargos_do_magistrado: tuple[str, ...]      # valores da coluna Cargo que identificam quem tem gabinete próprio
    # Valores que identificam o magistrado já fora de exercício (aposentado, cedido). Vazio = os mesmos de cima.
    cargos_do_magistrado_inativo: tuple[str, ...] = ()
    # Magistrado convocado de outro tribunal que chefia gabinete (substitui quem está afastado ou cobre vaga).
    # Entra na tabela com rótulo próprio, mas NÃO conta na composição legal do tribunal.
    cargos_do_magistrado_convocado: tuple[str, ...] = ()
    rotulo_magistrado: str = "ministro"
    rotulo_plural: str = ""                    # vazio = rótulo + "s" (ministros); desembargador → desembargadores
    instancia: str = "superior"                # "superior" | "regional", para agrupar a comparação no índice
    composicao: int | None = None              # nº de cargos previstos em lei, para conferência
    # Lotações que NÃO são gabinete: aposentado, pensionista, cedido a outro órgão. Comparadas sem acento e em
    # maiúsculas. Quem está numa delas fica fora do custo por magistrado e entra na estatística separada.
    lotacao_fora_de_exercicio: tuple[str, ...] = ("INATIVO", "PENSIONISTA", "PENSIONISTA CIVIL",
                                                 "A DISPOSICAO DE OUTRO ORGAO", "CEDIDO", "LICENCA SEM VENCIMENTOS",
                                                 "EXONERADO", "APOSENTADO", "FALECIDO")
    # O magistrado em exercício tem gabinete próprio; o nome da lotação precisa casar com isto.
    padrao_gabinete: str = r"GABINETE|GAB\."
    fonte: str = ""
    url: str = ""
    coluna_valor: str = ""
    observacao: str = ""
    aliases_gabinete: dict[str, str] = field(default_factory=dict)


TRIBUNAIS: dict[str, Tribunal] = {
    "tst": Tribunal(
        sigla="TST", nome="Tribunal Superior do Trabalho", baixar=tst,
        cargos_do_magistrado=("MINISTRO", "MINISTRO CLASSISTA"),
        cargos_do_magistrado_convocado=("MAGISTRADO CONVOCADO AUXILIAR", "DESEMBARGADOR EM SUBSTITUICAO",
                                        "DESEMBARGADOR CONVOCADO"), composicao=27,
        fonte="TST — Transparência, Remuneração (transparencia-remuneracao.tst.jus.br), exportação CSV mensal",
        url="https://transparencia-remuneracao.tst.jus.br/",
        coluna_valor="Total de Rendimentos, sem indenizações, menos a Retenção por Teto Constitucional",
        observacao="O CSV cobre o TST. Os 24 Tribunais Regionais do Trabalho publicam folha em portais próprios e "
                   "não estão aqui; o total da Justiça do Trabalho no orçamento inclui todos.",
    ),
    "stj": Tribunal(
        sigla="STJ", nome="Superior Tribunal de Justiça", baixar=stj,
        cargos_do_magistrado=("MINISTRO ATIVO",), cargos_do_magistrado_inativo=("MINISTRO APOSENTADO",),
        cargos_do_magistrado_convocado=("MAGISTRADO CONVOCADO",), composicao=33,
        fonte="STJ — Dados Abertos, Folha de Pagamento de Pessoal (dadosabertos.web.stj.jus.br), CSV mensal desde 2020",
        url="https://dadosabertos.web.stj.jus.br/dataset/folha-de-pagamento-de-pessoal",
        coluna_valor="Total de Créditos, sem indenizações, menos a Retenção por Teto Constitucional",
        observacao="Pensionistas, que são familiares e não servidores, ficam fora de todos os números desta página. "
                   "A estrutura da Presidência do STJ é dividida em várias unidades, listadas fora do custo por ministro.",
    ),
    "stm": Tribunal(
        sigla="STM", nome="Superior Tribunal Militar", baixar=stm,
        cargos_do_magistrado=("MINISTRO DO SUPERIOR TRIBUNAL MILITAR",), composicao=15,
        padrao_gabinete=r"GAB MIN|GABINETE|PRESIDENCIA",
        fonte="STM — Remuneração e proventos (www2.stm.jus.br/rem_web), exportação CSV mensal",
        url="https://www.stm.jus.br/transparencia-e-prestacao-de-contas/gestao-de-pessoas",
        coluna_valor="Bruto (inclui indenizações e é antes da retenção do teto; o CSV do STM não detalha as verbas)",
        observacao="O CSV do STM traz um único valor bruto, antes da retenção do teto e já com indenizações dentro; "
                   "nos outros tribunais a indenização sai do valor comparável. Para quem bate no teto isso superestima "
                   "o número em torno de 3%. O presidente e o vice aparecem "
                   "com a Presidência e a Vice-Presidência, que acumulam estrutura institucional.",
    ),
    "trf6": Tribunal(
        sigla="TRF6", nome="Tribunal Regional Federal da 6ª Região", baixar=trf6,
        cargos_do_magistrado=("DESEMBARGADOR FEDERAL",), composicao=18,
        rotulo_magistrado="desembargador", rotulo_plural="desembargadores", instancia="regional",
        fonte="TRF6 — Transparência, Anexo VIII da Resolução CNJ 102/2009 (portal.trf6.jus.br), XML mensal",
        url="https://portal.trf6.jus.br/institucional/transparencia/relatorios-cnj/anexo-viii/anexo-viii-trf6/",
        coluna_valor="Total de créditos, sem indenizações, menos a Retenção por Teto Constitucional",
        observacao="No XML do TRF6 o desembargador aparece com lotação genérica do tribunal: o gabinete dele é "
                   "identificado pelo nome na lotação dos servidores, e a grafia nem sempre é igual. Quem exerce a "
                   "Presidência, a Vice e a Corregedoria não tem gabinete próprio na folha e aparece sem gabinete.",
    ),
    "trf4": Tribunal(
        sigla="TRF4", nome="Tribunal Regional Federal da 4ª Região", baixar=trf4,
        cargos_do_magistrado=("DESEMBARGADOR FEDERAL - TRF",), composicao=39,
        rotulo_magistrado="desembargador", rotulo_plural="desembargadores", instancia="regional",
        fonte="TRF4 — Transparência, contracheque (www.trf4.jus.br), consulta mensal por órgão e tipo",
        url="https://www.trf4.jus.br/trf4/controlador.php?acao=pagina_visualizar&id_pagina=2037",
        coluna_valor="Total de Créditos (já abatido o teto constitucional), sem indenizações",
        observacao="A consulta do TRF4 devolve 50 pessoas por página, então buscamos os quatro meses mais recentes com "
                   "folha de magistrados. O gabinete é casado pelo código da lotação, que o desembargador e a equipe "
                   "dele compartilham. A folha de magistrados do sistema para em abril de 2026, embora a de servidores "
                   "siga atualizada — é lacuna da fonte.",
    ),
}
