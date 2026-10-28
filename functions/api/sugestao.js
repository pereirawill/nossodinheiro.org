/**
 * Recebe sugestões do formulário de /sugestoes/. Aceita JSON (envio por JavaScript) e formulário comum
 * (sem JavaScript), caso em que responde com redirecionamento para a página de agradecimento.
 * Não grava IP, user-agent nem cookie. O contato é opcional e vem digitado pela própria pessoa.
 */
const MIN = 10, MAX = 2000, MAX_CONTATO = 120;

function responder(form, env, status, mensagem) {
  if (form) {
    const destino = status === 200 ? "/sugestoes/obrigado/" : "/sugestoes/?erro=1";
    return new Response(null, { status: 303, headers: { location: destino } });
  }
  return Response.json(status === 200 ? { ok: true } : { erro: mensagem }, { status });
}

export async function onRequestPost({ request, env }) {
  const tipo = request.headers.get("content-type") || "";
  const form = !tipo.includes("application/json");
  let d = {};
  try {
    if (form) {
      const fd = await request.formData();
      d = { texto: fd.get("texto"), contato: fd.get("contato"), assunto: fd.get("assunto"), s: fd.get("s") };
    } else {
      d = await request.json();
    }
  } catch {
    return responder(form, env, 400, "corpo inválido");
  }
  // campo-armadilha: fica escondido no formulário, então só robô preenche
  if (String(d.assunto || "").trim()) return responder(form, env, 200, null);

  const texto = String(d.texto || "").trim().slice(0, MAX);
  if (texto.length < MIN) return responder(form, env, 400, `escreva pelo menos ${MIN} caracteres`);
  const contato = String(d.contato || "").trim().slice(0, MAX_CONTATO) || null;
  const sessao = String(d.s || "").slice(0, 40) || null;
  let pagina = null;
  try {
    pagina = new URL(request.headers.get("referer") || "").pathname.slice(0, 200);
  } catch {}

  if (!env.DB) return responder(form, env, 503, "o banco de sugestões não está ligado neste ambiente");
  const agora = Math.floor(Date.now() / 1000);
  try {
    if (sessao) {
      const { results } = await env.DB.prepare(
        "SELECT COUNT(*) AS n, MAX(ts) AS ultimo FROM sugestao WHERE sessao = ? AND ts > ?"
      ).bind(sessao, agora - 3600).all();
      const r = results?.[0] || {};
      if ((r.n ?? 0) >= 3) return responder(form, env, 429, "já recebemos várias sugestões suas nesta hora, obrigado");
      if (r.ultimo && agora - r.ultimo < 20) return responder(form, env, 429, "espere alguns segundos");
    }
    await env.DB.prepare(
      "INSERT INTO sugestao (ts, texto, contato, pagina, sessao) VALUES (?, ?, ?, ?, ?)"
    ).bind(agora, texto, contato, pagina, sessao).run();
  } catch {
    return responder(form, env, 503, "não foi possível gravar agora");
  }
  return responder(form, env, 200, null);
}
