from kubernetes import client, config

import os, sys
base_path = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_path)

from kube_python_scheduler.common.monitor import Monitor
from kube_python_scheduler.common.filter import Filter
from kube_python_scheduler.stratigies.fcfs.strategy import FCFS
from kube_python_scheduler.scheduler.scheduler import Scheduler

from time import sleep

mnt = Monitor()
flt = Filter()
fcfs = FCFS()
sched = Scheduler(strategy=fcfs)

while True:
    pod, node = sched.decision()
    if pod is not None:
        sched.scheduling(pod, node)
    sleep(10)