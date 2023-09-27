from gym_super_mario_bros.actions import SIMPLE_MOVEMENT
import numpy as np
# from keras.models import Sequential      # One layer after the other
# from keras.layers import Dense, Flatten  # Dense layers are fully connected layers, Flatten layers flatten out multidimensional inputs
from collections import deque            # For storing moves 


## A Reinforcement Learning: Deep Q Network  Agent implementation that can play super mario bros
## Goal of this class is to return a action that mario must do.
## Currently do not understand the code for making the neural network so will just create the collection 


# def is_terminal(): # An episode reaches a terminal state if it reaches the end of the level, dies and leads to a game over, or if it gets stuck and stays in same position for more than 2 iterations,
#     pass 

GAMMA = 0.9
EPSILON = 0.7
replay_buffer = deque()

def rLAgent(state, action, reward, next_state, done):
    replay_buffer.append(state, action, next_state, done)
    


# replay_buffer = deque()
# experience = (state, action, reward, next_state, done)

class RLAgent:
    def __init__(self, action_space, state, action, reward, next_state, done):
        self.action_space = action_space
        self.state = state
        self.action = action
        self.reward = reward
        self.next_state = next_state
        self.done = done

    def select_action(self, observation):
        
        # Implement your rule-based logic here based on Super Mario Bros observations
        action = self.rule_based_logic(observation)
        return action

    def reinforcement_learning(self, observation):
        # Define your rules and heuristics for Super Mario Bros here to select an action
        # Example: Move right and jump if an obstacle is in front; otherwise, keep moving right.
        # Example: If a power-up is nearby, move toward it.
        # Example: If Mario is low on health, prioritize avoiding enemies.
        
        # Replace the following line with your logic to select an action
        # Example: action = 0  # Move right
        action = 0  # Placeholder; replace with your logic
        return action

    def update(self, state, action, reward, next_state, done):
        # Rule-based agents typically do not require updates since they do not learn from experience.
        print("Hello World")
        pass

    def save_model(self, path):
        # Rule-based agents do not have a model to save.
        pass

    def is_terminal(self):
        
        pass

RLAgent.update(1,1,1,1,1,1)
x = RLAgent(1)
print(x)