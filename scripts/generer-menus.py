#!/usr/bin/env python3
"""Écrit le menu (.pages) des sections de fiches d'après leur README.

  python3 scripts/generer-menus.py           # dit si les menus sont à jour
  python3 scripts/generer-menus.py --write   # écrit les .pages

Le menu reprend l'ordre du sommaire de la section : chaque titre « ## » du
README devient un groupe du menu, chaque titre « ### » un sous-groupe, et les
fiches y paraissent dans l'ordre où le README les cite. Une fiche citée deux
fois ne paraît qu'à sa première place. Les fiches du groupe « Fiches
transversales » sont placées en tête, hors groupe ; le groupe « Voir aussi »
est ignoré. Une fiche que le README ne cite pas paraît à la fin (« ... »).

Le sommaire reste ainsi la seule liste tenue à la main (ou par
generer-index-techniques.py pour Techniques/) : le menu le suit.
"""

import argparse
import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parents[1]
SECTIONS = ("chagi", "makgi", "jirugi")
EN_TETE = "Fiches transversales"
IGNORES = ("Voir aussi",)
LIEN = re.compile(r"\]\(([^)/#\s]+\.md)(?:#[^)]*)?\)")


def libelle(titre):
    """« ## 1. Coups de pied avant (*Ap*) » -> « Coups de pied avant (Ap) »."""
    titre = re.sub(r"^\d+(\.\d+)*\.?\s+", "", titre.strip())
    titre = re.sub(r"[*_`]", "", titre)
    return titre.strip()


def citer(chaine):
    """Valeur YAML sûre : entre guillemets si besoin."""
    if re.search(r"[:#'\"«»\[\]{},&*!|>%@`]", chaine) or chaine != chaine.strip():
        return '"' + chaine.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return chaine


def arbre(dossier):
    """Lit le README : liste de (groupe, sous-groupe, fichier)."""
    presents = {p.name for p in dossier.glob("*.md")}
    vus, entrees = {"README.md"}, []
    groupe = sous_groupe = None
    for ligne in (dossier / "README.md").read_text(encoding="utf-8").splitlines():
        if ligne.startswith("## "):
            groupe, sous_groupe = libelle(ligne[3:]), None
            continue
        if ligne.startswith("### "):
            sous_groupe = libelle(ligne[4:])
            continue
        if groupe in IGNORES:
            continue
        for fichier in LIEN.findall(ligne):
            if fichier in presents and fichier not in vus:
                vus.add(fichier)
                entrees.append((groupe, sous_groupe, fichier))
    return entrees


def produire(dossier):
    lignes = [
        "# Fichier produit par scripts/generer-menus.py : ne pas modifier à la",
        "# main. L'ordre suit le sommaire (README.md) de la section.",
        "nav:",
        "  - README.md",
    ]
    entrees = arbre(dossier)
    groupe_ouvert = sous_ouvert = object()
    for groupe, sous_groupe, fichier in entrees:
        if groupe in (None, EN_TETE):
            lignes.append(f"  - {fichier}")
            groupe_ouvert = sous_ouvert = object()
            continue
        if groupe != groupe_ouvert:
            lignes.append(f"  - {citer(groupe)}:")
            groupe_ouvert, sous_ouvert = groupe, None
        if sous_groupe is None:
            lignes.append(f"    - {fichier}")
            continue
        if sous_groupe != sous_ouvert:
            lignes.append(f"    - {citer(sous_groupe)}:")
            sous_ouvert = sous_groupe
        lignes.append(f"      - {fichier}")
    lignes.append("  - ...")
    return "\n".join(lignes) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--write", action="store_true", help="écrit les fichiers")
    args = p.parse_args()
    differents = []
    for nom in SECTIONS:
        cible = RACINE / nom / ".pages"
        texte = produire(RACINE / nom)
        actuel = cible.read_text(encoding="utf-8") if cible.exists() else ""
        if texte != actuel:
            differents.append(nom)
            if args.write:
                cible.write_text(texte, encoding="utf-8")
    if not differents:
        print("menus déjà à jour")
    elif args.write:
        print("menus écrits : " + ", ".join(differents))
    else:
        print("le menu produit diffère du fichier : " + ", ".join(differents))
    return 0


if __name__ == "__main__":
    sys.exit(main())
