from dataclasses import asdict
from typing import Any
import random
import logging
import json
import pprint

import numpy as np
from gymnasium import spaces
from stable_baselines3 import PPO

from ExplodingKittensGame import Cards
from ExplodingKittensGym import ExplodingKittensGym, MAX_CARDS_PER_TYPE

class ExplodingKittensSinglePlayerGym(ExplodingKittensGym):
    def __init__(self, config_file: str = None):
        super().__init__()

        self.logger = logging.getLogger(__name__)

        self.bot_player_type = "random"

        if config_file is not None:
            with open(config_file, "r") as f:
                self.config = json.load(f)

            self.bot_player_type = self.config["bot_player_type"]

            if self.bot_player_type == "agent":
                self.logger.info("LOADING AGENT")
                self.agent = PPO.load(self.config["agent_path"])

        # Player is the agent stepping the gym, and is 0 if they go first, 1 if they go second
        self.player_number = 1#random.choice([0, 1])

        self.action_space = spaces.Discrete(Cards.num_playable_card_types() + 1)
        self.observation_space = spaces.Dict(
            {
                "deck": spaces.MultiDiscrete([Cards.num_card_types()+1]*self.total_num_cards), #spaces.Sequence(spaces.Discrete(Cards.num_card_types()), stack=True),
                "player_hand": spaces.Box(low=0, high=MAX_CARDS_PER_TYPE, shape=(Cards.num_playable_card_types(),), dtype=int),
                "opponent_hand": spaces.Box(low=0, high=MAX_CARDS_PER_TYPE, shape=(Cards.num_playable_card_types(),), dtype=int),
                "player_is_out": spaces.Discrete(2),
                "opponent_is_out": spaces.Discrete(2),
                "current_player": spaces.Discrete(2),
                "play_direction": spaces.Discrete(2),
                'discard_pile': spaces.MultiDiscrete([Cards.num_card_types()+1]*self.total_num_cards), #spaces.Sequence(spaces.Discrete(Cards.num_card_types())),
                'num_attacks': spaces.Discrete(10),
                'current_player_played_attack': spaces.Discrete(2),
            }
        )

    def reset(self, seed: Any = None):
        (game_state, info) = super().reset(seed)
    
        if self.player_number == 1:
            while (self.player_number is not self.game.game_state.current_player) and not self.game.game_state.game_over:
                action = self.get_bot_action()
                (game_state, _, _, _, info) = super().step(action)

        obs = self.game_state
        self.logger.info("GAME STATE:\n{}".format(pprint.pformat(obs, indent=4)))

        return (game_state, info)
    
    def get_bot_action(self) -> int:
        # obs = self.game_state
        # self.logger.info("GAME STATE:\n{}".format(pprint.pformat(obs, indent=4)))
        if self.bot_player_type == "random":
            return self.get_random_action()
        elif self.bot_player_type == "agent":
            return self.get_agent_action()

    def get_agent_action(self) -> int:
        obs = self.game_state
        action, _ = self.agent.predict(obs, deterministic=True)
        self.logger.info("AGENT CHOSE ACTION: " + str(action))
        return action.item()

    def get_random_action(self) -> int:
        playable_card_types = list(self.game.game_state.playable_card_types)
        self.logger.info("PLAYABLE CARD TYPES: " + str([str(playable_card_type) for playable_card_type in playable_card_types]))
        playable_card_types.append('DRAW_CARD')

        chosen_action = random.choice(playable_card_types)

        self.logger.info("CHOSEN ACTION: {}".format(chosen_action))

        try:
            action = self.card_to_int_mapping[chosen_action]
            self.logger.info("ACTION: {}".format(action))
            
        except:
            action = Cards.num_playable_card_types()
            self.logger.info("ACTION: {}".format(action))

        return action

    def step(self, action: Any):
        (_, reward, terminated, truncated, info) = super().step(action)

        while (self.player_number is not self.game.game_state.current_player) and not terminated:
            action = self.get_bot_action()
            (_, _, terminated, truncated, info) = super().step(action)

        end_reward = 1 if (self.game.game_state.winner == self.player_number) else 0

        reward += end_reward

        game_state = self.game_state

        obs = self.game_state
        self.logger.info("GAME STATE:\n{}".format(pprint.pformat(obs, indent=4)))

        return (game_state, reward, terminated, truncated, info)
    
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

        opponent_number = 1 - self.player_number

        _game_state['player_hand'] = np.array(list(_game_state['player_states'][self.player_number]['hand'].values()))
        _game_state['opponent_hand'] = np.array(list(_game_state['player_states'][opponent_number]['hand'].values()))

        _game_state['player_is_out'] = int(_game_state['player_states'][self.player_number]['is_out'])
        _game_state['opponent_is_out'] = int(_game_state['player_states'][opponent_number]['is_out'])

        del _game_state['player_states']

        return _game_state
        
if __name__ == "__main__":
    from stable_baselines3.common.env_checker import check_env

    env = ExplodingKittensGym()
    state, info = env.reset()

    print(state)

    (state, reward, terminated, truncated, info) = env.step(0)

    print(state)

    