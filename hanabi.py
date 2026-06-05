#!/usr/bin/env python3
"""Hanabi JFP 16"""
import sys

# Identity of the Card. If we dont know the value or color, we set it to None. 
# The visible property (means we know the card) is true if both are not None
class Card:
    def __init__(self, value=None, color=None):
        self.value = value  # int or None
        self.color = color  # str ('A'..'Z') or None

    # Means we know the card value and color 
    @property
    def visible(self):
        return self.value is not None and self.color is not None

    def __str__(self):
        v = self.value if self.value is not None else '?'
        c = self.color if self.color is not None else '?'
        return f"{v}{c}"

# Property of A card that we know (or don't know)
# We can have positive knowledge (value/color known) 
# and negative knowledge (value/color known NOT to be) 
# The special property is for mode 7, and the date is for mode 6.
class Knowledge:
    def __init__(self, date=0):
        self.value = None  # The card known value or None
        self.color = None  # Known color or None
        self.neg_values = set()  # Values that we know the card is NOT
        self.neg_colors = set()  # Colors that we know the card is NOT
        self.special = False  # Mode 7 sepcial hint
        self.date = date  # Date of the last info received about this card (mode 6) 

    # Basically the same as visible, but for knowledge
    # We have complete knowledge about the card if we know its value and color
    @property
    def complete(self):
        return self.value is not None and self.color is not None

    # Mode 5: if we have k-1 negative hints about a card, we can deduce the last one
    def deduce(self, all_values, all_colors):
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


# Each player has a hand of k cards, and a knowledge about each card.
class Player:
    def __init__(self, k):
        self.k = k
        self.cards = {p: Card() for p in range(1, k + 1)}
        self.knowledge = {p: Knowledge() for p in range(1, k + 1)}

    def positions(self):
        return range(1, self.k + 1)

    def receive_card(self, p, value, color, date):
        self.cards[p] = Card(value, color)
        self.knowledge[p] = Knowledge(date)


# Global state of the game
class GameState:
    def __init__(self, k, n, moi, mode):
        self.k = k  # num of cards by player
        self.n = n  # num of players
        self.moi = moi  # our player number (1..n)
        self.mode = mode  # game mode (1..7)
        self.lives = 3
        self.tokens = 8
        self.piles = {c: 0 for c in self._all_colors(k)}  # top card of each pile of color c 
        self.players = {j: Player(k) for j in range(1, n + 1)} 
        self.current_turn = 0   # inscreased at each of our turn
        self.global_turn = 0    # increased at each message 't'
                                
        # a list of hashmap (for each player) of type {card value, color} to 
        # keep track how many cards of such combination we've seen 
        # (in played piles, discard pile and hands of OTHER players)
        # we init for each player, the seen cards of each combinasion to 0
        self.seen_cards = {
            p: {(v, chr(ord('A') + c - 1)): 0 for v in range(1, k + 1) for c in range(1, k + 1)}
            for p in range(n)
        }


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

    # top of pile of color c is v-1, so we can play value v on it
    def is_playable(self, value, color):
        return self.piles.get(color, 0) == value - 1

    def next_player(self):
        return 1 + (self.moi % self.n)

# Contains methods to execute the commands 
# received from the game and update the global state
class AI:
    def __init__(self):
        self.game = None

    # Init the game
    def start_game(self, k, n, moi, mode):
        self.game = GameState(k, n, moi, mode)

    # Command n j p v c
    def on_new_card(self, j, p, value, color):
        g = self.game
        g.players[j].receive_card(p, value, color, g.global_turn)
        # Mode 8
        # for all the players (execpt j) we update seen_cards (if its v,c is not None)
        if g.mode >= 8 and value is not None and color is not None:
            for q in range(1, g.n + 1):
                if q != j:
                    g.seen_cards[q][(value, color)] += 1


    # Command i j v b1 b2 ... bk 
    def on_value_hint(self, j, value, bits):
        g = self.game
        special = (sum(bits) == 1)  # theres only one bit 1 -> special hint
                                    # as other player hint to play this card
        player = g.players[j]
        for p in player.positions():
            # We update the knowledge of player j about his card p
            # according to hint bits
            kn = player.knowledge[p] 
            if bits[p - 1] == 1:
                if kn.value is None:
                    kn.value = value
                if g.mode >= 7 and special:
                    kn.special = True
            else:
                # If the bit is 0, we know the card is NOT of the hinted value, 
                # so we add it to neg_values
                kn.neg_values.add(value)
            
            # Deduce if receive enough negative hints (mode 5)
            if g.mode >= 5:
                kn.deduce(g.value_set, g.color_set)

    # Command I j c b1 b2 ... bk
    # Basically the same as on_value_hint
    def on_color_hint(self, j, color, bits):
        g = self.game
        special = (sum(bits) == 1)
        player = g.players[j]
        # We update the knowledge of player j about his card p
        # according to hint bits
        for p in player.positions():    # at each index p of the hand
            kn = player.knowledge[p]
            if bits[p - 1] == 1:
                if kn.color is None:
                    kn.color = color
                if g.mode >= 7 and special:
                    kn.special = True
            else:
                kn.neg_colors.add(color)

            # Deduce if receive enough negative hints (mode 5)
            if g.mode >= 5:
                kn.deduce(g.value_set, g.color_set)

    # j vies jetons hA hB ... hw
    # we just update the global state
    def on_state(self, lives, tokens, pile_heights):
        g = self.game
        g.lives = lives
        g.tokens = tokens
        for c, h in zip(g.colors, pile_heights):
            g.piles[c] = h

    # Command t j
    # its turn player j
    def on_turn(self, j):
        g = self.game
        g.global_turn += 1
        if j != g.moi:
            return None
        if g.mode <= 3:  # for simple mode
            return self.cycle_action()

        # for deduction mode
        return self.smart_action()

    # Requests to display infos
    # For mode 2, we show the hands of the other players
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

    # Strategy
    # Mode 1-3 : action cycles are fixed
    def cycle_action(self):
        g = self.game
        g.current_turn += 1 # temps
        phase = g.current_turn % 3
        if phase == 1:
            return f"I {g.next_player()} A"
        if phase == 2:
            return "d 1"
        return "e 1"

    # For mode 4 to 7
    def smart_action(self):
        return (self.rule_special_play()  # rule 1bis (mode 7)
                or self.rule_play()  # rule 1 (mode 4)
                or self.rule_hint()  # rule 2 (mode 4)/ 2bis (mode 7)
                or self.rule_discard())  # rule 3 (mode 4) / 3bis (mode 6)


    def rule_special_play(self):
        g = self.game
        # We must in mode >= 7 and theres still life to gamble
        if g.mode < 7 or g.lives <= 0:
            return None
        me = g.me()
        # Play the smallest position having the hint
        for p in me.positions():
            if me.knowledge[p].special:
                return f"e {p}"
        return None

    # For each card, if the player has full info on that card
    # and we can stack it on the pile (top of pile is v-1 for color c)
    # then we play command e p
    def rule_play(self):
        g = self.game
        me = g.me()
        for p in me.positions():
            kn = me.knowledge[p]
            if kn.complete and g.is_playable(kn.value, kn.color):
                return f"e {p}"
        return None

    # For each card of each other player.
    # if the card is visible and stackable
    # and the other player doesnt have knowledge about it
    # we give a hint about its value or color
    def rule_hint(self):
        g = self.game
        if g.tokens <= 0:  # no token left
            return None
        if g.mode >= 7:  # if we do a hint and its mode 7
            special = self.special_hint()  # rule 2bis
            if special:
                return special

        # for all the player (prefer the one with lowest id first if multiple)
        for j in range(1, g.n + 1):
            if j == g.moi:  # skip ourself
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

    # Rule 2bis (mode 7)
    # If theres only one unique color or value among the playable cards of other players, 
    # we can give a special hint about it (hint of rule 1 bis)
    def special_hint(self):
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
                # If the player already has complete knowledge or already got a special hint about it
                # skip
                if kn.complete or kn.special:
                    continue

                # Rule 2ter mode 8: if the card is critical, 
                # we give a special hint about it to make the other player play it immediately
                if g.mode >= 8 and self.is_crtical_hint(card.value, card.color):
                    kn.special = True
                    if kn.value is None:
                        return f"i {j} {card.value}"
                    return f"I {j} {card.color}"

                val_count = sum(1 for q in player.positions()
                                if player.cards[q].value == card.value)
                col_count = sum(1 for q in player.positions()
                                if player.cards[q].color == card.color)
                if val_count == 1:  # if only one card has this value, give hint
                    return f"i {j} {card.value}"
                if col_count == 1:  # if only one card has this color, give hint
                    return f"I {j} {card.color}"
        return None

    # If theres no playable move indicated by rule1 and 2. We discard
    def rule_discard(self):
        g = self.game
        if g.mode < 6:  # if mode 4 and 5 we discard the first card
            return self.discard_card(1)
        
        # mode 6 and 7, we discard the card with the lowest date (turn counter)
        me = g.me()
        best_p = -1
        best_date = int(1e9)
        for p in me.positions():
            d = me.knowledge[p].date
            if d < best_date or (d == best_date and p < best_p):
                if g.mode >= 8 and me.knowledge[p].complete and self.is_critical(me.cards[p].value, me.cards[p].color):
                    continue  # skip critical cards in mode 8 (rule 4)
                best_p, best_date = p, d

        if (g.mode >= 8 and best_p == -1):
            # if all cards are critical, we have to discard one of them, 
            # so we take the one with the lowest date
            for p in me.positions():
                d = me.knowledge[p].date
                if d < best_date or (d == best_date and p < best_p):
                    best_p, best_date = p, d

        return self.discard_card(best_p)

    # Wrapper method to accomodate mode 8
    def discard_card(self, p):
        # Mode 8:
        # we increase seen_cards for all the players of the value (v,c) of the discarded card
        if self.game.mode >= 8:
            me = self.game.me()
            card = me.cards[p]
            for player in range(1, self.game.n + 1):
                self.game.seen_cards[player][(card.value, card.color)] += 1

        return f"d {p}"

    # This is called before attempting to discard a card with (v,c)
    # A critical card that it is the last one of its kind (v,c)
    # that is we've seen total-1 of them from other players and piles
    # The total number of cards of any combination (v,c) is
    # 3 if v=1, 1 if v=k and 2 otherwise
    def is_critical(self, value, color):
        g = self.game
        total = 3 if value == 1 else (1 if value == g.k else 2)
        seen = g.seen_cards[g.moi][(value, color)]
        return seen >= total - 1

    # This is called before attempting to give a hint about a card with (v,c)
    # If the other player doesnt have knowledge about a card and
    # such card is CRITICAL (as we've seen a TOTAL nb of them from other players and from discard pile)
    # and also playable,
    # we give a special hint about it to make them instantly play it
    def is_crtical_hint(self, value, color):
        g = self.game
        total = 3 if value == 1 else (1 if value == g.k else 2)
        seen = g.seen_cards[g.moi][(value, color)]
        return seen >= total

class Hanabi:
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
            
            # Mode 2
            elif tag == 'm':
                for line_out in agent.show_hands():
                    self._emit(line_out)

            # Mode 3
            elif tag == 'r':
                for line_out in agent.show_knowledge():
                    self._emit(line_out)

            # End game
            elif tag == 'f':
                if int(parts[1]) == 0:
                    return


def main():
    Hanabi(AI()).run(sys.stdin)


if __name__ == "__main__":
    main()

