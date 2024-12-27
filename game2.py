import numpy as np
import logging
import random
from enum import Enum
import json
import gymnasium as gym
from gymnasium import spaces

import pdb

# TODO: check out: https://github.com/pirasalbe/Exploding-Kittens-Telegram-bot/tree/main

# Mapping from Card Type to position (index) in the Agent's state
class Cards(Enum):
    DEFUSE = 0
    ATTACK = 1
    SKIP = 2
    FAVOR = 3
    SHUFFLE = 4
    CAT1 = 5
    CAT2 = 6
    CAT3 = 7
    CAT4 = 8
    CAT5 = 9
    EXPLODING_KITTEN = 15

    @staticmethod
    def numCardTypes():
        return len(Cards) - 1

class PlayerState:
    def __init__(self, hand):
        self.hand = hand
        self.isOut = False

def isCatCard(value):
    return True if (value > 4 and value < 10) else False

class EKGameV0(gym.Env):
    def __init__(self, config_file=None, debug=False):
        super(EKGameV0, self).__init__()

        if config_file is None:
            config_file = None
        else:
            with open(config_file, "r") as f:
                self.game_config = json.load(f)

        self.NUM_CARD_TYPES = 10
        self.NUM_CARDS_IN_STARTING_DECK = sum([int(self.game_config[k]) for k in self.game_config if "card" in k and "in_starting_hand" not in k])
        self.NUM_TOTAL_CARDS = self.NUM_CARDS_IN_STARTING_DECK + sum([int(self.game_config[k]) for k in self.game_config if "in_starting_hand" in k]) * self.game_config["num_players"]

        self.debug = debug
        self.playerId = 0
        # self.actionSpace = np.array([0] * self.NUM_CARD_TYPES, dtype=int)
        # self.action_size = len(self.actionSpace)
        self.name = 'exploding_kittens'
        
        
        if self.debug:
            print(self.NUM_TOTAL_CARDS)
            print(self.NUM_CARDS_IN_STARTING_DECK)

        # Define action and observation space
        # They must be gymnasium.spaces objects
        self.action_space = spaces.Discrete(self.NUM_CARD_TYPES)
        self.observation_space = spaces.MultiDiscrete([2])

        self.reset()

    def reset(self, seed=None):
        # Put all card in deck except E.K. and 2 defuse cards        
        deck = [Cards.DEFUSE] * self.game_config["num_defuse_cards"] \
                + [Cards.ATTACK] * self.game_config["num_attack_cards"] \
                + [Cards.SKIP] * self.game_config["num_skip_cards"] \
                + [Cards.FAVOR] * self.game_config["num_favor_cards"] \
                + [Cards.SHUFFLE] * self.game_config["num_shuffle_cards"] \
                + [Cards.CAT1] * self.game_config["num_cat1_cards"] \
                + [Cards.CAT2] * self.game_config["num_cat2_cards"] \
                + [Cards.CAT3] * self.game_config["num_cat3_cards"] \
                + [Cards.CAT4] * self.game_config["num_cat4_cards"] \
                + [Cards.CAT5] * self.game_config["num_cat5_cards"]

        # Shuffle deck
        random.shuffle(deck)

        # Deal hands (plus 1 defuse)
        hand1 = [0] * self.NUM_CARD_TYPES
        for _ in range(self.game_config["num_cards_in_starting_hand"]):
            card = deck.pop()
            hand1[card.value] += 1
        hand1[Cards.DEFUSE.value] += self.game_config["num_defuse_cards_in_starting_hand"]
        player1 = PlayerState(hand1)

        hand2 = [0] * self.NUM_CARD_TYPES
        for _ in range(self.game_config["num_cards_in_starting_hand"]):
            card = deck.pop()
            hand2[card.value] += 1
        hand2[Cards.DEFUSE.value] += self.game_config["num_defuse_cards_in_starting_hand"]
        player2 = PlayerState(hand2)

        players = [player1, player2]
        currentPlayer = self.playerId
        # currentPlayer = random.choice([0, 1])

        # Insert E.K. into deck randomly
        position = random.randint(0, len(deck)-1)
        deck.insert(position, Cards.EXPLODING_KITTEN)
        self.gameState = ExplodingKittensGameState(deck, players, currentPlayer, self.debug)

        self.STARTING_DECK_SIZE = len(deck)

        return (self.observation, {})

    def step(self, action):
        # Make sure the action is valid in this game state
        isValidAction = self.gameState.isValidAction(action)
        if self.debug and not isValidAction:
            print("INVALID ACTION, TRY AGAIN")

        if self.debug:
            print("Own observation:", self.observation)
            print("Own state:", self.state)
            print('Own action selected:', action, Cards(action))

        # reward is 0 unless the game is over
        reward = 0

        # Execute the given action and 
        done = self.gameState.takeAction(action)

        # Check if this action ended the game, in which case the player lost and reward is -1
        if done:
            reward = -1

        # execute random action for opponent
        while not done and self.gameState.currentPlayer != self.playerId:
            if self.debug:
                print("Opponent observation:", self.observation)
                print("Opponent state:", self.state)

            allowedActions = self.gameState.allowedActions
            action = allowedActions[random.randint(0, len(allowedActions)-1)]
            action = self.getRandomAction()

            if self.debug:
                print('Opponent action selected:', action, Cards(action))


            # Check if opponent action ended the game, in which case the player won and reward is 1
            done = self.gameState.takeAction(action)
            if done:
                reward = 1
                # break

        info = {
            'validAction': isValidAction
        }

        # Sends current (state reward, done, and info)
        return (self.observation, reward, done, info)

    @property
    def observation(self):
        discard = [0]*10
        for card in self.gameState.discardPile:
            discard[card.value] += 1

        playerStates = []
        playerStates.append(",".join([str(x) for x in self.gameState.playerHands[self.playerId].hand]))

        for playerIdx, playerState in enumerate(self.gameState.playerHands):
            if playerIdx != self.playerId:
                playerStates.append(str(sum(playerState.hand)))

        # for playerIdx, playerState in enumerate(self.gameState.playerHands):
        #     if playerIdx == self.gameState.currentPlayer:
        #         # if playerIdx != 0:
        #         #     print("STATE IS NOT GOOD")
        #         #     pdb.set_trace()
        #         playerStates.append(",".join([str(x) for x in playerState.hand]))
        #     else:
        #         playerStates.append(str(sum(playerState.hand)))

        deck = [0] * self.STARTING_DECK_SIZE
        deck[:len(self.gameState.deck)] = self.gameState.deck

        obs = np.array(playerStates + deck + discard)

        # obs = "|".join(playerStates) + "|" + str(len(self.gameState.deck)) + "|" + ",".join([str(x) for x in discard])
        # state = "|".join([",".join([str(x) for x in playerState.hand]) for playerState in self.playerHands]) + "|" + str(len(self.deck)) + "|" + ",".join([str(x) for x in discard])
        return obs

    @property
    def state(self):
        discard = [0]*10
        for card in self.gameState.discardPile:
            discard[card.value] += 1

        playerStates = []
        for playerIdx, playerState in enumerate(self.gameState.playerHands):
            playerStates.append(",".join([str(x) for x in playerState.hand]))

        obs = "|".join(playerStates) + "|" + ",".join([str(x) for x in self.gameState.deck]) + "|" + ",".join([str(x) for x in discard])
        # state = "|".join([",".join([str(x) for x in playerState.hand]) for playerState in self.playerHands]) + "|" + str(len(self.deck)) + "|" + ",".join([str(x) for x in discard])
        return obs


    @property
    def allowedActions(self):
        return self.gameState.allowedActions

    def getRandomAction(self):
        allowedActions = self.allowedActions
        return allowedActions[random.randint(0, len(allowedActions)-1)]
    
    def render(self, mode='human'):
        # Render the environment to the screen
        print(f"State: {self.state}")

    

class ExplodingKittensGameState():
    def __init__(self, deck, playerHands, currentPlayer, debug=False):
        self.debug = debug
        self.deck = deck
        self.playerHands = playerHands
        self.currentPlayer = currentPlayer
        self.playDirection = "left"
        self.discardPile = []
        # self.lastPlayedCard = None
        self.numAttacks = 0

    @property
    def currentHand(self):
        return self.playerHands[self.currentPlayer].hand
        
    @property
    def allowedActions(self):
        _allowedActions = [Cards.NULL.value]
        for cardIdx, numCardsOfType in enumerate(self.currentHand): 
            # If no cards of this type are the hand, this card acannot be played
            if numCardsOfType == 0:
                continue  

            card = Cards(cardIdx)           
            if card == Cards.DEFUSE:
                # TODO This action signifies playing a defuse card. Disallow for now, but we can potentially
                # have the agent learn that they should never play this card to show that the agent
                # is learning something
                continue
            elif card == Cards.ATTACK:
                # To simplify, disallow playing an attack card the first turn after
                # one has just been played
                if self.lastPlayedCard != Cards.ATTACK:
                    _allowedActions.append(cardIdx)
            elif card == Cards.SHUFFLE:
                # Can always play a shuffle card
                _allowedActions.append(cardIdx)
            elif card == Cards.SKIP:
                # Can always play a skip card
                _allowedActions.append(cardIdx)
            elif card == Cards.FAVOR:
                # Favor card requires at least one opponent to have a card in their hand
                for playerId, player in enumerate(self.playerHands):
                    if playerId != self.currentPlayer and sum(player.hand) > 0:
                        _allowedActions.append(cardIdx)
                        break
            # elif not isCatCard(cardIdx) and numCardsOfType >= 1:
            #     # If there is more than one of a non cat-type card, allow that action
            #     _allowedActions.append(cardIdx)
            elif isCatCard(cardIdx):
                if numCardsOfType >= 2:
                    # Game rules dictate there must be 2 of a kind to play a 'CAT' card
                    for playerId, player in enumerate(self.playerHands):
                        if playerId != self.currentPlayer and sum(player.hand) > 0:
                            _allowedActions.append(cardIdx)
                            break

        return _allowedActions

    @property
    def numPlayers(self):
        return len(self.playerHands)

    @property
    def nextPlayer(self):
        if len(self.deck) == 0:
            # Cycle through players in play direction until player that is in is found
            dir = -1 if self.playDirection == "left" else 1
            currentPlayer = (self.currentPlayer + dir) % self.numPlayers
            while self.playerHands[currentPlayer].isOut:
                currentPlayer = (currentPlayer + dir) % self.numPlayers
            return currentPlayer

        # If attacks count is not zero at the end of the turn, currentPlayer stays the same
        if self.lastPlayedCard != Cards.ATTACK and self.numAttacks > 0:
            self.numAttacks -= 1
            if self.numAttacks > 0:
                return self.currentPlayer

        # Cycle through players in play direction until player that is in is found
        dir = -1 if self.playDirection == "left" else 1
        currentPlayer = (self.currentPlayer + dir) % self.numPlayers
        while self.playerHands[currentPlayer].isOut:
            currentPlayer = (currentPlayer + dir) % self.numPlayers
        return currentPlayer

    @property
    def lastPlayedCard(self):
        return self.discardPile[-1] if self.discardPile else None

    def isValidAction(self, action):
        return action in self.allowedActions

    # def stringify(self):
    #     discard = [0]*10
    #     for card in self.discard:
    #         # print("self.discard[i].value", self.discard[i].value)
    #         discard[card.value] += 1
    #     state = ",".join([str(x) for x in self.currentHand]) + "|" + ",".join([str(x) for x in self.opposingHand]) + "|" + ",".join([str(x) for x in self.deck]) + "|" + ",".join([str(x) for x in discard])
    #     return state

    def stringifyFullStateExceptDeck(self):
        discard = [0]*10
        for card in self.discardPile:
            discard[card.value] += 1
        state = "|".join([",".join([str(x) for x in playerState.hand]) for playerState in self.playerHands]) + "|" + str(len(self.deck)) + "|" + ",".join([str(x) for x in discard])
        return state

    def _goToNextPlayer(self):
        # Cycle through players in play direction until player that is in is found
        dir = -1 if self.playDirection == "left" else 1
        self.currentPlayer = (self.currentPlayer + dir) % self.numPlayers
        while self.playerHands[self.currentPlayer].isOut:
            self.currentPlayer = (self.currentPlayer + dir) % self.numPlayers

    def takeAction(self, action, opponentSelected=None):
        # Make sure the action taken is valid. If not, return the same state and redo the turn.
        if not self.isValidAction(action):
            return False

        # Get the card corresponding to the action
        card = Cards(action)

        if card != Cards.NULL: 
            # Remember the last played card for things like skip, attack, etc.
            # self.lastPlayedCard = card

            # Take the card out of the hand
            self.currentHand[card.value] -= 1
            self.discardPile.append(card)

        # Logic depending on which card was played
        if card == Cards.NULL:
            # Draw a card from the deck
            card = self.deck.pop()
            if card == Cards.EXPLODING_KITTEN:
                if self.debug:
                    print('BOMB WAS DRAWN')
                if self.currentHand[Cards.DEFUSE.value] != 0:
                    # Has a defuse
                    self.currentHand[Cards.DEFUSE.value] -= 1

                    # Insert E.K. into deck randomly
                    if len(self.deck) == 0:
                        self.deck.insert(0, Cards.EXPLODING_KITTEN)
                    else:
                        position = random.randint(0, len(self.deck)-1)
                        self.deck.insert(position, Cards.EXPLODING_KITTEN)
                else:
                    self.playerHands[self.currentPlayer].isOut = True
                    self.currentPlayer = self.nextPlayer
                    if (self.numPlayers - sum([p.isOut for p in self.playerHands])) == 1:
                        # Game is done
                        return True
            else:
                self.currentHand[card.value] += 1

            # If attacks count is not zero at the end of the turn, currentPlayer stays the same
            # if self.numAttacks > 0:
            #     self.numAttacks -= 1
            #     if self.numAttacks > 0:
            #         return False

            # Go to next player
            self.currentPlayer = self.nextPlayer
            # self._goToNextPlayer()
            return False
        
        elif card == Cards.ATTACK:
            # Add 2 attacks counts to the current number of attack counts
            self.numAttacks += 2

            # Go to next player
            self.currentPlayer = self.nextPlayer
            return False

        elif card == Cards.SKIP:
            # If attacks count is not zero at the end of the turn, currentPlayer stays the same
            # if self.numAttacks > 0:
            #     self.numAttacks -= 1
            #     if self.numAttacks > 0:
            #         return False

            # Go to next player
            self.currentPlayer = self.nextPlayer
            return False

        elif card == Cards.SHUFFLE:
            random.shuffle(self.deck)
            return False

        elif card == Cards.FAVOR:
            # If no opponent was selected or selected opponent has no cards, choose opponent at random
            if opponentSelected == None or sum(self.playerHands[opponentSelected].hand) == 0:
                opponents = [i for i in range(self.numPlayers) if i is not self.currentPlayer and sum(self.playerHands[i].hand) > 0]
                opponentSelected = np.random.choice(opponents)
            assert opponentSelected is not self.currentPlayer and opponentSelected in range(self.numPlayers)

            # Get number of cards
            numOpponentCards = sum(self.playerHands[opponentSelected].hand)
            if self.debug:
                probabilities = [n / numOpponentCards for n in self.playerHands[opponentSelected].hand]
                print('Favor probabilities:', probabilities)

            # Take a random card from the selected opponents hand
            chosenCardIndex = np.random.choice(Cards.numCardTypes(), p=[n / numOpponentCards for n in self.playerHands[opponentSelected].hand])
            
            # chosenCard = random.randint(0, sum(self.playerHands[opponentSelected].hand)-1)
            self.currentHand[chosenCardIndex] += 1
            self.playerHands[opponentSelected].hand[chosenCardIndex] -= 1
            return False

        elif isCatCard(card.value):
            # Take 2 cards from hand
            if card != Cards.FAVOR:
                self.currentHand[action] -= 1
                self.discardPile.append(card)

            # If no opponent was selected or selected opponent has no cards, choose opponent at random
            if opponentSelected == None or sum(self.playerHands[opponentSelected].hand) == 0:
                opponents = [i for i in range(self.numPlayers) if i is not self.currentPlayer and sum(self.playerHands[i].hand) > 0]
                opponentSelected = np.random.choice(opponents)
            assert opponentSelected is not self.currentPlayer and opponentSelected in range(self.numPlayers)

            # pdb.set_trace()

            # Get number of cards
            numOpponentCards = sum(self.playerHands[opponentSelected].hand)
            if self.debug:
                probabilities = [n / numOpponentCards for n in self.playerHands[opponentSelected].hand]
                print('Favor probabilities:', probabilities)

            # Take a random card from the selected opponents hand
            chosenCardIndex = np.random.choice(Cards.numCardTypes(), p=[n / numOpponentCards for n in self.playerHands[opponentSelected].hand])
            
            # chosenCard = random.randint(0, sum(self.playerHands[opponentSelected].hand)-1)
            self.currentHand[chosenCardIndex] += 1
            self.playerHands[opponentSelected].hand[chosenCardIndex] -= 1
            return False

if __name__ == "__main__":
    print(Cards.numCardTypes())
    print(len(Cards))