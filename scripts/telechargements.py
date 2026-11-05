#!/usr/bin/env python3
"""Nombre de téléchargements de hors-ligne.zip.

Chaque publication du site crée une Release GitHub avec hors-ligne.zip en
pièce jointe (voir .github/workflows/deploy-site.yml). GitHub compte les
téléchargements de chaque pièce jointe ; ce script les additionne.

    python3 scripts/telechargements.py           # total et détail par Release
    python3 scripts/telechargements.py --total   # total seulement

Sans jeton, l'API GitHub accepte 60 requêtes par heure ; GITHUB_TOKEN ou
GH_TOKEN, s'il est défini, est utilisé.

Les clics sur les liens du site (et les visites) sont aussi comptés par
GoatCounter : https://hosinsul.goatcounter.com
"""
import json
import os
import sys
import urllib.request

DEPOT = "yvmori1/La-boite-outils-ITF"
FICHIER = "hors-ligne.zip"


def releases():
    page = 1
    jeton = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    while True:
        url = f"https://api.github.com/repos/{DEPOT}/releases?per_page=100&page={page}"
        requete = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        if jeton:
            requete.add_header("Authorization", f"Bearer {jeton}")
        with urllib.request.urlopen(requete) as reponse:
            lot = json.load(reponse)
        if not lot:
            return
        yield from lot
        page += 1


def main():
    total = 0
    lignes = []
    for release in releases():
        for piece in release.get("assets", []):
            if piece["name"] == FICHIER:
                total += piece["download_count"]
                lignes.append((release["published_at"] or "", release["tag_name"], piece["download_count"]))
    if "--total" not in sys.argv:
        for date, etiquette, nombre in sorted(lignes):
            print(f"{date[:10]}  {etiquette:<40} {nombre:>6}")
        print()
    print(f"Total des téléchargements de {FICHIER} : {total}")


if __name__ == "__main__":
    main()
