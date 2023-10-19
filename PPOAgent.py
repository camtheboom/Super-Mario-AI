import gym_super_mario_bros 
from nes_py.wrappers import JoypadSpace
from gym_super_mario_bros.actions import SIMPLE_MOVEMENT
from gym.wrappers import GrayScaleObservation
from stable_baselines3.common.vec_env import VecFrameStack, DummyVecEnv
from matplotlib import pyplot as plt
import gym
import os 
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback

## This class is used to save the model after every N steps and also log the training process, making sure progress isnt lost.
class TrainAndLoggingCallback(BaseCallback):

    def __init__(self, check_freq, save_path, verbose=1):
        super(TrainAndLoggingCallback, self).__init__(verbose)
        self.check_freq = check_freq
        self.save_path = save_path

    def _init_callback(self):
        if self.save_path is not None:
            os.makedirs(self.save_path, exist_ok=True)

    def _on_step(self):
        if self.n_calls % self.check_freq == 0:
            model_path = os.path.join(self.save_path, 'best_model_{}'.format(self.n_calls))
            self.model.save(model_path)

        return True

## The following segment of code is for preprocessing the environment by stacking frames and grayscaling them making it easier for the model to learn

env = gym.make('SuperMarioBros-v0')
env = JoypadSpace(env, SIMPLE_MOVEMENT)
env = GrayScaleObservation(env, keep_dim=True)
env = DummyVecEnv([lambda: env])
env = VecFrameStack(env, 4, channels_order='last')

CHECKPOINT_DIR = './train/'
LOG_DIR = './logs/'

callback = TrainAndLoggingCallback(check_freq=10000, save_path=CHECKPOINT_DIR)

## The following segment of code is for training the model from scratch over given amount of timesteps

model = PPO('CnnPolicy', env, verbose=1, tensorboard_log=LOG_DIR, learning_rate=0.00001, 
            n_steps=512) 

model.learn(total_timesteps=100000, callback=callback)
model.save('mario') 

## The following segment of code loads a pretrained model and runs it. To see it in action, comment the training code.
model = PPO.load('./train/best_model_100000')
state = env.reset()

while True: 
    action, _ = model.predict(state)
    state, reward, done, info = env.step(action)    
    env.render() 
