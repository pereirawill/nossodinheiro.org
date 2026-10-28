# Painel — Estatais: lucro, prejuízo e dividendos

Última revisão: 2026-10-28. Código: `etl/estatais/{extract,sest,dividendos}.py` → `data/public/estatais.json`.
Atualização mensal (dia 16). Página: `/estatais/`.

## 1. Por que são três fontes, e não uma

Não existe uma base que traga o lucro de todas as estatais do Brasil. Existem três recortes, cada um com um universo
diferente, e a página mostra os três separados — nunca somados entre si:

| Fonte | Universo | Desde |
|---|---|---|
| **Tesouro Nacional** (RTN, série histórica, tabela 2.2, linha 1.4.2) | **dividendos** que a União recebeu de estatais | **1997** |
| **SEST / Ministério da Gestão** (microdado de dados financeiros) | **estatais federais**, inclusive as de capital fechado (Caixa, Correios, BNDES) | **2016** |
| **CVM** (DFP + formulário de referência) | quem **entrega demonstração à CVM** — ações em bolsa ou dívida registrada —, nas **três esferas** | **2010** |

**1988 não é possível.** Nenhuma fonte oficial aberta publica lucro de estatal antes de 2016 (SEST) ou 2010 (CVM). Os
boletins trimestrais da SEST, que existem desde 2017, publicam só comparativos de dois anos — nunca a série. A série
mais longa que existe é a dos dividendos, e começa em 1997, com o próprio RTN. Isso está escrito na página e na
tabela "até onde cada fonte volta" de `/historico/`.

## 2. Dividendos (Tesouro, desde 1997)

Planilha **Resultado do Tesouro Nacional — Série Histórica**, resolvida pela API do CKAN do Tesouro Transparente
(`package_show?id=resultado-do-tesouro-nacional`), porque o nome do arquivo muda a cada mês (`seriehistoricajul26.xlsx`).
Aba **2.2** (anual, R$ milhões correntes), linha **1.4.2 Dividendos e Participações**, com abertura por empresa nas
linhas 1.4.2.1 a 1.4.2.9 (Banco do Brasil, BNB, BNDES, Caixa, Correios, Eletrobrás, IRB, Petrobras, Demais).

- É **regime de caixa**: vale o ano em que o dinheiro entrou no Tesouro. O dividendo de um ano corresponde, em geral,
  ao lucro do ano anterior — então não dividimos um pelo outro na mesma coluna.
- Está dentro das receitas **não administradas** pela Receita Federal. Não é imposto: é a parte do lucro que cabe à
  União como acionista.
- Valores nominais no JSON; a página corrige pelo IPCA (deflator de `historico.json`, reais do último ano fechado).

## 3. Estatais federais (SEST, desde 2016)

Dois ZIPs em `gov.br/gestao/pt-br/assuntos/estatais/transparencia/` (sem chave, mas o servidor exige user-agent de
navegador e Referer): `sestidentificacao.zip` (quem são) e `sestdadosfinanceiros.zip` (demonstrações, linha a linha,
em R$ 1,00).

O agregado soma só as **empresas de controle direto** — 44 das 117 ativas —, que é o universo que o Ministério da
Gestão usa quando divulga "o lucro das estatais federais". As 73 de controle indireto são subsidiárias: o resultado
delas já está no consolidado da mãe.

Quatro armadilhas do arquivo, todas tratadas no código:

1. **A conta do lucro tem dois códigos**: `500000` (plano antigo) e `290000000` (plano atual).
2. **O código `500000` aparece em outros demonstrativos.** Sem filtrar `demonstrativo == "DRE"`, 2024 dá R$ 295,7 bi
   em vez de R$ 114,5 bi.
3. **Os grupos econômicos vêm junto com as empresas** ("GR. PETROBRAS" e "PETROBRAS"): os 9 códigos de
   `sest-identificacao-grupos.csv` são excluídos, senão o lucro conta duas vezes.
4. **O ano corrente não tem linha `Anual`** — vem no `4º Trimestre`, que é acumulado no ano. A página diz qual
   periodicidade foi usada em cada ano.

**Viés de sobrevivência.** `empresas-ativas.csv` é um retrato de hoje. Seis empresas de controle direto saíram no
período (Eletrobras em 17/06/2022, CODESA, EPL, CODOMAR, CASEMG, VDMG) e estão em `empresas-inativas.csv`. Por isso o
JSON traz duas somas: `agregado` (só as 44 de hoje) e `agregado_com_inativas` (quem era estatal naquele ano). Em 2016
a diferença **inverte o sinal**: −1,4 bi vira +2,0 bi, quase tudo Eletrobras. De 2022 em diante as duas são iguais.
A página usa a primeira no gráfico e declara a segunda no aviso.

**Conferência com o número oficial.** Nossa soma de 2025 dá R$ 168,1 bi; o Ministério da Gestão divulgou R$ 169,4 bi
(nota de 02/07/2026) — diferença de 0,8%. Em 2024: R$ 114,5 bi contra R$ 116,5 bi (1,7%). Duas empresas (CDRJ e
Ceasaminas) não têm DRE de 2025 no arquivo; **o restante não está explicado** — em 2024 as 44 estão presentes e ainda
sobram R$ 2,0 bi de diferença. Por isso os dois números aparecem lado a lado na página, em vez de escolhermos um.
O número publicado está no JSON (`sest.oficial`) e na página, ao lado do nosso.

### O dinheiro que vai na direção contrária

O arquivo traz as duas pontas, e publicar só uma deixaria a página otimista por construção:

- **Subvenção do Tesouro Nacional** (DRE, `407000` no plano antigo e `260100000` no atual) — dinheiro do Orçamento para
  custeio de quem não se paga. **Entra como receita na DRE**, ou seja, o lucro publicado já a inclui. Por isso o JSON
  traz `agregado_sem_subvencao` e, por empresa, `subvencao` e `sem_subvencao`. Em 2025: R$ 30,9 bi de subvenção, com o
  lucro das federais caindo de R$ 168,1 bi para R$ 137,2 bi sem ela. A subvenção era R$ 12,7 bi em 2016 — 2,4 vezes
  menor, em valores correntes.
- **Aporte de capital da União** e **AFAC** (fluxo de caixa, `400700`/`330034000` e `400600`/`330031000`): não passam
  pelo resultado, são capital.
- **Dividendos e JCP pagos à União** pelo caixa da própria empresa (`400411`/`330022010` e `400421`/`330025010`).
  Servem de conferência da série do Tesouro, que continua sendo a fonte oficial do dividendo: 2025 dá R$ 46,2 bi aqui
  (32,1 de dividendo + 14,2 de JCP) contra R$ 49,8 bi no RTN — fontes e regimes diferentes, por isso os dois ficam
  separados na página e não são somados.

**Armadilha da periodicidade**: no ano que vem do 4º trimestre (acumulado), o fluxo precisa ser lido no **mesmo**
trimestre. Ler "o primeiro trimestre que aparecer" dava R$ 6,8 bi de subvenção em 2025 em vez de R$ 30,9 bi. Tem teste.

**O efeito na leitura das dependentes**: a EBSERH publica resultado de −R$ 159 mi em 2025; antes da subvenção de
R$ 13,7 bi, são −R$ 13,8 bi. Com as 42 empresas, 13 fecharam 2025 no vermelho pelo número publicado e **18** sem a
subvenção. Isso ainda **não** é o custo total das dependentes para o Orçamento: investimento e outras transferências
entram por rubricas que não estão neste arquivo (estão em `/poderes/`).

**"Dependente do Tesouro"** é classificação da própria SEST: 17 empresas que não se sustentam com receita própria e
recebem dinheiro do Orçamento para pessoal e custeio. Para elas o resultado contábil não mede o custo para o país — a
página diz isso e aponta para `/poderes/`.

**O RAEEF (relatório agregado) está inacessível**: os PDFs em `gov.br/gestao/.../relatorios-das-estatais/` redirecionam
para tela de login (permissão quebrada no Plone, confirmado em navegador real). O Painel das Estatais é embed de Power
BI e Qlik, sem JSON de apoio. A API `dados.gov.br/api/publico/` exige chave. Por isso as URLs dos ZIPs são fixas no
código — e três dos cinco recursos catalogados no dados.gov.br apontam para pastas que dão 404.

## 4. Empresa por empresa, três esferas (CVM, desde 2010)

**DFP** (`dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/dfp_cia_aberta_<ano>.zip`): o arquivo `DRE_con` traz a
última linha da demonstração do resultado e, abaixo, a parte atribuída aos sócios da controladora. Quem não publica
consolidado entra pelo `DRE_ind`. Valores em milhares (coluna `ESCALA_MOEDA`), convertidos para reais.

- **O código da linha do lucro não é fixo**: é `3.11` nas empresas não financeiras e `3.09` nos bancos até 2019.
  Fixar `3.11` fazia o Banco do Brasil e o Banrisul perderem dez anos de série. A linha é achada pela descrição
  ("lucro … do período", fora "antes de" e "por ação") e o código usado fica gravado no JSON.
- **Lucro consolidado ≠ parte do controlador.** O JSON traz os dois (`lucro` e `controlador`). A página usa o
  consolidado e **não** chama a parte do controlador de "fatia da União": controlador aqui é o grupo, não o governo.
  O que cabe ao poder público é o dividendo (seção 2).

**Quem controlava a empresa em cada ano** sai do **formulário de referência** (`.../FRE/DADOS/`, arquivo
`posicao_acionaria`), e não de datas de privatização digitadas por nós. Regra:

- só linhas de **posição direta** (as de cadeia de controle vêm com `Acionista_Relacionado` preenchido);
- a linha precisa ter **CNPJ brasileiro** (o arquivo tem "Governo Francês", "Município de Medellin");
- é estatal no ano quando um **ente público** aparece com **≥ 50% das ações ordinárias**, ou é marcado pela própria
  companhia como **acionista controlador** com ≥ 20%;
- **controle indireto conta**: Petrobras na antiga BR Distribuidora, Banco do Brasil na BB Seguridade, Caixa na Caixa
  Seguridade. Nesse caso a empresa fica **fora do agregado** (`dentro_de`), porque o lucro dela já está no consolidado
  da mãe — vale também para Cemig D e Cemig GT dentro da Cemig;
- **ano sem formulário** é preenchido entre dois anos confirmados, e os anos anteriores ao primeiro também contam
  (todas as empresas da lista nasceram estatais). **Nunca para frente**: ausência depois do último ano confirmado é
  justamente o que marca a privatização. Cada ano traz a origem em `estatal_origem`.
- **Falso positivo corrigido**: "do **Estado** de São Paulo" no nome da Sabesp fazia a própria Sabesp (já privatizada,
  compradora da Emae em 2026) passar por ente público. Nome que parece empresa (S.A., Cia, Banco, Participações,
  Fundo) não é tratado como ente, e BNDES/BNDESPar/Caixa entram por CNPJ.

Consequência a declarar: a privatização aparece pelo **formulário**, não pela data do leilão. O formulário do ano da
venda já costuma vir sem o ente público, então a Cesp (leilão em out/2018) tem 2017 como último ano estatal, e a Corsan
(dez/2023) tem 2022.

### Como a lista de empresas foi levantada, e o que ficou fora

A lista de CNPJs em `EMPRESAS` saiu de uma varredura da posição acionária de todos os anos do FRE em busca de
acionista que é ente público, conferida caso a caso. O que apareceu e **não** entrou:

- **IRB Brasil RE**: depois da abertura de capital, a participação **direta** da União é de 11,7% das ordinárias — os
  50,7% que aparecem no arquivo são linha de cadeia, via Banco do Brasil. Pela regra não é estatal em nenhum ano da
  janela, então saiu da lista.
- **CEEE-G**: nenhum ano com posição que satisfaça a regra.
- **Ferrovia Centro-Atlântica, Ferrovia Norte-Sul, Transnordestina, Rota do Oeste, aeroporto de Guarulhos, Metanor**:
  aparecem com "União Federal 100%" por erro de preenchimento ou por serem concessionárias (a União é poder
  concedente, não acionista). São empresas privadas.
- **Taesa, Gasmig**: controladas pela Cemig em conjunto com sócios privados, não consolidadas no mesmo sentido —
  ficaram fora para não inflar a conta.
- **BRB (Banco de Brasília)**: é controlado pelo GDF, mas não entrega DFP à CVM; sem demonstração, não há lucro a
  publicar.
- **Governos estrangeiros** (Banco RCI/Governo Francês, ISA/Município de Medellin, Porto Sudeste/Abu Dhabi).

## 5. O que esta página não faz

- **Não soma os três recortes.** Federal pela SEST e federal pela CVM são a mesma empresa contada de duas formas.
- **Não compara lucro com dividendo na mesma linha** sem dizer que um é competência e o outro é caixa, com um ano de
  defasagem.
- **Não diz se privatizar foi bom ou ruim.** A tabela de quem deixou de ser estatal mostra o último ano com controle
  público e o resultado de hoje; entre um e outro mudaram tarifa, dívida, investimento e setor.
- **Não entra no conceito fiscal de "déficit das estatais"** (série do Banco Central, desde dez/2001, três esferas,
  excluindo os grupos Petrobras e Eletrobras). É outro número, com outro sinal e outro universo. Matéria de imprensa
  sobre déficit das estatais costuma ser esse, e não o lucro contábil.
- **Não trata estatal dependente como se o lucro medisse o custo dela** — o custo está no Orçamento, em `/poderes/`.
