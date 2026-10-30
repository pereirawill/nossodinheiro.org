# Regras da revisão editorial do site

Este documento é o **prompt** da varredura com modelo. O que é regra fixa já está em `tools/checar_site.py`
(`make checar`), roda em segundos e custa zero — a varredura **não deve repetir** essas checagens. Aqui ficam
só as que exigem ler o texto e julgar.

## Como rodar

Uma fatia por grupo de painéis, em paralelo. Cada agente recebe:

- a lista de arquivos da fatia: `site/src/pages/<painel>/index.astro`, o `etl/<painel>/*.py` correspondente,
  a seção do painel em `site/src/pages/metodologia.md` e `docs/metodologia/painel-<painel>.md`;
- este documento;
- a instrução de **não ler** `site/public/data/*.json` inteiros (16 MB; o maior tem 9 MB). Para conferir um
  número, ler o campo específico com `python -c "import json; ..."`, nunca o arquivo todo;
- a instrução de **não editar nada**: a saída é um plano.

Saída de cada agente, uma linha por achado:

```
arquivo:linha | REGRA | o que está escrito | por que viola | correção sugerida (1 frase)
```

Sem código, sem reescrever a página. Ordenar por gravidade. Quando não tiver certeza, dizer que não tem —
"não consegui conferir" é um achado válido e melhor que um palpite.

## As regras

**R1 — Causa não declarada pelo dado.** A página não explica *por que* um número subiu ou caiu, a menos que a
explicação esteja na própria fonte. Frases como "por causa da reestruturação", "efeito da política X",
"reflexo da crise" são violação, mesmo quando verdadeiras. O padrão aceito é o de `/transito/`: "esta página
não atribui a queda a nenhuma causa".
*Erro real já cometido:* atribuir o prejuízo dos bancos em 2001 à compra do Banespa (o leilão foi em 2000).

**R2 — Número sem fonte primária.** Todo valor tem de vir (a) de um JSON gerado por ETL, (b) de uma constante
declarada em `site/src/lib/*.ts` com `fonte`, `url` e data de leitura, ou (c) de documento oficial citado com
página. Material de terceiros — notícia, blog, consultoria, enciclopédia — não sustenta número nem definição.
*Erro real já cometido:* identificar uma conta do Cosif a partir de um blog de advocacia.

**R3 — Régua trocada no meio.** Duas medições diferentes não podem virar uma série só. Se o período muda de
fonte, metodologia, universo ou moeda, a página mostra as duas e diz qual é qual.
*Padrão correto:* `/educacao/` com três pesquisas em três cores; `/bancos/` com o balancete e o IF.data lado a lado.

**R4 — Ressalva que sumiu.** Toda limitação documentada na metodologia do painel precisa aparecer **na página**,
não só no documento. Conferir os dois sentidos: ressalva na metodologia que não está na página, e afirmação na
página mais forte do que a metodologia permite.

**R5 — Rótulo que não bate com o dado.** Conferir que o texto descreve o que o campo realmente é: real × teto ×
projeção; pago × empenhado × dotação; ano fechado × ano parcial; fluxo × saldo; pessoa × benefício; vínculo ×
pessoa. Um ano parcial nunca pode entrar numa soma anual sem rótulo.

**R6 — Número no texto que contradiz o JSON.** Quando a frase traz um valor fixo ("R$ 209,9 bi em 2025"),
conferir contra o campo do JSON. Se divergir, dizer os dois. Atenção especial a números em prosa na
metodologia, que não são recalculados no build.

**R7 — Total que soma o que não se soma.** Três níveis de governo, benefício e pessoa, vínculo e indivíduo,
grupo e instituição. Se a página soma, tem de haver uma frase dizendo por que pode.

**R8 — Comparação sem pareamento.** Comparar Brasil com outros países, ou órgão com órgão, exige mesma
definição e mesmo perímetro, declarados. Se o pareamento é imperfeito, a página diz em que.

**R9 — Juízo de valor.** O site publica, não julga: nada de "caro", "excessivo", "ineficiente", "privilégio",
nem nota, ranking de bom/ruim ou adjetivo que o dado não sustenta. Descrever é permitido; qualificar, não.

**R10 — Promessa não cumprida.** Links e referências que o texto faz ("ver a seção X", "a metodologia explica",
"o gráfico abaixo") precisam existir e dizer o que a frase promete.

**R11 — Data e cadência.** "Atualizado em", "último ano fechado", "dado mais recente" têm de bater com o JSON.
Painel cuja fonte parou de publicar precisa dizer isso na página, em vez de parecer atual.

**R12 — Acessibilidade do número.** Todo gráfico tem `<title>` por elemento ou tabela equivalente; toda sigla
aparece por extenso na primeira vez ou tem verbete no glossário.

## O que a varredura NÃO faz

- Não roda ETL, não baixa fonte externa, não edita arquivo, não cria branch.
- Não repete o que `make checar` já cobre (glossário, links, datasets, sincronia de JSON, workflows).
- Não propõe reescrita de layout nem muda o menu — isso é decisão do dono, e já foi recusado duas vezes.
- Não lê `site/public/data/*.json` inteiros nem `site/src/lib/mapa-uf.ts`.

## Depois da varredura

O plano consolidado sai em `docs/revisao-<data>.md`, agrupado por gravidade e por painel, com uma linha por
achado. A execução é separada: o dono decide o que aplicar, e aí sim um modelo forte edita arquivo por arquivo,
lendo só o trecho apontado.
