/**
 * Lei nº 15.270, de 26 de novembro de 2025 — a norma que isentou o imposto de renda até R$ 5.000 por mês e criou
 * uma tributação mínima sobre altas rendas, incluindo lucros e dividendos na base.
 *
 * Está aqui porque é a resposta documental a "nos últimos 20 anos defendeu-se taxar os mais ricos; aconteceu?".
 * Números e artigos lidos no texto da lei no Planalto, não em notícia. A lei vigora desde 1º/01/2026, então os
 * efeitos ainda NÃO aparecem em nenhuma série de arrecadação que o site publica — o último ano fechado da OCDE é
 * 2024 e o dos Grandes Números do IRPF é o ano-calendário 2024. A página diz isso.
 */
export const LEI_ALTAS_RENDAS = {
  norma: "Lei nº 15.270, de 26 de novembro de 2025",
  ano: 2025,
  url: "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2025/lei/L15270.htm",
  lido: "30/10/2026",
  vigencia: "1º de janeiro de 2026",
  vigencia_artigo: "art. 8º",
  isencao: {
    artigo: "art. 3º-A",
    ate: 5000,
    reducao_parcial_ate: 7350,
    texto: "Redução que zera o imposto mensal para rendimento tributável de até R$ 5.000,00, decrescente de R$ 5.000,01 a R$ 7.350,00.",
  },
  minima: {
    artigo: "art. 16-A",
    piso_anual: 600000,
    aliquota_cheia_a_partir_de: 1200000,
    aliquota_maxima_pct: 10,
    dividendos_na_base: true,
    texto:
      "Tributação mínima da pessoa física para quem soma mais de R$ 600.000,00 de rendimentos no ano, chegando a " +
      "10% a partir de R$ 1.200.000,00. Lucros e dividendos entram na base de cálculo, com as exclusões dos incisos " +
      "I a XII do § 1º.",
  },
  /** O que a lei NÃO faz — para a página não sugerir mais do que o documento diz. */
  limites:
    "A lei fixa um piso de tributação, não uma alíquota nova sobre dividendos: quem já paga 10% ou mais sobre o " +
    "conjunto da renda não recolhe nada a mais. E a isenção de lucros e dividendos na declaração, da Lei 9.249/1995, " +
    "continua na lei — o que mudou foi a existência de um mínimo no topo.",
};
