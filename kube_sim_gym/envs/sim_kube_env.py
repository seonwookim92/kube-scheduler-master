import gym
import numpy as np
import importlib
import matplotlib.pyplot as plt

import os, sys
base_path = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(base_path)

from kube_sim_gym.components.cluster import Cluster
from kube_sim_gym.utils.sim_stress_gen import SimStressGen

# Simulate kubernetes node and pods with cpu, memory resources
class SimKubeEnv(gym.Env):
    def __init__(self, strategy_file="default.py", scenario_file="scenario-5l-10m-1000p-60m.csv", n_node=5, cpu_pool=50000, mem_pool=50000, debug=None):
        # self.debug = True if debug == None else debug
        self.debug = True

        # Strategy
        self.strategy = strategy_file

        self.stress_gen = SimStressGen(scenario_file, self.debug)
        
        self.n_node = n_node
        self.cpu_pool = cpu_pool
        self.mem_pool = mem_pool

        self.cluster = Cluster(n_node, cpu_pool, mem_pool, self.debug)
        self.scheduler_type = 'rl'
        
        self.time = 0
        
        self.reward = 0
        self.done = False
        self.observation_space = gym.spaces.Box(low=0, high=100, shape=(n_node * 2 + 2,), dtype=np.float32)
        self.action_space = gym.spaces.Discrete(n_node + 1)

        self.action_map = {'0': 'standby'}
        for i in range(n_node):
            self.action_map[str(i + 1)] = 'node-{}'.format(i+1)

        self.info = {
            'last_pod' : None,
            'is_scheduled' : None
        }

    def get_reward(self, cluster, action, is_scheduled, time):

        strategy_module_path = os.path.join(f"kube_{self.scheduler_type}_scheduler", "strategies", "reward", os.path.splitext(self.strategy)[0]).replace('/', '.')
        strategy = importlib.import_module(strategy_module_path)
        reward = strategy.get_reward(cluster, action, is_scheduled, time, self.debug)

        return reward

    def get_state(self):
        node_state = []
        for node in self.cluster.nodes:
            node_cpu_ratio = node.get_node_rsrc_ratio()[0]
            node_mem_ratio = node.get_node_rsrc_ratio()[1]
            node_state += [node_cpu_ratio, node_mem_ratio]

        if  self.cluster.pending_pods:
            pending_pod = self.cluster.pending_pods[0]
            pending_pod_state = [pending_pod.spec["cpu_ratio"], pending_pod.spec["mem_ratio"]]
        else:
            pending_pod_state = [0, 0]

        if self.debug:
            print(f"(SimKubeEnv) Pending Pod State: {pending_pod_state}")
            print(f"(SimKubeEnv) Node state: {node_state}")

        state = node_state + pending_pod_state

        return np.array(state, dtype=np.float32)
    
    def get_done(self):
        len_scenario = len(self.stress_gen.scenario)
        len_scheduled = len(self.cluster.terminated_pods + self.cluster.running_pods)
        if len_scenario == len_scheduled:
            self.done = True
        else:
            self.done = False
        return self.done

        


    def step(self, action):
        self.time += 1
        is_scheduled = None
        
        new_pod_spec = self.stress_gen.create_pod(self.time)
        node_spec = self.cluster.nodes[0].spec
        if new_pod_spec:
            self.cluster.queue_pod(new_pod_spec, node_spec)

        # Update cluster
        self.cluster.update(self.time)

        # Initialize info
        self.info = {
            'last_pod' : None,
            'is_scheduled' : None
        }


        # Do action
        if self.cluster.pending_pods:
            deploy_node = self.cluster.get_node(self.action_map[str(action)])
            if deploy_node:
                if self.debug:
                    print(f"(SimKubeEnv) Deploying pod to node {deploy_node.node_name}")
                pending_pod = self.cluster.pending_pods[0]
                is_scheduled = self.cluster.deploy_pod(pending_pod, deploy_node, self.time)
                if is_scheduled:
                    if self.debug:
                        print(f"(SimKubeEnv) Pod deployed to node {deploy_node.node_name}")
                else:
                    if self.debug:
                        print(f"(SimKubeEnv) Failed to deploy pod to node {deploy_node.node_name}")
                # for pod in self.cluster.pending_pods:
                #     if self.cluster.deploy_pod(pod, deploy_node, self.time):
                #         break
                self.info = {
                    'last_pod' : pending_pod,
                    'is_scheduled' : is_scheduled
                }
            else:
                if self.debug:
                    print(f"(SimKubeEnv) Standby")
        else:
            if self.debug:
                print(f"(SimKubeEnv) No pending pods")

        # Get reward
        self.reward = self.get_reward(self.cluster, action, is_scheduled, self.time)

        # Get state
        state = self.get_state()

        # Get done
        self.done = self.get_done()

        return state, self.reward, self.done, self.info

    def reset(self):
        self.time = 0
        self.cluster.reset()
        self.stress_gen.reset()

        return self.get_state()