Tu as déjà corrigé toi‑même trois points : l'indexation de `seen_cards` (`range(1, n+1)`), le typo `is_critical_hint`, et l'ajout du test « encore utile » (`g.piles[color] <= value - 1`). 👍

D'abord, une rectification de ma part : **les deux seuils `total-1` / `total` ne sont PAS une incohérence** — je m'étais trompé. La différence est correcte et nécessaire :
- `is_critical` (ma carte) : `seen` compte les **autres** copies (mains adverses + mes défausses), ma carte n'y est pas → seuil `total-1`.
- `is_critical_hint` (carte adverse) : `seen` **inclut** la carte visée (comptée à sa distribution) → seuil `total`, soit `(seen-1) ≥ total-1` pour les autres copies.

Donc ça, on n'y touche pas. Restent **deux vraies incohérences** : la **priorité de la règle 2 ter** et la **mutation spéculative** `kn.special = True`. Je les corrige et j'écris le fichier corrigé.

Maintenant je vérifie : (1) les 16 tests modes 1‑7, (2) un scénario mode 8 ciblant la défausse critique et l'indication critique.

16/16 toujours bons. Maintenant je teste le **mode 8** directement en pilotant les méthodes (plus fiable qu'un scénario protocole complet pour cibler chaque règle) :

Tout est vert. Récapitulatif de ce que j'ai corrigé (et de ce qui n'était pas un vrai problème) :

## Corrections appliquées

**1. 🟠→✅ Priorité de la règle 2 ter** (la vraie incohérence avec `extension.md`)
La protection des cartes critiques est désormais une règle à part, `rule_protect_critical()`, placée **en tête** de `smart_action()` :
```python
return (self.rule_protect_critical()  # 2ter — avant même de jouer
        or self.rule_special_play()
        or self.rule_play()
        or self.rule_hint()
        or self.rule_discard())
```
Le test **T3** le prouve : alors que `rule_play()` voudrait jouer ma carte (`e 1`), `smart_action()` renvoie `i 2 1` — il protège d'abord la carte critique de l'adversaire, exactement comme le dit `extension.md` (« avant même de chercher une carte directement empilable »). Elle scanne **tous** les joueurs/positions, ce qui corrige aussi le problème de priorité seulement « locale ».

**2. 🟡→✅ Mutation spéculative supprimée**
J'ai retiré le `kn.special = True` qui modifiait l'état d'un autre joueur depuis une fonction de décision. C'était redondant : quand on émet `i j v`, le serveur renvoie l'écho du hint (visible dans les samples, ex. `00-7-p1-1.in`), et `on_value_hint`/`on_color_hint` positionne `special` correctement. Les décisions sont maintenant **pures**.

**3. 📝 Comptage des piles : documenté comme volontairement omis**
`extension.md` parlait de compter « + piles », mais grâce à ton garde `piles[c] <= v-1`, une carte déjà posée n'est jamais critique et une copie jouée ne peut pas changer le verdict → compter les piles serait du code mort. Je l'ai expliqué en commentaire plutôt que d'ajouter du code inutile.

## Ce qui n'était PAS une incohérence (ma méprise)

Les seuils **`total-1`** (`is_critical`) vs **`total`** (`is_critical_hint`) sont **corrects**. Ils diffèrent parce que `seen` n'inclut pas ma propre carte (→ `total-1`) mais inclut la carte de l'adversaire comptée à sa distribution (→ `total`). Test **T2** confirme. Je les ai laissés, avec un commentaire qui explique le décalage de 1.

## Limite irréductible (à connaître)

On **ne peut pas** suivre les défausses des *autres* joueurs : le protocole ne te donne jamais l'identité d'une carte qu'un adversaire défausse (tu ne vois que sa carte de remplacement). Le compteur `seen_cards` reste donc une approximation *conservatrice* (il a tendance à « surprotéger »), ce qui va dans le bon sens pour éviter les pertes. C'est une limite de la stratégie de `extension.md`, pas un bug.

Le fichier corrigé est écrit dans [hanabi.py](hanabi.py), les 16 tests modes 1‑7 passent toujours, et les 4 tests ciblés du mode 8 (T1–T4) valident le comportement.