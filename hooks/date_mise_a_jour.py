"""Affiche la date de la dernière mise à jour sur la page d'accueil du site.

La date est celle du dernier commit (celui qui déclenche la publication).
Elle n'est ajoutée qu'au site construit : le README.md du dépôt reste inchangé.
"""

import datetime
import subprocess

MOIS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]

_date = None


def on_config(config):
    global _date
    try:
        sortie = subprocess.run(
            ["git", "log", "-1", "--format=%cs"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        _date = datetime.date.fromisoformat(sortie)
    except (OSError, subprocess.CalledProcessError, ValueError):
        _date = datetime.date.today()
    return config


def on_page_markdown(markdown, page, config, files):
    if not page.is_homepage or _date is None:
        return markdown
    jour = "1er" if _date.day == 1 else str(_date.day)
    ligne = f"*Dernière mise à jour : {jour} {MOIS[_date.month - 1]} {_date.year}*"
    lignes = markdown.split("\n")
    # Juste sous le titre principal, s'il y en a un.
    for i, texte in enumerate(lignes):
        if texte.startswith("# "):
            lignes[i + 1:i + 1] = ["", ligne]
            return "\n".join(lignes)
    return ligne + "\n\n" + markdown
