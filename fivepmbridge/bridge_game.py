from enum import Enum
import random
from collections import defaultdict

class Suit(Enum):
    CLUBS = "C"
    DIAMONDS = "D"
    HEARTS = "H"
    SPADES = "S"
    NO_TRUMP = "N"

class Card():
    def __init__(self, value, suit: Suit) -> None:
        assert value in range(1, 14)
        self.value = value
        self.suit = suit
    def is_better(self, other_card, lead_suit:Suit, trump:Suit):
        # If only this card is trump
        if self.suit == trump and not other_card.suit == trump:
            return True
        # if only other card is trump
        if other_card.suit == trump and not self.suit == trump:
            return False

        # If only this card is trump
        if self.suit == lead_suit and not other_card.suit == lead_suit:
            return True
        # if only other card is trump
        if other_card.suit == lead_suit and not self.suit == lead_suit:
            return False

        return self.value > other_card.value
    def to_code(self):
        return f"{self.suit.value}{self.value}"

    @classmethod
    def from_code(cls, code):
        suit_code = code[0]
        if suit_code == 'C':
            suit = Suit.CLUBS
        elif suit_code == 'D':
            suit = Suit.DIAMONDS
        elif suit_code == 'H':
            suit = Suit.HEARTS
        elif suit_code == 'S':
            suit = Suit.SPADES
        value = int(code[1:])
        return Card(value, suit)

    def __eq__(self, other):
        if isinstance(other, str):
            suit_code = other[0]
            if suit_code == 'C':
                suit = Suit.CLUBS
            elif suit_code == 'D':
                suit = Suit.DIAMONDS
            elif suit_code == 'H':
                suit = Suit.HEARTS
            elif suit_code == 'S':
                suit = Suit.SPADES
            value = int(other[1:])
            return suit == self.suit and value == self.value
        else:
            return self.suit == other.suit and self.value == other.value

class Trick():
    def __init__(self, trump:Suit) -> None:
        self.trump = trump
        self.cards = {}
        self.lead_suit = None
    def play_card(self, card, player):
        if self.cards == []:
            self.lead_suit = card.suit()
        self.cards[player] = card
    def score_trick(self):
        best_card = None
        best_player = None
        for player, card in self.cards.items():
            if not best_card:
                best_card = card
                best_player = player
                continue

            if card.is_better(best_card, self.lead_suit, self.tump):
                best_card = card
                best_player = player

        return best_player

class Hand():
    def __init__(self) -> None:
        pass
    def deal_hands(self):
        pass
    def start_auction(self):
        pass


class Player():
    def __init__(self) -> None:
        self.hand = []
        self.score = 0
    def deal_hand(self, cards):
        assert self.hand == []
        self.hand = cards
    def deal_card(self, card):
        self.cards.append(card)
    def play_card(self, card):
        return self.cards.pop(card)


class Partnership():
    def __init__(self, player1: Player, player2: Player) -> None:
        self.player1 = player1
        self.player2 = player2
        self.score = 0
        self.current_below_score = 0
        self.games = 0

    @property
    def vulnerable(self):
        return bool(self.games)

    def award(self, above, below):
        self.player1.score += above + below
        self.player2.score += above + below
        self.score += above + below
        self.current_below_score += below

class Bid():
    def __init__(self, value=0, suit=0, is_pass=False, is_dobule=False) -> None:
        self.value = value
        self.suit = suit
        self.is_pass = is_pass
        self.is_double = is_dobule
    def is_greater(self, other):
        if not other:
            return True
        if self.value > other.value:
            return True
        if self.value == other.value:
            if self.suit > other.suit:
                return True
        return False

class Auction():
    def __init__(self, south, west, north, east) -> None:
        self.players = [south,west,north,east]
        self.declares = [[],[],[],[]]
        self.doubled = False
        self.num_passes = 0
        self.bid_turn = 0
        self.current_bid = None
    def make_bid(self, player, bid:Bid):
        player_index = self.bid_turn%len(self.players)
        partner_index = (self.bid_turn+2)%len(self.players)
        assert player is self.players[player_index]
        if bid.is_pass:
            self.bid_turn += 1
            self.num_passes += 1
            return True
        elif bid.is_double and not self.doubled:
            self.bid_turn += 1
            self.num_passes += 1
            self.is_doubled = True
            return True
        elif bid.is_greater(self.current_bid):
            self.current_bid = bid
            if bid.suit not in self.declares[player_index] + self.declares[partner_index]:
                self.declares[player_index].append(bid.suit)
            self.bid_turn += 1
            self.is_doubled = False
            return True
        print(f"You can't bid {bid}")
        return False


class Rubber():
    def __init__(self, partnership1, partnership2) -> None:
        self.partnership1 = partnership1
        self.partnership2 = partnership2
        self.is_over = False

    def check_for_rubber(self):
        if self.partnership1.games == 2:
            return True
        if self.partnership2.games == 2:
            return True
        return False
    def score_rubber(self):
        self.is_over = True
        rubber_score = 700
        if self.partnership1.games + self.partnership2.games == 3:
            rubber_score = 500

        if self.partnership1.games == 2:
            self.partnership1.award(rubber_score,0)

        if self.partnership2.games == 2:
            self.partnership2.award(rubber_score,0)

    def start(self):
        pass

class ContractBridge():
    def __init__(self, players) -> None:
        self.players = players
        self.hands = {}
        self.players_to_played_cards = defaultdict(None)
        self.players_to_cards = defaultdict(list)

    def get_hands(self):
        return self.players_to_cards
    def get_played_cards(self):
        return self.players_to_played_cards
    def deal(self):
        cards_exist = False
        for  cards in self.players_to_cards.values():
            if len(cards) > 0:
                cards_exist = True
        if cards_exist and len(self.players_to_cards.keys()) != 4:
            return False
        else:
            hands = deal_cards()
            for i, player in enumerate(self.players_to_cards):
                self.players_to_cards[player] = hands[i]
                self.players_to_played_cards[player] = None
            return True

    def play_card(self, player, card_code):
        card = Card.from_code(card_code)
        if self.players_to_played_cards[player]:
            return False
        if card in self.players_to_cards[player]:
            self.players_to_played_cards[player] = card
            self.players_to_cards[player].remove(card)
            return True
        else:
            return False

    def take_trick(self, player):
        four_cards = True
        for value in self.players_to_played_cards.values():
            if value is None:
                four_cards = False
        if four_cards:
            for i, player in enumerate(self.players_to_cards):
                self.players_to_played_cards[player] = None
            return True
        return False

    # def draw_for_partners(self):
    #     self.has_drawn_for_partners = True
    #     self.rubber1 = Rubber(Partnership(self.player1, self.player2), Partnership(self.player3, self.player4))
    #     self.rubber2 = Rubber(Partnership(self.player1, self.player3), Partnership(self.player2, self.player4))
    #     self.rubber3 = Rubber(Partnership(self.player1, self.player4), Partnership(self.player3, self.player4))

    # def play_rubber1(self):
    #     assert not self.has_played_rubber1 and not self.has_played_rubber2 and not self.has_played_rubber3
    #     self.rubber1.start()
    # def play_rubber2(self):
    #     assert self.has_played_rubber1 and not self.has_played_rubber2 and not self.has_played_rubber3
    # def play_rubber3(self):
    #     assert self.has_played_rubber1 and self.has_played_rubber2 and not self.has_played_rubber3


def deal_cards():
    # Create a standard deck (no NO_TRUMP)
    deck = [Card(value, suit) for suit in list(Suit)[:4] for value in range(1, 14)]

    # Shuffle the deck
    random.shuffle(deck)

    # Deal cards to four players
    hands = [[], [], [], []]
    for i, card in enumerate(deck):
        hands[i % 4].append(card)

    # Define custom sort key: suit priority first, then value (descending)
    suit_priority = {
        Suit.SPADES: 0,
        Suit.HEARTS: 1,
        Suit.CLUBS: 2,
        Suit.DIAMONDS: 3
    }

    for hand in hands:
        hand.sort(key=lambda card: (suit_priority[card.suit], -card.value))

    return hands