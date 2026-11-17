"""Emplacements du contenu du site, partagés par tous les scripts.

Tout le contenu publié est dans docs/, rangé comme le menu du site
(menu.yml) : un dossier par partie du Manuel, avec les fiches qui la mettent
en pratique, puis les annexes et les pages « À propos ».

    docs/
      README.md                   accueil
      sommaire.md                 sommaire du Manuel
      1-art-et-voie/ … 3-grammaire-des-techniques/   chapitres + revision.md
      4-positions/                chapitres 14-16, fiches/ (positions)
      5-repertoire-technique/     chapitres 17-19, jirugi/, makgi/, chagi/,
                                  combinees/ (techniques combinées)
      6-formes/                   chapitres 20-26, fiches/ (formes)
      7-combat/                   pages du combat, combats-arranges/,
                                  hosinsul/ (Manuel, partie VII, et autodefense.md)
      8-progression/              ceintures/, programme-session/, examens/
      annexes/                    a-lexique/, b-glossaire/,
                                  c-analyse-statistique.md, d-bibliographie.md
      a-propos/                   application.md, confidentialite.md
      audio/  images/  assets/

Un script qui a besoin d'un dossier le prend ici plutôt que d'écrire son
chemin en dur : un déplacement ne se corrige alors qu'à un seul endroit.
"""

import os
import pathlib

RACINE = pathlib.Path(__file__).resolve().parents[1]
DOCS = RACINE / "docs"
AUDIO = DOCS / "audio"
IMAGES = DOCS / "images"

# Familles de fiches : nom court -> dossier sous docs/. Le nom court est aussi
# celui du sous-dossier d'audio (audio/tul/chon-ji.m4a…), qui ne change pas.
FICHES = {
    "sogi": "4-positions/fiches",
    "jirugi": "5-repertoire-technique/jirugi",
    "makgi": "5-repertoire-technique/makgi",
    "chagi": "5-repertoire-technique/chagi",
    "Techniques": "5-repertoire-technique/combinees",
    "tul": "6-formes/fiches",
}

# Parties du Manuel : numéro -> dossier sous docs/ (la révision de fin de
# partie y est revision.md).
PARTIES = {
    1: "1-art-et-voie",
    2: "2-principes-physiques",
    3: "3-grammaire-des-techniques",
    4: "4-positions",
    5: "5-repertoire-technique",
    6: "6-formes",
    7: "7-combat",
    8: "8-progression",
}

SOMMAIRE = DOCS / "sommaire.md"
HOSINSUL = DOCS / "7-combat" / "hosinsul"
# page du combat rangée avec le programme par grade, mais hors du Manuel
AUTODEFENSE = HOSINSUL / "autodefense.md"
LEXIQUE = DOCS / "annexes" / "a-lexique"
COMBAT = DOCS / "7-combat"
COMBATS_ARRANGES = DOCS / "7-combat" / "combats-arranges"
CEINTURES = DOCS / "8-progression" / "ceintures"
PROGRAMME = DOCS / "8-progression" / "programme-session"
EXAMENS = DOCS / "8-progression" / "examens"
GLOSSAIRE = DOCS / "annexes" / "b-glossaire"
ACCUEIL = DOCS / "README.md"


def fiches(nom):
    """Dossier d'une famille de fiches (« tul », « sogi »…)."""
    return DOCS / FICHES[nom]


def famille(chemin):
    """Nom court de la famille d'une fiche, ou None."""
    for nom, dossier in FICHES.items():
        if pathlib.Path(chemin).parent == DOCS / dossier:
            return nom
    return None


def revision(partie):
    return DOCS / PARTIES[partie] / "revision.md"


def pages_manuel():
    """Toutes les pages du Manuel : sommaire, chapitres des parties I à VI,
    partie VII (Hosinsul par grade) et annexe A. Les fiches et les révisions
    n'en font pas partie."""
    pages = [SOMMAIRE]
    for n in range(1, 7):
        pages += (DOCS / PARTIES[n]).glob("*.md")
    pages += (p for p in HOSINSUL.glob("*.md") if p != AUTODEFENSE)
    pages += LEXIQUE.glob("*.md")
    return sorted(p for p in pages if p.name != "revision.md")


def pages_combat():
    """Pages propres au combat (7-combat/*.md et l'autodéfense), sans la
    révision."""
    return sorted([p for p in COMBAT.glob("*.md") if p.name != "revision.md"]
                  + [AUTODEFENSE])


def site(chemin):
    """Chemin d'une page relatif à docs/, tel que MkDocs et menu.yml le
    nomment (« 6-formes/fiches/chon-ji.md »)."""
    return pathlib.Path(chemin).resolve().relative_to(DOCS).as_posix()


def lien(depuis, vers):
    """Lien relatif d'une page Markdown vers un fichier ou un dossier."""
    return os.path.relpath(vers, pathlib.Path(depuis).parent).replace(os.sep, "/")
