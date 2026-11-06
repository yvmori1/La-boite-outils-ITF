#!/usr/bin/env python3
"""Compte les positions et les techniques nommées dans les fiches de tul/.

Chaque mouvement des formes est lié à sa fiche (scripts/lier-mouvements.py) ;
le texte de ces liens est le nom coréen de la technique. Ce script les compte
et imprime les tableaux en Markdown utilisés par Theorie/Analyse_Statistique.md.

  python3 scripts/statistiques-formes.py

Il n'écrit rien : on recopie à la main les tableaux dans la page.
"""

import collections
import pathlib
import re

RACINE = pathlib.Path(__file__).resolve().parents[1]
LIEN = re.compile(r"\[([^\]]+)\]\(\.\./(?:Techniques|sogi|makgi|jirugi|chagi)/[^)]+\)")
POSITION = re.compile(
    r"\b(gunnun|niunja|annun|dwitbal|moa|kyocha|guburyo|nachuo|waebal|"
    r"soojik|sasun|gojung|narani)\s+so(gi)?\b")
NOMS_POSITIONS = {
    "gunnun": "Gunnun Sogi (marche)", "niunja": "Niunja Sogi (en L)",
    "annun": "Annun Sogi (assise)", "dwitbal": "Dwitbal Sogi (pied arrière)",
    "kyocha": "Kyocha Sogi (croisée)", "moa": "Moa Sogi (fermée)",
    "gojung": "Gojung Sogi (fixe)", "narani": "Narani Sogi (parallèle)",
    "waebal": "Waebal Sogi (sur une jambe)", "nachuo": "Nachuo Sogi (basse)",
    "sasun": "Sasun Sogi (diagonale)", "soojik": "Soojik Sogi (verticale)",
    "guburyo": "Guburyo Sogi (flexion)",
}
COUP_DE_PIED = re.compile(r"\b(?!kyocha\b)(\w*cha|\w*chagi|busigi|olligi)\b")


def famille(nom):
    if nom.endswith("sogi") or re.search(r"\bsogi [abcd]$", nom):
        return "Positions seules (préparation)"
    if COUP_DE_PIED.search(nom):
        return "Coups de pied"
    if nom.endswith("makgi"):
        return "Blocages"
    if re.search(r"(jirugi|taerigi|tulgi|ghutgi)$", nom):
        return "Attaques de la main et du coude"
    return "Autres (sauts, saisies, déplacements)"


def sans_cote(nom):
    return " ".join(w for w in nom.split() if w not in ("wen", "orun"))


def main():
    noms = []
    for fiche in sorted((RACINE / "tul").glob("*.md")):
        if fiche.name == "README.md":
            continue
        for ligne in fiche.read_text(encoding="utf-8").splitlines():
            for texte in LIEN.findall(ligne):
                noms.append(sans_cote(texte.lower().replace("-", " ")))
    total = len(noms)
    print(f"Techniques nommées : {total}\n")

    def tableau(titre, compteur, n=None):
        print(f"| {titre} | Occurrences | Part |\n| :--- | ---: | ---: |")
        for cle, nb in compteur.most_common(n):
            print(f"| {cle[0].upper() + cle[1:] if cle.islower() else cle} | {nb} | "
                  f"{100 * nb / total:.1f} % |".replace(".", ","))
        print()

    positions = collections.Counter()
    for nom in noms:
        m = POSITION.search(nom)
        positions[NOMS_POSITIONS[m.group(1)] if m else "Sans position nommée"] += 1
    tableau("Position", positions)
    tableau("Famille", collections.Counter(famille(n) for n in noms))
    for fam in ("Attaques de la main et du coude", "Blocages", "Coups de pied"):
        tableau(fam, collections.Counter(n for n in noms if famille(n) == fam), 8)

    distincts = collections.Counter(noms).most_common()
    cumul = 0
    for seuil in (50, 80):
        k = 0
        cumul = 0
        while cumul < total * seuil / 100:
            cumul += distincts[k][1]
            k += 1
        print(f"{k} techniques distinctes sur {len(distincts)} "
              f"couvrent {seuil} % des occurrences")


if __name__ == "__main__":
    main()
