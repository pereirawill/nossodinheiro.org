"""
Lucro de cada grupo financeiro desde o Plano Real, pelos balancetes do Cosif.

O IF.data (ver `extract.py`) começa em março de 2000. Antes disso o Banco Central publica os **balancetes**:
um arquivo por data-base com todas as contas de cada instituição (documento 4010) e de cada conglomerado
financeiro (documento **4040**), em `bcb.gov.br/content/estabilidadefinanceira/cosif/`. O índice de arquivos
vem da própria API do site (`Documentos/byListGuid`), porque o nome do arquivo muda ao longo do tempo
(`.ZIP`, `.csv.zip`, e um `.zip.csv.zip`).

Três coisas que esta parte do painel resolve, e uma que ela não resolve:

1. **Começa em dezembro de 1994.** Os arquivos existem desde julho de 1988, mas até junho de 1994 os valores
   estão em cruzeiro real — o patrimônio do Banco do Brasil aparece como 17.692 bilhões em jun/1994 e como
   R$ 5,75 bilhões em dez/1994. A primeira data-base em reais é dez/1994, o primeiro semestre fechado depois do
   Plano Real.
2. **A conta do lucro é a mesma do IF.data**: soma das contas de resultado credoras (7) e devedoras (8). O
   Banco Central publica a fórmula no próprio IF.data, e ela tem um terceiro termo: menos a conta 8.1.9.55.00-2,
   "Juros ao Capital". Essa conta é de 4º nível e **não existe nos arquivos públicos**, que vão até o 3º.
3. **O tamanho dessa diferença está medido**, conglomerado a conglomerado, em `convergencia`: o balancete dá de
   52% a 83% do lucro que o BC publica entre 2000 e 2018 e **exatamente 100%** em 2019, 2020 e 2021 — quando a
   conta de juros ao capital saiu do Cosif. Por isso o número de 1996 a 1999 é um **piso**: é o lucro depois dos
   juros sobre capital próprio. Em 1994 e 1995 não há essa ressalva, porque o JCP só passou a existir com a Lei
   9.249, de dezembro de 1995.

**O que não dá**: o total do sistema antes de 2000. O BC não publica, nessa época, quais bancos pertencem a
qual grupo, e somar banco a banco conta duas vezes o resultado que a controladora reconhece da controlada —
medimos +17% a +36% nos anos em que dá para comparar. Por isso esta parte do painel é por **grupo**, e o total
continua começando em 2000.
"""

from __future__ import annotations

import collections
import io
import json
import logging
import re
import zipfile
from pathlib import Path

import httpx

log = logging.getLogger("etl.bancos.cosif")
RAW = Path("data/raw/cosif_congl")
INDICE = ("https://www.bcb.gov.br/api/servico/sitebcb/Documentos/byListGuid?tronco=estabilidadefinanceira"
          "&guidLista=a11917e4-c729-4259-bd4e-0266827b6acd&ordem=DataDocumento%20desc"
          "&pasta=/Conglomerados-financeiros")
SITE = "https://www.bcb.gov.br"
UA = {"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}
# Contas de resultado, nas duas gerações do plano de contas (o Cosif passou a códigos de 10 dígitos em 2023).
RESULTADO = {"70000009", "80000006", "7000000003", "8000000002"}
# Conta 8.9.1 "apuração de resultado". Até jun/1995 o balancete de encerramento vem com as contas de resultado
# já zeradas (7 e 8 se anulam) e o lucro do semestre fica aqui, com o sinal trocado — é assim que se lê o
# Itaú de dez/1994 (R$ 126,1 mi) ou o Bradesco (R$ 186,8 mi).
APURACAO = {"89100000", "8910000004"}
TOLERANCIA = 1000.0      # em reais: abaixo disso, a conta está zerada
PRIMEIRA = 199412          # dez/1994: a primeira data-base em reais
ULTIMO_HISTORICO = 1999    # de 2000 em diante o painel usa o IF.data
CONFERENCIA = (2000, 2005, 2010, 2015, 2018, 2019, 2020, 2021)


def indice(c: httpx.Client) -> dict[int, str]:
    """{AAAAMM: url} dos balancetes de conglomerado financeiro publicados pelo BC."""
    r = c.get(INDICE, headers=UA, timeout=120.0)
    r.raise_for_status()
    fora = {}
    for x in r.json()["conteudo"]:
        m = re.match(r"(\d{6})", x.get("Nome") or "")
        if m and x.get("Url"):
            fora[int(m.group(1))] = SITE + x["Url"]
    return fora


def _csv(c: httpx.Client, anomes: int, url: str) -> list[str]:
    arq = RAW / f"{anomes}.ZIP"
    if not arq.exists() or arq.stat().st_size < 1000:
        r = c.get(url, headers=UA, timeout=300.0)
        r.raise_for_status()
        RAW.mkdir(parents=True, exist_ok=True)
        arq.write_bytes(r.content)
    b = arq.read_bytes()
    if b[:2] == b"PK":                      # alguns períodos vêm como CSV solto, outros zipados
        with zipfile.ZipFile(io.BytesIO(b)) as zf:
            b = zf.read(zf.namelist()[0])
    return b.decode("latin-1").splitlines()


def lucro_por_grupo(c: httpx.Client, anomes: int, url: str) -> tuple[dict[str, float], dict[str, str], list[str]]:
    """
    Lucro do semestre e nome de cada conglomerado financeiro na data-base.

    Devolve também os grupos que ficaram **sem leitura**: os que trazem as contas de resultado e a conta de
    apuração preenchidas ao mesmo tempo (13 a 18 grupos em dez/1994 e jun/1995). Nesses não dá para saber se os
    dois valores se somam ou se repetem, e preferimos não publicar número a publicar um que pode estar dobrado.
    """
    linhas = _csv(c, anomes, url)
    i = next(k for k, l in enumerate(linhas[:10]) if "CONTA" in l.upper())
    campos = [x.strip().upper().lstrip("#") for x in linhas[i].lstrip("#").split(";")]
    resultado: dict[str, float] = collections.defaultdict(float)
    apuracao: dict[str, float] = collections.defaultdict(float)
    nomes: dict[str, str] = {}
    for linha in linhas[i + 1:]:
        p = [x.strip() for x in linha.split(";")]
        if len(p) != len(campos):
            continue
        r = dict(zip(campos, p))
        if r.get("DOCUMENTO") != "4040":     # o arquivo traz também o balanço semestral (4046)
            continue
        # o formato antigo identifica o grupo por "COD.CONGLOMERADO" (00010014); o novo, por "COD_CONGL"
        # (C0010014), que é o mesmo código do IF.data — a diferença é só o prefixo.
        cod = r.get("COD_CONGL") or ("C" + r["COD.CONGLOMERADO"][1:] if r.get("COD.CONGLOMERADO") else "")
        if not cod:
            continue
        nomes[cod] = (r.get("NOME_CONGL") or r.get("NOME CONGLOMERADO") or "").strip()
        conta = r["CONTA"].lstrip("0")
        if conta in RESULTADO:
            resultado[cod] += float(r["SALDO"].replace(",", "."))
        elif conta in APURACAO:
            apuracao[cod] += float(r["SALDO"].replace(",", "."))
    lucro: dict[str, float] = {}
    sem_leitura: list[str] = []
    for cod in set(resultado) | set(apuracao):
        pelo_resultado = abs(resultado.get(cod, 0.0)) > TOLERANCIA
        pela_apuracao = abs(apuracao.get(cod, 0.0)) > TOLERANCIA
        if pelo_resultado and pela_apuracao:
            sem_leitura.append(cod)
        elif pela_apuracao:
            lucro[cod] = -apuracao[cod]          # balancete já encerrado
        else:
            lucro[cod] = resultado.get(cod, 0.0)
    return lucro, nomes, sem_leitura


def serie(c: httpx.Client, ate: int = ULTIMO_HISTORICO) -> dict:
    """Série anual por grupo de dez/1994 ao último ano pedido, mais a conferência contra o IF.data."""
    arquivos = indice(c)
    anos: dict[str, dict[int, float]] = collections.defaultdict(dict)
    nomes: dict[str, str] = {}
    meio_ano: list[int] = []      # anos em que só um semestre está publicado em reais
    perdidos: dict[int, int] = {}
    for ano in range(PRIMEIRA // 100, ate + 1):
        total: dict[str, float] = collections.defaultdict(float)
        completo: dict[str, int] = collections.Counter()
        periodos = [p for p in (ano * 100 + 6, ano * 100 + 12) if p >= PRIMEIRA and p in arquivos]
        if not periodos:
            continue
        fora: set[str] = set()
        for p in periodos:
            lucro, nome, sem = lucro_por_grupo(c, p, arquivos[p])
            nomes.update({k: v for k, v in nome.items() if v})
            fora.update(sem)
            for k, v in lucro.items():
                total[k] += v
                completo[k] += 1
        if len(periodos) == 1:
            meio_ano.append(ano)
        perdidos[ano] = len(fora)
        for k, v in total.items():
            # um grupo que só tem um dos dois semestres do ano não entra: seria meio ano contado como ano
            if k not in fora and completo[k] == len(periodos):
                anos[k][ano] = round(v, 2)
        log.info("%d: %d grupos financeiros, lucro somado R$ %.2f bi (%d semestre(s), %d sem leitura)",
                 ano, len(total), sum(total.values()) / 1e9, len(periodos), len(fora))
    grupos = [{"cod": k, "nome": nomes.get(k, k), "serie": {str(a): v for a, v in sorted(s.items())}}
              for k, s in anos.items()]
    return {"ano_inicio": PRIMEIRA // 100, "ano_fim": ate, "primeira_base": PRIMEIRA, "grupos": grupos,
            "meio_ano": meio_ano, "sem_leitura_por_ano": perdidos}


def convergencia(c: httpx.Client, ifdata_por_ano: dict[int, dict[str, float]]) -> list[dict]:
    """
    Quanto o balancete dá, em relação ao que o BC publica como lucro líquido, nos mesmos conglomerados.
    É a medida do termo que falta (juros ao capital, conta de 4º nível que os arquivos públicos não trazem).
    """
    arquivos = indice(c)
    fora = []
    for ano in CONFERENCIA:
        if ano not in ifdata_por_ano:
            continue
        cosif: dict[str, float] = collections.defaultdict(float)
        semestres: dict[str, int] = collections.Counter()
        for mes in (6, 12):
            p = ano * 100 + mes
            if p in arquivos:
                lucro, _, _sem = lucro_por_grupo(c, p, arquivos[p])
                for k, v in lucro.items():
                    cosif[k] += v
                    semestres[k] += 1
        # só os grupos que existem dos dois lados e têm os dois semestres no balancete, senão a conta compara
        # um ano inteiro do IF.data com meio ano do Cosif e a razão cai sem que nada tenha mudado
        comuns = [k for k in cosif if k in ifdata_por_ano[ano] and semestres[k] == 2]
        soma_if = sum(ifdata_por_ano[ano][k] for k in comuns)
        if len(comuns) < 20 or soma_if <= 0:
            continue
        soma_cosif = sum(cosif[k] for k in comuns)
        fora.append({"ano": ano, "grupos": len(comuns), "cosif": round(soma_cosif, 2),
                     "ifdata": round(soma_if, 2), "razao": round(soma_cosif / soma_if, 3)})
    return fora
