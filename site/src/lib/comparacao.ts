/**
 * Números internacionais que não existem em API aberta e por isso ficam aqui, cada linha com fonte, página e data de
 * verificação — mesma regra de `beneficios.ts`. Nada daqui é estimativa nossa; o que é cálculo nosso está marcado.
 * Verificado em 28/10/2026.
 */

export type LinhaJud = {
  pais: string;
  tribunais: number | null;      // orçamento dos TRIBUNAIS, % do PIB (CEPEJ 2022) — é o que compara com o CNJ
  sistema: number | null;        // tribunais + Ministério Público + assistência judiciária, % do PIB (CEPEJ 2022)
  eurostat: number | null;       // COFOG GF0303 (tribunais), % do PIB (Eurostat 2024)
  nota?: string;
};

/** CNJ, Justiça em Números 2026 (ano-base 2025). */
export const JUDICIARIO_BR = {
  edicao: 2026,
  ano: 2025,
  despesa: 164_649_661_456,
  pct_pib: 1.3,                  // publicado pelo CNJ (p. 64 e 607)
  pct_pib_calculado: 1.293,      // conferência nossa: despesa ÷ PIB de 2025 (IBGE, SIDRA 1846, 4 trimestres)
  pct_pib_sem_inativos: 1.1,     // o CNJ publica também sem aposentados e pensionistas (15,3% da despesa)
  por_habitante: 771.48,
  por_habitante_eur: 122.29,     // cálculo nosso, PTAX média de 2025 = R$ 6,3085/EUR
  magistrados: 19_094,
  cargos: 23_114,
  magistrados_100k: 8.95,
  arrecadacao: 68_200_000_000,   // o Judiciário arrecada custas e taxas: 41% da própria despesa
  fonte: "CNJ, Justiça em Números 2026 (ano-base 2025), p. 51, 64–66 e 607",
  url: "https://www.cnj.jus.br/pesquisas-judiciarias/justica-em-numeros/",
  pdf: "https://www.cnj.jus.br/wp-content/uploads/2026/06/relatorio-justica-em-numeros2026-1.pdf",
};

/** CEPEJ (Conselho da Europa), ciclo 2024 com dados de 2022 — o ciclo com dados de 2025 ainda não saiu. */
export const JUDICIARIO_EUROPA: LinhaJud[] = [
  { pais: "Polônia", tribunais: 0.456, sistema: null, eurostat: 0.532 },
  { pais: "Bulgária", tribunais: 0.335, sistema: 0.550, eurostat: 0.726 },
  { pais: "Espanha", tribunais: 0.290, sistema: 0.342, eurostat: 0.339 },
  { pais: "Itália", tribunais: 0.207, sistema: 0.311, eurostat: 0.351 },
  { pais: "Reino Unido — Irlanda do Norte", tribunais: 0.187, sistema: 0.461, eurostat: null, nota: "o Reino Unido informa as três jurisdições separadamente" },
  { pais: "França", tribunais: 0.141, sistema: 0.200, eurostat: 0.283 },
  { pais: "Suécia", tribunais: 0.131, sistema: 0.236, eurostat: 0.259 },
  { pais: "Países Baixos", tribunais: 0.130, sistema: 0.258, eurostat: 0.291 },
  { pais: "Reino Unido — Inglaterra e Gales", tribunais: 0.126, sistema: null, eurostat: null },
  { pais: "Reino Unido — Escócia", tribunais: 0.096, sistema: 0.272, eurostat: null },
  { pais: "Dinamarca", tribunais: 0.075, sistema: 0.151, eurostat: 0.165 },
  { pais: "Noruega", tribunais: 0.050, sistema: 0.088, eurostat: 0.132 },
  { pais: "Alemanha", tribunais: null, sistema: 0.296, eurostat: 0.369 },
  { pais: "Portugal", tribunais: null, sistema: null, eurostat: 0.286 },
];

export const JUDICIARIO_EUROPA_META = {
  ano_cepej: 2022,
  ano_eurostat: 2024,
  mediana_tribunais: 0.186,       // mediana dos 39 países que responderam à CEPEJ
  paises_cepej: 39,
  ue27_eurostat: 0.327,
  ue27_por_habitante_eur: 131.87,
  mediana_magistrados_100k: 17.43,
  fonte: "CEPEJ (Conselho da Europa), ciclo 2024 com dados de 2022, e Eurostat (COFOG GF0303, 2024)",
  url_cepej: "https://www.coe.int/en/web/cepej/cepej-stat",
  url_eurostat: "https://ec.europa.eu/eurostat/databrowser/view/gov_10a_exp/",
};

export type Monarquia = {
  pais: string;
  iso3: string;
  moeda: string;
  valor: number;
  ano: string;
  status: string;
  inclui: string;
  fora: string;
  ajustado?: { valor: number; moeda: string; nota: string };   // valor comparável depois de somar ou tirar o que falta
  fonte: string;
  url: string;
};

/** Custo anual da monarquia no orçamento público, cada um na moeda e no conceito do próprio país. */
export const MONARQUIAS: Monarquia[] = [
  {
    pais: "Reino Unido", iso3: "GBR", moeda: "GBP", valor: 132_100_000, ano: "exercício encerrado em 31/03/2026",
    status: "realizado e auditado",
    inclui: "pessoal (563 pessoas), viagens oficiais e £ 67,5 mi de reforma de palácios",
    fora: "segurança física, que o próprio relatório diz estar excluída",
    fonte: "Sovereign Grant and Sovereign Grant Reserve — Annual Report and Accounts 2025-26, p. 10 e 112",
    url: "https://assets.publishing.service.gov.uk/media/6a3d589fda47783d87723b5a/The_Sovereign_Grant_and_Sovereign_Grant_Reserve_-_Annual_Report_and_Accounts.pdf",
  },
  {
    pais: "Japão", iso3: "JPN", moeda: "JPY", valor: 25_602_451_000, ano: "ano fiscal 2026",
    status: "orçamento como submetido",
    inclui: "despesas da família imperial e o custo inteiro da Agência da Casa Imperial",
    fora: "a polícia imperial, com 942 agentes e ¥8,9 bi, que fica na Polícia Nacional",
    fonte: "Agência da Casa Imperial, evolução do orçamento (令和8年度)",
    url: "https://www.kunaicho.go.jp/wp-content/uploads/2026/04/yosansuii-r08.pdf",
  },
  {
    pais: "Noruega", iso3: "NOR", moeda: "NOK", valor: 307_710_000, ano: "2026", status: "aprovado pelo Parlamento",
    inclui: "a casa real e a manutenção corrente dos palácios",
    fora: "obras nos imóveis estatais e a escolta policial, que o governo declara não divulgar",
    fonte: "Statsbudsjettet 2026 (blåboka), p. 9",
    url: "https://www.stortinget.no/globalassets/pdf/budsjettsiden/blaabok_2026.pdf",
  },
  {
    pais: "Suécia", iso3: "SWE", moeda: "SEK", valor: 190_457_000, ano: "2026", status: "aprovado em 03/12/2025",
    inclui: "a casa real (51%) e a administração dos palácios do Estado (49%)",
    fora: "a segurança, que fica na polícia de segurança",
    fonte: "Prop. 2025/26:1, área de despesa 1, seção 3.1.1",
    url: "https://www.riksdagen.se/sv/dokument-och-lagar/dokument/proposition/budgetpropositionen-for-2026-utgiftsomrade-1_hd031d3/html/",
  },
  {
    pais: "Dinamarca", iso3: "DNK", moeda: "DKK", valor: 154_000_000, ano: "2026", status: "orçado",
    inclui: "apenas os pagamentos em dinheiro ao rei e aos membros da casa real, reajustados duas vezes por ano",
    fora: "pessoal, operação, palácios, segurança e o iate real — nada disso está nesta rubrica",
    fonte: "Finansministeriet, §1 Kongen e §2 Medlemmer af det kongelige hus",
    url: "https://fm.dk/media/zv3jra2c/1-kongen.pdf",
  },
  {
    pais: "Países Baixos", iso3: "NLD", moeda: "EUR", valor: 60_800_000, ano: "2026", status: "orçado",
    inclui: "pagamentos aos membros da casa real, despesas funcionais e serviços repassados",
    fora: "os palácios (€ 21,4 mi em outro capítulo) e a segurança, que o orçamento diz não detalhar por risco",
    ajustado: { valor: 82_200_000, moeda: "EUR", nota: "somando os palácios do capítulo XXII" },
    fonte: "Rijksbegroting 2026, capítulo I (de Koning)",
    url: "https://www.rijksfinancien.nl/memorie-van-toelichting/2026/OWB/I",
  },
  {
    pais: "Bélgica", iso3: "BEL", moeda: "EUR", valor: 44_592_000, ano: "2026", status: "após o 1º ajuste de 30/04/2026",
    inclui: "a lista civil do rei (€ 15,6 mi), a polícia federal de proteção (~€ 18,4 mi) e a casa militar (€ 2,7 mi)",
    fora: "investimento em imóveis",
    ajustado: { valor: 23_600_000, moeda: "EUR", nota: "tirando a polícia e os militares, para comparar com os outros" },
    fonte: "Câmara dos Representantes, DOC 56 1281/001 p. 3 e 1470/001 p. 662",
    url: "https://www.dekamer.be/FLWB/PDF/56/1281/56K1281001.pdf",
  },
  {
    pais: "Espanha", iso3: "ESP", moeda: "EUR", valor: 8_431_150, ano: "2026", status: "orçamento prorrogado",
    inclui: "uma única transferência ao rei, que ele distribui (art. 65 da Constituição espanhola)",
    fora: "palácios (Patrimônio Nacional), Guarda Real e segurança — ficam fora por construção da rubrica",
    fonte: "Presupuestos Generales del Estado, Sección 01, conceito 480",
    url: "https://www.sepg.pap.hacienda.gob.es/Presup/PGE2025Prorroga/MaestroDocumentos/PGE-ROM/doc/1/2/1/1/1/N_25P_E_R_31_101_1_1_1_1911M_2.PDF",
  },
];
