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
};

export type TermoId = keyof typeof GLOSSARIO;
