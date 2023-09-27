# import gym_super_mario_bros as gym
# from nes_py.wrappers import JoypadSpace
# from gym_super_mario_bros.actions import SIMPLE_MOVEMENT
# from stable_baselines3 import PPO
# import random

# random.seed(42)

# env = JoypadSpace(env, SIMPLE_MOVEMENT)
# model = PPO('CnnPolicy', env, verbose=1, batch_size=64)

# model.learn(total_timesteps=1000)

# model.save("mario_model")

# del model

# model = PPO.load("mario_model")

# obs = env.reset()

# while True:
#     action, _states = model.predict(obs)

#     env.render()

# Import the game
import gym_super_mario_bros as gym
# Import the Joypad wrapper
from nes_py.wrappers import JoypadSpace
# Import the SIMPLIFIED controls
from gym_super_mario_bros.actions import SIMPLE_MOVEMENT

# Import Frame Stacker Wrapper and GrayScaling Wrapper
from gym.wrappers import GrayScaleObservation
# Import Vectorization Wrappers
from stable_baselines3.common.vec_env import VecFrameStack, DummyVecEnv
# Import Matplotlib to show the impact of frame stacking
from matplotlib import pyplot as plt

# Setup game
env = gym.make('SuperMarioBros-v0', apply_api_compatibility=True, render_mode="human")
env = JoypadSpace(env, SIMPLE_MOVEMENT)

# env = GrayScaleObservation(env, keep_dim=True)
# # 4. Wrap inside the Dummy Environment
# env = DummyVecEnv([lambda: env])
# # 5. Stack the frames
# env = VecFrameStack(env, 4, channels_order='last')

# # state = env.reset()

# state, reward, terminated, truncated, info = env.step([5])

# Create a flag - restart or not
done = True
# Loop through each frame in the game
for step in range(100000): 
    # Start the game to begin with 
    if done: 
        # Start the gamee
        env.reset()
    # Do random actions
    # state, reward, done, info = env.step(env.action_space.sample())
    action = env.action_space.sample()
    state, reward, terminated, truncated, info = env.step(action)    # Show the game on the screen
    done = terminated or truncated

    if done:
       env.reset()
    # env.render()
# Close the game
env.close()



