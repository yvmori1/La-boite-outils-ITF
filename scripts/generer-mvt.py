#!/usr/bin/env python3
"""Régénère mvt.txt : tous les mouvements des formes sous leur nom coréen.

  python3 scripts/generer-mvt.py           # résumé, n'écrit rien
  python3 scripts/generer-mvt.py --write   # écrit mvt.txt

Parcourt les fiches de tul/ dans l'ordre pédagogique et produit un fichier
texte listant, forme par forme, chaque mouvement sous son nom coréen romanisé,
suivi d'un index alphabétique des techniques distinctes.

Les noms déjà transformés en hyperliens par scripts/lier-mouvements.py sont
reconnus : seul le libellé est conservé, jamais la cible du lien.
"""

import argparse
import collections
import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parents[1]
TUL = RACINE / "tul"
SORTIE = RACINE / "mvt.txt"
LARGEUR = 78

# ordre pédagogique, repris de tul/README.md
FORMES = [
    ("EXERCICES FONDAMENTAUX", [
        ("saju-jirugi", "SAJU JIRUGI",
         "10e Gup — exécuté à droite et à gauche : 14 mouvements au total"),
        ("saju-makgi", "SAJU MAKGI",
         "10e Gup — exécuté à droite et à gauche : 16 mouvements au total"),
        ("saju-tulgi", "SAJU TULGI", "10e Gup"),
    ]),
    ("FORMES DES GRADES GUP", [
        ("chon-ji", "CHON-JI", "9e Gup"),
        ("dan-gun", "DAN-GUN", "8e Gup"),
        ("do-san", "DO-SAN", "7e Gup"),
        ("won-hyo", "WON-HYO", "6e Gup"),
        ("yul-gok", "YUL-GOK", "5e Gup"),
        ("joong-gun", "JOONG-GUN", "4e Gup"),
        ("toi-gye", "TOI-GYE", "3e Gup"),
        ("hwa-rang", "HWA-RANG", "2e Gup"),
        ("choong-moo", "CHOONG-MOO", "1er Gup"),
    ]),
    ("FORMES DES GRADES DAN", [
        ("kwang-gae", "KWANG-GAE", "1er Dan"),
        ("po-eun", "PO-EUN", "1er Dan"),
        ("ge-baek", "GE-BAEK", "1er Dan"),
        ("eui-am", "EUI-AM", "2e Dan"),
        ("choong-jang", "CHOONG-JANG", "2e Dan"),
        ("juche", "JUCHE", "2e Dan"),
        ("ko-dang", "KO-DANG", "2e Dan (alternative à Juche)"),
        ("sam-il", "SAM-IL", "3e Dan"),
        ("yoo-sin", "YOO-SIN", "3e Dan"),
        ("choi-yong", "CHOI-YONG", "3e Dan"),
        ("yon-gae", "YON-GAE", "4e Dan"),
        ("ul-ji", "UL-JI", "4e Dan"),
        ("moon-moo", "MOON-MOO", "4e Dan"),
        ("so-san", "SO-SAN", "5e Dan"),
        ("se-jong", "SE-JONG", "5e Dan"),
        ("tong-il", "TONG-IL", "6e Dan"),
    ]),
]

# mouvements dont la fiche ne donne pas de nom coréen
DEDUITS = {}
PREPARATOIRES = {("hwa-rang", 11), ("choong-moo", 11)}

NUMERO = re.compile(r"^(\d+)\.\s+(.*)$")
ITALIQUE = re.compile(r"^\s*\*\((.+?)\)\*\s*$")
INLINE = re.compile(r"\(((?:[^()]|\([^()]*\))*)\)\s*\.?\s*$")
FLECHE = re.compile(r"^\s*\*\*\s*→\s*\(((?:[^()]|\([^()]*\))*)\)\s*\*\*\s*$")
LIEN = re.compile(r"\[([^\]]+)\]\([^)]*\)")


def sans_lien(s):
    """« [Nom](../cible.md) » -> « Nom »."""
    return LIEN.sub(r"\1", s).strip()


def capitaliser(s):
    return re.sub(r"[A-Za-zÀ-ÿ]+", lambda m: m.group(0).capitalize(), s)


def mouvements(slug):
    """[(numéro, nom coréen ou None)] pour une forme."""
    lignes = (TUL / f"{slug}.md").read_text(encoding="utf-8").splitlines()
    depart = next((i for i, l in enumerate(lignes)
                   if re.search(r"^#+ .*Mouvements", l, re.I)), 0)
    resultat, i = [], depart
    while i < len(lignes):
        m = NUMERO.match(lignes[i])
        if m:
            numero, texte = int(m.group(1)), m.group(2).strip()
            coreen = None
            j = i + 1
            while j < len(lignes) and not NUMERO.match(lignes[j]):
                mi = ITALIQUE.match(lignes[j]) or FLECHE.match(lignes[j])
                if mi:
                    coreen = mi.group(1)
                    break
                if lignes[j].strip() and not lignes[j].startswith(" "):
                    break
                j += 1
            if coreen is None:
                mb = INLINE.search(texte)
                if mb:
                    coreen = mb.group(1)
            resultat.append((numero, sans_lien(coreen) if coreen else None))
        i += 1
    return resultat


def construire():
    lignes, index = [], collections.Counter()
    total, sans_nom = 0, []
    ajouter = lignes.append

    ajouter("=" * LARGEUR)
    ajouter("  MOUVEMENTS DES FORMES (TUL) — NOMENCLATURE CORÉENNE")
    ajouter("  La boîte à outils ITF")
    ajouter("=" * LARGEUR)
    ajouter("")
    ajouter("Liste de tous les mouvements de chaque forme, dans l'ordre d'exécution,")
    ajouter("sous leur nom coréen romanisé. Généré à partir des fiches de tul/.")
    ajouter("")
    ajouter("Légende :")
    ajouter("  [déduit]        nom absent de la fiche, reconstitué d'après le texte français")
    ajouter("  [préparatoire]  mouvement préparatoire, nommé avec le mouvement suivant")
    ajouter("")

    for titre, formes in FORMES:
        ajouter("")
        ajouter("=" * LARGEUR)
        ajouter(f"  {titre}")
        ajouter("=" * LARGEUR)
        for slug, nom, grade in formes:
            mvts = mouvements(slug)
            total += len(mvts)
            ajouter("")
            ajouter(f"{nom}  ({len(mvts)} mouvements)")
            ajouter(grade)
            ajouter("-" * LARGEUR)
            for numero, coreen in mvts:
                if (slug, numero) in DEDUITS:
                    ajouter(f"{numero:>4}. {DEDUITS[(slug, numero)]}  [déduit]")
                    sans_nom.append((nom, numero))
                elif (slug, numero) in PREPARATOIRES:
                    ajouter(f"{numero:>4}. (mouvement préparatoire)  [préparatoire]")
                    sans_nom.append((nom, numero))
                elif coreen:
                    propre = capitaliser(coreen.strip().strip("."))
                    ajouter(f"{numero:>4}. {propre}")
                    for part in propre.split(","):
                        index[part.strip()] += 1
                else:
                    ajouter(f"{numero:>4}. (nom coréen absent de la fiche)")
                    sans_nom.append((nom, numero))

    ajouter("")
    ajouter("")
    ajouter("=" * LARGEUR)
    ajouter("  INDEX ALPHABÉTIQUE DES TECHNIQUES")
    ajouter("=" * LARGEUR)
    ajouter("")
    ajouter(f"{len(index)} techniques distinctes, avec leur nombre d'occurrences dans")
    ajouter("l'ensemble des formes.")
    ajouter("")
    for technique in sorted(index):
        ajouter(f"  {index[technique]:>4} ×  {technique}")

    ajouter("")
    ajouter("")
    ajouter("=" * LARGEUR)
    nb_fiches = sum(len(f) for _, f in FORMES)
    ajouter(f"  TOTAL : {total} mouvements sur {nb_fiches} fiches")
    ajouter("=" * LARGEUR)

    return "\n".join(lignes) + "\n", total, len(index), sans_nom


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--write", action="store_true",
                   help="écrit mvt.txt (sinon simple résumé)")
    args = p.parse_args()

    if not TUL.is_dir():
        sys.exit(f"répertoire introuvable : {TUL}")

    contenu, total, distinctes, sans_nom = construire()
    identique = SORTIE.exists() and SORTIE.read_text(encoding="utf-8") == contenu

    print(f"mouvements            : {total}")
    print(f"techniques distinctes : {distinctes}")
    print(f"sans nom dans la fiche: {len(sans_nom)}")
    if "](" in contenu:
        print("ATTENTION : un lien Markdown subsiste dans la sortie")
    print("état                  : " + ("déjà à jour" if identique
                                        else "diffère du fichier"))
    if args.write and not identique:
        SORTIE.write_text(contenu, encoding="utf-8")
        print("écriture              : OUI")
    elif not args.write:
        print("écriture              : non — relancer avec --write")


if __name__ == "__main__":
    main()
