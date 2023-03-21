import gym
import numpy as np

import os, sys
base_path = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_path)

from kube_sim_gym.components.cluster import Cluster
from kube_sim_gym.sim_stress_gen import SimStressGen

# Simulate kubernetes node and pods with cpu, memory resources
class KubeSimEnv(gym.Env):
    def __init__(self, scenario_file="scenario-2023-02-27.csv", n_node=6, cpu_pool=20000, mem_pool=124000, debug=None):
        # self.debug = True if debug == None else debug
        self.debug = False

        self.stress_gen = SimStressGen(scenario_file, self.debug)
        
        self.n_node = n_node
        self.cpu_pool = cpu_pool
        self.mem_pool = mem_pool

        self.cluster = Cluster(n_node, cpu_pool, mem_pool, self.debug)
        
        self.time = 0
        
        self.reward = 0
        self.done = False
        self.observation_space = gym.spaces.Box(low=0, high=100, shape=(n_node * 3,), dtype=np.float32)
        self.action_space = gym.spaces.Discrete(n_node + 1)

        self.action_map = {'0': 'standby'}
        for i in range(n_node):
            self.action_map[str(i + 1)] = 'node-{}'.format(i+1)

    def get_reward(self):
        util = {}
        for node in self.cluster.nodes:
            cpu_util, mem_util = node.get_node_rsrc_util()
            util[node.node_name] = {
                "cpu": cpu_util,
                "mem": mem_util
            }

        # AvgUtil = mean of cpu and mem utilization of all node
        avg_cpu = round(np.mean([util[node]["cpu"] for node in util]), 2)
        avg_mem = round(np.mean([util[node]["mem"] for node in util]), 2)
        avg_util = round((avg_cpu + avg_mem) / 2, 2)
        if self.debug:
            print(f"(KubeSimEnv) Avg CPU util: {avg_cpu}")
            print(f"(KubeSimEnv) Avg Mem util: {avg_mem}")
            print(f"(KubeSimEnv) Avg Util: {avg_util}")

        # ImBalance = summation of standard deviation of each resource in all nodes
        std_cpu = round(np.std([util[node]["cpu"] for node in util]), 2)
        std_mem = round(np.std([util[node]["mem"] for node in util]), 2)
        imbalance = round(std_cpu + std_mem, 2)
        if self.debug:
            print(f"(KubeSimEnv) Std CPU util: {std_cpu}")
            print(f"(KubeSimEnv) Std Mem util: {std_mem}")
            print(f"(KubeSimEnv) Imbalance: {imbalance}")

        # Reward = a*AvgUtil - b*ImBalance
        a = 10
        b = 1
        reward = round(a * avg_util - b * imbalance, 2)
        if self.debug:
            print(f"(KubeSimEnv) Reward: {reward}")

        return reward

    def get_state(self):
        node_state = []
        for node in self.cluster.nodes:
            node_cpu_util = node.get_node_rsrc_util()[0]
            node_mem_util = node.get_node_rsrc_util()[1]
            node_state += [node_cpu_util, node_mem_util]

        if  self.cluster.pending_pods:
            pending_pod = self.cluster.pending_pods[0]
            pending_pod_state = [pending_pod.spec["cpu_req"], pending_pod.spec["mem_req"]]
        else:
            pending_pod_state = [0, 0]

        if self.debug:
            print(f"(KubeSimEnv) Pending Pod State: {pending_pod_state}")
            print(f"(KubeSimEnv) Node state: {node_state}")

        state = (node_state, pending_pod_state)

        return state
    
    def get_done(self):
        is_all_scheduled = len(np.unique([pod[-1] for pod in self.stress_gen.scenario])) == 1
        if self.time >= int(self.stress_gen.scenario[-1][-3]) and is_all_scheduled:
            self.done = True
        else:
            self.done = False

        return self.done

        


    def step(self, action):
        self.time += 1
        
        new_pod_spec = self.stress_gen.create_pod(self.time)
        if new_pod_spec:
            self.cluster.queue_pod(new_pod_spec)

        # Update cluster
        self.cluster.update(self.time)

        # Do action
        if self.cluster.pending_pods:
            deploy_node = self.cluster.get_node(self.action_map[str(action)])
            if deploy_node:
                if self.debug:
                    print(f"(KubeSimEnv) Deploying pod to node {deploy_node.node_name}")
                pending_pod = self.cluster.pending_pods[0]
                if self.cluster.deploy_pod(pending_pod, deploy_node, self.time):
                    print(f"(KubeSimEnv) Pod deployed to node {deploy_node.node_name}")
                else:
                    print(f"(KubeSimEnv) Failed to deploy pod to node {deploy_node.node_name}")
                # for pod in self.cluster.pending_pods:
                #     if self.cluster.deploy_pod(pod, deploy_node, self.time):
                #         break
            else:
                if self.debug:
                    print(f"(KubeSimEnv) Standby")
        else:
            if self.debug:
                print(f"(KubeSimEnv) No pending pods")




    def reset(self):
        self.time = 0
        self.cluster.reset()
        self.stress_gen.reset()

        return self.get_state()





