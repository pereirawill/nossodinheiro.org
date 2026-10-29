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

export type Parlamento = {
  pais: string;
  casas: string;
  moeda: string;
  valor: number;                 // só as duas casas, sem órgãos auxiliares
  base: string;                  // realizado | aprovado | prorrogado — muda a leitura
  ano: string;
  cadeiras: number;
  cadeiras_nota?: string;
  pensoes: string;               // quanto de aposentadoria está dentro da rubrica: é o eixo que mais distorce
  fora: string;
  fonte: string;
  url: string;
};

/**
 * Custo anual do parlamento nacional, só as duas casas e sem órgãos auxiliares (tribunal de contas, ombudsman,
 * biblioteca), para o perímetro ser o mesmo. O que cada país ainda carrega dentro está na coluna "pensões" e em "fora".
 * O Brasil entra pelo nosso próprio dado (SIOP, órgãos 01000 e 02000), não por esta lista.
 */
export const PARLAMENTOS: Parlamento[] = [
  {
    pais: "Estados Unidos", casas: "House of Representatives + Senate", moeda: "USD", valor: 3_550_194_000,
    base: "aprovado (enacted)", ano: "ano fiscal 2026", cadeiras: 535,
    cadeiras_nota: "435 deputados com voto e 100 senadores; há mais 6 delegados sem voto",
    pensoes: "zero — a aposentadoria dos congressistas corre em outra lei, e o próprio salário também",
    fora: "a polícia do Capitólio (US$ 852 mi), os prédios (Architect of the Capitol, US$ 812 mi), o tribunal de contas (GAO) e a Biblioteca do Congresso",
    fonte: "Legislative Branch Appropriations Act, 2026 (P.L. 119-37, Division C), Título I",
    url: "https://www.congress.gov/119/plaws/publ37/PLAW-119publ37.pdf",
  },
  {
    pais: "Itália", casas: "Camera dei Deputati + Senato", moeda: "EUR", valor: 1_449_222_000,
    base: "dotação aprovada", ano: "2026", cadeiras: 605,
    cadeiras_nota: "400 deputados e 200 senadores eleitos, mais 5 senadores vitalícios",
    pensoes: "47% da despesa da Camera são inativos: ex-deputados e servidores aposentados",
    fora: "a Corte dei conti, que está em outro programa do orçamento",
    fonte: "Bilancio dello Stato 2026, missione 17, capítulos 2103 e 2104",
    url: "https://www.rgs.mef.gov.it/_Documenti/VERSIONE-I/attivita_istituzionali/formazione_e_gestione_del_bilancio/bilancio_di_previsione/bilancio_finanziario/2026-2028/LB/LB-04-DRC-020-MEF.pdf",
  },
  {
    pais: "Alemanha", casas: "Bundestag", moeda: "EUR", valor: 1_275_973_000,
    base: "aprovado em lei", ano: "2026", cadeiras: 630,
    cadeiras_nota: "só o Bundestag; o Bundesrat (69 votos) é formado por ministros dos governos estaduais e não tem par com o Senado brasileiro",
    pensoes: "cerca de 6% — € 61 mi de aposentadoria de ex-deputados",
    fora: "as obras grandes (€ 113 mi em outro capítulo), o financiamento de partidos (€ 242 mi) e o tribunal de contas",
    fonte: "Haushaltsgesetz 2026, Gesamtplan, Einzelplan 02",
    url: "https://www.gesetze-im-internet.de/hg_2026/BJNR1570A0025.html",
  },
  {
    pais: "França", casas: "Assemblée nationale + Sénat", moeda: "EUR", valor: 988_011_451,
    base: "gasto próprio realizado", ano: "2025", cadeiras: 925,
    pensoes: "só a parte patronal; as caixas de aposentadoria têm contabilidade separada",
    fora: "a Cour des comptes e os canais de TV das casas; as duas gastam mais que a dotação e cobrem a diferença com reservas",
    fonte: "Annexe Pouvoirs publics ao projeto de lei de finanças 2027, p. 7 e 21",
    url: "https://www.assemblee-nationale.fr/dyn/contenu/visualisation/1128255/file/PAP%202027%20-%20Pouvoirs%20publics.pdf",
  },
  {
    pais: "Reino Unido", casas: "House of Commons + House of Lords", moeda: "GBP", valor: 786_860_000,
    base: "realizado e auditado", ano: "exercício 2024-25", cadeiras: 1_447,
    cadeiras_nota: "650 deputados e 797 lordes, que recebem ajuda de custo por dia de presença e não salário",
    pensoes: "quase nada: o fundo dos deputados tem contas próprias",
    fora: "o salário e as despesas dos deputados, que ficam numa autoridade separada (£ 320 mi), e a restauração do palácio",
    fonte: "Annual Report and Accounts 2024-25 das três estimativas (Commons Administration, Commons Members e Lords)",
    url: "https://www.parliament.uk/globalassets/documents/commons-expenditure/admin-annual-accounts/administration_annual_report_and_accounts_2024-25.pdf",
  },
  {
    pais: "Suécia", casas: "Riksdagen", moeda: "SEK", valor: 2_728_172_000,
    base: "aprovado", ano: "2026", cadeiras: 349,
    pensoes: "dentro da verba dos parlamentares, sem linha separada",
    fora: "nesta linha excluímos o tribunal de contas e o ombudsman, que no orçamento sueco ficam dentro do mesmo bloco do parlamento",
    fonte: "Prop. 2025/26:1, área de despesa 1, verbas 2:1, 2:2 e 2:3",
    url: "https://data.riksdagen.se/fil/8C213240-E714-48F9-9CDB-2A9208A1A332",
  },
  {
    pais: "Japão", casas: "Câmara dos Representantes + Câmara dos Conselheiros", moeda: "JPY", valor: 115_408_556_000,
    base: "aprovado", ano: "ano fiscal 2026", cadeiras: 713,
    pensoes: "não identificada em rubrica própria",
    fora: "a Biblioteca Nacional da Dieta (¥ 20,8 bi), que no orçamento japonês fica dentro do bloco do parlamento, e o tribunal de contas",
    fonte: "Orçamento geral do ano fiscal 2026, bloco do Parlamento (国会所管), p. 42",
    url: "https://www.bb.mof.go.jp/server/2026/dlpdf/DL202611001.pdf",
  },
  {
    pais: "Países Baixos", casas: "Tweede Kamer + Eerste Kamer", moeda: "EUR", valor: 288_241_000,
    base: "aprovado em lei", ano: "2026", cadeiras: 225,
    pensoes: "8% — € 23 mi de aposentadoria e auxílio de ex-deputados",
    fora: "a reforma do prédio do parlamento e o tribunal de contas, que está em lei orçamentária separada",
    fonte: "Begroting IIA Staten-Generaal 2026 (Stb. 2026, 135)",
    url: "https://zoek.officielebekendmakingen.nl/stb-2026-135.html",
  },
  {
    pais: "Portugal", casas: "Assembleia da República", moeda: "EUR", valor: 184_989_509,
    base: "aprovado", ano: "2026", cadeiras: 230,
    pensoes: "só contribuições patronais",
    fora: "nove entidades independentes que funcionam junto à Assembleia (Provedor de Justiça, ERC, CNPD e outras) e o Tribunal de Contas; a verba do ano também traz € 19,3 mi de campanha eleitoral, que não é recorrente",
    fonte: "Orçamento do Estado para 2026, Mapa 4 e desenvolvimentos orçamentais",
    url: "https://www.eo.gov.pt/politicaorcamental/OrcamentodeEstado/2026/OrcamentoEstadoAprovado/MapasContabilisticos/OE2026_doc05_Mapa04.pdf",
  },
  {
    pais: "Espanha", casas: "Congreso de los Diputados + Senado", moeda: "EUR", valor: 174_557_750,
    base: "orçamento prorrogado de 2023", ano: "em vigor em 2026", cadeiras: 616,
    pensoes: "só contribuições patronais",
    fora: "o Tribunal de Cuentas e o Defensor del Pueblo; o apoio parlamentar vem como subvenção a grupos, não como gabinete, o que torna o valor por cadeira muito menor que o alemão",
    fonte: "Presupuestos Generales del Estado, Sección 02, programa 911N",
    url: "https://www.sepg.pap.hacienda.gob.es/Presup/PGE2025Prorroga/MaestroDocumentos/PGE-ROM/doc/1/2/2/1/1/N_25P_E_R_31_102_1_1_1_1911N_2.PDF",
  },
];

/** Congresso Nacional pelo nosso próprio dado (SIOP, 2025). Os inativos entram separados porque é o eixo que mais distorce. */
export const CONGRESSO_BR = {
  ano: 2025,
  camara: 7_027_000_000,
  senado: 5_856_000_000,
  total: 12_883_000_000,
  inativos: 4_914_000_000,       // 38,1% do total: Câmara 32,3% e Senado 45,2%
  sem_inativos: 7_969_000_000,
  cadeiras: 594,                 // 513 deputados + 81 senadores
  fonte: "SIOP, execução orçamentária da União de 2025, órgãos 01000 e 02000 (o TCU é órgão próprio e fica fora)",
};

/**
 * Mortes em conflitos armados, para comparar a ordem de grandeza com a violência no Brasil (pedido de 29/10/2026).
 *
 * Esta é a comparação mais fácil de usar para enganar, e por isso cada linha carrega o que o número NÃO inclui.
 * Regras que seguimos aqui:
 * - só número divulgado por **órgão da ONU**, com a data em que lemos;
 * - a taxa é calculada por nós (mortes ÷ população ÷ anos do período), e a população vem do Banco Mundial;
 * - guerra e homicídio não são a mesma coisa: um conflito mata também por fome e doença, e essas mortes não
 *   entram em nenhuma destas contagens.
 */
export type Conflito = {
  lugar: string;
  mortes: number;
  periodo: string;
  anos: number;            // duração do período, para a taxa anual
  populacao: number;       // habitantes, Banco Mundial
  oQueConta: string;
  oQueNaoConta: string;
  fonte: string;
  url: string;
  lido: string;
};

export const CONFLITOS: Conflito[] = [
  {
    lugar: "Faixa de Gaza",
    mortes: 72045,
    periodo: "7 de outubro de 2023 a fevereiro de 2026",
    anos: 2.35,
    populacao: 2_200_000,
    oQueConta: "mortes registradas pelo Ministério da Saúde de Gaza, civis e combatentes juntos",
    oQueNaoConta: "quem morreu sob escombros sem registro, e as mortes indiretas por fome e falta de tratamento",
    fonte: "ONU/OCHA — Humanitarian Situation Update, citando o Ministério da Saúde de Gaza",
    url: "https://www.unocha.org/occupied-palestinian-territory",
    lido: "29/10/2026",
  },
  {
    lugar: "Ucrânia",
    mortes: 16874,
    periodo: "24 de fevereiro de 2022 a setembro de 2026",
    anos: 4.6,
    populacao: 39_000_000,
    oQueConta: "apenas civis cuja morte a ONU conseguiu verificar, um a um",
    oQueNaoConta: "militares dos dois lados (não há número oficial) e os civis que a própria ONU diz que faltam, " +
      "porque a verificação não alcança território ocupado nem áreas de combate",
    fonte: "ONU/OHCHR — Missão de Monitoramento de Direitos Humanos na Ucrânia",
    url: "https://ukraine.ohchr.org/en/reports/protection-of-civilians",
    lido: "29/10/2026",
  },
];

/** Conflitos em que a ONU não publica um total verificado — a ausência também é informação. */
export const SEM_TOTAL_OFICIAL = [
  "Sudão: a guerra civil desde abril de 2023 não tem contagem verificada pela ONU; os números que circulam vêm de " +
    "projetos acadêmicos e de organizações humanitárias, com estimativas que variam em dezenas de milhares.",
  "República Democrática do Congo, Mianmar, Haiti e Sahel: idem. Onde o Estado não registra a morte, ninguém conta " +
    "direito — e isso vale para o Brasil também, nas 13,5 mil mortes a esclarecer que o Sinesp registrou em 2025.",
];
