import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
import numpy as np

from ExplodingKittensGym import ExplodingKittensGym
from ExplodingKittensSinglePlayerGym import ExplodingKittensSinglePlayerGym

# Import the EKGameV0 environment
from game2 import EKGameV0

# Create the environment
env = ExplodingKittensSinglePlayerGym()

# Check if the environment follows the gymnasium interface
check_env(env, warn=True)

# Create the PPO agent
model = PPO("MultiInputPolicy", env, verbose=1)

# Train the agent
model.learn(total_timesteps=500000)

# # Save the model
model.save("ppo_ekgamesingle4")

# # To demonstrate loading and using the model
del model  # delete the trained model to demonstrate loading

# Load the trained model
model = PPO.load("ppo_ekgamesingle4")

# Enjoy trained agent
num_wins = 0
num_games = 10000
total_rewards = 0
for i in range(num_games):
    obs, info = env.reset()
    done = False
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        action = action.item()
        # action = env.get_random_action()
        obs, rewards, done, truncated, info = env.step(action)

    if rewards == 1:
        total_rewards += 1

    if env.game.game_state.winner == 1:
        num_wins += 1

print("Wins: {}, Rewards: {}, Percent: {}".format(num_wins, total_rewards, 100*num_wins/num_games))

    