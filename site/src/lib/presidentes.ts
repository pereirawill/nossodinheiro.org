/**
 * Quem era presidente da República em cada período, para servir de régua de tempo embaixo dos gráficos.
 *
 * É só marcação de tempo: nenhum número deste site é atribuído a nenhum governo. Lucro de banco, inflação e
 * arrecadação dependem de lei, juro, câmbio e economia mundial, e separar o efeito de cada coisa exige estudo
 * que não é um dado público — a mesma regra que a página de Trânsito aplica à queda das mortes desde 2012.
 *
 * Datas: a posse presidencial é em 1º de janeiro (Constituição, art. 82, com o mandato de quatro anos; até 2018
 * a posse ocorria em 1º de janeiro do ano seguinte à eleição). A única troca fora dessa data no período é a de
 * 2016: Michel Temer assumiu interinamente em 12/05/2016, quando o Senado instaurou o processo, e em definitivo
 * em 31/08/2016, com a Resolução 35/2016 do Senado Federal. Usamos 31/08/2016 como fronteira e declaramos o
 * período de interinidade.
 *
 * A Galeria de Presidentes da Presidência da República (fonte da lista) estava fora do ar em 29/10/2026 —
 * a página do Planalto exige verificação e a Biblioteca da Presidência respondia "em manutenção".
 */
export type Presidente = { nome: string; curto: string; inicio: string; fim: string | null; nota?: string };

export const FONTE_PRESIDENTES = {
  nome: "Presidência da República — Galeria de Presidentes; Senado Federal, Resolução 35/2016",
  url: "https://www.gov.br/planalto/pt-br/conheca-a-presidencia/galeria-de-presidentes",
  lido: "29/10/2026",
};

/** Da véspera do Plano Real até hoje. `fim: null` = em exercício. */
export const PRESIDENTES: Presidente[] = [
  { nome: "Itamar Franco", curto: "Itamar", inicio: "1992-12-29", fim: "1995-01-01" },
  { nome: "Fernando Henrique Cardoso", curto: "FHC", inicio: "1995-01-01", fim: "2003-01-01" },
  { nome: "Luiz Inácio Lula da Silva", curto: "Lula", inicio: "2003-01-01", fim: "2011-01-01" },
  { nome: "Dilma Rousseff", curto: "Dilma", inicio: "2011-01-01", fim: "2016-08-31",
    nota: "afastada em 12/05/2016, quando o vice assumiu interinamente" },
  { nome: "Michel Temer", curto: "Temer", inicio: "2016-08-31", fim: "2019-01-01",
    nota: "no exercício do cargo desde 12/05/2016, de forma interina" },
  { nome: "Jair Bolsonaro", curto: "Bolsonaro", inicio: "2019-01-01", fim: "2023-01-01" },
  { nome: "Luiz Inácio Lula da Silva", curto: "Lula", inicio: "2023-01-01", fim: null },
];

/** Posição do começo de um mandato na escala do gráfico, em anos fracionários (2016-08-31 → 2016,66). */
export function anoFracionario(data: string): number {
  const d = new Date(data + "T00:00:00Z");
  const ano = d.getUTCFullYear();
  const inicio = Date.UTC(ano, 0, 1), fim = Date.UTC(ano + 1, 0, 1);
  return ano + (d.getTime() - inicio) / (fim - inicio);
}
