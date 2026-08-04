#!/usr/bin/env python3
"""Génère les schémas d'alignement des pieds des positions (Sogi).

  python3 scripts/generer-sogi.py            # liste ce qui serait écrit
  python3 scripts/generer-sogi.py --write    # écrit images/sogi/*.png
  python3 scripts/generer-sogi.py --write --only gunnun-sogi

Chaque position est décrite par ses mesures réelles, en centimètres, telles que
définies dans Theorie/grammaire-itf.md : largeur d'épaule 47 cm, pied standard
25 x 9 cm. Les pieds sont posés par un point de repère nommé (talon, gros
orteil, centre, bord interne...), jamais à l'œil : deux pieds « collés » se
touchent donc exactement, sans se chevaucher.

Le contour de pied est repris des tracés vectoriels de images/gojung-sogi.svg,
pour que les schémas générés restent cohérents avec les schémas existants.

Dépendance : matplotlib (pip install matplotlib).
"""

import argparse
import math
import pathlib
import re
import sys

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    from matplotlib.transforms import Affine2D
except ImportError:  # pragma: no cover
    sys.exit("matplotlib est requis : pip install matplotlib")

RACINE = pathlib.Path(__file__).resolve().parents[1]
SORTIE = RACINE / "images" / "sogi"

# ---------------------------------------------------------------- mesures ---

EPAULE = 47.0          # largeur d'épaule standard (cm)
EPAULE_15 = 70.5       # une largeur et demie d'épaule
PIED_L = 25.0          # longueur de pied standard
PIED_l = 9.0           # largeur de pied standard

# Toute longueur et toute largeur se disent en largeurs d'épaule, jamais en
# centimètres : c'est ainsi que la position s'enseigne et se corrige.
L_EPAULE = "1 largeur d'épaule"
L_EPAULE_15 = "1 largeur 1/2 d'épaule"
L_NACHUO = "1 largeur 1/2 d'épaule\n+ 1 longueur de pied"

# ------------------------------------------------------------------ style ---

NOIR = "#000000"
COTE = "#C55A11"       # cotes et angles (orange du corpus existant)
GRIS = "#8A8A8A"       # appui partiel ou pied en l'air

TAILLE_PX = 350        # les schémas sont carrés, 350 x 350 pixels
DPI = 100
MARGE = 0.04           # marge, en fraction du côté

T_TITRE = 8.0          # tailles de police, en points sur la vignette
T_SOUS = 5.5
T_COTE = 6.0
T_NOTE = 5.5

# ------------------------------------------------- contour de pied (droit) ---

# Tracés repris de images/gojung-sogi.svg : plante, gros orteil, puis les
# quatre autres orteils. Repère SVG (y vers le bas), pied pointant vers le haut.
CONTOURS = [
    "M102.846 261.417C113.152 234.004 112.079 219.481 115.486 202.315 120.542 176.844 120.385 179.218 126.567 162.846 138.623 130.919 138.758 123.15 139.592 113.66 140.758 100.437 138.233 94.4123 134.004 88.3639 128.556 80.5716 123.651 77.3053 117.235 73.4616 111.84 70.2304 84.1353 48.9764 66.6375 48.9939 36.5121 49.0172 35.1123 57.1828 30.9128 60.9157 26.3109 65.0102 22.333 73.7591 24.3803 86.5791 27.0749 103.441 46.0776 132.54 47.3374 160.712 48.6847 190.959 48.8422 186.952 47.4774 204.398 46.3109 219.329 43.6045 221.977 45.261 239.393 46.6608 254.091 44.8527 257.801 54.8265 272.178 61.1432 281.289 76.9437 280.945 76.9437 280.945 76.9437 280.945 96.6929 277.795 102.846 261.417Z",
    "M43.0154 1.63313C60.4199-0.192476 65.156 21.8489 62.6421 44.4678 50.277 44.0011 31.8285 46.0951 22.8288 68.5914 16.5296 49.2272 19.4517 4.11198 43.0154 1.63313ZM62.6421 44.4678C50.277 44.0011 39.0784 47.2674 25.0802 59.6325 18.781 40.2683 68.9414 23.7037 62.6421 44.4678Z",
    "M88.7722 50.767C78.7401 46.5675 77.107 44.7011 68.9414 44.4678 62.6421 25.1035 72.0968 9.99708 79.8075 10.1662 88.6555 10.3645 95.0714 30.0029 88.7722 50.767ZM88.7722 50.767C78.7401 46.5675 77.107 44.7011 68.9414 44.4678 62.6421 25.1035 71.741 16.238 79.44 16.7046 87.594 17.2003 95.0714 30.0029 88.7722 50.767Z",
    "M95.363 54.9839C93.6133 44.7769 95.4622 26.7891 105.232 26.935 115.783 27.0924 112.569 51.5952 108.737 62.4263 105.704 61.2598 99.93 57.4103 95.363 54.9839Z",
    "M114.651 66.095C113.817 56.9262 114.22 40.2041 123.36 40.7874 134.342 41.4931 131.041 65.0918 126.083 74.6165 122.776 71.4085 119.218 68.5214 114.651 66.095Z",
    "M131.624 80.7932C130.458 74.2782 131.7 59.5217 139.399 59.9883 147.553 60.4841 147.524 79.8192 138.425 87.9848 136.384 85.9434 135.363 83.6104 131.624 80.7932Z",
]

_JETON = re.compile(r"[MmCcLlZz]|-?\d*\.?\d+(?:[eE][-+]?\d+)?")


def _parser_svg(d):
    """Sous-ensemble de la syntaxe « path » SVG (M, L, C, Z absolus).

    Renvoie un Path matplotlib en coordonnées mathématiques (y vers le haut).
    """
    jetons = _JETON.findall(d)
    sommets, codes = [], []
    i, cmd = 0, None
    while i < len(jetons):
        j = jetons[i]
        if j.isalpha():
            cmd = j
            i += 1
            if cmd in "Zz":
                sommets.append((0.0, 0.0))
                codes.append(Path.CLOSEPOLY)
                continue
        n = {"M": 2, "L": 2, "C": 6}[cmd.upper()]
        v = [float(x) for x in jetons[i:i + n]]
        i += n
        pts = [(v[k], -v[k + 1]) for k in range(0, n, 2)]
        sommets += pts
        if cmd.upper() == "M":
            codes += [Path.MOVETO]
            cmd = "L"          # les paires suivantes d'un M sont des L
        elif cmd.upper() == "L":
            codes += [Path.LINETO]
        else:
            codes += [Path.CURVE4] * 3
    return Path(sommets, codes)


def _points(path):
    """Sommets du tracé aplati, hors sommets fictifs de fermeture."""
    plat = path.cleaned(curves=False)
    return [tuple(p) for p, c in zip(plat.vertices, plat.codes)
            if c in (Path.MOVETO, Path.LINETO)]


def _normaliser(bruts):
    """Met les tracés à l'échelle réelle : talon à l'origine, pied vers +y.

    Le pied mesure exactement PIED_L de long et PIED_l de large, ce qui rend
    lisibles les cotes prises sur les bords (« bords extérieurs », « collés »).
    """
    tous = [p for c in bruts for p in _points(c)]
    xs, ys = [p[0] for p in tous], [p[1] for p in tous]
    sx, sy = PIED_l / (max(xs) - min(xs)), PIED_L / (max(ys) - min(ys))
    talon = [p for p in tous if p[1] < min(ys) + 0.05 * (max(ys) - min(ys))]
    cx = (min(p[0] for p in talon) + max(p[0] for p in talon)) / 2
    t = Affine2D().translate(-cx, -min(ys)).scale(sx, sy)
    return [c.transformed(t) for c in bruts]


PIED = _normaliser([_parser_svg(d) for d in CONTOURS])


def _reperes(contours):
    """Points de repère du pied droit, en cm, talon centré à l'origine."""
    tous = [p for c in contours for p in _points(c)]
    plante = _points(contours[0])
    gros = _points(contours[1])
    petit = _points(contours[-1])
    xmin, xmax = min(p[0] for p in tous), max(p[0] for p in tous)
    bas = [p for p in plante if p[1] < 3.5]      # arrondi du talon
    return {
        "talon": (0.0, 0.0),
        "talon-interne": (min(p[0] for p in bas), 0.0),
        "talon-externe": (max(p[0] for p in bas), 0.0),
        "interne": (xmin, 0.0),                  # bord interne, au talon
        "externe": (xmax, 0.0),
        "centre": ((xmin + xmax) / 2, PIED_L / 2),
        "gros-orteil": max(gros, key=lambda p: p[1]),
        "petit-orteil": max(petit, key=lambda p: p[1]),
        "orteils": max(tous, key=lambda p: p[1]),
        "plante-avant": ((xmin + xmax) / 2, 0.72 * PIED_L),
    }


REPERES = _reperes(PIED)

# ------------------------------------------------------------------ scène ---


class Pied:
    """Un pied posé : côté, point de repère, position et orientation.

    `angle` est en degrés, sens trigonométrique, 0 = orteils vers l'avant (+y).
    La rotation se fait autour du repère d'ancrage, ce qui garantit que le
    point coté (talon, gros orteil...) tombe exactement où il est demandé.
    """

    def __init__(self, cote, at=(0.0, 0.0), angle=0.0, repere="talon",
                 appui="plein"):
        self.cote, self.appui = cote, appui
        ax, ay = REPERES[repere]
        if cote == "G":
            ax = -ax
        t = Affine2D()
        if cote == "G":
            t.scale(-1, 1)
        self.tr = t.translate(-ax, -ay).rotate_deg(angle).translate(*at)
        self.angle = angle

    def rp(self, nom):
        """Position réelle d'un repère de ce pied."""
        x, y = REPERES[nom]
        if self.cote == "G":
            x = -x
        return tuple(self.tr.transform_point((x, y)))

    def decaler(self, dx, dy):
        self.tr = self.tr.frozen().translate(dx, dy)
        return self

    def points(self):
        return [tuple(p) for c in PIED for p in _points(c.transformed(self.tr))]

    def dessiner(self, ax):
        style = {
            "plein": dict(fc=NOIR, ec="none", lw=0),
            "plante": dict(fc="none", ec=NOIR, lw=1.3),      # appui sur la plante
            "leve": dict(fc="none", ec=GRIS, lw=1.2, ls=(0, (4, 3))),
        }[self.appui]
        for c in PIED:
            ax.add_patch(PathPatch(c, transform=self.tr + ax.transData,
                                   zorder=2, **style))


class Scene:
    """Accumule les tracés, puis les rend sur une vignette carrée.

    Les textes ont une taille fixe en points sur la vignette : leur
    encombrement en centimètres dépend donc du cadrage, qu'ils élargissent à
    leur tour. Le cadre est trouvé par quelques itérations dans `rendre`.
    """

    def __init__(self, titre, sous_titre=None):
        self.titre, self.sous_titre = titre, sous_titre
        self.pieds, self.ops, self.pts, self.textes = [], [], [], []

    # -- pieds --------------------------------------------------------------
    def pied(self, cote, **kw):
        p = Pied(cote, **kw)
        self.pieds.append(p)
        return p

    # -- cotes et repères ---------------------------------------------------
    def _borner(self, *pts):
        self.pts.extend(pts)

    def _borner_texte(self, xy, texte, taille, ha="center", va="center"):
        """Note un texte à prendre en compte au cadrage."""
        self.textes.append((xy, texte, taille, ha, va))

    @staticmethod
    def _coins(entree, cm_pt):
        """Coins de l'encombrement d'un texte, en cm, pour un cadrage donné.

        On majore un peu la largeur des caractères pour ne rien rogner.
        """
        (x, y), texte, taille, ha, va = entree
        lignes = texte.split("\n")
        w = max(len(l) for l in lignes) * 0.58 * taille * cm_pt
        h = len(lignes) * 1.25 * taille * cm_pt
        x0 = {"center": x - w / 2, "left": x, "right": x - w}[ha]
        y0 = {"center": y - h / 2, "bottom": y, "top": y - h}[va]
        return [(x0, y0), (x0 + w, y0 + h)]

    def cote_v(self, x, y0, y1, texte, ext=None, cote_texte="droite"):
        """Cote verticale entre y0 et y1, avec lignes d'attache facultatives."""
        self._borner((x, y0), (x, y1))
        dx = 3.0 if cote_texte == "droite" else -3.0
        ha = "left" if cote_texte == "droite" else "right"
        self._borner_texte((x + dx, (y0 + y1) / 2), texte, T_COTE, ha, "center")

        def op(ax):
            ax.annotate("", xy=(x, y1), xytext=(x, y0),
                        arrowprops=dict(arrowstyle="<->", ls="--", lw=1.1,
                                        color=COTE, shrinkA=0, shrinkB=0))
            if ext:
                for y in (y0, y1):
                    ax.plot([ext[0], ext[1]], [y, y], color=COTE, lw=0.9,
                            zorder=1)
            ax.text(x + dx, (y0 + y1) / 2, texte, color=COTE, fontsize=T_COTE,
                    ha=ha, va="center")
        self.ops.append(op)

    def cote_h(self, y, x0, x1, texte, ext=None, dessous=False):
        """Cote horizontale entre x0 et x1."""
        self._borner((x0, y), (x1, y))
        self._borner_texte(((x0 + x1) / 2, y + (-2.5 if dessous else 2.5)), texte,
                           T_COTE, "center", "top" if dessous else "bottom")

        def op(ax):
            ax.annotate("", xy=(x1, y), xytext=(x0, y),
                        arrowprops=dict(arrowstyle="<->", ls="--", lw=1.1,
                                        color=COTE, shrinkA=0, shrinkB=0))
            if ext:
                for x in (x0, x1):
                    ax.plot([x, x], [ext[0], ext[1]], color=COTE, lw=0.9,
                            zorder=1)
            ax.text((x0 + x1) / 2, y + (-2.5 if dessous else 2.5), texte,
                    color=COTE, fontsize=T_COTE, ha="center",
                    va="top" if dessous else "bottom")
        self.ops.append(op)

    def angle(self, centre, a0, a1, r, texte, rayons=None):
        """Arc coté entre deux directions (degrés, sens trigonométrique)."""
        cx, cy = centre
        rr = rayons or r
        for a in (a0, a1):
            self._borner((cx + rr * math.cos(math.radians(a)),
                          cy + rr * math.sin(math.radians(a))))
        am = math.radians((a0 + a1) / 2)
        self._borner_texte((cx + (r + 2) * math.cos(am), cy + (r + 2) * math.sin(am)),
                           texte, T_COTE)

        def op(ax):
            for a in (a0, a1):
                ar = math.radians(a)
                ax.plot([cx, cx + rr * math.cos(ar)], [cy, cy + rr * math.sin(ar)],
                        color=COTE, lw=0.9, ls=(0, (4, 4)), zorder=1)
            ts = [math.radians(a0 + (a1 - a0) * k / 72) for k in range(73)]
            ax.plot([cx + r * math.cos(t) for t in ts],
                    [cy + r * math.sin(t) for t in ts], color=COTE, lw=1.2,
                    zorder=3)
            ax.text(cx + (r + 2) * math.cos(am), cy + (r + 2) * math.sin(am),
                    texte, color=COTE, fontsize=T_COTE, ha="center", va="center")
        self.ops.append(op)

    def ligne(self, p0, p1, couleur=COTE):
        self._borner(p0, p1)
        self.ops.append(lambda ax: ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                                           color=couleur, lw=0.9,
                                           ls=(0, (4, 4)), zorder=1))

    def texte(self, xy, texte, couleur=NOIR, taille=T_NOTE, ha="center",
              va="center"):
        self._borner_texte(xy, texte, taille, ha, va)
        self.ops.append(lambda ax: ax.text(xy[0], xy[1], texte, color=couleur,
                                           fontsize=taille, ha=ha, va=va,
                                           zorder=4))

    def note(self, xy, xytext, texte, courbe=0.25):
        self._borner(xy)
        self._borner_texte(xytext, texte, T_NOTE)
        self.ops.append(lambda ax: ax.annotate(
            texte, xy=xy, xytext=xytext, fontsize=T_NOTE, color=NOIR,
            ha="center", va="center",
            arrowprops=dict(arrowstyle="->", color=NOIR, lw=0.9,
                            connectionstyle="arc3,rad=%s" % courbe)))

    def poids(self, pied, texte):
        """Répartition du poids, posée hors de l'empreinte, du côté du pied."""
        pts = pied.points()
        ymin = min(p[1] for p in pts)
        if pied.cote == "G":
            x, ha = min(p[0] for p in pts) - 1.5, "right"
        else:
            x, ha = max(p[0] for p in pts) + 1.5, "left"
        self.texte((x, ymin - 2.0), texte, taille=T_COTE, ha=ha, va="top")

    # -- rendu --------------------------------------------------------------
    def _titres(self, geo, cm_pt):
        """Titre et sous-titre, empilés au-dessus de tout le reste.

        Le calcul part du dessin et de ses légendes, jamais des titres
        eux-mêmes : sans quoi le bloc de titre s'éloignerait à chaque itération.
        """
        pts = list(geo)
        for e in self.textes:
            pts += self._coins(e, cm_pt)
        cx = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2
        y = max(p[1] for p in pts) + 0.05 * (max(p[1] for p in pts)
                                             - min(p[1] for p in pts))
        entrees = []
        if self.sous_titre:
            entrees.append(((cx, y), self.sous_titre, T_SOUS, "center", "bottom"))
            y += 1.6 * T_SOUS * cm_pt
        entrees.append(((cx, y), self.titre, T_TITRE, "center", "bottom"))
        return entrees

    def rendre(self, chemin):
        geo = list(self.pts) + [p for f in self.pieds for p in f.points()]
        boite = (min(p[0] for p in geo), min(p[1] for p in geo),
                 max(p[0] for p in geo), max(p[1] for p in geo))
        titres, cm_pt = [], 0.0
        for _ in range(6):                     # le cadre et les textes se règlent
            cote = max(boite[2] - boite[0], boite[3] - boite[1])
            cm_pt = cote / TAILLE_PX * (DPI / 72.0)
            titres = self._titres(geo, cm_pt)
            pts = list(geo)
            for e in self.textes + titres:
                pts += self._coins(e, cm_pt)
            boite = (min(p[0] for p in pts), min(p[1] for p in pts),
                     max(p[0] for p in pts), max(p[1] for p in pts))
        cx, cy = (boite[0] + boite[2]) / 2, (boite[1] + boite[3]) / 2
        demi = max(boite[2] - boite[0], boite[3] - boite[1]) * (0.5 + MARGE)
        fig = plt.figure(figsize=(TAILLE_PX / DPI, TAILLE_PX / DPI), dpi=DPI)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(cx - demi, cx + demi)
        ax.set_ylim(cy - demi, cy + demi)
        ax.set_aspect("equal")
        ax.axis("off")
        for f in self.pieds:
            f.dessiner(ax)
        for op in self.ops:
            op(ax)
        for (x, y), texte, taille, ha, va in titres:
            ax.text(x, y, texte, fontsize=taille, color=NOIR, ha=ha, va=va,
                    zorder=4)
        fig.savefig(chemin, transparent=True)
        plt.close(fig)


# -------------------------------------------------------------- positions ---

POSITIONS = []


def position(slug, titre, sous_titre=None):
    def deco(fn):
        POSITIONS.append((slug, titre, sous_titre, fn))
        return fn
    return deco


def _avancer(pied, repere, cible):
    """Décale un pied pour amener l'ordonnée d'un de ses repères sur `cible`."""
    return pied.decaler(0.0, cible - pied.rp(repere)[1])


@position("junbi-sogi", "Junbi Sogi", "position d'attente")
def _junbi(s):
    g = s.pied("G", at=(-EPAULE / 2, 0), repere="externe")
    d = s.pied("D", at=(EPAULE / 2, 0), repere="externe")
    s.cote_h(-13, -EPAULE / 2, EPAULE / 2, L_EPAULE + "\n(bords extérieurs)",
             ext=(-15, 1), dessous=True)
    s.poids(g, "50 %")
    s.poids(d, "50 %")
    s.texte((0, PIED_L + 5), "Pieds parallèles (0°)")


@position("narani-sogi", "Narani Sogi", "position parallèle")
def _narani(s):
    g = s.pied("G", at=(-EPAULE / 2, PIED_L), repere="gros-orteil")
    d = s.pied("D", at=(EPAULE / 2, PIED_L), repere="gros-orteil")
    s.cote_h(PIED_L + 6, -EPAULE / 2, EPAULE / 2,
             L_EPAULE + "\n(gros orteil à gros orteil)",
             ext=(PIED_L, PIED_L + 8))
    s.poids(g, "50 %")
    s.poids(d, "50 %")


@position("narani-junbi-sogi", "Narani Junbi Sogi", "position d'attente parallèle")
def _narani_junbi(s):
    _narani(s)


@position("moa-sogi", "Moa Sogi", "position rapprochée")
def _moa(s):
    g = s.pied("G", at=(0, 0), repere="interne")
    d = s.pied("D", at=(0, 0), repere="interne")
    s.ligne((0, -4), (0, PIED_L + 4))
    s.note((0, 2), (24, -10), "Bords internes\nen contact", courbe=-0.25)
    s.poids(g, "50 %")
    s.poids(d, "50 %")


@position("moa-junbi-sogi", "Moa Junbi Sogi", "position d'attente rapprochée")
def _moa_junbi(s):
    _moa(s)


@position("charyo-sogi", "Charyo Sogi", "position à l'attention")
def _charyo(s):
    g = s.pied("G", at=(0, 0), angle=22.5, repere="talon-interne")
    d = s.pied("D", at=(0, 0), angle=-22.5, repere="talon-interne")
    s.angle((0, 0), 67.5, 112.5, PIED_L + 5, "45°", rayons=PIED_L + 11)
    s.ligne((0, 0), (0, PIED_L + 11))
    s.note((0, 0.5), (0, -16), "Talons collés", courbe=0)
    s.poids(g, "50 %")
    s.poids(d, "50 %")


@position("kyong-ye-jase", "Kyong Ye Jase", "position de salut")
def _kyong_ye(s):
    _charyo(s)
    s.texte((0, -26), "Buste incliné de 15° vers l'avant")


@position("annun-sogi", "Annun Sogi", "position assise (du cavalier)")
def _annun(s):
    g = s.pied("G", at=(-EPAULE_15 / 2, 0), repere="centre")
    d = s.pied("D", at=(EPAULE_15 / 2, 0), repere="centre")
    s.cote_h(-23, -EPAULE_15 / 2, EPAULE_15 / 2,
             L_EPAULE_15 + "\n(de centre à centre)", ext=(-25, -12.5),
             dessous=True)
    s.poids(g, "50 %")
    s.poids(d, "50 %")
    s.texte((0, PIED_L + 8), "Genoux forcés vers l'extérieur")


@position("gunnun-sogi", "Gunnun Sogi", "position de marche — pied gauche avant")
def _gunnun(s, longueur=EPAULE_15, titre_long=L_EPAULE_15):
    d = s.pied("D", at=(EPAULE / 2, 0), angle=-25, repere="centre")
    g = s.pied("G", at=(-EPAULE / 2, 0), repere="centre")
    _avancer(g, "gros-orteil", d.rp("gros-orteil")[1] + longueur)
    y0, y1 = d.rp("gros-orteil")[1], g.rp("gros-orteil")[1]
    s.cote_v(EPAULE / 2 + 16, y0, y1, titre_long + "\n(gros orteil\nà gros orteil)",
             ext=(-EPAULE / 2, EPAULE / 2 + 18))
    s.cote_h(-24, -EPAULE / 2, EPAULE / 2, L_EPAULE + "\n(de centre à centre)",
             ext=(-26, -13), dessous=True)
    s.angle(d.rp("talon"), 90, 65, PIED_L + 5, "25°", rayons=PIED_L + 11)
    s.poids(g, "50 %")
    s.poids(d, "50 %")


@position("nachuo-sogi", "Nachuo Sogi", "position basse — pied gauche avant")
def _nachuo(s):
    _gunnun(s, longueur=EPAULE_15 + PIED_L, titre_long=L_NACHUO)


@position("niunja-sogi", "Niunja Sogi", "position en « L » — pied gauche avant")
def _niunja(s):
    d = s.pied("D", at=(0, 0), angle=-75, repere="talon")
    g = s.pied("G", at=(-2.5, 0), angle=-15, repere="gros-orteil")
    _avancer(g, "gros-orteil", d.rp("petit-orteil")[1] + EPAULE_15)
    y0, y1 = d.rp("petit-orteil")[1], g.rp("gros-orteil")[1]
    s.cote_v(20, y0, y1,
             L_EPAULE_15 + "\n(petit orteil arrière →\ngros orteil avant)",
             ext=(-12, 22))
    s.cote_h(y0 - 12, -2.5, 0,
             "Gros orteil avant à 2,5 cm\nà l'extérieur du talon arrière",
             ext=(y0 - 14, 2), dessous=True)
    s.ligne((-2.5, y0 - 14), (-2.5, y1))
    s.poids(g, "30 %")
    s.poids(d, "70 %")
    s.texte((0, y1 + 8), "Pieds à ~90°, orteils rentrés de 15°")


@position("gojung-sogi", "Gojung Sogi", "position fixe — pied gauche avant")
def _gojung(s):
    d = s.pied("D", at=(0, 0), angle=-75, repere="talon")
    g = s.pied("G", at=(-2.5, 0), angle=-15, repere="gros-orteil")
    _avancer(g, "gros-orteil", d.rp("gros-orteil")[1] + EPAULE_15)
    y0, y1 = d.rp("gros-orteil")[1], g.rp("gros-orteil")[1]
    s.cote_v(20, y0, y1, L_EPAULE_15 + "\n(gros orteil à gros orteil)",
             ext=(-12, 22))
    s.poids(g, "50 %")
    s.poids(d, "50 %")
    s.texte((0, y1 + 8), "Appuis de Niunja Sogi, poids réparti également")


@position("dwitbal-sogi", "Dwitbal Sogi",
          "position arrière rapprochée — pied gauche avant")
def _dwitbal(s):
    d = s.pied("D", at=(0, 0), angle=-35, repere="talon")
    g = s.pied("G", at=(0, 0), angle=-25, repere="centre", appui="plante")
    _avancer(g, "petit-orteil", d.rp("petit-orteil")[1] + EPAULE)
    y0, y1 = d.rp("petit-orteil")[1], g.rp("petit-orteil")[1]
    s.cote_v(22, y0, y1, L_EPAULE + "\n(petit orteil\nà petit orteil)",
             ext=(-14, 24))
    s.ligne((0, y0 - 8), (0, y1 + 8))
    s.note(g.rp("talon"), (-34, y1 * 0.6),
           "Talon avant décollé :\nappui sur la plante", courbe=0.25)
    s.angle(d.rp("talon"), 55, 90, PIED_L + 5, "35°", rayons=PIED_L + 11)
    s.poids(g, "0 %")
    s.poids(d, "~100 %")
    s.texte((0, -22), "Pied avant centré sur l'axe du talon arrière")


@position("soojik-sogi", "Soojik Sogi", "position verticale — pied gauche avant")
def _soojik(s):
    d = s.pied("D", at=(PIED_l / 2 + 1, 0), angle=-90, repere="talon")
    g = s.pied("G", at=(-PIED_l / 2 - 1, 0), angle=-15, repere="centre")
    _avancer(g, "gros-orteil", d.rp("gros-orteil")[1] + EPAULE)
    y0, y1 = d.rp("gros-orteil")[1], g.rp("gros-orteil")[1]
    s.cote_v(42, y0, y1, L_EPAULE + "\n(gros orteil à gros orteil)",
             ext=(-14, 44))
    s.angle(d.rp("talon"), 0, 90, 19, "90°", rayons=27)
    s.poids(g, "40 %")
    s.poids(d, "60 %")
    s.texte((0, y1 + 8), "Pied avant rentré de 15°\nPied arrière à 90°")


@position("sasun-sogi", "Sasun Sogi", "position en diagonale — pied gauche avant")
def _sasun(s):
    d = s.pied("D", at=(EPAULE_15 / 2, 0), repere="centre")
    g = s.pied("G", at=(-EPAULE_15 / 2, 0), repere="centre")
    _avancer(g, "talon", d.rp("orteils")[1])
    s.cote_h(-23, -EPAULE_15 / 2, EPAULE_15 / 2,
             L_EPAULE_15 + "\n(dimensions de Annun Sogi)", ext=(-25, -12.5),
             dessous=True)
    s.ligne((-EPAULE_15 / 2 - 8, d.rp("orteils")[1]),
            (EPAULE_15 / 2 + 8, d.rp("orteils")[1]))
    s.note(g.rp("talon"), (-EPAULE_15 / 2 - 26, d.rp("orteils")[1] + 8),
           "Talon avant aligné\nsur les orteils arrière", courbe=-0.2)


@position("oguryo-sogi", "Oguryo Sogi", "position accroupie")
def _oguryo(s):
    _sasun(s)
    s.texte((0, PIED_L + 22),
            "Appuis de Sasun Sogi\nGenoux fléchis vers l'intérieur")


@position("kyocha-sogi", "Kyocha Sogi", "position en « X »")
def _kyocha(s):
    g = s.pied("G", at=(0, 0), repere="talon")
    d = s.pied("D", at=(-9, 0), repere="plante-avant", appui="plante")
    s.note(g.rp("centre"), (24, PIED_L + 6),
           "Pied d'appui à plat :\n100 % du poids", courbe=0.25)
    s.note(d.rp("orteils"), (-30, -12),
           "Pied croisé : plante seule,\n0 % du poids", courbe=0.25)


@position("waebal-sogi", "Waebal Sogi", "position sur une jambe — appui droit")
def _waebal(s):
    d = s.pied("D", at=(0, 0), repere="talon")
    s.pied("G", at=(-20, 0), repere="centre", appui="leve")
    s.note(d.rp("centre"), (26, PIED_L + 4),
           "Jambe d'appui tendue :\n100 % du poids", courbe=0.25)
    s.texte((-20, -16), "Pied relevé (0 %), parallèle\nau pied d'appui :\n"
                        "tranchant externe sur la rotule", couleur=GRIS)


@position("guburyo-sogi", "Guburyo Sogi", "position fléchie — appui droit")
def _guburyo(s):
    _waebal(s)
    s.texte((6, -30), "Appuis de Waebal Sogi, jambe d'appui fléchie")


@position("guburyo-junbi-sogi", "Guburyo Junbi Sogi", "position d'attente fléchie")
def _guburyo_junbi(s):
    d = s.pied("D", at=(0, 0), repere="talon")
    s.pied("G", at=(-20, 0), repere="centre", appui="leve")
    s.note(d.rp("centre"), (26, PIED_L + 4),
           "Jambe d'appui fléchie :\n100 % du poids", courbe=0.25)
    s.texte((-20, -16), "Pied relevé (0 %), parallèle\nau pied d'appui, à hauteur\n"
                        "du genou d'appui", couleur=GRIS)


@position("an-palja-sogi", "An Palja Sogi", "position ouverte vers l'intérieur")
def _an_palja(s):
    g = s.pied("G", at=(-EPAULE / 2, 0), angle=-15, repere="centre")
    d = s.pied("D", at=(EPAULE / 2, 0), angle=15, repere="centre")
    s.cote_h(-22, -EPAULE / 2, EPAULE / 2, L_EPAULE, ext=(-24, -12),
             dessous=True)
    s.angle(d.rp("talon"), 90, 105, PIED_L + 5, "15°", rayons=PIED_L + 11)
    s.angle(g.rp("talon"), 75, 90, PIED_L + 5, "15°", rayons=PIED_L + 11)
    s.texte((0, PIED_L + 8), "Orteils pointés vers l'intérieur")


@position("bakat-palja-sogi", "Bakat Palja Sogi", "position ouverte vers l'extérieur")
def _bakat_palja(s):
    g = s.pied("G", at=(-EPAULE / 2, 0), angle=45, repere="centre")
    d = s.pied("D", at=(EPAULE / 2, 0), angle=-45, repere="centre")
    s.cote_h(-26, -EPAULE / 2, EPAULE / 2, L_EPAULE, ext=(-28, -14),
             dessous=True)
    s.angle(d.rp("talon"), 45, 90, PIED_L + 5, "45°", rayons=PIED_L + 11)
    s.angle(g.rp("talon"), 90, 135, PIED_L + 5, "45°", rayons=PIED_L + 11)
    s.texte((0, PIED_L + 10), "Orteils ouverts à 45° vers l'extérieur")


# ---------------------------------------------------------------- exécution ---


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true",
                    help="écrit réellement les fichiers PNG")
    ap.add_argument("--only", metavar="SLUG",
                    help="ne traiter qu'une position (ex. gunnun-sogi)")
    ap.add_argument("--out", metavar="DOSSIER", default=str(SORTIE),
                    help="dossier de sortie (défaut : images/sogi)")
    args = ap.parse_args()

    choix = [p for p in POSITIONS if args.only in (None, p[0])]
    if not choix:
        sys.exit("position inconnue : %s (voir --help)" % args.only)

    dossier = pathlib.Path(args.out)
    if args.write:
        dossier.mkdir(parents=True, exist_ok=True)

    for slug, titre, sous_titre, fn in choix:
        chemin = dossier / (slug + ".png")
        if not args.write:
            print("écrirait %s — %s, %s" % (chemin.relative_to(RACINE)
                                            if chemin.is_absolute() and
                                            RACINE in chemin.parents else chemin,
                                            titre, sous_titre))
            continue
        s = Scene(titre, sous_titre)
        fn(s)
        s.rendre(chemin)
        print("écrit %s" % chemin)

    if not args.write:
        print("\n%d schéma(s) — relancer avec --write pour écrire." % len(choix))


if __name__ == "__main__":
    main()
