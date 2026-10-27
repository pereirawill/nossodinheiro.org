# Painel — Imposto de Renda: renda declarada, alíquota efetiva e ocupação

Última revisão: 2026-10-27. Código: `etl/irpf/extract.py` → `data/public/irpf.json`. Atualização anual (a Receita publica a
edição nova em março/abril; o workflow roda dia 8 de abril e dia 8 de maio).

## 1. Fonte

- **Receita Federal, "Grandes Números do IRPF"** — planilha anual de tabelas (~20 MB, sem chave, uma edição por ano desde 2008).
  Página-índice: `gov.br/receitafederal/.../grandes-numeros-do-IRPF-2008-a-2025`. O slug de cada edição varia (a de 2024 termina
  em `-tabelas-1`, a de 2025 em `-tabelas`), por isso o extrator **lê o índice e pega o link mais recente** em vez de montar a URL.
- **Banco Central, SGS série 1619** (salário mínimo mensal), valor de dezembro do ano-calendário: a planilha publica as faixas em
  salários mínimos e não em reais.

Das 22 tabelas da planilha usamos três:

| Tabela | O que traz | Onde aparece |
|---|---|---|
| 8 | declarações por faixa de rendimento total em salários mínimos (tributável + tributação exclusiva + isentos), por UF e formulário | curva de alíquota efetiva, quem paga o imposto, composição da renda isenta |
| 15 | declarações por **natureza da ocupação** (servidor das três esferas, empregado privado, proprietário de empresa, capitalista, aposentado, MEI…) | tabela de renda média por natureza |
| 16 | declarações por **ocupação principal** (134 categorias) | as vinte maiores rendas médias e as carreiras de Estado |

## 2. Regras

- **Universo:** só quem declara — 41,7 milhões de pessoas no ano-calendário 2024, menos de um terço dos brasileiros com renda.
  Nenhum percentual do painel é "dos brasileiros": é sempre **de quem declara**. Quem ganha abaixo do limite de obrigatoriedade
  não aparece, e é exatamente a maior parte da população.
- **Renda** = rendimento tributável + rendimentos de tributação exclusiva + rendimentos isentos e não tributáveis, que é como a
  própria faixa da tabela 8 é definida. É renda **anual** e **informada pelo contribuinte**.
- **Alíquota efetiva** = imposto devido total ÷ renda (como definida acima). **Não é** a alíquota da tabela do IR, que incide só
  sobre a parte tributável. O denominador inclui renda isenta e, no topo, herança recebida, que não é renda recorrente — por isso
  a página mostra a composição da renda isenta ao lado da curva, e não apenas a curva.
- **Conversão para reais:** a faixa em salários mínimos é anual (`piso × 12 × salário mínimo`). Conferido contra a tabela 5 da
  própria planilha: a base de cálculo média de cada faixa cai dentro dos limites convertidos. A conversão é **nossa** e o valor do
  salário mínimo usado está declarado na página.
- **Sigilo:** células com pouquíssimos contribuintes vêm com `x`. São lidas como zero e contadas em `celulas_suprimidas`.
  **Nunca** reconstruímos uma célula suprimida subtraindo do total — o controle é deliberado da Receita.
- **Ocupação:** é a que o contribuinte declara, sem conferência da Receita. A categoria vazia da tabela 16 (6,6 milhões de
  declarantes, a segunda maior) entra como "Não informada" e **não** é descartada. Aposentados saem da carreira de origem e
  entram na natureza "aposentado", o que puxa para baixo a média das carreiras com muita gente aposentada.
- **Grupos da natureza da ocupação** (setor público, estatais e bancos, setor privado, donos de negócio, capital, autônomos,
  aposentados): agrupamento **nosso**, em `GRUPOS_NATUREZA`, só para ordenar e colorir a tabela. Os rótulos da Receita ficam
  intactos no JSON e na página.
- **Comparação com o subsídio do deputado:** usa o subsídio vigente em **cada mês do ano-calendário** (`etl/camara/config.py`,
  Decreto Legislativo 172/2022), com 13º e um terço de férias — R$ 584.422,67 em 2024, ou 34,5 salários mínimos anuais. Isso cai
  **dentro** da faixa de 30 a 40 salários mínimos, e a Receita não publica valores individuais. Por isso a página dá o número
  seguro ("pelo menos 867.083 declararam acima do teto da faixa dele") e mostra separado quanta gente está na mesma faixa.
- **Invariantes que derrubam o run:** declarantes fora da janela de 30 a 80 milhões; totais das tabelas 8, 15 e 16 divergindo mais
  de 0,1% entre si (a diferença normal, de poucas dezenas de pessoas, vem da supressão por sigilo); imposto devido total abaixo
  de R$ 50 bilhões.

## 3. Leitura honesta

- **Alíquota efetiva baixa no topo não é sonegação.** A renda do topo é majoritariamente isenta por lei: lucro e dividendo
  distribuído é isento na pessoa física desde a Lei 9.249/1995 (a empresa já pagou IRPJ e CSLL sobre o lucro), e herança e doação
  têm tributação estadual (ITCMD), não federal. A página mostra a composição exatamente para que a conta não seja lida como crime.
- **O Imposto de Renda é uma base entre cinco.** 71,7% de tudo que União, estados e municípios arrecadam incide sobre outra coisa
  (consumo, folha, propriedade, transações financeiras) — tabela INC 01-A do estudo Carga Tributária no Brasil, trazida para o
  painel Impostos. Quem não declara IRPF continua pagando tributo embutido no preço.
- **Renda declarada ≠ renda da PNAD.** O painel Renda mede por amostra e cobre toda a população; o IRPF é declaração obrigatória e
  enxerga bem só a cauda alta. Os dois números não são substituíveis um pelo outro e não devem ser somados ou comparados linha a linha.
- **Médias por ocupação escondem dispersão.** "Membro do Poder Legislativo" reúne deputados federais, estaduais e vereadores das
  5.568 câmaras municipais; a média baixa reflete a maioria de vereadores de cidade pequena, não o salário de um parlamentar federal.
- O painel **não** classifica ninguém como elite, nem diz se a alíquota de alguém é justa. Publica a curva, a composição e as
  médias com a fonte de cada número.

## 4. Pendências

1. Série desde 2008 (uma planilha por edição) para mostrar a evolução da alíquota efetiva e da renda isenta no tempo.
2. Renda declarada por município de residência (tabela 13) e por região administrativa do DF (tabela 14).
3. Recebedores de lucros e dividendos por ocupação (tabelas 9 e 10) — quem são os sócios, por carreira.
4. Bens e direitos declarados por grupo e localização (tabela 20), inclusive bens no exterior.
5. Cruzar o número de declarantes com a população ocupada da PNAD para dizer que fatia do país declara.
