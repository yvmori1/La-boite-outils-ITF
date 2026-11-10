#!/usr/bin/env python3
"""Parcours d'apprentissage : lectures par grade et révisions par partie.

  python3 scripts/generer-parcours.py           # dit si tout est à jour
  python3 scripts/generer-parcours.py --write   # écrit les fichiers

Deux productions, tirées de tables tenues ici :

  * PARCOURS : dans chaque fiche de grade (Ceintures/), sous l'encadré
    « Pour ce grade », un bloc « À lire dans le Manuel » : les chapitres à
    lire pour ce grade, dans l'ordre, chacun avec une case à cocher que
    assets/parcours.js garde cochée dans le navigateur.
  * REVISIONS : une page Theorie/revisions/partie-N.md par partie du Manuel,
    faite de questions recopiées des examens théoriques (Theorie/examens/),
    avec leur corrigé. assets/quiz.js y installe le mode révision.

Les titres des chapitres sont lus dans les fichiers ; les questions sont
recopiées telles quelles : corriger un examen corrige aussi la révision
(relancer le script, ou scripts/maintenir.py --write).
"""

import argparse
import os
import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parents[1]
MANUEL = "Theorie/manuel/"
CH = {
    1: "partie-1-art-et-voie/01-ce-qu-est-le-taekwon-do.md",
    2: "partie-1-art-et-voie/02-histoire-et-filiation.md",
    3: "partie-1-art-et-voie/03-le-do-la-culture-morale-de-l-adepte.md",
    4: "partie-1-art-et-voie/04-etiquette-et-vie-du-dojang.md",
    5: "partie-1-art-et-voie/05-le-dobok-et-les-ceintures.md",
    6: "partie-2-principes-physiques/06-la-theorie-de-la-puissance-him-ui-wolli.md",
    7: "partie-2-principes-physiques/07-le-mouvement-de-vague.md",
    8: "partie-2-principes-physiques/08-respiration-ki-et-meditation.md",
    9: "partie-3-grammaire-des-techniques/09-les-deux-formules-de-construction.md",
    10: "partie-3-grammaire-des-techniques/10-les-briques-de-la-formule.md",
    11: "partie-3-grammaire-des-techniques/11-les-verbes-d-action.md",
    12: "partie-3-grammaire-des-techniques/12-les-armes-naturelles-jook-bang.md",
    13: "partie-3-grammaire-des-techniques/13-decrypter-un-nom-de-technique.md",
    14: "partie-4-positions-sogi/14-principes-et-constantes.md",
    15: "partie-4-positions-sogi/15-les-positions-d-un-coup-d-oeil.md",
    16: "partie-4-positions-sogi/16-les-21-positions-en-detail.md",
    17: "partie-5-repertoire-technique/17-les-deplacements-dolgi.md",
    18: "partie-5-repertoire-technique/18-les-techniques-de-bras.md",
    19: "partie-5-repertoire-technique/19-les-techniques-de-jambes.md",
    20: "partie-6-formes-tul/20-la-forme-comme-heritage.md",
    21: "partie-6-formes-tul/21-directives-d-execution.md",
    22: "partie-6-formes-tul/22-les-exercices-fondamentaux-saju.md",
    23: "partie-6-formes-tul/23-les-vingt-quatre-formes-en-un-tableau.md",
    24: "partie-6-formes-tul/24-les-formes-une-a-une.md",
    25: "annexe-b-distances-de-saut.md",
    26: "annexe-c-types-de-mouvements.md",
}


def ch(n):
    return MANUEL + CH[n]


# Lectures par grade : ce qui s'ajoute à ce grade, dans l'ordre de lecture.
# Les chapitres suivent la matière de l'examen théorique du grade et le
# programme technique ; chaque grade suppose les lectures des précédents.
PARCOURS = {
    "01_Blanche.md": [ch(1), ch(3), ch(4), ch(5), ch(22)],
    "02_Blanche_I.md": [ch(2), ch(14), ch(20), ch(21), ch(24)],
    "03_Jaune.md": [ch(9), ch(15), ch(17)],
    "04_Jaune_I.md": [ch(6), ch(10), ch(18)],
    "05_Verte.md": [ch(11), ch(12), ch(19)],
    "06_Verte_I.md": [ch(7), ch(13), "Combat/kyokpa.md"],
    "07_Bleu.md": [ch(8), "Combat/systemes-de-combat.md", "Combat/prise-de-mesure.md"],
    "08_Bleu_I.md": [ch(16), "Combat/combat-libre.md", "Combat/arbitrage.md"],
    "09_Rouge.md": ["Combat/README.md", ch(23), ch(25), ch(26)],
    "10_Rouge_I.md": ["Combat/points-vitaux.md", "Combat/hosinsul.md",
                      "Combat/progression.md"],
    "11_Noire_I.md": [ch(20), ch(24)],
    "12_Noire_II.md": [ch(24), "Theorie/glossaire/README.md"],
}

# Révisions : (partie, titre) -> questions (examen, numéro de question).
C, N = "Theorie/examens/ceintures-de-couleur/", "Theorie/examens/ceintures-noires/"
G = {1: C + "01-10e-gup.md", 2: C + "02-9e-gup.md", 3: C + "03-8e-gup.md",
     4: C + "04-7e-gup.md", 5: C + "05-6e-gup.md", 6: C + "06-5e-gup.md",
     7: C + "07-4e-gup.md", 8: C + "08-3e-gup.md", 9: C + "09-2e-gup.md",
     10: C + "10-1er-gup.md"}
D = {1: N + "01-1er-dan.md", 3: N + "03-3e-dan.md", 4: N + "04-4e-dan.md"}
REVISIONS = [
    (1, "L'art et sa voie", [(G[1], 1), (G[1], 2), (G[1], 5), (G[2], 1), (G[3], 1),
                             (G[3], 4), (G[4], 4), (G[5], 3), (G[6], 3)]),
    (2, "Les principes physiques", [(G[4], 3), (G[7], 3)]),
    (3, "La grammaire des techniques", [(G[1], 4), (G[2], 5), (G[3], 5)]),
    (4, "Les positions (Sogi)", [(G[8], 4), (G[7], 2), (G[9], 3)]),
    (5, "Le répertoire technique", [(G[4], 5), (G[5], 5), (G[6], 5), (G[7], 5),
                                    (G[8], 5), (G[9], 5)]),
    (6, "Les formes (Tul)", [(G[2], 4), (G[1], 3), (G[2], 3), (G[3], 3), (G[4], 2),
                             (G[5], 1), (G[6], 2), (G[8], 2), (G[10], 3), (D[3], 1)]),
    (7, "Combat, autodéfense et casse", [(G[6], 4), (G[7], 4), (G[8], 3), (G[9], 2)]),
    (8, "La progression", [(G[10], 4), (D[1], 4), (D[3], 4), (D[4], 4)]),
]
ROMAINS = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII"}

DEBUT = "<!-- parcours : bloc produit par scripts/generer-parcours.py -->"
FIN = "<!-- /parcours -->"
BLOC = re.compile(r"\n*" + re.escape(DEBUT) + r".*?" + re.escape(FIN) + r"\n*", re.S)
LIEN = re.compile(r"(\]\()([^)#\s]+)([^)]*\))")


def titre(chemin):
    p = RACINE / chemin
    if not p.exists():
        sys.exit(f"generer-parcours.py : fichier absent : {chemin}")
    m = re.search(r"^#\s+(.+)$", p.read_text(encoding="utf-8"), re.M)
    t = m.group(1).strip() if m else p.stem
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)  # lien audio dans le titre
    return re.sub(r"\s+—\s+$", "", t)


def relatif(cible, depuis):
    """Chemin de cible (depuis la racine) vu du dossier du fichier depuis."""
    return os.path.relpath(RACINE / cible, (RACINE / depuis).parent).replace(os.sep, "/")


def bloc_parcours(fiche, chemins):
    depuis = "Ceintures/" + fiche
    lignes = [f"* [ ] [{titre(c)}]({relatif(c, depuis)})" for c in chemins]
    return ("\n\n" + DEBUT + "\n\n**À lire dans le Manuel pour ce grade, dans l'ordre :**\n\n"
            + "\n".join(lignes) + "\n\n" + FIN + "\n\n")


def appliquer_parcours(texte, bloc):
    texte = BLOC.sub("\n\n", texte)
    # le bloc suit l'encadré « Pour ce grade » (ou, à défaut, le titre)
    m = re.search(r"^> \*\*Pour ce grade :\*\*.*$", texte, re.M) or \
        re.search(r"^# .+$", texte, re.M)
    fin = m.end()
    return texte[:fin].rstrip("\n") + bloc + texte[fin:].lstrip("\n")


def question(examen, n):
    texte = (RACINE / examen).read_text(encoding="utf-8")
    m = re.search(r"^### Q%d\.\s*(.+?)$(.*?)(?=^#{1,3} |\Z)" % n, texte, re.M | re.S)
    if not m:
        sys.exit(f"generer-parcours.py : question Q{n} absente de {examen}")
    intitule = re.sub(r"\s*\(\d+ points?\)\s*$", "", m.group(1).strip())
    corps = m.group(2).strip("\n")
    corps = corps.rstrip().removesuffix("---").rstrip()
    return intitule, corps


def recibler(corps, examen, page):
    """Réécrit les liens relatifs du corrigé pour la page de révision."""
    def rep(m):
        cible = m.group(2)
        if re.match(r"[a-z]+:", cible) or cible.startswith("/"):
            return m.group(0)
        absolu = os.path.normpath(os.path.join(os.path.dirname(examen), cible))
        return m.group(1) + relatif(absolu, page) + m.group(3)
    return LIEN.sub(rep, corps)


def nom_examen(examen):
    t = titre(examen)
    m = re.search(r"\((\d+(?:er|e) (?:Gup|Dan))\)", t)
    return m.group(1) if m else t


def page_revision(partie, nom, questions):
    page = f"Theorie/revisions/partie-{partie}.md"
    lignes = [f"# Révision — Partie {ROMAINS[partie]} : {nom}", "",
              f"{len(questions)} questions tirées des "
              "[examens théoriques](../examens/README.md), avec leur corrigé. "
              "Répondez de tête, ouvrez le corrigé, puis notez-vous : le mode "
              "révision garde le score dans ce navigateur.", ""]
    for i, (examen, n) in enumerate(questions, 1):
        intitule, corps = question(examen, n)
        lignes += [f"### Q{i}. {intitule}", "",
                   f"*Examen du {nom_examen(examen)}, question {n} "
                   f"([voir l'examen]({relatif(examen, page)})).*", "",
                   recibler(corps, examen, page), ""]
    return page, "\n".join(lignes).rstrip("\n") + "\n"


def produire():
    fichiers = {}
    for fiche, chemins in PARCOURS.items():
        p = RACINE / "Ceintures" / fiche
        fichiers[p] = appliquer_parcours(p.read_text(encoding="utf-8"),
                                         bloc_parcours(fiche, chemins))
    for partie, nom, questions in REVISIONS:
        page, texte = page_revision(partie, nom, questions)
        fichiers[RACINE / page] = texte
    return fichiers


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--write", action="store_true", help="écrit les fichiers")
    args = p.parse_args()
    differents = []
    for chemin, texte in produire().items():
        actuel = chemin.read_text(encoding="utf-8") if chemin.exists() else ""
        if texte != actuel:
            differents.append(str(chemin.relative_to(RACINE)))
            if args.write:
                chemin.parent.mkdir(parents=True, exist_ok=True)
                chemin.write_text(texte, encoding="utf-8")
    if not differents:
        print("parcours déjà à jour")
    elif args.write:
        print("parcours écrits : " + ", ".join(differents))
    else:
        print("le parcours produit diffère du fichier : " + ", ".join(differents))
    return 0


if __name__ == "__main__":
    sys.exit(main())
