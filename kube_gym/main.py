import gym

import os, sys
base_path = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_path)

import kube_gym, kube_python_scheduler, kube_stress_generator
from kube_gym.envs.real_kube_env import RealKubeEnv

env = gym.make('RealKubeEnv-v0')
envv = RealKubeEnv()

action_map = {
    0: "standby",
    1: "node-1",
    2: "node-2",
    3: "node-3",
    4: "node-4",
    5: "node-5",
}

while 