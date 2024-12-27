from dataclasses import asdict
from typing import Any

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from ExplodingKittensGame import ExplodingKittensGame, Cards

MAX_CARDS_PER_TYPE = 10

class ExplodingKittensGym(gym.Env):
    def __init__(self):
        super().__init__()
        
        self.game = ExplodingKittensGame("game_config_very_small.json")

        self.card_to_int_mapping = {
            card: i for i, card in enumerate(Cards)
        }
        
        self.int_to_card_mapping = {
            i: card for i, card in enumerate(Cards)
        }

        self.action_space = spaces.Discrete(Cards.num_playable_card_types())
        self.observation_space = spaces.Dict(
            {
                "deck": spaces.Sequence(spaces.Discrete(Cards.num_card_types()), stack=True),
                "player_hands": spaces.Sequence(
                    spaces.Box(low=0, high=MAX_CARDS_PER_TYPE, shape=(Cards.num_playable_card_types(),), dtype=int),
                    stack=True
                ),
                "player_is_out": spaces.Sequence(
                    spaces.MultiBinary(n=1),
                    stack=True
                ),
                "current_player": spaces.Discrete(2),
                "play_direction": spaces.Discrete(2),
                'discard_pile': spaces.Sequence(spaces.Discrete(Cards.num_card_types())),
                'num_attacks': spaces.Discrete(10),
                'current_player_played_attack': spaces.Discrete(2),
            }
        )

        # sample = self.observation_space.sample()
        # print(sample, sample['player_is_out'].shape)

    def reset(self, seed: Any = None):
        self.seed = seed
        self.game = ExplodingKittensGame("game_config_very_small.json")

        info = {}

        return (self.game_state, info)

    def step(self, action: Any):
        if action == 0:
            self.game.draw_card()
        else:
            card = self.int_to_card_mapping[action]
            self.game.play_card(card)

        reward = 0
        terminated = False
        truncated = False
        info = {}
        return (self.game_state, reward, terminated, truncated, info)
    
    @property
    def game_state(self):
        _game_state = asdict(self.game.game_state)

        _game_state['current_player_played_attack'] = int(_game_state['current_player_played_attack'])

        _game_state['deck'] = np.array([self.card_to_int_mapping[card] for card in _game_state['deck']], dtype=int)

        _game_state['discard_pile'] = np.array([self.card_to_int_mapping[card] for card in _game_state['discard_pile']], dtype=int)

        _game_state['play_direction'] = 0 if _game_state['play_direction'] == 'left' else 1

        _game_state['player_hands'] = np.array(
            [list(player_state['hand'].values()) for player_state in _game_state['player_states']]
        )

        _game_state['player_is_out'] = np.array(
            [int(player_state['is_out']) for player_state in _game_state['player_states']]
        )

        del _game_state['player_states']

        return _game_state
    
if __name__ == "__main__":
    from stable_baselines3.common.env_checker import check_env

    env = ExplodingKittensGym()
    state, info = env.reset()

    print(state)

    (state, reward, terminated, truncated, info) = env.step(0)

    print(state)

    