#!/usr/bin/env python3
"""Ajoute en bas des fiches un bloc « Fiches liées » calculé, jamais écrit à la main.

  python3 scripts/generer-voir-aussi.py           # dit si les blocs sont à jour
  python3 scripts/generer-voir-aussi.py --write   # écrit les blocs

Pour une fiche de Techniques/ :
  * sa position (fiche de sogi/), d'après le mot qui précède « So » ;
  * son geste de base (chagi/, makgi/, jirugi/), dont le nom est contenu
    dans le sien ;
  * les formes qui la citent.
Pour une fiche de chagi/, makgi/ ou jirugi/ : les techniques complètes qui
utilisent ce geste, et les formes où il paraît (directement ou par elles).
Pour une fiche de sogi/ : le nombre de techniques dans cette position, et les
formes qui citent la fiche.
Pour toutes : en tête, le chapitre du Manuel qui explique la famille de la
fiche (« Dans le Manuel »), d'après son dossier (table MANUEL).

Les formes sont lues dans les liens des pages de tul/ (posés par
lier-mouvements.py) et rangées dans l'ordre du menu Formes (tul/.pages).
Le bloc est encadré de deux commentaires HTML, invisibles à l'affichage : le
script remplace ce qui est entre eux et ne touche à rien d'autre.
"""

import argparse
import collections
import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parents[1]
BASES = ("chagi", "makgi", "jirugi")
CIBLES = ("Techniques", "sogi") + BASES
HORS = {"README.md", "nomenclature.md", "Dans-les-formes.md"}
DEBUT = "<!-- fiches-liees : bloc produit par scripts/generer-voir-aussi.py -->"
FIN = "<!-- /fiches-liees -->"
BLOC = re.compile(r"\n*" + re.escape(DEBUT) + r".*?" + re.escape(FIN) + r"\n*", re.S)
LIEN = re.compile(r"\]\(\.\./(" + "|".join(CIBLES) + r")/([^)#\s]+\.md)")
MAX_TECHNIQUES = 20
# Chapitres du Manuel qui expliquent chaque famille de fiches.
M = "Theorie/manuel/"
CH13 = (M + "partie-3-grammaire-des-techniques/13-decrypter-un-nom-de-technique.md",
        "13. Décrypter un nom de technique")
CH16 = (M + "partie-4-positions-sogi/16-les-21-positions-en-detail.md",
        "16. Les 27 positions en détail")
CH18 = (M + "partie-5-repertoire-technique/18-les-techniques-de-bras.md",
        "18. Les techniques de bras")
CH19 = (M + "partie-5-repertoire-technique/19-les-techniques-de-jambes.md",
        "19. Les techniques de jambes")
MANUEL = {"sogi": [CH16], "jirugi": [CH18], "makgi": [CH18], "chagi": [CH19]}
LATERAL = {"wen", "orun"}
MODIFICATEURS = {"najunde", "kaunde", "nopunde", "bandae", "baro"}


def fiches(dossier):
    return sorted(p for p in (RACINE / dossier).glob("*.md") if p.name not in HORS)


def titre(p):
    m = re.search(r"^#\s+(.+)$", p.read_text(encoding="utf-8"), re.M)
    t = m.group(1).strip() if m else p.stem.replace("-", " ")
    # un titre peut porter un lien audio : on n'en garde que le texte
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)


def nom_forme(p):
    """« chon-ji.md » -> « Chon-Ji », « saju-jirugi.md » -> « Saju Jirugi »."""
    if p.stem.startswith("saju-"):
        return " ".join(m.capitalize() for m in p.stem.split("-"))
    return "-".join(m.capitalize() for m in p.stem.split("-"))


def ordre_formes():
    """Fichiers de tul/ dans l'ordre du menu."""
    pages = (RACINE / "tul" / ".pages").read_text(encoding="utf-8")
    ordre = re.findall(r"([\w-]+\.md)\s*$", pages, re.M)
    return [n for n in ordre if n != "README.md"]


def formes_citant():
    """Fiche (« Techniques/X.md ») -> formes qui la citent, dans l'ordre du menu."""
    ordre = ordre_formes()
    rang = {n: i for i, n in enumerate(ordre)}
    cites = collections.defaultdict(set)
    for p in (RACINE / "tul").glob("*.md"):
        if p.name == "README.md":
            continue
        for dossier, fichier in LIEN.findall(p.read_text(encoding="utf-8")):
            cites[f"{dossier}/{fichier}"].add(p.name)
    return {k: sorted(v, key=lambda n: rang.get(n, len(rang)))
            for k, v in cites.items()}


def mots(nom):
    return [m.lower() for m in nom[:-3].split("-") if m]


def position(nom):
    ms = mots(nom)
    for i, m in enumerate(ms):
        if m in ("so", "sogi") and i > 0:
            return ms[i - 1]
    return None


def gestes(nom, bases):
    """Gestes de base dont le nom (sans tirets) recouvre des mots consécutifs.

    Les mots de niveau et de sens (Kaunde, Bandae…) peuvent s'intercaler :
    « Palmok Kaunde Daebi Makgi » relève de « Palmok Daebi Makgi ».
    """
    ms = [m for m in mots(nom) if m not in LATERAL]
    trouves = []
    for cle, (chemin, mots_base) in bases.items():
        lus = [m for m in ms if m not in MODIFICATEURS or m in mots_base]
        for suite in (ms, lus):
            for i in range(len(suite)):
                for j in range(i + 1, len(suite) + 1):
                    if "".join(suite[i:j]) == cle:
                        trouves.append((j - i, len(cle), cle, chemin))
    # le plus précis (le plus de mots) d'abord ; un geste déjà contenu dans
    # un geste retenu (Yop Makgi dans Nopunde Yop Makgi) est écarté
    trouves.sort(key=lambda x: (-x[0], -x[1], x[3]))
    retenus = []
    for _, _, cle, chemin in trouves:
        if all(cle not in c for c, _ in retenus):
            retenus.append((cle, chemin))
    return [chemin for _, chemin in retenus[:2]]


def lien(depuis, cible, texte):
    return f"[{texte}](../{cible})"


def liste_formes(noms):
    return ", ".join(f"[{nom_forme(RACINE / 'tul' / n)}](../tul/{n})" for n in noms)


def ligne_manuel(chapitres):
    return "* **Dans le Manuel :** " + ", ".join(
        f"[{texte}](../{chemin})" for chemin, texte in chapitres)


def chapitres_technique(nom, geste):
    """Une technique combinée : la grammaire de son nom (ch. 13), puis le
    chapitre de son geste, jambes (ch. 19) ou bras (ch. 18)."""
    ms = mots(nom)
    jambe = any(g.startswith("chagi/") for g in geste) or any(
        m.startswith("cha") for m in ms)
    return [CH13, CH19 if jambe else CH18]


def construire():
    cites = formes_citant()
    rang = {n: i for i, n in enumerate(ordre_formes())}
    bases = {"".join(mots(p.name)): (f"{p.parent.name}/{p.name}", set(mots(p.name)))
             for d in BASES for p in fiches(d)}
    titres = {f"{d}/{p.name}": titre(p) for d in CIBLES for p in fiches(d)}
    sogi = {p.name.lower(): f"sogi/{p.name}" for p in fiches("sogi")}

    blocs = {}
    usages = collections.defaultdict(list)
    par_position = collections.Counter()
    for p in fiches("Techniques"):
        cle = f"Techniques/{p.name}"
        lignes = []
        pos = position(p.name)
        if pos:
            par_position[pos] += 1
            fiche_pos = sogi.get(f"{pos}-sogi.md")
            if fiche_pos:
                lignes.append(f"* **Position :** {lien(cle, fiche_pos, titres[fiche_pos])}")
        geste = gestes(p.name, bases)
        lignes.insert(0, ligne_manuel(chapitres_technique(p.name, geste)))
        for g in geste:
            usages[g].append(cle)
        if geste:
            lignes.append("* **Geste de base :** " + ", ".join(
                lien(cle, g, titres[g]) for g in geste))
        if cites.get(cle):
            lignes.append("* **Dans les formes :** " + liste_formes(cites[cle]))
        blocs[cle] = lignes

    for d in BASES:
        for p in fiches(d):
            cle = f"{d}/{p.name}"
            lignes = [ligne_manuel(MANUEL[d])]
            techniques = sorted(usages.get(cle, []))
            if techniques:
                montres = techniques[:MAX_TECHNIQUES]
                texte = ", ".join(lien(cle, t, titres[t]) for t in montres)
                reste = len(techniques) - len(montres)
                if reste:
                    texte += (f", et {reste} autres dans "
                              f"[Techniques](../Techniques/README.md)")
                lignes.append(f"* **Techniques complètes :** {texte}")
            formes = set(cites.get(cle, []))
            for t in techniques:
                formes.update(cites.get(t, []))
            if formes:
                lignes.append("* **Dans les formes :** " + liste_formes(
                    sorted(formes, key=lambda n: rang.get(n, len(rang)))))
            blocs[cle] = lignes

    for p in fiches("sogi"):
        cle = f"sogi/{p.name}"
        lignes = [ligne_manuel(MANUEL["sogi"])]
        pos = p.name.lower()[:-len("-sogi.md")] if p.name.lower().endswith("-sogi.md") else None
        if pos and par_position.get(pos):
            lignes.append(f"* **Techniques dans cette position :** "
                          f"{par_position[pos]} fiches, classées dans "
                          f"[Techniques](../Techniques/README.md)")
        if cites.get(cle):
            lignes.append("* **Dans les formes :** " + liste_formes(cites[cle]))
        blocs[cle] = lignes
    return blocs


def appliquer(texte, lignes):
    if not lignes and DEBUT not in texte:
        return texte
    texte = BLOC.sub("\n", texte).rstrip("\n") + "\n"
    if not lignes:
        return texte
    return (texte + "\n" + DEBUT + "\n\n## Fiches liées\n\n"
            + "\n".join(lignes) + "\n\n" + FIN + "\n")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--write", action="store_true", help="écrit les blocs")
    args = p.parse_args()
    differents = []
    for cle, lignes in construire().items():
        chemin = RACINE / cle
        actuel = chemin.read_text(encoding="utf-8")
        nouveau = appliquer(actuel, lignes)
        if nouveau != actuel:
            differents.append(cle)
            if args.write:
                chemin.write_text(nouveau, encoding="utf-8")
    if not differents:
        print("blocs déjà à jour")
    elif args.write:
        print(f"blocs écrits : {len(differents)} fiche(s)")
    else:
        print(f"le bloc produit diffère du fichier : {len(differents)} fiche(s), "
              f"dont {', '.join(differents[:3])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
