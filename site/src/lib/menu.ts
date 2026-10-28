/**
 * Menu do site em dois níveis. Fonte única: o cabeçalho, as páginas de seção (/secao/<slug>/) e o rodapé
 * leem daqui. Eram 30 itens numa linha só; agora são 6 grupos, e a segunda linha mostra só os painéis do
 * grupo em que a página está.
 *
 * Ordem dos grupos = o caminho do dinheiro: entra (quanto pagamos), sai (quem gasta), chega no território
 * (onde), vira serviço (o que recebemos), afeta a vida (como vivemos) e por fim o contexto (no mundo e no tempo).
 */
export type ItemMenu = { href: string; label: string; nota: string };
export type GrupoMenu = { slug: string; nome: string; chamada: string; itens: ItemMenu[] };

export const GRUPOS: GrupoMenu[] = [
  {
    slug: "quanto-pagamos", nome: "Quanto pagamos",
    chamada: "O dinheiro que sai do seu bolso: quanto o país arrecada, quem paga e quanto a inflação come.",
    itens: [
      { href: "/impostos/", label: "Impostos", nota: "Arrecadação por tributo, por base e por estado, e quantos meses do ano o país trabalha só para pagar imposto." },
      { href: "/imposto-de-renda/", label: "Imposto de Renda", nota: "Quanto cada faixa declara e paga, de onde vem a renda isenta do topo e quantos ganham mais que um deputado." },
      { href: "/inflacao/", label: "Inflação", nota: "O IPCA desde 1979, o poder de compra do real desde o Plano Real e o câmbio frente a outras moedas." },
    ],
  },
  {
    slug: "quem-gasta", nome: "Quem gasta",
    chamada: "Para onde o dinheiro vai dentro do Estado: cada Poder, cada casa, cada gabinete, com a folha publicada.",
    itens: [
      { href: "/", label: "Panorama", nota: "O retrato geral: o que a União, os estados e os municípios pagaram, e em quê." },
      { href: "/poderes/", label: "Poderes", nota: "Orçamento inteiro da União, do autorizado ao pago, e quanto custa manter a máquina de cada Poder." },
      { href: "/presidencia/", label: "Presidência", nota: "Cartão corporativo da Presidência da República, mês a mês, e o que está sob sigilo." },
      { href: "/deputados/", label: "Deputados", nota: "Custo de cada um dos 513, com cota parlamentar real, verba de gabinete e a bancada de cada estado." },
      { href: "/senadores/", label: "Senadores", nota: "Custo dos 81, com a cota do Senado e os gastos que ficam fora dela." },
      { href: "/judiciario/", label: "Judiciário", nota: "Custo por ministro com o gabinete no STF, STJ, TST, STM, TRF4 e TRF6, tribunal a tribunal." },
      { href: "/emendas/", label: "Emendas", nota: "Quanto cada parlamentar alocou e quanto foi pago, por função e por destino." },
      { href: "/corrupcao/", label: "Corrupção", nota: "Punições por improbidade, multas da Lei Anticorrupção, acordos de leniência e servidores expulsos." },
    ],
  },
  {
    slug: "onde", nome: "Onde",
    chamada: "O mesmo dinheiro visto pelo território: seu estado, sua cidade e as obras que deveriam estar de pé.",
    itens: [
      { href: "/estados/", label: "Estados", nota: "O que cada estado paga por função e por habitante, com mapa." },
      { href: "/municipios/", label: "Municípios", nota: "O custo da Câmara de cada uma das 5,5 mil cidades, por habitante e por vereador." },
      { href: "/obras/", label: "Obras", nota: "O cadastro federal de investimentos e as obras paralisadas ou inacabadas, por estado e por tipo." },
    ],
  },
  {
    slug: "o-que-recebemos", nome: "O que recebemos",
    chamada: "O que o dinheiro compra e o que ele paga: serviço na ponta e benefício no fim do mês.",
    itens: [
      { href: "/saude/", label: "Saúde", nota: "Quanto os três níveis gastam, quantos têm plano e os indicadores de cada estado." },
      { href: "/educacao/", label: "Educação", nota: "IDEB por estado e município, até onde os adultos estudaram e o analfabetismo desde 1991." },
      { href: "/seguranca/", label: "Segurança", nota: "Mortes violentas intencionais por estado e por município, com a série desde 2015." },
      { href: "/inss/", label: "INSS", nota: "Tudo que o instituto paga, e por que 42% disso não é aposentadoria." },
      { href: "/aposentadoria/", label: "Aposentadoria", nota: "Os dois regimes lado a lado: o INSS e o regime próprio dos servidores." },
    ],
  },
  {
    slug: "como-vivemos", nome: "Como vivemos",
    chamada: "O país que paga a conta: quem trabalha, quanto ganha e quanto deve.",
    itens: [
      { href: "/trabalho/", label: "Trabalho", nota: "Quem trabalha, quem contribui, o tamanho das empresas e de onde vem a renda das famílias." },
      { href: "/renda/", label: "Renda", nota: "Público e privado, os 10% e o 1% mais ricos, e quantos vivem com até um salário mínimo." },
      { href: "/inadimplencia/", label: "Inadimplência", nota: "A parte do crédito vencida há mais de 90 dias, por estado, modalidade e ocupação." },
    ],
  },
  {
    slug: "no-mundo-e-no-tempo", nome: "No mundo e no tempo",
    chamada: "O Brasil comparado com outros países e com o próprio passado.",
    itens: [
      { href: "/comparacao/", label: "Comparação", nota: "Quanto cada país gasta nas mesmas coisas, quanto custa a Justiça, a Coroa e os parlamentos." },
      { href: "/rankings/", label: "Rankings", nota: "A posição do Brasil em dez indicadores internacionais, com a trajetória de cada um." },
      { href: "/historico/", label: "Histórico", nota: "Séries longas corrigidas pela inflação e até onde cada fonte volta no tempo." },
    ],
  },
];

/** Links de serviço: ficam numa faixa própria, menor, porque não são painel de dado. */
export const SERVICO: ItemMenu[] = [
  { href: "/agora/", label: "Agora", nota: "O que está sendo olhado no site neste momento." },
  { href: "/sugestoes/", label: "Sugestões", nota: "Diga qual número público está faltando aqui." },
  { href: "/dados/", label: "Dados", nota: "Catálogo dos arquivos abertos que alimentam cada painel." },
  { href: "/metodologia/", label: "Metodologia", nota: "Como cada número é apurado, com as fontes e os limites." },
  { href: "/sobre/", label: "Sobre", nota: "O que é este site e quem o mantém." },
];

/** Grupo a que uma rota pertence (usa o painel-pai: /deputados/uf/sp/ cai em Deputados). */
export function grupoDe(caminho: string): GrupoMenu | null {
  const partes = caminho.split("/").filter(Boolean);
  if (partes[0] === "secao") return GRUPOS.find((g) => g.slug === partes[1]) ?? null;
  const alvo = caminho === "/" ? "/" : `/${partes[0] ?? ""}/`;
  return GRUPOS.find((g) => g.itens.some((i) => i.href === alvo)) ?? null;
}

export function itemAtivo(caminho: string, href: string): boolean {
  if (href === "/") return caminho === "/";
  return caminho === href || caminho.startsWith(href);
}
