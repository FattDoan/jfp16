#!/usr/bin/env python3
import sys

# Hanabi game

# A card has a color (from A to Z) and a value (an integer)
class Card:
    # How to explicitely represent type?
    def __init__(self, color, value):
        self.color = color
        self.value = value

    def get_color(self):
        return self.color

    def get_value(self):
        return self.value


# We eed to have a list of cards:
# as
# draw pile, discard pile, piles of played card (for each color), and each plaers' hand

def main():
    k = n = moi = mode = 0
    hands = {}        # hands[j][p] = (value_int, color_str) or ('?','?')
    known_val = {}    # known_val[j][p] = int or None
    known_col = {}    # known_col[j][p] = str or None
    neg_val = {}      # neg_val[j][p] = set of int values known NOT to be there
    neg_col = {}      # neg_col[j][p] = set of str colors known NOT to be there
    special_hinted = {}  # special_hinted[j][p] = bool (mode 7)
    card_date = {}    # card_date[j][p] = global_turn when card arrived (mode 6)
    piles = {}        # piles[c] = int height
    lives = tokens = 0
    current_turn = 0  # temps: increments only when it's our turn (modes 1-3)
    global_turn = 0   # increments on every 't' message

    def colors():
        return [chr(ord('A') + i) for i in range(k)]

    def init_game():
        nonlocal k, n, moi, mode, lives, tokens, current_turn, global_turn
        hands.clear()
        known_val.clear()
        known_col.clear()
        neg_val.clear()
        neg_col.clear()
        special_hinted.clear()
        card_date.clear()
        piles.clear()
        current_turn = 0
        global_turn = 0
        lives = 3
        tokens = 8

    def init_player(j):
        hands[j] = {}
        known_val[j] = {}
        known_col[j] = {}
        neg_val[j] = {}
        neg_col[j] = {}
        special_hinted[j] = {}
        card_date[j] = {}
        for p in range(1, k + 1):
            hands[j][p] = ('?', '?')
            known_val[j][p] = None
            known_col[j][p] = None
            neg_val[j][p] = set()
            neg_col[j][p] = set()
            special_hinted[j][p] = False
            card_date[j][p] = 0

    def apply_deductions(j, p):
        if mode < 5:
            return
        if known_val[j][p] is None:
            remaining = set(range(1, k + 1)) - neg_val[j][p]
            if len(remaining) == 1:
                known_val[j][p] = next(iter(remaining))
        if known_col[j][p] is None:
            remaining = set(colors()) - neg_col[j][p]
            if len(remaining) == 1:
                known_col[j][p] = next(iter(remaining))

    def is_playable(v, c):
        return piles.get(c, 0) == v - 1

    def complete_info(j, p):
        return known_val[j][p] is not None and known_col[j][p] is not None

    def action_cycle():
        nonlocal current_turn
        current_turn += 1
        j_next = 1 + (moi % n)
        t = current_turn % 3
        if t == 1:
            return f"I {j_next} A"
        elif t == 2:
            return f"d 1"
        else:
            return f"e 1"

    def action_smart():
        # Mode 7 Rule 1 bis: special-hinted positions
        if mode >= 7 and lives > 0:
            for p in range(1, k + 1):
                if special_hinted[moi][p]:
                    return f"e {p}"

        # Rule 1: complete info + playable
        for p in range(1, k + 1):
            if complete_info(moi, p):
                v = known_val[moi][p]
                c = known_col[moi][p]
                if is_playable(v, c):
                    return f"e {p}"

        # Rule 2 / 2 bis
        if tokens > 0:
            if mode >= 7:
                # Rule 2 bis: find playable card of another player where special hint is possible
                for j in range(1, n + 1):
                    if j == moi:
                        continue
                    for p in range(1, k + 1):
                        v, c = hands[j][p]
                        if v == '?':
                            continue
                        v = int(v)
                        if not is_playable(v, c):
                            continue
                        if complete_info(j, p):
                            continue
                        if special_hinted[j][p]:
                            continue
                        # Check if value hint or color hint would be special
                        val_count = sum(1 for pp in range(1, k + 1)
                                        if hands[j][pp][0] != '?' and int(hands[j][pp][0]) == v)
                        col_count = sum(1 for pp in range(1, k + 1)
                                        if hands[j][pp][1] != '?' and hands[j][pp][1] == c)
                        if val_count == 1:
                            return f"i {j} {v}"
                        if col_count == 1:
                            return f"I {j} {c}"

            # Rule 2: give hint to another player's playable card without complete info
            for j in range(1, n + 1):
                if j == moi:
                    continue
                for p in range(1, k + 1):
                    v, c = hands[j][p]
                    if v == '?':
                        continue
                    v = int(v)
                    if not is_playable(v, c):
                        continue
                    if complete_info(j, p):
                        continue
                    if known_val[j][p] is None:
                        return f"i {j} {v}"
                    else:
                        return f"I {j} {c}"

        # Rule 3 / 3 bis: discard
        if mode >= 6:
            best_p = 1
            best_date = card_date[moi][1]
            for p in range(2, k + 1):
                d = card_date[moi][p]
                if d < best_date or (d == best_date and p < best_p):
                    best_p = p
                    best_date = d
            return f"d {best_p}"
        else:
            return "d 1"

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        msg = parts[0]

        if msg == 'p':
            k, n, moi, mode = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
            init_game()
            for c in colors():
                piles[c] = 0
            for j in range(1, n + 1):
                init_player(j)

        elif msg == 'n':
            j, p = int(parts[1]), int(parts[2])
            v_str, c_str = parts[3], parts[4]
            if v_str == '?':
                hands[j][p] = ('?', '?')
            else:
                hands[j][p] = (int(v_str), c_str)
            known_val[j][p] = None
            known_col[j][p] = None
            neg_val[j][p] = set()
            neg_col[j][p] = set()
            special_hinted[j][p] = False
            card_date[j][p] = global_turn

        elif msg == 'i':
            j, v = int(parts[1]), int(parts[2])
            bits = [int(parts[3 + i]) for i in range(k)]
            is_special = (sum(bits) == 1)
            for p in range(1, k + 1):
                if bits[p - 1] == 1:
                    if known_val[j][p] is None:
                        known_val[j][p] = v
                    if mode >= 7 and is_special:
                        special_hinted[j][p] = True
                else:
                    neg_val[j][p].add(v)
                apply_deductions(j, p)

        elif msg == 'I':
            j, c = int(parts[1]), parts[2]
            bits = [int(parts[3 + i]) for i in range(k)]
            is_special = (sum(bits) == 1)
            for p in range(1, k + 1):
                if bits[p - 1] == 1:
                    if known_col[j][p] is None:
                        known_col[j][p] = c
                    if mode >= 7 and is_special:
                        special_hinted[j][p] = True
                else:
                    neg_col[j][p].add(c)
                apply_deductions(j, p)

        elif msg == 'j':
            lives = int(parts[1])
            tokens = int(parts[2])
            for idx, c in enumerate(colors()):
                piles[c] = int(parts[3 + idx])

        elif msg == 't':
            j = int(parts[1])
            global_turn += 1
            if j != moi:
                continue
            if mode <= 3:
                print(action_cycle(), flush=True)
            else:
                print(action_smart(), flush=True)

        elif msg == 'm':
            for j in range(1, n + 1):
                if j == moi:
                    continue
                cards = " ".join(
                    f"{v}{c}" if v != '?' else "??"
                    for p in range(1, k + 1)
                    for v, c in [hands[j][p]]
                )
                print(f"{j} m {cards}", flush=True)

        elif msg == 'r':
            for j in range(1, n + 1):
                parts_r = " ".join(
                    f"{known_val[j][p] if known_val[j][p] is not None else '?'}"
                    f"{known_col[j][p] if known_col[j][p] is not None else '?'}"
                    for p in range(1, k + 1)
                )
                print(f"{j} r {parts_r}", flush=True)

        elif msg == 'f':
            if int(parts[1]) == 0:
                sys.exit(0)


main()
