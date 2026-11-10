#!/usr/bin/env python3
"""Dérive du logo Hosinsul (images/logo/hosinsul.svg) les variantes et les
icônes du site.

  python3 scripts/generer-icones.py            # ce qui serait écrit
  python3 scripts/generer-icones.py --write    # écrire les fichiers

Demande cairosvg (pip install cairosvg). Le logo d'origine n'est jamais
modifié ; on écrit :

- images/logo/hosinsul-contour.svg : le logo entouré d'un liseré blanc. La
  plante du pied et le talon (gris très foncé) disparaissaient sur l'en-tête
  noir et sur le fond sombre du thème ; sur fond blanc le liseré ne se voit
  pas. C'est la version utilisée par le site (en-tête, accueil, impression).
- images/logo/hosinsul-orteils.svg : les cinq orteils seuls, dans un carré.
  Le logo entier est illisible à 16-32 px : c'est l'icône d'onglet (favicon).
- docs/assets/icones/*.png : favicon et icônes de l'application (écran
  d'accueil iPhone, iPad, Android) : le logo entier sur fond blanc.
"""

import argparse
import pathlib
import re

RACINE = pathlib.Path(__file__).resolve().parents[1]
LOGO = RACINE / "images" / "logo" / "hosinsul.svg"
CONTOUR = RACINE / "images" / "logo" / "hosinsul-contour.svg"
ORTEILS = RACINE / "images" / "logo" / "hosinsul-orteils.svg"
ICONES = RACINE / "docs" / "assets" / "icones"

LISERE = 5  # épaisseur du liseré blanc, en unités du logo (465 de large)

# Côté de l'icône, largeur du logo en part du côté. Icône « maskable » :
# Android peut rogner l'icône en cercle de 80 % du côté ; un logo de 0,74 de
# large (hauteur 0,28) y tient entier.
ICONES_LOGO = {
    "apple-touch-icon.png": (180, 0.90),
    "icone-192.png": (192, 0.90),
    "icone-512.png": (512, 0.90),
    "icone-512-masquable.png": (512, 0.74),
}
FAVICONS = {"favicon.png": 48}


def chemin(svg, classe):
    """Attribut d du premier <path> de cette classe."""
    m = re.search(r'<path class="%s" d="([^"]+)"' % classe, svg)
    if not m:
        raise SystemExit(f"{LOGO}: forme « {classe} » introuvable")
    return m.group(1)


def vue(svg):
    return [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]


def contour(svg):
    """Liseré blanc sous la plante (st2, déjà bordée de 8) et le talon (st1)."""
    marge = LISERE + 4
    x, y, l, h = vue(svg)
    halos = (
        f'\n  <g fill="#fff" stroke="#fff" stroke-linejoin="round">'
        f'\n    <path stroke-width="{8 + 2 * LISERE}" d="{chemin(svg, "st2")}"/>'
        f'\n    <path stroke-width="{2 * LISERE}" d="{chemin(svg, "st1")}"/>'
        f'\n  </g>'
    )
    svg = svg.replace("</defs>", "</defs>" + halos, 1)
    # largeur et hauteur propres (en px) : taille d'affichage par défaut, utile
    # à l'impression (assets/site.css) ; l'en-tête et l'accueil la fixent.
    l, h = l + 2 * marge, h + 2 * marge
    nouvelle = (f'width="{160:g}" height="{160 * h / l:.1f}" '
                f'viewBox="{x - marge:g} {y - marge:g} {l:g} {h:g}"')
    return re.sub(r'viewBox="[^"]+"', nouvelle, svg, count=1)


def boite(d):
    """Boîte englobante (points de contrôle compris) d'un chemin SVG fait de
    commandes M, L, H, V, C, S, Q, T, Z absolues ou relatives."""
    jetons = re.findall(r"[A-Za-z]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?", d)
    arite = {"M": 2, "L": 2, "T": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4}
    xs, ys, x, y, cmd, i = [], [], 0.0, 0.0, "M", 0
    while i < len(jetons):
        if jetons[i].isalpha():
            cmd = jetons[i]
            i += 1
            if cmd in "Zz":
                continue
        n = arite[cmd.upper()]
        v = [float(t) for t in jetons[i:i + n]]
        i += n
        rel = cmd.islower()
        if cmd.upper() == "H":
            x = x + v[0] if rel else v[0]
        elif cmd.upper() == "V":
            y = y + v[0] if rel else v[0]
        else:
            for j in range(0, n, 2):
                px, py = (x + v[j], y + v[j + 1]) if rel else (v[j], v[j + 1])
                xs.append(px)
                ys.append(py)
            x, y = px, py
        xs.append(x)
        ys.append(y)
        if cmd == "M":
            cmd = "L"
        elif cmd == "m":
            cmd = "l"
    return min(xs), min(ys), max(xs), max(ys)


# Grossissement de chaque orteil pour l'icône d'onglet : à 16-32 px les quatre
# petits orteils ne feraient que 2 à 4 pixels. Chacun grossit autour de son
# centre, sans se déplacer ni toucher son voisin.
GROSSISSEMENT = {"st1": 1.0, "st5": 1.25, "st0": 1.3, "st4": 1.35, "st6": 1.35}


def orteils(svg):
    """Les cinq orteils (talon compris), grossis, centrés dans un carré."""
    styles = re.search(r"<defs>.*?</defs>", svg, re.S).group(0)
    corps, halo, bords = [], "", []
    for c, k in GROSSISSEMENT.items():
        d = chemin(svg, c)
        x0, y0, x1, y1 = boite(d)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        bords.append((cx - (cx - x0) * k, cy - (cy - y0) * k, cx + (x1 - cx) * k, cy + (y1 - cy) * k))
        t = f"translate({cx:.2f} {cy:.2f}) scale({k:g}) translate({-cx:.2f} {-cy:.2f})"
        corps.append(f'  <path class="{c}" transform="{t}" d="{d}"/>')
        if c == "st1":  # liseré blanc du talon, visible sur un onglet sombre
            halo = (f'  <path fill="#fff" stroke="#fff" stroke-width="{2 * LISERE / k:g}" '
                    f'transform="{t}" d="{d}"/>')
    x0 = min(b[0] for b in bords) - LISERE
    y0 = min(b[1] for b in bords) - LISERE
    x1 = max(b[2] for b in bords) + LISERE
    y1 = max(b[3] for b in bords) + LISERE
    cote = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    corps = "\n".join(corps)
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
        f'viewBox="{cx - cote / 2:.2f} {cy - cote / 2:.2f} {cote:.2f} {cote:.2f}">\n'
        f'  <!-- Orteils du logo Hosinsul, grossis pour l\'icône d\'onglet '
        f'(scripts/generer-icones.py) -->\n'
        f'  {styles}\n{halo}\n{corps}\n</svg>\n'
    )


def icone(svg, cote, part, fond="#ffffff"):
    import cairosvg

    x, y, l, h = vue(svg)
    largeur = cote * part
    hauteur = largeur * h / l
    image = cairosvg.svg2png(bytestring=svg.encode(), output_width=round(largeur),
                             output_height=round(hauteur))
    # centrer sur un carré de fond plein (iOS arrondit lui-même les coins)
    import io
    from PIL import Image

    carre = Image.new("RGBA", (cote, cote), fond)
    logo = Image.open(io.BytesIO(image)).convert("RGBA")
    carre.alpha_composite(logo, ((cote - logo.width) // 2, (cote - logo.height) // 2))
    sortie = io.BytesIO()
    carre.convert("RGB").save(sortie, "PNG", optimize=True)
    return sortie.getvalue()


def favicon(svg, cote):
    import cairosvg

    return cairosvg.svg2png(bytestring=svg.encode(), output_width=cote, output_height=cote)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    logo = LOGO.read_text(encoding="utf-8")
    svg_contour = contour(logo)
    svg_orteils = orteils(logo)
    sorties = {CONTOUR: svg_contour.encode(), ORTEILS: svg_orteils.encode()}
    for nom, (cote, part) in ICONES_LOGO.items():
        sorties[ICONES / nom] = lambda c=cote, p=part: icone(svg_contour, c, p)
    for nom, cote in FAVICONS.items():
        sorties[ICONES / nom] = lambda c=cote: favicon(svg_orteils, c)
    for fichier, contenu in sorties.items():
        print(("écrit " if args.write else "écrirait ") + str(fichier.relative_to(RACINE)))
        if args.write:
            fichier.parent.mkdir(parents=True, exist_ok=True)
            fichier.write_bytes(contenu() if callable(contenu) else contenu)


if __name__ == "__main__":
    main()
