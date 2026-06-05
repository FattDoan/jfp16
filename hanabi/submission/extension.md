# Mode 8 : Éviter les défausses inutiles

## Idée

En mode 7, un joueur peut se retrouver à défausser une carte qui est encore utile
(valeur non encore jouée sur la pile correspondante), faute d'information suffisante.
Le mode 8 ajoute une règle de sécurité avant la défausse, et raffine la stratégie
d'indication pour protéger les cartes rares.

## Règle 4 : Ne pas défausser une carte potentiellement critique

Avant de défausser, le joueur calcule pour chaque carte en main un **score de danger** :
une carte est dite *critique* si elle est le dernier exemplaire jouable d'une valeur/couleur
(c'est-à-dire qu'il n'existe qu'un seul exemplaire restant dans le jeu pour cette combinaison).

Si parmi les cartes candidates à la défausse (selon la règle 3 bis), la moins ancienne
n'est pas critique, on la choisit. Sinon, on cherche une carte non critique à défausser
(toujours avec la priorité sur la date puis la position). Si toutes les cartes candidates
sont critiques, on continue quand même avec la règle 3 bis classique.

Pour évaluer si une carte est critique, on maintient un compteur des cartes visibles
(mains des autres joueurs + piles) et on en déduit ce qui reste dans la pioche/notre main.

## Règle 2 ter : Protéger les cartes critiques

Si un autre joueur possède une carte critique (dernière de son type, pas encore jouée,
empilable dans un futur proche) et qu'il ne sait pas qu'elle est spéciale, on lui envoie
une indication — de préférence spéciale si possible — avant même de chercher une carte
directement empilable.

## Intérêt

Ces deux règles réduisent les pertes irrémédiables (cartes jetées qui bloquent définitivement
une couleur), ce qui est le principal obstacle à un score élevé en mode 7. En pratique,
éviter une seule défausse critique peut valoir 3 à 5 points de plus en fin de partie.

## Codabilité

- La détection des cartes critiques nécessite un compteur par (valeur, couleur) des cartes
  vues (mains adverses + défausse). Ce compteur est maintenable en O(1) par message `n` ou `d`.
- Les règles 4 et 2 ter s'insèrent directement dans les méthodes `_rule_discard()` et
  `_rule_hint()` de la classe `Agent`, avec quelques dizaines de lignes de Python.
- Estimation : 45-60 minutes de développement supplémentaire.
