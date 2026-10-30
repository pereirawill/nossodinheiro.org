#!/usr/bin/env python3
"""
Checagem mecânica do site, sem modelo nenhum: roda em segundos e custa zero.

    python tools/checar_site.py              # relatório no terminal
    python tools/checar_site.py --json       # para outro programa consumir
    make checar

Pega a metade do trabalho que é regra fixa — verbete de glossário que não existe, painel sem entrada no
catálogo de dados, link interno quebrado, JSON fora de sincronia, workflow que não dispara o deploy, campo lido
de um JSON que não tem esse campo. O que exige julgamento (frase que atribui causa, número sem fonte, ressalva
que sumiu) fica para a varredura com modelo, descrita em `docs/revisao-regras.md`.

Saída: cada achado com arquivo:linha, a regra violada e o que fazer. Sai com código 1 se houver ERRO.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGINAS = RAIZ / "site/src/pages"
LIB = RAIZ / "site/src/lib"
COMPONENTES = RAIZ / "site/src/components"
DADOS_SITE = RAIZ / "site/public/data"
DADOS_PUB = RAIZ / "data/public"
WORKFLOWS = RAIZ / ".github/workflows"

# Arquivos gerados por máquina: não são revisados nem contam como fonte de erro.
IGNORAR = {"mapa-uf.ts"}
# Rotas que existem fora de src/pages (Cloudflare Functions, arquivos estáticos, âncoras do próprio site).
ROTAS_EXTERNAS = {"/sitemap-index.xml", "/robots.txt", "/og.png", "/sugestoes/obrigado/"}

ERRO, AVISO, NOTA = "ERRO", "aviso", "nota"


class Achados:
    def __init__(self) -> None:
        self.itens: list[dict] = []

    def add(self, nivel: str, regra: str, onde: str, o_que: str, fazer: str = "") -> None:
        self.itens.append({"nivel": nivel, "regra": regra, "onde": onde, "o_que": o_que, "fazer": fazer})

    @property
    def erros(self) -> int:
        return sum(1 for i in self.itens if i["nivel"] == ERRO)


def arquivos(*pastas: Path, sufixos=(".astro", ".md", ".ts")) -> list[Path]:
    fora = []
    for p in pastas:
        for f in sorted(p.rglob("*")):
            if f.is_file() and f.suffix in sufixos and f.name not in IGNORAR:
                fora.append(f)
    return fora


def rel(f: Path) -> str:
    return str(f.relative_to(RAIZ))


def linha_de(texto: str, pos: int) -> int:
    return texto.count("\n", 0, pos) + 1


# ------------------------------------------------------------------ checagens


def checar_glossario(a: Achados) -> None:
    """Todo <Termo t="x"> e todo item de <Glossario termos={[...]}> precisa existir em glossario.ts."""
    fonte = (LIB / "glossario.ts").read_text(encoding="utf-8")
    definidos = set(re.findall(r"^\s{2}([a-z0-9_]+):\s*\{", fonte, re.M))
    usados: set[str] = set()
    for f in arquivos(PAGINAS, COMPONENTES):
        texto = f.read_text(encoding="utf-8")
        for m in re.finditer(r'<Termo\s+t="([^"]+)"', texto):
            usados.add(m.group(1))
            if m.group(1) not in definidos:
                a.add(ERRO, "glossario", f"{rel(f)}:{linha_de(texto, m.start())}",
                      f'<Termo t="{m.group(1)}"> não existe no glossário',
                      "criar o verbete em site/src/lib/glossario.ts ou corrigir o nome")
        for m in re.finditer(r"<Glossario\s+termos=\{\[(.*?)\]\}", texto, re.S):
            for termo in re.findall(r'"([a-z0-9_]+)"', m.group(1)):
                usados.add(termo)
                if termo not in definidos:
                    a.add(ERRO, "glossario", f"{rel(f)}:{linha_de(texto, m.start())}",
                          f'"{termo}" na lista do rodapé não existe no glossário', "criar o verbete ou tirar da lista")
    for termo in sorted(definidos - usados):
        a.add(NOTA, "glossario-orfao", "site/src/lib/glossario.ts", f'"{termo}" está definido e nunca é usado',
              "usar em alguma página ou remover")


def rotas_do_site() -> set[str]:
    rotas = {"/"}
    for f in PAGINAS.rglob("*"):
        if not f.is_file() or f.suffix not in (".astro", ".md"):
            continue
        r = "/" + str(f.relative_to(PAGINAS)).replace("index.astro", "").replace("index.md", "")
        r = re.sub(r"\.(astro|md)$", "/", r).replace("//", "/")
        rotas.add(r if r.endswith("/") else r + "/")
    return rotas


def checar_links(a: Achados) -> None:
    """Link interno que não corresponde a nenhuma rota (rota dinâmica [x] vira padrão)."""
    rotas = rotas_do_site()
    dinamicas = [re.compile("^" + re.sub(r"\[[^\]]+\]", "[^/]+", r) + "$") for r in rotas if "[" in r]
    fixas = {r for r in rotas if "[" not in r} | ROTAS_EXTERNAS
    for f in arquivos(PAGINAS, COMPONENTES, LIB):
        texto = f.read_text(encoding="utf-8")
        for m in re.finditer(r'href="(/[^"#?]*)"', texto):
            destino = m.group(1)
            if not destino.endswith("/") and "." not in destino.rsplit("/", 1)[-1]:
                destino += "/"
            if destino in fixas or any(d.match(destino) for d in dinamicas):
                continue
            if destino.startswith("/data/") and (DADOS_SITE / destino.removeprefix("/data/")).exists():
                continue          # arquivo publicado, não rota
            if destino.startswith(("/deputados/", "/senadores/", "/municipios/", "/judiciario/")):
                continue          # rotas geradas por getStaticPaths a partir dos dados
            a.add(ERRO, "link", f"{rel(f)}:{linha_de(texto, m.start())}",
                  f"link para {destino}, que não é rota do site", "corrigir o endereço ou criar a página")


def checar_datasets(a: Achados) -> None:
    """Painel (página com JSON próprio) tem de ter entrada em datasets.ts, que alimenta /dados/ e o JSON-LD."""
    fonte = (LIB / "datasets.ts").read_text(encoding="utf-8")
    slugs = set(re.findall(r'slug:\s*"([^"]+)"', fonte))
    citados = set(re.findall(r'"([a-z0-9_]+\.json)"', fonte))
    for f in sorted(PAGINAS.rglob("index.astro")) + sorted(PAGINAS.glob("*.astro")):
        texto = f.read_text(encoding="utf-8")
        if "public/data/" not in texto:
            continue
        rota = "/" + str(f.relative_to(PAGINAS)).replace("index.astro", "")
        rota = re.sub(r"\.astro$", "/", rota).replace("//", "/")
        if rota in ("/", "/conferir/", "/dados/", "/agora/", "/beneficios/"):
            continue              # não são painéis de dado próprio: leem os JSONs dos outros
        if rota not in slugs:
            a.add(AVISO, "datasets", rel(f), f"painel {rota} não tem entrada em datasets.ts",
                  "acrescentar nome, descrição, arquivos, fontes, período e cadência")
    publicados = {f.name for f in DADOS_SITE.glob("*.json")}
    for arq in sorted(publicados - citados):
        if re.search(r"_(19|20)\d\d\.json$", arq):
            continue              # arquivos por ano são citados pelo nome-base
        a.add(NOTA, "datasets", "site/src/lib/datasets.ts", f"{arq} está publicado e não aparece no catálogo",
              "citar em `arquivos` do painel correspondente")


def checar_json(a: Achados) -> None:
    """JSON importado existe, está igual nas duas pastas e tem os campos de primeiro nível que a página lê."""
    for arq in sorted(DADOS_SITE.glob("*.json")):
        if arq.name == "fotos.json":
            continue              # manifesto das fotos: o ETL grava direto em site/public
        par = DADOS_PUB / arq.name
        if not par.exists():
            a.add(AVISO, "json-sync", f"data/public/{arq.name}", "existe em site/public/data e não em data/public",
                  "rodar o ETL do painel ou remover o arquivo órfão")
        elif par.read_bytes() != arq.read_bytes():
            a.add(ERRO, "json-sync", f"site/public/data/{arq.name}",
                  "o JSON publicado está diferente do gerado em data/public",
                  "copiar: cp data/public/<arquivo> site/public/data/")
    for f in arquivos(PAGINAS, COMPONENTES):
        texto = f.read_text(encoding="utf-8")
        for m in re.finditer(r'import\s+(\w+)\s+from\s+"[^"]*public/data/([a-z0-9_]+\.json)"', texto):
            nome, arq = m.group(1), m.group(2)
            caminho = DADOS_SITE / arq
            if not caminho.exists():
                a.add(ERRO, "json", f"{rel(f)}:{linha_de(texto, m.start())}",
                      f"importa {arq}, que não existe em site/public/data",
                      "gerar o arquivo pelo ETL ou corrigir o import")
                continue
            try:
                dados = json.loads(caminho.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                a.add(ERRO, "json", f"site/public/data/{arq}", f"JSON inválido: {e}", "regerar pelo ETL")
                continue
            if not isinstance(dados, dict):
                continue
            # `(?<![\w.])` evita casar o nome dentro de uma cadeia (bAno.segmentos.bancos.lucro) e o
            # próprio import (".../bancos.json"); `json` nunca é campo.
            acesso = re.compile(rf"(?:\(\s*{nome}\s+as\s+any\s*\)|(?<![\w.\"/]){nome})\.([a-z_][a-z0-9_]*)")
            for mm in acesso.finditer(texto):
                campo = mm.group(1)
                if campo == "json" or texto[:mm.start()].rsplit("\n", 1)[-1].lstrip().startswith("import"):
                    continue
                if campo not in dados:
                    a.add(ERRO, "json-campo", f"{rel(f)}:{linha_de(texto, mm.start())}",
                          f"lê {nome}.{campo}, que não existe em {arq}",
                          "conferir o nome do campo no JSON ou atualizar o ETL")


def checar_workflows(a: Achados) -> None:
    """Todo ETL tem workflow, e todo workflow de ETL dispara o deploy (senão o dado entra e o site não sai)."""
    deploy = (WORKFLOWS / "deploy.yml").read_text(encoding="utf-8")
    nomes_no_deploy = set(re.findall(r'"(ETL [^"]+)"', deploy))
    nomes_dos_workflows = set()
    for wf in sorted(WORKFLOWS.glob("*.yml")):
        if not re.search(r"^name:\s*ETL ", wf.read_text(encoding="utf-8"), re.M):
            continue
        texto = wf.read_text(encoding="utf-8")
        m = re.search(r"^name:\s*(.+)$", texto, re.M)
        if not m:
            a.add(ERRO, "workflow", rel(wf), "workflow sem `name:`", "dar um nome ao workflow")
            continue
        nome = m.group(1).strip()
        nomes_dos_workflows.add(nome)
        if nome not in nomes_no_deploy:
            a.add(ERRO, "workflow", rel(wf),
                  f'"{nome}" não está na lista de gatilhos do deploy.yml',
                  "acrescentar o nome exato em workflows: [...] do deploy.yml, senão o dado é commitado e o site não é publicado")
    for nome in sorted(nomes_no_deploy - nomes_dos_workflows):
        a.add(AVISO, "workflow", ".github/workflows/deploy.yml",
              f'"{nome}" dispara o deploy mas não existe mais como workflow', "remover da lista")
    for mod in sorted(p for p in (RAIZ / "etl").iterdir() if p.is_dir() and (p / "extract.py").exists()):
        if not any(mod.name in wf.read_text(encoding="utf-8") for wf in WORKFLOWS.glob("*.yml")):
            a.add(AVISO, "workflow", f"etl/{mod.name}/", "ETL sem workflow que o execute",
                  "criar .github/workflows/etl-<painel>.yml ou documentar por que é manual")


CADENCIA_DIAS = {"diaria": 3, "semanal": 10, "mensal": 45, "trimestral": 130, "anual": 400}


def checar_frescor(a: Achados, limite_dias: int = 45) -> None:
    """JSON parado há muito tempo: ou o ETL está quebrado em silêncio, ou a fonte parou de publicar."""
    hoje = datetime.now(timezone.utc)
    for arq in sorted(DADOS_SITE.glob("*.json")):
        try:
            dados = json.loads(arq.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(dados, dict):
            continue
        quando = dados.get("gerado_em_utc")
        if not quando:
            continue
        try:
            d = datetime.fromisoformat(quando.replace("Z", "+00:00"))
        except ValueError:
            continue
        idade = (hoje - d).days
        if idade > limite_dias:
            a.add(AVISO, "frescor", f"site/public/data/{arq.name}",
                  f"gerado há {idade} dias ({d:%d/%m/%Y})",
                  "conferir se o workflow do painel está passando e se a fonte ainda publica")


def checar_numeros_fixos(a: Achados) -> None:
    """
    Valor em reais escrito à mão no meio da página. Nem todo caso é erro — há constantes declaradas em .ts com
    fonte —, mas todo caso precisa ter sido conferido, e é isso que a varredura com modelo vai olhar.
    """
    padrao = re.compile(r"R\$\s?\d[\d.,]*\s*(?:mil|mi|bi|tri)?\b")
    for f in sorted(PAGINAS.rglob("*.astro")):
        texto = f.read_text(encoding="utf-8")
        for m in padrao.finditer(texto):
            inicio = texto.rfind("\n", 0, m.start())
            trecho = texto[inicio:m.start()]
            if "{" in trecho and "}" not in trecho.split("{")[-1]:
                continue          # está dentro de uma expressão: o número vem do JSON
            a.add(NOTA, "numero-fixo", f"{rel(f)}:{linha_de(texto, m.start())}",
                  f'"{m.group(0).strip()}" está escrito no HTML',
                  "ou vem do JSON, ou é constante declarada com fonte e data — conferir qual")


def checar_metodologia(a: Achados) -> None:
    """Painel no menu precisa de seção na metodologia (a página promete isso no rodapé de cada painel)."""
    base = (RAIZ / "site/src/layouts/Base.astro").read_text(encoding="utf-8")
    m = re.search(r"const nav = \[(.*?)\n\];", base, re.S)
    if not m:
        a.add(ERRO, "menu", "site/src/layouts/Base.astro", "não achei o `const nav`", "conferir o layout")
        return
    itens = re.findall(r'\["([^"]+)",\s*"([^"]+)"\]', m.group(1))
    rotas = rotas_do_site()
    metodologia = (PAGINAS / "metodologia.md").read_text(encoding="utf-8").lower()
    for rota, rotulo in itens:
        if rota not in rotas and rota != "/":
            a.add(ERRO, "menu", "site/src/layouts/Base.astro", f"menu aponta para {rota}, que não é rota do site",
                  "corrigir o endereço no nav")
        if rota in ("/", "/metodologia/", "/sobre/", "/dados/", "/agora/", "/sugestoes/"):
            continue
        if rotulo.lower().split()[0] not in metodologia:
            a.add(AVISO, "metodologia", "site/src/pages/metodologia.md",
                  f'o painel "{rotulo}" não aparece na metodologia',
                  "escrever a seção: o que é, fonte, atenção, e o link do documento completo")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true", help="saída em JSON")
    p.add_argument("--nivel", choices=[ERRO, AVISO, NOTA], default=NOTA, help="nível mínimo a mostrar")
    args = p.parse_args()

    a = Achados()
    for checagem in (checar_glossario, checar_links, checar_datasets, checar_json,
                     checar_workflows, checar_frescor, checar_numeros_fixos, checar_metodologia):
        try:
            checagem(a)
        except Exception as e:                                   # uma checagem quebrada não derruba as outras
            a.add(ERRO, "checador", f"tools/checar_site.py:{checagem.__name__}", f"a checagem falhou: {e!r}",
                  "corrigir o checador")

    ordem = {ERRO: 0, AVISO: 1, NOTA: 2}
    itens = sorted(a.itens, key=lambda i: (ordem[i["nivel"]], i["regra"], i["onde"]))
    itens = [i for i in itens if ordem[i["nivel"]] <= ordem[args.nivel]]

    if args.json:
        print(json.dumps({"gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                          "achados": itens}, ensure_ascii=False, indent=1))
        return 1 if a.erros else 0

    por_regra: dict[str, list[dict]] = {}
    for i in itens:
        por_regra.setdefault(i["regra"], []).append(i)
    for regra, lista in por_regra.items():
        print(f"\n## {regra} ({len(lista)})")
        for i in lista:
            print(f"  [{i['nivel']}] {i['onde']}\n      {i['o_que']}" + (f"\n      → {i['fazer']}" if i["fazer"] else ""))
    erros = a.erros
    avisos = sum(1 for i in a.itens if i["nivel"] == AVISO)
    print(f"\n{erros} erro(s), {avisos} aviso(s), {len(a.itens) - erros - avisos} nota(s).")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
