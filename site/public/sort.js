// Ordenação de tabelas por clique no cabeçalho. Melhoria progressiva: sem JS a tabela fica na ordem
      // padrão (maior custo primeiro). Não carrega nada externo. Números pt-BR ("R$ 1.234,56", "12%") e texto.
      (function () {
        var num = function (t) {
          var m = t.replace(/\s/g, "").replace(/[R$%]/g, "").replace(/\.(?=\d{3}(\D|$))/g, "").replace(",", ".");
          return /^-?\d+(\.\d+)?$/.test(m) ? parseFloat(m) : null;
        };
        var cell = function (tr, i) { var td = tr.children[i]; return td ? (td.dataset.v != null ? td.dataset.v : td.textContent.trim()) : ""; };
        document.querySelectorAll("table").forEach(function (table) {
          var thead = table.tHead, tbody = table.tBodies[0];
          if (!thead || !tbody || tbody.rows.length < 2) return;
          Array.prototype.forEach.call(thead.rows[0].cells, function (th, i) {
            if (th.textContent.trim() === "#") return;
            th.classList.add("ord"); th.tabIndex = 0; th.title = "Clique para ordenar";
            var go = function () {
              var asc = th.getAttribute("aria-sort") !== "ascending";
              Array.prototype.forEach.call(thead.rows[0].cells, function (o) { o.removeAttribute("aria-sort"); });
              th.setAttribute("aria-sort", asc ? "ascending" : "descending");
              var rows = Array.prototype.slice.call(tbody.rows);
              var numeric = rows.every(function (r) { var v = cell(r, i); return v === "" || v === "—" || num(v) !== null; });
              rows.sort(function (x, y) {
                var a = cell(x, i), b = cell(y, i);
                if (numeric) { var na = num(a), nb = num(b); na = na === null ? -Infinity : na; nb = nb === null ? -Infinity : nb; return asc ? na - nb : nb - na; }
                return asc ? a.localeCompare(b, "pt-BR") : b.localeCompare(a, "pt-BR");
              });
              rows.forEach(function (r) { tbody.appendChild(r); });
            };
            th.addEventListener("click", go);
            th.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } });
          });
        });
      })();
