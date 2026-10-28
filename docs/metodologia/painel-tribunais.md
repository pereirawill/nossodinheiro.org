# Painel — Tribunais superiores: custo por ministro com o gabinete

Última revisão: 2026-10-28. Código: `etl/tribunais/` (`fontes.py`, `extract.py`, `transform.py`) →
`data/public/custo_magistrado_<sigla>_<ano>.json` + `meta_<sigla>_<ano>.json`. Páginas: `/judiciario/stj/`,
`/judiciario/tst/`, `/judiciario/stm/`, mais `/stf/` (painel próprio, anterior) e o índice `/judiciario/`.
Atualização mensal (dia 24, depois de o STJ publicar o mês anterior).

## 1. Fontes, uma por tribunal

Todos os tribunais publicam remuneração por pessoa (Resolução CNJ 102/2009, Anexo VIII), **cada um no seu portal e no
seu formato**. O que existe aberto, conferido em 28/10/2026:

| Tribunal | Fonte | Formato | Série |
|---|---|---|---|
| STJ | Dados Abertos (CKAN), "Folha de Pagamento de Pessoal" | 1 CSV cumulativo de ~110 MB, resolvido por `package_show` | jan/2020 → |
| TST | Transparência → Remuneração | 1 CSV por mês, listado em `/arquivos` (JSON) | 2010 → (CSV nos anos recentes) |
| STM | Remuneração e proventos (`rem_web`) | 1 CSV por mês, botão "Gerar CSV" (POST com token CSRF) | fev/2013 → |
| STF | Portal da Transparência → Remuneração | CSV por cargo e por lotação (`etl/stf/`) | painel próprio |
| TRF4 | Transparência → contracheque | HTML, 50 pessoas por página, POST com paginação | jun/2012 → |
| TRF6 | Transparência → Anexo VIII | 1 XML por mês, listado no índice | set/2022 → |

**Os runners do GitHub alcançam os três portais** (testado em 28/10/2026, workflow verde), ao contrário do portal do
STF, que recusa IPs fora do Brasil — por isso o `etl-tribunais.yml` é agendado e o do STF, não. Um tribunal que falhe
não derruba os outros: o painel dele fica com o dado do mês anterior.

**O id do recurso do STJ muda** quando o tribunal substitui o arquivo, então o extrator resolve pelo nome do pacote a
cada execução, nunca pela URL fixa. O STM exige um GET antes do POST, para o cookie de sessão e o token CSRF.

## 2. O que é "custo de um ministro"

- **Custo** = remuneração bruta do ministro + a soma da mesma coluna de **todas as pessoas lotadas no gabinete dele**,
  sem contar o próprio ministro. É a mesma regra do painel do STF, para os números serem comparáveis.
- **Valor comparável** = remuneração bruta **após a retenção do teto constitucional** e **sem indenizações**. É o
  conceito da coluna que o STF publica pronta. Onde o tribunal publica o total antes do teto, somamos a retenção (que
  vem negativa); onde publica indenizações em coluna própria, elas saem da conta.
- **Indenizações ficam fora e aparecem em campo próprio** (`indenizacoes`): auxílio-alimentação, saúde, moradia, ajuda
  de custo. Não é detalhe pequeno — num mês de 2026 um ministro do STJ teve R$ 30,8 mil só nessa coluna, e a média é de
  R$ 36 mil por ministro por mês no STJ e R$ 27 mil no TST. Somá-las em um tribunal e não no outro inviabilizaria a
  comparação, porque a coluna do STF não as inclui.
- **Exceção declarada: o STM.** O CSV dele traz um único valor bruto, antes do teto e já com indenizações dentro, e não
  detalha verbas. Por isso a coluna de remuneração do STM é maior que a dos outros (R$ 99 mil contra R$ 53 a 65 mil) e a
  página diz isso em dois lugares. O gabinete, que é a maior parte do custo, não sofre desse problema.

## 3. Quem é ministro e quem tem gabinete

- O magistrado é identificado pelo valor da coluna de cargo/vínculo de cada fonte (`cargos_do_magistrado` em
  `fontes.py`): `MINISTRO` no TST, `Ministro Ativo` no STJ, `MINISTRO DO SUPERIOR TRIBUNAL MILITAR` no STM.
- **Em exercício** = a lotação não é pseudo-unidade (inativo, pensionista, cedido, exonerado, falecido) **e** parece um
  gabinete (`padrao_gabinete`). Quem não passa nesse teste entra na estatística separada de aposentados e cedidos.
- **Magistrado convocado** de outro tribunal ganha linha própria **só quando chefia um gabinete sem titular** — caso de
  dois gabinetes do STJ em 2026, um por afastamento do ministro e outro por vaga. Quando é juiz auxiliar **dentro** do
  gabinete de um titular, como no TST, conta como pessoal daquele gabinete, não como centro de custo: somar os dois
  contaria as mesmas pessoas duas vezes.
- **Unidades de direção** (Presidência, Vice, Corregedoria, Ouvidoria, escolas judiciais) não são somadas a nenhum
  ministro, pelo mesmo motivo, e vão numa tabela própria para a conta fechar com a folha inteira. No STM o presidente e
  o vice aparecem sozinhos em unidades chamadas "Presidência" e "Vice-Presidência", com a equipe num "Gabinete da
  Presidência" separado — a página mostra os dois fora da média e explica.
- **Pensionistas** (familiares, não servidores) ficam fora de todos os números e o extrator do STJ nem guarda o nome.
  Nenhuma fonte publica CPF.

## 4. Por que os destaques usam um único mês

Quem assume ou sai no meio do ano tem média distorcida, e o mesmo vale para o gabinete: em 2026 um ministro do STJ está
afastado e a equipe dele passou ao gabinete de um desembargador convocado em fevereiro. Por isso os números grandes da
página vêm do **último mês publicado** (`ultimo_mes_resumo`), com a lista de quem ficou fora e por quê. A tabela mantém
a média do ano ao lado, e `meses_com_folha` e `gabinete_meses` dizem sobre quantos meses cada coluna foi calculada.

## 5. Invariantes que derrubam o run

- Nenhum mês pode ter mais magistrados com gabinete que a composição legal (11 no STF, 33 no STJ, 27 no TST, 15 no STM).
  Mais magistrados **no ano** que a composição é normal e só indica troca, e isso vira log, não erro.
- Nenhum magistrado em exercício identificado = a coluna de cargo mudou de nome → erro.
- Extração vazia = portal fora do ar, formato novo ou IP bloqueado → erro.

## 6. Resultado em 2026 (meses publicados até setembro)

| Tribunal | Ministros | Remuneração/mês | Pessoas no gabinete | Custo médio no ano | No último mês |
|---|---|---|---|---|---|
| TST | 26 de 27 | R$ 65.231 | 41 | R$ 990.959 | R$ 1.055.382 |
| STJ | 32 de 33 | R$ 54.236 | 43 | R$ 908.686 | R$ 924.123 |
| STF | 10 de 11 | R$ 53.362 | 31 | R$ 811.097 | — (painel usa só média) |
| STM | 13 de 15 | R$ 99.015 (inclui indenizações) | 15 | R$ 303.929 | R$ 342.675 |

As duas colunas aparecem lado a lado no índice `/judiciario/`, porque cada painel destaca o **último mês** e a média do
ano é o que permite comparar com o painel do STF, que só tem média. A diferença entre elas é de 2% a 13% e vem de quem
assumiu ou saiu no meio do ano e dos meses em que caem 13º e férias.

## 6b. Os dois Tribunais Regionais Federais com painel

- **TRF4** (39 desembargadores): a consulta devolve 50 pessoas por página e exige repetir o POST com o hash dos
  critérios, então buscamos os **quatro meses mais recentes** com folha de magistrados (cada mês custa ~24 requisições).
  O gabinete é casado pelo **código** da lotação (`TRF4/GLIPPEL`), que o desembargador e a equipe compartilham — é o
  join mais limpo de todos os tribunais. O "Total de Créditos" do TRF4 **já vem abatido o teto**, conferido na própria
  página. A folha de magistrados do sistema para em **abril de 2026**, embora a de servidores siga atualizada: é lacuna
  da fonte, não nossa. 36 em exercício em abril de 2026, R$ 325.880 por mês com o gabinete, 14 pessoas por gabinete.
- **TRF6** (18 desembargadores, criado em 2022): XML do Anexo VIII. O desembargador aparece com lotação **genérica** do
  tribunal; o gabinete existe só na lotação dos servidores, com o nome dele dentro da string e **nem sempre com a mesma
  grafia** (há um `KUSCHEL` × `KUSCHELL` na fonte). O casamento é por tokens de sobrenome, com tolerância a diferença no
  fim da palavra, e quem não casa fica sem gabinete e aparece na lista de exceções — foi o caso dos dois desembargadores
  que ocupam cargos de direção. 16 com gabinete em setembro de 2026, R$ 185.792 por mês, 8 pessoas por gabinete.
- O índice do TRF6 tem dois links errados (o "XML" de junho/2026 aponta para julho e o de janeiro/2026 para
  janeiro/2025), e o diretório do arquivo é o do **upload**, não o do mês: por isso o mês é lido do **nome do arquivo**.

## 7. O que não está aqui, e por quê

- **TJDFT**: a consulta de remuneração é protegida por **reCAPTCHA v3**, com nomes de campo que mudam a cada
  carregamento, e não há arquivo para baixar — apesar de a própria página do tribunal declarar "formatos disponíveis:
  XLS; CSV; PDF". Os dados abertos do TJDFT têm API de gestão de pessoas (cedidos, estagiários, matriz de cargos) e
  **nenhum** endpoint de folha. Só há PDF mensal até maio de 2012. Pendência: pedido via LAI citando a própria frase.
- **TSE**: a folha é aberta (Anexo VIII em HTML, jun/2012 →), mas os ministros são **cedidos do STF e do STJ** e o
  arquivo traz só a gratificação eleitoral, cerca de R$ 21 mil por mês. Publicar isso como "custo de um ministro do TSE"
  seria enganoso. O gabinete, sim, é pago pelo TSE — painel possível numa fase seguinte, com o numerador declarado.
- **CNJ**: folha aberta (tabela HTML, jun/2012 →), mas 9 dos 11 conselheiros são requisitados e recebem do tribunal de
  origem; o CNJ paga só uma parcela (R$ 2,2 mil a R$ 12,6 mil). Mesmo problema do TSE, e o gabinete é nomeado pela vaga
  ("gabinete vaga juiz TRF"), não pela pessoa, então não há como casar conselheiro e gabinete pelo dado publicado.
- **TCU**: tem API JSON pública e viva (`consultaremuneracao.apps.tcu.gov.br/api/publico/remuneracoes`), com o mês
  corrente, mas **não publica lotação em nenhum escopo**. Sem lotação não há como atribuir servidor a ministro, e o
  painel seria só a remuneração do próprio ministro — outro número, não o deste painel. Os 84 registros com "gabinete"
  são nomes genéricos de função (chefe, oficial, auxiliar de gabinete).
- **TRF1**: o sistema de folha (`app.trf1.jus.br/verificafolha`) está **em manutenção**, com aviso de acesso interno por
  VPN; o que responde é um espelho congelado em 03/04/2025, com XML mensal de 2010 a março de 2025. Publicar um painel
  "atual" com dado de março de 2025 seria enganoso. Quando o sistema voltar, o XML é bom: 43 desembargadores com gabinete
  nominal, e a equipe dividida entre `GABINETE` e `ASSESSORIA` do mesmo desembargador, que precisam ser somadas.
- **TRF5**: publica só **PDF** (com camada de texto, mas em colunas que exigem extração por coordenada) e está parado em
  **fevereiro de 2026**. Além disso o desembargador tem lotação genérica e o gabinete casa por nome. Fica para depois de
  um pedido pela Ouvidoria pelo arquivo estruturado.
- **TRF2 e TRF3**: levantamento em andamento.
- **TRTs e TREs regionais**: 51 tribunais, um portal cada. Pendência.
- **Tribunais de Justiça dos estados**: orçamento dos entes, via SICONFI (função 02), no painel Estados.

## 8. Pendências

1. TCU (ministros com subsídio igual ao do STJ) e os seis TRFs.
2. Série histórica: o STJ tem CSV desde 2020 e o STM desde 2013 — dá para mostrar a evolução do custo por ministro.
3. Para o TSE e o CNJ, somar o que o tribunal de origem paga, quando algum tribunal publicar isso de forma casável.
4. Pedido via LAI ao TJDFT pelo CSV que a própria página declara publicar.
