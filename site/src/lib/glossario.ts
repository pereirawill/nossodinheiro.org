/**
 * Glossário dos termos usados nos painéis. Cada entrada: rótulo curto + explicação em uma ou duas frases.
 * Usado pelo componente <Termo t="…"> (dica ⓘ) e pelo <Glossario> (lista no fim da página).
 * Definições seguem o Manual Técnico de Orçamento (MTO/SOF) e a Lei 4.320/1964; fontes na metodologia.
 */
export const GLOSSARIO: Record<string, { rotulo: string; texto: string }> = {
  // Etapas da despesa (Lei 4.320/1964, arts. 58–65)
  empenhado: { rotulo: "Empenhado", texto: "Primeira etapa da despesa: o órgão reservou o valor no orçamento e assumiu o compromisso de pagar. O dinheiro ainda não saiu do caixa." },
  liquidado: { rotulo: "Liquidado", texto: "Segunda etapa: o órgão conferiu que o bem foi entregue ou o serviço prestado e autorizou o pagamento." },
  pago: { rotulo: "Pago", texto: "Última etapa: o dinheiro saiu de fato do caixa do Tesouro para o favorecido. É o valor que usamos como 'gasto'." },
  restos_a_pagar: { rotulo: "Restos a pagar", texto: "Valores empenhados em anos anteriores e pagos neste ano. Entram em coluna separada para não misturar exercícios." },
  dotacao: { rotulo: "Dotação", texto: "Quanto a Lei Orçamentária autorizou gastar no ano (lei + créditos adicionais). É o teto, não o gasto." },

  // Emendas
  emenda_individual: { rotulo: "Emenda individual", texto: "Parcela do orçamento que cada deputado e senador tem direito a indicar para onde quiser (obras, hospitais, prefeituras). Tem autor único e execução obrigatória (RP 6)." },
  emenda_bancada: { rotulo: "Emenda de bancada", texto: "Emenda coletiva dos parlamentares de um mesmo estado, para projetos de interesse do estado. Não tem autor individual (RP 7)." },
  emenda_comissao: { rotulo: "Emenda de comissão", texto: "Emenda proposta por uma comissão permanente da Câmara ou do Senado (saúde, educação…). Também coletiva, sem autor individual (RP 8)." },
  emenda_relator: { rotulo: "Emenda de relator", texto: "Indicada pelo relator-geral do orçamento sem identificar quem pediu (o 'orçamento secreto', RP 9). Declarada inconstitucional pelo STF em dezembro de 2022." },
  alocou: { rotulo: "Alocou", texto: "Neste painel, 'alocou' = valor empenhado em emendas do autor. 'Recebeu' = valor efetivamente pago." },

  // Custo do parlamentar
  subsidio: { rotulo: "Subsídio", texto: "O salário do parlamentar, fixado por decreto legislativo do Congresso, igual para deputados e senadores. Pago 13 vezes ao ano mais um terço de férias." },
  cota_parlamentar: { rotulo: "Cota parlamentar (CEAP)", texto: "Verba mensal de reembolso de despesas do mandato: passagens, combustível, divulgação, aluguel de escritório, consultorias. Tem teto por estado; aqui entra só o que foi efetivamente usado." },
  glosa: { rotulo: "Glosa", texto: "Parte de uma nota apresentada à cota que a Câmara recusou reembolsar. Mostramos o valor líquido, já sem a glosa." },
  verba_gabinete: { rotulo: "Verba de gabinete", texto: "Valor mensal para contratar até 25 secretários parlamentares. A Câmara não publica na API quanto cada deputado usa; por isso contamos o teto, igual para todos." },
  auxilio_moradia: { rotulo: "Auxílio-moradia", texto: "Ajuda mensal para moradia em Brasília a quem não usa apartamento funcional. Fica fora do total porque não sabemos quem recebe." },
  teto: { rotulo: "Teto", texto: "Limite máximo permitido. Quando o gasto real não é publicado, usamos o teto e dizemos isso no rótulo." },
  projecao: { rotulo: "Projeção", texto: "Para o ano corrente, o custo anual é estimado: o que já foi gasto até o mês atual, projetado para 12 meses." },

  // Senadores
  ceaps_senado: { rotulo: "Cota CEAPS", texto: "Cota para Exercício da Atividade Parlamentar do Senado: reembolso de aluguel de escritório, locomoção e hospedagem, serviços de apoio, divulgação, passagens e material. Teto mensal varia por estado; aqui entra só o que foi reembolsado." },
  gastos_nao_inclusos: { rotulo: "Gastos fora da cota", texto: "Despesas do senador que o Senado paga por fora da cota e publica por nome: diárias de viagens oficiais, passagens aéreas compradas pelo Senado, correios, material e impulsionamento em mídias sociais." },
  imovel_funcional: { rotulo: "Imóvel funcional", texto: "Apartamento do Senado em Brasília cedido ao senador. Quem não ocupa pode receber auxílio-moradia. Nenhum dos dois entra no total porque o Senado não publica o custo por senador." },

  // STF
  remuneracao_bruta: { rotulo: "Remuneração bruta", texto: "Coluna 'remuneração bruta após o teto constitucional somada com outras verbas' da folha do STF: o subsídio limitado ao teto mais verbas indenizatórias e eventuais (auxílios, retroativos, substituições). Antes dos descontos de imposto de renda e previdência." },
  teto_constitucional: { rotulo: "Teto constitucional", texto: "Limite para qualquer remuneração no serviço público: o subsídio de ministro do STF (R$ 46.366,19 desde fevereiro de 2025). Verbas indenizatórias, como auxílios, ficam fora do teto, por isso o bruto pode passar dele." },
  gabinete_stf: { rotulo: "Gabinete do ministro", texto: "Equipe lotada no gabinete: assessores, analistas, técnicos, servidores cedidos de outros órgãos, juízes auxiliares. O valor é a soma da remuneração bruta de todos eles no mês, conforme a folha publicada pelo STF." },
  pessoas_gabinete: { rotulo: "Pessoas no gabinete", texto: "Quantas pessoas constam na folha do gabinete no último mês publicado. O número muda de mês para mês (entradas, saídas, cessões), por isso o custo do gabinete é a média mensal do ano, mas a contagem é a de um mês só." },
  gabinete_presidencia: { rotulo: "Gabinete da Presidência", texto: "O ministro que preside o STF aparece na folha lotado no Gabinete da Presidência, uma unidade administrativa pequena. A equipe que julga os processos dele fica em outras lotações que o portal não separa, por isso o custo do presidente sai subestimado aqui." },
  ministro_aposentado: { rotulo: "Ministros aposentados", texto: "Ex-ministros do STF que seguem pagos pela folha do próprio Tribunal, com proventos iguais aos da ativa (subsídio mais vantagens pessoais). Aposentadoria compulsória aos 75 anos. Mostramos o total como informação; não entra no custo de nenhum ministro em atividade." },

  // Municípios
  funcao_legislativa: { rotulo: "Função Legislativa", texto: "Classificação oficial do orçamento (Portaria 42/1999): tudo que o município paga com a Câmara de Vereadores — subsídio dos vereadores, servidores, prédio, contratos. Nos estados, inclui a Assembleia Legislativa e o Tribunal de Contas." },

  // Impostos
  arrecadacao: { rotulo: "Arrecadação", texto: "Tudo que entrou nos cofres da União em tributos federais no período, como a Receita Federal publica: impostos, contribuições (inclusive previdência) e receitas administradas por outros órgãos. Não inclui ICMS, IPVA, ISS e IPTU, que são de estados e municípios." },
  base_incidencia: { rotulo: "Base de incidência", texto: "Sobre o que o tributo é cobrado: consumo e produção (IPI, COFINS, PIS), folha de salários (previdência), lucro das empresas (IRPJ, CSLL), renda do trabalho (IRPF, IRRF sobre salários), renda do capital (IRRF sobre aplicações, IOF), patrimônio (ITR). É a classificação econômica usual; o agrupamento é nosso e está na metodologia." },
  quem_paga: { rotulo: "Quem recolhe não é quem paga", texto: "A Receita registra quem entregou o dinheiro, não quem o perdeu. COFINS e PIS são recolhidos pela empresa, mas entram no preço e saem do bolso do consumidor; a previdência tem a parte do empregado e a do patrão na mesma linha. Por isso falamos em 'vem do trabalho' e 'vem do consumo', não em 'imposto dos trabalhadores' ou 'das empresas'." },

  // Presidência
  cartao_corporativo: { rotulo: "Cartão corporativo (CPGF)", texto: "Cartão de Pagamento do Governo Federal: cartão de crédito em nome de servidores (portadores) para despesas pequenas e urgentes, como combustível, hospedagem e material. O Portal da Transparência publica cada transação com órgão, portador, fornecedor, data e valor." },
  sigilo: { rotulo: "Sob sigilo", texto: "Transação que o governo publica só com o valor, sem portador nem fornecedor, por segurança do presidente, do vice e das famílias (Lei de Acesso à Informação, art. 23). Nós mostramos o total sigiloso e a parte que ele representa; não há como saber em que foi gasto." },

  // Poderes
  maquina: { rotulo: "Manter a máquina", texto: "Despesas do 'Programa de Gestão e Manutenção' de cada Poder na Lei Orçamentária: salários, aposentadorias e pensões do órgão, prédios, custeio, equipamentos. É o que o Poder gasta para existir e funcionar." },
  politicas_publicas: { rotulo: "Políticas públicas", texto: "Programas finalísticos do orçamento: Previdência, SUS, Bolsa Família, educação, estradas. São serviços entregues à população, não custo de funcionamento do órgão." },
  encargos_especiais: { rotulo: "Encargos especiais", texto: "Despesas que não geram serviço nem produto: sentenças judiciais, precatórios, indenizações, participação em organismos internacionais (programas 09xx da LOA)." },
  divida_transferencias: { rotulo: "Dívida/Transferências", texto: "Juros e amortização da dívida pública, transferências constitucionais a estados e municípios, operações de crédito e encargos previdenciários de órgãos extintos. Não é custo de nenhum Poder, por isso fica fora da comparação." },
  funcoes_essenciais: { rotulo: "Funções essenciais", texto: "Ministério Público da União e Defensoria Pública da União: têm orçamento próprio e autonomia, mas a Constituição não os define como Poder." },
  pessoal_ativo: { rotulo: "Pessoal ativo e encargos", texto: "Salários de servidores, magistrados, parlamentares e militares na ativa, mais a contribuição patronal do órgão para a previdência deles." },
  aposentados: { rotulo: "Aposentados e pensionistas", texto: "Aposentadorias e pensões pagas pelo órgão a ex-servidores (e, no Executivo, a militares inativos). É despesa de pessoal, mas de quem não trabalha mais." },
  custeio: { rotulo: "Custeio", texto: "Despesas correntes para o órgão funcionar: energia, limpeza, segurança, TI, aluguel, diárias, material de consumo, terceirizados." },
  investimento: { rotulo: "Investimento", texto: "Obras, reformas, compra de equipamentos e imóveis: gastos que aumentam o patrimônio do órgão." },
  orgao_superior: { rotulo: "Órgão superior", texto: "O ministério, tribunal ou casa legislativa que responde pelo orçamento. Ex.: Ministério da Educação é o órgão superior das universidades federais." },
  unidade_orcamentaria: { rotulo: "Unidade orçamentária", texto: "A menor divisão da Lei Orçamentária com orçamento próprio: uma universidade, um tribunal regional, um fundo. É o que chamamos de 'órgão' nas tabelas." },
  per_capita: { rotulo: "Por habitante", texto: "Valor dividido pela população do Brasil estimada pelo IBGE (212,6 milhões). Serve só para dar escala; não é quanto cada pessoa pagou." },
  despesa_paga: { rotulo: "Despesa paga", texto: "Tudo que saiu do caixa no ano, incluindo benefícios e transferências. Não confundir com 'custo da máquina', que é só a parte de manutenção do órgão." },

  // Renda (PNAD Contínua)
  rendimento_habitual: { rotulo: "Rendimento médio habitual", texto: "Quanto a pessoa diz receber normalmente por mês no trabalho principal, em dinheiro ou produtos, antes de descontos. Média entre quem tem rendimento; a PNAD é uma pesquisa por amostra do IBGE, com margem de erro." },
  setor_publico_pnad: { rotulo: "Setor público (PNAD)", texto: "Empregados de órgãos públicos das três esferas: servidores estatutários, militares e celetistas. Inclui professor da rede municipal e agente de saúde, não só carreiras federais. Comparar a média com o setor privado mistura ocupações e escolaridades diferentes." },
  percentil: { rotulo: "Percentil (P10, P90, P99)", texto: "Imagine todos os brasileiros em fila, do que tem menos renda para o que tem mais. O percentil é a renda de quem está num certo ponto dessa fila: no P10 ficam 10% das pessoas atrás, no P50 metade, no P90 noventa por cento. Por isso 'acima do P90' quer dizer 'entre os 10% mais ricos' e 'acima do P99', 'no 1% mais rico'." },
  renda_domiciliar_pc: { rotulo: "Renda domiciliar por pessoa", texto: "Soma de todos os rendimentos do domicílio (trabalho, aposentadoria, aluguel, programas sociais) dividida pelo número de moradores. É a medida que o IBGE usa para distribuição e desigualdade." },
  gini: { rotulo: "Índice de Gini", texto: "Mede desigualdade de 0 (todos com a mesma renda) a 1 (uma pessoa com tudo). Calculado pelo IBGE sobre a renda domiciliar por pessoa." },
  // Educação (IDEB)
  ideb: { rotulo: "IDEB", texto: "Índice de Desenvolvimento da Educação Básica, do INEP: taxa de aprovação multiplicada pela nota média no Saeb (português e matemática), de 0 a 10. Divulgado a cada dois anos para anos iniciais (1º ao 5º), anos finais (6º ao 9º) e ensino médio." },
  rede_publica: { rotulo: "Rede pública", texto: "Escolas estaduais e municipais juntas (e federais, quando há). Nos anos iniciais a maior parte é municipal; no ensino médio, estadual. O IDEB por município é calculado só para a rede pública." },
  // Segurança (Sinesp)
  taxa_100k: { rotulo: "Taxa por 100 mil habitantes", texto: "Número de ocorrências ou vítimas no ano dividido pela população estimada pelo IBGE e multiplicado por 100 mil. Permite comparar lugares de tamanhos diferentes; em cidades pequenas, poucos casos mudam muito a taxa." },
  registro_policial: { rotulo: "Registro policial", texto: "O dado é o que as polícias civis e militares registraram e os estados enviaram ao Ministério da Justiça (Sinesp VDE). Crimes não denunciados não aparecem; cada estado alimenta o sistema no seu ritmo e pode corrigir depois." },
  homicidio_doloso: { rotulo: "Homicídio doloso", texto: "Morte causada intencionalmente por outra pessoa, contada em vítimas. Feminicídio, latrocínio (roubo seguido de morte) e lesão corporal seguida de morte são registrados em categorias próprias; aqui cada uma aparece separada, como o MJ publica." },
  // Punições e sanções
  improbidade: { rotulo: "Improbidade administrativa", texto: "Lei 8.429/1992: pune agente público (e quem agiu com ele) por enriquecimento ilícito, por causar prejuízo ao erário ou por violar princípios da administração. Quem aplica é a Justiça, em ação movida pelo Ministério Público ou pelo próprio órgão; as penas vão de multa e devolução do dinheiro a perda do cargo e proibição de contratar." },
  ceis: { rotulo: "CEIS", texto: "Cadastro de Empresas Inidôneas e Suspensas: a lista oficial de quem está impedido de contratar com o poder público, por decisão de órgãos federais, estaduais ou municipais. Inclui empresas e pessoas físicas, e reúne sanções da Lei de Licitações, da Lei do Pregão e da Lei de Improbidade." },
  lei_anticorrupcao: { rotulo: "Lei Anticorrupção", texto: "Lei 12.846/2013: pune a empresa — e não apenas a pessoa que agiu — por atos contra a administração pública, como pagar propina ou fraudar licitação. As punições vão de multa a dissolução compulsória e ficam no CNEP." },
  leniencia: { rotulo: "Acordo de leniência", texto: "Acordo em que a empresa admite a irregularidade, colabora com a investigação, devolve o que ganhou indevidamente e paga multa, em troca de redução da punição e do direito de continuar contratando com o poder público. Quem assina pela União é a CGU, com a AGU." },
  expulsao: { rotulo: "Expulsão da administração", texto: "Punição máxima a servidor federal em processo disciplinar: demissão (de quem está na ativa), cassação de aposentadoria (de quem já saiu) ou destituição de cargo. Fica registrada no CEAF, com o artigo do Estatuto do Servidor que embasou a decisão." },
  cpi: { rotulo: "Índice de Percepção da Corrupção", texto: "Nota de 0 a 100 que a Transparência Internacional, uma ONG, calcula para cada país a partir de pesquisas com especialistas e executivos. Mede percepção, não casos comprovados, e por isso fica separado dos registros oficiais." },
  carga_tributaria: { rotulo: "Carga tributária bruta", texto: "Tudo que União, estados e municípios arrecadam em impostos, taxas e contribuições (inclusive previdência) dividido pelo PIB, o valor de tudo que o país produziu no ano. É a medida oficial do peso da tributação, calculada pela Receita Federal com o PIB do IBGE. Não é o quanto uma pessoa paga: é a proporção do bolo inteiro." },
  faixa_pessoal: { rotulo: "Faixa de pessoal ocupado", texto: "Quantas pessoas trabalham na empresa, contando sócios e donos que trabalham nela, não só os assalariados. O IBGE agrupa as empresas em faixas (de 0 a 4 pessoas até 500 ou mais) no Cadastro Central de Empresas, que cobre quem tem CNPJ e entrega as declarações." },
  // Inflação
  ipca: { rotulo: "IPCA", texto: "Índice Nacional de Preços ao Consumidor Amplo, o índice oficial de inflação do país. O IBGE acompanha todo mês o preço de centenas de produtos e serviços em 16 áreas e calcula quanto subiu a cesta de uma família com renda de 1 a 40 salários mínimos. É o índice usado na meta do Banco Central." },
  inpc: { rotulo: "INPC", texto: "Índice Nacional de Preços ao Consumidor: mesma coleta do IPCA, mas com a cesta das famílias que ganham até 5 salários mínimos, onde comida e transporte pesam mais. É o índice usado em muitos reajustes salariais." },
  meta_inflacao: { rotulo: "Meta de inflação", texto: "Percentual de alta de preços que o Conselho Monetário Nacional define como objetivo para o ano; o Banco Central usa os juros para persegui-la. Há uma margem de tolerância em torno do valor central, que não mostramos no gráfico." },
  peso_ipca: { rotulo: "Peso na cesta", texto: "Quanto cada grupo representa do gasto da família média pesquisada. Alimentação e transporte pesam muito; comunicação pesa pouco. Por isso um item que sobe 20% pode mexer pouco no índice geral se o peso dele for pequeno." },
  // Obras
  obra_parada: { rotulo: "Paralisada ou inacabada", texto: "No cadastro federal de obras, 'paralisada' é a obra que começou e foi interrompida; 'inacabada' é a que foi abandonada sem ser concluída. Quem declara a situação é o órgão responsável pela obra, e a data registrada é a da última atualização do status — não necessariamente o dia em que as máquinas pararam." },
  // Previdência
  rgps: { rotulo: "RGPS (o regime do INSS)", texto: "Regime Geral de Previdência Social: quem trabalha com carteira assinada, por conta própria, como doméstico ou contribuinte individual contribui para ele e se aposenta por ele. É administrado pelo INSS, tem teto (em 2026, pouco acima de R$ 8 mil) e funciona por repartição: quem trabalha hoje paga quem está aposentado hoje." },
  rpps: { rotulo: "RPPS (regime próprio do servidor)", texto: "Regime Próprio de Previdência Social: cada ente — União, estado ou município — tem o seu, para os servidores concursados. Quem entrou depois da reforma de 2019 (ou de quando o ente criou previdência complementar) também tem teto igual ao do INSS; quem entrou antes pode ter regras de transição mais generosas. Militares têm sistema próprio, separado." },
  aposentadoria_idade_tempo: { rotulo: "Por idade × por tempo de contribuição", texto: "Até a reforma de 2019 dava para se aposentar só por tempo de contribuição (35 anos para homem, 30 para mulher), sem idade mínima; ou por idade (65/60) com menos tempo de contribuição. A Emenda 103/2019 acabou com a modalidade só por tempo e criou idade mínima para todos, com regras de transição." },
  pensao_morte: { rotulo: "Pensão por morte", texto: "Benefício pago a cônjuge, companheiro e filhos de quem contribuía ou já recebia aposentadoria. Desde 2015 e 2019 o valor e a duração dependem da idade do beneficiário e do tempo de união e de contribuição." },
  beneficio_x_pessoa: { rotulo: "Benefício não é pessoa", texto: "As estatísticas do INSS contam benefícios emitidos, não beneficiários: quem recebe uma aposentadoria e uma pensão por morte aparece duas vezes. Por isso não dá para somar benefícios com população nem dizer que X milhões de pessoas vivem do INSS." },
  bpc: { rotulo: "BPC/LOAS", texto: "Benefício de Prestação Continuada: um salário mínimo por mês a pessoas com 65 anos ou mais e a pessoas com deficiência de famílias de baixa renda. Não exige nenhuma contribuição, não paga 13º e não gera pensão por morte — é assistência social, operada pelo INSS mas custeada pelo Tesouro." },
  // Saúde
  cobertura_planos: { rotulo: "Cobertura de planos de saúde", texto: "Quantos vínculos de plano de assistência médica existem, dividido pela população. A ANS conta vínculos, não pessoas: quem tem dois planos conta duas vezes, e por isso em algumas cidades a taxa passa de 100%. Quem não aparece aqui depende do SUS — que atende todo mundo, inclusive quem tem plano." },
  repasse_saude: { rotulo: "Valores que se sobrepõem", texto: "Boa parte do que a União paga em saúde é repassada a estados e prefeituras (transferências fundo a fundo do SUS) e aparece de novo na despesa deles. Somar os três níveis contaria o mesmo dinheiro duas vezes, por isso mostramos cada um separado e nunca um total do país." },
  esperanca_vida: { rotulo: "Esperança de vida ao nascer", texto: "Quantos anos viveria, em média, uma pessoa nascida hoje se as taxas de morte de cada idade continuassem as de hoje. Não é uma previsão sobre ninguém em particular: é um retrato da mortalidade atual." },
  projecao_ibge: { rotulo: "Projeção do IBGE", texto: "Número calculado pelo IBGE na Projeção da População, não medido diretamente no ano. É a única série de esperança de vida e mortalidade infantil por estado que chega ao ano corrente; por isso a usamos, sempre dizendo que é projeção." },
  mortalidade_menores5: { rotulo: "Mortalidade de menores de 5 anos", texto: "De cada mil crianças nascidas vivas, quantas morrem antes de completar 5 anos. Indicador 3.2.1 dos Objetivos de Desenvolvimento Sustentável, calculado pelo IBGE com os registros de óbito do Ministério da Saúde." },
  mortalidade_neonatal: { rotulo: "Mortalidade neonatal", texto: "De cada mil crianças nascidas vivas, quantas morrem nos primeiros 27 dias de vida. É a parte da mortalidade infantil mais ligada ao pré-natal e ao parto." },
  mortalidade_materna: { rotulo: "Mortalidade materna", texto: "Mortes de mulheres por causas ligadas à gravidez, ao parto ou ao pós-parto, a cada 100 mil crianças nascidas vivas. Indicador 3.1.1 dos Objetivos de Desenvolvimento Sustentável." },
  // Crédito (Banco Central)
  inadimplencia_scr: { rotulo: "Inadimplência (SCR)", texto: "Parte do dinheiro emprestado que está com parcelas vencidas há mais de 90 dias, dividida por todo o crédito ativo. É inadimplência em reais, não em número de pessoas: o Banco Central não publica quantas pessoas estão com nome sujo." },
  carteira_ativa: { rotulo: "Carteira ativa", texto: "Tudo que bancos, cooperativas e financeiras têm emprestado a pessoas (PF) ou empresas (PJ) na data: parcelas a vencer e vencidas. Fonte: SCR, o cadastro de operações de crédito do Banco Central." },
  modalidade_credito: { rotulo: "Modalidade", texto: "Tipo de crédito: empréstimos (cartão, consignado, pessoal), financiamentos (veículos), imobiliário, rural, entre outros, conforme a classificação do Banco Central." },
};

export type TermoId = keyof typeof GLOSSARIO;
