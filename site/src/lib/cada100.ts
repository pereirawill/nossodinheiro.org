/**
 * Para onde vai cada R$ 100 do gasto público, nos três níveis de governo, sem contar o mesmo real duas vezes.
 * Usado na home e em /conferir/ — uma conta só, para as duas páginas não divergirem.
 *
 * Base = União em políticas públicas e máquina, SEM os repasses a estados e municípios (que já estão no gasto de
 * quem recebeu), mais os juros que a União pagou no ano, mais os estados (sem encargos especiais, que o DCA não
 * abre) e as prefeituras que prestaram contas. Fora, de propósito: o refinanciamento da dívida, que é rolagem.
 *
 * O que é piso: a linha de juros é só da União (os dos estados estão nos encargos especiais excluídos); a
 * assistência social de estados e municípios não está nas funções que baixamos e fica em "todo o resto".
 * A folha de pessoal não é linha: o professor está em educação, o médico em saúde.
 */
export type Destino = { nome: string; v: number };

export function cada100(dados: {
  funcoes: any[]; poderes: any[]; categorias: any[]; estados: any[]; municipios: any[];
}) {
  const { funcoes, poderes, categorias, estados, municipios } = dados;
  const fn = (cod: string) => funcoes.find((f) => f.funcao === cod);
  const direta = (cod: string) => { const f = fn(cod); return f ? (f.pago_aplicacao_direta ?? f.pago) : 0; };
  const sE = (k: string) => estados.reduce((t, e) => t + (e[k] || 0), 0);
  const sM = (k: string) => municipios.reduce((t, m) => t + (m[k] || 0), 0);

  const juros = categorias.filter((c) => c.subcategoria === "Juros e Encargos da Dívida").reduce((t, c) => t + c.pago, 0);
  const uniaoPoliticas = poderes.filter((p) => p.poder !== "Dívida/Transferências").reduce((t, p) => t + p.pago, 0);
  // os repasses da função 28 já saem com o órgão (poder Dívida/Transferências); os demais estão dentro do Executivo
  const repasses = funcoes.filter((f) => f.funcao !== "28").reduce((t, f) => t + (f.pago_transferido_entes || 0), 0);
  const estadosSemEncargos = estados.reduce((t, e) => t + e.pago_total - (e.pago_encargos || 0), 0);
  const prefeituras = municipios.reduce((t, m) => t + (m.pago_total || 0), 0);
  const base = uniaoPoliticas - repasses + juros + estadosSemEncargos + prefeituras;

  const destinos: Destino[] = [
    { nome: "Aposentadoria e pensão", v: direta("09") + sE("pago_previdencia") },
    { nome: "Educação", v: direta("12") + sE("pago_educacao") + sM("pago_educacao") },
    { nome: "Saúde", v: direta("10") + sE("pago_saude") + sM("pago_saude") },
    { nome: "Juros da dívida", v: juros },
    { nome: "Administração", v: direta("04") + sE("pago_administracao") + sM("pago_administracao") },
    { nome: "Judiciário e Ministério Público", v: direta("02") + sE("pago_judiciaria") + sE("pago_essencial_justica") },
    { nome: "Segurança pública", v: direta("06") + sE("pago_seguranca") },
    { nome: "Legislativo", v: direta("01") + sE("pago_legislativa") + sM("pago_legislativo") },
  ].sort((a, b) => b.v - a.v);
  const resto = base - destinos.reduce((t, d) => t + d.v, 0);
  const por100 = (v: number) => (100 * v) / base;
  return { base, repasses, juros, destinos, resto, por100,
           r2: (v: number) => por100(v).toFixed(2).replace(".", ",") };
}
