import time
from kubernetes import client, config

import os, sys
base_path = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(base_path)

from kube_stress_generator.job_gen import JobGenerator
from kube_gym.utils import monitor

class StressGen:
    def __init__(self, scenario_file="scenario-2023-02-27.csv"):
        self.scenario_file = scenario_file
        self.config = config.load_kube_config()
        self.batch_api = client.BatchV1Api()
        self.scenario = self.load_scenario(scenario_file)
        self.mnt = monitor.Monitor()

    def load_scenario(self, scenario_file):
        # Load scenario
        scenario_path = "kube_stress_generator/scenarios/" + scenario_file
        scenario = []
        with open(scenario_path, "r") as f:
            lines = f.readlines()
            for line in lines:
                scenario.append(line.strip().split(","))
        return scenario

    def run_stress_gen(self):
        scenario_start_time = time.time()

        # While running this program, checking how many minutes have passed since the start of the scenario
        idx = 0
        while idx < len(self.scenario):
            # Print the current minute from the start of the scenario
            current_elpased_time = time.time() - scenario_start_time
            current_elpased_minute = int((time.time() - scenario_start_time) / 60)
            current_elpased_second = int((time.time() - scenario_start_time) % 60)
            print("Current elpased time: " + str(current_elpased_minute) + "m :" + str(current_elpased_second) + "s (Elapsed time: " + str(int(current_elpased_time)) + "s)")

            current_job = self.scenario[idx]
            # If the current minute is equal to the minute of the current job, create the job
            if current_elpased_time >= int(current_job[-1]):
                # Create a job
                job_generator = JobGenerator(current_job[0], current_job[1], int(current_job[2]), int(current_job[3]), config)
                job = job_generator.generate_job()
                self.batch_api.create_namespaced_job(namespace="default", body=job)
                print("Created a job: " + job.metadata.name)
                idx += 1

            time.sleep(5)

    def log_scenario(self, debug=False):
        if debug:
            print("Logging the scenario...")
            print("This should be run before the scenario starts.")

        # Open a log file to write
        # Name should be the current time
        log_file_path = os.path.join("logs", "log-" + str(time.time()) + ".txt")
        log_file = open(log_file_path, "w")

        # Check if it's proper to log the scenario
        # If there is already a job running, it's not proper to log the scenario
        if len(self.mnt.get_jobs()[0]) != 0:
            msg = "There is a job running. Exit the logger"
            print(msg)
            log_file.write(msg + "\n")
            return

        while True:
            if len(self.mnt.get_jobs()[0]) != 0:
                start_time = time.time()
                msg = f"Scenario & Loggin started at {start_time}"
                print(msg)
                log_file.write(msg + "\n")
                break
        
        while True:
            # Monitoring if all jobs are done
            break

        log_file.close()

        
            
        scenario_start_time = t
        # After job deploying is done, monitor when all jobs are done.
        # If all jobs are done, log the end time and duration of the scenario.
        # Also log should contain all jobs with their start and end times.

