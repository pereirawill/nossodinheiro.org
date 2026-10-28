/**
 * Agregados do painel "Agora". Só contagens; nenhuma linha identifica ninguém.
 *   agora        — sessões distintas vistas nos últimos 5 minutos
 *   dia          — páginas mais abertas nas últimas 24 h
 *   subindo      — páginas que mais cresceram na última hora contra a hora anterior
 *   partidos/ufs — filtros de parlamentar e de estado mais olhados nas últimas 24 h
 *   origens      — de onde as pessoas chegaram nas últimas 24 h
 * Cache de 20 s na borda: o número é "ao vivo" o suficiente e o banco não leva uma consulta por visita.
 */
const CACHE = "public, max-age=20, s-maxage=20";

export async function onRequestGet({ env }) {
  if (!env.DB) {
    return Response.json({ indisponivel: "o banco do painel não está ligado neste ambiente" },
                         { status: 503, headers: { "cache-control": "no-store" } });
  }
  const agora = Math.floor(Date.now() / 1000);
  const t5 = agora - 300, t1h = agora - 3600, t2h = agora - 7200, t24h = agora - 86400;
  try {
    const [pessoas, dia, horaAtual, horaAnterior, partidos, ufs, origens, total24h] = await env.DB.batch([
      env.DB.prepare("SELECT COUNT(DISTINCT sessao) AS n FROM evento WHERE ts > ?").bind(t5),
      env.DB.prepare(`SELECT slug, MAX(titulo) AS titulo, COUNT(*) AS n, COUNT(DISTINCT sessao) AS pessoas
                      FROM evento WHERE ts > ? GROUP BY slug ORDER BY n DESC LIMIT 12`).bind(t24h),
      env.DB.prepare(`SELECT slug, MAX(titulo) AS titulo, COUNT(*) AS n FROM evento WHERE ts > ? GROUP BY slug`).bind(t1h),
      env.DB.prepare(`SELECT slug, COUNT(*) AS n FROM evento WHERE ts > ? AND ts <= ? GROUP BY slug`).bind(t2h, t1h),
      env.DB.prepare(`SELECT partido, COUNT(*) AS n FROM evento WHERE ts > ? AND partido IS NOT NULL
                      GROUP BY partido ORDER BY n DESC LIMIT 10`).bind(t24h),
      env.DB.prepare(`SELECT uf, COUNT(*) AS n FROM evento WHERE ts > ? AND uf IS NOT NULL
                      GROUP BY uf ORDER BY n DESC LIMIT 10`).bind(t24h),
      env.DB.prepare(`SELECT origem, COUNT(*) AS n FROM evento WHERE ts > ? GROUP BY origem ORDER BY n DESC LIMIT 8`).bind(t24h),
      env.DB.prepare("SELECT COUNT(*) AS n, COUNT(DISTINCT sessao) AS pessoas FROM evento WHERE ts > ?").bind(t24h),
    ]);
    const anterior = new Map((horaAnterior.results ?? []).map((r) => [r.slug, r.n]));
    const titulos = new Map((dia.results ?? []).map((r) => [r.slug, r.titulo]));
    const subindo = (horaAtual.results ?? [])
      .map((r) => ({ slug: r.slug, titulo: r.titulo || titulos.get(r.slug) || r.slug,
                     agora: r.n, antes: anterior.get(r.slug) ?? 0 }))
      .map((r) => ({ ...r, delta: r.agora - r.antes }))
      .filter((r) => r.delta > 0 && r.agora >= 3)
      .sort((a, b) => b.delta - a.delta || b.agora - a.agora)
      .slice(0, 8);
    return Response.json({
      gerado_em: new Date().toISOString(),
      pessoas_agora: pessoas.results?.[0]?.n ?? 0,
      dia: dia.results ?? [],
      subindo,
      partidos: partidos.results ?? [],
      ufs: ufs.results ?? [],
      origens: origens.results ?? [],
      total_24h: total24h.results?.[0] ?? { n: 0, pessoas: 0 },
    }, { headers: { "cache-control": CACHE } });
  } catch (e) {
    return Response.json({ erro: "consulta falhou" }, { status: 503, headers: { "cache-control": "no-store" } });
  }
}
