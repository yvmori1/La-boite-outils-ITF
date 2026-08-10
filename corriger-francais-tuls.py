#!/usr/bin/env python3
"""Corrige le français des fiches de tul/, d'après recueil-complet-formes-taekwondo-v2.md.

  python3 corriger-francais-tuls.py           # essai à blanc, n'écrit rien
  python3 corriger-francais-tuls.py --write   # applique les corrections

Le recueil sert de référence pour la syntaxe française ; le vocabulaire
technique reste celui du dépôt (« latéral perçant », « avant fouetté »,
« blocage montant », « position de préparation pliée »), aligné sur les
fiches de Techniques/, chagi/, makgi/ et jirugi/.

Le script est idempotent : une deuxième exécution ne signale aucun changement.
"""

import argparse
import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parent
TUL = RACINE / "tul"

# --- corrections applicables à toutes les fiches ------------------------------

GLOBALES = [
    # anglais resté dans le texte
    (r"\bwith\b", "avec"),
    (r"Exécuter (\d+) à travers (\d+) en mouvement", r"Exécuter \1 à \2 en mouvement"),

    # ordre des mots calqué de l'anglais
    (r"un (droit|gauche) position de préparation pliée ([AB]) vers",
     lambda m: f"une position de préparation pliée {m.group(2)} "
               f"{'droite' if m.group(1) == 'droit' else 'gauche'} vers"),
    (r"un (droit|gauche) position de marche de préparation vers",
     lambda m: "une position de marche de préparation "
               f"{'droite' if m.group(1) == 'droit' else 'gauche'} vers"),
    (r"\bun position de préparation fermée\b", "une position de préparation fermée"),
    (r"avec un (gauche|droit) double avant-bras",
     lambda m: f"avec le double avant-bras {m.group(1)}"),
    (r"avec un (gauche|droit) double poing",
     lambda m: f"avec le double poing {m.group(1)}"),
    (r"en un en glissant mouvement pour former", "en glissant pour former"),
    (r"en un en glissant mouvement", "en glissant le pied"),
    (r"en un double en avançant mouvement", "en un double pas en avant"),

    # accords et articles
    (r"avec une paumes jumelées", "avec les paumes jumelées"),
    (r"avec un jumelé coude", "avec les deux coudes"),
    (r"avec un alterné paume", "avec les paumes alternées"),
    (r"\bla épaule\b", "l'épaule"),
    (r"\bla aisselle\b", "l'aisselle"),
    (r"avec la paume droit\b", "avec la paume droite"),
    (r"en pivotant avec gauche pied", "en pivotant avec le pied gauche"),
    (r"en tirant gauche pied", "en tirant le pied gauche"),
    (r"vers le côté[ -]vers le bas", "vers le bas sur le côté"),
    (r"côté-vers le bas", "vers le bas sur le côté"),
    (r"l'avant-bras (droit|gauche) côté vers le bas",
     lambda m: f"l'avant-bras {m.group(1)} vers le bas sur le côté"),

    # « pique de doigts » : le dépôt dit « le bout des doigts »
    (r"avec la pique de doigts à plat (droit|gauche)",
     r"avec le bout des doigts \1 à plat"),
    (r"avec la pique à deux doigts (droit|gauche)",
     lambda m: "avec les deux doigts de la main "
               f"{'droite' if m.group(1) == 'droit' else 'gauche'}"),

    # article manquant
    (r"\bsur ligne ([A-H]{1,2})\b", r"sur la ligne \1"),

    # graphies
    (r"(?<!-)\bantihoraire\b", "anti-horaire"),
]

# --- corrections propres à une fiche -----------------------------------------
# (ancien, nouveau) ; l'ancien doit apparaître exactement une fois, sauf
# mention d'un nombre d'occurrences attendu.

PAR_FICHE = {
    "chon-ji.md": [],

    "do-san.md": [
        ("une pique moyenne vers D avec la pique de doigts droite droit.",
         "une pique moyenne vers D avec le bout des doigts droit."),
        ("Vriller le tranchant de la main droite conjointement avec le corps dans "
         "le sens anti-horaire jusqu'à ce que sa paume fait visage vers le bas puis "
         "déplacer le pied gauche",
         "Pivoter la main droite dans le sens anti-horaire jusqu'à ce que sa paume "
         "soit tournée vers le bas, puis déplacer le pied gauche"),
    ],

    "won-hyo.md": [
        ("vers B, à la même en exécutant un blocage de garde moyen",
         "vers B, tout en exécutant un blocage de garde moyen"),
    ],

    "joong-gun.md": [
        ("Vriller le poing gauche dans le sens anti-horaire jusqu'à ce que le revers "
         "du poing fait visage vers le bas, en même temps pour former une position de "
         "marche gauche vers E",
         "Pivoter le poing gauche dans le sens anti-horaire jusqu'à ce que son revers "
         "soit tourné vers le bas, tout en formant une position de marche gauche vers E"),
        ("Vriller le poing droit dans le sens horaire jusqu'à ce que le revers "
         "du poing fait visage vers le bas, en même temps pour former une position de "
         "marche droite vers F",
         "Pivoter le poing droit dans le sens horaire jusqu'à ce que son revers "
         "soit tourné vers le bas, tout en formant une position de marche droite vers F"),
    ],

    "toi-gye.md": [
        ("Étendre les deux mains vers le haut comme si vers saisir l'adversaire’s tête",
         "Étendre les deux mains vers le haut comme pour saisir la tête de l'adversaire"),
    ],

    # hwa-rang : « en un en glissant mouvement » est traité par les règles globales
    "hwa-rang.md": [],

    "choong-moo.md": [
        ("un piqué haut vers A avec le bout des doigts gauche à plat",
         "une pique haute vers A avec le bout des doigts gauche à plat"),
        ("un piqué bas vers C avec le piqué de doigts renversé droit",
         "une pique basse vers C avec le bout des doigts droit renversé"),
        ("un piqué moyen vers C avec le bout des doigts droit",
         "une pique moyenne vers C avec le bout des doigts droit"),
        # vouvoiement isolé ; le dépôt est à l'infinitif partout ailleurs
        # (« antihoraire » a déjà été normalisé par les règles globales)
        ("Sautez et pivotez dans le sens anti-horaire pour atterrir",
         "Sauter et pivoter dans le sens anti-horaire pour atterrir"),
    ],

    "ge-baek.md": [],

    "po-eun.md": [],

    "eui-am.md": [],

    "choong-jang.md": [
        ("comme si en saisissant l'adversaire’s jambe.",
         "comme pour saisir la jambe de l'adversaire."),
    ],

    "juche.md": [
        ("décide de tout; autrement dit", "décide de tout ; autrement dit"),
        ("une position fermée avec un ciel main vers D",
         "une position fermée avec les mains du ciel vers D"),
        ("orun joomuk dwijibo jirigi", "orun joomuk dwijibo jirugi"),
    ],

    "ko-dang.md": [
        ("Moa Chunbi Sogi C", "Moa Junbi Sogi C"),
    ],

    "sam-il.md": [],

    "yoo-sin.md": [],

    "choi-yong.md": [
        ("CHOOI-YONG est nommé", "CHOI-YONG est nommé"),
        ("sur la jambe droite vers D\n", "sur la jambe droite vers D.\n"),
        ("sur la jambe gauche vers C\n", "sur la jambe gauche vers C.\n"),
    ],

    "yon-gae.md": [
        ("# YONG-GAE", "# YON-GAE"),
        ("| YONG-GAE est nommé", "| YON-GAE est nommé"),
        ("[YONG-GAE](https://youtu.be/", "[YON-GAE](https://youtu.be/"),
        # « droit » y traduisait sun (rectiligne), pas le côté droit
        ("avec un jumelé droit avant-bras",
         "avec les deux avant-bras rectilignes"),  # 2 occurrences
    ],

    "ul-ji.md": [
        ("(guerrière d'usure)", "(guerre d'usure)"),
        ("une frappe horizontale avec jumelé côté poings",
         "une frappe horizontale avec les côtés des poings jumelés"),
        ("tout en piquant avec un jumelé côté coude",
         "tout en piquant latéralement avec les deux coudes"),
        ("une pique moyenne vers D avec la pique de doigts droite droit.",
         "une pique moyenne vers D avec le bout des doigts droit."),
    ],

    "moon-moo.md": [],

    "so-san.md": [
        ("Ramener la paume droite sur le devant du poing gauche puis vriller les dans "
         "le sens anti-horaire jusqu'à ce que le revers du poing gauche fait visage vers "
         "le bas tout en formant une position de marche gauche vers A, en glissant le "
         "pied gauche. exécuter en mouvement de relâchement.",
         "Amener la paume droite sur le devant du poing gauche, puis les pivoter dans "
         "le sens anti-horaire jusqu'à ce que le revers du poing gauche soit tourné vers "
         "le bas, tout en formant une position de marche gauche vers A, en glissant le "
         "pied gauche."),
        ("Ramener la paume gauche sur le devant du poing droit puis vriller les dans "
         "le sens horaire jusqu'à ce que le revers du poing droit fait visage vers "
         "le bas tout en formant une position de marche droite vers B, en glissant le "
         "pied droit. exécuter en mouvement de relâchement.",
         "Amener la paume gauche sur le devant du poing droit, puis les pivoter dans "
         "le sens horaire jusqu'à ce que le revers du poing droit soit tourné vers "
         "le bas, tout en formant une position de marche droite vers B, en glissant le "
         "pied droit."),
    ],

    "se-jong.md": [],

    "tong-il.md": [
        ("| ![**|**](../images/tong-il.png) |", "| ![**\\|**](../images/tong-il.png) |"),
        ("une double pique arrière du coude latérale",
         "une double pique latérale arrière du coude"),
    ],

    "saju-tulgi.md": [
        ('Position fermé "C"', "Position fermée « C »"),
        ("1. Pivot à 180° vers la gauche, reculer", "1. Pivoter à 180° vers la gauche, reculer"),
        ("5. Pivot à 180° vers la droite, reculer", "5. Pivoter à 180° vers la droite, reculer"),
    ],

    "dan-gun.md": [
        ("un blocage double des avant-bras vers F..", "un blocage double des avant-bras vers F."),
    ],
}

# notes à insérer après la ligne de lien du mouvement indiqué
NOTES = {
    "so-san.md": {18: "Exécuter en mouvement de relâchement.",
                  21: "Exécuter en mouvement de relâchement."},
}


def corriger_choong_moo(texte):
    """« posture » y remplace « position » partout, contre les 27 autres fiches."""
    # les en-têtes « Posture de départ » et la ligne FIN gardent le mot
    texte = re.sub(r"(?<!P)(?<!p)\bposture\b(?! de départ)", "position", texte)
    texte = texte.replace("1 posture de marche", "1 position de marche")
    # indentation des lignes de lien : 2 espaces au lieu de 3
    texte = re.sub(r"^  (\*\(\[)", r"   \1", texte, flags=re.M)
    return texte


PARTICULIERES = {"choong-moo.md": corriger_choong_moo}


def nettoyer(texte):
    """Corrections typographiques communes à toutes les fiches."""
    # double espace après les puces d'en-tête
    texte = re.sub(r"^(\* \*\*[^*]+ :\*\*)  +", r"\1 ", texte, flags=re.M)
    # ligne FIN : un point final partout
    texte = re.sub(r"^(### FIN : .*[^.\s])\s*$", r"\1.", texte, flags=re.M)
    return texte


def inserer_notes(texte, notes):
    lignes = texte.splitlines(keepends=True)
    sortie, i = [], 0
    while i < len(lignes):
        sortie.append(lignes[i])
        m = re.match(r"^(\d+)\.\s", lignes[i])
        if m and int(m.group(1)) in notes:
            n = int(m.group(1))
            note = f"   > *{notes[n]}*\n"
            # la ligne de lien suit le mouvement ; la note vient après
            if i + 1 < len(lignes) and lignes[i + 1].lstrip().startswith("*("):
                sortie.append(lignes[i + 1]); i += 1
            if note not in lignes[i:i + 2]:
                sortie.append(note)
        i += 1
    return "".join(sortie)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true", help="applique les corrections")
    args = p.parse_args()

    total, fiches_touchees, erreurs = 0, 0, []

    for fiche in sorted(TUL.glob("*.md")):
        if fiche.name == "README.md":
            continue
        avant = fiche.read_text(encoding="utf-8")
        texte, n = avant, 0

        for motif, remplacement in GLOBALES:
            texte, k = re.subn(motif, remplacement, texte)
            n += k

        for ancien, nouveau in PAR_FICHE.get(fiche.name, []):
            k = texte.count(ancien)
            if k == 0 and nouveau not in texte:
                # ni le motif ni son remplacement : le motif est périmé
                erreurs.append(f"{fiche.name} : introuvable — {ancien[:60]}…")
            texte = texte.replace(ancien, nouveau)
            n += k

        if fiche.name in PARTICULIERES:
            t2 = PARTICULIERES[fiche.name](texte)
            if t2 != texte:
                n += 1
            texte = t2

        if fiche.name in NOTES:
            t2 = inserer_notes(texte, NOTES[fiche.name])
            if t2 != texte:
                n += 1
            texte = t2

        t2 = nettoyer(texte)
        if t2 != texte:
            n += 1
        texte = t2

        if not texte.endswith("\n"):
            texte += "\n"
            n += 1

        if texte != avant:
            fiches_touchees += 1
            total += n
            print(f"{fiche.name:20s} {n:3d} correction(s)")
            if args.write:
                fiche.write_text(texte, encoding="utf-8")

    print(f"\n{total} correction(s) sur {fiches_touchees} fiche(s)")
    if erreurs:
        print("\nmotifs non trouvés :")
        for e in erreurs:
            print("  " + e)
    print("écriture : " + ("oui" if args.write else "non — relancer avec --write"))
    return 1 if erreurs else 0


if __name__ == "__main__":
    sys.exit(main())
