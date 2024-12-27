from dataclasses import asdict
from typing import Any
import logging

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from ExplodingKittensGame import ExplodingKittensGame, ExplodingKittensGameState, Cards

MAX_CARDS_PER_TYPE = 10

def _get_total_num_cards(game_state: ExplodingKittensGameState) -> int:
    return len(game_state.deck) \
        + len(game_state.discard_pile) \
        + sum([sum(player_state.hand.values()) for player_state in game_state.player_states])

class ExplodingKittensGym(gym.Env):
    def __init__(self):
        super().__init__()

        self.logger = logging.getLogger(__name__)
        
        self.game = ExplodingKittensGame("game_config_very_small.json")

        self.total_num_cards = _get_total_num_cards(self.game.game_state)

        self.card_to_int_mapping = {
            card: i for i, card in enumerate(Cards)
        }
        
        self.int_to_card_mapping = {
            i: card for i, card in enumerate(Cards)
        }

        self.action_space = spaces.Discrete(Cards.num_playable_card_types() + 1)
        self.observation_space = spaces.Dict(
            {
                "deck": spaces.MultiDiscrete([Cards.num_card_types()+1]*self.total_num_cards), #spaces.Sequence(spaces.Discrete(Cards.num_card_types()), stack=True),
                "player_0_hand": spaces.Box(low=0, high=MAX_CARDS_PER_TYPE, shape=(Cards.num_playable_card_types(),), dtype=int),
                "player_1_hand": spaces.Box(low=0, high=MAX_CARDS_PER_TYPE, shape=(Cards.num_playable_card_types(),), dtype=int),
                "player_0_is_out": spaces.Discrete(2),
                "player_1_is_out": spaces.Discrete(2),
                "current_player": spaces.Discrete(2),
                "play_direction": spaces.Discrete(2),
                'discard_pile': spaces.MultiDiscrete([Cards.num_card_types()+1]*self.total_num_cards), #spaces.Sequence(spaces.Discrete(Cards.num_card_types())),
                'num_attacks': spaces.Discrete(10),
                'current_player_played_attack': spaces.Discrete(2),
            }
        )

    def reset(self, seed: Any = None):
        self.seed = seed

        self.game = ExplodingKittensGame("game_config_very_small.json")

        info = {}

        return (self.game_state, info)

    def step(self, action: Any):
        reward = 0

        if action == Cards.num_playable_card_types():
            self.game.draw_card()
        else:
            card = self.int_to_card_mapping[action]
            if card not in self.game.game_state.playable_card_types:
                self.logger.info("CHOSEN CARD {} is not in playable_card_types {}".format(card, self.game.game_state.playable_card_types))
                reward = -0.1
                self.game.draw_card()
            else:
                self.game.play_card(card)

        terminated = self.game.game_state.game_over            

        truncated = False

        info = {}

        return (self.game_state, reward, terminated, truncated, info)
    
    @property
    def game_state(self):
        _game_state = asdict(self.game.game_state)

        _game_state['current_player_played_attack'] = int(_game_state['current_player_played_attack'])

        deck = np.ones((self.total_num_cards), dtype=int) * Cards.num_card_types()
        for i, card in enumerate(_game_state['deck']):
            deck[i] = self.card_to_int_mapping[card]

        _game_state['deck'] = deck

        discard_pile = np.ones((self.total_num_cards), dtype=int) * Cards.num_card_types()
        for i, card in enumerate(_game_state['discard_pile']):
            discard_pile[i] = self.card_to_int_mapping[card]

        _game_state['discard_pile'] = discard_pile

        _game_state['play_direction'] = 0 if _game_state['play_direction'] == 'left' else 1

        _game_state['player_0_hand'] = np.array(list(_game_state['player_states'][0]['hand'].values()))
        _game_state['player_1_hand'] = np.array(list(_game_state['player_states'][1]['hand'].values()))

        _game_state['player_0_is_out'] = int(_game_state['player_states'][0]['is_out'])
        _game_state['player_1_is_out'] = int(_game_state['player_states'][1]['is_out'])

        del _game_state['player_states']

        return _game_state
    
    def get_random_action(self):
        card_chosen = np.random.choice(self.game.game_state.playable_card_types)
        return self.card_to_int_mapping[card_chosen]


if __name__ == "__main__":
    from stable_baselines3.common.env_checker import check_env

    env = ExplodingKittensGym()
    state, info = env.reset()

    print(state)

    (state, reward, terminated, truncated, info) = env.step(0)

    print(state)

    