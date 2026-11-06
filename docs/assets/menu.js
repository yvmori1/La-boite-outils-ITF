// Insère le menu principal, écrit une seule fois dans assets/menu.html, à la
// place de l'en-tête de menu que porte chaque page (voir hooks/menu_partage.py),
// puis ouvre les sections qui mènent à la page et y place sa table des
// matières, comme le ferait Material. Le menu est chargé une fois, puis
// réutilisé à chaque changement de page.
(function () {
  if (!window.__md_scope) return;
  var menu = null;
  var attente = null;

  function charger() {
    if (menu) return Promise.resolve(menu);
    if (!attente) {
      // « no-cache » : après une publication, ne pas reprendre l'ancien menu
      // gardé par le cache HTTP du navigateur (10 minutes sur GitHub Pages).
      attente = fetch(new URL("assets/menu.html", __md_scope).href, { cache: "no-cache" }).then(function (r) {
        if (!r.ok) throw new Error("menu " + r.status);
        return r.text();
      }).then(function (texte) { menu = texte; return texte; });
      attente.catch(function () { attente = null; });
    }
    return attente;
  }

  function chemin(url) {
    return new URL(url, location.href).pathname.replace(/index\.html$/, "");
  }

  function activer(nav, gabaritToc) {
    var ici = chemin(location.href);
    var liens = nav.querySelectorAll("a.md-nav__link");
    var lien = null;
    for (var i = 0; i < liens.length; i++) {
      if (chemin(liens[i].href) === ici) { lien = liens[i]; break; }
    }
    if (!lien) return null;
    lien.classList.add("md-nav__link--active");
    var item = lien.closest("li.md-nav__item");
    var indexDeSection = !!lien.closest(".md-nav__container");
    for (var p = item; p; p = p.parentElement && p.parentElement.closest("li.md-nav__item")) {
      p.classList.add("md-nav__item--active");
      var bascule = p.querySelector(":scope > input.md-nav__toggle");
      if (bascule) bascule.checked = true;
      var sous = p.querySelector(":scope > nav.md-nav");
      if (sous) sous.setAttribute("aria-expanded", "true");
    }
    if (!indexDeSection && item) {
      var entree = document.createElement("input");
      entree.className = "md-nav__toggle md-toggle";
      entree.type = "checkbox";
      entree.id = "__toc";
      item.insertBefore(entree, lien);
      var toc = gabaritToc && gabaritToc.content.querySelector("nav");
      if (toc) {
        var etiquette = document.createElement("label");
        etiquette.className = "md-nav__link md-nav__link--active";
        etiquette.htmlFor = "__toc";
        etiquette.innerHTML = lien.innerHTML + '<span class="md-nav__icon md-icon"></span>';
        item.insertBefore(etiquette, lien);
        item.appendChild(document.importNode(toc, true));
      }
    }
    return lien;
  }

  function installer() {
    var vide = document.querySelector("nav.md-nav--primary[data-menu-partage]");
    if (!vide) return;
    charger().then(function (html) {
      if (!vide.isConnected) return;
      var boite = document.createElement("div");
      boite.innerHTML = html;
      var nav = boite.querySelector("nav");
      nav.querySelectorAll("a[href]").forEach(function (a) {
        a.setAttribute("href", new URL(a.getAttribute("href"), __md_scope).href);
      });
      var lien = activer(nav, vide.querySelector("template[data-menu-toc]"));
      vide.replaceWith(nav);
      // Sur grand écran, faire voir la page active dans la barre latérale.
      var defile = nav.closest(".md-sidebar__scrollwrap");
      if (lien && defile && defile.offsetParent) {
        var ecart = lien.getBoundingClientRect().top - defile.getBoundingClientRect().top;
        if (ecart > defile.clientHeight) defile.scrollTop += ecart - defile.clientHeight / 2;
      }
    }).catch(function () { /* hors ligne et menu absent : la page reste lisible */ });
  }

  if (window.document$) window.document$.subscribe(installer);
  else document.addEventListener("DOMContentLoaded", installer);
})();
