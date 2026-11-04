// Bouton « Imprimer / PDF » sur les fiches d'examen (Requis Examen et
// examens théoriques). Il ouvre l'impression du navigateur, qui permet aussi
// d'« Enregistrer au format PDF ». Les corrigés repliés sont dépliés le temps
// de l'impression.
(function () {
  function installer() {
    var p = location.pathname;
    if (p.indexOf("/Ceintures/") === -1 && p.indexOf("/Theorie/examens/") === -1) return;
    var titre = document.querySelector(".md-content__inner h1");
    if (!titre || document.querySelector(".bouton-imprimer")) return;
    var b = document.createElement("button");
    b.type = "button";
    b.className = "md-button bouton-imprimer";
    b.textContent = "🖨 Imprimer / PDF";
    b.addEventListener("click", function () { window.print(); });
    titre.parentNode.insertBefore(b, titre.nextSibling);
  }
  var replies = [];
  window.addEventListener("beforeprint", function () {
    replies = Array.prototype.filter.call(document.querySelectorAll("details"), function (d) { return !d.open; });
    replies.forEach(function (d) { d.open = true; });
  });
  window.addEventListener("afterprint", function () {
    replies.forEach(function (d) { d.open = false; });
    replies = [];
  });
  if (window.document$) window.document$.subscribe(installer);
  else document.addEventListener("DOMContentLoaded", installer);
})();
