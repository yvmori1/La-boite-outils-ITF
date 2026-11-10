# Scripts d'entretien

Outils de maintenance du dépôt. Tous sont **en essai à blanc par défaut** :
il faut `--write` pour qu'ils modifient quoi que ce soit, et tous sont
**idempotents** — les relancer sans changement ne produit rien.

Aucune dépendance à installer : Python 3 seul — sauf
[generer-sogi.py](generer-sogi.py), qui dessine et demande `matplotlib`. La
synthèse vocale utilise `say` et `afconvert`, donc macOS.

## Au quotidien

Après avoir ajouté des fiches, renommé un fichier ou corrigé une romanisation :

```sh
python3 scripts/maintenir.py            # ce qui serait fait
python3 scripts/maintenir.py --write    # tout remettre en cohérence
```

Pour seulement vérifier, sans rien changer :

```sh
python3 scripts/verifier.py
```

`verifier.py` rend un code de sortie non nul en cas d'anomalie : il peut servir
de hook `pre-commit` ou d'étape d'intégration continue.

## Les scripts

| Script | Rôle |
| :--- | :--- |
| [maintenir.py](maintenir.py) | Enchaîne tous les autres dans l'ordre, puis contrôle |
| [verifier.py](verifier.py) | Onze contrôles d'intégrité, n'écrit jamais |
| [generer-index-techniques.py](generer-index-techniques.py) | Reconstruit `Techniques/README.md` |
| [generer-voir-aussi.py](generer-voir-aussi.py) | Bloc « Fiches liées » en bas des fiches : position, geste de base, techniques, formes |
| [generer-menus.py](generer-menus.py) | Écrit le menu (`.pages`) de sogi, chagi, makgi, jirugi et Techniques d'après leur sommaire |
| [lier-mouvements.py](lier-mouvements.py) | Lie les mouvements des formes aux fiches techniques |
| [generer-audio.py](generer-audio.py) | Prononciations coréennes et liens vers l'audio |
| [romanisation.py](romanisation.py) | Nom de fichier romanisé d'un hangul (utilisé par `generer-audio.py`) |
| [generer-sogi.py](generer-sogi.py) | Dessine les schémas de pieds des positions dans `images/sogi/` |
| [generer-points-vitaux.py](generer-points-vitaux.py) | Dessine les trois planches des 49 points vitaux dans `images/points-vitaux/` |
| [generer-icones.py](generer-icones.py) | Tire du logo Hosinsul (`images/logo/hosinsul.svg`) la version à liseré blanc du site, l'icône d'onglet (les orteils) et les icônes de l'application dans `docs/assets/icones/` (demande cairosvg et Pillow) |
| [generer-manuel.py](generer-manuel.py) | Hors service : assemblait l'ancien manuel d'un seul tenant |
| [formater-markdown.py](formater-markdown.py) | Met les listes en forme pour qu'elles s'affichent pareil sur GitHub et sur le site |

### maintenir.py

Étapes, dans un ordre où chacune dépend des précédentes : index de `Techniques/`,
compteurs du README racine, normalisation des graphies (y compris les hangul
fautifs relevés par le glossaire), liens des formes, fiches liées, prononciations
de tout le site, réparation des audio manquants, index de `Techniques/` une
seconde fois, menus des sections, mise en forme Markdown, contrôle final.

`--sans-audio` saute la synthèse vocale, de loin l'étape la plus longue.

### verifier.py

Liens Markdown morts · liens audio morts · fichiers audio orphelins · fiches
vides · compteurs du README racine · index Techniques à jour · fiches liées à jour · menus à jour ·
graphies concurrentes · couverture des formes · mise en forme Markdown.

Les graphies surveillées sont déclarées en tête du fichier (`GRAPHIES`) : une
forme de référence et ses variantes fautives. Ajouter une paire suffit à
surveiller un nouveau terme.

### formater-markdown.py

Le site est construit par MkDocs (Python-Markdown), plus strict que
l'affichage des fichiers sur GitHub. Pour qu'un fichier s'affiche pareil des
deux côtés :

* **indenter chaque niveau de liste imbriquée de 4 espaces** (2 ou 3 espaces
  suffisent à GitHub, mais MkDocs aplatit alors la liste) ;
* **laisser une ligne vide entre un paragraphe et la liste qui le suit**, y
  compris dans une citation (`>` seul sur la ligne) ;
* **écrire `<details markdown="1">`** plutôt que `<details>`, sans quoi MkDocs
  affiche le Markdown du bloc tel quel.

Le script applique ces trois règles ; `verifier.py` signale tout fichier qui
s'en écarte. Les encadrés `!!! note` restent propres au site : GitHub les
affiche en texte simple.

### generer-index-techniques.py

Classe chaque fiche d'après son nom de fichier — posture, position d'appui,
coup de pied, ou sans position. Une position inconnue crée sa propre section ;
lui donner un libellé français se fait dans la liste `POSITIONS`.

### lier-mouvements.py

```sh
python3 scripts/lier-mouvements.py --couverture           # état par forme, en %
python3 scripts/lier-mouvements.py --couverture --detail  # techniques manquantes
python3 scripts/lier-mouvements.py --manquants            # classement global
```

Un lien est toujours un fragment réel du nom du mouvement ; quand la fiche
exacte n'existe pas, il pointe vers l'explication la plus proche.

### generer-audio.py

```sh
python3 scripts/generer-audio.py --write            # fiches
python3 scripts/generer-audio.py --manuel --write   # pages de Theorie/manuel/
python3 scripts/generer-audio.py --combats --write  # pages de Combat/
python3 scripts/generer-audio.py --reparer --write  # audio manquants
python3 scripts/generer-audio.py --tout --write     # chaque hangul du site
```

`--tout` étend ce traitement à **tous** les documents publiés : chaque hangul
d'une fiche, d'un README, du glossaire, du manuel ou de Combat/ devient un lien
vers sa prononciation (sauf le titre « # » de la page, les blocs de code et ce
qui est déjà un lien). Les nouveaux enregistrements hors manuel et Combat/ vont
dans `audio/termes/`, sous le nom romanisé du hangul (`yopcha-tulgi.m4a`,
voir [romanisation.py](romanisation.py)). C'est ce que lance
`maintenir.py`.

Hors macOS, `--sans-synthese` ne lie que les hangul dont l'audio existe déjà et
compte les autres « en attente » ; `maintenir.py` l'ajoute de lui-même quand
`say` est absent. Le passage suivant sur Mac produit et lie le reste.

La ligne « 🔊 **Prononciation :** » d'une fiche fait foi : son audio dit
exactement ce qu'elle affiche. Pour corriger une graphie, corriger le texte,
supprimer l'audio devenu faux, puis relancer `maintenir.py --write` sur Mac.

`--manuel` et `--combats` traitent un document de fond entier : chaque hangul y
devient un lien vers sa prononciation. Les documents et leur sous-dossier audio
sont déclarés dans la table `DOCUMENTS`, en tête du fichier. `--manuel` remplace
les anciens `--lexique` et `--grammaire`, dont les deux fiches sont désormais
fusionnées dans le manuel ; les deux noms restent acceptés et font la même chose.

Le hangul est lu dans les fiches ; ce qui en est absent vient de la table
`NOMS_TUL`, en tête du fichier — **elles ne proviennent pas
du dépôt et méritent vérification**. Deux textes coréens identiques partagent
toujours le même enregistrement.

`--reparer` reproduit l'audio de tout lien dont le fichier a disparu : c'est ce
qui permet de corriger une graphie sans effort — corriger le texte, supprimer
l'audio devenu faux, relancer.

### generer-points-vitaux.py

```sh
python3 scripts/generer-points-vitaux.py           # liste ce qui serait écrit
python3 scripts/generer-points-vitaux.py --write   # écrit images/points-vitaux/*.svg
```

Dessine en SVG la tête de profil, le corps de face et le corps de dos, avec les
49 points vitaux de [Combat/points-vitaux.md](../Combat/points-vitaux.md) placés
d'après les croquis de l'Encyclopédie (p. 108-111). Les noms et les termes
coréens sont lus dans le tableau de la page : après une correction de nom,
relancer avec `--write`. `verifier.py` signale des planches en retard.

### generer-sogi.py

```sh
python3 scripts/generer-sogi.py                        # liste les 22 schémas
python3 scripts/generer-sogi.py --write                # écrit images/sogi/*.png
python3 scripts/generer-sogi.py --write --only niunja-sogi
```

Dessine, vue de dessus, la position des pieds des 21 positions de la
[partie IV du manuel](../Theorie/manuel/partie-4-positions-sogi/README.md) — *Palja Sogi* donnant
deux schémas, intérieur et extérieur. Voir [../images/sogi/](../images/sogi/README.md).

Chaque pied est posé par un repère nommé — talon, talon interne, gros orteil,
petit orteil, centre, bord interne — et jamais à l'œil : les distances du schéma
sont donc bien celles de la position, et « talons collés » ou « bords internes
en contact » se dessinent sans chevauchement. La géométrie est calculée sur les
dimensions standard (épaule 47 cm, pied 25 × 9 cm), mais les cotes se libellent
toujours en largeurs d'épaule, jamais en centimètres. Le contour de pied vient
des tracés de [../images/gojung-sogi.svg](../images/gojung-sogi.svg).

Chaque schéma est une vignette carrée de 350 × 350 pixels : le cadrage s'ajuste
au dessin, et les textes, de taille fixe sur la vignette, sont pris en compte
par quelques itérations avant le rendu.

Ajouter une position tient en une fonction décorée par `@position(slug, titre)` :
elle pose ses pieds, puis ses cotes (`cote_v`, `cote_h`, `angle`, `note`,
`poids`). Le cadrage et la taille du fichier s'en déduisent.

Ce script n'est pas enchaîné par `maintenir.py` : les images ne changent que
lorsqu'une mesure change.

### generer-manuel.py — hors service

Ce script assemblait l'ancien `Theorie/manuel-taekwon-do.md`, d'un seul tenant, à
partir de quatre fiches de théorie — `Genes.md`, `grammaire-itf.md`,
`mouvement_de_vagues.md` et `Lexique.md`. Ces quatre fiches ayant été fusionnées
dans le manuel puis supprimées, **il ne peut plus s'exécuter** : le manuel est
désormais entretenu directement, découpé en une page par chapitre dans
[../Theorie/manuel/](../Theorie/manuel/README.md).

Le fichier est conservé pour mémoire de la façon dont le manuel a été composé —
l'ordre des parties, et le dictionnaire `FUSIONS` qui note, passage par passage,
pourquoi deux versions d'un même contenu ont été refondues en une.

### telechargements.py — téléchargements de hors-ligne.zip

Chaque publication du site dépose `hors-ligne.zip` dans une Release GitHub, dont
GitHub compte les téléchargements. Ce script les additionne, Release par Release :

```sh
python3 scripts/telechargements.py
```

Les visites, les clics sur les liens du zip et les installations de
l'application sont comptés à part, par GoatCounter
(<https://hosinsul.goatcounter.com>, voir `docs/assets/statistiques.js`).
