"""Charge includes/infobulles.md comme glossaire de l'extension « abbr ».

Survoler ou toucher « Joomuk », partout sur le site, affiche « Poing (주먹) ».
Le fichier est produit par scripts/generer-infobulles.py à partir du glossaire
coréen-français. Le charger une fois ici, plutôt que de l'ajouter à la fin de
chaque page, garde la construction du site rapide.
"""

import os
import re

DEFINITION = re.compile(r"^\*\[(.+?)\]:\s*(.*)$")


def on_config(config, **kwargs):
    chemin = os.path.join(os.path.dirname(config["config_file_path"]), "includes", "infobulles.md")
    if not os.path.exists(chemin):
        return config
    glossaire = {}
    with open(chemin, encoding="utf-8") as f:
        for ligne in f:
            m = DEFINITION.match(ligne.strip())
            if m:
                glossaire[m.group(1)] = m.group(2)
    if "abbr" not in config["markdown_extensions"]:
        config["markdown_extensions"].append("abbr")
    config["mdx_configs"].setdefault("abbr", {})["glossary"] = glossaire
    return config
