// Statistiques de fréquentation avec GoatCounter (goatcounter.com) : sans
// témoins (cookies) ni données personnelles, donc sans bannière de
// consentement. Tableau de bord : https://hosinsul.goatcounter.com
//
// Compte :
//   - chaque page vue, y compris les changements de page sans rechargement
//     (navigation.instant de Material) ;
//   - les clics sur un lien vers hors-ligne.zip (événement
//     « telechargement-hors-ligne-zip ») ;
//   - la première ouverture de l'application installée sur l'écran
//     d'accueil (événement « installation-app »). Safari sur iPhone et iPad
//     ne signale pas l'installation elle-même : la première ouverture en
//     plein écran en tient lieu.
//
// Rien n'est compté hors du domaine public (essais en local, copie
// hors-ligne.zip ouverte en file://) ni sans connexion : l'usage de
// l'application hors ligne n'apparaît donc pas dans les statistiques.
(function () {
  var CODE = "hosinsul";
  if (location.protocol !== "https:" || location.hostname !== "outils.hosinsul.ca") return;

  var enAttente = [];
  // Adresse donnée ici et pas seulement sur la balise <script> : la
  // navigation sans rechargement de Material remplace l'en-tête de la page,
  // et count.js ne retrouverait plus la balise.
  var ADRESSE = "https://" + CODE + ".goatcounter.com/count";
  window.goatcounter = { no_onload: true, endpoint: ADRESSE };

  function compter(donnees) {
    if (window.goatcounter && typeof window.goatcounter.count === "function") {
      window.goatcounter.count(donnees);
    } else {
      enAttente.push(donnees);
    }
  }

  var script = document.createElement("script");
  script.async = true;
  script.src = "https://gc.zgo.at/count.js";
  script.setAttribute("data-goatcounter", ADRESSE);
  script.onload = function () {
    var file = enAttente;
    enAttente = [];
    file.forEach(compter);
  };
  document.head.appendChild(script);

  // Pages vues.
  var dernierePage = null;
  function pageVue() {
    var chemin = location.pathname + location.search;
    if (chemin === dernierePage) return;
    // Après un changement de page sans rechargement, document.referrer reste
    // le site d'origine de la visite : on donne la page précédente, que
    // GoatCounter ignore comme provenance interne.
    var provenance = dernierePage === null ? document.referrer : location.origin + dernierePage;
    dernierePage = chemin;
    compter({ path: chemin, title: document.title, referrer: provenance });
  }
  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(pageVue);
  } else {
    pageVue();
  }

  // Téléchargements de hors-ligne.zip.
  document.addEventListener("click", function (evenement) {
    var lien = evenement.target.closest && evenement.target.closest("a[href]");
    if (lien && /hors-ligne\.zip(?:$|[?#])/.test(lien.href)) {
      compter({ path: "telechargement-hors-ligne-zip", title: "Téléchargement de hors-ligne.zip", event: true });
    }
  }, true);

  // Première ouverture de l'application installée.
  var CLE_INSTALLATION = "itf-installation-comptee";
  var installee = navigator.standalone === true ||
    (window.matchMedia && window.matchMedia("(display-mode: standalone)").matches);
  if (installee && navigator.onLine !== false) {
    var dejaComptee = true;
    try { dejaComptee = localStorage.getItem(CLE_INSTALLATION) === "oui"; } catch (e) { /* sans stockage */ }
    if (!dejaComptee) {
      compter({ path: "installation-app", title: "Première ouverture de l'application installée", event: true });
      try { localStorage.setItem(CLE_INSTALLATION, "oui"); } catch (e) { /* sans stockage */ }
    }
  }
})();
