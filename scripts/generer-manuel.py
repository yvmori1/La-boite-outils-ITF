#!/usr/bin/env python3
"""Assemble Theorie/manuel-taekwon-do.md à partir des quatre fiches de fond.

  python3 scripts/generer-manuel.py           # résumé, n'écrit rien
  python3 scripts/generer-manuel.py --write   # écrit le manuel

Réunit en un seul document, dans un ordre d'apprentissage, le contenu de
Lexique.md, grammaire-itf.md, mouvement_de_vagues.md et Genes.md : d'abord
l'art et sa voie, puis les principes physiques, la grammaire, les positions,
le répertoire technique, les formes, l'autodéfense, et le lexique en annexe.

Le texte n'est pas recopié : il est extrait des sources à chaque exécution, de
sorte qu'une correction dans une fiche se retrouve dans le manuel. Seuls les
passages **fusionnés** — ceux qui existaient en double dans deux sources — sont
écrits ici, dans FUSIONS, avec la raison de la fusion.

Doublons résolus (ce que le manuel ne reprend qu'une fois) :

  * le crédo : Genes.md et grammaire-itf.md le donnaient tous deux ;
  * les principes de position : quatre dans grammaire-itf.md, six dans Genes.md ;
  * les 21 positions : fiches cotées de grammaire-itf.md, contre un tableau
    résumé dans Genes.md et un tableau trilingue dans Lexique.md ;
  * les modificateurs de nomenclature : définis dans grammaire-itf.md, traduits
    dans Lexique.md — les deux sont refondus en une seule liste ;
  * les déplacements : listés dans les deux, seul le tableau trilingue reste ;
  * les verbes d'action : typologie de grammaire-itf.md et index de fin de
    document, refondus en un tableau unique ;
  * le vocabulaire du dojang : bullets de grammaire-itf.md contre tableau de
    Lexique.md, réduits au tableau de l'annexe.
"""

import argparse
import pathlib
import re
import sys

RACINE = pathlib.Path(__file__).resolve().parents[1]
THEORIE = RACINE / "Theorie"
SORTIE = THEORIE / "manuel-taekwon-do.md"

SOURCES = {
    "genes": THEORIE / "Genes.md",
    "grammaire": THEORIE / "grammaire-itf.md",
    "lexique": THEORIE / "Lexique.md",
    "vague": THEORIE / "mouvement_de_vagues.md",
}

# ------------------------------------------------------------- extraction ---

_ENTETE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def _decouper(texte):
    """Sections d'un document, indexées par le libellé exact de leur titre."""
    lignes = texte.splitlines()
    entetes, dans_bloc = [], False
    for i, l in enumerate(lignes):
        if l.lstrip().startswith("```"):
            dans_bloc = not dans_bloc
        if dans_bloc:
            continue
        m = _ENTETE.match(l)
        if m:
            entetes.append((i, len(m.group(1)), m.group(2)))
    sections = {}
    for k, (i, niveau, titre) in enumerate(entetes):
        fin = len(lignes)
        for j, niveau_j, _ in entetes[k + 1:]:
            if niveau_j <= niveau:
                fin = j
                break
        sections.setdefault(titre, lignes[i + 1:fin])
    return sections


_CACHE = {}


def extrait(source, titre, decalage=0, depuis=None, jusqua=None):
    """Corps d'une section d'une source, titres internes décalés si besoin.

    `depuis` et `jusqua` permettent de ne prendre qu'une partie du corps quand
    une section mêle deux contenus dont un seul a sa place ici.
    """
    if source not in _CACHE:
        _CACHE[source] = _decouper(SOURCES[source].read_text(encoding="utf-8"))
    if titre not in _CACHE[source]:
        sys.exit("section introuvable dans %s : %s" % (SOURCES[source].name, titre))
    lignes = list(_CACHE[source][titre])
    # Les filets horizontaux des sources séparaient leurs propres sections ;
    # ici c'est le manuel qui découpe, ils ne veulent plus rien dire.
    lignes = [l for l in lignes if l.strip() != "---"]
    if decalage:
        lignes = [("#" * decalage + l) if _ENTETE.match(l) else l for l in lignes]
    texte = "\n".join(lignes).strip("\n")
    if depuis:
        texte = texte[texte.index(depuis):]
    if jusqua:
        texte = texte[:texte.index(jusqua)]
    return texte.strip("\n")


def h(niveau, titre):
    return "#" * niveau + " " + titre


_FICHE = re.compile(r"^(#+) 3\.(\d+) (.+?) \((.+)\)\s*$")


def _renumeroter(texte, chapitre):
    """Aligne la numérotation et la casse des fiches de position sur le manuel.

    Les fiches sont numérotées 3.1 à 3.21 dans grammaire-itf.md, d'après la
    section qui les porte là-bas ; ici elles appartiennent à un autre chapitre.
    Leur titre, tout en capitales à la source, passe en casse de phrase.
    """
    sorties = []
    for l in texte.splitlines():
        m = _FICHE.match(l)
        if m:
            nom = m.group(3).capitalize()
            for lettre in ("L", "X"):
                nom = nom.replace("« %s »" % lettre.lower(), "« %s »" % lettre)
            l = "%s %d.%s %s (%s)" % (m.group(1), chapitre, m.group(2), nom,
                                      m.group(4))
        sorties.append(l)
    return "\n".join(sorties)


# ---------------------------------------------------------------- fusions ---

FUSIONS = {}

# Crédo : Genes.md en donnait le commentaire, grammaire-itf.md la prononciation.
FUSIONS["credo"] = """Le but ultime du Taekwon-Do est d'éliminer le combat en décourageant l'agression
par une force morale. Chaque adepte s'efforce d'assimiler et de manifester les
cinq principes fondamentaux de l'art :

| Principe | Ce qu'il engage |
| --- | --- |
| **Courtoisie** — *Ye Ui / [예의](../audio/lexique/Ye-Ui.m4a)* | Promouvoir un esprit de concessions mutuelles, être poli, se conduire selon l'étiquette (*Sajeji Do*), respecter les possessions d'autrui et agir avec équité. |
| **Intégrité** — *Yum Chi / [염치](../audio/lexique/Yum-Chi.m4a)* | Distinguer clairement le bien du mal et ressentir une culpabilité sincère face à l'erreur. L'intégrité fait défaut chez l'instructeur apathique qui enseigne de mauvaises techniques, chez l'étudiant qui triche dans ses cassages ou tente d'acheter un grade, chez le professeur guidé par le seul commerce. |
| **Persévérance** — *In Nae / [인내](../audio/lexique/In-Nae.m4a)* | *« La patience mène à la vertu et au mérite. Un foyer peut connaître la paix si l'on est cent fois patient. »* La ténacité permet de surmonter toutes les difficultés pour perfectionner son art. |
| **Contrôle de soi** — *Guk Gi / [극기](../audio/lexique/Guk-Gi.m4a)* | Essentiel tant à l'intérieur qu'à l'extérieur du dojang : une perte de contrôle peut être désastreuse en combat comme dans les affaires personnelles. Lao-Tzu : *« On appelle "fort" celui qui se vainc soi-même et non celui qui vainc les autres. »* |
| **Esprit indomptable** — *Baekjul Boolgool / [백절불굴](../audio/lexique/Baekjul-Boolgool.m4a)* | Être modeste et honnête, mais affronter l'injustice sans peur ni hésitation, peu importe le nombre d'adversaires. Confucius : *« C'est un geste de lâcheté que de se taire en face de l'injustice. »* |"""

# Principes de position : quatre côté grammaire, six côté Genes, même propos.
FUSIONS["principes-position"] = """Une position juste obéit à six principes, valables de la première à la dernière
ceinture :

1. **Tenir le dos parfaitement droit**, sauf les rares exceptions exigées par la technique.
2. **Détendre complètement les épaules** pour libérer la fluidité du haut du corps.
3. **Contracter et tendre l'abdomen** pour stabiliser le tronc.
4. **Conserver le bon angle de face** : pleine face, demi-face (45 degrés) ou de côté par rapport à l'adversaire.
5. **Assurer un équilibre stable mais dynamique**, en statique comme en mouvement.
6. **Utiliser la force de ressort du genou** — l'action sinusoïdale décrite au chapitre du mouvement de vague — pour amorcer et conclure le mouvement."""

# Modificateurs : définis dans grammaire-itf.md, traduits dans Lexique.md.
FUSIONS["briques"] = """Chaque brique de la formule a un nom coréen, un équivalent anglais employé dans
les manuels de l'ITF, et un sens mécanique précis.

**Hauteur de la cible** — *Nopai / [높이](../audio/grammaire/Nopai.m4a)*

* **Nopunde** ([높은데](../audio/grammaire/Nopunde.m4a)) — *high section* — niveau haut : le visage et le cou, au-dessus des épaules.
* **Kaunde** ([가운데](../audio/grammaire/Kaunde.m4a)) — *middle section* — niveau moyen : le tronc, le plexus solaire, les côtes flottantes.
* **Najunde** ([낮은데](../audio/grammaire/Najunde.m4a)) — *low section* — niveau bas : sous la ceinture, l'abdomen et le bas-ventre.

**Alignement du bras par rapport à la jambe avancée**

* **Baro** ([바로](../audio/grammaire/Baro.m4a)) — *obverse, same side* — en poursuite : le bras qui agit est du **même côté** que la jambe placée à l'avant.
* **Bandae** ([반대](../audio/grammaire/Bandae.m4a)) — *reverse, opposite side* — contraire : le bras qui agit est du **côté opposé** à la jambe avant.

**Direction et trajectoire** — *Banghyang / [방향](../audio/grammaire/Banghyang.m4a)*

* **Ap** ([앞](../audio/grammaire/Ap.m4a)) — *front* — de face.
* **Yop** ([옆](../audio/grammaire/Yop.m4a)) — *side* — latéral, de côté.
* **Dollyo** ([돌려](../audio/grammaire/Dollyo.m4a)) — *turning, round* — circulaire.
* **Ollyo** ([올려](../audio/grammaire/Ollyo.m4a)) — *rising, upward* — ascendant.
* **Naeryo** ([내려](../audio/grammaire/Naeryo.m4a)) — *downward* — descendant.
* **Anuro** ([안으로](../audio/grammaire/Anuro.m4a)) — *inward* — de l'extérieur vers l'intérieur.
* **Bakuro** ([밖으로](../audio/grammaire/Bakuro.m4a)) — *outward* — de l'intérieur vers l'extérieur.

**Modalité de déplacement et d'exécution**

* **Twimyo / Twio** ([뛰며](../audio/grammaire/Twimyo.m4a) / [뛰어](../audio/grammaire/Twio.m4a)) — *jumping, flying* — technique sautée, en suspension complète.
* **Mikulgi** ([미끌기](../audio/grammaire/Mikulgi.m4a)) — *sliding* — technique glissée : déplacement rasant qui ferme instantanément la distance.
* **Dora** ([돌아](../audio/grammaire/Dora.m4a)) — *spinning* — technique retournée : pivot de 180° ou 360° par le dos.
* **Sangbal** ([쌍발](../audio/grammaire/Sangbal.m4a)) — *twin foot* — les deux jambes attaquent en même temps, en l'air.
* **Yonsok** ([연속](../audio/grammaire/Yonsok.m4a)) — *consecutive* — plusieurs frappes de la même jambe sans la reposer.

**Latéralité** — s'emploie lorsque le nom seul ne lève pas l'ambiguïté, notamment
en position assise (*Annun So*) où les deux côtés travaillent alternativement
sans changement de posture.

* **Wen** ([왼](../audio/grammaire/Wen.m4a)) — *left* — le membre gauche exécute l'action.
* **Orun** ([오른](../audio/grammaire/Orun.m4a)) — *right* — le membre droit exécute l'action.

> *Annun So **Orun** Joomuk Kaunde Jirugi* = en position assise, coup de poing moyen du **poing droit**."""

# Verbes : typologie du répertoire des jambes + index de fin de grammaire-itf.md.
FUSIONS["verbes"] = """Le dernier mot d'un nom de technique dit **comment** le corps frappe. Deux
techniques qui visent la même cible avec la même arme mais ne portent pas le
même verbe ne s'exécutent pas de la même façon.

| Terme | Famille | Mécanique corporelle | Arme ou exemple |
| --- | --- | --- | --- |
| **Chagi** | Catégorie | Action offensive de la jambe ou du pied. | Membres inférieurs. |
| **Makgi** | Catégorie | Action défensive : blocage, protection, déviation. | Membres supérieurs ou inférieurs. |
| **Jirugi** | Impact | Frappe rectiligne et pénétrante, en piston, avec engagement du bassin. | *Ap Joomuk*, *Dwitchuk*… |
| **Taerigi** | Impact | Frappe balistique, circulaire ou cinglante, en courbe. | *Dung Joomuk*, *Sonkal*… |
| **Tulgi** | Impact | Pique incisive sur une surface réduite, visant une faille anatomique. | *Sonkut*, *Apkumchi*… |
| **Busigi** | Dynamique | Extension explosive suivie d'un réarmement instantané du genou (*snap*). | Genou — *Ap Cha Busigi*. |
| **Olligi** | Dynamique | Élévation rectiligne continue, sans pliure du genou. | Jambe tendue — *Ap Cha Olligi*. |
| **Milgi** | Dynamique | Poussée continue en force, projetant le centre de gravité. | Plante du pied — *Cha Milgi*. |
| **Suroh** | Dynamique | Fauchage circulaire rasant le sol. | Voûte plantaire — *Suroh Chagi*. |
| **Naeryo** | Dynamique | Percussion lourde verticale, du haut vers le bas. | Talon ou tranchant externe. |
| **Nullo** | Dynamique | Écrasement vertical vers le bas pour briser un appui. | Plante du pied ou paume. |
| **Goro** | Dynamique | Trajectoire circulaire qui dépasse la cible pour la ramener en crochet. | Arrière du talon — *Goro Chagi*. |
| **Bituro** | Dynamique | Départ axial s'ouvrant en torsion vers l'extérieur à l'impact. | Bol du pied — *Bituro Chagi*. |"""

# ------------------------------------------------------------------ plan ---

PREAMBULE = """Ce manuel réunit en un seul parcours les quatre documents de fond du dépôt :
[Genes.md](Genes.md), [grammaire-itf.md](grammaire-itf.md),
[mouvement_de_vagues.md](mouvement_de_vagues.md) et [Lexique.md](Lexique.md).
Il est **assemblé automatiquement** par
[../scripts/generer-manuel.py](../scripts/generer-manuel.py) : les quatre fiches
restent les sources, ce document en donne la lecture continue.

L'ordre suit celui de l'apprentissage plutôt que celui des fiches d'origine : ce
qu'est l'art et d'où il vient, les principes physiques qui font la puissance, la
grammaire qui permet de nommer et de comprendre chaque technique, les positions
qui les portent, le répertoire technique, les formes, l'autodéfense, et enfin le
lexique trilingue en annexe.

Ce qui figurait deux fois dans les sources ne figure ici qu'une : le crédo, les
principes de position, les modificateurs de nomenclature, les déplacements, les
verbes d'action et le vocabulaire du dojang ont été refondus."""


def manuel():
    """Le document complet, dans l'ordre d'apprentissage."""
    b = []
    a = b.append

    a(h(1, "Manuel de Taekwon-Do ITF"))
    a(PREAMBULE)
    a("---")

    # ---- I ---------------------------------------------------------------
    a(h(2, "Partie I — L'art et sa voie"))
    a("Avant les techniques : ce qu'est le Taekwon-Do, d'où il vient, et la "
      "conduite qu'il demande. C'est la matière des examens théoriques de tous "
      "les grades.")

    a(h(3, "1. Ce qu'est le Taekwon-Do"))
    a("**Taekwon-Do** ([태권도](../audio/grammaire/Taekwon-Do.m4a)) : *Tae*, "
      "frapper ou briser avec le pied ; *Kwon*, frapper ou briser avec le "
      "poing ; *Do*, la voie, l'art, le cheminement spirituel. Au-delà de sa "
      "dimension sportive et de combat, le Taekwon-Do ITF se définit comme un "
      "mode de vie et de pensée, fusion de la discipline corporelle et du "
      "réarmement moral.")
    a(extrait("genes", "1. Le Cycle Évolutif et la Composition du Taekwon-Do"))

    a(h(3, "2. Histoire et filiation"))
    a(h(4, "Genèse du Taekwon-Do moderne"))
    a(extrait("genes", "1. Genèse du Taekwon-Do Moderne"))
    a(h(4, "Le Général Choi Hong Hi, fondateur"))
    a(extrait("genes", "2. Le Général Choi Hong Hi (Fondateur)"))
    a(h(4, "Maître J. André Blake, pionnier québécois"))
    a(extrait("genes", "3. Maître J. André Blake (Pionnier Québécois)"))
    a(h(4, "Instructeurs fondateurs du club de Blainville"))
    a(extrait("genes", "4. Instructeurs Fondateurs du Club de Blainville"))
    a(h(4, "Racines des arts martiaux"))
    a(extrait("genes", "5. Histoire Générale des Arts Martiaux Mondiaux"))

    a(h(3, "3. Le Do : la culture morale de l'adepte"))
    a(h(4, "Le crédo (Taekwon-Do Jungshin)"))
    a(FUSIONS["credo"])
    a(h(4, "Le serment de l'adepte"))
    a(extrait("genes", "2. Le Serment de l'Adepte"))
    a(h(4, "La charte du Taekwon-Do (Taekwon-Do Jang)"))
    a(extrait("genes", "3. La Charte du Taekwon-Do (Taekwon-Do Jang)"))
    a(h(4, "Philosophie de la société et vertus cardinales"))
    a(extrait("genes", "4. La Philosophie de la Société et les Vertus Cardinales"))
    a(h(4, "Règles de vie pour l'auto-culture"))
    a(extrait("genes", "5. Règles de Vie pour l'Auto-Culture (Nature Humaine)"))

    a(h(3, "4. Étiquette et vie du dojang"))
    a(h(4, "Le salut (Kyong Ye)"))
    a(extrait("genes", "1. Protocole du Salut (Kyong Ye)"))
    a("> La position de salut elle-même est décrite avec les positions de "
      "pieds, au chapitre 16.")
    a(h(4, "Communication et conduite"))
    a(extrait("genes", "2. Règles de Communication et de Conduite Spécifiques"))
    a(h(4, "Les douze directives de discipline"))
    a(extrait("genes", "3. Les Douze Directives de Discipline du Dojang"))

    a(h(3, "5. Le dobok et les ceintures"))
    a(h(4, "Rôle et conception du dobok"))
    a(extrait("genes", "1. Rôle et Conception du Dobok"))
    a(h(4, "La réforme du 28 mars 1968"))
    a(extrait("genes", "2. Réforme Historique du Dobok (28 mars 1968)"))
    a(h(4, "Spécifications de l'uniforme"))
    a(extrait("genes", "3. Spécifications Techniques de l'Uniforme"))
    a(h(4, "Symbolisme des couleurs de ceinture"))
    a(extrait("genes", "4. Signification Symbolique des Couleurs de Ceinture"))
    a("---")

    # ---- II --------------------------------------------------------------
    a(h(2, "Partie II — Les principes physiques"))
    a("Ce qui distingue le Taekwon-Do d'une gymnastique : la puissance y est "
      "calculée. Ces principes commandent l'exécution de toutes les techniques "
      "des parties suivantes.")

    a(h(3, "6. La théorie de la puissance (Him Ui Wolli)"))
    a(extrait("genes", "SECTION VII : LA THÉORIE DE LA PUISSANCE (HIM UI WOLLI)",
              jusqua="### 1."))
    a(extrait("genes", "1. Les Sept Facteurs Physiques de Puissance"))

    a(h(3, "7. Le mouvement de vague"))
    a(extrait("vague", "Le mouvement de vague", decalage=2))

    a(h(3, "8. Respiration, ki et méditation"))
    a(h(4, "La respiration et le ki"))
    a(extrait("genes", "1. La Respiration et le Ki"))
    a(h(4, "Le protocole de respiration isotonique"))
    a(extrait("genes", "2. Le Protocole de Respiration Isotonique"))
    a(h(4, "Méditation zen active (Jung-Joong-Dong)"))
    a(extrait("genes", "3. Méditation Zen Active (Jung-Joong-Dong)"))
    a("---")

    # ---- III -------------------------------------------------------------
    a(h(2, "Partie III — La grammaire des techniques"))
    a("En Taekwon-Do ITF, le nom d'une technique n'est pas une étiquette : il "
      "en décrit la mécanique, la trajectoire et l'intention. Savoir lire un "
      "nom, c'est savoir exécuter le mouvement sans l'avoir vu.")

    a(h(3, "9. Les deux formules de construction"))
    a(h(4, "Techniques de mains et de bras"))
    a(extrait("grammaire",
              "A. Formule Magique des Techniques de Mains / Bras (Membres Supérieurs)"))
    a(h(4, "Techniques de jambes et de pieds"))
    a(extrait("grammaire",
              "B. Formule Magique des Techniques de Jambes / Pieds (Membres Inférieurs)"))

    a(h(3, "10. Les briques de la formule"))
    a(FUSIONS["briques"])

    a(h(3, "11. Les verbes d'action"))
    a(FUSIONS["verbes"])

    a(h(3, "12. Les armes naturelles (Jook Bang)"))
    a(extrait("grammaire", "4. Les Armes Naturelles (Surfaces d'Impact — Jook Bang)",
              jusqua="### A."))
    a(h(4, "Membres supérieurs : mains, avant-bras, coudes"))
    a(extrait("grammaire", "A. Membres Supérieurs (Mains, Avant-bras, Coudes)",
              decalage=1))
    a(h(4, "Membres inférieurs : pieds, chevilles, genoux"))
    a(extrait("grammaire", "B. Membres Inférieurs (Pieds, Chevilles, Genoux)"))

    a(h(3, "13. Décrypter un nom de technique"))
    a(extrait("grammaire", "6. Guide d'Application de Décryptage de la Grammaire",
              decalage=1))
    a("---")

    # ---- IV --------------------------------------------------------------
    a(h(2, "Partie IV — Les positions (Sogi)"))
    a("La position est le point de départ et d'appui de tout mouvement : sa "
      "géométrie décide de la stabilité, de la portée et de la puissance de la "
      "technique qu'elle porte.")

    a(h(3, "14. Principes et constantes"))
    a(FUSIONS["principes-position"])
    a(extrait("grammaire", "A. Constantes Physiques de Référence"))
    a(extrait("genes", "1. Les Six Principes de Base d'une Bonne Position",
              depuis="*Note sur la répartition du poids"))

    a(h(3, "15. Les positions d'un coup d'œil"))
    a("Nom français, nom anglais des manuels ITF, nom coréen et prononciation. "
      "Le détail géométrique de chacune suit au chapitre 16.")
    a(extrait("lexique", "Positions (Sogi)"))

    a(h(3, "16. Les 21 positions en détail"))
    a("Chaque fiche donne les dimensions, l'orientation des pieds, la "
      "répartition du poids et le schéma d'alignement coté. Les schémas sont "
      "générés par [../scripts/generer-sogi.py](../scripts/generer-sogi.py) ; "
      "les longueurs y sont exprimées en largeurs d'épaule.")
    a(_renumeroter(
        extrait("grammaire", "C. Fiches Techniques Exhaustives des 21 Positions de Pieds"),
        16))
    a("---")

    # ---- V ---------------------------------------------------------------
    a(h(2, "Partie V — Le répertoire technique"))
    a("Les techniques elles-mêmes, classées par famille. Le commentaire donne "
      "la mécanique ; l'annexe donne la traduction et la prononciation de "
      "chaque terme.")

    a(h(3, "17. Les déplacements (Dolgi)"))
    a("Les déplacements décrivent la manière dont le pratiquant ajuste sa "
      "distance et pivote pour générer de la puissance cinétique.")
    a(extrait("lexique", "Déplacements (Dolgi)"))

    a(h(3, "18. Les techniques de bras"))
    a(extrait("grammaire", "B. Répertoire des Techniques de Bras (Membres Supérieurs)",
              decalage=0))

    a(h(3, "19. Les techniques de jambes"))
    a(h(4, "Les coups de pied (Chagi)"))
    a(extrait("grammaire", "2. Les Coups de Pied Classiques et Avancés (Chagi)"))
    a(h(4, "Techniques sautées et spéciales"))
    a(extrait("grammaire", "3. Les Techniques Sautées et Spéciales (Special & Flying)"))
    a("---")

    # ---- VI --------------------------------------------------------------
    a(h(2, "Partie VI — Les formes (Tul)"))
    a(extrait("genes", "SECTION X : LE GUIDE DES VINGT-QUATRE TULS DE L'ITF",
              jusqua="### 1."))

    a(h(3, "20. Directives d'exécution"))
    a(extrait("genes", "1. Directives d'Exécution des Formes"))

    a(h(3, "21. Les vingt-quatre formes"))
    a(extrait("genes", "2. Répertoire Historique et Philosophique des Tuls"))
    a("> Le tracé au sol de chaque forme est dans [../images/README.md](../images/README.md) ; "
      "l'exécution mouvement par mouvement dans [../tul/README.md](../tul/README.md).")
    a("---")

    # ---- VII -------------------------------------------------------------
    a(h(2, "Partie VII — L'autodéfense (Hosinsul)"))
    a("Programme de la FQTI, grade par grade. C'est la validation finale du "
      "cycle : coordination, vitesse et concentration face à une agression "
      "spontanée.")
    for niveau, titre in [
        ("1. Niveau Ceinture Blanche (Dégagement sur Saisies)",
         "22. Ceinture blanche — dégagements sur saisies"),
        ("2. Niveau Ceinture Blanche I (Défense sur Poussées)",
         "23. Ceinture blanche I — défenses sur poussées"),
        ("3. Niveau Ceinture Jaune (Défense contre Attaques de Face)",
         "24. Ceinture jaune — attaques de face"),
        ("4. Niveau Ceinture Jaune I (Défense contre Attaques par l'Arrière)",
         "25. Ceinture jaune I — attaques par l'arrière"),
        ("5. Niveau Ceinture Verte (Défense contre Attaques de Côté)",
         "26. Ceinture verte — attaques de côté"),
        ("6. Niveau Ceinture Verte I (Défense contre Attaques au Sol)",
         "27. Ceinture verte I — attaques au sol"),
        ("7. Niveau Ceinture Bleue (Défense contre Attaques Combinées)",
         "28. Ceinture bleue — attaques combinées"),
    ]:
        a(h(3, titre))
        a(extrait("genes", niveau))
    a("---")

    # ---- Annexe ----------------------------------------------------------
    a(h(2, "Annexe — Lexique trilingue"))
    a("Français, anglais et coréen, avec la prononciation. Les positions "
      "figurent au chapitre 15, les modificateurs au chapitre 10 et les "
      "déplacements au chapitre 17 : ils ne sont pas repris ici.")

    a(h(3, "A. Termes généraux, dojang et compétition"))
    a(extrait("lexique", "Termes Généraux de Compétition et de Base"))
    a(h(3, "B. Coups de pied (Chagi)"))
    a(extrait("lexique", "Techniques de Pied (Chagi)"))
    a(h(3, "C. Blocages (Makgi)"))
    a(extrait("lexique", "Blocages (Makgi)"))
    a(h(3, "D. Frappes et attaques (Jirugi / Taerigi / Tulgi)"))
    a(extrait("lexique", "Frappes et Attaques (Taerigi / Jirugi / Tulgi)"))
    a("---")

    a("[← Retour à la théorie](README.md) — [← Retour à l'index général](../README.md)")

    return "\n\n".join(x for x in b if x) + "\n"


# ------------------------------------------------------------------- table ---

def _ancre(titre):
    """Ancre GitHub d'un titre : minuscules, ponctuation retirée, espaces liés."""
    t = titre.lower()
    t = re.sub(r"[^\w\s\-–—]", "", t, flags=re.UNICODE)
    t = t.replace("–", "").replace("—", "")
    return re.sub(r"\s+", "-", t.strip())


def table_des_matieres(texte):
    lignes = []
    for l in texte.splitlines():
        m = _ENTETE.match(l)
        if not m or len(m.group(1)) not in (2, 3):
            continue
        titre = m.group(2)
        puce = "* " if len(m.group(1)) == 2 else "    * "
        lignes.append("%s[%s](#%s)" % (puce, titre, _ancre(titre)))
    return "## Table des matières\n\n" + "\n".join(lignes)


def assembler():
    texte = manuel()
    tete, reste = texte.split("---", 1)
    return tete + table_des_matieres(reste) + "\n\n---" + reste


# --------------------------------------------------------------- exécution ---

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true", help="écrit le manuel")
    args = ap.parse_args()

    texte = assembler()
    titres = sum(1 for l in texte.splitlines() if _ENTETE.match(l))
    resume = "%s — %d lignes, %d titres, %d caractères" % (
        SORTIE.relative_to(RACINE), len(texte.splitlines()), titres, len(texte))

    if not args.write:
        print("écrirait %s" % resume)
        print("relancer avec --write pour écrire.")
        return
    ancien = SORTIE.read_text(encoding="utf-8") if SORTIE.exists() else None
    if ancien == texte:
        print("inchangé %s" % resume)
        return
    SORTIE.write_text(texte, encoding="utf-8")
    print("écrit %s" % resume)


if __name__ == "__main__":
    main()
