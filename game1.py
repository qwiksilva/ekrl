import numpy as np
import logging
import random
from enum import Enum

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
    NULL = 10
    EXPLODING_KITTEN = 15

class ExplodingKittensSingleRandom:
    def __init__(self):
        self.game = OnePlayerGame()
        self.actionSpace = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=np.int)
        self.action_size = len(self.actionSpace)
        self.name = 'exploding_kittens'

    def reset(self):
        gameState = self.game.reset()
        return (gameState.stringify(), 0, False, None)

    def step(self, action):
        (next_state, reward, done, invalidAction) = self.game.step(action)
        return (next_state.stringify(), reward, done, None)

class OnePlayerGame:
    def __init__(self, debug=False):
        self.game = Game()
        self.debug = debug

    def reset(self):
        return self.game.reset()

    def _randomAction(self):
        allowedAction = self.game.gameState._allowedActions()
        action = allowedAction[random.randint(0, len(allowedAction)-1)]
        return action

    def step(self, action):
        if self.debug:
            print("CURRENT PLAYER:", self.game.gameState.currentPlayer)
        (next_state, value, done, invalidAction) = self.game.step(action)
        # if invalidAction:
        #     return (next_state, value, done, invalidAction)

        if done:
            reward = -1
            if next_state.currentPlayer == -1:
                next_state = GameState(next_state.deck, next_state.opposingHand, next_state.currentHand, next_state.discard, next_state.lastPlayedCard, 1)
            return ((next_state, reward, done, invalidAction))

        if next_state.currentPlayer == 1:
            reward = 0
            return ((next_state, reward, done, invalidAction))

        if self.debug:
            print("NEW PLAYER:", next_state.currentPlayer)
        while next_state.currentPlayer == -1:
            opponentAction = self._randomAction()
            (next_state, value, done, invalidAction) = self.game.step(opponentAction)
            if done:
                reward = 1
                # print("ORIGNAL END STATE:", next_state.stringify())
                # print("ORIGNAL currentPlayer:", next_state.currentPlayer)
                if next_state.currentPlayer == -1:
                    next_state = GameState(next_state.deck, next_state.opposingHand, next_state.currentHand, next_state.discard, next_state.lastPlayedCard, 1)
                return ((next_state, reward, done, invalidAction))
            if next_state.currentPlayer == 1:
                return ((next_state, value, done, invalidAction))
        

class Game:
    def __init__(self, debug=False):
        self.debug = debug
        self.num_players = 2
        self.reset()

    def _initGameState(self):
        # Put all card in deck except E.K. and 2 defuse
        deck = [Cards.DEFUSE, Cards.DEFUSE,
                Cards.ATTACK, Cards.ATTACK, Cards.ATTACK, Cards.ATTACK,
                Cards.SKIP, Cards.SKIP, Cards.SKIP, Cards.SKIP,
                Cards.FAVOR, Cards.FAVOR, Cards.FAVOR, Cards.FAVOR,
                Cards.SHUFFLE, Cards.SHUFFLE, Cards.SHUFFLE, Cards.SHUFFLE,
                Cards.CAT1, Cards.CAT1, Cards.CAT1, Cards.CAT1,
                Cards.CAT2, Cards.CAT2, Cards.CAT2, Cards.CAT2,
                Cards.CAT3, Cards.CAT3, Cards.CAT3, Cards.CAT3,
                Cards.CAT4, Cards.CAT4, Cards.CAT4, Cards.CAT4,
                Cards.CAT5, Cards.CAT5, Cards.CAT5, Cards.CAT5]

        deck = [Cards.DEFUSE,
                Cards.ATTACK,
                Cards.SKIP,
                Cards.FAVOR,
                Cards.SHUFFLE,
                Cards.CAT1, Cards.CAT1,
                Cards.CAT2, Cards.CAT2,
                Cards.CAT3, Cards.CAT3,
                Cards.CAT4, Cards.CAT4]

        # Shuffle deck
        random.shuffle(deck)

        # Deal hands (plus 1 defuse)
        HAND_SIZE = 3

        hand1 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for _ in range(HAND_SIZE):
            card = deck.pop()
            hand1[card.value] += 1
        hand1[Cards.DEFUSE.value] = 1

        hand2 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        for _ in range(HAND_SIZE):
            card = deck.pop()
            hand2[card.value] += 1
        hand2[Cards.DEFUSE.value] = 1

        # Insert E.K. into deck randomly
        position = random.randint(0, len(deck)-1)
        deck.insert(position, Cards.EXPLODING_KITTEN)
        return GameState(deck, hand1, hand2, [], None, self.currentPlayer)

    def reset(self):
        # Current player is an int, 1 and -1
        self.currentPlayer = 1
        self.gameState = self._initGameState()
        # Action for each type of card in the game
        self.actionSpace = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=np.int)
        self.action_size = len(self.actionSpace)
        self.name = 'exploding_kittens'
        return self.gameState

    def step(self, action):
        next_state, value, done, invalidAction, next_player = self.gameState.takeAction(
            action)  # Added a penalize player to penalize the right player
        if invalidAction:
            if self.debug:
                print("INVALID ACTION, TRY AGAIN")
        self.gameState = next_state
        self.currentPlayer = next_player
        info = None
        # Sends out next_state, penalty, whether game is done and which player to penalize
        return ((next_state, value, done, invalidAction))

    def identities(self, state, actionValues):  # ???? Ryan please proof read
        identities = [(state, actionValues)]
        # opposingHand = state.currentHand
        # currentHand = state.opposingHand
        # stateopp = GameState(state.deck, currentHand, opposingHand,
        #                      state.discard, state.lastPlayedCard, state.currentPlayer)
        # identities.append((stateopp, actionValues))
        return identities


class GameState():
    def __init__(self, deck, currentHand, opposingHand, discard, lastPlayedCard, currentPlayer, debug=False):
        self.debug = debug
        self.deck = deck
        self.currentHand = currentHand
        self.opposingHand = opposingHand
        self.discard = discard
        self.numTypes = 10
        self.lastPlayedCard = lastPlayedCard
        self.currentPlayer = currentPlayer
        self.playerTurn = currentPlayer
        self.noDrawThisTurn = False
        self.numAttacks = 0
        self.isEndGame = False
        self.binary = np.array(self._binary())
        self.id = self._convertStateToId()
        self.allowedActions = self._allowedActions()
        self.value = self._getValue()
        self.score = self._getScore()

    def _allowedActions(self):
        allowedActions = [10]
        for cardType, numCards in enumerate(self.currentHand):              
            if cardType == 0:
                # This action signifies playing a defuse card. Disallow for now, but we can potentially
                # have the agent learn that they should never play this card to show that the agent
                # is learning something
                continue
            elif self.lastPlayedCard == Cards.ATTACK and cardType == 1:
                # To simplify, disallow playing an attack card the first turn after
                # one has just been played
                continue
            elif cardType < 5 and numCards >= 1:  # ????
                # If there is more than one of a non cat-type card, allow that action
                allowedActions.append(cardType)
            elif cardType >= 5 and numCards >= 2:
                # Game rules dictate there must be 2 of a kind to play a 'CAT' card
                allowedActions.append(cardType)
        return allowedActions

    #  binarizes the state observed according to the current player
    def _binary(self):
        lastPlayedValue = self.lastPlayedCard.value if self.lastPlayedCard != None else -1
        state = self.currentHand.copy()
        state.append(lastPlayedValue)
        state.append(len(self.deck))
        return state

    def stringify(self):
        discard = [0]*10
        for card in self.discard:
            # print("self.discard[i].value", self.discard[i].value)
            discard[card.value] += 1
        state = ",".join([str(x) for x in self.currentHand]) + "|" + ",".join([str(x) for x in self.opposingHand]) + "|" + ",".join([str(x) for x in self.deck]) + "|" + ",".join([str(x) for x in discard])
        return state

    def stringify1(self):
        discard = [0]*10
        for i in self.discard:
            discard[self.discard[i].value] += 1
        state = ",".join([str(x) for x in self.currentHand]) + "|" + len(self.opposingHand) + "|" + len(self.deck) + "|" + ",".join([str(x) for x in discard])
        return state


    # End the turn by drawing a card. Don't draw if noDrawThisTurn (i.e. an attack or skip was played)
    # Returns whether the game ended due to an exploding kitten or not
    def _endTurn(self, newDeck, newCurrentHand, noDrawThisTurn):
        if noDrawThisTurn:
            return False, newDeck, newCurrentHand
        card = newDeck.pop()
        if card == Cards.EXPLODING_KITTEN:
            # if self.debug:
            # print('BOMB WAS DRAWN')
            if newCurrentHand[Cards.DEFUSE.value] != 0:
                # Has a defuse
                newCurrentHand[Cards.DEFUSE.value] -= 1
                # Insert E.K. into deck randomly
                if len(newDeck) == 0:
                    newDeck.insert(0, Cards.EXPLODING_KITTEN)
                else:
                    position = random.randint(0, len(newDeck)-1)
                    newDeck.insert(position, Cards.EXPLODING_KITTEN)
            else:
                # EndGame
                return True, newDeck, newCurrentHand
        else:
            newCurrentHand[card.value] += 1
        return False, newDeck, newCurrentHand

    # def _convertStateToId(self):
    #     state = self._binary()
    #     done = 1 if self.isEndGame else 0
    #     state.append(done)

    #     id = ''.join(map(str, state))

    #     return id

    def _convertStateToId(self):
        state = self.deck.copy()
        state.append(self.discard.copy())
        state.append(self.currentHand.copy())
        state.append(self.opposingHand.copy())

        id = ''.join(map(str, state))

        return id

    def _getValue(self):
        # This is the value of the state for the current player
        # i.e. if the previous player played a winning move, you lose
        if self.isEndGame:
            return (-1, -1, 1)
        return (0, 0, 0)

    def _getScore(self):
        tmp = self._getValue()
        return (tmp[1], tmp[2])

    def takeAction(self, action):
        # make sure the action taken is valid. If not, return the same state and redo the turn.
        self.allowedActions = self._allowedActions()
        if action not in self.allowedActions:
            return (self, self.value, self.isEndGame, True, self.currentPlayer)

        card = Cards(action)

        # Due to the way the MCTS algorithm is written, a state needs to be static
        # So only update newState, not the current state by making a copy of the current state
        newDeck = self.deck.copy()
        newDiscard = self.discard.copy()
        newCurrentHand = self.currentHand.copy()
        newOpposingHand = self.opposingHand.copy()

        # Take the card out of the hand
        if card != Cards.NULL:
            newCurrentHand[action] -= 1
            newDiscard.append(card)

        noDrawThisTurn = False
        if card == Cards.ATTACK:
            noDrawThisTurn = True
        elif card == Cards.SKIP:
            noDrawThisTurn = True
        elif card == Cards.SHUFFLE:
            random.shuffle(newDeck)
        elif (card == Cards.FAVOR) or (card == Cards.CAT1) or (card == Cards.CAT2) or (card == Cards.CAT3) or (card == Cards.CAT4) or (card == Cards.CAT5):

            # Take 2 cards from hand if a cat card was played
            if card != Cards.FAVOR:
                newCurrentHand[action] -= 1
                newDiscard.append(card)

            validActions = []
            for cardType, numCards in enumerate(newOpposingHand):
                if numCards > 0:
                    validActions.append(cardType)

            # If there are no cards in the opponent's hand, this action does nothing
            if validActions:
                action = random.randint(0, len(validActions)-1)
                chosenCard = validActions[action]

                newCurrentHand[chosenCard] += 1
                newOpposingHand[chosenCard] -= 1

        # Done taking actions, end turn by drawing a card and checking if the game ends
        isEndGame, newDeck, newCurrentHand = self._endTurn(
            newDeck, newCurrentHand, noDrawThisTurn)

        if self.lastPlayedCard == Cards.ATTACK:
            # Set the next players turn equal to the current players turn
            nextPlayer = self.currentPlayer
        else:
            nextPlayer = -self.currentPlayer

        if self.lastPlayedCard == Cards.ATTACK:
            # If the last card played was an attack, the next player is the same as the current player
            # Otherwise the state reverses
            nextPlayer = self.currentPlayer
            newState = GameState(newDeck, newCurrentHand,
                                 newOpposingHand, newDiscard, card, nextPlayer)
        else:
            nextPlayer = -self.currentPlayer
            newState = GameState(newDeck, newOpposingHand,
                                 newCurrentHand, newDiscard, card, nextPlayer)

        # # ???? Shouldn't the state reverse based on whether an attack card was played last?
        # if self.currentPlayer == 1:
        #     # The game states reverse every time
        #     newState = GameState(newDeck, newCurrentHand,
        #                          newOpposingHand, newDiscard, card, nextPlayer)
        # else:
        #     newState = GameState(newDeck, newOpposingHand,
        #                          newCurrentHand, newDiscard, card, nextPlayer)
        value = 0
        done = 0
        newState.isEndGame = isEndGame
        if newState.isEndGame == True:
            value = -1
            done = 1
        return (newState, value, done, False, nextPlayer)

    def T(self, action, newState):
        # state: [currentHand, lastPlayedCard, cardsInDeck]
        # newState: [opposingHand, card, cardsInDeck-1]
        card = Cards(action)
        if card != Cards.NULL:
            cardDrawn = self.deck[-1]
            count = self.deck.count(cardDrawn)
            transition_prob = float(count) / len(self.deck)
        else:
            transition_prob = 1.0

        # transition_probability = 1.0 / NUM_CARDS
        return transition_prob


'''

    def render(self, logger):
        for r in range(6):
            logger.info([self.pieces[str(x)] for x in self.board[7*r : (7*r + 7)]])
        logger.info('--------------')
'''
