/**
 * Endividamento de risco — números lidos do Relatório de Estabilidade Financeira do Banco Central, volume 25,
 * outubro de 2026 (PDF). Como não há API para eles, ficam aqui como constantes declaradas, cada bloco com a
 * página de onde foi lido e a data da leitura — o mesmo padrão de `comparacao.ts` e `beneficios.ts`.
 *
 * O que NÃO está aqui, de propósito: os valores de comprometimento de renda por faixa de salário mínimo. Eles
 * existem só como rótulo de gráfico no PDF (Gráfico 1.2.2.12), e ler número de gráfico é chute com régua. As
 * séries agregadas equivalentes vêm da API do SGS e estão em `credito.json`, bloco `familias`.
 */
export const FONTE_REF = {
  nome: "Banco Central do Brasil — Relatório de Estabilidade Financeira, volume 25",
  edicao: "outubro de 2026",
  url: "https://www.bcb.gov.br/content/publicacoes/ref/202610/RELESTAB202610-refPub.pdf",
  lido: "29/10/2026",
};

/** Definição oficial: é endividado de risco quem atende a DOIS OU MAIS destes critérios (REF, nota 70, p. 72). */
export const CRITERIOS: { titulo: string; detalhe: string }[] = [
  { titulo: "Atraso de mais de 90 dias", detalhe: "Deixou de pagar parcela de crédito há mais de três meses — é a mesma inadimplência que o painel mede pelo SCR." },
  { titulo: "Mais de 50% da renda na dívida", detalhe: "O pagamento mensal das dívidas consome mais da metade do que a pessoa recebe no mês." },
  { titulo: "Sobra abaixo da linha da pobreza", detalhe: "O que resta da renda depois de pagar as dívidas do mês fica abaixo da linha de pobreza." },
  { titulo: "Três créditos caros ao mesmo tempo", detalhe: "Usa simultaneamente cheque especial, crédito pessoal sem consignação e rotativo do cartão — as três modalidades mais caras." },
];

/** Gráfico 2.3.1 (p. 77): percentual dos devedores do SFN em endividamento de risco, de seis em seis meses. */
export const SERIE_RISCO: { periodo: string; pct: number }[] = [
  { periodo: "jun/2021", pct: 9.7 }, { periodo: "dez/2021", pct: 11.1 },
  { periodo: "jun/2022", pct: 13.1 }, { periodo: "dez/2022", pct: 13.6 },
  { periodo: "jun/2023", pct: 13.8 }, { periodo: "dez/2023", pct: 13.0 },
  { periodo: "jun/2024", pct: 13.1 }, { periodo: "dez/2024", pct: 13.4 },
  { periodo: "jun/2025", pct: 14.7 }, { periodo: "dez/2025", pct: 16.5 },
  { periodo: "jun/2026", pct: 17.0 },
];

/** Texto da p. 77, palavra por palavra do relatório. */
export const RISCO = {
  pessoas: 20_300_000,
  pct_devedores: 17,
  variacao_5_anos: 75,
  referencia: "junho de 2026",
  base: "junho de 2021",
  pagina: 77,
};

/**
 * Quantidade de tomadores por faixa de renda (Boxe 3, gráficos 1.2.2.24.a a .d, p. 37–38). Universo diferente
 * do de cima: aqui só entram os tomadores com renda conhecida e carteira acima de R$ 200, que é o cálculo do
 * comprometimento de renda individual. Por isso a soma não bate com os devedores do SFN — e a página diz isso.
 */
export const TOMADORES_POR_FAIXA: { faixa: string; milhoes: number }[] = [
  { faixa: "Até 2 salários mínimos", milhoes: 61.2 },
  { faixa: "Entre 2 e 5 salários mínimos", milhoes: 22.3 },
  { faixa: "Entre 5 e 10 salários mínimos", milhoes: 7.5 },
  { faixa: "Acima de 10 salários mínimos", milhoes: 4.4 },
];

/** Frases do relatório que explicam o movimento, citadas com a página. Não são opinião do site. */
export const ACHADOS: { texto: string; pagina: number }[] = [
  { texto: "A capacidade de pagamento das pessoas físicas permanece desafiadora, com o maior nível da série histórica de comprometimento de renda e o aumento da participação de modalidades mais caras.", pagina: 31 },
  { texto: "Independentemente da faixa de renda, os produtos mais relevantes para tomadores com comprometimento de renda mais elevado são o cartão de crédito e o crédito não consignado.", pagina: 37 },
  { texto: "Consumidores de menor renda recebem, em média, nove ofertas de crédito por mês, e parte dessas ofertas resulta em contratações não planejadas, inclusive por pessoas que inicialmente não buscavam crédito.", pagina: 78 },
];
