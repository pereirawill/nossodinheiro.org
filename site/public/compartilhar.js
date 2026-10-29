// Link por seção e botão de compartilhar. Melhoria progressiva: sem JS a página funciona igual, só sem os botões.
// Não carrega nada externo, não lê nem grava dado de quem acessa.
(function () {
  var toastEl = null;
  function toast(msg) {
    if (!toastEl) {
      toastEl = document.createElement("div");
      toastEl.className = "nd-toast";
      toastEl.setAttribute("role", "status");
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    toastEl.classList.add("mostrar");
    clearTimeout(toastEl._t);
    toastEl._t = setTimeout(function () { toastEl.classList.remove("mostrar"); }, 1800);
  }

  function copiar(texto) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(texto);
    }
    var ta = document.createElement("textarea");
    ta.value = texto; ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.focus(); ta.select();
    try { document.execCommand("copy"); } catch (e) {}
    document.body.removeChild(ta);
    return Promise.resolve();
  }

  // --- link de cada seção (H2) ---
  var ICONE = '<svg viewBox="0 0 16 16" width="13" height="13" aria-hidden="true"><path fill="currentColor" d="M6.5 9.5a1 1 0 0 0 1.4 1.4l3-3a1 1 0 0 0-1.4-1.4l-.3.3a2.5 2.5 0 0 0-3.5 0l-2 2a2.5 2.5 0 0 0 3.5 3.5l.9-.9a1 1 0 0 0-1.3-1.5l-.9.9a.5.5 0 0 1-.7-.7l2-2a.5.5 0 0 1 .7 0l.1.1-1.4 1.4-.1-.1Zm3-3 2-2a2.5 2.5 0 0 0-3.5-3.5l-.9.9a1 1 0 1 0 1.3 1.5l.9-.9a.5.5 0 0 1 .7.7l-2 2a.5.5 0 0 1-.7 0l-.1-.1 1.4-1.4.1.1a1 1 0 0 0-1.4 1.4l.2.3Z"/></svg>';
  var usados = {};
  function slug(t) {
    var s = t.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
      .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "secao";
    var base = s, n = 2;
    while (usados[s]) { s = base + "-" + n++; }
    usados[s] = true;
    return s;
  }

  document.querySelectorAll("main h2").forEach(function (h2) {
    if (!h2.id) h2.id = slug(h2.textContent || "");
    else usados[h2.id] = true;
    var a = document.createElement("a");
    a.href = "#" + h2.id;
    a.className = "h2-link";
    a.innerHTML = ICONE;
    a.setAttribute("aria-label", "Copiar o link desta seção");
    a.title = "Copiar o link desta seção";
    a.addEventListener("click", function () {
      var url = location.origin + location.pathname + location.search + "#" + h2.id;
      copiar(url).then(function () { toast("Link da seção copiado"); });
    });
    h2.appendChild(a);
  });

  // --- botão de compartilhar a página ---
  var btn = document.createElement("button");
  btn.type = "button";
  btn.className = "nd-compartilhar";
  btn.setAttribute("aria-label", "Compartilhar esta página");
  btn.title = "Compartilhar esta página";
  btn.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path fill="currentColor" d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7a2.5 2.5 0 0 0 0-1.4l7.05-4.11a2.99 2.99 0 1 0-.89-2.12l-7.05 4.11a3 3 0 1 0 0 5.64l7.13 4.16a3 3 0 1 0 2.85-2Z"/></svg>';
  btn.addEventListener("click", function () {
    var url = location.href;
    var titulo = document.title;
    if (navigator.share) {
      navigator.share({ title: titulo, url: url }).catch(function () {});
    } else {
      copiar(url).then(function () { toast("Link da página copiado"); });
    }
  });
  document.body.appendChild(btn);
})();
