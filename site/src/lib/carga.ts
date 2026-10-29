/**
 * Carga tributária bruta do Governo Geral — a medida do Tesouro Nacional, que sai em abril do ano seguinte, antes
 * do estudo da Receita Federal (que traz as tabelas completas e alimenta o resto da página). Não há API nem arquivo
 * aberto do boletim; o número vem da divulgação oficial do Ministério da Fazenda, como constante com fonte e data.
 * Receita e Tesouro medem a mesma coisa com pequenas diferenças de método: para 2024, 32,20% e 32,22%.
 */
export const CARGA_TESOURO = {
  ano: 2025,
  total_pct_pib: 32.40,
  por_ente: [
    { ente: "União", pct_pib: 21.60 },
    { ente: "Estados", pct_pib: 8.38 },
    { ente: "Municípios", pct_pib: 2.43 },
  ],
  ano_anterior: { ano: 2024, total_pct_pib: 32.22 },
  fonte: "Tesouro Nacional, Boletim de Estimativa da Carga Tributária Bruta do Governo Geral — 2025 (publicado em 10/04/2026), conforme divulgação do Ministério da Fazenda",
  url: "https://www.gov.br/fazenda/pt-br/assuntos/noticias/2026/abril/carga-tributaria-bruta-do-governo-geral-atinge-32-40-do-pib-em-2025-mostra-boletim-do-tesouro-nacional",
  lido: "29/10/2026",
};
