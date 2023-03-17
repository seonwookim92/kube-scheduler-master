from kubernetes import client, config

import os, sys
base_path = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.append(base_path)

from kube_python_scheduler.common.monitor import Monitor
from kube_python_scheduler.common.filter import Filter

class FCFS:
    def __init__(self, cfg=None):
        # Load the Kubernetes configuration
        if cfg is None:
            self.config = config.load_kube_config()
        else:
            self.config = cfg

        # Load the Kubernetes API client
        self.core_api = client.CoreV1Api()
        self.monitor = Monitor(cfg=self.config)
        self.filter = Filter()

    def scoring(self):
        # Check if there are pending pods
        # If there are no pending pods, return None
        # If there are pending pods, get the score of the available nodes

        # Get the pending pods
        pending_pods_name, _ = self.monitor.get_pending_pods()
        FCFS_output = {}

        if len(pending_pods_name) == 0:
            FCFS_output['pod'] = None
            FCFS_output['node_score'] = None
            return FCFS_output
        else:
            # Get the first pending pod (FCFS)
            pod_name = pending_pods_name[0]
            # Get the available nodes
            available_nodes_name = self.filter.get_available_nodes_name(pod_name)
            print(f"available_nodes : {available_nodes_name}")
            # Get the score of the available nodes
            # The more running pods a node has, the lower the score
            FCFS_output['pod'] = pod_name
            node_score = {}
            for node_name in available_nodes_name:
                # Exclude the controlplane node
                if node_name == "controlplane" or node_name == "node-0":
                    continue

                pods = self.core_api.list_pod_for_all_namespaces(field_selector=f"spec.nodeName={node_name}").items
                print(f"# of Pods on node {node_name}: {len(pods)}")
                running_pods = [pod for pod in pods if pod.status.phase == "Running"]
                num_running_pods = len(running_pods)

                node_score[node_name] = 100 - num_running_pods

            FCFS_output['node_score'] = node_score
            
        # Return the node_score dictionary
        return FCFS_output

        