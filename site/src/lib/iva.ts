/**
 * IVA — o imposto sobre valor agregado que a reforma tributária (EC 132/2023, LC 214/2025) cria no Brasil, em
 * dois pedaços: CBS (federal) e IBS (estados e municípios). Nada aqui tem API: são constantes declaradas, cada
 * bloco com fonte, URL e data de leitura — o padrão de `comparacao.ts` e `endividamento.ts`.
 *
 * A alíquota brasileira ainda NÃO existe: é estimativa de referência, calculada para que os dois impostos
 * arrecadem o mesmo que os cinco que substituem. Só será fixada por resolução do Senado, e a página diz isso.
 */
export const ALIQUOTA = {
  referencia: 27.91, ibs: 18.70,
  // 27,91 e 18,70 estão no Quadro 2 da resolução. A fatia da CBS NÃO está: é a diferença entre os dois, conta
  // nossa, e por isso vai declarada como tal em vez de aparecer como número do Comitê.
  cbs: 9.21, cbs_e_conta_nossa: true,
  trava: 26.5,          // LC 214/2025: se a soma passar de 26,5% em 2031, o Executivo propõe corte de benefícios
  fonte: "Comitê Gestor do IBS, Resolução CGIBS nº 14, de 29 de julho de 2026, Quadro 2 (Cálculo da Alíquota de Referência do IBS Adotada); trava de 26,5% na LC 214/2025",
  url: "https://cgibs.gov.br/upload/arquivos/202607/31144942-resoluc-ao-cgibs-n-14-de-29-de-julho-de-2026-proposta-percentual-ibs-cgibs-2027.pdf",
  lido: "30/10/2026",
  nota: "A própria resolução diz que a estimativa tem caráter prospectivo e foi feita para a proposta orçamentária do Comitê de 2027 — a alíquota de referência definitiva é fixada pelo Senado. A estimativa anterior, do Ministério da Fazenda (2024), era de 26,5%.",
};

/** Maiores alíquotas-padrão de IVA em vigor. OCDE, Consumption Tax Trends 2024, com as mudanças de 2025. */
export const MAIORES_IVA: { pais: string; iso3: string; aliquota: number }[] = [
  { pais: "Hungria", iso3: "HUN", aliquota: 27 },
  { pais: "Finlândia", iso3: "FIN", aliquota: 25.5 },
  { pais: "Dinamarca", iso3: "DNK", aliquota: 25 },
  { pais: "Suécia", iso3: "SWE", aliquota: 25 },
  { pais: "Noruega", iso3: "NOR", aliquota: 25 },
  { pais: "Croácia", iso3: "HRV", aliquota: 25 },
  { pais: "Estônia", iso3: "EST", aliquota: 24 },
  { pais: "Grécia", iso3: "GRC", aliquota: 24 },
  { pais: "Islândia", iso3: "ISL", aliquota: 24 },
  { pais: "Portugal", iso3: "PRT", aliquota: 23 },
  { pais: "Irlanda", iso3: "IRL", aliquota: 23 },
  { pais: "Polônia", iso3: "POL", aliquota: 23 },
  { pais: "Eslováquia", iso3: "SVK", aliquota: 23 },
];
export const FONTE_OCDE = {
  nome: "OCDE, Consumption Tax Trends 2024 (alíquotas-padrão de IVA), com as mudanças de 2025 (Finlândia 25,5%, Estônia 24%, Eslováquia 23%)",
  url: "https://www.oecd.org/en/publications/consumption-tax-trends-2024_dcd4dd36-en.html",
  lido: "29/10/2026",
};

/** O que fica fora da alíquota cheia (LC 214/2025). Cada exceção empurra a alíquota de quem não tem exceção. */
export const EXCECOES: { regime: string; quem: string }[] = [
  { regime: "Alíquota zero", quem: "Cesta básica nacional; frutas, hortaliças e ovos; medicamentos de uma lista; dispositivos de acessibilidade; serviços de educação do Prouni" },
  { regime: "Redução de 60%", quem: "Saúde, educação, medicamentos e dispositivos médicos em geral, transporte coletivo, produtos agropecuários in natura, insumos agropecuários, produções artísticas e culturais, atividades desportivas" },
  { regime: "Redução de 30%", quem: "Profissões intelectuais regulamentadas (advogados, contadores, engenheiros, médicos…)" },
  { regime: "Regimes próprios", quem: "Combustíveis, serviços financeiros, planos de saúde, operações com imóveis, cooperativas, sociedades anônimas de futebol, concursos de prognósticos" },
  { regime: "Fora do IVA", quem: "Simples Nacional (continua no regime próprio, com opção), Zona Franca de Manaus (crédito presumido)" },
];

/** Calendário da transição (EC 132/2023 e LC 214/2025). */
export const CALENDARIO: { ano: string; oQue: string }[] = [
  { ano: "2026", oQue: "Alíquota-teste: 0,9% de CBS e 0,1% de IBS, compensáveis com PIS/Cofins. Serve para calibrar, não para arrecadar." },
  { ano: "2027", oQue: "CBS entra com a alíquota cheia; PIS e Cofins são extintos; IPI vai a zero (exceto para a Zona Franca)." },
  { ano: "2029–2032", oQue: "ICMS e ISS caem a 9/10, 8/10, 7/10 e 6/10 das alíquotas de hoje, um degrau por ano, enquanto o IBS sobe na mesma proporção." },
  { ano: "2033", oQue: "ICMS e ISS extintos. O IVA dual (CBS + IBS) passa a ser o único imposto sobre consumo." },
];
export const FONTE_LEI = {
  nome: "Emenda Constitucional 132/2023 e Lei Complementar 214/2025",
  url: "https://www.planalto.gov.br/ccivil_03/leis/lcp/Lcp214.htm",
  lido: "29/10/2026",
};
