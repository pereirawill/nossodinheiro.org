/**
 * O que já conferimos, e contra o quê. Cada linha é uma comparação entre um número que esta página calcula e um
 * número publicado por outra fonte (ou pela mesma fonte, medido de outro jeito). Quando o valor existe no JSON do
 * painel, a página de /conferir/ o lê dali; os que estão escritos aqui vêm com a fonte, a URL e a data em que foram
 * lidos, como em `beneficios.ts` e `comparacao.ts`.
 *
 * Regra da casa: diferença conferida e explicada fica escrita; diferença que não sabemos explicar fica escrita
 * também, com as duas pontas, em vez de escolhermos a que nos agrada.
 */
export type Status = "bate" | "explicada" | "nao_explicada" | "em_aberto";

export type Checagem = {
  painel: string;
  slug: string;
  vivoId?: string;              // quando dois painéis têm o mesmo nome, identifica qual número vivo é desta linha
  oQue: string;                 // o que foi comparado
  nosso?: string;               // preenchido pela página quando vem do JSON
  outro?: string;
  diferenca?: string;
  status: Status;
  explicacao: string;
  fonte: string;
  url?: string;
  lido?: string;                // data em que a outra ponta foi lida
};

export const CHECAGENS: Checagem[] = [
  {
    painel: "Bancos", slug: "/bancos/", vivoId: "bancos_cosif",
    oQue: "O lucro dos mesmos grupos financeiros medido pelo IF.data e recalculado por nós nos balancetes que o próprio Banco Central publica (documento 4040), ano a ano entre 2000 e 2021",
    status: "explicada",
    explicacao: "O balancete dá menos até 2018 porque a fórmula que o próprio BC publica no IF.data subtrai uma " +
      "terceira conta, de 4º nível, que os arquivos de balancete não abrem — eles vão até o 3º. A partir de 2019 " +
      "as duas medidas passam a dar o mesmo número, o que mostra que a diferença era essa conta e não erro de " +
      "leitura. Por isso a série de 1995 a 1999, que só existe no balancete, é publicada como piso.",
    fonte: "Banco Central — Balancetes e Balanços Patrimoniais (Cosif) e IF.data",
    url: "https://www.bcb.gov.br/estabilidadefinanceira/balancetesbalancospatrimoniais",
    lido: "29/10/2026",
  },
  {
    painel: "Bancos", slug: "/bancos/", vivoId: "bancos_prudencial",
    oQue: "O lucro dos bancos em 2025 pelo conglomerado financeiro, que é o recorte do IF.data que alcança o ano 2000, contra o mesmo ano pelo conglomerado prudencial, recorte que o Banco Central criou em 2014 e que inclui também as empresas não financeiras de cada grupo",
    status: "bate",
    explicacao: "São dois recortes do mesmo Banco Central, montados por critérios diferentes, e param a menos de meio ponto percentual um " +
      "do outro. Usamos o financeiro na série porque é o único publicado desde 2000; o prudencial serve de " +
      "conferência do último ano fechado e está no próprio bancos.json.",
    fonte: "Banco Central — IF.data, relatório Resumo, dezembro de 2025 (TipoInstituicao 1 e 2)",
    url: "https://www3.bcb.gov.br/ifdata/",
    lido: "29/10/2026",
  },
  {
    painel: "Bancos", slug: "/bancos/", vivoId: "bancos_cvm",
    oQue: "O lucro de 2025 de cinco bancos de capital aberto no IF.data do Banco Central contra o lucro consolidado que as mesmas empresas entregaram à CVM na demonstração financeira padronizada",
    status: "explicada",
    explicacao: "Os dois números não deviam bater: o IF.data mede o conglomerado financeiro no Brasil pelo plano " +
      "de contas do Banco Central (Cosif), e o balanço da CVM é da holding inteira, com as empresas não " +
      "financeiras do grupo e as operações no exterior, em outro padrão contábil. A conferência serve para " +
      "mostrar a ordem de grandeza e o sinal da diferença — o IF.data é maior nos cinco casos. A página publica " +
      "as duas colunas em vez de escolher uma.",
    fonte: "CVM — Dados abertos, DFP 2025 (DRE consolidada) e Banco Central, IF.data",
    url: "https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp",
    lido: "29/10/2026",
  },
  {
    painel: "Inadimplência", slug: "/inadimplencia/",
    oQue: "Nossa inadimplência de pessoa física, calculada do SCR.data aberto, contra o endividamento de risco que o próprio Banco Central calcula com a renda de cada devedor (dado que ele não publica aberto)",
    status: "bate",
    explicacao: "São medidas diferentes — reais em atraso de um lado, pessoas em risco do outro — e por isso os " +
      "números não são comparáveis em nível. O que dá para conferir é a direção, e ela é a mesma: nossa taxa de PF " +
      "foi de 3,97% (jan/2025) a 6,19% (ago/2026) enquanto o indicador do BC foi de 13,4% para 17,0% dos devedores " +
      "no mesmo período. Duas contas independentes, feitas de jeitos diferentes, subindo juntas.",
    fonte: "Banco Central — Relatório de Estabilidade Financeira, volume 25 (outubro de 2026), p. 77",
    url: "https://www.bcb.gov.br/content/publicacoes/ref/202610/RELESTAB202610-refPub.pdf",
    lido: "29/10/2026",
  },
  {
    painel: "Poder de compra", slug: "/economia/poder-de-compra/",
    oQue: "Nível geral de preços do Brasil em relação aos Estados Unidos, medido pelo ICP 2021 do Banco Mundial e pela razão entre a paridade de poder de compra e o câmbio de mercado, que é outra série do mesmo banco",
    status: "bate",
    explicacao: "São duas contas independentes: o ICP compara a mesma cesta coletada em cada país (Brasil a 44,0% do " +
      "preço americano no ano de referência de 2021) e a razão PPP ÷ câmbio dá 45,7% em 2025. Ficam a menos de dois " +
      "pontos uma da outra, em anos diferentes — é a confirmação de que o Brasil é, no geral, barato em dólares.",
    fonte: "Banco Mundial — ICP 2021 e séries PA.NUS.PPP e PA.NUS.FCRF",
    url: "https://www.worldbank.org/en/programs/icp",
    lido: "29/10/2026",
  },
  {
    painel: "Saneamento", slug: "/saneamento/",
    oQue: "Domicílios com esgoto ligado à rede em 2022, medidos pelo Censo (recenseia todos) e pela PNAD Contínua (amostra)",
    status: "explicada",
    explicacao: "A diferença (2,3 pontos) é maior que a margem de erro da amostra, que o próprio IBGE publica (0,2%). " +
      "Ou seja: não é acaso de sorteio, é definição e método — e o total de domicílios das duas pesquisas bate em 0,3%.",
    fonte: "IBGE — Censo Demográfico 2022 e PNAD Contínua 2022 (SIDRA)",
    url: "https://sidra.ibge.gov.br/",
  },
  {
    painel: "Estatais", slug: "/estatais/",
    oQue: "Lucro somado das estatais federais de controle direto em 2025, pela nossa soma do microdado e pelo número que o Ministério da Gestão divulgou",
    status: "nao_explicada",
    explicacao: "Parte da diferença são duas empresas sem demonstração de 2025 no arquivo (CDRJ e Ceasaminas). O resto " +
      "não está explicado: em 2024 as 44 empresas estão no arquivo e ainda sobram R$ 2,0 bi. Publicamos os dois números.",
    fonte: "Ministério da Gestão — nota de 02/07/2026",
    url: "https://www.gov.br/gestao/pt-br/assuntos/noticias/2026/julho/estatais-federais-lucram-r-169-4-bilhoes-em-2025-aumento-de-45-sobre-2024",
    lido: "28/10/2026",
  },
  {
    painel: "Poderes", slug: "/poderes/",
    oQue: "Orçamento e pagamento da União em 2026, pelo SIOP (que usamos) e pelo painel do Portal da Transparência",
    outro: "R$ 6,43 tri de orçamento atualizado e R$ 4,76 tri pagos",
    status: "nao_explicada",
    explicacao: "Diferença de 1,6% no orçamento e 3,8% no pago. São sistemas diferentes (SIOP e Siafi) e não achamos a " +
      "conciliação: não é a reserva de contingência, que são R$ 13,1 bi. Fica declarado aqui e na metodologia.",
    fonte: "Portal da Transparência — Despesas Públicas do Governo Federal",
    url: "https://portaldatransparencia.gov.br/despesas",
    lido: "27/10/2026",
  },
  {
    painel: "Impostos", slug: "/impostos/",
    oQue: "Arrecadação federal de março de 2026, somada por nós a partir do CSV por estado e tributo, contra o total que a Receita divulga no relatório do mês",
    outro: "R$ 229,25 bi",
    status: "explicada",
    explicacao: "Diferença de 2,0%: o CSV por estado não inclui algumas receitas que o relatório traz no consolidado. " +
      "Usamos o CSV porque é o único que abre por estado e por tributo, e dizemos qual é o total oficial.",
    fonte: "Receita Federal — Análise da Arrecadação, março de 2026",
    url: "https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/relatorios/arrecadacao",
    lido: "26/10/2026",
  },
  {
    painel: "Deputados", slug: "/deputados/",
    oQue: "Cota parlamentar (CEAP) gasta em 2026, somada do CSV anual da Câmara, contra o total que a própria Câmara mostra na página de transparência",
    nosso: "R$ 141,3 mi (todas as linhas com identificação de deputado)",
    outro: "R$ 179,09 mi",
    status: "explicada",
    explicacao: "Os R$ 37,8 mi de diferença (−21%) são gastos de lideranças partidárias, que não têm deputado " +
      "identificado na linha, e de ex-deputados. Como o painel é 'custo por deputado em exercício', essas linhas ficam fora.",
    fonte: "Câmara dos Deputados — Transparência: gastos parlamentares",
    url: "https://www.camara.leg.br/transparencia/gastos-parlamentares",
    lido: "26/10/2026",
  },
  {
    painel: "Tribunais superiores", slug: "/judiciario/",
    oQue: "Remuneração de ministro do STJ pela coluna 'Total de Créditos' da folha e pela coluna comparável ao STF (bruto após o teto, sem indenizações)",
    nosso: "R$ 909 mil/mês por ministro com o gabinete",
    outro: "R$ 1,1 mi/mês se usássemos o Total de Créditos",
    status: "explicada",
    explicacao: "O 'Total de Créditos' do STJ inclui indenizações (auxílios e ajudas de custo) e a coluna do STF não. " +
      "Sem essa correção a comparação entre tribunais inflava cerca de 30%. O STM não detalha as verbas, e isso está dito na página.",
    fonte: "Folhas de pagamento do STJ, TST, STM e do STF",
    lido: "28/10/2026",
  },
  {
    painel: "Trabalho", slug: "/trabalho/",
    oQue: "População ocupada pela tabela do trimestre móvel e pela do trimestre fechado da PNAD Contínua",
    nosso: "103,5 milhões",
    outro: "103,1 milhões",
    status: "explicada",
    explicacao: "0,4% de diferença entre duas tabelas do mesmo IBGE, porque o período de referência não é o mesmo. " +
      "A página usa uma delas e diz qual, em vez de escolher a maior.",
    fonte: "IBGE — PNAD Contínua, tabelas 6318 e 4097",
    url: "https://sidra.ibge.gov.br/",
  },
  {
    painel: "Segurança", slug: "/seguranca/",
    oQue: "Se feminicídio deve somar ao total de mortes violentas intencionais",
    nosso: "Não soma",
    outro: "1.578 feminicídios contra 2.084 vítimas mulheres de homicídio doloso",
    status: "bate",
    explicacao: "Feminicídio é qualificadora do homicídio: somar os dois contaria a mesma morte duas vezes. " +
      "Conferimos pelos próprios números do Sinesp e deixamos o feminicídio fora do total, dizendo por quê.",
    fonte: "MJSP — Sinesp VDE, 2025",
  },
  {
    painel: "Saúde", slug: "/saude/",
    oQue: "Pessoas com plano de saúde, pela contagem da ANS",
    nosso: "53,1 milhões de vínculos — tratado como piso",
    status: "explicada",
    explicacao: "A ANS conta vínculos, não pessoas: quem tem dois planos aparece duas vezes. Por isso a página diz " +
      "'no mínimo' e nunca apresenta o número como quantidade de pessoas.",
    fonte: "ANS — PDA 047, taxa de cobertura",
  },
  {
    painel: "Educação", slug: "/educacao/",
    oQue: "Analfabetismo de 1991 a 2025, medido por três pesquisas diferentes",
    status: "explicada",
    explicacao: "Censo (1991 e 2000), PNAD antiga (2001–2015) e PNAD Contínua (2016–2025) não são a mesma medida. " +
      "O gráfico usa uma cor por pesquisa e não emenda as três numa linha só — emendar esconderia a troca de método.",
    fonte: "IBGE — SIDRA, tabelas 204, 271 e 7113",
  },
  {
    painel: "Dívida", slug: "/divida/",
    oQue: "O custo da dívida em 2025, pelos juros nominais do Tesouro e pelos juros pagos dentro do Orçamento",
    nosso: "R$ 891,9 bi de juros nominais",
    outro: "R$ 362,7 bi pagos como juros e encargos no Orçamento",
    status: "explicada",
    explicacao: "Conceitos diferentes: o juro nominal inclui o que é apropriado no estoque dos títulos e só vira " +
      "pagamento no resgate. E a amortização (R$ 1,77 tri) não é custo nenhum — é rolagem. A página publica os três " +
      "números lado a lado em vez de escolher o mais impressionante.",
    fonte: "Tesouro Nacional (RTN, tabela 2.1) e SIOP",
    url: "https://www.tesourotransparente.gov.br/ckan/dataset/resultado-do-tesouro-nacional",
  },
  {
    painel: "Trânsito", slug: "/transito/",
    oQue: "Mortes no trânsito, pelo atestado de óbito (Ministério da Saúde) e pelo registro policial (Sinesp)",
    nosso: "37.150 (2024, atestado de óbito)",
    outro: "25.074 (2025, registro policial)",
    status: "nao_explicada",
    explicacao: "O registro policial fica 32% abaixo do atestado de óbito. Parte é conhecida — quem morre dias " +
      "depois no hospital não volta ao registro —, mas não temos como medir o resto. As duas contagens são " +
      "publicadas lado a lado, e os anos de referência são diferentes.",
    fonte: "IBGE/ODS 3.6.1 (SIM) e MJSP (Sinesp VDE)",
    url: "https://sidra.ibge.gov.br/tabela/4408",
  },
  {
    painel: "Educação", slug: "/educacao/",
    oQue: "Adultos sem o ensino fundamental completo em 2022, medidos pelo Censo e pela PNAD Contínua",
    nosso: "35,2% pelo Censo",
    outro: "34,2% pela PNAD Contínua",
    status: "explicada",
    explicacao: "Um ponto de diferença entre recenseamento e amostra no mesmo ano, para a mesma pergunta. É a " +
      "ordem de grandeza do desencontro entre os dois instrumentos do IBGE, e aparece ao lado do gráfico que " +
      "junta os Censos desde 1991 com a pesquisa anual.",
    fonte: "IBGE — Censo 2022 (tabela 10141) e PNAD Contínua 2022 (tabela 7189)",
    url: "https://sidra.ibge.gov.br/tabela/10141",
  },
  {
    painel: "Comparação", slug: "/comparacao/",
    oQue: "Gasto em educação do Brasil, medido em % do PIB e em dólares por aluno",
    nosso: "5,6% do PIB — acima da média dos países de referência",
    outro: "US$ 2.972 por aluno do fundamental, contra US$ 11.605 da Coreia",
    status: "explicada",
    explicacao: "As duas medidas são verdadeiras e dizem coisas opostas. Percentual do PIB não é dinheiro: a mesma " +
      "fatia rende menos onde o PIB por habitante é menor e onde há mais crianças por adulto (19,4% da população " +
      "brasileira tem até 14 anos, contra 10,2% na Coreia). A página passou a mostrar as duas depois de o dono " +
      "apontar que só o percentual 'não traduz a realidade'.",
    fonte: "Banco Mundial — SE.XPD.TOTL.GD.ZS, SE.XPD.PRIM.PC.ZS e NY.GDP.PCAP.PP.CD",
    url: "https://data.worldbank.org/indicator/SE.XPD.PRIM.PC.ZS",
  },
];

/** As regras que valem para todas as páginas, e que é possível checar olhando o site. */
export const REGRAS: { titulo: string; texto: string }[] = [
  {
    titulo: "Série de pesquisas diferentes nunca vira uma linha só",
    texto: "Quando a fonte muda de método (Censo e PNAD, plano de contas antigo e novo, IPCA antes e depois de uma " +
      "troca de moeda), cada pedaço aparece separado, com a sua cor e o seu rótulo. Emendar daria um gráfico mais " +
      "bonito e esconderia exatamente o que importa.",
  },
  {
    titulo: "Todo número diz até onde a fonte vai",
    texto: "Cada painel tem a linha 'até onde esta fonte volta no tempo' e o motivo. É por isso que respondemos " +
      "'não dá' quando pedem uma série desde 1988: nenhuma base aberta chega lá, e inventar o começo seria o pior caminho.",
  },
  {
    titulo: "Declarado é diferente de medido",
    texto: "Situação de obra, emprego gerado, cota glosada, índice de atendimento de saneamento: há muito dado que o " +
      "próprio órgão declara sobre si mesmo. Quando é esse o caso, a página escreve quem declarou.",
  },
  {
    titulo: "Teto, projeção e gasto real não se misturam",
    texto: "Quando um componente não é publicado (o gasto real de gabinete de deputado, por exemplo), entra o teto " +
      "legal com rótulo de teto — e o total diz que parte dele é projeção.",
  },
  {
    titulo: "O arquivo fica público",
    texto: "Todo painel publica o JSON que a página lê, com a tabela ou o endpoint de origem de cada número. A lista " +
      "está em /dados/. Refazer a conta não depende de nós.",
  },
  {
    titulo: "Erro achado é erro escrito",
    texto: "Quando encontramos um erro nosso, a correção vai para a página e para o registro de mudanças, com a data. " +
      "A lista está mais abaixo.",
  },
];

/** O que nenhuma conferência nossa alcança — dito nas páginas, repetido aqui. */
export const LIMITES: string[] = [
  "O preço em reais de alimento (pão, arroz, feijão, leite): o IBGE publica a variação desses preços, nunca o valor. Quem publica preço de alimento é instituto privado, que não usamos como número principal.",
  "Quantas pessoas estão em endividamento de risco por estado ou por cidade: o Banco Central calcula isso com a renda de cada devedor, que não está nos arquivos abertos do SCR — só publica o total do país.",
  "Quantas horas de trabalho custa uma TV ou um carro em cada país: exigiria o preço do mesmo modelo em cada lugar, que nenhum órgão público publica. O que existe é o nível de preços por categoria, do ICP.",
  "O preço da bomba comparado entre países: o indicador do Banco Mundial que trazia isso (EP.PMP.SGAS.CD) foi arquivado e não responde mais.",
  "Quanto do preço de um carro ou de uma geladeira é imposto: a abertura em imposto, insumo, frete e margem não é publicada por órgão oficial.",
  "Quanto de imposto cada família realmente pagou: o imposto sobre consumo está embutido no preço e ninguém o declara. O que existe é estimativa por modelo — e dois textos para discussão de instituições públicas, do Ipea (2022) e da Consultoria Legislativa do Senado (2024), chegam a conclusões opostas sobre o resultado. A seção /impostos/#quem-paga-mais publica os números de um e as objeções do outro, sem escolher.",
  "Se o morador respondeu certo ao recenseador, ou se o prestador declarou certo ao sistema do governo.",
  "Se a obra registrada como 'em execução' existe no mundo: a situação é declarada pelo próprio órgão.",
  "Se a nota fiscal de uma cota parlamentar corresponde ao serviço prestado. O link da nota está publicado; a conferência é caso a caso.",
  "Se o esgoto que entra na rede é tratado antes de voltar ao rio. O IBGE não pergunta isso.",
  "O que o governo não publica em formato aberto: gasto real de gabinete, salário de vereador, remuneração de governador, custo do TRF1.",
  "Fraude dentro do dado de origem. O que fazemos é cruzar fontes independentes; onde só existe uma, dizemos que só existe uma.",
];

/**
 * Afirmações que circulam sobre o dinheiro público, conferidas contra a fonte primária. Entram aqui as que
 * chegam por mensagem, notícia ou resposta de inteligência artificial — o que elas dizem, o que o dado mostra e
 * em que ponto as duas coisas se separam. Os valores do nosso lado são lidos dos JSONs pela própria página.
 */
export type Afirmacao = { afirma: string; dado: string; dado_calculado?: "cada100";
  veredito: "confere" | "ordem certa" | "nao_confere" | "sem_fonte"; };
export const AFIRMACOES: { titulo: string; origem: string; itens: Afirmacao[] } = {
  titulo: "Para onde vai o dinheiro: o que circula e o que o dado mostra",
  origem: "Texto recebido em 30/10/2026, com números declarados pelo próprio autor como \"de memória\". " +
    "Conferido contra SIOP, SICONFI, Tesouro, Receita Federal, IBGE e Banco Mundial, nas versões publicadas aqui.",
  itens: [
    { afirma: "Juros da dívida custam de 6% a 8% do PIB.",
      dado: "7,6% do PIB em 2025 — os juros nominais do Governo Central apurados pelo Tesouro.",
      veredito: "confere" },
    { afirma: "Em ano de juro alto, os juros passam saúde e educação somadas.",
      dado: "Nos três níveis de governo, saúde e educação somaram 10,6% do PIB em 2025, contra 7,6% dos juros nominais — e 3,1% se a comparação for com os juros efetivamente pagos no Orçamento. A frase só se sustenta comparando juros apropriados com a despesa paga de um nível só.",
      veredito: "nao_confere" },
    { afirma: "A previdência custa cerca de 13% do PIB.",
      dado: "O que dá para somar com dado aberto é 10,7% do PIB (União e estados). Faltam os regimes próprios dos municípios, e o número mistura o INSS com a aposentadoria do servidor, que são regimes diferentes.",
      veredito: "ordem certa" },
    { afirma: "O Brasil gasta cerca de 6% do PIB em educação, acima da média da OCDE.",
      dado: "5,8% somando os três níveis; 5,6% pelo Banco Mundial. A mediana dos 20 países de referência é 5,0%.",
      veredito: "confere" },
    { afirma: "Gasta cerca de 4% em saúde, contra 7% na OCDE.",
      dado: "4,8% nos três níveis; 4,3% de gasto público pelo Banco Mundial. A mediana dos 20 de referência é 6,4%.",
      veredito: "ordem certa" },
    { afirma: "O país paga mais de R$ 700 bilhões por ano só de juros.",
      dado: "R$ 891,9 bilhões de juros nominais em 2025; R$ 362,7 bilhões efetivamente pagos no Orçamento. São dois números diferentes e os dois são oficiais.",
      veredito: "confere" },
    { afirma: "O servidor federal ganha cerca de duas vezes o equivalente no setor privado.",
      dado: "Na PNAD Contínua, o rendimento médio no setor público é R$ 5.301 e no privado com carteira R$ 3.176 — 1,67 vez. A comparação não controla escolaridade nem função, então nenhum dos dois números mede \"equivalente\".",
      veredito: "ordem certa" },
    { afirma: "De cada R$ 100, R$ 40 vão para aposentadoria, R$ 20 para juros e R$ 25 para salário de servidor.",
      dado: "A folha de pessoal não aparece separada porque está dentro de cada função — o professor está em educação, o médico em saúde.",
      dado_calculado: "cada100", veredito: "nao_confere" },
    { afirma: "Pessoal nos três níveis ~10% do PIB; assistência ~2%; investimento público ~2%; renúncias fiscais ~4% a 5%.",
      dado: "Não temos essas quebras em fonte aberta comparável, e por isso não publicamos número nenhum nessas quatro linhas.",
      veredito: "sem_fonte" },
  ],
};

/** Correções que já fizemos no próprio site, com a data e como apareceram. */
export const CORRECOES: { data: string; painel: string; oQue: string; como: string }[] = [
  {
    data: "29/10/2026", painel: "Inflação",
    oQue: "A página tinha virado uma sequência de cartões defendendo que o salário mínimo subiu mais que os preços — verdade, " +
      "mas o salário mínimo é a única renda do país com aumento real garantido por lei, e a página quase não falava de quem não " +
      "ganha o mínimo. O dono disse que os números não traduziam a realidade; o problema era o protagonista, não a conta.",
    como: "Os cartões argumentativos saíram. Entrou um quadro com o rendimento real por tipo de ocupação (PNAD Contínua, 2012→2025): " +
      "quem trabalha ganhou 15,5% em treze anos, quem tem carteira no setor privado 8,3%, o empregador médio −0,5%; o próprio mínimo " +
      "subiu 17% nesse trecho — o salto dele foi antes de 2012. Ao lado, a parcela da renda comprometida com dívida (23,5% → 29,0%), " +
      "que não entra no IPCA. O aviso da página passou a dizer o que o índice não mede: compra de imóvel, juros, redução de embalagem.",
  },
  {
    data: "29/10/2026", painel: "Inflação",
    oQue: "A explicação do poder de compra usava um pão de R$ 0,10 em 1999 como âncora e concluía que ele custaria " +
      "R$ 0,68 hoje. O preço de 1999 era suposição nossa, não dado publicado — e o resultado, R$ 0,68, não bate com " +
      "a padaria de ninguém. O dono apontou.",
    como: "O exemplo passou a usar a gasolina, cujo preço a ANP publica em reais nos dois extremos da série: " +
      "R$ 180 ÷ R$ 1,68 = 107 litros em julho de 2001; R$ 1.621 ÷ R$ 6,54 = 248 litros hoje. Nenhum número estimado. " +
      "A página passou a dizer, onde cabe, que o IBGE publica a variação do preço do pão e nunca o preço — por isso " +
      "a tabela parte de uma coisa que custava R$ 1,00, e não de um preço inventado.",
  },
  {
    data: "28/10/2026", painel: "Estatais",
    oQue: "O lucro das estatais federais incluía R$ 30,9 bi de subvenção do Tesouro, que entra como receita na " +
      "demonstração. A página passou a mostrar o lucro com e sem, e a tabela das dependentes ganhou as duas colunas.",
    como: "O dono do site perguntou se a página não estava otimista demais. Estava.",
  },
  {
    data: "28/10/2026", painel: "Estatais",
    oQue: "A lista de empresas tinha 14 e deixava de fora estatais com ações em bolsa (Banco do Nordeste, Banco da " +
      "Amazônia, Celesc, Casan, Saneago, Cagece, Cedae, Metrô de São Paulo, entre outras). Passou a 33.",
    como: "Varredura do próprio arquivo da CVM em busca de acionista que é ente público, em vez de lista escolhida a dedo.",
  },
  {
    data: "28/10/2026", painel: "Tribunais superiores",
    oQue: "A remuneração dos ministros do STJ estava sendo lida pela coluna que inclui indenizações, enquanto a do " +
      "STF não as inclui. A comparação entre tribunais inflava cerca de 30%.",
    como: "Conferência linha a linha de um mês de folha, procurando por que um tribunal destoava tanto.",
  },
  {
    data: "28/10/2026", painel: "Estatais e Saneamento",
    oQue: "Ano recém-aberto, com poucas empresas ou poucos respondentes, podia virar 'o último ano' da página inteira, " +
      "com tabela quase vazia. Agora só entra o ano com pelo menos metade dos registros do ano mais cheio.",
    como: "Revisão do que aconteceria na virada do ano, antes de acontecer.",
  },
  {
    data: "27/10/2026", painel: "Inflação",
    oQue: "A tabela 'quanto os preços subiram desde…' tinha rótulos ambíguos, que davam a entender dinheiro guardado " +
      "em casa. Os rótulos foram trocados.",
    como: "O dono do site apontou a ambiguidade.",
  },
  {
    data: "26/10/2026", painel: "Deputados",
    oQue: "O subsídio estava com a data do reajuste errada (fevereiro de 2026 em vez de fevereiro de 2025), o que " +
      "mudava o custo calculado de todos os deputados.",
    como: "Conferência das constantes contra o decreto legislativo que as fixa.",
  },
  {
    data: "26/10/2026", painel: "Poderes",
    oQue: "A despesa do Legislativo, do Judiciário e do Ministério Público nunca aparecia. A fonte foi trocada do " +
      "Portal da Transparência para o SIOP, que cobre todos os Poderes.",
    como: "O número não fechava com o Orçamento, e a documentação do próprio Portal dizia que a API só cobre o Executivo.",
  },
];
