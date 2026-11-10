// Lectures par grade (fiches de Ceintures/, bloc produit par
// scripts/generer-parcours.py) : les cases « lu » deviennent cliquables et
// restent cochées dans ce navigateur seulement.
(function () {
  function cle(lien) { return "parcours:" + new URL(lien, location.href).pathname; }

  function installer() {
    if (location.pathname.indexOf("/Ceintures/") === -1) return;
    document.querySelectorAll(".md-content .task-list-item").forEach(function (li) {
      var caseLu = li.querySelector("input[type=checkbox]");
      var lien = li.querySelector("a[href]");
      if (!caseLu || !lien || caseLu.dataset.parcours) return;
      caseLu.dataset.parcours = "1";
      caseLu.disabled = false;
      caseLu.title = "Marquer comme lu";
      try { caseLu.checked = localStorage.getItem(cle(lien.getAttribute("href"))) === "1"; } catch (e) {}
      caseLu.addEventListener("change", function () {
        try {
          if (caseLu.checked) localStorage.setItem(cle(lien.getAttribute("href")), "1");
          else localStorage.removeItem(cle(lien.getAttribute("href")));
        } catch (e) {}
      });
    });
  }

  // navigation.instant : la page change sans rechargement
  if (window.document$) window.document$.subscribe(installer);
  else document.addEventListener("DOMContentLoaded", installer);
})();
