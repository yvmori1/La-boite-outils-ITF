# Analyse statistique des formes

Combien de fois chaque position et chaque technique revient-elle dans les formes du Taekwon-Do ITF ? Cette page répond par des comptes, tirés des fiches de [tul](../tul/README.md) du site.

## Méthode

Chaque mouvement des 28 fiches de formes (les 24 tuls, Ko-Dang et les trois exercices Saju) renvoie par un lien à la fiche de sa technique. Le script `scripts/statistiques-formes.py` compte le nom coréen porté par ces liens : **1 048 techniques nommées** pour 1 030 mouvements (un mouvement peut en enchaîner deux). Le côté (*Wen*, *Orun*) est ignoré ; tout le reste du nom distingue les techniques.

Les chiffres décrivent donc les fiches du site, pas un relevé officiel de l'ITF. Ils changent si une fiche de forme est corrigée : il suffit alors de relancer le script.

## 1. Les positions (Sogi)

| Position | Occurrences | Part |
| :--- | ---: | ---: |
| Gunnun Sogi (marche) | 371 | 35,4 % |
| Niunja Sogi (en L) | 216 | 20,6 % |
| Sans position nommée | 202 | 19,3 % |
| Annun Sogi (assise) | 125 | 11,9 % |
| Dwitbal Sogi (pied arrière) | 33 | 3,1 % |
| Kyocha Sogi (croisée) | 30 | 2,9 % |
| Moa Sogi (fermée) | 18 | 1,7 % |
| Gojung Sogi (fixe) | 16 | 1,5 % |
| Narani Sogi (parallèle) | 13 | 1,2 % |
| Waebal Sogi (sur une jambe) | 10 | 1,0 % |
| Nachuo Sogi (basse) | 9 | 0,9 % |
| Sasun Sogi (diagonale) | 3 | 0,3 % |
| Soojik Sogi (verticale) | 2 | 0,2 % |

Trois positions portent près de 70 % des techniques : la position de marche (*Gunnun Sogi*), la position en L (*Niunja Sogi*) et la position assise (*Annun Sogi*). La ligne « Sans position nommée » regroupe surtout les coups de pied, dont le nom n'indique pas de position, et les techniques qui gardent la position du mouvement précédent.

*Chon-Ji* montre cette répartition dès le 9e Gup : ses huit premiers mouvements se font en position de marche, les suivants alternent la position en L pour les blocages et la position de marche pour les coups de poing.

## 2. Les grandes familles de techniques

| Famille | Occurrences | Part |
| :--- | ---: | ---: |
| Blocages | 424 | 40,5 % |
| Attaques de la main et du coude | 423 | 40,4 % |
| Coups de pied | 151 | 14,4 % |
| Positions seules (préparation) | 32 | 3,1 % |
| Autres (sauts, saisies, déplacements) | 18 | 1,7 % |

Blocages et attaques de la main s'équilibrent presque exactement. Les coups de pied ne représentent qu'un septième des techniques des formes, alors qu'ils dominent le combat libre.

## 3. Les attaques de la main et du coude

| Attaques de la main et du coude | Occurrences | Part |
| :--- | ---: | ---: |
| Gunnun so kaunde jirugi | 42 | 4,0 % |
| Gunnun so kaunde bandae jirugi | 34 | 3,2 % |
| Gunnun so nopunde jirugi | 18 | 1,7 % |
| Annun so joomuk kaunde jirugi | 18 | 1,7 % |
| Niunja so kaunde baro jirugi | 14 | 1,3 % |
| Niunja so yop palkup tulgi | 13 | 1,2 % |
| Niunja so sonkal kaunde bakuro taerigi | 10 | 1,0 % |
| Gunnun so sang joomuk nopunde sewo jirugi | 10 | 1,0 % |

Le coup de poing moyen en position de marche (*Gunnun So Kaunde Jirugi*), avant ou inversé, est de loin l'attaque la plus fréquente : on le retrouve dans presque toutes les formes, de *Saju Jirugi* à *Tong-Il*.

## 4. Les blocages

| Blocages | Occurrences | Part |
| :--- | ---: | ---: |
| Niunja so sonkal kaunde daebi makgi | 42 | 4,0 % |
| Niunja so palmok kaunde daebi makgi | 24 | 2,3 % |
| Gunnun so an palmok dollimyo makgi | 14 | 1,3 % |
| Gunnun so palmok najunde makgi | 13 | 1,2 % |
| Annun so bakat palmok san makgi | 13 | 1,2 % |
| Gunnun so palmok chookyo makgi | 12 | 1,1 % |
| Niunja so sonkal najunde daebi makgi | 10 | 1,0 % |
| Gunnun so bakat palmok nopunde yop makgi | 10 | 1,0 % |

Le blocage de garde moyen en position en L, du tranchant de la main (*Sonkal Daebi Makgi*) ou de l'avant-bras (*Palmok Daebi Makgi*), est le blocage le plus répété des formes.

## 5. Les coups de pied

| Coups de pied | Occurrences | Part |
| :--- | ---: | ---: |
| Kaunde yopcha jirugi | 28 | 2,7 % |
| Nopunde yopcha jirugi | 13 | 1,2 % |
| Nopunde bandae dollyo gorochagi | 10 | 1,0 % |
| Kaunde apcha busigi | 10 | 1,0 % |
| Najunde apcha busigi | 10 | 1,0 % |
| Kaunde dollyo chagi | 7 | 0,7 % |
| Nopunde dollyo chagi | 6 | 0,6 % |
| Kaunde dwitcha jirugi | 6 | 0,6 % |

Le coup de pied latéral perçant (*Yopcha Jirugi*) est le plus fréquent, suivi du coup de pied avant (*Apcha Busigi*). Le coup de pied circulaire (*Dollyo Chagi*), très présent en combat, reste rare dans les formes.

## 6. Un petit noyau, un long répertoire

Les 1 048 techniques nommées correspondent à **303 techniques distinctes**. Les 42 plus fréquentes (14 %) couvrent la moitié des occurrences ; il en faut 151 (50 %) pour atteindre 80 %.

La « loi des 20/80 » ne s'applique donc pas aux formes : un noyau d'une quarantaine de techniques en fait la moitié, mais le reste du répertoire est très étalé, et chaque forme supérieure apporte des techniques qu'on ne retrouve presque nulle part ailleurs. Travailler ce noyau avec soin est utile, sans dispenser d'apprendre le reste.

## Voir aussi

* [Les formes une à une](manuel/partie-6-formes-tul/24-les-formes-une-a-une.md) — sens et histoire de chaque forme.
* [Techniques](../Techniques/README.md) — la fiche de chacune des techniques citées.
