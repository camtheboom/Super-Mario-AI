from nes_py.wrappers import JoypadSpace
import gym_super_mario_bros
from gym_super_mario_bros.actions import SIMPLE_MOVEMENT
import gym

# Import Frame Stacker Wrapper and GrayScaling Wrapper
from gym.wrappers import GrayScaleObservation
# Import Vectorization Wrappers
from stable_baselines3.common.vec_env import VecFrameStack, DummyVecEnv
# Import Matplotlib to show the impact of frame stacking
from matplotlib import pyplot as plt

# Import PPO for algos
from stable_baselines3 import PPO


env = gym.make('SuperMarioBros-v0', apply_api_compatibility=True, render_mode="human")
env = JoypadSpace(env, SIMPLE_MOVEMENT)

# env = GrayScaleObservation(env, keep_dim=True)
# # 4. Wrap inside the Dummy Environment
# env = DummyVecEnv([lambda: env])
# # 5. Stack the frames
# env = VecFrameStack(env, 4, channels_order='last')

done = True
# state = env.reset()
# action = env.action_space.sample()
# state, reward, terminated, truncated, info = env.step(action)

model = PPO('CnnPolicy', env, verbose=1, learning_rate=0.000001, n_steps=512) 
model.learn(total_timesteps=10)
model.save('thisisatestmodel')

del model
model = PPO.load('thisisatestmodel', env=env)

state = env.reset()

while True:
    action, _ = model.predict(state)
    state, reward, terminated, truncated, info = env.step(action)
    env.render()

# plt.figure(figsize=(20,16))
# for idx in range(state.shape[0]):
#     plt.subplot(1, state.shape[0], idx+1)
#     plt.imshow(state[0])
# plt.show()

# for step in range(5000):
#     action = env.action_space.sample()
#     state, reward, terminated, truncated, info = env.step(action)
#     done = terminated or truncated

#     if done:
#        env.reset()

# env.close()