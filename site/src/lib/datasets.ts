/**
 * Catálogo dos dados publicados em /data/*.json — alimenta a página /dados/ e o
 * schema.org/Dataset de cada painel (prop `dataset` do Base.astro).
 * Licença: CC BY 4.0. Fontes primárias listadas por painel.
 */
export type Fonte = { nome: string; url: string };
export type Dataset = {
  slug: string;            // rota do painel, ex. "/deputados/"
  nome: string;
  descricao: string;
  arquivos: string[];      // nomes em site/public/data/
  fontes: Fonte[];
  periodo?: string;        // ISO 8601 interval ou ano
  atualizacao: string;     // texto livre: "diária", "mensal", …
};

export const DATASETS: Dataset[] = [
  {
    slug: "/deputados/", nome: "Custo por deputado federal",
    descricao: "Subsídio, cota parlamentar (gasto real, líquido de glosas) e verba de gabinete (teto) por deputado em exercício; cota por categoria e por fornecedor, com link da nota fiscal.",
    arquivos: ["custo_deputado_2026.json", "ceap_categoria_2026.json", "ceap_fornecedor_2026.json", "fornecedor_rede_2026.json", "meta_2026.json"],
    fontes: [{ nome: "Câmara dos Deputados — Dados Abertos (CEAP)", url: "https://dadosabertos.camara.leg.br/" },
             { nome: "Câmara — Transparência: gastos parlamentares", url: "https://www.camara.leg.br/transparencia/gastos-parlamentares" }],
    periodo: "2026", atualizacao: "diária",
  },
  {
    slug: "/senadores/", nome: "Custo por senador",
    descricao: "Subsídio, CEAPS por categoria e gastos fora da cota (diárias, passagens, correios, mídias) por senador.",
    arquivos: ["custo_senador_2026.json", "custo_senador_2025.json", "meta_senado_2026.json", "meta_senado_2025.json"],
    fontes: [{ nome: "Senado Federal — Dados Abertos Administrativos", url: "https://adm.senado.gov.br/adm-dadosabertos/" }],
    periodo: "2025/2026", atualizacao: "diária",
  },
  {
    slug: "/stf/", nome: "Custo por ministro do STF",
    descricao: "Remuneração bruta dos ministros e folha de cada gabinete, a partir da folha de pagamento publicada pelo STF.",
    arquivos: ["custo_ministro_stf_2026.json", "meta_stf_2026.json"],
    fontes: [{ nome: "STF — Transparência: rendimentos da folha", url: "https://egesp-portal.stf.jus.br/transparencia/rendimento_folha" }],
    periodo: "2026", atualizacao: "mensal (manual)",
  },
  {
    slug: "/presidencia/", nome: "Presidência da República — cartão corporativo",
    descricao: "Gastos com Cartão de Pagamento do Governo Federal (CPGF) do órgão superior Presidência: por mês, órgão, tipo e favorecidos PJ.",
    arquivos: ["presidencia_cpgf_2026.json", "presidencia_cpgf_2025.json"],
    fontes: [{ nome: "Portal da Transparência — CPGF (download de dados)", url: "https://portaldatransparencia.gov.br/download-de-dados/cpgf" }],
    periodo: "2025/2026", atualizacao: "mensal",
  },
  {
    slug: "/judiciario/", nome: "Custo por magistrado dos tribunais federais",
    descricao: "Remuneração de cada ministro (bruta após o teto constitucional, sem indenizações) e folha de todas as pessoas lotadas no gabinete dele, no STJ, no TST e no STM, com indenizações, aposentados e unidades de direção em campos separados.",
    arquivos: ["custo_magistrado_stj_2026.json", "custo_magistrado_tst_2026.json", "custo_magistrado_stm_2026.json",
               "custo_magistrado_trf4_2026.json", "custo_magistrado_trf6_2026.json",
               "meta_stj_2026.json", "meta_tst_2026.json", "meta_stm_2026.json", "meta_trf4_2026.json", "meta_trf6_2026.json"],
    fontes: [{ nome: "STJ — Dados Abertos, Folha de Pagamento de Pessoal", url: "https://dadosabertos.web.stj.jus.br/dataset/folha-de-pagamento-de-pessoal" },
             { nome: "TST — Transparência, Remuneração", url: "https://transparencia-remuneracao.tst.jus.br/" },
             { nome: "STM — Remuneração e proventos", url: "https://www.stm.jus.br/transparencia-e-prestacao-de-contas/gestao-de-pessoas" },
             { nome: "TRF4 — Transparência, contracheque", url: "https://www.trf4.jus.br/trf4/controlador.php?acao=pagina_visualizar&id_pagina=2037" },
             { nome: "TRF6 — Anexo VIII da Resolução CNJ 102/2009", url: "https://portal.trf6.jus.br/institucional/transparencia/relatorios-cnj/anexo-viii/anexo-viii-trf6/" }],
    periodo: "2026", atualizacao: "mensal",
  },
  {
    slug: "/emendas/", nome: "Emendas parlamentares por autor",
    descricao: "Empenhado, liquidado e pago por autor e tipo de emenda (individual, bancada, comissão), com cruzamento para deputados e senadores.",
    arquivos: ["emendas_por_autor_2025.json"],
    fontes: [{ nome: "Portal da Transparência — API de Dados (emendas)", url: "https://portaldatransparencia.gov.br/api-de-dados" }],
    periodo: "2025", atualizacao: "semanal",
  },
  {
    slug: "/poderes/", nome: "Despesa da União por Poder, órgão, função e GND",
    descricao: "Despesa paga por Legislativo, Judiciário, Executivo, funções essenciais e dívida; por unidade orçamentária, função e grupo de natureza; 'manter a máquina' × políticas públicas.",
    arquivos: ["poderes_2025.json", "poderes_orgaos_2025.json", "poderes_funcao_2025.json", "poderes_gnd_2025.json", "poderes_categoria_2025.json"],
    fontes: [{ nome: "SIOP — Painel do Orçamento (SPARQL)", url: "https://www1.siop.planejamento.gov.br/sparql/" }],
    periodo: "2025", atualizacao: "semanal",
  },
  {
    slug: "/estados/", nome: "Despesa dos estados por função",
    descricao: "Legislativa, Judiciária, Essencial à Justiça, Administração, Segurança, Previdência, Saúde, Educação e Encargos, por estado e por habitante (DCA/SICONFI).",
    arquivos: ["estados_2025.json"],
    fontes: [{ nome: "Tesouro Nacional — SICONFI (DCA)", url: "https://siconfi.tesouro.gov.br/" }],
    periodo: "2025", atualizacao: "trimestral",
  },
  {
    slug: "/municipios/", nome: "Câmaras Municipais — custo do Legislativo em 5,5 mil municípios",
    descricao: "Função Legislativa paga por município, por habitante, por vereador e como % do orçamento (DCA/SICONFI, vagas TSE, população IBGE).",
    arquivos: ["municipios_2025.json", "municipios_meta_2025.json"],
    fontes: [{ nome: "Tesouro Nacional — SICONFI (DCA)", url: "https://siconfi.tesouro.gov.br/" },
             { nome: "TSE — vagas por município", url: "https://www.tse.jus.br/" }],
    periodo: "2025", atualizacao: "trimestral",
  },
  {
    slug: "/obras/", nome: "Obras e projetos de investimento com recurso federal",
    descricao: "Cadastro federal de obras (Obrasgov/CIPI): quantidade, valor previsto e empenhado por situação, estado, eixo e tipo, com o recorte das obras paralisadas e inacabadas, tempo sem atualização da situação e prazo vencido.",
    arquivos: ["obras.json"],
    fontes: [{ nome: "Obrasgov/CIPI — API pública do Ministério da Gestão", url: "https://api.obrasgov.gestao.gov.br/obrasgov/api/" }],
    periodo: "2026", atualizacao: "mensal",
  },
  {
    slug: "/impostos/", nome: "Arrecadação federal por estado e tributo",
    descricao: "Receita administrada pela Receita Federal, mensal desde 2000, por UF e por tributo.",
    arquivos: ["impostos.json"],
    fontes: [{ nome: "Receita Federal — arrecadação por estado (dados abertos)", url: "https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/dados-abertos" }],
    periodo: "2000/..", atualizacao: "mensal",
  },
  {
    slug: "/imposto-de-renda/", nome: "Imposto de Renda — renda declarada, alíquota efetiva e ocupação",
    descricao: "Declarantes do IRPF por faixa de renda total em salários mínimos, com renda tributável, de tributação exclusiva e isenta (detalhada em nove componentes), imposto devido, alíquota efetiva e bens declarados; renda média por natureza da ocupação e por ocupação principal.",
    arquivos: ["irpf.json"],
    fontes: [{ nome: "Receita Federal — Grandes Números do IRPF", url: "https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/estudos/imposto-de-renda" },
             { nome: "Banco Central — SGS série 1619 (salário mínimo)", url: "https://www3.bcb.gov.br/sgspub/" }],
    periodo: "2024", atualizacao: "anual (a Receita publica em março/abril)",
  },
  {
    slug: "/inflacao/", nome: "Inflação (IPCA)", descricao: "IPCA mensal e acumulado, por grupo.",
    arquivos: ["inflacao.json"], fontes: [{ nome: "IBGE — SIDRA", url: "https://sidra.ibge.gov.br/" }], atualizacao: "mensal",
  },
  {
    slug: "/trabalho/", nome: "Trabalho — ocupação, empresas e INSS",
    descricao: "PNAD Contínua (ocupação, desemprego, rendimento), Mapa de Empresas e benefícios do INSS (BEPS).",
    arquivos: ["trabalho.json"],
    fontes: [{ nome: "IBGE — SIDRA (PNAD Contínua)", url: "https://sidra.ibge.gov.br/" },
             { nome: "Mapa de Empresas (MEMP)", url: "https://www.gov.br/empresas-e-negocios/pt-br/mapa-de-empresas" },
             { nome: "INSS — Boletim Estatístico da Previdência Social", url: "https://www.gov.br/previdencia/pt-br/assuntos/previdencia-social/arquivos/beps" }],
    atualizacao: "mensal",
  },
  {
    slug: "/inss/", nome: "Previdência — receitas, despesas e benefícios", descricao: "Arrecadação, benefícios emitidos e resultado do RGPS.",
    arquivos: ["previdencia.json"],
    fontes: [{ nome: "INSS — BEPS", url: "https://www.gov.br/previdencia/pt-br/assuntos/previdencia-social/arquivos/beps" }], atualizacao: "mensal",
  },
  {
    slug: "/renda/", nome: "Renda — distribuição e desigualdade",
    descricao: "Rendimento por posição na ocupação, massa por percentil, limites P90/P99 e Gini (PNAD Contínua).",
    arquivos: ["renda.json"], fontes: [{ nome: "IBGE — SIDRA (PNAD Contínua)", url: "https://sidra.ibge.gov.br/" },
             { nome: "IBGE — Censo Demográfico 2022 (tabelas 10292 e 10296)", url: "https://sidra.ibge.gov.br/tabela/10296" }], atualizacao: "mensal",
  },
  {
    slug: "/educacao/", nome: "Educação — IDEB", descricao: "IDEB por Brasil, UF e município (rede pública), última edição 2023.",
    arquivos: ["educacao.json"], fontes: [{ nome: "INEP — IDEB", url: "https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/ideb" },
             { nome: "IBGE — PNAD Contínua anual, tabelas 7189 e 7113 (escolaridade e analfabetismo)", url: "https://sidra.ibge.gov.br/tabela/7189" }],
    periodo: "2005/2023", atualizacao: "bienal",
  },
  {
    slug: "/seguranca/", nome: "Segurança — Sinesp VDE",
    descricao: "Vítimas e ocorrências por UF e município (≥100 mil hab. e capitais), série desde 2015, taxas por 100 mil habitantes.",
    arquivos: ["seguranca.json"], fontes: [{ nome: "MJSP — Sinesp VDE", url: "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica" }],
    periodo: "2015/..", atualizacao: "mensal",
  },
  {
    slug: "/saude/", nome: "Saúde — cobertura de planos e indicadores",
    descricao: "Vínculos de planos de saúde por UF e capital (ANS), esperança de vida e mortalidade (IBGE), despesa em saúde dos três níveis.",
    arquivos: ["saude.json"],
    fontes: [{ nome: "ANS — Dados Abertos (PDA 047)", url: "https://dadosabertos.ans.gov.br/" }, { nome: "IBGE — SIDRA", url: "https://sidra.ibge.gov.br/" }],
    atualizacao: "mensal",
  },
  {
    slug: "/inadimplencia/", nome: "Crédito e inadimplência (SCR)",
    descricao: "Carteira ativa e inadimplência (>90 dias) por UF, tipo de cliente, modalidade e porte; série de 24 meses.",
    arquivos: ["credito.json"], fontes: [{ nome: "Banco Central — SCR.data", url: "https://www.bcb.gov.br/estabilidadefinanceira/scr" }], atualizacao: "mensal",
  },
  {
    slug: "/corrupcao/", nome: "Corrupção — sanções e indicadores", descricao: "Ver página para fontes e recortes.",
    arquivos: ["corrupcao.json"], fontes: [{ nome: "Portal da Transparência — sanções (CEIS/CNEP)", url: "https://portaldatransparencia.gov.br/sancoes" }], atualizacao: "mensal",
  },
  {
    slug: "/comparacao/", nome: "Comparação internacional de gasto público",
    descricao: "Gasto público em educação, saúde, defesa, total do governo central e transferências de benefícios como percentual do PIB, no Brasil e em 20 países de referência, mais a diferença entre a carga tributária medida pelo Banco Mundial (governo central) e pela Receita Federal (três níveis).",
    arquivos: ["rankings.json", "impostos.json", "poderes_funcao_2025.json"],
    fontes: [{ nome: "Banco Mundial — dados abertos", url: "https://data.worldbank.org/" },
             { nome: "Receita Federal — Carga Tributária no Brasil", url: "https://www.gov.br/receitafederal/pt-br/centrais-de-conteudo/publicacoes/estudos/carga-tributaria" }],
    periodo: "2022/2025", atualizacao: "mensal",
  },
  {
    slug: "/rankings/", nome: "Brasil em rankings internacionais",
    descricao: "PIB, PIB per capita, expectativa de vida, Gini, educação, homicídios (Banco Mundial/UNODC), IDH (PNUD) e Índice de Percepção da Corrupção (TI).",
    arquivos: ["rankings.json"],
    fontes: [{ nome: "Banco Mundial — API", url: "https://data.worldbank.org/" }, { nome: "PNUD — Human Development Reports", url: "https://hdr.undp.org/" },
             { nome: "Transparency International — CPI", url: "https://www.transparency.org/en/cpi" }],
    atualizacao: "mensal",
  },
  {
    slug: "/historico/", nome: "Séries longas desde 2000",
    descricao: "Despesa da União por função (SIOP), arrecadação, benefícios do INSS e IPCA para deflacionar.",
    arquivos: ["historico.json"],
    fontes: [{ nome: "SIOP — SPARQL", url: "https://www1.siop.planejamento.gov.br/sparql/" }, { nome: "IBGE — IPCA (SIDRA)", url: "https://sidra.ibge.gov.br/" }],
    periodo: "2000/..", atualizacao: "mensal",
  },
  {
    slug: "/estatais/", nome: "Lucro das estatais e dividendos da União",
    descricao: "Lucro ou prejuízo das estatais federais de controle direto (microdado da SEST, desde 2016), lucro empresa por empresa nas três esferas com quem controlava cada uma em cada ano (CVM, desde 2010) e dividendos recebidos pela União (Tesouro, desde 1997).",
    arquivos: ["estatais.json"],
    fontes: [{ nome: "Ministério da Gestão — SEST: estatais federais, dados financeiros", url: "https://dados.gov.br/dados/conjuntos-dados/empresas-estatais-federais---dados-financeiros" },
             { nome: "CVM — Dados abertos: DFP e formulário de referência", url: "https://dados.cvm.gov.br/dataset/cia_aberta-doc-dfp" },
             { nome: "Tesouro Nacional — Resultado do Tesouro Nacional, série histórica", url: "https://www.tesourotransparente.gov.br/ckan/dataset/resultado-do-tesouro-nacional" }],
    periodo: "1997/2025", atualizacao: "mensal",
  },
  {
    slug: "/saneamento/", nome: "Saneamento: água, esgoto e lixo",
    descricao: "Percentual de domicílios com água da rede geral, esgoto ligado à rede e lixo coletado, nos Censos de 1991, 2000, 2010 e 2022 e na PNAD Contínua anual, no Brasil e por estado, com a categoria exata somada em cada pesquisa.",
    arquivos: ["saneamento.json"],
    fontes: [{ nome: "IBGE — Censo Demográfico (SIDRA)", url: "https://sidra.ibge.gov.br/" },
             { nome: "IBGE — PNAD Contínua anual (SIDRA)", url: "https://sidra.ibge.gov.br/pesquisa/pnadca/tabelas" }],
    periodo: "1991/2025", atualizacao: "anual",
  },
  {
    slug: "/divida/", nome: "Dívida pública federal: custo e estoque",
    descricao: "Juros nominais do Governo Central desde 1997, estoque da Dívida Pública Federal mês a mês, composição por indexador e perfil de vencimento.",
    arquivos: ["divida.json"],
    fontes: [{ nome: "Tesouro Nacional — Resultado do Tesouro Nacional, série histórica (tabela 2.1)", url: "https://www.tesourotransparente.gov.br/ckan/dataset/resultado-do-tesouro-nacional" },
             { nome: "Tesouro Transparente — Estoque da Dívida Pública Federal", url: "https://www.tesourotransparente.gov.br/ckan/dataset/estoque-da-divida-publica-federal" }],
    periodo: "1997/2026", atualizacao: "mensal",
  },
  {
    slug: "/transito/", nome: "Mortes no trânsito",
    descricao: "Mortes por acidente de trânsito no Brasil desde 2000, por ano, estado, sexo e faixa de idade, a partir do atestado de óbito (SIM/Ministério da Saúde), com a comparação com o registro policial e com outros países.",
    arquivos: ["transito.json"],
    fontes: [{ nome: "IBGE — indicador ODS 3.6.1 (tabela 4408 do SIDRA), a partir do SIM/Ministério da Saúde", url: "https://sidra.ibge.gov.br/tabela/4408" },
             { nome: "MJSP — Sinesp VDE (registro policial)", url: "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica" },
             { nome: "Banco Mundial / OMS — mortes no trânsito por 100 mil", url: "https://data.worldbank.org/indicator/SH.STA.TRAF.P5" }],
    periodo: "2000/2024", atualizacao: "anual",
  },
  {
    slug: "/desenvolvimento/", nome: "Desenvolvimento: a trajetória do Brasil",
    descricao: "Doze indicadores de desenvolvimento com a série do Brasil desde os anos 1980 e a posição do país no mundo ano a ano: mortalidade infantil, expectativa de vida, escolaridade, internet, energia, desigualdade, renda por pessoa, produtividade, investimento, abertura comercial, IDH e percepção da corrupção.",
    arquivos: ["rankings.json", "desenvolvimento.json"],
    fontes: [{ nome: "IBGE — Censo Demográfico por UF (tabelas 142, 1974, 3547 e 10141) e indicador ODS 16.1.1 (tabela 6606)", url: "https://sidra.ibge.gov.br/" },
             { nome: "Banco Mundial — indicadores de desenvolvimento", url: "https://data.worldbank.org/" },
             { nome: "PNUD — Relatório de Desenvolvimento Humano", url: "https://hdr.undp.org/" },
             { nome: "Transparência Internacional — Índice de Percepção da Corrupção", url: "https://www.transparency.org/en/cpi" }],
    periodo: "1985/2025", atualizacao: "mensal",
  },
  {
    slug: "/economia/", nome: "Economia: PIB, Selic e contas públicas",
    descricao: "PIB anual e trimestral desde 1996, meta da Selic desde 1999 e resultado primário e nominal do Governo Central desde 1997.",
    arquivos: ["economia.json"],
    fontes: [{ nome: "IBGE — Contas Nacionais Anuais (SIDRA 6784) e Trimestrais (SIDRA 5932)", url: "https://sidra.ibge.gov.br/tabela/5932" },
             { nome: "Banco Central — SGS, série 432 (meta Selic)", url: "https://www3.bcb.gov.br/sgspub/" },
             { nome: "Tesouro Nacional — Resultado do Tesouro Nacional, série histórica", url: "https://www.tesourotransparente.gov.br/ckan/dataset/resultado-do-tesouro-nacional" }],
    periodo: "1996/2026", atualizacao: "mensal",
  },
  {
    slug: "/economia/poder-de-compra/", nome: "Poder de compra: preço em tempo de trabalho",
    descricao: "Preço médio de revenda de combustíveis por mês desde julho de 2001 e por estado, convertido em minutos de trabalho no salário mínimo e no rendimento médio; índice de nível de preços por categoria de consumo em 21 países.",
    arquivos: ["precos.json"],
    fontes: [{ nome: "ANP — Sistema de Levantamento de Preços (série histórica)", url: "https://www.gov.br/anp/pt-br/assuntos/precos-e-defesa-da-concorrencia/precos/precos-revenda-e-de-distribuicao-combustiveis/serie-historica-do-levantamento-de-precos" },
             { nome: "Banco Central — SGS, série 1619 (salário mínimo)", url: "https://www3.bcb.gov.br/sgspub/" },
             { nome: "IBGE — PNAD Contínua trimestral (SIDRA 5436 e 6371)", url: "https://sidra.ibge.gov.br/tabela/5436" },
             { nome: "Banco Mundial — International Comparison Program (ICP) 2021", url: "https://www.worldbank.org/en/programs/icp" }],
    periodo: "2001/2026", atualizacao: "mensal",
  },
  {
    slug: "/desenvolvimento/", nome: "Indústria: participação, produção física e pauta de exportação",
    descricao: "Participação da indústria de transformação no valor adicionado (Brasil e grupos de países), manufaturados nas exportações desde 1962, emprego industrial, conteúdo tecnológico e índice de produção física do IBGE.",
    arquivos: ["industria.json", "desenvolvimento.json"],
    fontes: [{ nome: "Banco Mundial — World Development Indicators", url: "https://data.worldbank.org/" },
             { nome: "IBGE — Pesquisa Industrial Mensal, Produção Física (SIDRA 8888)", url: "https://sidra.ibge.gov.br/tabela/8888" }],
    periodo: "1962/2026", atualizacao: "mensal",
  },
];

export const porSlug = (slug: string) => DATASETS.find((d) => d.slug === slug);
