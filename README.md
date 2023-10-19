# Super-Mario-AI

PPO Agent Requirements:

Dependency Versions:
- Stable Baselines3 version 1.3.0
- Gym version 0.17.3
- Python version 3.8

To Run Agent:
- If a training file is already supplied then within the code, modify the file location inside the PPO.load function on line 53 and comment out the training segment of code.
- If no training file is supplied then leave the training segment uncommented and modify the amount of timesteps you want to train the model for, and it will save its progress to a folder called 'train'.
- Run the code with 'python ./PPOAgent.py' making sure youre in the virtual environment with all the installations.
