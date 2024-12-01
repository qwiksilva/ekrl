from game import Game, GameState, Cards

def print_hand(hand):
    print('\t', hand)
    for card_type, num_cards in enumerate(hand):
        print('\t', Cards(card_type), ":", num_cards, '\t(action number', card_type, ')')

def print_game_state(g):
    print_allowed_actions(g)
    print('currentPlayer:', g.gameState.currentPlayer)
    print('currentHand:')
    print_hand(g.gameState.currentHand)
    print('opposingHand:')
    print_hand(g.gameState.opposingHand)

def print_allowed_actions(g):
    print('Allowed actions:')
    for action in g.gameState._allowedActions():
        print('\t', Cards(action), ":",  action)

g = Game()
num_steps = 10
for t in range(num_steps):
    print_game_state(g)
    input_action = int(input())
    print('Action selected:', input_action)
    (next_state, value, done, penalizeplayer) = g.step