/**
 * Painel "Agora": busca /api/agora e desenha. Única página do site com JavaScript de verdade, pelo motivo óbvio
 * de que número ao vivo não existe em página estática. Nada aqui lê nem grava dado de quem acessa.
 */
(function () {
  var alvo = document.getElementById("agora");
  if (!alvo) return;
  var num = function (v) { return (v || 0).toLocaleString("pt-BR"); };
  var esc = function (s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
    return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]; }); };

  function lista(itens, campo, rotulo) {
    if (!itens || !itens.length) return '<p class="src">Sem movimento suficiente nos últimos minutos.</p>';
    var max = Math.max.apply(null, itens.map(function (i) { return i[campo] || 0; })) || 1;
    return '<table><tbody>' + itens.map(function (i) {
      var larg = Math.round(((i[campo] || 0) / max) * 100);
      var nome = i.titulo ? esc(i.titulo) : esc(i.partido || i.uf || i.origem || i.slug);
      var link = i.slug ? '<a href="' + esc(i.slug) + '">' + nome + "</a>" : nome;
      return '<tr><td>' + link + '</td><td class="num">' + num(i[campo]) +
        (rotulo ? " " + rotulo : "") + '</td><td class="barra-cel"><span class="barra" style="width:' +
        larg + '%"></span></td></tr>';
    }).join("") + "</tbody></table>";
  }

  function desenhar(d) {
    if (d.indisponivel || d.erro) {
      alvo.innerHTML = '<div class="card"><p style="margin:0">O painel ao vivo está indisponível neste momento. ' +
        'O resto do site não depende dele.</p></div>';
      return;
    }
    var h = '<div class="hero">' +
      '<div class="stat big"><b>' + num(d.pessoas_agora) + '</b><span>pessoas no site <strong>neste momento</strong>' +
      ' (sessões distintas nos últimos 5 minutos)</span></div>' +
      '<div class="stat"><b>' + num(d.total_24h.pessoas) + '</b><span>pessoas nas últimas 24 horas, com ' +
      num(d.total_24h.n) + ' páginas abertas</span></div></div>' +
      '<h2>Os crachás que mais subiram na última hora</h2><div class="card">' + lista(d.subindo, "delta", "a mais") +
      '<p class="src">Comparação da última hora com a hora anterior, só páginas com pelo menos 3 aberturas na última hora.</p></div>' +
      '<h2>As páginas mais abertas do dia</h2><div class="card">' + lista(d.dia, "n") +
      '<p class="src">Últimas 24 horas, por número de aberturas.</p></div>';
    if (d.partidos.length) h += '<h2>Partidos mais olhados</h2><div class="card">' + lista(d.partidos, "n") + "</div>";
    if (d.ufs.length) h += '<h2>Estados mais consultados</h2><div class="card">' + lista(d.ufs, "n") + "</div>";
    if (d.origens.length) h += '<h2>De onde as pessoas chegam</h2><div class="card">' + lista(d.origens, "n") +
      '<p class="src">Só o domínio de origem; nunca o endereço completo. "direto" é quem digitou o endereço ou veio de aplicativo que não informa origem.</p></div>';
    alvo.innerHTML = h;
  }

  function buscar() {
    fetch("/api/agora", { headers: { accept: "application/json" } })
      .then(function (r) { return r.json(); })
      .then(desenhar)
      .catch(function () {
        alvo.innerHTML = '<div class="card"><p style="margin:0">Não foi possível carregar o painel ao vivo.</p></div>';
      });
  }
  buscar();
  setInterval(buscar, 20000);
})();
