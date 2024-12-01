# SELF PLAY
EPISODES = 8
MCTS_SIMS = 50
MEMORY_SIZE = 256
TURNS_UNTIL_TAU0 = 10  # turn on which it starts playing deterministically
CPUCT = 3
EPSILON = 0.2
ALPHA = 0.8


# RETRAINING
BATCH_SIZE = 256
EPOCHS = 1
REG_CONST = 0.0001
LEARNING_RATE = 0.01
MOMENTUM = 0.9
TRAINING_LOOPS = 500

HIDDEN_CNN_LAYERS = [
    {'filters': 75, 'kernel_size': (4, 4)},
    {'filters': 75, 'kernel_size': (4, 4)}
]

# EVALUATION
EVAL_EPISODES = 20
SCORING_THRESHOLD = 1.2
