from kubernetes import client, config

import os, sys
base_path = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_path)

from kube_stress_generator.stress_gen import StressGen

stress_gen = StressGen(silent=True)
stress_gen.start()