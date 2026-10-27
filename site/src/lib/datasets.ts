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
    arquivos: ["educacao.json"], fontes: [{ nome: "INEP — IDEB", url: "https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/ideb" }],
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
];

export const porSlug = (slug: string) => DATASETS.find((d) => d.slug === slug);
