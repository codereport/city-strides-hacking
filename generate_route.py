
import utils
import random
from itertools import chain
from collections import defaultdict

obj     = utils.load_json('bangkok')
nodes   = utils.node_dictionary(obj)
streets = utils.street_dictionary(obj)

START_NODE_ID = 702209198 # 2385175793 # 4634907181
RANGE_IN_KM   = 8

# first, filter out nodes
x, y = nodes[START_NODE_ID]
filtered_nodes = {}
for n, (x1, y1) in nodes.items():
    if utils.dist(x, x1, y, y1) < RANGE_IN_KM:
        filtered_nodes[n] = (x1, y1)

def adjacency_list(streets):
    adj_list = defaultdict(set)
    for _, snodes in streets.items():
        for ssnodes in snodes:
            for a, b in zip(ssnodes, ssnodes[1:]):
                adj_list[a].add(b)
                adj_list[b].add(a)
    return adj_list

adj_list = adjacency_list(streets)

def streets_completed(path, streets):
    count = 0
    for _, snodes in streets.items():
        if all(node in path for node in chain(*snodes)):
            count += 1
    return count

def node_scores():
    scores = defaultdict(int)
    for _, n in streets.items():
        tl = utils.total_length(n, nodes)
        for node in set(chain(*n)):
            scores[node] = max(scores[node], (100 * (0.2 - min(tl, 0.2))) // 10)
    return scores

ns = node_scores()

def determine_next_choice_via_random_but_prioritize_new(path, last, adj_list):
    id = path[-1]
    choices = list(adj_list[id])
    if len(choices) == 1:
        return choices[0]
    else:
        if last in choices:
            choices.remove(last)
        if len(choices) == 1:
            return choices[0]
        else:
            return random.choice(choices)

prev_distance, prev_completed = 0, 0
best_path, best_completed, best_score = "", 0, 0

def distance_of_path(p):
    return sum(utils.node_dist(a, b, nodes) for a, b in zip(p, p[1:]))

def path_bfs(path_: list, dist: float, choices_left: int):
    global best_completed, best_path, best_score
    path = path_.copy()
    if choices_left == 0:
        done = streets_completed(path, streets)
        done_delta = done - prev_completed
        score = done_delta / dist

        if score > best_score:
            best_completed = done
            best_score = score
            best_path = path
            print(score, done)
        return
    id = path[-1]
    choices = list(adj_list[id])
    if len(choices) == 1:
        next_id = choices[0]
        path.append(next_id)
        path_bfs(path, dist + utils.node_dist(id, next_id, nodes), choices_left)
    else:
        if len(path) > 1:
            last = path[-2]
            if last in choices:
                choices.remove(last)
        if len(choices) == 1:
            next_id = choices[0]
            path.append(next_id)
            path_bfs(path, dist + utils.node_dist(id, next_id, nodes), choices_left)
        else:
            for choice in choices:
                new_path = path.copy()
                new_path.append(choice)
                path_bfs(new_path, dist + utils.node_dist(id, choice, nodes), choices_left - 1)


def determine_next_choice_via_mcts(path, steps):
    global best_completed, best_path, best_score
    best_path, best_completed, best_score = [], 0, 0
    path_bfs(path, 0, steps)
    print(f"{best_path=}")
    print(f"{best_completed=}")
    return best_path

def node_list_for_csv(p):
    nodes = []
    for i, id in enumerate(p):
        (lat, lon) = filtered_nodes[id]
        nodes.append([float(lat), float(lon), 2, f"\"Name: {id}\"", i])
    return nodes

path = [START_NODE_ID]
total_distance = 0

while total_distance < 40:
    path = determine_next_choice_via_mcts(path, 8)[:-3]
    total_distance = distance_of_path(path)
    print(total_distance)
    prev_completed = best_completed
    prev_distance = total_distance
    utils.write_nodes_csv(node_list_for_csv(path))

print(path)
print(len(path))
print(f"{streets_completed(path, streets)=}")

utils.write_nodes_csv(node_list_for_csv(path))
