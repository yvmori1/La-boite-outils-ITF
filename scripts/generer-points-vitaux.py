#!/usr/bin/env python3
"""Génère les planches des 49 points vitaux (Kupso) de Combat/points-vitaux.md.

  python3 scripts/generer-points-vitaux.py            # liste ce qui serait écrit
  python3 scripts/generer-points-vitaux.py --write    # écrit images/points-vitaux/*.svg

Trois planches SVG : la tête de profil (agrandie), le corps de face et le
corps de dos. Les numéros et les noms sont ceux du tableau de la page, eux-mêmes
repris de l'Encyclopédie (1999), p. 108-111. Chaque point est placé là où les
croquis de l'Encyclopédie le montrent ; un point qui a deux côtés (rein, creux
du genou...) n'est marqué qu'une fois.

Aucune dépendance : le SVG est écrit à la main.
"""

import argparse
import pathlib
import re

RACINE = pathlib.Path(__file__).resolve().parent.parent
PAGE = RACINE / "Combat" / "points-vitaux.md"
SORTIE = RACINE / "images" / "points-vitaux"

LARGEUR = 780
COL = 200          # largeur d'une colonne d'étiquettes
ECART = 36         # écart vertical minimal entre deux étiquettes (2 lignes)
ENCRE = "#222"
ROUGE = "#c62828"


def lire_points():
    """{numéro: (nom court, terme coréen)} depuis le tableau de la page."""
    ligne = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*\*([^*]+)\*\s*\|")
    points = {}
    for l in PAGE.read_text(encoding="utf-8").splitlines():
        m = ligne.match(l)
        if m:
            nom = m.group(2).split(",")[0].split(" (")[0].strip()
            points[int(m.group(1))] = (nom, m.group(3).strip())
    if sorted(points) != list(range(1, 50)):
        raise SystemExit(f"{PAGE} : tableau des 49 points introuvable ou incomplet")
    return points


# --- Tracés -----------------------------------------------------------------

def lisse(pts, ferme=True):
    """Chemin SVG lissé (Catmull-Rom vers Bézier) passant par les points."""
    n = len(pts)
    d = [f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"]
    fin = n if ferme else n - 1
    for i in range(fin):
        p0 = pts[(i - 1) % n] if (ferme or i > 0) else pts[i]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (ferme or i + 2 < n) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}")
    return "".join(d) + ("Z" if ferme else "")


# Moitié droite (côté droit de l'image) du corps, bras légèrement écartés,
# paumes vers l'avant ; du cou jusqu'à l'entrejambe. x = 0 sur l'axe du corps.
DEMI_CORPS = [
    (16, 128), (19, 160), (40, 172), (66, 180), (86, 192), (98, 218),
    (104, 260), (108, 310), (116, 372), (128, 430), (140, 488),
    (150, 506), (160, 532), (162, 566), (154, 596), (142, 604),
    (132, 590), (128, 560), (122, 532), (120, 500),
    (108, 440), (94, 380), (84, 320), (76, 262),
    (72, 300), (64, 360), (66, 400), (76, 440), (80, 490), (78, 550),
    (68, 620), (66, 690), (54, 772), (58, 796), (74, 812), (72, 826),
    (40, 828), (22, 820), (22, 790), (24, 770), (18, 690), (14, 620),
    (10, 540), (3, 494),
]


def silhouette(cx, haut):
    """Contour complet (tête à part) centré en cx, décalé de haut."""
    droite = [(cx + x, haut + y) for x, y in DEMI_CORPS]
    gauche = [(cx - x, haut + y) for x, y in reversed(DEMI_CORPS)]
    return lisse(droite + gauche)


def trait(d, epais=2.2, extra=""):
    return (f'<path d="{d}" fill="none" stroke="{ENCRE}" stroke-width="{epais}" '
            f'stroke-linecap="round" stroke-linejoin="round"{extra}/>')


def courbe(*pts, epais=1.4):
    return trait(lisse(list(pts), ferme=False), epais)


def corps(cx, haut, dos=False):
    s = []
    peau = 'fill="#fff"'
    s.append(f'<path d="{silhouette(cx, haut)}" {peau} stroke="{ENCRE}" '
             'stroke-width="2.2" stroke-linejoin="round"/>')
    s.append(f'<ellipse cx="{cx}" cy="{haut + 82}" rx="36" ry="48" {peau} '
             f'stroke="{ENCRE}" stroke-width="2.2"/>')
    for sx in (-1, 1):   # oreilles
        s.append(f'<ellipse cx="{cx + sx * 37}" cy="{haut + 86}" rx="6" ry="12" '
                 f'{peau} stroke="{ENCRE}" stroke-width="1.6"/>')
    y = lambda v: haut + v
    if not dos:
        # visage, clavicules, pectoraux, nombril, short
        s.append(courbe((cx - 16, y(76)), (cx - 10, y(73)), (cx - 4, y(76))))
        s.append(courbe((cx + 4, y(76)), (cx + 10, y(73)), (cx + 16, y(76))))
        s.append(courbe((cx, y(80)), (cx - 4, y(96)), (cx + 2, y(98))))
        s.append(courbe((cx - 9, y(112)), (cx, y(115)), (cx + 9, y(112))))
        for sx in (-1, 1):
            s.append(courbe((cx + sx * 6, y(174)), (cx + sx * 30, y(170)), (cx + sx * 58, y(180))))
            s.append(courbe((cx + sx * 8, y(250)), (cx + sx * 34, y(258)), (cx + sx * 58, y(240))))
        s.append(f'<circle cx="{cx}" cy="{y(392)}" r="2.5" fill="{ENCRE}"/>')
    else:
        # cheveux, omoplates, colonne, short
        s.append(courbe((cx - 34, y(70)), (cx, y(58)), (cx + 34, y(70)), epais=1.2))
        for sx in (-1, 1):
            s.append(courbe((cx + sx * 20, y(200)), (cx + sx * 50, y(214)),
                            (cx + sx * 46, y(262)), (cx + sx * 24, y(276))))
            s.append(courbe((cx + sx * 34, y(776)), (cx + sx * 38, y(800)), epais=1.2))
        s.append(courbe((cx, y(200)), (cx, y(300)), (cx, y(420)), epais=1.0))
    # short (comme les croquis de l'Encyclopédie)
    s.append(trait(lisse([(cx - 70, y(428)), (cx, y(436)), (cx + 70, y(428))], False), 2))
    for sx in (-1, 1):
        s.append(trait(lisse([(cx + sx * 79, y(500)), (cx + sx * 40, y(506)),
                              (cx + sx * 6, y(500))], False), 2))
    if dos:
        s.append(courbe((cx, y(470)), (cx, y(494)), epais=1.4))
    return "\n".join(s)


# Tête de profil (vers la droite), agrandie.
PROFIL = [
    (-58, 395), (-52, 330), (-58, 278), (-82, 236), (-104, 190), (-110, 140),
    (-96, 80), (-60, 38), (-10, 18), (40, 24), (78, 54), (96, 96),
    (100, 124), (96, 140), (106, 160), (122, 186), (126, 198), (112, 204),
    (110, 218), (116, 228), (106, 236), (114, 248), (104, 258), (112, 272),
    (106, 290), (82, 300), (58, 306), (60, 322), (66, 336), (58, 352), (56, 395),
]


def tete(cx, haut):
    p = lambda x, y: (cx + x, haut + y)
    s = [f'<path d="{lisse([p(*q) for q in PROFIL], ferme=False)}" fill="#fff" '
         f'stroke="{ENCRE}" stroke-width="2.4" stroke-linejoin="round"/>']
    s.append(trait(f"M{p(-58, 395)[0]},{p(0, 395)[1]} L{p(56, 395)[0]},{p(0, 395)[1]}",
                   1.2, ' stroke-dasharray="4 5"'))
    # oreille, oeil, sourcil, bouche, mâchoire, cheveux
    s.append(f'<ellipse cx="{p(-22, 0)[0]}" cy="{p(0, 172)[1]}" rx="17" ry="30" '
             f'fill="#fff" stroke="{ENCRE}" stroke-width="2"/>')
    s.append(courbe(p(-26, 156), p(-16, 168), p(-24, 186), epais=1.2))
    s.append(courbe(p(60, 146), p(72, 140), p(84, 146)))
    s.append(courbe(p(60, 146), p(72, 152), p(84, 146)))
    s.append(courbe(p(56, 128), p(74, 122), p(92, 128), epais=2))
    s.append(courbe(p(92, 234), p(108, 233), epais=1.6))
    s.append(courbe(p(-8, 212), p(-6, 250), p(10, 270), p(60, 284), p(100, 280), epais=1.3))
    s.append(courbe(p(80, 74), p(30, 62), p(-30, 80), p(-62, 150), epais=1.2))
    return "\n".join(s)


# --- Planches ---------------------------------------------------------------
# (numéro, x, y, côté des étiquettes) ; x, y relatifs au repère du dessin.

FACE = [
    (20, -88, 206, "G"), (15, 34, 177, "D"), (23, 0, 214, "D"), (45, -76, 262, "G"),
    (24, 20, 262, "D"), (25, 0, 286, "G"), (27, -38, 318, "G"), (28, 0, 324, "D"),
    (26, 40, 316, "D"), (46, -66, 358, "G"), (29, 0, 392, "D"), (30, 0, 418, "G"),
    (31, 0, 448, "D"), (32, -30, 466, "G"), (33, 0, 486, "D"),
    (17, -144, 490, "G"), (19, 132, 496, "D"), (16, -152, 528, "G"),
    (48, 16, 548, "D"), (47, -68, 620, "G"), (49, -38, 700, "G"), (34, 46, 800, "D"),
]

DOS = [
    (35, 0, 94, "D"), (36, 0, 146, "G"), (37, 0, 226, "D"), (38, 0, 300, "G"),
    (39, 36, 342, "D"), (44, -105, 372, "G"), (40, 0, 474, "D"),
    (18, 134, 494, "D"), (41, -40, 616, "G"), (42, -36, 758, "G"), (43, 50, 784, "D"),
]

TETE = [
    (1, -26, 18, "G"), (2, 46, 120, "D"), (3, 98, 136, "D"), (4, 72, 147, "D"),
    (21, 112, 172, "D"), (5, -30, 214, "G"), (6, 6, 186, "G"), (7, 109, 212, "D"),
    (10, 113, 234, "D"), (11, -6, 262, "G"), (8, 50, 272, "G"), (9, 110, 274, "D"),
    (12, 14, 300, "G"), (22, 30, 334, "G"), (13, 64, 334, "D"), (14, 57, 368, "D"),
]


def repartit(ys, haut, bas):
    """Étale les étiquettes : ordre conservé, écart minimal ECART."""
    out = []
    for y in ys:
        out.append(max(y, (out[-1] + ECART) if out else haut))
    depasse = out[-1] - bas if out else 0
    if depasse > 0:
        for i in range(len(out) - 1, -1, -1):
            limite = bas if i == len(out) - 1 else out[i + 1] - ECART
            out[i] = min(out[i], limite)
    return out


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace("'", "&#39;")


def planche(titre, dessin, marques, points, hauteur, cx, oy):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LARGEUR} {hauteur}" '
         f'width="{LARGEUR}" height="{hauteur}" font-family="Helvetica, Arial, sans-serif">',
         f"<title>{esc(titre)}</title>",
         f'<rect width="{LARGEUR}" height="{hauteur}" fill="#fff"/>',
         f'<text x="{LARGEUR / 2}" y="30" text-anchor="middle" font-size="20" '
         f'font-weight="bold" fill="{ENCRE}">{esc(titre)}</text>',
         dessin]
    lignes, textes = [], []
    for cote in "GD":
        sel = sorted((m for m in marques if m[3] == cote), key=lambda m: m[2])
        ys = repartit([oy + m[2] for m in sel], 60, hauteur - 24)
        for (num, x, y, _), ly in zip(sel, ys):
            px, py = cx + x, oy + y
            nom, coreen = points[num]
            if cote == "G":
                tx, ancre, bout = COL - 6, "end", COL
            else:
                tx, ancre, bout = LARGEUR - COL + 6, "start", LARGEUR - COL
            coude = bout + (14 if cote == "G" else -14)
            lignes.append(f'<polyline points="{bout},{ly} {coude},{ly} {px},{py}" '
                          f'fill="none" stroke="#888" stroke-width="1"/>')
            lignes.append(f'<circle cx="{px}" cy="{py}" r="5" fill="#fff" '
                          f'stroke="{ROUGE}" stroke-width="2.4"/>')
            textes.append(
                f'<text x="{tx}" y="{ly - 3}" text-anchor="{ancre}" font-size="13" '
                f'fill="{ENCRE}"><tspan font-weight="bold" fill="{ROUGE}">{num}</tspan> '
                f'{esc(nom)}</text>'
                f'<text x="{tx}" y="{ly + 12}" text-anchor="{ancre}" font-size="11.5" '
                f'font-style="italic" fill="#555">{esc(coreen)}</text>')
    s += lignes + textes + ["</svg>"]
    return "\n".join(s) + "\n"


def planches():
    pts = lire_points()
    places = sorted(m[0] for m in FACE + DOS + TETE)
    if places != list(range(1, 50)):
        raise SystemExit("chaque point vital doit être placé une et une seule fois")
    cx = LARGEUR / 2
    return {
        "tete-profil.svg": planche("Tête et cou, de profil", tete(cx - 10, 50),
                                   TETE, pts, 470, cx - 10, 50),
        "face.svg": planche("Face avant", corps(cx, 50), FACE, pts, 900, cx, 50),
        "dos.svg": planche("Face arrière", corps(cx, 50, dos=True), DOS, pts, 900, cx, 50),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true", help="écrit les fichiers")
    args = ap.parse_args()
    for nom, contenu in planches().items():
        f = SORTIE / nom
        if f.exists() and f.read_text(encoding="utf-8") == contenu:
            continue
        print(f"{'écrit' if args.write else 'à écrire'} : {f.relative_to(RACINE)}")
        if args.write:
            SORTIE.mkdir(parents=True, exist_ok=True)
            f.write_text(contenu, encoding="utf-8")


if __name__ == "__main__":
    main()
