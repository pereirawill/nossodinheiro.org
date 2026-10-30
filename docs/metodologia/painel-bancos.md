# Painel Bancos — quanto os bancos lucraram

Página: `/bancos/` · dados: `site/public/data/bancos.json` · ETL: `etl/bancos/extract.py` · workflow: `.github/workflows/etl-bancos.yml` (dia 21 de cada mês)

## 1. A pergunta e o que a fonte permite responder

A pergunta foi "quanto os bancos lucraram no Brasil desde 1988, os principais 10–15", e depois "dá para fazer desde
o Plano Real, ano a ano?". A resposta tem duas partes:

- **o total do sistema** começa em **2000**, porque é quando começa o **IF.data** do Banco Central (pedimos todos os
  períodos de 1993 a 1999 pela API e a resposta vem com zero linhas);
- **o lucro de cada grupo financeiro** vai até **dezembro de 1994**, pelos **balancetes do Cosif** — ver §8.

Por que o total não volta junto: nos anos 90 o Banco Central não publica **quais bancos pertencem a qual grupo**.
Somar banco a banco conta duas vezes o resultado que a controladora reconhece da controlada; medimos a diferença
nos anos em que dá para comparar e ela é de **+17% a +36%** (2000, 2005, 2010, 2015 e 2020). Tentamos duas saídas e
as duas falharam, e ficam registradas para não serem tentadas de novo: descontar as contas de participações
(erra de −43% a −165%) e casar banco e grupo pelo nome (acerta 73% a 78% do valor).

## 2. Fonte

- **Banco Central, IF.data**, API Olinda, sem chave:
  `https://olinda.bcb.gov.br/olinda/servico/IFDATA/versao/v1/odata/IfDataValores(AnoMes=@AnoMes,TipoInstituicao=@TipoInstituicao,Relatorio=@Relatorio)`
  com `Relatorio='1'` (**Resumo**), que traz por instituição Lucro Líquido, Patrimônio Líquido, Ativo Total,
  Captações e Carteira de Crédito. `IfDataCadastro(AnoMes=…)` dá nome, UF, tipo de consolidado bancário (`Tcb`) e o
  código do conglomerado prudencial de cada instituição **naquele período**.
- **IBGE, IPCA** (SIDRA 1737, variável 2266), índice de dezembro de cada ano, para a série em reais do último ano fechado.
- **CVM, DFP** (`dados.cvm.gov.br`), DRE consolidada, para conferir o lucro dos bancos de capital aberto.

`TipoInstituicao` vem documentado pelo próprio Olinda (endpoint `/aplicacao`): **1** = conglomerados prudenciais e
instituições independentes, **2** = conglomerados financeiros e instituições independentes, **3** = instituições
individuais, **4** = instituições com operações de câmbio. Os valores do `Saldo` estão **em reais**.

## 3. As três decisões que definem o painel

### 3.1 O lucro acumula no semestre

Foi o achado que mudou tudo. O Lucro Líquido do IF.data **não** é do trimestre nem acumulado no ano: acumula dentro
do **semestre**. Março = jan–mar, junho = jan–jun, setembro = jul–set, dezembro = jul–dez. Em 2025 o Itaú aparece com
R$ 10,9 bi em março, R$ 22,3 bi em junho e R$ 12,0 bi em setembro.

**Lucro do ano = junho + dezembro.** Somar os quatro trimestres contaria o primeiro semestre duas vezes e inflaria o
painel em cerca de 50%.

A regra é verificada por invariante (`_conferir_semestre`): a **mediana** da razão junho/março e dezembro/setembro
entre as 40 maiores por ativo tem de ficar em torno de 2. Medimos ano a ano de 2000 a 2026: a mediana fica entre
**1,65 e 2,50** em todos eles. O ETL falha se sair da faixa [1,5; 2,6] — é assim que a mudança de critério do BC
apareceria em vez de passar em silêncio.

### 3.2 Universo: conglomerado financeiro, com o prudencial como conferência

A série usa `TipoInstituicao=2` porque é o único recorte que alcança 2000. O conglomerado **prudencial**, que reúne
também as empresas não financeiras do grupo, só existe a partir de 2014 e é usado para conferir o último ano fechado:
em 2025, R$ 209,0 bi contra os R$ 209,9 bi desta página (0,4%).

### 3.3 Grupo, e o grupo **do ano**

Cada linha do ranking é o grupo econômico: o conglomerado financeiro mais as instituições do mesmo dono que o BC
publica à parte no universo financeiro — Redecard no Itaú, Getnet no Santander, Bitz no Bradesco, "NUBANK" e
"NU PAGAMENTOS" no Nubank. As linhas são **disjuntas** (conferido instituição por instituição em 2025), então somá-las
não duplica nada.

A chave do grupo é o **código do maior membro do conglomerado prudencial**, e vale **só nos anos em que a instituição
estava no grupo**. As duas partes importam:

- apelidar o grupo pelo maior membro mantém a série inteira: o conglomerado financeiro do Itaú (`C0010069`) é o mesmo
  código desde 2000, e usar o código do prudencial partiria cada banco em duas séries, uma até 2013 e outra de 2014 em diante;
- valer por ano impede atribuição retroativa: a Easynvest (`62169875`, "Título Corretora" até 2013) aparece desde 2000,
  mas só entra na conta do Nubank a partir de **2021**, quando o BC passa a publicá-la no conglomerado prudencial dele.

Para os anos **anteriores** à estreia de uma instituição em qualquer conglomerado prudencial (isto é, antes de 2014,
quando o conceito não existia), o grupo é o mesmo da estreia. É o que mantém inteira a série da Caixa, publicada como
instituição (`00360305`) até 2021 e como conglomerado financeiro (`C0051626`) depois — as duas metades de 2021 são o
primeiro e o segundo semestre do mesmo ano.

**Banco comprado tem a série encerrada**, e o lucro dele **não** é somado ao do comprador em anos anteriores: Unibanco
até 2008, ABN Amro até 2008, HSBC até 2016. Logo, o Itaú da série não inclui o Unibanco antes de 2009.

## 4. O que está publicado

- `anos`: por ano, o lucro e o patrimônio de cada segmento (bancos, cooperativas, não bancárias, sem classificação), o total do sistema,
  os períodos usados e se o ano é parcial.
- `maiores`: os 15 grupos de maior lucro somado em reais do ano-base, com a série ano a ano (lucro, patrimônio, ativo,
  carteira de crédito).
- `concentracao`: fatia dos cinco maiores no lucro do segmento bancário.
- `conferencia_prudencial` e `conferencia_cvm`.
- `deflator`: fator do IPCA por ano, para reais do último ano fechado. Os valores do JSON são **nominais**.

Segmento = campo `Tcb` do cadastro do BC: B1 (comercial, múltiplo com carteira comercial, caixa econômica), B2
(múltiplo sem carteira comercial, investimento, câmbio) e B4 (desenvolvimento) são **bancos**; B3S e B3C são
cooperativas; N1 a N4 são não bancárias. A classificação do grupo é a do seu maior membro no ano.

## 5. Armadilhas registradas

- **Instituições sem código.** Em 2000 e 2001 o Resumo traz duas linhas com `CodInst` nulo (R$ 14,7 mi e R$ 128,7 mi
  de lucro no 1º semestre de 2000). Não há como identificá-las; ficam fora, com aviso no log.
- **Linhas repetidas.** O trimestre mais recente volta com cada valor três vezes. O ETL deduplica por
  (instituição, conta, campo) e **falha** se duas cópias discordarem — repetição é dedupe, divergência é erro de leitura.
- **Concentração em ano de prejuízo.** Em 2001 o setor somou quase zero e a fatia dos cinco maiores dá 10.651%. A
  conta é uma divisão, não uma medida de mercado: esses anos são marcados com `sem_sentido` e a página não os mostra.
- **Instituição que desaparece no meio do ano.** O Unibanco tem resultado em dezembro de 2008 (R$ 1,49 bi) mas já
  não está no cadastro daquele mês (fusão com o Itaú). Por isso o cadastro é lido nos **dois períodos** do ano e a
  lacuna do tipo de consolidado é preenchida pelo ano conhecido mais próximo do mesmo grupo, olhando primeiro para
  trás. Sem isso o grupo some da soma dos segmentos **sem erro nenhum aparecer** — era o caso antes da correção.
  Sobra uma instituição por ano sem tipo em oito dos 27 anos, nenhuma passando de R$ 20 milhões.
- **Invariante da soma.** Os quatro segmentos (bancos, cooperativas, não bancárias e sem classificação) têm de
  somar o total em reais e em número de grupos, e o que ficou sem classificação não pode passar de 1% do total —
  se passar, é tipo novo no cadastro do BC e o ETL falha em vez de publicar uma soma que não fecha.
- **Olinda instável, e mais do que parecia.** Medido em 29/10/2026: devolve **500 para a mesma URL em cerca de
  uma tentativa a cada três**, e já devolveu 500 para *todos* os cadastros por vários minutos seguidos. A primeira
  execução no GitHub falhou por isso, com quatro tentativas em 50 segundos. Hoje são seis tentativas com espera
  crescente até 60 s; quando a rede falha e existe cópia em disco, vale a cópia com aviso; e três endereços
  seguidos sem resposta encerram a execução na hora, porque insistir nos outros 130 levaria uma hora para falhar
  do mesmo jeito. O 1º e o 3º trimestres, que só alimentam o invariante, não derrubam o ETL se faltarem. O retorno bruto é guardado em `data/raw/ifdata/` (não versionado) para que uma reexecução não repita
  as ~140 requisições — mas resposta **vazia** não vira arquivo (senão o período nunca mais seria buscado) e o **ano
  em curso** não é cacheado, porque o IF.data reapresenta os trimestres recentes.

## 6. O que o painel não responde

- **De onde vem o lucro.** O relatório Resumo traz o resultado, não a decomposição entre juros de crédito, tarifa,
  seguro e tesouraria. A decomposição do custo do crédito e do spread que o BC publica (hoje dentro do REF) é
  agregada para o sistema e não abre por banco.
- **Se o lucro é alto ou baixo.** A página publica o valor e o retorno sobre o patrimônio ao lado, e não dá nota.
  Comparação internacional exigiria igualar regra contábil, carga tributária e exigência de capital.
- **Tarifa por serviço e juro por modalidade.** São outras coletas do BC; o juro e a inadimplência por modalidade
  estão em `/inadimplencia/`.
- **Lucro antes de 2000** (§1).

## 8. Desde o Plano Real: os balancetes do Cosif

**Fonte**: Banco Central, *Balancetes e Balanços Patrimoniais*, pasta `Conglomerados-financeiros`, documento
**4040** (consolidado do conglomerado financeiro). O índice de arquivos vem da API do próprio site
(`api/servico/sitebcb/Documentos/byListGuid`), porque o nome muda ao longo do tempo (`.ZIP`, `.csv.zip` e um
`.zip.csv.zip`). Os arquivos existem desde **julho de 1988**.

**Começa em dez/1994**, não em 1988: até jun/1994 os valores estão em cruzeiro real — o patrimônio do Banco do
Brasil aparece como 17.692 bilhões em jun/1994 e como R$ 5,75 bilhões em dez/1994. A tabela da página mostra de
1995 a 1999 (anos inteiros); o semestre jul–dez/1994 entra só como valor somado, no texto.

**Duas convenções de balancete, e a regra para ler as duas** (§5 do código, com teste):
- de dez/1995 em diante o balancete vem aberto, e o lucro do semestre é a soma das contas de resultado
  (7 credoras + 8 devedoras), a mesma conta do IF.data;
- em dez/1994 e jun/1995 o balancete vem **encerrado**: 7 e 8 se anulam e o resultado está na conta 8.9.1
  ("apuração de resultado"), com o sinal trocado. É assim que se lê o Itaú de dez/1994 (R$ 126,1 mi) ou o
  Bradesco (R$ 186,8 mi), e o mesmo vale no arquivo por instituição;
- 18 grupos em dez/1994 e 13 em jun/1995 trazem **as duas** preenchidas. Não dá para saber se somam ou se
  repetem, então esses grupos ficam **sem valor** no semestre, em vez de publicarmos um número que pode estar
  dobrado.

**Por que o número de 1995 a 1999 é um piso.** A fórmula que o BC usa no IF.data é
`[7] + [8] − [8.1.9.55.00-2]`, e essa última conta — "juros ao capital", a despesa com juros sobre capital
próprio — é de 4º nível e **não aparece nos arquivos públicos**, que vão até o 3º. Medimos o efeito disso
comparando, nos mesmos grupos, o que o balancete dá e o que o BC publica: **61% a 74% entre 2000 e 2018** e
**98,5%, 99,8% e 100,2% em 2019, 2020 e 2021**, quando a conta sai do plano contábil. A quebra limpa em 2019 é a
prova de que a diferença é essa, e não erro de leitura. Logo, o lucro real de 1996–1999 foi maior que o
publicado aqui, e não temos como dizer quanto. Em 1994 e 1995 a ressalva é menor: os juros sobre capital próprio
só passaram a existir com a lei de dezembro de 1995.

**O que a série mostra**: Itaú R$ 19,4 bi e Bradesco R$ 12,1 bi somados em 1995–1999 (reais do ano-base), contra
**−R$ 41,3 bi do Banco do Brasil** (quase tudo no prejuízo de 1996) e −R$ 18,2 bi do Banestado. O último
balancete de cada grupo marca as quebras do período: Nacional e Econômico em 1995, Bozano,Simonsen e Multiplic
em 1997, Bandepe e Baneb em 1998.

## 9. Faixa dos presidentes

O gráfico do total traz embaixo quem era presidente em cada trecho (`site/src/lib/presidentes.ts`), com as datas
reais — a troca de 2016 cai no meio do ano. É **régua de tempo**: a página não calcula lucro por governo nem
ordena governos, porque o resultado dos bancos depende de juro, câmbio, lei e economia mundial, e separar o
efeito de cada coisa exige estudo que não é um dado público. Mesma regra que `/transito/` aplica à queda das
mortes desde 2012.

## 7. Lucro e imposto, lado a lado

A página mostra, no mesmo ano, o lucro dos bancos e as quatro linhas que a Receita Federal publica separadamente para
**entidades financeiras** (IRPJ, CSLL, Cofins e PIS/Pasep) — R$ 101,9 bi em 2025, lidas de `impostos.json`. **Os dois
números não são divisíveis um pelo outro**: "entidades financeiras" na Receita inclui seguradoras e outras empresas que
não estão no nosso total de bancos, e de fora ficam o IOF pago pelo cliente, a contribuição sobre a folha e os tributos
estaduais e municipais. Estão lado a lado porque são o mesmo ano e as duas fontes são oficiais; a conta de quanto o
setor paga sobre o próprio lucro exigiria a base de cálculo de cada banco, que não é pública.
