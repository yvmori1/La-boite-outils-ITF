// Lit la prononciation sur place : un clic sur un lien vers un fichier .m4a
// joue le son dans la page au lieu d'ouvrir le fichier dans un nouvel onglet.
// Un second clic sur le même lien arrête la lecture. Ctrl/Cmd+clic garde le
// comportement normal du navigateur (ouvrir ou télécharger le fichier).
(function () {
  var lecteur = null;
  var lienActif = null;

  function arreter() {
    if (lecteur) { lecteur.pause(); lecteur = null; }
    if (lienActif) { lienActif.classList.remove("audio-en-cours"); lienActif = null; }
  }

  document.addEventListener("click", function (e) {
    if (e.defaultPrevented || e.button !== 0 || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
    var lien = e.target.closest && e.target.closest('a[href$=".m4a"]');
    if (!lien) return;
    e.preventDefault();
    if (lien === lienActif) { arreter(); return; }
    arreter();
    lecteur = new Audio(lien.href);
    lienActif = lien;
    lien.classList.add("audio-en-cours");
    lecteur.addEventListener("ended", arreter);
    lecteur.addEventListener("error", function () {
      // Le navigateur ne sait pas lire le fichier : on l'ouvre comme avant.
      arreter();
      window.location.href = lien.href;
    });
    lecteur.play().catch(function () {});
  });

  // Indique aux lecteurs d'écran que ces liens jouent un son.
  function annoter() {
    document.querySelectorAll('a[href$=".m4a"]:not([data-audio])').forEach(function (a) {
      a.setAttribute("data-audio", "");
      if (!a.title) a.title = "Écouter la prononciation";
    });
  }
  if (window.document$) window.document$.subscribe(annoter);
  else document.addEventListener("DOMContentLoaded", annoter);
})();
