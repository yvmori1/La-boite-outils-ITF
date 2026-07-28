# La boîte à outils ITF

Recueil de documentation technique et théorique de **Taekwon-Do ITF** (International Taekwon-Do Federation), rédigé en français. L'ensemble est constitué de fiches Markdown autonomes : une fiche par technique, par grade ou par thème théorique.

Le dépôt sert deux usages :

* **Étude et révision** — fiches de passage de grade, lexique coréen, formes détaillées mouvement par mouvement.
* **Enseignement** — support de cours pour l'instructeur, nomenclature complète, décomposition pédagogique de chaque technique.

Les fiches techniques sont nommées en **romanisation coréenne** (`dollyo-chagi.md`, `najunde-makgi.md`) et titrées en français avec le terme coréen entre parenthèses.

---

## Index des répertoires

| Répertoire | Contenu | Fiches |
| :--- | :--- | :--- |
| [Ceintures](Ceintures/index.md) | Fiches d'étude officielles de passage de grade, du 10e Gup au 6e Dan | 17 |
| [tul](tul/index.md) | Les formes (Tul) et exercices fondamentaux, mouvement par mouvement | 28 |
| [chagi](chagi/index.md) | Les coups de pied — 차기 | 48 |
| [makgi](makgi/index.md) | Les blocages — 막기 | 44 |
| [jirugi](jirugi/index.md) | Les frappes de la main : poings, piques, coudes — 지르기 | 21 |
| [Techniques](Techniques/index.md) | Techniques complètes : position + blocage ou frappe combinés | 12 |
| [Theorie](Theorie/index.md) | Théorie, lexique, grammaire ITF, histoire des formes, analyses | 11 |
| [images](images/index.md) | Diagrammes des formes et schémas des positions | 37 |

---

## Comment s'y retrouver

**Si vous préparez un passage de grade** → commencez par [Ceintures/index.md](Ceintures/index.md), qui donne pour chaque grade la théorie, les formes, le lexique et les exigences physiques.

**Si vous cherchez une technique précise** → l'index du répertoire correspondant ([chagi](chagi/index.md), [makgi](makgi/index.md), [jirugi](jirugi/index.md)) classe les fiches par famille de mouvement, avec le nom français en regard du nom coréen.

**Si vous cherchez un terme coréen** → [Theorie/Lexique.md](Theorie/Lexique.md) (français – anglais – coréen) et [Theorie/grammaire-itf.md](Theorie/grammaire-itf.md) (règles de construction des noms de techniques).

**Si vous travaillez une forme** → [tul/index.md](tul/index.md) mène à la fiche de chaque forme (mouvement par mouvement) ; [Theorie/encyclopedie-historique-tuls.md](Theorie/encyclopedie-historique-tuls.md) en donne le sens et l'histoire.

---

## Convention de nommage

Un nom de technique ITF se lit dans l'ordre : **position → surface de frappe → niveau → direction → action**.

> *Gunnun So Bakat Palmok Nopunde Yop Makgi* = en position de marche, avec l'avant-bras externe, au niveau haut, blocage latéral.

Les fiches de [Techniques](Techniques/index.md) suivent cette construction complète ; celles de [chagi](chagi/index.md), [makgi](makgi/index.md) et [jirugi](jirugi/index.md) isolent un seul élément du vocabulaire. La règle est détaillée dans [Theorie/grammaire-itf.md](Theorie/grammaire-itf.md).

---

## Génération du site

Deux scripts convertissent ce dépôt en site consultable :

* [import-local.sh](import-local.sh) — convertit tous les `.md` en `.html` via Pandoc dans `public_html/`, en préservant l'arborescence et en réécrivant les liens internes.
* [import-wp.sh](import-wp.sh) — importe les images dans la médiathèque WordPress puis publie chaque fiche comme article, via WP-CLI.
