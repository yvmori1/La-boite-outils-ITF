// Mode révision des examens théoriques (Theorie/examens/).
// Après chaque corrigé, deux boutons : « Je savais » / « À revoir ».
// Un bandeau en haut de page tient le score et permet de ne revoir que les
// questions ratées. Les réponses sont gardées dans ce navigateur seulement.
(function () {
  function cle() { return "quiz:" + location.pathname; }
  function lire() {
    try { return JSON.parse(localStorage.getItem(cle())) || {}; } catch (e) { return {}; }
  }
  function ecrire(etat) {
    try { localStorage.setItem(cle(), JSON.stringify(etat)); } catch (e) {}
  }

  function installer() {
    if (location.pathname.indexOf("/Theorie/examens/") === -1) return;
    var contenu = document.querySelector(".md-content__inner");
    if (!contenu || contenu.querySelector(".quiz-bandeau")) return;

    // une question = un titre h3 « Q1. … » suivi de son <details> corrigé
    var questions = [];
    contenu.querySelectorAll("h3").forEach(function (h) {
      if (!/^Q\d+/.test(h.textContent.trim())) return;
      var bloc = [h], n = h.nextElementSibling, details = null;
      while (n && !/^H[1-3]$/.test(n.tagName)) {
        bloc.push(n);
        if (n.tagName === "DETAILS") details = n;
        n = n.nextElementSibling;
      }
      if (details) questions.push({ id: h.id || h.textContent.slice(0, 40), bloc: bloc, details: details });
    });
    if (!questions.length) return;

    var etat = lire();
    var filtre = false;

    var bandeau = document.createElement("div");
    bandeau.className = "quiz-bandeau admonition tip";
    bandeau.innerHTML =
      '<p class="admonition-title">Mode révision</p>' +
      '<p>Lisez la question, répondez de tête, ouvrez le corrigé puis notez-vous.</p>' +
      '<p class="quiz-score"></p>' +
      '<p><button type="button" class="md-button quiz-filtre">Revoir seulement les questions à revoir</button> ' +
      '<button type="button" class="md-button quiz-zero">Recommencer</button></p>';
    var premier = contenu.querySelector("h2") || questions[0].bloc[0];
    premier.parentNode.insertBefore(bandeau, premier);

    function maj() {
      var sus = 0, rev = 0;
      questions.forEach(function (q) {
        var v = etat[q.id];
        if (v === "ok") sus++; else if (v === "ko") rev++;
        q.boutons.forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.v === v ? "true" : "false"); });
        var cacher = filtre && v !== "ko";
        q.bloc.forEach(function (el) { el.style.display = cacher ? "none" : ""; });
      });
      bandeau.querySelector(".quiz-score").textContent =
        "Score : " + sus + " / " + questions.length + " sues · " + rev + " à revoir · " +
        (questions.length - sus - rev) + " sans réponse";
      bandeau.querySelector(".quiz-filtre").textContent = filtre
        ? "Afficher toutes les questions" : "Revoir seulement les questions à revoir";
    }

    questions.forEach(function (q) {
      var p = document.createElement("p");
      p.className = "quiz-choix";
      q.boutons = [["ok", "✓ Je savais"], ["ko", "✗ À revoir"]].map(function (c) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "md-button quiz-" + c[0];
        b.dataset.v = c[0];
        b.textContent = c[1];
        b.addEventListener("click", function () {
          etat[q.id] = etat[q.id] === c[0] ? undefined : c[0];
          ecrire(etat); maj();
        });
        p.appendChild(b);
        p.appendChild(document.createTextNode(" "));
        return b;
      });
      q.details.parentNode.insertBefore(p, q.details.nextSibling);
      q.bloc.push(p);
    });

    bandeau.querySelector(".quiz-filtre").addEventListener("click", function () { filtre = !filtre; maj(); });
    bandeau.querySelector(".quiz-zero").addEventListener("click", function () {
      etat = {}; filtre = false; ecrire(etat);
      questions.forEach(function (q) { q.details.open = false; });
      maj();
    });
    maj();
  }

  if (window.document$) window.document$.subscribe(installer);
  else document.addEventListener("DOMContentLoaded", installer);
})();
