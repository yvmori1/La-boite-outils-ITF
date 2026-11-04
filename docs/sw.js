// Service worker de l'application installable (iPhone, iPad, Android, ordinateur).
//
// Toutes les pages, images, sons et l'index de recherche sont servis depuis
// le cache de l'appareil dès qu'ils y sont, et le réseau n'est consulté que
// pour ce qui manque. La liste des fichiers du site, avec l'empreinte de
// chacun, est publiée à chaque construction dans pwa-fichiers.json par
// hooks/pwa.py, qui écrit aussi la VERSION ci-dessous : un site modifié donne
// donc un sw.js modifié, que le navigateur installe de lui-même. À
// l'installation, seuls les fichiers dont l'empreinte a changé sont retirés du
// cache ; ils sont téléchargés de nouveau à la demande, ou tous d'un coup par
// assets/pwa.js quand le site entier est enregistré sur l'appareil.
const VERSION = "__VERSION__";
const CACHE_SITE = "itf-site";
const CACHE_EXTERNE = "itf-externe";
const CACHE_META = "itf-meta";
const BASE = new URL("./", self.location).href;
// Clé absolue : la page (assets/pwa.js) lit la même entrée.
const CLE_LISTE = BASE + "pwa-liste-active";
// Ressources tierces gardées en cache après le premier usage : MathJax et
// les polices de Material.
const HOTES_EXTERNES = ["unpkg.com", "fonts.googleapis.com", "fonts.gstatic.com"];
// Jamais mis en cache : ce fichier, la liste et l'archive zip (90 Mo).
const NON_CACHES = new Set(["sw.js", "pwa-fichiers.json", "hors-ligne.zip"]);

let liste = null; // { version, fichiers: { chemin: [empreinte, taille] } }

async function listeActive() {
  if (liste) return liste;
  const meta = await caches.open(CACHE_META);
  const rep = await meta.match(CLE_LISTE);
  liste = rep ? await rep.json() : { version: "", fichiers: {} };
  return liste;
}

// Chemin relatif à la racine du site, décodé, sans « index.html » final :
// « Techniques/Ap-Chagi/ » sert de clé à Techniques/Ap-Chagi/index.html.
function cheminDe(url) {
  let chemin = url.href.slice(BASE.length).replace(/[?#].*$/, "");
  try { chemin = decodeURIComponent(chemin); } catch (e) { /* laissé tel quel */ }
  return chemin.replace(/(^|\/)index\.html$/, "$1");
}

function cleDe(chemin) {
  return BASE + encodeURI(chemin);
}

self.addEventListener("install", (evenement) => {
  evenement.waitUntil((async () => {
    const rep = await fetch(BASE + "pwa-fichiers.json", { cache: "no-store" });
    if (!rep.ok) throw new Error("pwa-fichiers.json : " + rep.status);
    const nouvelle = await rep.json();
    const ancienne = await listeActive();
    const cache = await caches.open(CACHE_SITE);
    // Retire ce qui a changé ou disparu depuis la version précédente.
    for (const requete of await cache.keys()) {
      const chemin = cheminDe(new URL(requete.url));
      const neuf = nouvelle.fichiers[chemin];
      const vieux = ancienne.fichiers[chemin];
      if (!neuf || !vieux || vieux[0] !== neuf[0]) await cache.delete(requete);
    }
    // Garde de quoi ouvrir l'accueil et naviguer hors ligne dès l'installation.
    const coquille = Object.keys(nouvelle.fichiers).filter((c) =>
      c === "" || c === "404.html" || c === "sitemap.xml" ||
      c === "manifest.webmanifest" || c.startsWith("assets/"));
    const presents = new Set((await cache.keys()).map((r) => cheminDe(new URL(r.url))));
    await Promise.all(coquille.filter((c) => !presents.has(c)).map(async (c) => {
      const r = await fetch(cleDe(c), { cache: "no-cache" });
      if (r.ok && !r.redirected) await cache.put(cleDe(c), r);
    }));
    const meta = await caches.open(CACHE_META);
    await meta.put(CLE_LISTE, new Response(JSON.stringify(nouvelle),
      { headers: { "Content-Type": "application/json" } }));
    liste = nouvelle;
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", (evenement) => {
  evenement.waitUntil((async () => {
    const gardes = [CACHE_SITE, CACHE_EXTERNE, CACHE_META];
    for (const nom of await caches.keys()) {
      if (!gardes.includes(nom)) await caches.delete(nom);
    }
    await self.clients.claim();
  })());
});

self.addEventListener("message", (evenement) => {
  if (evenement.data === "version" && evenement.ports[0]) {
    evenement.ports[0].postMessage(VERSION);
  }
});

self.addEventListener("fetch", (evenement) => {
  const requete = evenement.request;
  if (requete.method !== "GET") return;
  const url = new URL(requete.url);
  if (url.origin === self.location.origin) {
    if (!url.href.startsWith(BASE)) return;
    const chemin = cheminDe(url);
    if (NON_CACHES.has(chemin) || chemin.endsWith(".map")) return;
    evenement.respondWith(local(requete, chemin));
  } else if (HOTES_EXTERNES.includes(url.hostname)) {
    evenement.respondWith(externe(requete));
  }
});

async function local(requete, chemin) {
  const { fichiers } = await listeActive();
  const connu = chemin in fichiers;
  // « /Techniques/Ap-Chagi » sans barre finale : comme GitHub Pages, renvoyer
  // vers la page, même sans réseau.
  if (!connu && (chemin + "/") in fichiers && requete.mode === "navigate") {
    return Response.redirect(cleDe(chemin + "/"), 301);
  }
  const cache = await caches.open(CACHE_SITE);
  let rep = connu ? await cache.match(cleDe(chemin)) : undefined;
  if (!rep) {
    try {
      // Requête complète, sans en-tête Range, pour garder le fichier entier.
      rep = await fetch(connu ? cleDe(chemin) : requete);
    } catch (erreur) {
      return horsLigne(requete);
    }
    if (rep.redirected && requete.mode === "navigate") return Response.redirect(rep.url, 302);
    if (!connu || !rep.ok || rep.redirected) return rep;
    await cache.put(cleDe(chemin), rep.clone());
  }
  // Safari lit les sons par morceaux (Range) et refuse une réponse entière.
  if (requete.headers.has("range")) return plage(requete, rep);
  return rep;
}

async function plage(requete, rep) {
  const contenu = await rep.arrayBuffer();
  const taille = contenu.byteLength;
  const m = /bytes=(\d*)-(\d*)/.exec(requete.headers.get("range") || "");
  let debut = 0;
  let fin = taille - 1;
  if (m && m[1]) {
    debut = Number(m[1]);
    if (m[2]) fin = Math.min(Number(m[2]), taille - 1);
  } else if (m && m[2]) {
    debut = Math.max(taille - Number(m[2]), 0);
  }
  if (debut >= taille || debut > fin) {
    return new Response(null, { status: 416, headers: { "Content-Range": `bytes */${taille}` } });
  }
  return new Response(contenu.slice(debut, fin + 1), {
    status: 206,
    headers: {
      "Content-Type": rep.headers.get("Content-Type") || "application/octet-stream",
      "Content-Range": `bytes ${debut}-${fin}/${taille}`,
      "Content-Length": String(fin - debut + 1),
      "Accept-Ranges": "bytes",
    },
  });
}

async function externe(requete) {
  const cache = await caches.open(CACHE_EXTERNE);
  const garde = await cache.match(requete);
  if (garde) return garde;
  try {
    const rep = await fetch(requete);
    if (rep.ok || rep.type === "opaque") await cache.put(requete, rep.clone());
    return rep;
  } catch (erreur) {
    return Response.error();
  }
}

function horsLigne(requete) {
  if (requete.mode !== "navigate") return Response.error();
  const page = `<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hors ligne</title><style>
body{font-family:-apple-system,system-ui,sans-serif;margin:0;padding:2rem 1rem;
background:#fff;color:#222;line-height:1.5}main{max-width:32rem;margin:auto}
a{color:#d32f2f}@media(prefers-color-scheme:dark){body{background:#1e1e1e;color:#eee}}
</style></head><body><main><h1>Page non enregistrée</h1>
<p>Cette page n'est pas encore sur l'appareil et la connexion est coupée.</p>
<p>Pour tout avoir sans connexion, ouvrez la page
<a href="${BASE}Application/">Application iPhone et iPad</a> une fois connecté
et enregistrez le site entier.</p>
<p><a href="${BASE}">Retour à l'accueil</a></p></main></body></html>`;
  return new Response(page, { status: 503, headers: { "Content-Type": "text/html; charset=utf-8" } });
}
