# La boîte à outils ITF

Recueil de référence du Taekwon-Do ITF en français, publié sur
[outils.hosinsul.ca](https://outils.hosinsul.ca/). La page d'accueil du site
est [docs/README.md](docs/README.md).

Ce fichier s'adresse aux contributeurs : il explique où se trouve quoi dans le
dépôt. Pour une question ou une suggestion, les
[Discussions](https://github.com/yvmori1/La-boite-outils-ITF/discussions) sont
ouvertes à tous.

## Où se trouve quoi

Tout le contenu du site est dans [docs/](docs/), rangé **comme le menu du
site** : un dossier par partie du Manuel, avec les fiches qui la mettent en
pratique.

| Dossier | Dans le menu |
| :--- | :--- |
| [docs/README.md](docs/README.md) | Accueil |
| [docs/sommaire.md](docs/sommaire.md) | Sommaire du Manuel |
| [docs/1-art-et-voie/](docs/1-art-et-voie/) | I. L'art et sa voie |
| [docs/2-principes-physiques/](docs/2-principes-physiques/) | II. Les principes physiques |
| [docs/3-grammaire-des-techniques/](docs/3-grammaire-des-techniques/) | III. La grammaire des techniques |
| [docs/4-positions/](docs/4-positions/) | IV. Les positions (Sogi) ; fiches des positions dans `fiches/` |
| [docs/5-repertoire-technique/](docs/5-repertoire-technique/) | V. Le répertoire technique ; fiches dans `jirugi/`, `makgi/`, `chagi/` et `combinees/` (techniques combinées) |
| [docs/6-formes/](docs/6-formes/) | VI. Les formes (Tul), chapitres 20 à 26 ; fiches des formes dans `fiches/` |
| [docs/7-combat/](docs/7-combat/) | VII. Combat, autodéfense et casse ; `combats-arranges/`, `hosinsul-par-grade/` |
| [docs/8-progression/](docs/8-progression/) | VIII. La progression : `ceintures/` (Requis Examen), `programme-session/`, `examens/` |
| [docs/annexes/](docs/annexes/) | Annexes : A lexique, B glossaire, C analyse statistique, D bibliographie |
| [docs/a-propos/](docs/a-propos/) | À propos : application, confidentialité |
| [docs/audio/](docs/audio/), [docs/images/](docs/images/) | Prononciations et images, liées depuis les fiches |
| [docs/assets/](docs/assets/) | Feuille de style et scripts du site |

Chaque partie se termine par `revision.md`, la révision de fin de partie.

Hors du site :

* [mkdocs.yml](mkdocs.yml) : configuration de MkDocs, dont les redirections
  des anciennes adresses ;
* [menu.yml](menu.yml) : le plan du menu (titres et ordre) ;
* [scripts/](scripts/README.md) : outils d'entretien (contrôles, index,
  prononciations) ; [scripts/chemins.py](scripts/chemins.py) décrit
  l'arborescence pour tous les scripts ;
* [hooks/](hooks/), [overrides/](overrides/), [includes/](includes/) :
  extensions de MkDocs ;
* [encyclopedie/](encyclopedie/README.md) : notes de travail sur
  l'Encyclopédie, non publiées.

## Contribuer

1. Modifier ou ajouter une fiche dans le dossier de sa partie. Une fiche
   ajoutée dans un dossier de fiches apparaît d'elle-même dans le menu ; une
   nouvelle page de premier niveau s'ajoute dans [menu.yml](menu.yml).
2. Remettre le dépôt en cohérence (index, fiches liées, menus, mise en forme) :

   ```sh
   pip install -r requirements.txt
   python3 scripts/maintenir.py --write
   ```

3. Vérifier, puis prévisualiser le site sur <http://127.0.0.1:8000> :

   ```sh
   python3 scripts/verifier.py
   mkdocs build --strict
   mkdocs serve
   ```

Les liens entre fiches sont des liens Markdown relatifs, comme
`../fiches/chon-ji.md` : ils fonctionnent à la fois sur GitHub et sur le site. Les règles de mise en
forme sont dans [scripts/README.md](scripts/README.md).

Un fichier déplacé change d'adresse sur le site : ajouter alors l'ancienne
adresse dans `redirect_maps` de [mkdocs.yml](mkdocs.yml), pour ne pas casser
les liens déjà publiés. Ne pas déplacer `docs/googlec4a229f0d9aae752.html`
(vérification Google Search Console) ni `docs/robots.txt`.
