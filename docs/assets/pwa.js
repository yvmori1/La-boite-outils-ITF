// Application installable : enregistre le service worker (sw.js) et, sur
// demande ou dans l'application ouverte depuis l'écran d'accueil, télécharge
// le site entier sur l'appareil pour s'en servir sans connexion.
//
// Le téléchargement reprend là où il s'était arrêté (application fermée,
// réseau coupé) et, après une mise à jour du site, ne récupère que les
// fichiers modifiés. Rien ne se passe dans la copie hors-ligne.zip
// (ouverte en file://) ni sans prise en charge des service workers.
(function () {
  var lien = document.querySelector('link[rel="manifest"]');
  if (!lien || !("serviceWorker" in navigator) || !window.caches || !/^https?:$/.test(location.protocol)) return;

  var BASE = new URL("./", lien.href).href;
  var CACHE_SITE = "itf-site";
  var CLE_MODE = "itf-hors-ligne";
  var enCours = null;
  var etat = { faits: 0, total: 0, octets: 0, erreur: "" };

  function lireMode() { try { return localStorage.getItem(CLE_MODE) === "complet"; } catch (e) { return false; } }
  function ecrireMode() { try { localStorage.setItem(CLE_MODE, "complet"); } catch (e) { /* sans stockage */ } }
  function installee() {
    return navigator.standalone === true ||
      (window.matchMedia && window.matchMedia("(display-mode: standalone)").matches);
  }

  function cheminDe(url) {
    var c = url.slice(BASE.length).replace(/[?#].*$/, "");
    try { c = decodeURIComponent(c); } catch (e) { /* tel quel */ }
    return c.replace(/(^|\/)index\.html$/, "$1");
  }

  function mo(octets) { return (octets / 1048576).toLocaleString("fr-FR", { maximumFractionDigits: 0 }) + " Mo"; }

  // --- affichage -------------------------------------------------------
  var avis = null;
  function montrerAvis(texte, duree) {
    if (!avis) {
      avis = document.createElement("div");
      avis.className = "pwa-avis";
      avis.setAttribute("role", "status");
      document.body.appendChild(avis);
    }
    avis.textContent = texte;
    avis.hidden = false;
    clearTimeout(avis._minuterie);
    if (duree) avis._minuterie = setTimeout(function () { avis.hidden = true; }, duree);
  }

  function rafraichirPanneau() {
    var panneau = document.getElementById("pwa-etat");
    if (!panneau) return;
    var texte, bouton = null;
    if (enCours) {
      texte = "Téléchargement en cours : " + etat.faits + " fichiers sur " + etat.total + "…";
    } else if (etat.erreur) {
      texte = etat.erreur;
      bouton = "Réessayer";
    } else if (etat.total && etat.faits >= etat.total) {
      texte = "✓ Le site entier est enregistré sur cet appareil (" + mo(etat.octets) + ") et fonctionne sans connexion.";
    } else {
      texte = "Le site n'est pas encore enregistré en entier sur cet appareil" +
        (etat.octets ? " (environ " + mo(etat.octets) + " d'espace)." : ".");
      bouton = "Enregistrer tout le site sur cet appareil";
    }
    panneau.innerHTML = "";
    var p = document.createElement("p");
    p.textContent = texte;
    panneau.appendChild(p);
    if (bouton) {
      var b = document.createElement("button");
      b.className = "md-button md-button--primary";
      b.textContent = bouton;
      b.addEventListener("click", function () { ecrireMode(); completer(true); });
      panneau.appendChild(b);
    }
  }

  // --- téléchargement du site entier -------------------------------------
  function liste() {
    return caches.open("itf-meta").then(function (meta) { return meta.match(BASE + "pwa-liste-active"); })
      .then(function (rep) { return rep ? rep.json() : null; });
  }

  function manquants(fichiers) {
    return caches.open(CACHE_SITE).then(function (cache) { return cache.keys(); }).then(function (cles) {
      var presents = {};
      cles.forEach(function (r) { presents[cheminDe(r.url)] = true; });
      return Object.keys(fichiers).filter(function (c) { return !presents[c]; });
    });
  }

  function completer(demande) {
    if (enCours) return enCours;
    etat.erreur = "";
    enCours = navigator.serviceWorker.ready.then(function () {
      // Le service worker met chaque fichier en cache en le servant : il doit
      // donc contrôler cette page (première visite : juste après l'activation).
      if (navigator.serviceWorker.controller) return;
      return new Promise(function (ok) {
        navigator.serviceWorker.addEventListener("controllerchange", ok, { once: true });
        setTimeout(ok, 3000);
      });
    }).then(liste).then(function (l) {
      if (!l || !navigator.serviceWorker.controller) throw new Error("Le site n'est pas encore prêt, réessayez dans un instant.");
      var fichiers = l.fichiers;
      etat.octets = Object.keys(fichiers).reduce(function (s, c) { return s + fichiers[c][1]; }, 0);
      etat.total = Object.keys(fichiers).length;
      return manquants(fichiers).then(function (aFaire) {
        etat.faits = etat.total - aFaire.length;
        if (!aFaire.length) return;
        if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(function () {});
        var visible = demande || aFaire.length > 20;
        var i = 0, echecs = 0;
        function suivant() {
          if (i >= aFaire.length) return Promise.resolve();
          var chemin = aFaire[i++];
          return fetch(new URL(encodeURI(chemin), BASE).href, { cache: "no-cache" }).then(function (rep) {
            if (!rep.ok) { echecs++; return; }
            return rep.arrayBuffer().then(function () { etat.faits++; });
          }, function () { echecs++; }).then(function () {
            if (visible && etat.faits % 10 === 0) {
              montrerAvis("Enregistrement hors ligne : " + etat.faits + " / " + etat.total);
              rafraichirPanneau();
            }
            if (echecs > 20 && !navigator.onLine) throw new Error("Connexion perdue : le téléchargement reprendra plus tard.");
            return suivant();
          });
        }
        var files = [];
        for (var n = 0; n < 6; n++) files.push(suivant());
        return Promise.all(files).then(function () {
          if (echecs) throw new Error(echecs + " fichiers n'ont pas pu être téléchargés : réessayez plus tard.");
          if (visible) montrerAvis("✓ Site entier enregistré : il fonctionne sans connexion.", 5000);
        });
      });
    }).catch(function (erreur) {
      etat.erreur = erreur.message || String(erreur);
      if (demande) montrerAvis(etat.erreur, 6000);
    }).then(function () {
      enCours = null;
      rafraichirPanneau();
    });
    rafraichirPanneau();
    return enCours;
  }

  // --- démarrage -------------------------------------------------------
  var dejaControlee = !!navigator.serviceWorker.controller;
  navigator.serviceWorker.register(BASE + "sw.js", { scope: BASE }).then(function (inscription) {
    // L'application ouverte depuis l'écran d'accueil reprend souvent sans
    // recharger la page : on vérifie alors les mises à jour, au plus une fois
    // par heure.
    var derniere = Date.now();
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "visible" && Date.now() - derniere > 3600000) {
        derniere = Date.now();
        inscription.update().catch(function () {});
      }
    });
  }).catch(function () {});

  navigator.serviceWorker.addEventListener("controllerchange", function () {
    // Nouvelle version du site installée pendant la lecture.
    if (dejaControlee) {
      montrerAvis("Le site a été mis à jour.", 4000);
      if (lireMode() || installee()) setTimeout(completer, 1000);
    }
    dejaControlee = true;
  });

  if (installee() || lireMode()) {
    ecrireMode();
    completer(false);
  } else {
    // Sans téléchargement complet, on calcule seulement l'état à afficher.
    navigator.serviceWorker.ready.then(liste).then(function (l) {
      if (!l) return;
      etat.total = Object.keys(l.fichiers).length;
      etat.octets = Object.keys(l.fichiers).reduce(function (s, c) { return s + l.fichiers[c][1]; }, 0);
      return manquants(l.fichiers).then(function (m) { etat.faits = etat.total - m.length; });
    }).catch(function () {}).then(rafraichirPanneau);
  }

  if (window.document$) window.document$.subscribe(rafraichirPanneau);
  else document.addEventListener("DOMContentLoaded", rafraichirPanneau);
})();
