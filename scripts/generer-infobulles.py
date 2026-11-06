#!/usr/bin/env python3
"""Produit includes/infobulles.md : la traduction des termes coréens au survol.

Lit les tableaux du glossaire coréen-français (Theorie/glossaire/) et écrit une
définition d'abréviation Markdown par terme :

  *[Joomuk]: Poing (주먹)

hooks/infobulles.py charge ce fichier dans l'extension abbr de MkDocs :
partout sur le site, survoler ou toucher « Joomuk » affiche
sa traduction. Le fichier n'est pas une page du site.

  python3 scripts/generer-infobulles.py           # essai à blanc
  python3 scripts/generer-infobulles.py --write   # écrit le fichier

Les termes de moins de quatre lettres et ceux qui sont aussi des mots
français (EXCLUS) sont écartés, pour ne pas souligner « son » ou « sang ».
"""

import argparse
import pathlib
import re

RACINE = pathlib.Path(__file__).resolve().parents[1]
GLOSSAIRE = RACINE / "Theorie" / "glossaire"
SORTIE = RACINE / "includes" / "infobulles.md"
LIGNE = re.compile(
    r"^\|\s*\*\*\[?([^*\]|]+?)\]?(?:\([^)]*\))?\*\*\s*\|\s*\[?([^\]|]*)\]?"
    r"(?:\([^)]*\))?\s*\|\s*([^|]+?)\s*\|")
EXCLUS = {"sang", "page", "pose", "dore", "dole", "taille"}


def termes():
    vus = {}
    for page in sorted(GLOSSAIRE.glob("[0-9]*.md")):
        for ligne in page.read_text(encoding="utf-8").splitlines():
            m = LIGNE.match(ligne)
            if not m:
                continue
            terme, hangul, traduction = (x.strip() for x in m.groups())
            if len(terme.replace(" ", "")) < 4 or terme.lower() in EXCLUS:
                continue
            if not re.fullmatch(r"[A-Za-z][A-Za-z' -]*", terme):
                continue
            # un lien (audio ou autre) ne garde que son texte au survol
            texte = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", traduction)
            texte = texte.replace("*", "").replace("[", "").replace("]", "")
            if hangul:
                texte += f" ({hangul})"
            for variante in {terme, terme.lower(), terme.capitalize()}:
                vus.setdefault(variante, texte)
    return vus


def contenu():
    lignes = ["<!-- Généré par scripts/generer-infobulles.py : ne pas modifier à la main. -->", ""]
    for terme, texte in sorted(termes().items(), key=lambda x: (x[0].lower(), x[0])):
        lignes.append(f"*[{terme}]: {texte}")
    return "\n".join(lignes) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    neuf = contenu()
    ancien = SORTIE.read_text(encoding="utf-8") if SORTIE.exists() else ""
    if neuf == ancien:
        print("infobulles : déjà à jour")
    elif a.write:
        SORTIE.parent.mkdir(exist_ok=True)
        SORTIE.write_text(neuf, encoding="utf-8")
        print(f"infobulles : {neuf.count(chr(10)) - 2} définitions écrites")
    else:
        print("infobulles : à régénérer — relancer avec --write")


if __name__ == "__main__":
    main()
