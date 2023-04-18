import os, sys
base_path = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.append(base_path)

import importlib

class SimHrScheduler:
    def __init__(self, env, model_fname='random.py'):
        self.env = env

        self.model_name = model_fname.split('.')[0]
        model_path = os.path.join("kube_hr_scheduler", "strategies", "model", self.model_name).replace("/", ".")
        self.model = importlib.import_module(model_path).Model(self.env)

    def decision(self, env):
        action = self.model.predict(env)
        return action