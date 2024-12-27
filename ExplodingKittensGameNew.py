from typing import TypedDict, DefaultDict
from enum import Enum
import json
from dataclasses import dataclass, asdict, field
import random
import logging

import numpy as np

logger = logging.getLogger(__name__)

class Cards(str, Enum):
    EXPLODING_KITTEN = 0
    DEFUSE = 1
    ATTACK = 2
    SKIP = 3
    FAVOR = 4
    SHUFFLE = 5
    CAT1 = 6
    CAT2 = 7
    CAT3 = 8
    CAT4 = 9
    CAT5 = 10
    
    
    @staticmethod
    def num_card_types() -> int:
        return len(Cards)
    
    @staticmethod
    def num_playable_card_types() -> int:
        return len(Cards) - 1
    
def is_cat_card(card_type: Cards) -> bool:
    return True if 'CAT' in card_type else False

def empty_hand() -> dict[Cards, int]:
    return {
        Cards.DEFUSE.value: 0,
        Cards.ATTACK.value: 0,
        Cards.SKIP.value: 0,
        Cards.FAVOR.value: 0,
        Cards.SHUFFLE.value: 0,
        Cards.CAT1.value: 0,
        Cards.CAT2.value: 0,
        Cards.CAT3.value: 0,
        Cards.CAT4.value: 0,
        Cards.CAT5.value: 0,
    }

@dataclass
class PlayerState:
    hand: dict[Cards, int] = field(default_factory=empty_hand)
    is_out: bool = False

class ExplodingKittensGame:
    def __init__(self, config_file, debug=False):
        self.debug = debug
        self.game_state = ExplodingKittensGameState()

        if config_file is None:
            config_file = None
        else:
            with open(config_file, "r") as f:
                self.game_config = json.load(f)

        self.reset()

    def reset(self) -> None:
        # Put all card in deck except E.K. and 2 defuse cards        
        deck = [Cards.DEFUSE.value] * self.game_config["num_defuse_cards"] \
            + [Cards.ATTACK.value] * self.game_config["num_attack_cards"] \
            + [Cards.SKIP.value] * self.game_config["num_skip_cards"] \
            + [Cards.FAVOR.value] * self.game_config["num_favor_cards"] \
            + [Cards.SHUFFLE.value] * self.game_config["num_shuffle_cards"] \
            + [Cards.CAT1.value] * self.game_config["num_cat1_cards"] \
            + [Cards.CAT2.value] * self.game_config["num_cat2_cards"] \
            + [Cards.CAT3.value] * self.game_config["num_cat3_cards"] \
            + [Cards.CAT4.value] * self.game_config["num_cat4_cards"] \
            + [Cards.CAT5.value] * self.game_config["num_cat5_cards"]

        # Shuffle deck
        random.shuffle(deck)

        # Deal hands (plus 1 defuse)
        players = []
        for _ in range(self.game_config["num_players"]):
            player_state = PlayerState()
            for _ in range(self.game_config["num_cards_in_starting_hand"]):
                card = deck.pop()
                player_state.hand[card] += 1
            player_state.hand[Cards.DEFUSE.value] += self.game_config["num_defuse_cards_in_starting_hand"]

            players.append(player_state)

        # Insert E.K. into deck randomly
        num_eks_to_insert = self.game_config["num_players"] - 1
        logger.info('Inserting ' + str(num_eks_to_insert) + ' E.K. cards into deck')
        for _ in range(num_eks_to_insert):
            position = random.randint(0, len(deck)-1)
            deck.insert(position, Cards.EXPLODING_KITTEN.value)

        self.game_state = ExplodingKittensGameState(deck, players)

    def is_valid_card_type(self, card_type: int) -> bool:
        return card_type in self.game_state.playable_card_types

    def draw_card(self) -> None:
        if self.game_state.game_over:
            logger.info('NOT DRAWING CARD - GAME OVER')
            return
        # Draw a card from the deck
        card = self.game_state.deck.pop()
        logger.info('CARD DRAWN WAS: ' + card)
        if card == Cards.EXPLODING_KITTEN:
            logger.info('BOMB WAS DRAWN')
            if self.game_state.current_hand[Cards.DEFUSE.value] > 0:
                logger.info('PLAYER HAS DEFUSE')

                # Has a defuse
                self.game_state.current_hand[Cards.DEFUSE.value] -= 1
                self.game_state.discard_pile = np.append(self.game_state.discard_pile, [Cards.DEFUSE.value])

                # Insert E.K. into deck randomly
                if len(self.game_state.deck) == 0:
                    self.game_state.deck = np.append([card], self.game_state.deck)
                else:
                    position = random.randint(0, len(self.game_state.deck)-1)
                    np.insert(self.game_state.deck, position, card)
            else:
                logger.info('PLAYER ' + str(self.game_state.current_player) + ' IS OUT')
                self.game_state.player_is_out[self.game_state.current_player] = True
                np.append(self.game_state.discard_pile, [Cards.EXPLODING_KITTEN.value])

                num_players_in = 0
                winner = None
                for (i, is_out) in enumerate(self.game_state.player_is_out):
                    if not is_out:
                        winner = i
                        num_players_in += 1

                assert num_players_in == 1 and winner is not None

                logger.info('WINNER: PLAYER ' + str(winner))

        else:
            self.game_state.current_hand[card] += 1

        # Go to next player
        self.game_state.current_player = self.game_state.next_player

    def play_card(self, card_type, opponent_selected=None) -> None:
        logger.info('PLAYING CARD: ' + str(card_type))
        # Make sure the action taken is valid. If not, return the same state and redo the turn.
        if not self.is_valid_card_type(card_type):
            logger.info('INVALID CARD TYPE: ' + str(card_type))
            return

        # Get the card corresponding to the action
        card = card_type

        # Take the card out of the hand
        self.game_state.current_hand[card_type] -= 1
        np.append(self.game_state.discard_pile, card)

        # Logic depending on which card was played
        if card == Cards.ATTACK:
            # Add 2 attacks counts to the current number of attack counts
            self.game_state.num_attacks += 2

            self.game_state.current_player_played_attack = True
            logger.info('(play_card) current_player_played_attack: ' + str(self.game_state.current_player_played_attack))

            # Go to next player
            self.game_state.current_player = self.game_state.next_player

            self.game_state.current_player_played_attack = False

        elif card == Cards.SKIP:
            # Go to next player
            self.game_state.current_player = self.game_state.next_player

        elif card == Cards.SHUFFLE:
            random.shuffle(self.game_state.deck)

        elif card == Cards.FAVOR:
            # If no opponent was selected or selected opponent has no cards, choose opponent at random
            if opponent_selected is None or sum(self.game_state.player_hands[opponent_selected].values()) == 0:
                opponents = [i for i in range(self.game_state.num_players) if i != self.game_state.current_player and sum(self.game_state.player_states[i].hand.values()) > 0 and not self.game_state.player_states[i].is_out]
                opponent_selected = np.random.choice(opponents)
            assert opponent_selected != self.game_state.current_player and opponent_selected in range(self.game_state.num_players)

            chosen_card = random.choices(list(self.game_state.player_states[opponent_selected].hand.keys()), self.game_state.player_states[opponent_selected].hand.values())[0]
            
            logger.info('PLAYER SELECTED: PLAYER ' + str(opponent_selected))
            logger.info('PLAYER RANDOMLY CHOSE CARD: ' + str(chosen_card))

            self.game_state.current_hand[chosen_card] += 1
            self.game_state.player_states[opponent_selected].hand[chosen_card] -= 1

        elif is_cat_card(card):
            self.game_state.current_hand[card] -= 1
            self.game_state.discard_pile.append(card)

            # If no opponent was selected or selected opponent has no cards, choose opponent at random
            if opponent_selected is None or sum(self.game_state.player_states[opponent_selected].hand.values()) == 0:
                opponents = [i for i in range(self.game_state.num_players) if i != self.game_state.current_player and sum(self.game_state.player_states[i].hand.values()) > 0 and not self.game_state.player_states[i].is_out]
                opponent_selected = np.random.choice(opponents)
            assert opponent_selected != self.game_state.current_player and opponent_selected in range(self.game_state.num_players)

            chosen_card = random.choices(list(self.game_state.player_states[opponent_selected].hand.keys()), self.game_state.player_states[opponent_selected].hand.values())[0]
            
            logger.info('PLAYER SELECTED: PLAYER ' + str(opponent_selected))
            logger.info('PLAYER RANDOMLY CHOSE CARD: ' + str(chosen_card))

            self.game_state.current_hand[chosen_card] += 1
            self.game_state.player_states[opponent_selected].hand[chosen_card] -= 1


@dataclass
class ExplodingKittensGameState:
    deck: np.array = field(default_factory=lambda: np.array([]))
    player_hands: np.array = field(default_factory=lambda: np.array([]))
    player_is_out: np.array = field(default_factory=lambda: np.array([]))
    # player_states: list[PlayerState] = field(default_factory=list)
    current_player: int = 0
    play_direction: str = 'left'
    discard_pile: np.array = field(default_factory=lambda: np.array([]))
    num_attacks: int = 0
    current_player_played_attack: bool = False
    # test: np.array = field(default_factory=lambda: np.array([]))

    @property
    def game_over(self) -> bool:
        return len(self.deck) == 0 or sum(self.player_is_out) == self.num_players - 1

    @property
    def current_hand(self) -> dict[Cards, int]:
        return self.player_hands[self.current_player]
        
    @property
    def num_players(self) -> int:
        return len(self.player_hands)
    
    @property
    def last_played_card(self) -> Cards:
        return self.discard_pile[-1] if self.discard_pile else None
    
    @property
    def playable_card_types(self) -> set[int]:

        _playable_card_types = set()

        for card_type, num_cards_of_type in self.current_hand.items(): 
            
            if num_cards_of_type == 0:
                # If no cards of this type are the hand, this card acannot be played
                continue  
          
            if card_type == Cards.DEFUSE:
                # TODO This action signifies playing a defuse card. Disallow for now, but we can potentially
                # have the agent learn that they should never play this card to show that the agent
                # is learning something
                continue
           
            elif card_type == Cards.ATTACK:
                # To simplify, disallow playing an attack card the first turn after
                # one has just been played
                if self.last_played_card != Cards.ATTACK:
                    _playable_card_types.add(card_type)
            
            elif card_type == Cards.SHUFFLE:
                # Can always play a shuffle card
                _playable_card_types.add(card_type)
            
            elif card_type == Cards.SKIP:
                # Can always play a skip card
                _playable_card_types.add(card_type)
            
            elif card_type == Cards.FAVOR:
                # Favor card requires at least one opponent to have a card in their hand
                for playerId, player_state in enumerate(self.player_states):
                    if playerId != self.current_player and sum(player_state.hand.values()) > 0 and player_state.is_out == False:
                        _playable_card_types.add(card_type)
                        break
            
            elif is_cat_card(card_type):
                # Game rules dictate there must be 2 of a kind to play a 'CAT' card
                if num_cards_of_type >= 2:
                    for playerId, player_state in enumerate(self.player_states):
                        if playerId != self.current_player and sum(player_state.hand.values()) > 0:
                            _playable_card_types.add(card_type)
                            break

        return _playable_card_types
    
    @property
    def next_player(self) -> int:
        logger.info('=====================END OF TURN=====================')
        
        # If attacks count is not zero at the end of the turn, currentPlayer stays the same
        # logger.debug('LAST_PLAYED_CARD: ' + str(self.last_played_card))
        # logger.debug('NUM_ATTACKS: ' + str(self.num_attacks))
        # logger.debug(self.last_played_card != Cards.ATTACK)
        # logger.debug(self.num_attacks > 0)
        # logger.debug(self.last_played_card != Cards.ATTACK and self.num_attacks > 0)
        

        if not self.current_player_played_attack and self.num_attacks > 0:
            self.num_attacks -= 1
            logger.debug('NUM_ATTACKS: ' + str(self.num_attacks))
            if self.num_attacks > 0:
                logger.info('NEW CURRENT PLAYER: ' + str(self.current_player))
                return self.current_player

        # Cycle through players in play direction until player that is in is found
        dir = -1 if self.play_direction == "left" else 1
        current_player = (self.current_player + dir) % self.num_players
        while self.player_states[current_player].is_out:
            current_player = (current_player + dir) % self.num_players

        logger.info('NEW CURRENT PLAYER: ' + str(current_player))
        
        return current_player


def test(ekgs):
    card = Cards.DEFUSE
    _ = ekgs.player_states[0].hand[card]
    _ = ekgs.player_states[0].hand['DEFUSE']

def test_json(ekg):
    json.dumps(asdict(ekg.game_state))

if __name__ == "__main__":
    import pprint

    logging.basicConfig(level=logging.DEBUG)

    num_players = 2
    ekgs = ExplodingKittensGameState()
    ekgs.player_states = [PlayerState() for _ in range(num_players)]

    test(ekgs)

    # logger.debug(json.dumps(asdict(ekgs)))

    ekg = ExplodingKittensGame('game_config_very_small.json')

    pprint.pp(asdict(ekg.game_state), indent=0)

    # logger.debug()

    ekg.play_card(Cards.ATTACK)
    ekg.draw_card()

    pprint.pp(asdict(ekg.game_state), indent=0)


