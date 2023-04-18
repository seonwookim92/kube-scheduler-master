import numpy as np

# Define the nodes representing the Kubernetes nodes
nodes = [
    {'name': 'node1', 'cpu': 4, 'memory': 16},
    {'name': 'node2', 'cpu': 6, 'memory': 24},
    {'name': 'node3', 'cpu': 8, 'memory': 32},
    {'name': 'node4', 'cpu': 10, 'memory': 40},
    {'name': 'node5', 'cpu': 12, 'memory': 48},
]

# Get the index of node based on its name
def get_node_idx(node_name):
    for idx, node in enumerate(nodes):
        if node['name'] == node_name:
            return idx
        
def get_node_by_name(node_name):
    for node in nodes:
        if node['name'] == node_name:
            return node

# Define the pods representing the Kubernetes pods
pods = [
    {'name': 'pod1', 'cpu': 2, 'memory': 8},
    {'name': 'pod2', 'cpu': 4, 'memory': 16},
    {'name': 'pod3', 'cpu': 6, 'memory': 24},
]

def get_pod_by_name(pod_name):
    for pod in pods:
        if pod['name'] == pod_name:
            return pod

# Define the pheromone matrix initialized with a small positive constant
pheromone_matrix = np.ones((5, 5)) * 0.1

# Define the ant colony with each ant representing a Kubernetes pod
# ant_colony = [
#     {'name': 'ant1', 'pod': 'pod1', 'current_node': None, 'quality': 0},
#     {'name': 'ant2', 'pod': 'pod2', 'current_node': None, 'quality': 0},
#     {'name': 'ant3', 'pod': 'pod3', 'current_node': None, 'quality': 0},
# ]
ant_colony = [
    {'name': 'ant1', 'feature': 'cpu', 'current_node': None, 'quality': 0},
    {'name': 'ant2', 'feature': 'memory', 'current_node': None, 'quality': 0},
]

# Define the fitness function to evaluate the quality of the solution
# def evaluate_fitness(solution):
#     # Calculate the total resources used by the solution
#     cpu_used = sum([get_pod_by_name(pod)['cpu'] for pod, node in solution])
#     memory_used = sum([get_pod_by_name(pod)['memory'] for pod, node in solution])
#     # Calculate the fitness value based on the percentage of resources used
#     fitness = (cpu_used / sum([node['cpu'] for node in nodes])) * (memory_used / sum([node['memory'] for node in nodes]))
#     return fitness
def evaluate_fitness(solution, feature):
    # Calculate the total resources used by the solution
    feature_used = sum([get_pod_by_name(pod)[feature] for pod, node in solution])
    # Calculate the fitness value based on the percentage of resources used
    fitness = (feature_used / sum([node[feature] for node in nodes]))
    return fitness


# Define the function to get the valid nodes for a pod
# def get_valid_nodes(pod):
#     valid_nodes = []
#     for node in nodes:
#         if node['cpu'] >= pod['cpu'] and node['memory'] >= pod['memory']:
#             valid_nodes.append(node['name'])
#     return valid_nodes
def get_valid_nodes(feature):
    valid_nodes = []
    for node in nodes:
        if node[feature] >= pod[feature]:
            valid_nodes.append(node['name'])
    return valid_nodes

# Define the function to compute the probabilities of moving to the next node
def compute_probabilities(valid_nodes, current_node, pheromone_matrix):
    # print(f"valid_nodes: {valid_nodes}")
    pheromones = [pheromone_matrix[get_node_idx(current_node['name'])][get_node_idx(node)] for node in valid_nodes]

    # print(f"pheromones: {pheromones}")
    heuristics = [1.0 / (get_node_idx(node) + 1) for node in valid_nodes]
    # print(f"heuristics: {heuristics}")
    probabilities = [pheromones[i] * heuristics[i] for i in range(len(valid_nodes))]
    # print(f"probabilities: {probabilities}")
    sum_probabilities = sum(probabilities)
    if sum_probabilities == 0:
        probabilities = [1.0 / len(valid_nodes) for node in valid_nodes]
    else:
        probabilities = [p / sum_probabilities for p in probabilities]
    return probabilities

# Define the function to select the next node based on the probabilities
def select_next_node(valid_nodes, probabilities):
    cum_probabilities = np.cumsum(probabilities)
    random_number = np.random.rand()
    for i in range(len(cum_probabilities)):
        if random_number <= cum_probabilities[i]:
            return valid_nodes[i]

# Define the function to update the pheromone matrix after each ant has finished its tour
def update_pheromones(solution, pheromone_matrix, evaporation_rate, quality):
    for pod, node in solution:
        i = get_node_idx(node)
        j = get_node_idx(solution[(solution.index((pod, node)) + 1) % len(solution)][1])
        pheromone_matrix[i][j] = (1 - evaporation_rate) * pheromone_matrix[i][j] + evaporation_rate * quality

if __name__ == '__main__':
    # Define the parameters of the ACO algorithm
    evaporation_rate = 0.1
    num_iterations = 10
    num_ants = len(pods)

    pod = pods[2]

    # Run the ACO algorithm for the specified number of iterations
    for iteration in range(num_iterations):
        # Initialize the solutions for each ant
        solutions = {ant['name']: [] for ant in ant_colony}
        # Let each ant construct a solution by choosing the next node based on the probabilities
        for ant in ant_colony:
            # valid_nodes = get_valid_nodes([pod for pod in pods if pod['name'] == ant['pod']][0])
            valid_nodes = get_valid_nodes(ant['feature'])
            # print(f"Valid nodes for {ant['pod']}: {valid_nodes}")
            if not valid_nodes:
                continue
            if not ant['current_node']:
                ant['current_node'] = nodes[np.random.randint(len(nodes))]
            while len(solutions[ant['name']]) < len(nodes):
                probabilities = compute_probabilities(valid_nodes, ant['current_node'], pheromone_matrix)
                print(f"Probabilities: {probabilities}")
                next_node = select_next_node(valid_nodes, probabilities)
                solutions[ant['name']].append((pod['name'], [node for node in nodes if node['name'] == next_node][0]))
                ant['current_node'] = [node for node in nodes if node['name'] == next_node][0]
        # Evaluate the quality of each solution and update the pheromone matrix
        for ant in ant_colony:
            solution = solutions[ant['name']]
            fitness = evaluate_fitness(solution, ant['feature'])
            ant['quality'] = fitness
            update_pheromones(solution, pheromone_matrix, evaporation_rate, fitness)
        print(f"Solution: {solutions}")
        # Sort the ants by quality and print the best solution found so far
        ant_colony = sorted(ant_colony, key=lambda x: x['quality'], reverse=True)
        print(f"Ant colony: {ant_colony}")
        best_solution = solutions[ant_colony[0]['name']]
        print('Iteration {}: Best solution found: {}'.format(iteration+1, best_solution))

        
