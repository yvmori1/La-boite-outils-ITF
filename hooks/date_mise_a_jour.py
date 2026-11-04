"""Affiche la date de la dernière mise à jour sur la page d'accueil du site.

La date et l'heure (UTC) sont celles du dernier commit (celui qui déclenche la publication).
Elle n'est ajoutée qu'au site construit : le README.md du dépôt reste inchangé.
"""

import datetime
import subprocess

_date = None


def on_config(config):
    global _date
    try:
        sortie = subprocess.run(
            ["git", "log", "-1", "--format=%ct"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        _date = datetime.datetime.fromtimestamp(int(sortie), datetime.timezone.utc)
    except (OSError, subprocess.CalledProcessError, ValueError):
        _date = datetime.datetime.now(datetime.timezone.utc)
    return config


def on_page_markdown(markdown, page, config, files):
    if not page.is_homepage or _date is None:
        return markdown
    ligne = f"*Dernière mise à jour : {_date:%Y-%m-%d %H:%M:%S} UTC*"
    lignes = markdown.split("\n")
    # Juste sous le titre principal, s'il y en a un.
    for i, texte in enumerate(lignes):
        if texte.startswith("# "):
            lignes[i + 1:i + 1] = ["", ligne]
            return "\n".join(lignes)
    return ligne + "\n\n" + markdown
