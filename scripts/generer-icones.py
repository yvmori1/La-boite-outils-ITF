#!/usr/bin/env python3
"""Dessine les icônes de l'application installable (écran d'accueil iPhone,
iPad et Android) dans docs/assets/icones/.

  python3 scripts/generer-icones.py            # ce qui serait écrit
  python3 scripts/generer-icones.py --write    # écrire les PNG

Demande Pillow (pip install pillow). Fond noir plein cadre (iOS arrondit
lui-même les coins), « ITF » en blanc au-dessus d'une ceinture rouge.
"""

import argparse
import pathlib

from PIL import Image, ImageDraw, ImageFont

RACINE = pathlib.Path(__file__).resolve().parents[1]
SORTIE = RACINE / "docs" / "assets" / "icones"
POLICE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TAILLES = {
    "apple-touch-icon.png": (180, 1.0),
    "icone-192.png": (192, 1.0),
    "icone-512.png": (512, 1.0),
    # « maskable » : Android peut rogner jusqu'à 20 % du bord
    "icone-512-masquable.png": (512, 0.8),
}


def dessiner(cote, echelle):
    grand = cote * 4  # dessin suréchantillonné puis réduit : bords lisses
    img = Image.new("RGB", (grand, grand), "#000000")
    d = ImageDraw.Draw(img)
    centre = grand / 2
    police = ImageFont.truetype(POLICE, int(grand * 0.36 * echelle))
    gauche, haut, droite, bas = d.textbbox((0, 0), "ITF", font=police)
    y_texte = centre - grand * 0.10 * echelle
    d.text((centre - (gauche + droite) / 2, y_texte - (haut + bas) / 2), "ITF",
           font=police, fill="#ffffff")
    # ceinture rouge
    largeur = grand * 0.70 * echelle
    epaisseur = grand * 0.075 * echelle
    y = centre + grand * 0.20 * echelle
    d.rectangle([centre - largeur / 2, y, centre + largeur / 2, y + epaisseur],
                fill="#d32f2f")
    return img.resize((cote, cote), Image.LANCZOS)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    for nom, (cote, echelle) in TAILLES.items():
        chemin = SORTIE / nom
        print(("écrit " if args.write else "écrirait ") + str(chemin.relative_to(RACINE)))
        if args.write:
            SORTIE.mkdir(parents=True, exist_ok=True)
            dessiner(cote, echelle).save(chemin, optimize=True)


if __name__ == "__main__":
    main()
