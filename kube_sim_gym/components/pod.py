import os, sys
base_path = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(base_path)

class Pod:
    def __init__(self, pod_spec, node_spec, debug=False):
        self.debug = debug

        self.pod_idx = pod_spec[0]
        self.pod_name = f"stressng-{pod_spec[1]}-{pod_spec[2]}l-{pod_spec[3]}m-{pod_spec[4]}th"

        self.node_cpu_pool = node_spec["cpu_pool"]
        self.node_mem_pool = node_spec["mem_pool"]

        if pod_spec[1] == "cpu":
            cpu_req = int(pod_spec[2]) * 1000
            mem_req = 1000
        elif pod_spec[1] == "vm":
            cpu_req = 1000
            mem_req = int(pod_spec[2]) * 1000

        self.spec = {
            "cpu_req": cpu_req,
            "mem_req": mem_req,
            "cpu_ratio" : round(cpu_req / self.node_cpu_pool, 2),
            "mem_ratio" : round(mem_req / self.node_mem_pool, 2),
            "duration": int(pod_spec[3]),
            "arrival_time": int(pod_spec[4])
        }
        self.status = {
            "phase": None, # Pending, Running, Succeeded, Failed, Unknown
            "node_idx": None,
            "node_name": None,
            "start_time": None,
            "end_time": None,
        }

    def is_expired(self, time):
        if self.status["phase"] == "Running" and self.status["start_time"] + (self.spec["duration"] * 60) < time:
            if self.debug:
                print("(Pod) Pod {} is expired".format(self.pod_name))
            return True

    def deploy(self, node, time):
        if self.debug:
            print("(Pod) Deploy pod {} to node {}".format(self.pod_name, node.node_name))
        self.status["phase"] = "Running"
        self.status["node_idx"] = node.node_idx
        self.status["node_name"] = node.node_name
        self.status["start_time"] = time

    def terminate(self, time):
        is_running = self.status["phase"] == "Running"
        is_end_time_none = self.status["end_time"] is None
        is_duration_over = self.status["start_time"] + self.spec["duration"] < time

        if is_running and is_end_time_none and is_duration_over:
            self.status["phase"] = "Succeeded"
            self.status["end_time"] = time
            return True