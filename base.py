from nes_py.wrappers import JoypadSpace 
import gym_super_mario_bros
from gym_super_mario_bros.actions import SIMPLE_MOVEMENT 
import gym

env = gym.make('SuperMarioBros-v0') 
env = JoypadSpace(env, SIMPLE_MOVEMENT)
done = True 
env.reset() 
for step in range(5000):
    action = env.action_space.sample() 
    state, reward, done, info = env.step(action)
    if done: 
        state=env.reset() 
env.close()