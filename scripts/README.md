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
| [verifier.py](verifier.py) | Neuf contrôles d'intégrité, n'écrit jamais |
| [generer-index-techniques.py](generer-index-techniques.py) | Reconstruit `Techniques/README.md` |
| [lier-mouvements.py](lier-mouvements.py) | Lie les mouvements des formes aux fiches techniques |
| [generer-mvt.py](generer-mvt.py) | Reconstruit `mvt.txt` |
| [generer-audio.py](generer-audio.py) | Prononciations coréennes et liens vers l'audio |
| [generer-sogi.py](generer-sogi.py) | Dessine les schémas de pieds des positions dans `images/sogi/` |
| [generer-manuel.py](generer-manuel.py) | Assemble `Theorie/manuel-taekwon-do.md` à partir des quatre fiches de fond |

### maintenir.py

Étapes, dans un ordre où chacune dépend des précédentes : index de `Techniques/`,
compteurs du README racine, normalisation des graphies, liens des formes,
`mvt.txt`, prononciations, réparation des audio manquants, contrôle final.

`--sans-audio` saute la synthèse vocale, de loin l'étape la plus longue.

### verifier.py

Liens Markdown morts · liens audio morts · fichiers audio orphelins · fiches
vides · compteurs du README racine · index Techniques à jour · `mvt.txt` à jour ·
graphies concurrentes · couverture des formes.

Les graphies surveillées sont déclarées en tête du fichier (`GRAPHIES`) : une
forme de référence et ses variantes fautives. Ajouter une paire suffit à
surveiller un nouveau terme.

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
python3 scripts/generer-audio.py --write              # fiches
python3 scripts/generer-audio.py --lexique --write    # Theorie/Lexique.md
python3 scripts/generer-audio.py --grammaire --write  # Theorie/grammaire-itf.md
python3 scripts/generer-audio.py --reparer --write    # audio manquants
```

Le hangul est lu dans les fiches ; ce qui en est absent vient des tables
`NOMS_TUL` et `LEXIQUE_HANGUL`, en tête du fichier — **elles ne proviennent pas
du dépôt et méritent vérification**. Deux textes coréens identiques partagent
toujours le même enregistrement.

`--reparer` reproduit l'audio de tout lien dont le fichier a disparu : c'est ce
qui permet de corriger une graphie sans effort — corriger le texte, supprimer
l'audio devenu faux, relancer.

### generer-sogi.py

```sh
python3 scripts/generer-sogi.py                        # liste les 22 schémas
python3 scripts/generer-sogi.py --write                # écrit images/sogi/*.png
python3 scripts/generer-sogi.py --write --only niunja-sogi
```

Dessine, vue de dessus, la position des pieds des 21 positions de
[../Theorie/grammaire-itf.md](../Theorie/grammaire-itf.md) — *Palja Sogi* donnant
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

### generer-manuel.py

```sh
python3 scripts/generer-manuel.py           # résumé, n'écrit rien
python3 scripts/generer-manuel.py --write   # écrit Theorie/manuel-taekwon-do.md
```

Réunit [../Theorie/Genes.md](../Theorie/Genes.md),
[../Theorie/grammaire-itf.md](../Theorie/grammaire-itf.md),
[../Theorie/mouvement_de_vagues.md](../Theorie/mouvement_de_vagues.md) et
[../Theorie/Lexique.md](../Theorie/Lexique.md) en un seul manuel ordonné pour
l'apprentissage. Le texte n'est pas recopié : il est **extrait des sources à
chaque exécution**, donc corriger une fiche suffit — le manuel suit.

Seuls les passages qui existaient en double sont réécrits, dans le dictionnaire
`FUSIONS` en tête du fichier, chacun avec la raison de la fusion : le crédo, les
principes de position, les modificateurs de nomenclature et les verbes d'action.
Les autres doublons sont résolus en ne retenant que la version la plus riche —
l'en-tête du script en tient la liste.

Ajouter un chapitre tient en une ligne dans `manuel()` : un titre, puis
`extrait(source, "titre de la section")`. Le script s'arrête net si une section
citée n'existe plus, ce qui signale tout de suite un titre renommé à la source.
