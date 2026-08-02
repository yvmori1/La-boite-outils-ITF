#!/usr/bin/env python3
"""Transforme le nom coréen de chaque mouvement des tuls en hyperlien.

Parcourt les fiches de tul/ et remplace le nom coréen de chaque mouvement
par un lien vers la fiche qui l'explique, cherchée dans Techniques/, makgi/,
jirugi/ et chagi/.

  python3 scripts/lier-mouvements.py              # essai à blanc, n'écrit rien
  python3 scripts/lier-mouvements.py --write      # applique les modifications
  python3 scripts/lier-mouvements.py --manquants  # liste les noms sans fiche

Le script est idempotent : une ligne déjà liée est laissée intacte. Après
l'ajout de nouvelles fiches techniques, le relancer avec --write ne touche
que les mouvements nouvellement résolus.

Deux formats de fiches sont reconnus :
  1. Déplacer le pied gauche...
     *(Gunnun so palmok najunde makgi)*        <- nom sur sa propre ligne
  1. Déplacer le pied gauche... (Gunnun So Palmok Najunde Makgi).  <- en fin de ligne

Résolution d'une cible, du plus fidèle au plus approximatif :
  1. nom complet tel quel ;
  2. nom sans la posture de départ (« gunnun so », « niunja so »…) ;
  3. retrait des modificateurs — wen/orun, bandae/baro, najunde/kaunde/nopunde —
     dans toutes les combinaisons, des plus petites aux plus grandes ;
  4. raccourcissement par la fin (« ... baro ap makgi » -> « ap makgi »).
La comparaison ignore casse, tirets et espaces, ce qui réconcilie par exemple
« Kaunde yopcha jirugi » avec chagi/yop-cha-jirugi.md.

Un lien reste toujours un fragment réel du nom du mouvement ; sur les noms
longs, la cible peut n'expliquer qu'une partie de la technique.
"""

import argparse
import collections
import itertools
import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parents[1]
TUL = RACINE / "tul"
DOSSIERS_CIBLES = ("Techniques", "makgi", "jirugi", "chagi")
HORS_INDEX = {"README.md", "Dans-les-formes.md", "nomenclature.md"}

POSTURE = re.compile(
    r"^(gunnun|niunja|annun|dwitbal|moa|kyocha|guburyo|nachuo|waebal|soojik|"
    r"sasun|gojung|narani)\s+so(gi)?\b\s*")
MODIFICATEURS = {
    "lateral": re.compile(r"\b(wen|orun)\b"),
    "sens": re.compile(r"\b(bandae|baro)\b"),
    "niveau": re.compile(r"\b(najunde|kaunde|nopunde)\b"),
}
SEPARATEUR = re.compile(r"(\s*,\s*|\s+wa\s+)")

# nom coréen sur sa propre ligne, entre parenthèses en italique
LIGNE_ITALIQUE = re.compile(r"^(\s*)\*\((.+?)\)\*\s*$")
# nom coréen entre parenthèses en fin de ligne numérotée ; un niveau
# d'imbrication est toléré pour reconnaître les lignes déjà liées
LIGNE_INLINE = re.compile(
    r"^(\d+\.\s+.*?)\(((?:[^()]|\([^()]*\))*)\)(\s*\.?\s*)$")


def normaliser(s):
    s = s.lower().replace("-", " ")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return " ".join(s.split())


def cle(s):
    """Clé de comparaison : sans casse, sans tiret, sans espace."""
    return normaliser(s).replace(" ", "")


def indexer_cibles():
    cibles = {}
    for dossier in DOSSIERS_CIBLES:
        for fiche in sorted((RACINE / dossier).glob("*.md")):
            if fiche.name in HORS_INDEX:
                continue
            k = cle(fiche.stem)
            cibles.setdefault(k, f"../{dossier}/{fiche.name}")
    return cibles


def candidats(nom):
    """Variantes du nom, de la plus fidèle à la plus dégradée."""
    vus = set()
    sans_posture = POSTURE.sub("", nom)
    bases = [nom] + ([sans_posture] if sans_posture != nom else [])
    for base in bases:
        for taille in range(len(MODIFICATEURS) + 1):
            for combinaison in itertools.combinations(MODIFICATEURS, taille):
                v = base
                for m in combinaison:
                    v = MODIFICATEURS[m].sub(" ", v)
                v = " ".join(v.split())
                if v and v not in vus:
                    vus.add(v)
                    yield v
    mots = sans_posture.split()
    for i in range(1, max(1, len(mots) - 1)):
        v = " ".join(mots[i:])
        if v not in vus:
            vus.add(v)
            yield v


class Lieur:
    def __init__(self, cibles):
        self.cibles = cibles
        self.cache = {}
        self.manquants = collections.Counter()

    def resoudre(self, nom):
        if nom not in self.cache:
            trouve = None
            for rang, variante in enumerate(candidats(nom)):
                k = cle(variante)
                if k in self.cibles:
                    trouve = (self.cibles[k], rang)
                    break
            self.cache[nom] = trouve
        return self.cache[nom]

    def lier(self, coreen):
        """Rend (texte lié, nombre de liens posés)."""
        # la chaîne entière d'abord : une fiche peut couvrir la technique double
        entier = self.resoudre(normaliser(coreen))
        if entier and entier[1] == 0:
            return f"[{coreen.strip()}]({entier[0]})", 1

        morceaux, poses = [], 0
        for part in SEPARATEUR.split(coreen):
            if not part.strip() or SEPARATEUR.fullmatch(part):
                morceaux.append(part)
                continue
            resultat = self.resoudre(normaliser(part))
            if resultat:
                morceaux.append(f"[{part.strip()}]({resultat[0]})")
                poses += 1
            else:
                morceaux.append(part)
                self.manquants[normaliser(part)] += 1
        return "".join(morceaux), poses


def traiter(ecrire):
    lieur = Lieur(indexer_cibles())
    stats = collections.Counter()
    fiches_modifiees = []

    for fiche in sorted(TUL.glob("*.md")):
        if fiche.name == "README.md":
            continue
        lignes = fiche.read_text(encoding="utf-8").splitlines(keepends=True)
        sortie, modifiee = [], False

        for ligne in lignes:
            nu = ligne.rstrip("\n")
            m = LIGNE_ITALIQUE.match(nu) or LIGNE_INLINE.match(nu)
            if m:
                stats["mouvements"] += 1
                if "](" in nu:                      # déjà lié : on n'y touche pas
                    stats["deja_lies"] += 1
                else:
                    groupes = m.groups()
                    coreen = groupes[1]
                    nouveau, poses = lieur.lier(coreen)
                    if poses:
                        if len(groupes) == 2:       # format italique
                            ligne = f"{groupes[0]}*({nouveau})*\n"
                        else:                       # format en fin de ligne
                            ligne = f"{groupes[0]}({nouveau}){groupes[2]}\n"
                        modifiee = True
                        stats["nouveaux_liens"] += poses
                        stats["lignes_liees"] += 1
                    else:
                        stats["non_resolus"] += 1
            sortie.append(ligne)

        if modifiee:
            fiches_modifiees.append(fiche.name)
            if ecrire:
                fiche.write_text("".join(sortie), encoding="utf-8")

    return stats, fiches_modifiees, lieur


def main():
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("--write", action="store_true",
                         help="applique les modifications (sinon essai à blanc)")
    parseur.add_argument("--manquants", action="store_true",
                         help="liste les noms coréens sans fiche correspondante")
    args = parseur.parse_args()

    if not TUL.is_dir():
        sys.exit(f"répertoire introuvable : {TUL}")

    stats, fiches, lieur = traiter(args.write)

    print(f"mouvements détectés     : {stats['mouvements']}")
    print(f"  déjà liés             : {stats['deja_lies']}")
    print(f"  liens posés à ce tour : {stats['nouveaux_liens']}"
          f" sur {stats['lignes_liees']} lignes")
    print(f"  sans fiche cible      : {stats['non_resolus']}")
    print(f"fiches concernées       : {len(fiches)}")
    if fiches and not args.write:
        print("  " + ", ".join(fiches[:8]) + (" …" if len(fiches) > 8 else ""))
    print("écriture                : " + ("OUI" if args.write
                                          else "non — relancer avec --write"))

    if args.manquants:
        print(f"\nnoms distincts sans fiche : {len(lieur.manquants)}")
        for nom, n in sorted(lieur.manquants.items(), key=lambda x: -x[1]):
            print(f"  {n:>3} × {nom}")


if __name__ == "__main__":
    main()
