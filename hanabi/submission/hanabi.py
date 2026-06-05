#!/usr/bin/env python3
"""Joueur automatique pour le jeu Hanabi (JFP 16).

Le programme dialogue avec la table de jeu via stdin/stdout. Il gère les
modes 1 à 7 décrits dans le sujet. L'architecture est découpée en quatre
responsabilités :

  * Card       : l'identité physique d'une carte (valeur + couleur).
  * Knowledge  : ce que le propriétaire d'une carte sait de celle-ci.
  * Player     : la main d'un joueur (cartes + connaissances par position).
  * GameState  : l'état global de la partie (piles, vies, jetons, joueurs).
  * Agent      : la logique de décision, branchée selon le mode.

Le bloc final (`Protocol`) lit les messages et les route vers l'agent.
"""
import sys


class Card:
    """Identité physique d'une carte. Un champ inconnu vaut None."""

    def __init__(self, value=None, color=None):
        self.value = value  # int ou None
        self.color = color  # str ('A'..) ou None

    @property
    def visible(self):
        return self.value is not None and self.color is not None

    def __str__(self):
        v = self.value if self.value is not None else '?'
        c = self.color if self.color is not None else '?'
        return f"{v}{c}"


class Knowledge:
    """Ce que le propriétaire d'une carte sait d'elle (indices + déductions)."""

    def __init__(self, date=0):
        self.value = None          # valeur connue, ou None
        self.color = None          # couleur connue, ou None
        self.neg_values = set()    # valeurs dont on sait que ce n'est PAS
        self.neg_colors = set()    # couleurs dont on sait que ce n'est PAS
        self.special = False       # a reçu une indication spéciale (mode 7)
        self.date = date           # tour d'arrivée de la carte (mode 6)

    @property
    def complete(self):
        return self.value is not None and self.color is not None

    def deduce(self, all_values, all_colors):
        """Mode 5 : déduit le champ restant quand tous les autres sont exclus."""
        if self.value is None:
            remaining = all_values - self.neg_values
            if len(remaining) == 1:
                self.value = next(iter(remaining))
        if self.color is None:
            remaining = all_colors - self.neg_colors
            if len(remaining) == 1:
                self.color = next(iter(remaining))

    def __str__(self):
        v = self.value if self.value is not None else '?'
        c = self.color if self.color is not None else '?'
        return f"{v}{c}"


class Player:
    """La main d'un joueur : une carte et sa connaissance par position."""

    def __init__(self, k):
        self.k = k
        self.cards = {p: Card() for p in range(1, k + 1)}
        self.knowledge = {p: Knowledge() for p in range(1, k + 1)}

    def positions(self):
        return range(1, self.k + 1)

    def receive_card(self, p, value, color, date):
        self.cards[p] = Card(value, color)
        self.knowledge[p] = Knowledge(date)


class GameState:
    """État global de la partie."""

    def __init__(self, k, n, moi, mode):
        self.k = k
        self.n = n
        self.moi = moi
        self.mode = mode
        self.lives = 3
        self.tokens = 8
        self.piles = {c: 0 for c in self._all_colors(k)}
        self.players = {j: Player(k) for j in range(1, n + 1)}
        self.current_turn = 0   # "temps" : incrémenté à chacun de nos tours
        self.global_turn = 0    # incrémenté à chaque message 't'

    @staticmethod
    def _all_colors(k):
        return [chr(ord('A') + i) for i in range(k)]

    @property
    def colors(self):
        return self._all_colors(self.k)

    @property
    def value_set(self):
        return set(range(1, self.k + 1))

    @property
    def color_set(self):
        return set(self.colors)

    def me(self):
        return self.players[self.moi]

    def is_playable(self, value, color):
        return self.piles.get(color, 0) == value - 1

    def next_player(self):
        return 1 + (self.moi % self.n)


class Agent:
    """Reçoit les évènements de la partie et décide des actions."""

    def __init__(self):
        self.game = None

    # ---- Mise à jour de l'état ------------------------------------------

    def start_game(self, k, n, moi, mode):
        self.game = GameState(k, n, moi, mode)

    def on_new_card(self, j, p, value, color):
        g = self.game
        g.players[j].receive_card(p, value, color, g.global_turn)

    def on_value_hint(self, j, value, bits):
        g = self.game
        special = (sum(bits) == 1)
        player = g.players[j]
        for p in player.positions():
            kn = player.knowledge[p]
            if bits[p - 1] == 1:
                if kn.value is None:
                    kn.value = value
                if g.mode >= 7 and special:
                    kn.special = True
            else:
                kn.neg_values.add(value)
            if g.mode >= 5:
                kn.deduce(g.value_set, g.color_set)

    def on_color_hint(self, j, color, bits):
        g = self.game
        special = (sum(bits) == 1)
        player = g.players[j]
        for p in player.positions():
            kn = player.knowledge[p]
            if bits[p - 1] == 1:
                if kn.color is None:
                    kn.color = color
                if g.mode >= 7 and special:
                    kn.special = True
            else:
                kn.neg_colors.add(color)
            if g.mode >= 5:
                kn.deduce(g.value_set, g.color_set)

    def on_state(self, lives, tokens, pile_heights):
        g = self.game
        g.lives = lives
        g.tokens = tokens
        for c, h in zip(g.colors, pile_heights):
            g.piles[c] = h

    def on_turn(self, j):
        g = self.game
        g.global_turn += 1
        if j != g.moi:
            return None
        if g.mode <= 3:
            return self._cycle_action()
        return self._smart_action()

    # ---- Requêtes d'affichage -------------------------------------------

    def show_hands(self):
        g = self.game
        lines = []
        for j in range(1, g.n + 1):
            if j == g.moi:
                continue
            cards = " ".join(str(g.players[j].cards[p]) for p in g.players[j].positions())
            lines.append(f"{j} m {cards}")
        return lines

    def show_knowledge(self):
        g = self.game
        lines = []
        for j in range(1, g.n + 1):
            know = " ".join(str(g.players[j].knowledge[p]) for p in g.players[j].positions())
            lines.append(f"{j} r {know}")
        return lines

    # ---- Stratégies de décision -----------------------------------------

    def _cycle_action(self):
        """Modes 1-3 : action déterminée par le compteur de tours."""
        g = self.game
        g.current_turn += 1
        phase = g.current_turn % 3
        if phase == 1:
            return f"I {g.next_player()} A"
        if phase == 2:
            return "d 1"
        return "e 1"

    def _smart_action(self):
        """Modes 4-7 : règles 1/2/3 et leurs variantes bis."""
        return (self._rule_special_play()    # règle 1 bis (mode 7)
                or self._rule_play()          # règle 1
                or self._rule_hint()          # règles 2 / 2 bis
                or self._rule_discard())      # règles 3 / 3 bis

    def _rule_special_play(self):
        """Règle 1 bis : empiler une carte ayant reçu une indication spéciale."""
        g = self.game
        if g.mode < 7 or g.lives <= 0:
            return None
        me = g.me()
        for p in me.positions():
            if me.knowledge[p].special:
                return f"e {p}"
        return None

    def _rule_play(self):
        """Règle 1 : empiler une carte à information complète et empilable."""
        g = self.game
        me = g.me()
        for p in me.positions():
            kn = me.knowledge[p]
            if kn.complete and g.is_playable(kn.value, kn.color):
                return f"e {p}"
        return None

    def _rule_hint(self):
        """Règles 2 / 2 bis : indiquer une carte empilable d'un autre joueur."""
        g = self.game
        if g.tokens <= 0:
            return None
        if g.mode >= 7:
            special = self._special_hint()
            if special:
                return special
        for j in range(1, g.n + 1):
            if j == g.moi:
                continue
            player = g.players[j]
            for p in player.positions():
                card = player.cards[p]
                if not card.visible or not g.is_playable(card.value, card.color):
                    continue
                if player.knowledge[p].complete:
                    continue
                if player.knowledge[p].value is None:
                    return f"i {j} {card.value}"
                return f"I {j} {card.color}"
        return None

    def _special_hint(self):
        """Règle 2 bis : envoyer une indication spéciale (mode 7)."""
        g = self.game
        for j in range(1, g.n + 1):
            if j == g.moi:
                continue
            player = g.players[j]
            for p in player.positions():
                card = player.cards[p]
                if not card.visible or not g.is_playable(card.value, card.color):
                    continue
                kn = player.knowledge[p]
                if kn.complete or kn.special:
                    continue
                val_count = sum(1 for q in player.positions()
                                if player.cards[q].value == card.value)
                col_count = sum(1 for q in player.positions()
                                if player.cards[q].color == card.color)
                if val_count == 1:
                    return f"i {j} {card.value}"
                if col_count == 1:
                    return f"I {j} {card.color}"
        return None

    def _rule_discard(self):
        """Règles 3 / 3 bis : défausser (position 1, ou carte la plus ancienne)."""
        g = self.game
        if g.mode < 6:
            return "d 1"
        me = g.me()
        best_p = 1
        best_date = me.knowledge[1].date
        for p in me.positions():
            d = me.knowledge[p].date
            if d < best_date or (d == best_date and p < best_p):
                best_p, best_date = p, d
        return f"d {best_p}"


class Protocol:
    """Lit les messages stdin, met à jour l'agent, émet les actions."""

    def __init__(self, agent):
        self.agent = agent

    @staticmethod
    def _emit(text):
        print(text, flush=True)

    def run(self, stream):
        agent = self.agent
        for raw in stream:
            line = raw.strip()
            if not line:
                continue
            parts = line.split()
            tag = parts[0]

            if tag == 'p':
                k, n, moi, mode = map(int, parts[1:5])
                agent.start_game(k, n, moi, mode)

            elif tag == 'n':
                j, p = int(parts[1]), int(parts[2])
                v = None if parts[3] == '?' else int(parts[3])
                c = None if parts[4] == '?' else parts[4]
                agent.on_new_card(j, p, v, c)

            elif tag == 'i':
                j, v = int(parts[1]), int(parts[2])
                bits = [int(x) for x in parts[3:]]
                agent.on_value_hint(j, v, bits)

            elif tag == 'I':
                j, c = int(parts[1]), parts[2]
                bits = [int(x) for x in parts[3:]]
                agent.on_color_hint(j, c, bits)

            elif tag == 'j':
                lives, tokens = int(parts[1]), int(parts[2])
                heights = [int(x) for x in parts[3:]]
                agent.on_state(lives, tokens, heights)

            elif tag == 't':
                action = agent.on_turn(int(parts[1]))
                if action is not None:
                    self._emit(action)

            elif tag == 'm':
                for line_out in agent.show_hands():
                    self._emit(line_out)

            elif tag == 'r':
                for line_out in agent.show_knowledge():
                    self._emit(line_out)

            elif tag == 'f':
                if int(parts[1]) == 0:
                    return


def main():
    Protocol(Agent()).run(sys.stdin)


if __name__ == "__main__":
    main()
