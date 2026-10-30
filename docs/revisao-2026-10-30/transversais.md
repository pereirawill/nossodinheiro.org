# Revisão editorial — fatia Transversais (30/10/2026)

Arquivos lidos: `site/src/pages/{index,dados}.astro`, `site/src/pages/{rankings,desenvolvimento,conferir,beneficios}/index.astro`,
`site/src/lib/{beneficios,comparacao,presidentes,conferencias}.ts`, `etl/{rankings,desenvolvimento,industria}/extract.py`,
`docs/metodologia/{painel-rankings,painel-beneficios,painel-agora}.md`, seções Benefícios / Rankings / Desenvolvimento / Indústria /
Comparação / Agora / Como conferir de `site/src/pages/metodologia.md`. Números conferidos campo a campo em `rankings.json`,
`poderes_funcao_2025.json`, `poderes_2026.json`, `poderes_orgaos_2025.json`, `divida.json`, `estatais.json`, `emendas_por_autor_2025.json`,
`impostos.json`, `saneamento.json`, `seguranca.json`, `desenvolvimento.json`, `industria.json`, `educacao.json`; e no HTML gerado em
`site/dist/` (build de 30/10 10:47) para confirmar o que a página realmente mostra.

Formato: `GRAVIDADE | arquivo:linha | REGRA | o que está escrito | por que viola | correção sugerida`.

## ALTA

ALTA | site/src/pages/desenvolvimento/index.astro:53-60 (confirmado em site/dist/desenvolvimento/index.html) | R6/R5 | tabela "O que parou ou piorou" lista "Pessoas usando internet · 0,0 (1990) → 84,5 (2025) · −0,0%" | o valor de 1990 é 0 no JSON, `a.valor ? … : 0` dá variação 0 e `melhorou = variacao > 0` manda internet para "piorou"; a lede da mesma página diz "há luz e internet onde não havia" — o leitor vê o indicador que mais subiu classificado como piora | calcular a variação a partir do primeiro ano com valor > 0 (ou em pontos percentuais para os indicadores em %) e deixar o "melhorou" seguir o sinal real.

ALTA | site/src/pages/rankings/index.astro:12,43 (+ etl/rankings/extract.py:51,55-58,66) | R9 | "Em todos, 1º é o melhor." e a página renderiza os 27 índices do JSON — inclusive "População" (7º de 217, "Brasil à frente de 97% dos países"), "Crianças de 0 a 14 anos", "Gasto militar" (menor = 1º), "Despesa do governo central", "Receita tributária do governo central" e "Transferências e subsídios" (maior = 1º) | "melhor" para gasto militar menor, carga tributária maior ou população maior é juízo de valor nosso (campo `maior_melhor` escolhido no ETL para séries que só serviriam a /comparacao/ e /desenvolvimento/), e o aviso do cartão diz que só a posição é calculada por nós, não o sentido | restringir os cartões de /rankings/ a uma lista explícita (os dez originais e os de desenvolvimento) e, nos de gasto/população, trocar "1º é o melhor" por "ordenado do maior para o menor, sem juízo".

ALTA | site/src/pages/index.astro:212 | R8/R5 | "os juros da dívida federal em 2025 — mais que saúde e educação somadas" | compara juros nominais do Tesouro (competência, R$ 891,9 bi em `divida.json`) com despesa paga do SIOP (saúde 215,9 + educação 160,8 = R$ 376,7 bi); com a mesma régua — juros pagos no Orçamento, R$ 362,7 bi segundo a própria linha de /conferir/ — a frase é falsa (362,7 < 376,7); a comparação só é verdadeira misturando conceitos que a página de Dívida separa de propósito | tirar o "mais que saúde e educação somadas" ou refazê-lo com juros pagos × pago, dizendo que então não passa.

ALTA | site/src/pages/index.astro:114,140 | R7 | "Somando os três níveis, o setor público pagou R$ X por habitante no ano" / "por habitante por ano, somando os três níveis (com dívida e transferências contadas na União)" | a soma inclui o refinanciamento da dívida (rolagem, não custo — a própria /divida/ diz isso), as transferências constitucionais (contadas na União como função 28 e de novo em quem as gastou) e a cota do ICMS que estados repassam a municípios; o parêntese registra onde a dívida está, não que o mesmo real entra duas ou três vezes | somar só União sem encargos especiais + estados + municípios, com a frase "transferências entre níveis ainda aparecem duas vezes", ou retirar o por-habitante consolidado.

ALTA | site/src/pages/index.astro:84-92,113,194-202 | R7 | gráfico "Quem paga o quê" empilha União + estados + municípios por função e imprime o total; L113 "X% da saúde e Y% da educação são pagos por eles"; L202 "Transferências da União a estados e municípios aparecem no nível que gastou" | a função 10/12 da União no SIOP inclui os repasses fundo a fundo (SUS, complementação do Fundeb) como pago da União, e o mesmo dinheiro reaparece no DCA de quem recebeu — é exatamente a soma que o CLAUDE.md do painel Saúde proíbe ("nunca somar os três níveis"); a frase de L202 promete uma separação que o dado por função não faz. Não consegui confirmar no `transform_poderes.py` que modalidades 30/40 estejam excluídas da função — se estiverem, a frase está certa e a soma ainda assim não | não imprimir o total da pilha; trocar L202 por "o mesmo real pode aparecer na União (repasse) e no ente que gastou"; recalcular a frase "pagos por eles" só se houver exclusão das modalidades de transferência.

ALTA | site/src/pages/conferir/index.astro:88-89 (+ site/src/lib/conferencias.ts:131,143,154,175,192,204,216,228) | R10/R5 | "Os números do nosso lado são lidos dos mesmos arquivos que as páginas usam — não foram digitados aqui." | 8 das 19 conferências têm o `nosso` digitado em `conferencias.ts` (Deputados R$ 141,3 mi; Tribunais R$ 909 mil; Trabalho 103,5 mi; Saúde 53,1 mi; Dívida R$ 891,9 bi; Trânsito 37.150; Educação 35,2%; Comparação 5,6% e US$ 2.972) — e ao menos Dívida, Trânsito, Saúde e Comparação existem nos JSONs; na página que apresenta o método do site, o rótulo de procedência está invertido | ler do JSON os que existem e reescrever a frase: "quando o valor está no arquivo do painel, é lido dali; os demais estão em conferencias.ts, digitados, com data".

ALTA | site/src/lib/beneficios.ts:86 (exibido em site/src/pages/beneficios/index.astro:57 e /presidencia/) | R2 | "no 1º semestre de 2025 foram R$ 3,65 milhões para seis ex-presidentes, e R$ 9,42 milhões em 2024 (valores do dataset, citados pela imprensa; o portal estava fora do ar em 26/10/2026…)" | número publicado sem a fonte primária ter sido lida — a fonte declarada na linha é "Presidência da República, dados abertos", mas o que foi lido foi notícia; é o padrão já corrigido duas vezes (terceiro assinado como oficial) e R2 diz que imprensa não sustenta número | tirar os dois valores até a carga do dataset, deixando só a regra da Lei 7.474/1986 e o aviso de que o portal estava fora do ar.

ALTA | site/src/pages/desenvolvimento/index.astro:382-383 | R1/R3 | "A queda brasileira nesse trecho foi menor que a deles — o grosso da perda de participação aconteceu antes desta série." | afirma onde a perda aconteceu (antes de 1995) usando a mesma série que a frase seguinte declara ruído de preço (46,1% em 1979, 22,0% em 1980); não há fonte para a perda pré-1995 e a página admite que o indicador não a mede | cortar a frase ou escrever "com este indicador não dá para medir o que aconteceu antes de 1995".

## MÉDIA

MÉDIA | site/src/pages/index.astro:234 | R5/R10 | "75,2% dos brasileiros não têm plano de saúde e contam só com o SUS" | a ANS conta vínculos; /saude/ trata 24,8% como piso e a linha Saúde de /conferir/ promete que o site "nunca apresenta o número como quantidade de pessoas" — a home apresenta como pessoas e número exato (o certo é "pelo menos 75,2%") | "pelo menos X% … (a ANS conta vínculos, não pessoas)".

MÉDIA | site/src/pages/index.astro:98-99,213 | R5 | "R$ 168,1 bilhões · o lucro das estatais federais em 2025" | usa `sest.agregado`, que inclui R$ 30,9 bi de subvenção do Tesouro contada como receita (a correção de 28/10 registrada em /conferir/ diz que a página passou a mostrar com e sem); o cartão mostra só o maior, sem rótulo, e o agregado cobre 42 empresas de controle direto, não "as estatais federais" | rotular "lucro publicado das 42 de controle direto, com R$ 30,9 bi de subvenção dentro (R$ 137,2 bi sem)".

MÉDIA | site/src/pages/desenvolvimento/index.astro:449-451 (e metodologia.md, Indústria, "O que não dizemos") | R1 (ponto 2 das regras) | "Câmbio, juro, carga tributária, energia, infraestrutura e acordos comerciais são citados como causa por quem estuda o assunto; separar o peso de cada um não é dado público" | lista de causas sem fonte com ressalva anexada — "X explica Y, mas não separamos o peso" continua sendo R1 | cortar a lista; manter só "esta página não atribui causa".

MÉDIA | site/src/pages/desenvolvimento/index.astro:527-528 | R1 | "gastar mais não garante menos homicídio, e gastar menos não causa mais" | afirmação causal (negativa) sem fonte; um scatter sem tendência não prova ausência de causa, e a página acabou de dizer que não explica por quê | "o gráfico não mostra relação simples entre as duas medidas; esta página não atribui causa".

MÉDIA | site/src/pages/desenvolvimento/index.astro:282,296-300 | R5/R6 | título "Melhorou e mesmo assim caiu de posição" e legenda "As linhas subindo mostram… o Brasil melhorou em valor absoluto e perdeu posição relativa" | das cinco curvas, mortalidade infantil ganhou posição (87º→64º do grupo fixo de 130) e investimento piorou em valor (17,5%→17,1%); a frase generaliza o que vale para três | escolher para o gráfico só as curvas que cumprem o título ou derivar a legenda dos dados.

MÉDIA | site/src/pages/desenvolvimento/index.astro:218 | R3/R5 | hero: "o Brasil saiu do 73º para o 94º lugar" (produtividade) | posição bruta entre 1991 (171 países) e 2025 (172), que o aviso da própria página (L225) diz que "não compara épocas"; o grupo fixo dá 72º→91º de 168 | usar `posicao_fixa`/`total_fixo` no hero.

MÉDIA | site/src/pages/desenvolvimento/index.astro:253-255 | R3 | "os adultos sem o ensino fundamental caíram de 72,1% em 1991 para 30,7% hoje" | emenda Censo 1991 (régua de anos de estudo) com PNAD Contínua 2025 numa frase só, sem dizer que são pesquisas diferentes — /educacao/ as separa e a regra 1 de /conferir/ promete que isso nunca vira uma linha só | "72,1% no Censo de 1991 e 30,7% na PNAD Contínua de 2025 (pesquisas diferentes)".

MÉDIA | site/src/pages/desenvolvimento/index.astro:366,441-443 (e metodologia.md, Indústria, "o indicador mais citado é o que menos mostra o problema") | R9 | "é a que menos mostra o problema"; "Quem usa só esse número para falar em desindustrialização está usando o indicador mais fraco dos quatro" | pressupõe que há "um problema" e qualifica o argumento alheio; o dado mostra que a fatia variou pouco, não que o indicador é fraco | "é o indicador que menos variou dos quatro desde 1995", sem qualificar quem o usa.

MÉDIA | site/src/pages/desenvolvimento/index.astro:428-432,447-448 | R9/R5 | "voltamos a vender sobretudo produto primário"; "a indústria que restou é menos sofisticada que a de trinta anos atrás"; "a resposta é 'retrocedemos'" | o complemento de 23,8% de manufaturados inclui combustíveis, minérios e semimanufaturados, não só "primário"; "sofisticada" e "retrocedemos" qualificam o que a fatia de média-alta tecnologia apenas descreve | descrever as variações das fatias sem "sobretudo primário / sofisticada / retrocedemos".

MÉDIA | site/src/pages/conferir/index.astro:109 + site/src/lib/conferencias.ts:249-251,264-266 | R10 | "Todo painel publica o JSON que a página lê"; "Cada painel tem a linha 'até onde esta fonte volta no tempo' e o motivo" | Benefícios, Comparação (monarquias, parlamentos, Judiciário europeu), IVA, carga, endividamento vivem em constantes `.ts`, não em JSON; a tabela "até onde cada fonte volta" está em /historico/ e na Metodologia, não em cada painel | "os números sem API ficam em site/src/lib/*.ts com fonte e data; a tabela de alcance está em /historico/".

MÉDIA | site/src/pages/dados.astro:15,19,22 (+ site/src/pages/metodologia.md:645-649) | R10 | "Tudo que aparece nos painéis está aqui em JSON"; "código MIT no GitHub"; metodologia: "abra uma issue no repositório" | mesmas constantes `.ts` fora do JSON; o repositório é privado (CLAUDE.md), então o leitor não encontra o código nem abre issue | qualificar o "tudo" e condicionar a menção ao GitHub/issue à abertura do repositório.

MÉDIA | site/src/pages/conferir/index.astro:89 + site/src/lib/conferencias.ts:87-95,151-237 | R2/R10 | "Os da outra fonte estão em conferencias.ts com a URL e a data em que foram lidos" | 9 das 19 linhas não têm `lido` (Saneamento, Trabalho, Segurança, Saúde, Educação ×2, Dívida, Trânsito, Comparação) e 5 não têm `url` (Tribunais, Segurança, Saúde, Educação, Trabalho parcial) | preencher `lido`/`url` em todas ou escrever "quando há".

MÉDIA | site/src/lib/beneficios.ts:51 | R6 | "Todo senador ocupa imóvel funcional do Senado ou recebe auxílio-moradia… Em 2026: 63 usam imóvel, 11 recebem o auxílio." | 63 + 11 = 74, não 81: ou o "todo" está errado ou sete senadores não estão em nenhuma das duas contagens | reconferir na página de recursos e escrever "7 sem registro na fonte" ou tirar o "todo".

MÉDIA | site/src/lib/beneficios.ts:71 | R8/R5 | aposentados do STF: "cerca de R$ 62 mil cada, mais do que um ministro da ativa sem vantagens pessoais" | compara a média de um mês da folha (ago/2026; pode conter férias, 13º ou eventuais — o teto é R$ 46,4 mil) com o subsídio mensal; não consegui conferir a composição dos R$ 62 mil, e o "mais do que" induz leitura de privilégio | dizer qual coluna e mês, ou tirar a comparação.

MÉDIA | site/src/lib/beneficios.ts:79 | R2 (fato não numérico) | "o custo fica no orçamento do Comando da Aeronáutica (Defesa), não no da Presidência" | a fonte citada (Decreto 4.244/2002) regula o uso das aeronaves, não diz onde o custo é contabilizado | citar a UO/ação do SIOP em que o transporte presidencial aparece ou tirar a frase.

MÉDIA | docs/metodologia/painel-rankings.md:3,14-25,27,38 + site/src/pages/metodologia.md (Rankings, "Fontes"; Desenvolvimento, "desde os anos 1980") | R4 | documento lista 10 índices, "série desde 1985", "217 países"; metodologia.md lista só 5 do Banco Mundial; Desenvolvimento diz "desde os anos 1980" | `rankings.json` tem 27 índices, séries desde 1960, `posicao_fixa`/`total_fixo`, `medias_longas`, `agregados` e gasto por aluno; nada disso está no painel-rankings.md (última revisão 26/10) | atualizar a tabela de índices, a seção 3b (1960, grupo fixo) e acrescentar médias longas e agregados.

MÉDIA | site/src/lib/comparacao.ts:285-311 | R2 | CONFLITOS: `populacao: 2_200_000` com a nota "habitantes, Banco Mundial" para a Faixa de Gaza; Ucrânia `39_000_000` sem ano; `url` das duas linhas é a página de entrada da OCHA/OHCHR | o Banco Mundial só publica Cisjordânia + Gaza juntas (PSE, ~5,4 mi) — 2,2 mi vem do PCBS/OCHA; 39 mi não corresponde a nenhum ano recente do BM que eu conheça (37,7 mi em 2023) e não tem ano declarado; nas URLs não se acha o número | citar a fonte real da população (com ano) e o relatório/atualização específica de onde saiu cada total.

MÉDIA | site/src/pages/rankings/index.astro:47-53 | R4 | aviso: "Em índices do Banco Mundial a posição é calculada por nós ordenando os países" | não diz que o sentido da ordenação (qual ponta é 1º) também é escolha nossa nos índices de gasto, população e crianças — ver o achado ALTA de R9 | acrescentar "e o sentido (maior ou menor = 1º) está declarado em cada cartão".

## BAIXA

BAIXA | site/src/pages/rankings/index.astro:16-24 (dist: "212812405,0 em 2025") | R12/acabamento | `fmtValor` só formata os 10 índices originais | População sai "212812405,0", gasto por aluno "2972,4" sem US$, gasto em saúde "4,3" sem % | formatar pelo campo `unidade` ou cobrir os 17 ids novos.

BAIXA | site/src/pages/desenvolvimento/index.astro:537 | R6 | "contra uma mediana europeia de 0,19%" digitado | `JUDICIARIO_EUROPA_META.mediana_tribunais` (0,186) já existe em comparacao.ts | importar a constante.

BAIXA | site/src/lib/presidentes.ts:14-23 | R2 | `FONTE_PRESIDENTES.lido: "29/10/2026"` para a Galeria de Presidentes, que o próprio comentário diz que "estava fora do ar em 29/10/2026" | data de leitura de uma página que não foi lida | citar o que foi efetivamente consultado (Resolução 35/2016, DOU das posses) ou ajustar a data.

BAIXA | site/src/pages/index.astro:217 | R11/R6 | "R$ 47,1 bi empenhados em emendas parlamentares em 2025" digitado | bate hoje (soma de `emendas_por_autor_2025.json` = R$ 47,08 bi), mas é o único cartão da home fixo no texto | derivar do JSON.

BAIXA | site/src/pages/index.astro:223 | R6 | "10 rankings e o histórico de 40 anos" | `rankings.json` tem 27 índices e séries desde 1960 (66 anos) | derivar a contagem e dizer "desde 1960".

BAIXA | site/src/pages/index.astro:47,161 | R2 | `POP = 212_600_000` e "212,6 milhões de brasileiros (IBGE)" | constante digitada na página sem ano, tabela nem data de leitura (rankings.json traz 212.812.405 para 2025) | mover para constante com fonte/data ou ler de `trabalho.json`/`rankings.json`.

BAIXA | site/src/pages/index.astro:231 | R5 | "o 1% mais rico fica com X% da renda" | a PNAD mede renda, não riqueza | "o 1% de maior renda".

BAIXA | site/src/pages/index.astro:221 | R5 | "contra X% na faixa que mais paga" | é a faixa de maior alíquota efetiva, não a que mais paga em reais (7–30 SM pagam 54,7% do imposto) | "na faixa de maior alíquota efetiva".

BAIXA | site/src/pages/conferir/index.astro:132-133 | R6 | "Três destas correções vieram de alguém perguntando" | `CORRECOES` registra quatro apontadas pelo dono (29/10 ×2, 28/10 Estatais, 27/10 Inflação) | derivar ou corrigir para quatro.

BAIXA | site/src/pages/conferir/index.astro:34,46,111 | R11 | diferenças "2,0%", "1,6% e 3,8%" e "64,7%" digitadas ao lado de números vivos | hoje batem (2,06%; 1,61% e 3,78%), mas `poderes_2026.json` muda a cada carga e a diferença fica velha | calcular a diferença a partir de `outro` e do valor vivo.

BAIXA | site/src/lib/conferencias.ts:298,308 | R11 | "ganhou 15,5% em treze anos"; "248 litros hoje" | frases que envelhecem, dentro de um registro datado | "entre 2012 e 2025"; "em set/2026".

BAIXA | site/src/lib/comparacao.ts:128 | R2 | "a polícia federal de proteção (~€ 18,4 mi)" | til de aproximação num arquivo que abre com "Nada daqui é estimativa nossa; o que é cálculo nosso está marcado" | dar o valor exato do DOC 56 1281/001 ou marcar como cálculo nosso.

BAIXA | site/src/lib/beneficios.ts:27,29,30,49,51,63,65,67 + site/src/pages/beneficios/index.astro:12-14 | R11 | "Em 2026, 75% do limite foi usado", "409 ocupados em 2026", "130 deputados… 75 fazem isso", "41 pessoas por senador (2026)", "7 dos 8 contracheques lidos", "513 / 81 / 10 em exercício" | contagens do ano em curso fixadas em 26/10; as de composição existem em `meta_*.json` | derivar as contagens dos JSONs e datar as demais ("em out/2026").

BAIXA | site/src/pages/desenvolvimento/index.astro:333-334,462-463,623 | R2 | "não existe nada comparável entre países antes disso"; "sair de 60 para 70 anos de expectativa de vida custa menos que sair de 80 para 81"; "centro do debate econômico brasileiro há 40 anos" | afirmações sem fonte | cortar ou atribuir.

BAIXA | site/src/pages/desenvolvimento/index.astro:558 | R11 | "Todos os 27 estados avançaram." | fixo no texto; vale hoje, mas o mapa formata `+` sem checar o sinal | derivar (`porEstado.every(e => e.eduVar > 0)`).

BAIXA | site/src/pages/desenvolvimento/index.astro:252 | R11 | "uma melhora de 40 anos pode esconder uma década parada" | séries começam em 1960 | "uma melhora de décadas".

BAIXA | docs/metodologia/painel-agora.md:53-54 (e §2 L21) | R6 | "conta abas, não pessoas: quem abre duas abas conta uma vez… na prática, cada aba gera a sua sessão, então duas abas contam duas" | a frase se contradiz, e §2 diz que o id evita contar a mesma pessoa duas vezes | reescrever: "conta abas: duas abas da mesma pessoa contam duas".

BAIXA | site/src/pages/metodologia.md (Agora, "É a única página com JavaScript de verdade") | R6/R10 | — | o site carrega `sort.js` e `compartilhar.js` em todas as páginas (CLAUDE.md: três exceções) | "a única página cujo conteúdo depende de JavaScript".

## O que conferi e bateu (não é achado)

- /desenvolvimento/ L227-229: energia elétrica 98→215 países, "36 pontos" (94,9%→58,6%) e "3 pontos" no grupo fixo (94,8%→91,8%) batem com `rankings.json`.
- `CONGRESSO_BR` (7,027 / 5,856 / 12,883 bi) bate com `poderes_orgaos_2025.json` (7,0266 / 5,8559).
- "13,5 mil mortes a esclarecer" (comparacao.ts) = 13.537 em `seguranca.json`.
- /conferir/: Impostos mar/2026 2,06% e Poderes 1,61%/3,78% batem hoje; Saneamento 60,43 × 62,68 (2,25 p.p.).
- `JUDICIARIO_BR`: 1,3 × (1 − 0,153) = 1,10 e 68,2 / 164,6 = 41% conferem.
- Taxas dos conflitos (1.393 e 9,4 por 100 mil/ano) refazem-se com os números da constante.
- R1 em /desenvolvimento/: fora dos dois achados acima (lista de causas da indústria e "gastar menos não causa mais"), a página cumpre o que promete — "melhorou/piorou" vem de `maior_melhor`, o aviso e a seção final dizem que não atribuem causa.
- Não consegui conferir (sem fonte externa): Informativo STF 1210 (beneficios.ts:67), os valores das monarquias e parlamentos, o Annual Report 2025-26 do Sovereign Grant e as populações dos conflitos.
