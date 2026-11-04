"""Écrit le menu principal une seule fois, dans assets/menu.html.

Material répète le menu complet dans chaque page : avec plus de 600 entrées,
c'est environ 235 Ko par page et 165 Mo pour le site, presque tout le poids
de l'application iPhone et iPad. overrides/partials/nav.html ne laisse plus
dans chaque page que l'en-tête du menu et la table des matières de la page,
et assets/menu.js y insère le menu partagé, puis marque la page active.

La version hors-ligne.zip (HORS_LIGNE=true), lue en file:// où le menu ne
peut pas être chargé à part, garde le menu complet dans chaque page.
"""

import os
import pathlib

from mkdocs.commands.build import get_context

_nav = None

GABARIT = (
    '{% import "partials/language.html" as lang with context %}'
    "{% set features = config.theme.features or [] %}"
    '{% include "partials/nav-complet.html" %}'
)


def _actif():
    return os.environ.get("HORS_LIGNE", "").lower() not in ("true", "1", "yes", "on")


def on_config(config, **kwargs):
    config["extra"]["menu_partage"] = _actif()
    return config


def on_nav(nav, config, files, **kwargs):
    global _nav
    _nav = (nav, files)
    return nav


def on_post_build(config, **kwargs):
    if not _actif() or _nav is None:
        return
    nav, files = _nav
    # Aucune page active ; liens relatifs à la racine du site (« ./tul/ »),
    # que assets/menu.js résout.
    contexte = get_context(nav, files, config, page=None, base_url=".")
    html = config["theme"].get_env().from_string(GABARIT).render(contexte)
    # L'indentation des gabarits fait près de la moitié du poids.
    lignes = (ligne.strip() for ligne in html.splitlines())
    sortie = pathlib.Path(config["site_dir"]) / "assets" / "menu.html"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text("\n".join(l for l in lignes if l) + "\n", encoding="utf-8")
