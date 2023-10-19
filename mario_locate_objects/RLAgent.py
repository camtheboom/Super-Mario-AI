import gym_super_mario_bros as gym
from nes_py.wrappers import JoypadSpace
from gym_super_mario_bros.actions import SIMPLE_MOVEMENT
from stable_baselines3 import PPO

# Set the seed when creating the environment
env = gym.make('SuperMarioBros-v0', apply_api_compatibility=True, render_mode="human")

# Wrap the environment with JoypadSpace
env = JoypadSpace(env, SIMPLE_MOVEMENT)

model = PPO('CnnPolicy', env, verbose=1, batch_size=64)

model.learn(total_timesteps=1000)

model.save("mario_model")

del model

model = PPO.load("mario_model")

obs = env.reset()

while True:
    action, _ = model.predict(obs)
    state, reward, done, info = env.step(action)
    # obs, reward, terminated, truncated, info = env.step(action)
    env.render()
