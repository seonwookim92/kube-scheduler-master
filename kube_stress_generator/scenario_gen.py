# scenario_gen.py : Generate a scenario file to generate a sequence of stressors

# Parameters
STRESS_LEVEL_MAX = 5 # Maximum stress level
STRESS_DURATION_MAX = 5 # minutes
STRESS_TYPE = ["cpu", "vm"] # Stress types to generate
NUM_JOBS = 100 # Number of jobs to generate
RUN_TIME = 10 # minutes


import time, datetime
import random



# Will output the scenario file to the ./scenarios directory
# Each line should be [index, stress_type, stress_level, duration, start_time]

scenario = []

for i in range(NUM_JOBS):
    # Select a random stress type, stress level, and duration
    stress_type = random.choice(STRESS_TYPE)
    stress_level = random.randint(1, STRESS_LEVEL_MAX)
    duration = random.randint(1, STRESS_DURATION_MAX)
    start_time = random.randint(0, RUN_TIME * 60)
    
    scenario.append([stress_type, stress_level, duration, start_time])

# Sort the scenario by start time (ascending) and prepend the index
scenario.sort(key=lambda x: x[3])
for i in range(len(scenario)):
    scenario[i].insert(0, i)

for line in scenario:
    print(line)

# Write the scenario to a file
filename = f"scenario-{datetime.date.today()}.csv"
with open(f"./scenarios/{filename}", "w") as f:
    for line in scenario:
        f.write(f"{line[0]},{line[1]},{line[2]},{line[3]},{line[4]}\n")
print(f"Scenario file {filename} written to ./scenarios directory")

# Path: stress-gen/scenario_runner.py