from collections import defaultdict
import random
import pickle
from datetime import date

import keras



def def_value():
    return defaultdict(0.0)

class Experience:
    def __init__(self, s, a, r) -> None:
        self.s = s
        self.a = a
        self.r = r

class SARSALambda:
    def __init__(self, g, Q=None, traces=None) -> None:
        self.g = g
        self.action_space = range(g.action_size)
        self.observation_space = 100
        self.gamma = 0.01
        self.Q = defaultdict(lambda: defaultdict(int)) if Q is None else Q
        self.traces = defaultdict(lambda: defaultdict(int)) if traces is None else traces
        self.visits =  defaultdict(lambda: defaultdict(int))
        self.learning_rate = 0.2
        self.trace_decay_rate = 0.98
        self.last_experience = None
        self.espilon = 0.9

        self.hidden_space = 256

        self.model = self.model()

    def model(self):
        model = keras.Sequential()
        model.add(keras.Dense(self.hidden_space, input_shape=(self.observation_space,), activation='relu'))
        model.add(keras.Dense(self.hidden_space, activation='relu'))
        model.add(keras.Dense(self.action_space, activation='sigmoid'))
        model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

    def update(self, s, a, r):
        if self.last_experience != None:
            s1 = self.last_experience.s
            a1 = self.last_experience.a
            r1 = self.last_experience.r
            self.traces[s1][a1] += 1
            self.visits[s1][a1] += 1
            td_update = r1 + self.gamma * self.Q[s][a] - self.Q[s1][a1]
            for _s in self.traces:
                for _a in self.traces[_s]:
                    self.Q[_s][_a] += self.learning_rate * td_update * self.traces[_s][_a]
                    self.traces[_s][_a] *= self.gamma * self.trace_decay_rate
        self.last_experience = Experience(s, a, r)

    def greedy_action(self, s):
        if len(self.Q[s]) == 0:
            return self.g.getRandomAction()
            
        allowedActions = self.g.allowedActions
        actions = [(v, a) for a, v in self.Q[s].items()]
        actions.sort(reverse=True)
        for (v, a) in actions:
            if a in allowedActions:
                return a
        else:
            return self.g.getRandomAction()

    def epsilon_greedy_action(self, s):
        self.espilon *= 0.999999
        if len(self.Q[s]) == 0 or random.uniform(0, 1) < self.espilon:
            return self.g.getRandomAction()
        else:
            return self.greedy_action(s)

    def save(self, savefile=None):
        save_obj = {
            "Q": dict(self.Q),
            "traces": dict(self.traces),
            "visits": dict(self.visits)
        }

        if savefile == None:
            today = date.today()
            d = today.strftime("%b-%d-%Y")
            savefile = 'sarsaLambda-{}'.format(d)
        with open(savefile, 'wb') as f:
            pickle.dump(save_obj, f)
            # pickle.dump(self.espilon, f)

    def load(self, loadFile) -> None:
        with open(loadFile, 'rb') as f:
            save_obj = pickle.load(f)
            self.Q = defaultdict(lambda: defaultdict(int), save_obj["Q"])
            self.traces = defaultdict(lambda: defaultdict(int), save_obj["traces"])
            self.visits = defaultdict(lambda: defaultdict(int), save_obj["visits"])


class SARSA:
    def __init__(self, g, Q=None, traces=None) -> None:
        self.g = g
        self.action_space = range(g.action_size)
        self.gamma = 0.01
        self.Q = defaultdict(lambda: defaultdict(int)) if Q is None else Q
        self.traces = defaultdict(lambda: defaultdict(int)) if traces is None else traces
        self.visits = defaultdict(lambda: defaultdict(int))
        self.learning_rate = 0.2
        self.trace_decay_rate = 0.98
        self.last_experience = None
        self.espilon = 0.9

    def update(self, s, a, r):
        if self.last_experience != None:
            s1 = self.last_experience.s
            a1 = self.last_experience.a
            r1 = self.last_experience.r
            self.Q[s1][a1] += r1 + self.learning_rate * (r1 + self.gamma * self.Q[s][a] - self.Q[s1][a1])
            self.visits[s1][a1] += 1
        self.last_experience = Experience(s, a, r)

    def greedy_action(self, s):
        if len(self.Q[s]) == 0:
            return self.g.getRandomAction()
            
        allowedActions = self.g.allowedActions
        actions = [(v, a) for a, v in self.Q[s].items()]
        actions.sort(reverse=True)
        for (v, a) in actions:
            if a in allowedActions:
                return a
        else:
            return self.g.getRandomAction()

    def epsilon_greedy_action(self, s):
        self.espilon *= 0.999999
        if len(self.Q[s]) == 0 or random.uniform(0, 1) < self.espilon:
            return self.g.getRandomAction()
        else:
            return self.greedy_action(s)

    def save(self, savefile=None):
        save_obj = {
            "Q": dict(self.Q),
            "traces": dict(self.traces),
            "visits": dict(self.visits)
        }

        if savefile == None:
            today = date.today()
            d = today.strftime("%b-%d-%Y")
            savefile = 'sarsaLambda-{}'.format(d)
        with open(savefile, 'wb') as f:
            pickle.dump(save_obj, f)
            # pickle.dump(self.espilon, f)

    def load(self, loadFile) -> None:
        with open(loadFile, 'rb') as f:
            save_obj = pickle.load(f)
            self.Q = defaultdict(lambda: defaultdict(int), save_obj["Q"])
            self.traces = defaultdict(lambda: defaultdict(int), save_obj["traces"])
            self.visits =  defaultdict(lambda: defaultdict(int), save_obj["visits"])