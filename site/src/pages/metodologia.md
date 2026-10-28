---
layout: ../layouts/Base.astro
title: Metodologia — Nosso Dinheiro
---

Última revisão: 26/10/2026

**Regra única do site: só o que os órgãos públicos publicam, com a fonte de cada número.** Não damos nota,
não fazemos ranking de "bom ou ruim" e não estimamos o que a fonte não publica — quando usamos um teto no
lugar do gasto real, o rótulo diz isso. Abaixo, o essencial de cada painel. A versão completa de cada um, com
fórmulas, limitações e pendências, está no repositório do projeto (código MIT, dados e textos CC BY 4.0):
`github.com/pereirawill/nossodinheiro.org`, pasta `docs/metodologia/`.

## Geral — para onde vai o nosso dinheiro

- **O que é:** a primeira aba junta os totais pagos por União (SIOP), estados e municípios (SICONFI) no último ano fechado,
  a despesa da União por função (pizza, sem encargos especiais), a comparação por função entre os três níveis e um cartão
  com o número-chave de cada painel. Nada é calculado aqui que não venha de um painel detalhado.
- **Atenção:** "encargos especiais" (dívida, transferências) ficam fora da pizza e dentro do total; transferências da União
  aparecem no nível que gastou. Municípios: só saúde, educação, legislativo e administração por enquanto.

## Judiciário — quanto custa o Judiciário da União

- **O que é:** índice dos tribunais federais com o total pago de cada um (SIOP 2025) e link para o painel de folha onde já
  existe (STF). MPU e DPU como funções essenciais; TCU como controle externo (orçamento no Legislativo).
- **Fonte:** SIOP (órgãos 10000–17000, 29000, 34000, 59000, 03000); folha do STF no painel próprio.

## Deputados — quanto custa um deputado federal

- **Somamos:** subsídio (Decreto Legislativo 172/2022: R$ 46.366,19 desde fev/2025, 13 salários + ⅓ de férias por ano) + cota parlamentar
  realmente gasta, líquida de glosas (CSV anual da CEAP da Câmara) + verba de gabinete pelo **teto**
  (R$ 165.806,07/mês, igual para todos).
- **Não somamos:** auxílio-moradia (não há lista pública de quem recebe), plano de saúde, previdência,
  estrutura da Câmara, emendas (não são custo do deputado).
- **Fonte:** API de Dados Abertos da Câmara (lista e situação de cada deputado) e `camara.leg.br/cotas`.
- **Atenção:** o gasto real de gabinete não é publicado em dado aberto; por isso o teto. Ano corrente:
  valores até o mês atual, custo anual é projeção.
- Completo: `docs/metodologia/painel-1-custo-deputados.md`.

## Senadores — quanto custa um senador

- **Somamos:** subsídio (o mesmo dos deputados) + cota CEAPS reembolsada, por categoria + gastos fora da
  cota que o Senado publica por nome (diárias, passagens aéreas, correios, material, mídias sociais). Tudo gasto real.
- **Não somamos:** pessoal do gabinete (o Senado publica quantas pessoas, não quanto custam, e não há teto
  único publicado) nem auxílio-moradia e imóvel funcional (só "utilizou / não utilizou"). **Por isso o senador
  aparece mais barato que o deputado: compare só subsídio + cota.**
- **Fonte:** Senado Federal, Transparência → "Recursos utilizados" por senador (API `adm-dadosabertos`) e
  Dados Abertos do Senado (lista de senadores).
- Completo: `docs/metodologia/painel-senadores.md`.

## STF — quanto custa um ministro

- **Somamos:** a coluna "remuneração bruta após o teto constitucional somada com outras verbas" do ministro,
  mês a mês, + a mesma coluna para todas as pessoas lotadas no gabinete dele. É folha publicada, não estimativa.
- **Não somamos:** prédio, segurança, viagens, estrutura comum do Tribunal, ministros aposentados (mostrados à parte).
- **Fonte:** STF, Portal da Transparência → Remuneração, exportação CSV por cargo (ministros) e por lotação (gabinete).
- **Atenção:** o presidente do Tribunal aparece com o Gabinete da Presidência, menor que um gabinete de
  ministro; o custo dele fica subestimado. A folha de um mês sai no mês seguinte; a página informa até que mês há dados.
- Completo: `docs/metodologia/painel-stf.md`.

## Benefícios — o que cada um tem direito a receber

- **O que é:** lista fixa, uma linha por benefício, com valor ou regra, se o uso por pessoa é publicado, se entra
  no custo dos painéis, fonte e data de leitura. Benefício é regra, não transação: não há API.
- **Fontes:** páginas oficiais de transparência e FAQs da Câmara e do Senado, contracheque detalhado dos ministros no
  STF, Decreto Legislativo 172/2022 e os atos citados em cada linha. Boatos (ex.: "auxílio-paletó") entram só como
  desmentidos pela própria casa.
- Completo: `docs/metodologia/painel-beneficios.md`.

## Emendas — para onde vai o dinheiro das emendas

- **O que é:** valor empenhado (reservado) e pago (saiu do caixa) das emendas de cada autor no ano; só
  emendas individuais têm autor único. **Emenda não é custo do parlamentar** e nunca é somada aos painéis acima.
- **Autor → partido e UF:** cruzamento por nome com as listas oficiais de deputados e senadores da legislatura,
  inclusive quem já saiu; casamentos aproximados (títulos e sufixos ignorados) só quando há um único candidato,
  e ficam registrados. Quem não casa aparece sem sigla.
- **Fonte:** API de Dados do Portal da Transparência (CGU), `/emendas`.
- Completo: `docs/metodologia/painel-emendas.md`.

## Poderes — quanto custa manter cada Poder

- **O número:** despesa paga no ano por órgão da União, separada em "manter a máquina" (o Programa de Gestão e
  Manutenção de cada Poder na Lei Orçamentária: pessoal ativo, aposentados, custeio, investimento) e "políticas
  públicas" (programas finalísticos: Previdência, SUS, Bolsa Família). A divisão é a da própria LOA, não nossa.
- **Fora da comparação:** juros, amortização, transferências a estados e municípios e encargos de órgãos
  extintos ("Dívida/Transferências"). Ministério Público e Defensoria ficam em "Funções essenciais".
- **Fonte:** SIOP (Ministério do Planejamento e Orçamento), dados abertos da execução orçamentária, consulta SPARQL.
  Não usamos a API do Portal da Transparência porque ela cobre só o Poder Executivo.
- Completo: `docs/metodologia/painel-poderes.md`.

## Presidência — quanto gasta a Presidência

- **O que é:** subsídio do presidente, vice e ministros (DL 172/2022), cartão corporativo da Presidência mês a mês com a
  parte sob sigilo, e a despesa paga pelos órgãos da Presidência (SIOP). Não existe "gasto do presidente" como linha
  publicada; "primeira-dama" não é cargo nem centro de custo.
- **Fonte:** Portal da Transparência, download de dados do Cartão de Pagamento do Governo Federal (CPGF), órgão superior 20000.
- **Atenção:** ~98% do cartão da Presidência é publicado sob sigilo (segurança, LAI art. 23); mostramos o valor e o percentual.
  Só fornecedores pessoa jurídica são listados; CPF de pessoa física é mascarado.
- Completo: `docs/metodologia/painel-presidencia.md`.

## Estados — quanto custa cada governo estadual

- **O que é:** despesa paga por cada estado e pelo DF em 2025 por função (Assembleia + TCE, Tribunal de Justiça, MP e
  Defensoria, administração, segurança, saúde, educação, previdência, encargos), total e por habitante, com ranking.
- **Fonte:** SICONFI/Tesouro Nacional (DCA, anexo I-E), a mesma do painel de municípios.
- **Atenção:** o salário dos governadores é lei de cada estado; só entra com a lei como fonte (levantamento em andamento).
- Completo: `docs/metodologia/painel-municipios.md` (seção de estados).

## Municípios — quanto custa a Câmara Municipal da sua cidade

- **O que é:** despesa paga por cada prefeitura na função Legislativa (a Câmara inteira: vereadores, servidores, prédio),
  por habitante e por vereador, em todos os municípios que entregaram contas ao Tesouro; mais Assembleia, Tribunal de
  Justiça e total de cada estado. Uma página por município.
- **Fonte:** SICONFI/Tesouro Nacional (Declaração de Contas Anuais, anexo I-E) e TSE (vagas de vereador por cidade).
- **Atenção:** é o custo da Câmara, não o salário do vereador (lei de cada cidade, dentro do teto constitucional). Cidade
  sem contas entregues fica fora, não zero. Compare dentro da mesma faixa de população.
- Completo: `docs/metodologia/painel-municipios.md`.

## Impostos — quanto o Brasil paga de imposto federal

- **O que é:** arrecadação administrada pela Receita Federal, mês a mês desde 2000, agrupada por base de incidência
  (consumo, folha, lucro, renda do trabalho, renda do capital, patrimônio, Simples e outros), por tributo e por estado.
- **Fonte:** Receita Federal, dados abertos "Arrecadação por estado" (CSV). Só tributos federais; estaduais e municipais
  (ICMS, IPVA, ISS, IPTU) são o próximo passo, via SICONFI.
- **Atenção:** quem recolhe não é quem paga; o agrupamento por base é convenção nossa, declarada. Diferença de 2–4% para
  o total divulgado na imprensa (receitas não administradas pela RFB). Série anual em valores nominais.
- Completo: `docs/metodologia/painel-impostos.md`.

## Trabalho — quem trabalha, quem empreende, quem recebe

- **O que é:** ocupados por posição (carteira, sem carteira, conta própria, setor público, empregadores), desocupados e fora da
  força de trabalho (IBGE PNAD Contínua); empresas ativas por natureza e porte, com MEI (Mapa de Empresas); benefícios pagos pelo
  INSS por mês (BEPS).
- **Atenção:** os grupos se sobrepõem (MEI empregado, aposentado que trabalha); PNAD conta pessoas, Mapa conta CNPJs. Bolsa Família
  e optantes do Simples ainda não têm fonte aberta carregada.
- Completo: `docs/metodologia/painel-trabalho.md`.

## Rankings — onde o Brasil está

- **O que é:** posição do Brasil em índices internacionais, com os 10 primeiros e os vizinhos. 1º é sempre o melhor.
- **Fontes:** Banco Mundial (PIB, PIB per capita, expectativa de vida, Gini, gasto em educação), UNODC via Banco
  Mundial (homicídios), PNUD (IDH, posição oficial) e Transparência Internacional (corrupção, posição oficial; é ONG e
  está marcada como tal). Nos índices do Banco Mundial a posição é calculada por nós ordenando os países.
- **Atenção:** "Xº de N" é entre os países com dado, não entre todos; o ano pode variar por país e aparece na tabela.
- Completo: `docs/metodologia/painel-rankings.md`.

## Histórico — séries longas, em reais de hoje

- **O que é:** União por função desde 2000 (SIOP), arrecadação federal desde 2000 (Receita), benefícios do INSS desde 2000
  (BEPS), tudo corrigido pelo IPCA (IBGE) para reais do último ano fechado. Encargos especiais (dívida e transferências)
  separados. Ano corrente como parcial.
- Completo: `docs/metodologia/painel-historico.md`.

## Renda — setor público × privado e os 10% e 1% mais ricos

- **O que é:** rendimento médio habitual por vínculo (setor público: estatutários, militares, celetistas; privado com e sem
  carteira; doméstico; conta própria; empregador), Brasil desde 2012 e por estado; e a distribuição da renda domiciliar por
  pessoa: quanto fica com a metade mais pobre, os 10% e o 1% mais ricos, limites de cada faixa e Gini.
- **Fonte:** IBGE, PNAD Contínua anual (SIDRA 4659, 7527, 7530, 7533, 7438, 7535, 7435), valores a preços médios do último ano.
- **Atenção:** média não é salário típico; comparar setores mistura profissões e escolaridade. Pesquisa por amostra, renda
  declarada. "Setor público" inclui professores e agentes municipais, não só carreiras federais.
- **Até um salário mínimo:** a parcela de trabalhadores e de moradores que vive com até um mínimo vem do **Censo de 2022**
  (tabelas 10292 e 10296), porque a PNAD Contínua publica rendimento em reais e não em classes de salário mínimo. São duas
  medidas diferentes: 34,3% dos ocupados pelo rendimento do trabalho e 58,2% das pessoas pela renda da casa por morador.
  A tabela acumula em 1, 2, 3, 5 e 10 mínimos: até três mínimos são 81,3% dos ocupados e 88,4% das pessoas.
- Completo: `docs/metodologia/painel-renda.md`.

## Educação — IDEB por estado e município

- **O que é:** IDEB (aprovação × nota no Saeb, 0–10) da última edição por estado, região e Brasil, por rede (total, pública,
  privada, estadual), com a série desde 2005; por município (rede pública), com capitais e os 25 maiores por etapa.
- **Fonte:** INEP, planilhas de divulgação do IDEB (md5 conferido). Bienal; a edição seguinte entra quando o INEP publicar.
- **Atenção:** mede escolas e redes, não famílias; décimos não são ranking; municípios pequenos oscilam muito.
- Completo: `docs/metodologia/painel-educacao.md`.

## Segurança — ocorrências registradas por estado e município

- **O que é:** o total de **mortes violentas intencionais** (homicídio doloso + latrocínio + lesão corporal seguida de morte +
  mortes por intervenção de agente do Estado), como o Ministério da Justiça agrega, por estado (último ano fechado) e por município
  com 100 mil habitantes ou mais e capitais; taxa por 100 mil (população IBGE do mesmo ano); série desde 2015. Mais feminicídios,
  roubos e furtos de veículo e estupros.
- **Fonte:** Ministério da Justiça e Segurança Pública, Sinesp VDE (base anual dos gestores estaduais), só abrangência estadual.
- **Atenção:** registro policial, não medição independente. **Feminicídio não soma ao total** (é qualificadora do homicídio e já
  está dentro dele); mortes no trânsito, suicídios e "mortes a esclarecer" ficam fora. No recorte por cidade o total não inclui
  intervenção policial, informada só por estado. Taxa baixa pode significar pouco registro.
- Completo: `docs/metodologia/painel-seguranca.md`.

## Corrupção — o que foi punido

- **O que é:** empresas e pessoas impedidas de contratar com o poder público (CEIS), empresas punidas pela Lei Anticorrupção e o
  total das multas (CNEP), acordos de leniência da CGU e servidores federais expulsos (CEAF) — por estado do órgão que puniu,
  por ano, por órgão e pelo artigo citado na decisão. No fim, o Índice de Percepção da Corrupção, para o recorte mundial.
- **Fontes:** Portal da Transparência (CEIS, CNEP, CEAF e leniência). O índice internacional é da Transparência Internacional,
  uma ONG, e mede percepção — está rotulado como tal e separado dos registros oficiais.
- **Atenção:** isto não mede corrupção, mede o que foi **punido e registrado**; mais sanções num estado pode significar mais
  fiscalização. O estado é o do órgão que puniu, não o da empresa. Não publicamos nomes nem CPF de pessoas.
- Completo: `docs/metodologia/painel-corrupcao.md`.

## Obras — o cadastro federal de investimentos

- **O que é:** todas as obras e projetos com recurso federal registrados no Obrasgov/CIPI: situação declarada pelo órgão, valor
  previsto, empenhos já feitos, estado, eixo e tipo. A página destaca as paralisadas e inacabadas, onde estão e quanto já foi
  comprometido nelas.
- **Fonte:** Obrasgov/CIPI, API pública do Ministério da Gestão (o host mudou: `api.obrasgov.gestao.gov.br`).
- **Atenção:** só obras com dinheiro federal — obra tocada apenas por estado ou município pode não estar no cadastro. Valor previsto
  não é valor gasto, e a data da situação é a da última atualização do status, não o dia em que a obra parou; por isso mostramos
  "sem atualizar a situação" e "atraso do prazo" separados. Empregos gerados e população beneficiada são estimativas declaradas pelo
  próprio órgão e ficam fora dos números de destaque.
- Completo: `docs/metodologia/painel-obras.md`.

## Imposto de Renda — o que os brasileiros declaram ganhar

- **O que é:** quantas pessoas declararam cada faixa de renda, quanto cada faixa pagou de imposto (alíquota efetiva), de onde vem
  a renda isenta do topo, a renda média por natureza da ocupação e por ocupação principal, e quantos declararam renda acima da
  faixa em que está o subsídio de um deputado federal.
- **Fonte:** Receita Federal, Grandes Números do IRPF (tabelas 8, 15 e 16); salário mínimo do Banco Central (SGS 1619).
- **Atenção:** o universo é **quem declara** (41,7 milhões de pessoas), não a população — quem ganha pouco não declara. A renda e a
  ocupação são informadas pelo contribuinte. A alíquota efetiva usa toda a renda declarada no denominador, inclusive a isenta, e
  por isso é menor que a alíquota da tabela do IR. A conversão das faixas de salários mínimos para reais é nossa.
- **O que não dizemos:** se a alíquota de alguém é justa, e quem é ou não "elite". A página publica a curva, a composição da renda
  e as médias por ocupação, cada uma com a tabela de origem.
- Completo: `docs/metodologia/painel-imposto-de-renda.md`.

## Inflação — o IPCA desde 1979

- **O que é:** a alta de preços no mês, no ano e em 12 meses; a série mensal desde 1996; o resultado de cada ano comparado com a
  meta do Banco Central desde 1999; o que subiu mais em cada grupo de gasto, com o peso de cada um na cesta; a variação em cada
  uma das 16 áreas pesquisadas; e quanto os preços subiram desde 1995, 2000, 2010 e 2020.
- **Fontes:** IBGE (IPCA e INPC) e Banco Central (meta definida pelo Conselho Monetário Nacional).
- **Atenção:** nenhum índice é "a sua inflação" — o IPCA é a cesta média de quem ganha de 1 a 40 salários mínimos nas 16 áreas
  pesquisadas. A comparação com a meta usa só o valor central, sem a margem de tolerância. Não existe IPCA por estado.
- **Poder de compra:** a página mostra quanto compram hoje R$ 100 de julho de 1994, mês a mês, e quanto a moeda perdeu desde então.
- **Câmbio:** o real frente ao dólar (média mensal desde 1994) e a outras moedas (PTAX), mais o índice de câmbio efetivo real do
  Banco Central, que corrige a inflação dos dois lados. Câmbio **não** é inflação, e a página separa as duas coisas.
- Completo: `docs/metodologia/painel-inflacao.md` e `docs/metodologia/painel-cambio.md`.

## INSS e Aposentadoria — duas abas, de propósito

- **Por que separadas:** o INSS paga muito mais que aposentadoria (pensões, auxílios, salário-maternidade e o BPC, que é assistência
  sem contribuição) e aposentadoria não é só INSS (servidor público tem regime próprio, com outra caixa e outras regras). A aba
  **INSS** mostra tudo que o instituto paga; a aba **Aposentadoria** compara os dois regimes.
- **Fontes:** Boletim Estatístico da Previdência Social (benefícios por espécie, por estado e a série desde 2000); SIOP, para o que a
  União paga a servidores aposentados e pensionistas; SICONFI, para a previdência dos estados.
- **Atenção:** são benefícios, não pessoas — quem recebe aposentadoria e pensão conta duas vezes. Do regime próprio existe o valor
  pago, mas não há contagem nacional aberta de quantos servidores aposentados são, e por isso não comparamos valor médio.
- Completo: `docs/metodologia/painel-previdencia.md`.

## Saúde — gasto público, planos e indicadores

- **O que é:** o que União, governos estaduais e prefeituras pagaram na função Saúde; quantos brasileiros têm plano de saúde e
  quantos contam só com o SUS, por estado e nas capitais; esperança de vida, mortalidade infantil, de menores de 5 anos,
  neonatal e materna em cada estado.
- **Fontes:** SIOP (União) e SICONFI/Tesouro (estados e prefeituras) para a despesa; ANS, dados abertos, para os planos;
  IBGE (projeção da população e indicadores dos ODS, estes a partir do Sistema de Informações sobre Mortalidade do
  Ministério da Saúde) para os indicadores.
- **Atenção:** os gastos dos três níveis **não podem ser somados** — o repasse federal reaparece na despesa de quem recebeu.
  A ANS conta vínculos de plano, não pessoas — por isso "quem depende só do SUS" é um piso, escrito como "no mínimo".
  Esperança de vida e mortalidade infantil do ano corrente são projeção do IBGE.
- Completo: `docs/metodologia/painel-saude.md`.

## Inadimplência — crédito em atraso por estado

- **O que é:** parcela do crédito a pessoas e empresas vencida há mais de 90 dias, por estado, tipo de crédito e faixa de renda
  do tomador; série mensal dos últimos ~24 meses.
- **Fonte:** Banco Central, SCR.data (zips anuais com CSV mensal). Definições do BCB; valores em reais.
- **Atenção:** inadimplência em reais, não em pessoas; o estado é o menor recorte publicado — não há dado por município.
- Completo: `docs/metodologia/painel-credito.md`.

## Até onde cada fonte volta no tempo

Nenhuma fonte oficial em formato aberto chega a 1988. "Desde" é o primeiro ano legível por máquina; antes disso, quase
sempre só PDF ou metodologia diferente.

| Painel | Fonte aberta | Desde | Antes disso |
|---|---|---|---|
| União por função e por Poder | SIOP | 2000 | Balanço Geral da União em PDF; séries agregadas do Tesouro desde 1997 |
| Arrecadação federal | Receita Federal (CSV) | 2000 | planilhas da Receita desde 1995 |
| Benefícios do INSS | BEPS, tabelas 13, 14, 15 e 19 | 2000 | anuários antigos em PDF |
| Estados e municípios por função | SICONFI (DCA) | 2013 | Finbra antigo, arquivos anuais desde 1989, formato diferente (em avaliação) |
| Cota dos deputados e senadores | Câmara, Senado | 2008 | a cota não existia nesse formato |
| Folha do STF | portal do STF | ~2012 | não publicada |
| Cartão corporativo | Portal da Transparência | 2003 | cartão criado em 2001 |
| Emendas por autor | Portal da Transparência (API) | 2014 | SIOP tem emendas desde 2000, sem autor detalhado no início |
| Trabalho (PNAD Contínua) | IBGE | 2012 | PNAD anual 1992–2011, metodologia diferente |
| Empresas ativas (Mapa de Empresas) | governo federal | 2019 | base do CNPJ sem série pronta |
| Rankings | Banco Mundial / PNUD / Transparência Internacional | 1960 / 1990 / 2012 | já no histórico de rankings |
| Renda (PNAD Contínua) | IBGE | 2012 | PNAD anual 1992–2011 e Censos, metodologia diferente |
| IDEB | INEP | 2005 | o índice foi criado em 2007 com dados de 2005 |
| Ocorrências policiais (Sinesp VDE) | MJSP | 2015 | anuários do Fórum Brasileiro de Segurança Pública (ONG) e DATASUS/SIM para mortes |
| Inadimplência (SCR.data) | Banco Central | 2012 (v2 desde 2023; aqui 24 meses) | séries do SGS desde 2011 |
| Cobertura de planos de saúde | ANS | 2014 (aqui a competência mais recente) | cadastro de beneficiários desde 2000, sem série pronta por município |
| IPCA (inflação) | IBGE | dez/1979 (por grupo e região, 2020) | índices anteriores com outra metodologia e outras moedas |
| Câmbio (dólar) | Banco Central | jul/1994 | cotações anteriores em cruzeiro, cruzado e cruzeiro real |
| Punições e sanções (CEIS, CNEP, CEAF) | Portal da Transparência | o cadastro traz a sanção pela data de início; os registros mais antigos são dos anos 2000 | processos em papel, sem cadastro nacional |
| Mortalidade infantil, materna e de menores de 5 anos | IBGE/ODS, a partir do SIM | 1990 (neonatal), 2000 (até 5 anos), 2009 (materna) | SIM do Ministério da Saúde desde 1979, sem indicador calculado |

## Como conferir

Cada página tem a fonte no topo, um aviso com as premissas e um glossário no fim. Todo número fixo (subsídio,
teto, população) está em arquivos de configuração com fonte e data, e mudar um deles exige mudar a metodologia
na mesma alteração. Os dados brutos são baixados automaticamente das fontes oficiais; os agregados que
alimentam o site são versionados no repositório, com data de geração. Erro ou divergência: abra uma issue no
repositório ou escreva pelo Instagram.
