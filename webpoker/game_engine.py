# game_engine.py
import os
import random
from collections import defaultdict, Counter
from itertools import combinations

# --- Constants ---
SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
RANK_VALUES = {r: i for i, r in enumerate(RANKS, start=2)}

# Thresholds for evaluating hand strength
STRONG_HAND_THRESHOLD = 6
MEDIUM_HAND_THRESHOLD = 3

# Chip values (for potential future use in chip visualization)
CHIP_VALUES = {"black": 5, "blue": 10, "green": 20, "red": 50, "white": 100}

# --- Core Classes and Functions ---

class Card:
    def __init__(self, rank, suit, image_path=None):
        self.rank = rank
        self.suit = suit
        # image_path can be used by the frontend; default naming convention assumed
        self.image_path = image_path or f"{rank}_of_{suit}.png"

    def __str__(self):
        return f"{self.rank} of {self.suit}"

class Deck:
    def __init__(self, card_folder="static/cards"):
        self.cards = []
        for suit in SUITS:
            for rank in RANKS:
                # Assume images are stored under static/cards/
                path = os.path.join(card_folder, f"{rank}_of_{suit}.png")
                self.cards.append(Card(rank, suit, path))
        random.shuffle(self.cards)

    def deal(self):
        if self.cards:
            return self.cards.pop()
        return None

def check_straight(vals):
    # Allow Ace to be low in A-2-3-4-5
    if 14 in vals:
        temp = vals + [1]
    else:
        temp = vals
    temp = sorted(temp, reverse=True)
    run_length = 1
    best_run_high = None
    run_start_index = 0
    for i in range(len(temp) - 1):
        if temp[i] - 1 == temp[i + 1]:
            run_length += 1
            if run_length >= 5:
                top_of_run = temp[run_start_index]
                best_run_high = top_of_run if (best_run_high is None or top_of_run > best_run_high) else best_run_high
        else:
            run_length = 1
            run_start_index = i + 1
    if best_run_high:
        return True, best_run_high
    return False, None

def rank_hand(cards):
    values = sorted([RANK_VALUES[c.rank] for c in cards], reverse=True)
    suits = [c.suit for c in cards]
    vcount = Counter(values)
    scount = Counter(suits)
    is_flush = any(count >= 5 for count in scount.values())
    unique_vals = sorted(set(values), reverse=True)
    is_straight, straight_high = check_straight(unique_vals)
    freqs = sorted(vcount.values(), reverse=True)

    # Four of a Kind
    if 4 in freqs:
        quad_val = max(k for k, cnt in vcount.items() if cnt == 4)
        kicker = max(v for v in values if v != quad_val)
        return (8, quad_val, kicker)

    # Full House
    triple_candidates = [k for k, cnt in vcount.items() if cnt >= 3]
    if triple_candidates:
        best_three = max(triple_candidates)
        pair_candidates = [k for k, cnt in vcount.items() if cnt >= 2 and k != best_three]
        if pair_candidates:
            best_pair = max(pair_candidates)
            return (7, best_three, best_pair)

    # Flush
    if is_flush:
        flush_cards = flush_top_values(cards)
        return (6,) + tuple(flush_cards)

    # Straight
    if is_straight:
        return (5, straight_high)

    # Three of a Kind
    if 3 in freqs:
        three_val = max(k for k, cnt in vcount.items() if cnt == 3)
        kickers = sorted((v for v in values if v != three_val), reverse=True)[:2]
        return (4, three_val) + tuple(kickers)

    # Two Pair
    if freqs.count(2) >= 2:
        pairs = [k for k, cnt in vcount.items() if cnt == 2]
        pairs = sorted(pairs, reverse=True)
        top_two = pairs[:2]
        kicker = max(v for v in values if v not in top_two)
        return (3, top_two[0], top_two[1], kicker)

    # One Pair
    if 2 in freqs:
        pair_val = max(k for k, cnt in vcount.items() if cnt == 2)
        kickers = sorted((v for v in values if v != pair_val), reverse=True)[:3]
        return (2, pair_val) + tuple(kickers)

    # High Card
    top_five = values[:5]
    return (1,) + tuple(top_five)

def flush_top_values(cards):
    suit_cards = defaultdict(list)
    for c in cards:
        suit_cards[c.suit].append(RANK_VALUES[c.rank])
    for s, vals in suit_cards.items():
        if len(vals) >= 5:
            return sorted(vals, reverse=True)[:5]
    return []

def best_five_from_seven(cards):
    best = None
    for combo in combinations(cards, 5):
        val = rank_hand(list(combo))
        if best is None or val > best:
            best = val
    return best

def hand_description(val):
    rank_type = val[0]
    if rank_type == 9:
        high_card = val[1]
        if high_card == 14:
            return "Royal Flush"
        return "Straight Flush"
    elif rank_type == 8:
        return "Four of a Kind"
    elif rank_type == 7:
        return "Full House"
    elif rank_type == 6:
        return "Flush"
    elif rank_type == 5:
        return "Straight"
    elif rank_type == 4:
        return "Three of a Kind"
    elif rank_type == 3:
        return "Two Pair"
    elif rank_type == 2:
        return "One Pair"
    else:
        return "High Card"

class Player:
    def __init__(self, name, chips=1000, is_human=False, play_style="straightforward"):
        self.name = name
        self.chips = chips
        self.cards = []
        self.is_human = is_human
        self.folded = False
        self.current_bet = 0
        self.last_action = ""
        self.play_style = play_style
        self.placed_chips = []  # Not used in headless mode, but available for future expansion

    def reset_hand(self):
        self.cards = []
        self.folded = False
        self.current_bet = 0
        self.last_action = ""
        self.placed_chips = []

    def bet(self, amount):
        actual = min(amount, self.chips)
        self.chips -= actual
        self.current_bet += actual
        return actual

    def fold(self):
        self.folded = True
        self.last_action = "Fold"

    def to_dict(self):
        return {
            "name": self.name,
            "chips": self.chips,
            "cards": [str(c) for c in self.cards],
            "folded": self.folded,
            "current_bet": self.current_bet,
            "last_action": self.last_action,
            "play_style": self.play_style
        }

# --- Texas Hold'em Game Engine (Headless) ---

class TexasHoldemGame:
    def __init__(self):
        self.deck = None
        self.players = []
        self.dealer_index = 0
        self.small_blind = 50
        self.big_blind = 100
        self.current_bet = 0
        self.community_cards = []
        self.pot = 0
        self.stage = "preflop"  # stages: preflop, flop, turn, river, showdown
        self.message = ""
        self.initialize_players()

    def initialize_players(self):
        # Define a few players; one human and several opponents.
        self.players = [
            Player("You", chips=5000, is_human=True, play_style="strategic"),
            Player("Bob", chips=5000, play_style="risk_taker"),
            Player("Alice", chips=5000, play_style="risk_taker"),
            Player("Charlie", chips=5000, play_style="strategic")
        ]

    def start_hand(self):
        self.deck = Deck()  # reinitialize deck
        for p in self.players:
            p.reset_hand()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.stage = "preflop"
        self.message = "New hand started. Stage: Preflop."
        # Deal two hole cards to each player
        for _ in range(2):
            for p in self.players:
                card = self.deck.deal()
                if card:
                    p.cards.append(card)
        # Post blinds
        self.post_blinds()
        # Set current player (for headless, we start with the player after dealer)
        self.current_player_index = (self.dealer_index + 1) % len(self.players)

    def post_blinds(self):
        # Assume the player immediately after dealer posts small blind, next posts big blind.
        sb_index = (self.dealer_index + 1) % len(self.players)
        bb_index = (self.dealer_index + 2) % len(self.players)
        sb_amount = self.players[sb_index].bet(self.small_blind)
        bb_amount = self.players[bb_index].bet(self.big_blind)
        self.current_bet = self.big_blind
        self.pot += (sb_amount + bb_amount)
        self.message = f"{self.players[sb_index].name} posts SB {sb_amount}, {self.players[bb_index].name} posts BB {bb_amount}."

    def process_player_action(self, action, amount=0):
        """
        Process an action from the current player.
        Supported actions: "call", "fold", "bet", "all-in".
        """
        current_player = self.players[self.current_player_index]
        if current_player.folded:
            self.message = f"{current_player.name} has already folded."
        else:
            if action == "call":
                required = self.current_bet - current_player.current_bet
                bet_amount = current_player.bet(required)
                self.pot += bet_amount
                current_player.last_action = "Call"
                self.message = f"{current_player.name} calls {bet_amount}."
            elif action == "fold":
                current_player.fold()
                self.message = f"{current_player.name} folds."
            elif action == "bet":
                # Include call plus raise; amount is the extra raise above a call.
                required = self.current_bet - current_player.current_bet
                total_bet = required + amount
                bet_amount = current_player.bet(total_bet)
                self.pot += bet_amount
                if amount > 0:
                    self.current_bet = current_player.current_bet
                    current_player.last_action = f"Bet/Raise {amount}"
                    self.message = f"{current_player.name} bets/raises by {amount}."
                else:
                    current_player.last_action = "Call"
                    self.message = f"{current_player.name} calls {bet_amount}."
            elif action == "all-in":
                all_in_amount = current_player.chips
                bet_amount = current_player.bet(all_in_amount)
                self.pot += bet_amount
                current_player.last_action = f"All-In {bet_amount}"
                self.message = f"{current_player.name} goes all-in with {bet_amount}."
            else:
                self.message = "Unknown action."
        # Advance turn after action.
        self.advance_turn()
        return {"action": action, "amount": amount, "message": self.message}

    def advance_turn(self):
        # Simple turn rotation: move to next player who hasn't folded.
        for i in range(1, len(self.players) + 1):
            next_index = (self.current_player_index + i) % len(self.players)
            if not self.players[next_index].folded:
                self.current_player_index = next_index
                return
        # If all have folded, do nothing.

    def deal_community_cards(self, count):
        for _ in range(count):
            card = self.deck.deal()
            if card:
                self.community_cards.append(card)

    def next_stage(self):
        # Advance through the game stages: preflop -> flop -> turn -> river -> showdown.
        if self.stage == "preflop":
            self.deal_community_cards(3)  # Flop
            self.stage = "flop"
        elif self.stage == "flop":
            self.deal_community_cards(1)  # Turn
            self.stage = "turn"
        elif self.stage == "turn":
            self.deal_community_cards(1)  # River
            self.stage = "river"
        elif self.stage == "river":
            self.stage = "showdown"
            self.evaluate_showdown()
        self.message = f"Stage advanced to {self.stage}."

    def evaluate_showdown(self):
        # Evaluate active players' hands and determine the winner.
        active_players = [p for p in self.players if not p.folded]
        if not active_players:
            self.message = "No active players remain."
            return
        best_value = None
        winners = []
        for p in active_players:
            best_hand = best_five_from_seven(p.cards + self.community_cards)
            p.best_hand = best_hand
            if best_value is None or best_hand > best_value:
                best_value = best_hand
                winners = [p]
            elif best_hand == best_value:
                winners.append(p)
        hand_desc = hand_description(best_value) if best_value else "No hand"
        if len(winners) == 1:
            winners[0].chips += self.pot
            self.message = f"{winners[0].name} wins {self.pot} chips with a {hand_desc}!"
        else:
            split = self.pot // len(winners)
            for w in winners:
                w.chips += split
            names = ", ".join([w.name for w in winners])
            self.message = f"Split pot! {names} each win {split} chips with a {hand_desc}!"

    def get_state(self):
        """
        Return a dictionary representation of the current game state.
        This is used by the web API to update the UI.
        """
        return {
            "pot": self.pot,
            "stage": self.stage,
            "message": self.message,
            "current_bet": self.current_bet,
            "community_cards": [str(card) for card in self.community_cards],
            "players": [p.to_dict() for p in self.players],
            "current_player": self.players[self.current_player_index].name if self.players else None
        }

# --- For Testing Purposes ---
if __name__ == "__main__":
    game = TexasHoldemGame()
    game.start_hand()
    print("Initial state:", game.get_state())
    print("After call action:", game.process_player_action("call"))
    print("State:", game.get_state())
    game.next_stage()
    print("After advancing stage:", game.get_state())