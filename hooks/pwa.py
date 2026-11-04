"""Rend le site installable comme application (iPhone, iPad, Android).

- Ajoute à chaque page le manifeste, l'icône d'écran d'accueil et les balises
  Apple (ouverture plein écran, titre sous l'icône).
- Après la construction, écrit pwa-fichiers.json : la liste de tous les
  fichiers du site avec leur empreinte et leur taille, que le service worker
  (docs/sw.js) met en cache. L'empreinte globale de cette liste devient la
  VERSION de sw.js : chaque modification du site fait ainsi installer une
  nouvelle version, qui ne retélécharge que les fichiers modifiés.

Rien de tout cela dans la version hors-ligne.zip (HORS_LIGNE=true), lue en
file:// où les service workers n'existent pas.
"""

import hashlib
import json
import os
import pathlib
import urllib.parse

# Jamais mis en cache par l'application.
EXCLUS = {"CNAME", "sw.js", "pwa-fichiers.json", "hors-ligne.zip", "sitemap.xml.gz", ".nojekyll"}

BALISES = """
<link rel="manifest" href="{racine}manifest.webmanifest">
<link rel="apple-touch-icon" href="{racine}assets/icones/apple-touch-icon.png">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Outils ITF">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
"""


def _actif():
    return os.environ.get("HORS_LIGNE", "").lower() not in ("true", "1", "yes", "on")


def on_post_page(output, page, config, **kwargs):
    if not _actif():
        return output
    racine = urllib.parse.urlparse(config["site_url"] or "/").path or "/"
    if not racine.endswith("/"):
        racine += "/"
    return output.replace("</head>", BALISES.format(racine=racine) + "</head>", 1)


def on_post_build(config, **kwargs):
    if not _actif():
        return
    site = pathlib.Path(config["site_dir"])
    fichiers = {}
    for chemin in sorted(site.rglob("*")):
        if not chemin.is_file():
            continue
        relatif = chemin.relative_to(site).as_posix()
        if relatif in EXCLUS or relatif.endswith(".map"):
            continue
        contenu = chemin.read_bytes()
        # Techniques/Ap-Chagi/index.html est servi à l'adresse Techniques/Ap-Chagi/
        cle = relatif[:-len("index.html")] if relatif == "index.html" or relatif.endswith("/index.html") else relatif
        fichiers[cle] = [hashlib.sha1(contenu).hexdigest()[:12], len(contenu)]
    version = hashlib.sha1(json.dumps(fichiers, sort_keys=True).encode()).hexdigest()[:12]
    (site / "pwa-fichiers.json").write_text(
        json.dumps({"version": version, "fichiers": fichiers}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")
    sw = site / "sw.js"
    sw.write_text(sw.read_text(encoding="utf-8").replace("__VERSION__", version), encoding="utf-8")
