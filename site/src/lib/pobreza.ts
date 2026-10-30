/**
 * O que a lei brasileira define sobre renda — e o que ela não define.
 *
 * O Estado fixa em lei um valor de renda por pessoa para dizer quem é pobre o bastante para receber transferência.
 * Não existe norma equivalente dizendo o que é renda alta: nenhuma lei, decreto ou instrução normativa define
 * "rico", "classe alta" ou "alta renda" com um valor. As classes A/B/C/D/E que circulam na imprensa são o Critério
 * Brasil, da ABEP — associação privada de empresas de pesquisa —, e por isso não entram aqui como medida.
 *
 * Constante declarada com documento, artigo e data de leitura, no padrão de `comparacao.ts` e `endividamento.ts`.
 */
export const LINHA_LEGAL = {
  norma: "Lei nº 14.601, de 19 de junho de 2023 (Programa Bolsa Família)",
  artigo: "art. 5º, inciso II",
  valor_per_capita: 218,
  texto: "cuja renda familiar per capita mensal seja igual ou inferior a R$ 218,00",
  url: "https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/lei/L14601.htm",
  lido: "30/10/2026",
  nota:
    "É o limite de entrada no programa, não uma definição teórica de pobreza — a própria lei não conceitua o termo. " +
    "O valor é o que está escrito na lei; a operação do programa é ajustada por regulamento.",
};

/** Não existe o outro lado. Isto é uma afirmação sobre ausência, e está aqui para ser contestada com a norma, se existir. */
export const SEM_LINHA_DE_RIQUEZA = {
  afirmacao:
    "Não encontramos norma federal que defina renda alta, classe alta ou riqueza por um valor de renda. O que existe " +
    "de oficial são cortes estatísticos do IBGE (os percentis) e faixas de tributação da Receita Federal — nenhum " +
    "deles chamado de 'rico' pela fonte.",
  criterio_privado:
    "O A/B/C/D/E do noticiário é o Critério Brasil, da Associação Brasileira de Empresas de Pesquisa (ABEP). É " +
    "classificação de consumo feita por entidade privada, e este site não usa fonte de terceiro como medida.",
};
