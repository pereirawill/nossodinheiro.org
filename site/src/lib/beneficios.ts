/**
 * Benefícios e verbas de deputados, senadores e ministros do STF — lista fixa, com fonte e data em cada linha.
 * Não existe API para regras; aqui entra só o que a própria instituição publica. "uso" diz se a casa
 * publica quem usa / quanto usou por pessoa (e, quando sim, se já está num painel do site).
 * Mudou um valor → mude aqui e em docs/metodologia/painel-beneficios.md na mesma alteração.
 */
export type Beneficio = {
  item: string;
  valor: string;          // valor ou regra, em uma frase
  uso: "sim" | "parcial" | "nao";
  usoNota?: string;       // onde o uso por pessoa aparece
  fonte: string;          // norma e/ou página oficial
  url?: string;
  lido: string;           // data de leitura (AAAA-MM-DD)
  noCusto?: "sim" | "nao" | "teto"; // entra no custo calculado pelos painéis? (sim = gasto real; teto = limite)
};

export const LIDO = "2026-10-26";

export const DEPUTADOS: Beneficio[] = [
  { item: "Subsídio", valor: "R$ 46.366,19 por mês desde 1º/fev/2025, mais 13º subsídio e ⅓ de férias. Igual ao dos senadores (CF art. 49, VII). Falta não justificada em sessão deliberativa desconta.",
    uso: "sim", usoNota: "contracheque na transparência da Câmara", fonte: "Decreto Legislativo 172/2022, art. 1º; Câmara, esclarecimentos sobre consulta de remuneração", url: "https://www2.camara.leg.br/comunicacao/assessoria-de-imprensa/guia-para-jornalistas/salario-de-deputados", lido: LIDO, noCusto: "sim" },
  { item: "Ajuda de custo (mudança)", valor: "1 subsídio no início e 1 no fim do mandato, para mudança e transporte. Não é paga a reeleito, a residente no DF nem a quem assume só no recesso. É isso que circula como \"auxílio-paletó\": o nome é falso, a verba é esta.",
    uso: "nao", fonte: "DL 172/2022, art. 1º, §1º; Câmara, Comprove (\"É falso que os deputados recebem auxílio-paletó…\")", url: "https://www.camara.leg.br/comprove/1175595-e-falso-que-os-deputados-recebem-auxilios-paleto-educacao-restaurante-cultural-e-farmacia/", lido: LIDO, noCusto: "nao" },
  { item: "Cota parlamentar (CEAP)", valor: "Reembolso mensal de despesas do mandato (passagens, divulgação, aluguel de carro e escritório, combustível, celular…). Teto varia por estado conforme o preço da passagem a Brasília; o que não é usado no mês acumula no ano.",
    uso: "sim", usoNota: "por nota fiscal; painel Deputados", fonte: "Ato da Mesa 43/2009; Câmara, Gastos parlamentares", url: "https://www.camara.leg.br/transparencia/gastos-parlamentares", lido: LIDO, noCusto: "sim" },
  { item: "Verba de gabinete", valor: "Até R$ 165.806,07 por mês para contratar até 25 secretários parlamentares (salários de R$ 1.710,83 a R$ 25.958,90). 13º, férias e auxílio-alimentação dos secretários são pagos à parte pela Câmara. Em 2026, 75% do limite foi usado.",
    uso: "parcial", usoNota: "gasto real por deputado só na página da Câmara (não em dado aberto); o painel usa o teto", fonte: "Câmara, Gastos parlamentares", url: "https://www.camara.leg.br/transparencia/gastos-parlamentares", lido: LIDO, noCusto: "teto" },
  { item: "Apartamento funcional", valor: "447 apartamentos da Câmara em Brasília; 409 ocupados em 2026.", uso: "sim", usoNota: "por deputado na página da Câmara", fonte: "Câmara, Gastos parlamentares", url: "https://www.camara.leg.br/transparencia/gastos-parlamentares", lido: LIDO, noCusto: "nao" },
  { item: "Auxílio-moradia", valor: "R$ 4.253,00 por mês para quem não ocupa apartamento funcional (130 deputados em 2026); pode complementar com até R$ 4.148,80 da cota se o aluguel for maior (75 fazem isso).",
    uso: "sim", usoNota: "por deputado na página da Câmara; ainda não no painel", fonte: "Câmara, Gastos parlamentares", url: "https://www.camara.leg.br/transparencia/gastos-parlamentares", lido: LIDO, noCusto: "nao" },
  { item: "Saúde", valor: "Reembolso de despesas médicas, hospitalares e odontológicas só do próprio deputado, sem valor fixo, conforme orçamento (pedidos até R$ 135.400 decididos pelo 2º vice-presidente). Alternativa: aderir ao Pró-Saúde dos servidores pagando contribuição mensal, aí com dependentes.",
    uso: "nao", fonte: "Ato da Mesa 89/2013; Câmara, guia \"Atendimento médico para deputados\"", url: "https://www2.camara.leg.br/comunicacao/assessoria-de-imprensa/guia-para-jornalistas/atendimento-medico-para-deputados", lido: LIDO, noCusto: "nao" },
  { item: "Diárias de viagem oficial", valor: "R$ 842 por dia no Brasil; US$ 391 (América do Sul) e US$ 428 (demais países).", uso: "parcial", usoNota: "total anual publicado", fonte: "Câmara, Gastos parlamentares", url: "https://www.camara.leg.br/transparencia/gastos-parlamentares", lido: LIDO, noCusto: "nao" },
  { item: "Aposentadoria (PSSC)", valor: "Plano de Seguridade Social dos Congressistas, opcional e contributivo: 65 anos (homens) ou 62 (mulheres) e tempo de contribuição com pedágio de 30% sobre o que faltava em 13/11/2019.",
    uso: "nao", fonte: "Lei 9.506/1997; EC 103/2019; FAQ do Senado (mesmo plano)", url: "https://www12.senado.leg.br/perguntas-frequentes/canais-de-atendimento/senadores/como-funciona-a-aposentadoria-dos-senadores", lido: LIDO, noCusto: "nao" },
  { item: "Passaporte diplomático", valor: "Durante o mandato.", uso: "nao", fonte: "Decreto 5.978/2006, art. 6º", url: "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/decreto/d5978.htm", lido: LIDO, noCusto: "nao" },
];

export const SENADORES: Beneficio[] = [
  { item: "Subsídio", valor: "R$ 46.366,19 por mês desde 1º/fev/2025, igual ao dos deputados. 13º e ⅓ de férias: a Câmara confirma para deputados; para senadores assumimos o mesmo (premissa marcada na metodologia).",
    uso: "sim", usoNota: "\"Subsídios do Senador\" na transparência do Senado", fonte: "DL 172/2022; FAQ do Senado \"Quanto ganha um senador?\"", url: "https://www12.senado.leg.br/perguntas-frequentes/canais-de-atendimento/senadores/quanto-ganha-um-senador", lido: LIDO, noCusto: "sim" },
  { item: "Ajuda de custo (mudança)", valor: "1 subsídio no início e 1 no fim do mandato (DL 172/2022). O FAQ do Senado ainda cita R$ 33.763 do DL 276/2014, valor superado.",
    uso: "nao", fonte: "DL 172/2022, art. 1º, §1º; FAQ do Senado \"Os senadores recebem mais alguma verba…?\"", url: "https://www12.senado.leg.br/perguntas-frequentes/canais-de-atendimento/senadores/os-senadores-recebem-mais-alguma-verba-alem-do-subsidio", lido: LIDO, noCusto: "nao" },
  { item: "Cota (CEAPS)", valor: "Por mês: R$ 15.000 fixos mais o valor de 5 passagens Brasília–capital do estado (tabela IATA governo). Vai de cerca de R$ 21 mil (DF, GO) a cerca de R$ 44 mil (AM). Reembolsa aluguel de escritório, locomoção e hospedagem, serviços de apoio, divulgação, passagens, material, segurança.",
    uso: "sim", usoNota: "por categoria e por nota; painel Senadores", fonte: "Ato da Comissão Diretora 3/2003 e 9/2011; FAQ do Senado", url: "https://www12.senado.leg.br/perguntas-frequentes/canais-de-atendimento/senadores/os-senadores-recebem-mais-alguma-verba-alem-do-subsidio", lido: LIDO, noCusto: "sim" },
  { item: "Gastos fora da cota", valor: "O Senado paga diretamente e publica por senador: diárias de viagem oficial, passagens aéreas compradas pelo Senado (ATC 2/2023), correios, material, impulsionamento em mídias sociais.",
    uso: "sim", usoNota: "painel Senadores", fonte: "Senado, Transparência → Recursos utilizados por senador", url: "https://www25.senado.leg.br/web/transparencia/sen", lido: LIDO, noCusto: "sim" },
  { item: "Gabinete e escritórios de apoio", valor: "Equipe de comissionados, efetivos, estagiários e terceirizados no gabinete em Brasília e nos escritórios no estado; 41 pessoas por senador em média (2026). Não há um teto em reais publicado como na Câmara.",
    uso: "parcial", usoNota: "quantidade por senador sim (painel); custo não", fonte: "Senado, Recursos utilizados por senador", url: "https://www25.senado.leg.br/web/transparencia/sen", lido: LIDO, noCusto: "nao" },
  { item: "Imóvel funcional ou auxílio-moradia", valor: "Todo senador ocupa imóvel funcional do Senado ou recebe auxílio-moradia de R$ 5.500 por mês. Em 2026: 63 usam imóvel, 11 recebem o auxílio.",
    uso: "sim", usoNota: "painel Senadores", fonte: "Ato da Comissão Diretora 24/1992 e 6/2012; Ato do 3º-Secretário 1/2010; FAQ do Senado", url: "https://www12.senado.leg.br/perguntas-frequentes/canais-de-atendimento/senadores/os-senadores-tem-direito-a-imovel-funcional-e-auxilio-moradia", lido: LIDO, noCusto: "nao" },
  { item: "Saúde", valor: "O Senado custeia parte das despesas médicas, hospitalares, odontológicas, fisioterápicas e psicológicas do senador e dependentes, e de ex-senadores e cônjuges, com limites (livre escolha até 20× a tabela em consultas; ex-senador até R$ 32.958,12/ano; odontologia e psicologia até R$ 25.998,96/ano por família). Plano SIS/Saúde Caixa com contribuição por faixa etária.",
    uso: "nao", fonte: "FAQ da Transparência do Senado \"Como funciona o plano de saúde de Senadores e ex-Senadores?\"", url: "https://www12.senado.leg.br/transparencia/perguntas-frequentes-1/sobre-os-senadores/qual-e-o-ato-que-regula-a-assistencia-medica-para-senadores-e-ex-senadores", lido: LIDO, noCusto: "nao" },
  { item: "Aposentadoria (PSSC)", valor: "Mesmo plano dos deputados: opcional, contributivo, 65/62 anos e pedágio de 30% (EC 103/2019).", uso: "nao", fonte: "Lei 9.506/1997; EC 103/2019; FAQ do Senado", url: "https://www12.senado.leg.br/perguntas-frequentes/canais-de-atendimento/senadores/como-funciona-a-aposentadoria-dos-senadores", lido: LIDO, noCusto: "nao" },
  { item: "Passaporte diplomático", valor: "Durante o mandato.", uso: "nao", fonte: "Decreto 5.978/2006, art. 6º", url: "https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/decreto/d5978.htm", lido: LIDO, noCusto: "nao" },
];

// STF: a fonte é o contracheque detalhado de cada ministro (blocos A a S do Portal da Transparência do STF).
export const STF: Beneficio[] = [
  { item: "Subsídio", valor: "R$ 46.366,19 por mês: é o teto constitucional do serviço público (CF art. 37, XI). Mais 13º e ⅓ de férias, pagos em meses específicos.",
    uso: "sim", usoNota: "contracheque por ministro; painel STF", fonte: "DL 172/2022; STF, Remuneração (bloco A do contracheque)", url: "https://egesp-portal.stf.jus.br/transparencia/rendimento_folha", lido: LIDO, noCusto: "sim" },
  { item: "Vantagens pessoais", valor: "Adicional por tempo de serviço e vantagem pessoal nominalmente identificada (VPNI), de carreiras anteriores. Em ago/2026: de R$ 0 (Zanin) a R$ 16.228,17 (Gilmar Mendes, Cármen Lúcia); 7 dos 8 contracheques lidos têm a parcela.",
    uso: "sim", usoNota: "contracheque por ministro (bloco B)", fonte: "STF, Remuneração", url: "https://egesp-portal.stf.jus.br/transparencia/rendimento_folha", lido: LIDO, noCusto: "sim" },
  { item: "Abono de permanência", valor: "Devolução da contribuição previdenciária (R$ 7.552,67 em ago/2026) a quem já podia se aposentar e segue na ativa: Gilmar Mendes e Cármen Lúcia.",
    uso: "sim", usoNota: "contracheque (bloco G)", fonte: "STF, Remuneração; CF art. 40, §19", url: "https://egesp-portal.stf.jus.br/transparencia/rendimento_folha", lido: LIDO, noCusto: "sim" },
  { item: "Auxílios (alimentação, pré-escolar, saúde) e auxílio-moradia", valor: "R$ 0,00 para todos os ministros em ago/2026. Em 2026 o próprio STF declarou inconstitucionais auxílio-alimentação, moradia, combustível, creche e similares para magistrados, mantendo só ressarcimento de saúde comprovado.",
    uso: "sim", usoNota: "contracheque (blocos P e S)", fonte: "STF, Remuneração; Informativo STF 1210 (abr/2026)", url: "https://www.stf.jus.br/arquivo/informativo/documento/informativo1210.htm", lido: LIDO, noCusto: "sim" },
  { item: "Gabinete", valor: "Equipe lotada no gabinete (assessores, analistas, técnicos, cedidos, juízes auxiliares), 30 a 37 pessoas por ministro em ago/2026, paga pela folha do STF.",
    uso: "sim", usoNota: "folha por lotação; painel STF", fonte: "STF, Remuneração (filtro por lotação)", url: "https://egesp-portal.stf.jus.br/transparencia/rendimento_folha", lido: LIDO, noCusto: "sim" },
  { item: "Aposentadoria", valor: "Integral pela folha do próprio Tribunal; 16 ministros aposentados em ago/2026, R$ 992 mil no mês.", uso: "sim", usoNota: "painel STF (à parte)", fonte: "STF, Remuneração (situação \"Aposentado Ministro\")", url: "https://egesp-portal.stf.jus.br/transparencia/rendimento_folha", lido: LIDO, noCusto: "nao" },
];

export const EX_PRESIDENTES = {
  texto: "Ex-presidente da República não recebe salário nem pensão vitalícia. A Lei 7.474/1986 (regulamentada pelo Decreto 6.381/2008) garante, pelo resto da vida, até 8 servidores para segurança, apoio pessoal, assessoria e motoristas, e 2 veículos oficiais, custeados pela Presidência. A Presidência publica o custo dessas equipes no seu portal de dados abertos (\"Custos das equipes de segurança e apoio aos ex-Presidentes, 2021 a 2026\"); no 1º semestre de 2025 foram R$ 3,65 milhões para seis ex-presidentes. O portal estava fora do ar em 26/10/2026; a linha entra no site quando a carga for possível.",
  fonte: "Lei 7.474/1986; Decreto 6.381/2008; Presidência da República, dados abertos",
  url: "https://dadosabertos.presidencia.gov.br/dataset/custo-de-ex-presidentes-da-republica-lei-7474-1986",
};
