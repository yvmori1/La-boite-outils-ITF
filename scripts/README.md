# Scripts d'entretien

Outils de maintenance du dépôt. Tous sont **en essai à blanc par défaut** :
il faut `--write` pour qu'ils modifient quoi que ce soit, et tous sont
**idempotents** — les relancer sans changement ne produit rien.

Aucune dépendance à installer : Python 3 seul. La synthèse vocale utilise
`say` et `afconvert`, donc macOS.

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
