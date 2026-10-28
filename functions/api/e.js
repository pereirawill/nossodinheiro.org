/**
 * Recebe o sinal de uma página aberta e grava uma linha agregável. Sem IP, sem user-agent, sem cookie.
 * O corpo vem de navigator.sendBeacon: {p: caminho, t: título, r: domínio de origem, s: id de sessão da aba}.
 * Se o banco não estiver ligado no projeto, responde 204 e o site segue funcionando sem o painel.
 */
const BOT = /bot|crawl|spider|slurp|bing|baidu|yandex|duckduck|facebookexternalhit|headless|lighthouse|preview/i;

function classificar(caminho) {
  const partes = caminho.replace(/^\/+|\/+$/g, "").split("/").filter(Boolean);
  const tipo = partes[0] || "home";
  let uf = null, partido = null;
  if ((tipo === "deputados" || tipo === "senadores") && partes[1] === "uf") uf = (partes[2] || "").toUpperCase();
  if ((tipo === "deputados" || tipo === "senadores") && partes[1] === "partido") partido = (partes[2] || "").toUpperCase();
  if (tipo === "municipios" && partes.length >= 2 && partes[1] !== "uf" && partes[1].length === 2) uf = partes[1].toUpperCase();
  if (tipo === "municipios" && partes[1] === "uf") uf = (partes[2] || "").toUpperCase();
  return { tipo, uf, partido };
}

export async function onRequestPost({ request, env }) {
  if (!env.DB) return new Response(null, { status: 204 });
  if (BOT.test(request.headers.get("user-agent") || "")) return new Response(null, { status: 204 });
  let d;
  try {
    d = await request.json();
  } catch {
    return new Response("corpo inválido", { status: 400 });
  }
  const caminho = String(d.p || "/").slice(0, 200);
  if (!caminho.startsWith("/")) return new Response("caminho inválido", { status: 400 });
  const sessao = String(d.s || "").slice(0, 40);
  if (!sessao) return new Response("sem sessão", { status: 400 });
  const titulo = String(d.t || "").replace(/\s*—\s*Nosso Dinheiro\s*$/, "").slice(0, 120) || caminho;
  const origem = String(d.r || "").toLowerCase().replace(/[^a-z0-9.\-]/g, "").slice(0, 60) || "direto";
  const { tipo, uf, partido } = classificar(caminho);
  const agora = Math.floor(Date.now() / 1000);
  try {
    await env.DB.prepare(
      "INSERT INTO evento (ts, sessao, tipo, slug, titulo, uf, partido, origem) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    ).bind(agora, sessao, tipo, caminho, titulo, uf, partido, origem).run();
    // limpeza preguiçosa: ~1 em 200 gravações apaga o que passou de 48 h
    if (Math.random() < 0.005) {
      await env.DB.prepare("DELETE FROM evento WHERE ts < ?").bind(agora - 172800).run();
    }
  } catch (e) {
    return new Response("banco indisponível", { status: 503 });
  }
  return new Response(null, { status: 204 });
}
