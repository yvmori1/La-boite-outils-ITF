#!/usr/bin/env python3
"""Régénère Techniques/README.md à partir des fiches présentes.

  python3 scripts/generer-index-techniques.py           # affiche un résumé
  python3 scripts/generer-index-techniques.py --write   # écrit le README

Chaque fiche est classée automatiquement d'après son nom de fichier :

  * postures      -> « ...Sogi.md » ou « ...Junbi-So(gi).md »
  * position      -> le mot qui précède « -So- » (Wen-Kyocha-So-... -> kyocha)
  * coups de pied -> présence d'un mot de la famille chagi
  * le reste      -> sans position imposée

Le libellé français vient de la première phrase de la fiche (« est le **...** »),
débarrassé du rappel de posture redondant avec le titre de section. Ajouter une
fiche puis relancer le script suffit : aucune table n'est écrite à la main.
"""

import argparse
import collections
import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parents[1]
DOSSIER = RACINE / "Techniques"

# libellé et ordre d'apparition des sections de position
POSITIONS = [
    ("gunnun", "Position de marche (*Gunnun So*)"),
    ("niunja", "Position en « L » (*Niunja So*)"),
    ("annun", "Position assise (*Annun So*)"),
    ("dwitbal", "Position de pied arrière (*Dwitbal So*)"),
    ("gojung", "Position fixe (*Gojung So*)"),
    ("kyocha", "Position en « X » (*Kyocha So*)"),
    ("moa", "Position rapprochée (*Moa So*)"),
    ("nachuo", "Position basse (*Nachuo So*)"),
    ("waebal", "Position sur une jambe (*Waebal So*)"),
    ("guburyo", "Position fléchie (*Guburyo So*)"),
    ("soojik", "Position verticale (*Soojik So*)"),
    ("sasun", "Position en diagonale (*Sasun So*)"),
    ("narani", "Position parallèle (*Narani So*)"),
]
LABELS = dict(POSITIONS)
ORDRE = [slug for slug, _ in POSITIONS]

# au-delà de ce nombre de fiches, une section est découpée par famille d'action
SEUIL_DECOUPAGE = 25
FAMILLES = [
    ("jirugi", "Coups de poing (*Jirugi*)"),
    ("taerigi", "Frappes (*Taerigi*)"),
    ("makgi", "Blocages (*Makgi*)"),
    ("tulgi", "Piques, coudes et coupures (*Tulgi*, *Ghutgi*)"),
]

MOTS_CHAGI = {"chagi", "cha", "yopcha", "dwitcha", "gorochagi",
              "momchugi", "busigi", "olligi", "milgi"}
SUFFIXES_POSTURE = [
    " en posture du cavalier", " en posture de marche", " en posture en L",
    " en posture du pied arrière", " en posture de pied arrière",
    " en posture arrière rapprochée", " en posture fixe",
    " en posture en X", " en posture croisée",
]


def mots(nom):
    return [m.lower() for m in nom[:-3].split("-") if m]


def description(fiche):
    """Libellé français de la fiche, et faux si la fiche est incomplète."""
    t = fiche.read_text(encoding="utf-8")
    m = (re.search(r"est (?:le|la|l'|un|une)\s+\*\*(.+?)\*\*", t)
         or re.search(r"appelé[e]? (?:le|la|l')\s*\*\*(.+?)\*\*", t)
         or re.search(r"^#\s+(.+)$", t, re.M))
    if not m:
        # fiche vide ou sans titre : on retombe sur le nom de fichier
        return fiche.stem.replace("-", " ") + " — *fiche à rédiger*", False
    d = m.group(1).strip()
    for s in SUFFIXES_POSTURE:
        d = d.replace(s, "")
    d = d.strip()
    return (d[0].upper() + d[1:] if d else fiche.stem), True


def posture(nom):
    """La fiche décrit-elle une posture plutôt qu'une technique ?"""
    base = nom[:-3].lower()
    return base.endswith("sogi") or re.search(r"junbi-so(gi)?(-[ab])?$", base)


def position(nom):
    """Slug de la position d'appui, ou None."""
    ms = mots(nom)
    for i, m in enumerate(ms):
        if m in ("so", "sogi") and i > 0:
            return ms[i - 1]
    return None


def chagi(nom):
    return bool(MOTS_CHAGI & set(mots(nom)))


def famille(nom):
    base = nom[:-3].lower()
    for f in ("jirugi", "taerigi", "makgi"):
        if base.endswith(f):
            return f
    return "tulgi"


def tri(nom):
    """Trie en rapprochant les paires gauche/droite."""
    base = re.sub(r"\b(wen|orun)-", "", nom, flags=re.I).lower()
    lateral = 0 if re.search(r"\bwen-", nom, re.I) else (
        1 if re.search(r"\borun-", nom, re.I) else -1)
    return (base, lateral)


def table(noms, desc):
    lignes = ["| Fiche | Technique |", "| :--- | :--- |"]
    for n in sorted(noms, key=tri):
        lignes.append(f"| [{n}]({n}) | {desc[n]} |")
    return "\n".join(lignes)


def construire():
    fiches = [p for p in sorted(DOSSIER.glob("*.md")) if p.name != "README.md"]
    brut = {p.name: description(p) for p in fiches}
    desc = {n: v[0] for n, v in brut.items()}
    incompletes = [n for n, v in brut.items() if not v[1]]

    postures, kicks, autres = [], [], []
    par_position = collections.defaultdict(list)
    for p in fiches:
        n = p.name
        if posture(n):
            postures.append(n)
        elif position(n):
            par_position[position(n)].append(n)
        elif chagi(n):
            kicks.append(n)
        else:
            autres.append(n)

    slugs = [s for s in ORDRE if s in par_position]
    slugs += sorted(s for s in par_position if s not in LABELS)

    corps, num = [], 0
    for slug in slugs:
        num += 1
        noms = par_position[slug]
        titre = LABELS.get(slug, f"Position *{slug.capitalize()} So*")
        corps.append(f"## {num}. {titre}\n")
        # uniquement la fiche de la position elle-même (Annun-Sogi.md),
        # jamais une position de préparation (Gunnun-Junbi-Sogi.md)
        fiche_posture = next(
            (x for x in postures if x.lower() == f"{slug}-sogi.md"), None)
        if fiche_posture:
            corps.append(
                f"La posture elle-même est décrite dans "
                f"[{fiche_posture}]({fiche_posture}).\n")
        if len(noms) > SEUIL_DECOUPAGE:
            for i, (cle, libelle) in enumerate(FAMILLES, 1):
                sous = [x for x in noms if famille(x) == cle]
                if sous:
                    corps.append(f"### {num}.{i} {libelle}\n")
                    corps.append(table(sous, desc) + "\n")
        else:
            corps.append(table(noms, desc) + "\n")
        corps.append("---\n")

    for noms, titre, intro in (
        (kicks, "Coups de pied (*Chagi*)",
         "Techniques de jambe nommées sans position d'appui imposée.\n"),
        (autres, "Sans position imposée", None),
        (postures, "Postures et positions de préparation",
         "Les positions d'appui et de préparation, décrites pour elles-mêmes.\n"),
    ):
        if not noms:
            continue
        num += 1
        corps.append(f"## {num}. {titre}\n")
        if intro:
            corps.append(intro)
        corps.append(table(noms, desc) + "\n")
        corps.append("---\n")

    entete = f"""# Techniques complètes

Fiches de techniques **nommées intégralement**, c'est-à-dire position et mouvement combinés — la forme sous laquelle elles sont annoncées en cours et exigées en examen.

Là où [makgi](../makgi/README.md), [chagi](../chagi/README.md) et [jirugi](../jirugi/README.md) isolent un élément de vocabulaire, ce répertoire décrit le geste complet : mise en place de la position, coordination hanche/bras, force de réaction, temps d'exécution.

L'ordre de lecture d'un nom ITF est : **position → surface → niveau → direction → action**.

> *Gunnun So Bakat Palmok Nopunde Yop Makgi* = en position de marche, avec l'avant-bras externe, au niveau haut, blocage latéral.

Les techniques latéralisées portent la mention *Wen* (gauche) ou *Orun* (droite) ; elles sont classées côte à côte ci-dessous.

**{len(fiches)} fiches** au total.

---

"""
    pied = """## Voir aussi

* [../Theorie/positions.md](../Theorie/positions.md) — description détaillée de toutes les positions (*Sogi*).
* [../Theorie/grammaire-itf.md](../Theorie/grammaire-itf.md) — règles complètes de nomenclature.
* [../Ceintures/README.md](../Ceintures/README.md) — à quel grade chaque technique est exigée.
* [../mvt.txt](../mvt.txt) — tous les mouvements des formes sous leur nom coréen.
"""
    stats = {
        "total": len(fiches), "postures": len(postures),
        "chagi": len(kicks), "autres": len(autres),
        "a_rediger": len(incompletes),
        **{s: len(par_position[s]) for s in slugs},
    }
    return entete + "\n".join(corps) + "\n" + pied, stats


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--write", action="store_true",
                   help="écrit Techniques/README.md (sinon simple résumé)")
    args = p.parse_args()

    if not DOSSIER.is_dir():
        sys.exit(f"répertoire introuvable : {DOSSIER}")

    contenu, stats = construire()
    cible = DOSSIER / "README.md"
    identique = cible.exists() and cible.read_text(encoding="utf-8") == contenu

    for k, v in stats.items():
        print(f"  {k:<10} : {v}")
    print("état      : " + ("déjà à jour" if identique else "diffère du fichier"))
    if args.write and not identique:
        cible.write_text(contenu, encoding="utf-8")
        print("écriture  : OUI")
    elif not args.write:
        print("écriture  : non — relancer avec --write")


if __name__ == "__main__":
    main()
