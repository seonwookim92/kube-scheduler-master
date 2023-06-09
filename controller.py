import gym
import multiprocessing as mp
import subprocess

import os, sys
base_path = os.path.join(os.path.dirname(__file__))
sys.path.append(base_path)

import kube_real_gym, kube_hr_scheduler, kube_stress_generator
from kube_real_gym.envs.real_kube_env import RealKubeEnv

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
    print("2. Stop stress generator")
    print("3. Start python scheduler")
    print("4. Start RL scheduler")
    print("5. Exit")
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

def get_pid(name):
    output = subprocess.check_output("ps -ef | grep python", shell=True).decode()
    for line in output.split("\n"):
        # TODO This function is not perfect. Just temporary. Need to revisit!!!
        if name in line:
            return int(line.split()[1])

while True:
    # Prompt
    cmd = prompt()
    if cmd == "1":
        # Start stress generator
        p_stress_gen = mp.Process(target=run_stress_gen, args=())
        p_stress_gen.start()
    elif cmd == "2":
        # Stop stress generator
        pid = get_pid("kube")
        if pid:
            os.kill(pid, 9)
            print(f"Stress generator (pid: {pid}) is stopped")
        else:
            print("Stress generator is not running")

    elif cmd == "3":
        # Start python scheduler
        p_python_scheduler = mp.Process(target=run_python_scheduler, args=())
        p_python_scheduler.start()
    elif cmd == "4":
        # TBA
        pass
    elif cmd == "5":
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