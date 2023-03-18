import gym
import multiprocessing as mp

import os, sys
base_path = os.path.join(os.path.dirname(__file__))
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

proc = mp.current_process()

def prompt():
    print("Kubernetes Scheduler Simulator")
    print("================================")
    print("Process ID: ", proc.pid)
    print("================================")
    print("1. Start stress generator")
    print("2. Start python scheduler")
    print("3. Start RL scheduler")
    print("4. Exit")
    print("================================")
    cmd = input("Type in the number what you want to do : ")
    print("================================")
    return cmd

def run_stress_gen():
    exec(open("kube_stress_generator/main.py").read())

def run_python_scheduler():
    exec(open("kube_python_scheduler/main.py").read())

def run_rl():
    # TBA
    # exec(open("kube_gym/main.py").read())
    pass

while True:
    # Prompt
    cmd = prompt()
    if cmd == "1":
        # Start stress generator
        p_stress_gen = mp.Process(target=run_stress_gen, args=())
        p_stress_gen.start()
    elif cmd == "2":
        # Start python scheduler
        p_python_scheduler = mp.Process(target=run_python_scheduler, args=())
        p_python_scheduler.start()
    elif cmd == "3":
        # TBA
        pass
    elif cmd == "4":
        # Purge all kubernetes resources by running kube_stress_generator/purge_jobs.sh
        os.system("bash kube_stress_generator/purge_jobs.sh")
        # Stop all processes
        os.kill(proc.pid, 9)

    






# TODO
# 1. Incorporate stress_gen with the gym environment
# 2. Make main start stress_gen in each loop
# 3. Make agent communicate with gym environment
# 4. calloc to prevent OOM killed?
# 5. Scheduler dynamic catch istead of waiting for 10s?
# 6. Better way for the multiprocessing?

# FURTHER
# 1. Develop reward function
# 2. OOM failure handling