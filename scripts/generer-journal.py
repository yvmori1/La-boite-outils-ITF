#!/usr/bin/env python3
"""Écrit le journal des modifications d'après les PR fusionnées sur GitHub.

  python3 scripts/generer-journal.py           # dit si le journal est à jour
  python3 scripts/generer-journal.py --write   # écrit les deux fichiers

Le journal liste toutes les demandes de fusion (pull requests) fusionnées,
de la plus récente à la plus ancienne, regroupées par jour de fusion (heure
du Québec). Il est écrit à deux endroits, au même contenu :

* CHANGELOG.md, à la racine, pour les contributeurs ;
* docs/a-propos/journal.md, la page « Journal des modifications » du site.

La liste vient de l'API REST de GitHub : il faut donc le réseau. Un jeton
(GH_TOKEN ou GITHUB_TOKEN) est facultatif, il évite seulement la limite de
60 requêtes par heure. Le déploiement (.github/workflows/deploy-site.yml)
lance ce script à chaque publication et remet CHANGELOG.md à jour dans main :
il n'y a rien à faire à la main.
"""

import argparse
import datetime
import json
import os
import re
import sys
import urllib.request
import zoneinfo

from chemins import DOCS, RACINE

DEPOT = os.environ.get("GITHUB_REPOSITORY", "yvmori1/La-boite-outils-ITF")
FUSEAU = zoneinfo.ZoneInfo("America/Toronto")
CIBLES = (RACINE / "CHANGELOG.md", DOCS / "a-propos" / "journal.md")

EN_TETE = """\
# Journal des modifications

Toutes les modifications fusionnées dans le recueil, de la plus récente à la
plus ancienne. Chaque ligne renvoie à sa demande de fusion (*pull request*)
sur GitHub, qui en donne le détail.

<!-- Fichier généré par scripts/generer-journal.py à chaque publication du
site : ne pas le modifier à la main. -->
"""


def demandes_fusionnees():
    """Les PR fusionnées : liste de (numéro, date de fusion, titre, adresse)."""
    jeton = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    entetes = {"Accept": "application/vnd.github+json",
               "User-Agent": "generer-journal"}
    if jeton:
        entetes["Authorization"] = f"Bearer {jeton}"
    resultat, page = [], 1
    while True:
        adresse = (f"https://api.github.com/repos/{DEPOT}/pulls"
                   f"?state=closed&per_page=100&page={page}")
        with urllib.request.urlopen(
                urllib.request.Request(adresse, headers=entetes),
                timeout=30) as reponse:
            lot = json.load(reponse)
        for pr in lot:
            if pr.get("merged_at"):
                fusion = datetime.datetime.fromisoformat(
                    pr["merged_at"].replace("Z", "+00:00"))
                resultat.append((pr["number"], fusion, pr["title"],
                                 pr["html_url"]))
        if len(lot) < 100:
            break
        page += 1
    resultat.sort(key=lambda pr: (pr[1], pr[0]), reverse=True)
    return resultat


def echapper(titre):
    """Titre de PR affiché tel quel, sans être lu comme du Markdown."""
    return re.sub(r"([\\`*_\[\]<>|])", r"\\\1", titre.strip())


def journal(demandes):
    lignes = [EN_TETE.rstrip()]
    jour_courant = None
    for numero, fusion, titre, adresse in demandes:
        jour = fusion.astimezone(FUSEAU).date().isoformat()
        if jour != jour_courant:
            lignes.append(f"\n## {jour}\n")
            jour_courant = jour
        lignes.append(f"* [#{numero}]({adresse}) {echapper(titre)}")
    return "\n".join(lignes) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true",
                        help="écrire les fichiers (sinon : essai à blanc)")
    args = parser.parse_args()

    try:
        demandes = demandes_fusionnees()
    except OSError as erreur:
        print(f"GitHub injoignable : {erreur}", file=sys.stderr)
        return 1
    texte = journal(demandes)

    a_ecrire = [c for c in CIBLES
                if not c.exists() or c.read_text(encoding="utf-8") != texte]
    for cible in a_ecrire:
        nom = cible.relative_to(RACINE)
        if args.write:
            cible.write_text(texte, encoding="utf-8")
            print(f"écrit : {nom} ({len(demandes)} PR)")
        else:
            print(f"à mettre à jour : {nom}")
    if not a_ecrire:
        print(f"journal à jour ({len(demandes)} PR)")
    return 1 if a_ecrire and not args.write else 0


if __name__ == "__main__":
    sys.exit(main())
