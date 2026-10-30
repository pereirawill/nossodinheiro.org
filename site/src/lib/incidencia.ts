/**
 * Quem paga mais imposto, em proporção da renda — números lidos de dois textos para discussão de instituições
 * públicas que chegam a conclusões opostas. Não há API para nenhum deles; ficam aqui como constantes declaradas,
 * cada bloco com a página/gráfico de onde saiu e a data da leitura, no padrão de `endividamento.ts`,
 * `comparacao.ts` e `beneficios.ts`.
 *
 * Os dois são "texto para discussão": publicação de pesquisa de órgão público que, por regra da própria casa,
 * NÃO é posição oficial do órgão. Os dois trazem essa ressalva impressa e ela está citada abaixo e na página.
 *
 * O que NÃO está aqui, de propósito:
 *
 * 1. A decomposição do índice de Gini por etapa (gráfico 8 do TD do Ipea). Os seis valores do gráfico são
 *    rótulos soltos, e o texto que os comenta atribui a variação de 5,22% à renda total enquanto os valores
 *    só fecham se ela for da renda monetária — as outras duas frases do mesmo parágrafo apontam para a
 *    atribuição contrária. Não dá para saber qual série é qual sem ler o gráfico renderizado, e ler número de
 *    gráfico é chute com régua. Ficou só a frase final, que está no texto corrido e não depende do gráfico.
 *
 * 2. O "45% da carga em produção e consumo contra 32% na OCDE" que o TD do Ipea cita da RFB (2020). A página
 *    já publica 43,5% da tabela INC 01-A do estudo da Receita, lida por nós direto da fonte. São edições e
 *    recortes diferentes; usar os dois lado a lado sem explicar a diferença seria confundir.
 */

export const FONTE_IPEA = {
  nome: "Ipea — Texto para Discussão nº 2.823, Tributação indireta: alíquotas efetivas e incidência sobre as famílias",
  autores: "Fernando Gaiger Silveira, Theo Ribas Palomo, Felipe Moraes Cornelio e Marcelo Resende Tonon",
  edicao: "dezembro de 2022",
  base: "microdados da POF 2017-2018 (IBGE)",
  url: "https://repositorio.ipea.gov.br/handle/11058/11624",
  lido: "30/10/2026",
  ressalva:
    "As opiniões emitidas nesta publicação são de exclusiva e inteira responsabilidade dos autores, não exprimindo, " +
    "necessariamente, o ponto de vista do Instituto de Pesquisa Econômica Aplicada ou do Ministério da Economia.",
};

export const FONTE_SENADO = {
  nome: "Senado Federal, Consultoria Legislativa — Texto para Discussão nº 328, A hipertributação dos pobres no Brasil: um mito influente",
  autores: "Marcos Antonio Köhler",
  edicao: "abril de 2024",
  url: "https://www12.senado.leg.br/publicacoes/estudos-legislativos/tipos-de-estudos/textos-para-discussao/td328",
  lido: "30/10/2026",
  ressalva:
    "O conteúdo deste trabalho é de responsabilidade dos autores e não representa posicionamento oficial do Senado Federal.",
};

/**
 * Gráfico 3 do TD 2.823: incidência sobre a renda total, por décimo de renda familiar per capita.
 * Conferido contra o texto corrido, que diz "a incidência nos 10% mais pobres alcançando 26,4%, ao passo que
 * nos 10% mais ricos os tributos representam 19,2% da renda" — 3,0 + 23,4 e 10,6 + 8,6. E contra a seção 4,
 * que dá 23,42% e 8,62% para os indiretos nas duas pontas.
 */
export const DECIS: { decil: number; direto: number; indireto: number }[] = [
  { decil: 1, direto: 3.0, indireto: 23.4 },
  { decil: 2, direto: 3.8, indireto: 17.3 },
  { decil: 3, direto: 3.8, indireto: 15.6 },
  { decil: 4, direto: 4.3, indireto: 14.3 },
  { decil: 5, direto: 4.9, indireto: 14.0 },
  { decil: 6, direto: 5.0, indireto: 13.1 },
  { decil: 7, direto: 5.6, indireto: 12.7 },
  { decil: 8, direto: 6.7, indireto: 12.5 },
  { decil: 9, direto: 8.2, indireto: 11.5 },
  { decil: 10, direto: 10.6, indireto: 8.6 },
];

/** Média do conjunto (última coluna dos gráficos 2 e 3): é a razão do total, puxada pelo topo, não a média dos décimos. */
export const MEDIA = { direto: 8.0, indireto: 11.2 };

/**
 * Seção 4 do TD 2.823: a resposta muda conforme o que se põe no denominador. Os próprios autores discutem os
 * três parâmetros e explicam por que escolheram a renda total. Os números são do texto corrido, não de gráfico.
 */
export const PARAMETROS: {
  parametro: string;
  oQue: string;
  primeiro: number;
  ultimo: number;
  decimais: 1 | 2;              // quantas casas o texto do estudo publica — não inventar precisão
  escolhido?: boolean;
  nota: string;
}[] = [
  {
    parametro: "Renda monetária",
    oQue: "Só o dinheiro que entra: salário, aposentadoria, aluguel recebido, programa social.",
    primeiro: 42.66,
    ultimo: 9.5,
    decimais: 2,
    nota:
      "É o número mais extremo. Os autores não o adotam porque a renda declarada nas pesquisas domiciliares é " +
      "subestimada — e, segundo eles, em toda a distribuição, não só embaixo.",
  },
  {
    parametro: "Renda total",
    oQue: "O dinheiro mais o que a família consome sem pagar: aluguel do imóvel próprio, comida de produção própria, doações.",
    primeiro: 23.42,
    ultimo: 8.62,
    decimais: 2,
    escolhido: true,
    nota: "É o parâmetro que o estudo adota, e é o que alimenta todos os outros números desta seção.",
  },
  {
    parametro: "Despesa de consumo",
    oQue: "O quanto a família gasta, em vez do quanto ganha.",
    primeiro: 23.8,
    ultimo: 19.6,
    decimais: 1,
    nota:
      "Quase emparelha as pontas, e é o parâmetro defendido por quem contesta a tese da regressividade: ele supõe " +
      "que o que hoje é poupado será consumido (e tributado) mais tarde. Mesmo assim o estudo encontra queda — " +
      "22,1% no quinto décimo.",
  },
];

/** Gráfico 4 do TD 2.823: alíquota efetiva dos tributos indiretos embutida em cada grupo de consumo. */
export const RUBRICAS: { rubrica: string; aliquota: number }[] = [
  { rubrica: "Educação", aliquota: 7.8 },
  { rubrica: "Serviços pessoais", aliquota: 8.8 },
  { rubrica: "Habitação", aliquota: 11.0 },
  { rubrica: "Alimentação", aliquota: 15.0 },
  { rubrica: "Assistência à saúde", aliquota: 15.4 },
  { rubrica: "Despesas diversas", aliquota: 15.8 },
  { rubrica: "Vestuário", aliquota: 20.4 },
  { rubrica: "Cultura", aliquota: 21.1 },
  { rubrica: "Transporte", aliquota: 23.3 },
  { rubrica: "Higiene", aliquota: 25.9 },
];

/**
 * Gráfico 6 do TD 2.823: composição da despesa de consumo por estrato de renda familiar per capita.
 * A leitura dos rótulos foi conferida contra quatro afirmações do texto corrido — alimentação como segunda
 * rubrica dos 40% mais pobres, higiene empatando com saúde nesse estrato, transporte perto de 1/4 nos 20%
 * mais ricos e alimentação abaixo de 1/5 neles. As três colunas somam 100% (com arredondamento).
 */
export const COMPOSICAO: { rubrica: string; pobres: number; meio: number; ricos: number }[] = [
  { rubrica: "Habitação", pobres: 29, meio: 26, ricos: 25 },
  { rubrica: "Alimentação", pobres: 26, meio: 21, ricos: 17 },
  { rubrica: "Transporte", pobres: 16, meio: 21, ricos: 24 },
  { rubrica: "Higiene", pobres: 7, meio: 5, ricos: 3 },
  { rubrica: "Assistência à saúde", pobres: 7, meio: 9, ricos: 11 },
  { rubrica: "Vestuário", pobres: 6, meio: 5, ricos: 4 },
  { rubrica: "Educação", pobres: 4, meio: 5, ricos: 7 },
  { rubrica: "Cultura", pobres: 2, meio: 3, ricos: 3 },
  { rubrica: "Despesas diversas", pobres: 2, meio: 3, ricos: 5 },
  { rubrica: "Serviços pessoais", pobres: 2, meio: 2, ricos: 2 },
];

export const ESTRATOS = { pobres: "40% mais pobres", meio: "40% do meio", ricos: "20% mais ricos" };

/**
 * Efeito líquido sobre a desigualdade. Frase do texto corrido do TD 2.823 (seção 6) — não do gráfico 8,
 * cujos rótulos não fecham com o comentário (ver cabeçalho deste arquivo).
 */
export const EFEITO_DESIGUALDADE = {
  texto:
    "Da renda inicial para a renda pós-tributação, esse índice aumenta em 3,26% no caso da parcela de " +
    "rendimentos monetários e em 1,19% se considerados os rendimentos totais.",
  leitura:
    "Ou seja: pela conta desse estudo, a desigualdade medida pelo índice de Gini termina maior depois dos " +
    "impostos do que era antes deles. Os tributos diretos a reduzem um pouco; os indiretos a aumentam mais.",
};

/** As cinco lacunas que o TD 328 do Senado aponta no TD do Ipea. Resumidas da lista da p. 1–2 do texto. */
export const CRITICAS: { titulo: string; detalhe: string }[] = [
  {
    titulo: "A POF não vê dois terços da carga",
    detalhe:
      "A renda captada na pesquisa responde por cerca de 12,3% do PIB em tributos, de uma carga de 33,6%. O resto " +
      "incide fora do orçamento das famílias pesquisadas e não entra na conta.",
  },
  {
    titulo: "Subsídios cruzados e subvenções ficam de fora",
    detalhe:
      "Tarifa social de energia e água, gratuidade e subvenção no transporte coletivo e no gás de cozinha reduzem o " +
      "preço pago pelas famílias de renda baixa, mas não aparecem como abatimento na conta do imposto.",
  },
  {
    titulo: "Serviço público gratuito não entra na renda",
    detalhe:
      "Se a escolha metodológica é usar a renda total, com a parte não monetária, então saúde e educação públicas e " +
      "habitação popular subsidiada também deveriam entrar — e são mais usadas por quem tem menos renda.",
  },
  {
    titulo: "Alíquotas estimadas com inconsistências",
    detalhe:
      "A matriz insumo-produto é agregada demais para a especificidade da lei tributária: o texto aponta itens da " +
      "cesta básica com alíquota estimada acima de 19% e materiais de construção com alíquota zero.",
  },
  {
    titulo: "O imposto das empresas não é atribuído aos donos",
    detalhe:
      "IRPJ e CSLL somam cerca de 2,85% do PIB e, economicamente, recaem sobre acionistas e proprietários — que " +
      "estão nos décimos mais altos. O estudo não os imputa a ninguém.",
  },
];

/** O que o TD 328 declara explicitamente que NÃO faz. É a frase decisiva para o leitor avaliar a controvérsia. */
export const LIMITE_CRITICA =
  "Mensurar o grau dessa progressividade foge ao escopo deste artigo, mas sua existência é incontestável, pelos argumentos já apresentados.";
