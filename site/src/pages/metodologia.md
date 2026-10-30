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


> **"E como saber se esse dado não é maquiado?"** Essa pergunta tem página própria: **[Como conferir estes números](/conferir/)** —
> as conferências que já fizemos contra outras fontes (inclusive as diferenças que não sabemos explicar), as regras que valem para
> todos os painéis, o que está fora do nosso alcance e as correções que já fizemos, com data.

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
- **Média longa (29/10/2026):** cada barra da comparação traz também a **média dos últimos 25 anos** daquele país, porque um ano
  é foto e o que forma uma população é o esforço sustentado. No caso da educação a conclusão não muda: o Brasil tem 5,5% do PIB
  na média de 20 anos, contra 4,8% dos demais. **A cobertura é desigual** — há país com 20 anos de dado na janela e país com 7 —,
  e o número de anos de cada um aparece na dica da barra.
- **Gasto por aluno (29/10/2026):** "% do PIB em educação" esconde o tamanho do bolo e o número de alunos. A página passou a
  mostrar também o **gasto por aluno em dólares PPP**, conta nossa a partir de dois dados do Banco Mundial (despesa por aluno como
  % do PIB por habitante × PIB por habitante em PPP do mesmo ano e país): Brasil US$ 2.972, Coreia US$ 11.605. O ano é antigo
  (2015 no caso do Brasil) porque a série da UNESCO parou de ser alimentada por muitos países, e o ano de cada um fica na dica.
- **Violência e guerras (29/10/2026):** a página de Comparação traz a taxa de homicídios do Brasil ao lado dos países de
  referência e dos cinco com a maior taxa do mundo (UNODC, via Banco Mundial), e uma comparação com conflitos armados. Nos
  conflitos só entra número divulgado por **órgão da ONU**, com a data em que foi lido, e cada linha diz o que **não** conta:
  o número da Ucrânia (OHCHR) é só de civis verificados um a um, sem militares; o de Gaza (OCHA, citando o Ministério da Saúde
  local) junta civis e combatentes e não alcança mortes indiretas. A taxa por 100 mil por ano é conta nossa. Onde a ONU não
  publica total verificado — Sudão, Congo, Mianmar, Haiti — a página diz que não há, em vez de usar estimativa de imprensa.
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
- **Escolaridade e analfabetismo:** além do IDEB, a página mostra até onde a população adulta estudou (IBGE, PNAD
  Contínua, tabela 7189, pessoas de 25 anos ou mais) e a taxa de analfabetismo (tabela 7113, 15 anos ou mais), de 2016 a
  2025, com mapa por estado. As faixas são acumulativas, então os percentuais de fundamental, médio e superior somam mais
  de 100%. Não usamos "analfabetismo funcional": o IBGE não publica mais, e o indicador mais citado é de instituto
  privado; o oficial mais próximo é a parcela de adultos sem o ensino fundamental. Não há como medir daqui o efeito do
  Plano Real: a série começa em 2016, e os anos 1990 estavam na PNAD antiga, de outra metodologia.
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

## Estatais — lucro, prejuízo e dividendos

- **O que é:** quanto as empresas do poder público lucraram ou perderam, e quanto disso chegou ao Tesouro como dividendo. São três
  recortes, mostrados separados porque têm universos diferentes: os **dividendos** que a União recebeu (desde 1997), o lucro das
  **estatais federais**, inclusive as de capital fechado como Caixa, Correios e BNDES (desde 2016), e o lucro **empresa por empresa
  nas três esferas**, de quem entrega demonstração à CVM (desde 2010).
- **Fontes:** Tesouro Nacional (Resultado do Tesouro Nacional, série histórica, tabela 2.2, linha 1.4.2); Ministério da Gestão/SEST
  (microdado de dados financeiros das estatais federais); CVM (DFP e formulário de referência).
- **As duas pontas:** a página mostra o que a União recebe (dividendo) e o que o Orçamento põe (subvenção do Tesouro, aporte de
  capital, AFAC). A **subvenção entra como receita na DRE**, então o lucro publicado já a inclui: em 2025 foram R$ 30,9 bi, e sem
  eles o lucro das federais cai de R$ 168,1 bi para R$ 137,2 bi. Pelo número publicado, 13 das 42 fecharam o ano no vermelho; sem a
  subvenção, 18. Não entram nessa conta renúncia fiscal, crédito subsidiado nem garantia da União — não há base aberta por empresa.
- **Atenção:** lucro é resultado contábil da empresa — não é dinheiro no caixa do governo. O que entra no Tesouro é o dividendo, pago
  no ano seguinte e só sobre a fatia do poder público. Os três recortes **não se somam**. O conjunto de empresas muda de ano para ano
  (a Eletrobras saiu do grupo das federais em 17/06/2022), então o agregado não é série comparável sem ressalva — incluindo quem era
  estatal naquele ano, 2016 deixa de ser prejuízo e vira lucro. Quem controlava cada empresa em cada ano sai do formulário da CVM, não
  de datas digitadas por nós: por isso a privatização aparece como o documento a registra, e não pela data do leilão. Nossa soma das
  federais em 2025 dá R$ 168,1 bi; o Ministério da Gestão divulgou R$ 169,4 bi (diferença de 0,8%), e os dois números estão na página.
  Não entra aqui o "déficit das estatais" no conceito fiscal do Banco Central: é outro número, com outro sinal e outro universo.
- Completo: `docs/metodologia/painel-estatais.md`.

## Saneamento — água, esgoto e lixo

- **O que é:** percentual de domicílios com água da rede geral, esgoto ligado à rede e lixo coletado, nos Censos de 1991, 2000,
  2010 e 2022 e na PNAD Contínua anual, no Brasil e por estado; mais o gasto público na função Saneamento nos três níveis.
- **Fonte:** IBGE (Censo Demográfico e PNAD Contínua, pelo SIDRA); SICONFI e SIOP para o dinheiro.
- **Atenção:** **não existe 1988** — o Censo mais próximo é o de 1991, e o eixo do gráfico começa em 1988 para mostrar o vazio. A
  categoria que conta como "ligado à rede" muda de um Censo para o outro e está gravada no arquivo de dados, por isso as pesquisas
  aparecem separadas e não viram uma linha só. A PNAD Contínua **não tem 2020 nem 2021** (pandemia) e a linha é quebrada. O Censo de
  2010 não traz o destino do lixo no mesmo recorte. **Esgoto ligado à rede não quer dizer esgoto tratado** — isso o IBGE não pergunta;
  quem publica é o prestador, ao SNIS, que ainda não está aqui. O gasto dos três níveis **não se soma** como investimento do país:
  a maior parte da obra é das companhias estaduais, com tarifa e financiamento, fora do orçamento (veja Estatais).
- **Como conferir que o dado não é maquiado:** o Censo de 2022 e a PNAD de 2022 mediram o mesmo ano por métodos diferentes e dão
  60,4% e 62,7% de esgoto na rede — diferença maior que a margem de erro da amostra (0,2%), ou seja, de definição, não de acaso. A
  página mostra as duas, a categoria somada em cada pesquisa e o código da tabela de origem de cada número.
- Completo: `docs/metodologia/painel-saneamento.md`.

## Dívida pública — o que ela custa por ano

- **O que é:** os três números que costumam ser chamados de "gasto com a dívida" — juros nominais do Governo Central
  (R$ 891,9 bi em 2025), juros e encargos pagos pelo Orçamento (R$ 362,7 bi) e amortização (R$ 1,77 tri) —, a série dos juros
  desde 1997, o estoque da Dívida Pública Federal mês a mês, a composição por indexador e o perfil de vencimento.
- **Fonte:** Tesouro Nacional (Resultado do Tesouro Nacional, tabela 2.1; Estoque da Dívida Pública Federal) e SIOP.
- **Atenção:** **amortização não é custo** — é rolagem, dívida velha paga com dívida nova; somá-la aos juros dobra a conta. O
  recorte é a **União**: o número de cerca de R$ 1,1 trilhão que circula é o do setor público consolidado (com estados,
  municípios e estatais), apurado pelo Banco Central. O estoque é saldo devedor e por isso não é corrigido pela inflação como
  se fosse despesa. Dívida bruta em % do PIB não entra aqui porque depende de um PIB que é revisado.
- Completo: `docs/metodologia/painel-divida.md`.

## Bancos — quanto lucraram, ano a ano

- **O que é:** o lucro líquido de cada conglomerado financeiro que opera no Brasil, somado por ano desde 2000, com o total do
  segmento bancário (R$ 209,9 bi em 2025), o retorno sobre o patrimônio, o ranking dos quinze maiores pelo lucro somado em
  reais de 2025 (Itaú R$ 696,7 bi, BB R$ 523,9 bi, Bradesco R$ 522,3 bi) e a fatia dos cinco maiores no lucro do setor.
- **Fonte:** Banco Central, **IF.data** (API Olinda), relatório 1 — Resumo, recorte *conglomerado financeiro e instituições
  independentes*; IPCA (SIDRA 1737) para corrigir a série; CVM (DFP) e o recorte *conglomerado prudencial* para conferir.
- **Atenção:** **o lucro do IF.data acumula no semestre**, não no ano — junho é jan–jun e dezembro é jul–dez, então o ano é a
  soma dos dois; somar os quatro trimestres contaria o primeiro semestre duas vezes (há invariante no ETL, conferido em todos
  os 27 anos), e os quatro segmentos têm de somar o total em reais e em número de grupos. **Não existe 1988**: o IF.data começa em março de 2000 e os períodos anteriores voltam vazios. Cada linha do
  ranking é o **grupo** — o conglomerado financeiro mais as instituições do mesmo dono que o BC publica à parte (Redecard no
  Itaú, Getnet no Santander, as duas metades do Nubank) —, e o critério é o conglomerado prudencial **do ano**, para que a
  compra de uma corretora não jogue para o comprador o lucro que ela teve antes de ser comprada. **Banco comprado tem a série
  encerrada** e não é somado ao comprador: Unibanco até 2008, ABN Amro até 2008, HSBC até 2016. O Nubank aparece no ranking
  pelo valor, mas na classificação do BC não é banco (licença de financeira e de instituição de pagamento) e por isso **não
  está** no total do segmento bancário. A página não decompõe o lucro entre juros, tarifa e título público, porque o relatório
  Resumo não abre isso, e não dá nota de "alto" ou "baixo".
- **Desde o Plano Real:** o lucro de cada grupo financeiro vai a **dez/1994** pelos **balancetes do Cosif** (documento
  4040), que existem desde 1988 mas só estão em reais a partir dali. Até jun/1995 o balancete vem encerrado e o
  resultado é lido na conta de apuração; 18 grupos em 1994 e 13 em 1995 ficam sem valor porque trazem as duas contas
  preenchidas. Esses números são um **piso**: a fórmula que o próprio BC publica no IF.data subtrai uma conta de 4º
  nível que os arquivos de balancete não abrem — medimos 61% a 74% do lucro publicado entre 2000 e 2018 e 100% de 2019
  em diante, quando essa conta deixa de pesar. O **total** do sistema não volta antes de 2000: o BC não publica, nessa
  época, quais bancos pertencem a qual grupo, e somar banco a banco dupla-conta de 17% a 36%.
- A faixa com os presidentes embaixo do gráfico é **régua de tempo**: a página não atribui lucro a governo.
- Completo: `docs/metodologia/painel-bancos.md`.

## Mortes no trânsito

- **O que é:** quantas pessoas morrem em acidente de trânsito por ano desde 2000, por estado, sexo e faixa de idade, com a
  comparação entre as duas contagens oficiais e com outros países.
- **Fonte:** IBGE, indicador ODS 3.6.1 (tabela 4408 do SIDRA), a partir do Sistema de Informações sobre Mortalidade do Ministério
  da Saúde; Sinesp VDE para o registro policial; OMS/Banco Mundial para a comparação internacional.
- **Atenção:** **não entra no painel de Segurança** porque não é morte intencional — somar as duas contas inflaria a violência.
  As duas contagens brasileiras não batem: 37.150 mortes pelo atestado de óbito (2024) contra 25.074 pelo registro policial
  (2025), diferença de 32% que só em parte sabemos explicar. O número internacional é **estimativa da OMS**, que corrige o
  sub-registro de cada país e por isso não coincide com a contagem nacional. A página não atribui a queda desde o pico de 2012 a
  nenhuma causa.
- Completo: `docs/metodologia/painel-transito.md`.

## Desenvolvimento — o Brasil está se desenvolvendo?

- **O que é:** doze indicadores com a série do Brasil desde os anos 1980 e a posição do país no mundo ano a ano, separados pelo que
  o próprio dado diz: o que melhorou, o que parou ou piorou, e onde o Brasil perdeu posição mesmo melhorando.
- **Fonte:** Banco Mundial (indicadores de desenvolvimento), PNUD (IDH), Transparência Internacional (percepção da corrupção), mais
  as séries próprias de educação e saneamento deste site.
- **Atenção:** a página **não diz por quê** — atribuir causa à queda do investimento ou à estagnação da produtividade é disputa entre
  economistas, não dado. Posição bruta não compara épocas, porque o número de países com dado muda; por isso usamos o **percentil**,
  e mesmo ele tem limite (no acesso a energia elétrica a lista vai de 98 países em 1990 a 215 em 2024). "Melhorou" e "piorou" são
  decididos pelo próprio indicador, que traz se é melhor quando sobe ou quando desce. O ano de referência muda de indicador para
  indicador e está sempre na tabela.
- **Comparação com o mundo (29/10/2026):** as tabelas "o que melhorou" e "o que parou" trazem, ao lado da variação do Brasil, a
  mesma variação no mesmo período para o Mundo, a América Latina e os países de renda alta — grupos publicados pelo próprio
  Banco Mundial. Serve para separar remada de maré: a mortalidade infantil caiu 90,3% no Brasil contra 56,7% no mundo, enquanto a
  renda por pessoa subiu 250% aqui contra 358% no mundo.
- **Eficiência (29/10/2026):** a seção "Quanto custa e o que entrega" põe gasto e resultado lado a lado — gasto por aluno ×
  adultos com médio completo, gasto público em saúde × expectativa de vida e mortalidade infantil, gasto estadual em segurança
  por habitante × homicídios por estado. **Não é nota de eficiência e não há linha de tendência**: o resultado de hoje vem de
  décadas de gasto, o preço de um professor ou de um hospital muda de lugar para lugar, e o ponto de partida importa. Judiciário
  e obras entram só como limite declarado, porque o dado do lado do resultado é do próprio órgão interessado.
- Completo: nesta página; os números por país estão em `/rankings/`.

## Economia — PIB, juros e contas públicas

- **O que é:** o tamanho da economia e o quanto ela cresce (desde 1996), a meta da Selic (desde 1999) e o resultado primário e
  nominal do Governo Central (desde 1997). É também a porta de entrada para os painéis de impostos, inflação, dívida, trabalho,
  renda, inadimplência e estatais.
- **Fonte:** IBGE, Contas Nacionais Anuais (SIDRA 6784) e Trimestrais (SIDRA 5932, PIB a preços de mercado); Banco Central, série
  432 do SGS (meta da Selic definida pelo Copom — a taxa efetiva fica um pouco abaixo); Tesouro Nacional, RTN tabela 2.1
  (resultado primário "abaixo da linha" e nominal).
- **Atenção:** **nada aqui é previsão** — o site publica o que já aconteceu. O PIB anual sai com cerca de dois anos de atraso,
  então o último ano fechado é mais antigo que o último trimestre publicado. O SGS recusa janelas maiores que dez anos em série
  diária e falha de forma intermitente (502, ou HTML com status 200), então a coleta vai em fatias e com repetição.
- **Sugestões:** a caixa de sugestões (`/sugestoes/`) grava texto, contato opcional e página de origem; **nunca** IP, cookie ou
  navegador. O site mostra só a contagem de 24 horas — publicar texto de terceiro exigiria moderação, e isso está dito na página.

## Indústria — seção de Desenvolvimento

- **O que é:** quatro medidas de industrialização, que não respondem a mesma pergunta: participação da indústria de
  transformação no valor adicionado (Brasil e grupos de países), participação dos manufaturados nas exportações desde 1962,
  emprego na indústria, conteúdo de média e alta tecnologia, e o índice de produção física do IBGE.
- **Fonte:** Banco Mundial, World Development Indicators (`NV.IND.MANF.ZS`, `NV.IND.TOTL.ZS`, `NV.AGR.TOTL.ZS`,
  `NV.SRV.TOTL.ZS`, `TX.VAL.MANF.ZS.UN`, `SL.IND.EMPL.ZS`, `NV.MNF.TECH.ZS.UN`) e IBGE, Pesquisa Industrial Mensal —
  Produção Física (SIDRA **8888**, número-índice 2022 = 100).
- **Por que o gráfico de participação começa em 1995, e não há 50 anos dela:** a participação setorial é medida a **preços
  correntes**. Sob inflação alta ela oscila com o preço relativo em vez da produção — a mesma série dá 46,1% em 1979 e 22,0%
  em 1980. Isso não é indústria aparecendo e sumindo em um ano, é ruído de preço. A série inteira fica no JSON, marcada, e o
  gráfico usa só o trecho que mede o que diz medir. A série de exportações, que é razão entre valores em dólar, sofre muito
  menos com isso e por isso é ela que dá o arco de 1962 em diante.
- **Zeros:** nos primeiros anos o Banco Mundial publica 0,00 onde não há dado. Participação setorial zero não existe, então o
  extrator os descarta — com teste.
- **Produção física:** só anos com doze meses entram na média anual; o ano em curso fica num campo `parcial`, para não
  comparar oito meses com doze.
- **O que os dados dizem, e que contraria o senso comum:** pela participação no PIB a queda brasileira desde 2000 foi **menor**
  que a dos países de renda alta — o indicador mais citado é o que menos mostra o problema. A perda aparece na **produção
  física** (abaixo do pico de 2013 e quase igual à de 2002), na **pauta de exportação** (manufaturados caíram de 58,7% em 1993
  para 23,8%) e no **conteúdo tecnológico** (de 51,0% para 31,9% do valor adicionado industrial).
- **O que não dizemos:** se desindustrializar é bom ou ruim, e por que aconteceu. Câmbio, juro, carga, energia e acordos
  comerciais são apontados como causa por quem estuda o tema; medir o peso de cada um é pesquisa, não dado público.

## Endividamento de risco — seção de Inadimplência

- **O que é:** quantas pessoas o Banco Central classifica em endividamento de risco (20,3 milhões, ou 17% dos devedores do
  sistema financeiro, em junho de 2026), a série de seis em seis meses desde 2021, os quatro critérios da definição, quantos
  tomadores há em cada faixa de renda, e o peso da dívida no conjunto das famílias desde 2005.
- **Fonte:** Banco Central, **Relatório de Estabilidade Financeira, volume 25, outubro de 2026** (PDF) — número de pessoas e
  Gráfico 2.3.1 na p. 77, definição na nota 70 da p. 72, tomadores por faixa de renda no Boxe 3, p. 37–38; e Banco Central,
  **SGS séries 29034** (comprometimento de renda das famílias) e **29037** (endividamento das famílias), mensais desde 2005.
- **Como entra no site:** os números do relatório não têm API, então ficam como constantes declaradas em
  `site/src/lib/endividamento.ts`, cada bloco com a página do PDF e a data da leitura — o mesmo padrão de `comparacao.ts`.
  As duas séries do SGS entram pelo ETL do painel (`etl/credito/extract.py`), pela API.
- **O que NÃO publicamos:** os valores de comprometimento de renda por faixa de salário mínimo que a imprensa citou (42% para
  quem ganha até dois mínimos). Eles existem no relatório **apenas como rótulo de gráfico** (Gráfico 1.2.2.12), e ler número de
  gráfico é estimativa com régua. Enquanto o BC não publicar a tabela, a página fica sem esse recorte.
- **Atenção, porque são três universos diferentes:** (1) os 20,3 milhões são pessoas, calculadas pelo BC dentro do SCR com a
  renda de cada devedor — informação que ele tem e não abre; (2) o resto do painel é **reais em atraso**, dos arquivos abertos
  do SCR; (3) os 95,4 milhões de tomadores por faixa de renda só incluem quem tem renda conhecida e carteira acima de R$ 200.
  Os três não se somam, e a página diz isso em cada bloco.
- **Atraso é só um dos quatro critérios**: dá para ser endividado de risco sem nunca ter deixado de pagar, bastando comprometer
  mais de 50% da renda e usar cheque especial, crédito pessoal não consignado e rotativo ao mesmo tempo.
- **O que não dizemos:** se o crédito deveria ser mais caro, mais barato ou mais restrito. As frases de análise na página são
  **citações do relatório, com a página**, e não opinião do site.

## Poder de compra — o preço medido em tempo de trabalho

- **O que é:** quanto tempo de trabalho custa um litro de gasolina, de etanol e de diesel, o botijão de 13 kg e o metro cúbico de
  GNV, mês a mês desde julho de 2001 e por estado; e em que categorias de consumo o preço brasileiro está fora da linha quando
  comparado com o de outros 20 países.
- **Fonte:** ANP, Sistema de Levantamento de Preços — preço médio de **revenda ao consumidor**, média mensal, em duas planilhas
  contíguas (`mensal-brasil-2001-a-2012`, de jul/2001 a dez/2012, e `mensal-brasil-desde-jan2013`) mais `mensal-estados-desde-jan2013`;
  Banco Central, SGS 1619 (salário mínimo); IBGE, PNAD Contínua trimestral, tabelas 5436 (rendimento habitual de todos os trabalhos,
  variável 5933) e 6371 (horas habitualmente trabalhadas em todos os trabalhos, variável 8190); Banco Mundial, International
  Comparison Program (ICP) 2021, classificação `PX.WL` (índice de nível de preços, mundo = 100), e séries `PA.NUS.PPP` e
  `PA.NUS.FCRF`.
- **Como a conta é feita:** a hora no salário mínimo é o salário do mês dividido por **220 horas**, o divisor mensal da jornada de
  44 horas semanais (CLT, art. 58 e 64). É valor de lei, exato para cada mês, e por isso é a régua da série longa. A hora do
  trabalhador médio (rendimento ÷ horas, mesma pesquisa e mesmo trimestre) aparece **só no retrato atual**: aquela série é
  publicada a preços do último trimestre, e usá-la ano a ano contra um preço corrente daria número errado.
- **Atenção:** as duas planilhas da ANP são edições diferentes do mesmo relatório, com a mesma definição de coluna e períodos que
  não se sobrepõem — por isso a série é uma só, sem emenda de metodologia. A própria ANP declara que **não houve pesquisa entre
  18/8 e 17/10 de 2020**, que a semana da greve dos caminhoneiros de 2018 teve 85% menos postos e que a abrangência caiu de 501
  para 459 municípios em 2017; as três coisas aparecem na página. A gasolina aditivada, que só existe no arquivo a partir de 2013,
  fica fora da série comparável.
- **Sobre a comparação entre países:** o ICP mede **nível de preços por categoria**, não o preço de um produto — diz se "compra de
  veículo" é cara no país, não quanto custa um modelo. O **preço relativo** publicado na página (nível da categoria ÷ nível geral
  do mesmo país) é conta nossa, e é o que permite comparar países de renda muito diferente. Usamos só a rodada **ICP 2021**: a
  rodada 2017 republica os mesmos anos com números um pouco diferentes, e juntar as duas seria emendar vintages.
- **O que não existe:** horas de trabalho para comprar uma TV ou um carro em cada país (nenhum órgão público publica preço de
  produto por país); comparação do preço da bomba entre países (o indicador `EP.PMP.SGAS.CD` do Banco Mundial foi arquivado);
  abertura do preço de um carro ou de uma geladeira em imposto, insumo, frete e margem (só institutos privados estimam isso, e o
  site não usa fonte paga como número principal). Antes de julho de 2001 o que existe é o poder de compra medido pelo IPCA, no
  painel de Inflação.
- **O que não dizemos:** que o imposto explica o preço. A página publica, lado a lado, em que categorias o preço relativo
  brasileiro está fora da linha e quanto da arrecadação incide sobre bens e serviços — e deixa a conclusão para o leitor.

## Carga tributária de 2025 — número do Tesouro (29/10/2026)

- **O que é:** o destaque "quantos dias o país trabalha para pagar imposto" passou a usar a **carga tributária bruta do Governo
  Geral de 2025** (32,40% do PIB; União 21,60, estados 8,38, municípios 2,43), do boletim do Tesouro Nacional publicado em abril
  de 2026, que sai antes do estudo da Receita Federal. O estudo da Receita (edição 2024) continua alimentando a série histórica, a
  divisão por base de incidência e a comparação com a OCDE.
- **Fonte:** constante em `site/src/lib/carga.ts`, com URL da divulgação oficial do Ministério da Fazenda e data de leitura — o
  boletim do Tesouro não tem arquivo aberto nem API no Tesouro Transparente (a página é um aplicativo sem link direto).
- **Atenção:** Receita e Tesouro medem a mesma coisa com pequena diferença de método (2024: 32,20% × 32,22%); a página diz
  isso. **Não existe número oficial para 2026**: a carga só é calculada com o ano fechado. A reforma tributária é neutra em
  arrecadação por lei, então o que muda a partir de 2027 é quem paga, não o total — e isso só será conferido quando a carga de
  2027 sair, em 2028.

## Carga tributária no mundo — bloco em Impostos (29/10/2026)

- **O que é:** quantos dias do ano cada país trabalha para pagar tributos, para 21 países de referência, com a posição do Brasil
  entre os 145 que a OCDE mede e a média da OCDE.
- **Fonte:** OCDE, *Global Revenue Statistics*, API SDMX pública (dataflow `DSD_REV_COMP_GLOBAL@DF_RSGLOBAL`, série "receita
  tributária, governo geral, total, % do PIB"). `etl/carga_mundo/extract.py` → `carga_mundo.json`, mensal. Governo geral =
  todos os níveis, com previdência — a definição comparável. **Não** usamos a série do Banco Mundial, que é só do governo central
  e dá 15% para o Brasil.
- **Atenção:** para o Brasil a OCDE calcula **33,68% em 2024**, contra 32,22% do Tesouro e 32,20% da Receita — diferença de
  método no que conta como tributo. A página usa o número brasileiro no destaque e o da OCDE na comparação, porque comparar
  países exige a mesma régua para todos, e diz isso ao lado do gráfico. Países sem dado para o último ano aparecem com o ano
  mais recente que têm, marcado.
- **O que não dizemos:** se a carga é alta ou baixa "demais". O que cada país entrega em troca está em Comparação internacional.

## IVA — bloco em Impostos (29/10/2026)

- **O que é:** a alíquota de referência estimada para o IVA da reforma tributária (CBS + IBS), o ranking das maiores
  alíquotas-padrão do mundo, as exceções da lei e o calendário de transição até 2033.
- **Fonte:** constantes declaradas em `site/src/lib/iva.ts`, com URL e data de leitura — não há API. Alíquota: estimativa do
  Comitê Gestor do IBS (27,91%); trava de 26,5% e exceções: LC 214/2025; ranking: OCDE, Consumption Tax Trends 2024, com as
  mudanças de 2025. Ao lado, o dado já publicado nesta página (Receita Federal, tabela 07: bens e serviços 13,0% do PIB contra
  10,5% na OCDE) explica por que a alíquota sai alta sem precisar de opinião.
- **Atenção:** a alíquota brasileira **não existe ainda** — será fixada por resolução do Senado. A página diz isso e será
  atualizada quando sair o número. "Maior do mundo" compara alíquotas-padrão; o que cada país tira do consumo em % do PIB é
  outra medida, e está na tabela da OCDE acima.
- **O que não dizemos:** se a reforma é boa ou ruim.

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

## Tribunais superiores — custo por ministro com o gabinete

- **O que é:** a remuneração de cada ministro e a folha de todas as pessoas lotadas no gabinete dele, no STJ, no TST e no
  STM, no mesmo molde do painel do STF, mais a comparação entre os quatro tribunais.
- **Fontes:** a folha que cada tribunal publica por exigência da Resolução CNJ 102/2009 — dados abertos do STJ (CSV),
  Transparência do TST (CSV mensal), `rem_web` do STM (CSV mensal) e Portal da Transparência do STF.
- **Medida comparável:** remuneração bruta **após o teto constitucional** e **sem indenizações** (auxílio-alimentação,
  saúde, moradia, ajuda de custo), que aparecem em destaque próprio porque passam de R$ 30 mil por mês por ministro em
  alguns tribunais. O CSV do STM não detalha verbas e é antes do teto: está declarado na página dele e na comparação.
- **Atenção:** os destaques usam o **último mês publicado**, não a média do ano, porque quem assume ou sai no meio do ano
  distorce média — em 2026 um ministro do STJ está afastado e a equipe passou a um desembargador convocado. Unidades de
  direção (Presidência, Corregedoria) não entram no custo de nenhum ministro, para não contar pessoas duas vezes.
- **O que não tem, e por quê:** o TJDFT protege a consulta com captcha e não publica arquivo; no TSE e no CNJ a folha é
  aberta, mas os ministros e conselheiros são cedidos ou requisitados e o arquivo traz só a parcela que aquele órgão
  paga — publicar isso como custo seria enganoso.
- Completo: `docs/metodologia/painel-tribunais.md`.

## Comparação internacional — quanto cada país gasta

- **O que é:** gasto público em educação, saúde, defesa, o total do governo central e as transferências de benefícios,
  como percentual do PIB, no Brasil e em 20 países de referência, mais a diferença entre a carga tributária que o Banco
  Mundial registra e a que a Receita Federal publica.
- **Fontes:** Banco Mundial (dados abertos, os mesmos indicadores do painel Rankings) e Receita Federal.
- **Atenção:** percentual do PIB **não é nota de eficiência** — pode refletir população mais velha, mais gente para
  atender ou serviço pago direto pelas famílias. Cada país informa num ano diferente e a tabela mostra o ano de cada
  número. "Despesa do governo central" e "transferências" não incluem estados e municípios.
- **A armadilha da carga tributária:** o indicador internacional cobre só o governo central (15,4% do PIB no Brasil);
  o número comparável com a OCDE é o da Receita, de 32,2%, porque estados e municípios arrecadam quase um terço do total.
- **Média, não mediana:** o gráfico mostra a média dos 20 países e a nota traz a mediana como conferência. Nas seis
  áreas as duas ficam a menos de um ponto uma da outra, então nenhuma conclusão depende da escolha.
- **A Coroa é o chefe de Estado**, então o par brasileiro é a Presidência da República (R$ 1,87 bi em 2025 como unidade
  orçamentária, R$ 3,36 bi com ABIN e EBC), não o Judiciário nem o Congresso. A ressalva vale nos dois lados: a
  Presidência inclui estrutura de governo que numa monarquia parlamentarista fica com o primeiro-ministro.
- **Parlamentos:** dez países, só as duas casas, sem tribunal de contas, ombudsman ou biblioteca, porque cada país põe
  coisas diferentes na mesma rubrica. O Congresso pagou R$ 12,88 bi em 2025 (Câmara 7,03 e Senado 5,86; o TCU é órgão
  próprio e fica fora) e aparece em segundo lugar, atrás dos Estados Unidos. **O eixo que mais distorce é a aposentadoria
  dentro da rubrica:** 47% na Câmara italiana, 38% no Congresso brasileiro e zero nos Estados Unidos, onde até o salário
  dos congressistas corre em outra lei. Por isso publicamos também o Congresso sem inativos, R$ 7,97 bi. A coluna "base"
  diz se o valor é realizado, aprovado ou, no caso da Espanha, um orçamento de 2023 prorrogado três vezes.
- **Os 20 países são escolha nossa** (vizinhos, maiores economias e os de comparação habitual) e está dito na página; a
  base tem quase 200 países e a posição do Brasil entre todos está em Rankings.
- **Judiciário:** o Brasil gastou 1,3% do PIB com o Poder Judiciário em 2025 (CNJ, Justiça em Números 2026) contra uma
  mediana europeia de 0,19% no mesmo conceito (CEPEJ, dados de 2022). O par tem de casar escopo: o CNJ mede **só
  tribunais**, e a CEPEJ mede tribunais mais Ministério Público e assistência judiciária — comparar o número do CNJ com o
  total europeu seria erro de construção. Por habitante a leitura se inverte e as duas são verdade: R$ 771,48 equivalem a
  € 122, perto dos € 132 da União Europeia, porque o PIB por habitante brasileiro é muito menor. Não conseguimos
  confirmar se os orçamentos europeus incluem aposentadorias, então publicamos os dois números brasileiros (1,3% com
  inativos e 1,1% sem) e não afirmamos nada além.
- **Monarquias:** oito países, cada valor do documento oficial do próprio país, em moeda local. As oito linhas **não
  medem a mesma coisa** e a página mostra o que entra e o que fica fora em cada uma: a Bélgica é a única que inclui a
  polícia de proteção (47% do total), os Países Baixos deixam os palácios fora, e a Dinamarca conta só pagamentos em
  dinheiro a pessoas. A conversão para reais usa a PTAX do dia e serve apenas de ordem de grandeza.

## Agora — o movimento do próprio site

- **O que é:** a única página que não publica dado de órgão público, e sim o movimento daqui: quantas pessoas estão
  lendo neste momento, o que subiu na última hora, o que foi mais aberto no dia, partidos e estados mais consultados e
  de qual domínio as pessoas chegaram.
- **O que coletamos:** caminho da página, título, horário e domínio de origem. **Nada mais.**
- **O que não coletamos:** endereço de IP, cookie, user-agent, aparelho, tela, localização ou o endereço completo de
  origem. Para não contar a mesma pessoa duas vezes no número de "agora", o navegador gera um identificador aleatório
  que morre quando a aba fecha. Nada identifica ninguém, nada é cruzado, e os registros são apagados em **48 horas**.
- **Robôs são descartados** pelo user-agent, que é lido e não gravado.
- **É a única página com JavaScript de verdade**, porque número ao vivo não existe em página estática. Se o painel sair
  do ar, nenhuma outra página do site é afetada.
- Completo: `docs/metodologia/painel-agora.md`.

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
| Dividendos recebidos pela União | Tesouro Nacional (RTN, série histórica) | 1997 | o RTN começa em 1997; antes, balanços anuais em PDF |
| Lucro das estatais federais (todas) | Ministério da Gestão / SEST (microdado) | 2016 | os boletins da SEST publicam só comparativos de dois anos |
| Lucro das estatais com registro na CVM (três esferas) | CVM (DFP e formulário de referência) | 2010 | demonstrações em PDF, empresa por empresa |
| Água, esgoto e lixo nos domicílios | IBGE — Censo Demográfico | 1991 | o Censo de 1980 não está no SIDRA nesse recorte |
| Água e esgoto ano a ano | IBGE — PNAD Contínua | 2016 (esgoto, 2019) | PNAD antiga com outra pergunta; sem 2020 e 2021 |
| Juros nominais do Governo Central | Tesouro Nacional (RTN, tabela 2.1) | 1997 | o RTN começa em 1997 |
| Estoque da Dívida Pública Federal | Tesouro Transparente (CSV por título) | set/2017 | relatórios mensais em PDF |
| Lucro do sistema bancário (total) | Banco Central — IF.data | mar/2000 | antes disso o BC não publica a composição dos grupos, e somar banco a banco dupla-conta |
| Lucro de cada grupo financeiro | Banco Central — balancetes do Cosif | dez/1994 | os arquivos vão a jul/1988, mas até jun/1994 os valores estão em cruzeiro real |
| Mortes no trânsito | IBGE/ODS 3.6.1, do SIM (Ministério da Saúde) | 2000 | o SIM existe desde 1979, sem indicador calculado |
| Mortalidade infantil, materna e de menores de 5 anos | IBGE/ODS, a partir do SIM | 1990 (neonatal), 2000 (até 5 anos), 2009 (materna) | SIM do Ministério da Saúde desde 1979, sem indicador calculado |

## Como conferir

Cada página tem a fonte no topo, um aviso com as premissas e um glossário no fim. Todo número fixo (subsídio,
teto, população) está em arquivos de configuração com fonte e data, e mudar um deles exige mudar a metodologia
na mesma alteração. Os dados brutos são baixados automaticamente das fontes oficiais; os agregados que
alimentam o site são versionados no repositório, com data de geração. Erro ou divergência: abra uma issue no
repositório ou escreva pelo Instagram.
