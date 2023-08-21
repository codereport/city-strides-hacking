
import utils
import random
from itertools import chain
from collections import defaultdict
from statistics import mean

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

def adjacency_list(nodes, streets):
    adj_list = defaultdict(set)
    for _, snodes in streets.items():
        for ssnodes in snodes:
            for a, b in zip(ssnodes, ssnodes[1:]):
                # if a in nodes and b in nodes:
                adj_list[a].add(b)
                adj_list[b].add(a)
    return adj_list

# for name, snodes in streets.items():
#     if START_NODE_ID in set(chain(*snodes)):
#         print(name, snodes)

adj_list = adjacency_list(nodes, streets)

# for a, b in adj_list.items():
#     print(a, b)

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

def determine_next_choice_via_mcts(path, last, adj_list, steps, iterations):
    stats = {}
    best_option = None
    best_score = (0, 0, 0, 0)
    choices = adj_list[path[-1]]
    if last in choices:
        choices.remove(last)
    for option in adj_list[path[-1]]:
        completed = []
        total_distances = []
        total_scores = []
        for _ in range(iterations):
            _path = path.copy()
            # _seen = seen.copy()
            _last = last
            total_distance = 0
            total_score = 0
            #######
            for _ in range(steps):
                id = _path[-1]
                next_id = determine_next_choice_via_random_but_prioritize_new(_path, _last, adj_list)
                total_distance += utils.node_dist(id, next_id, nodes)
                total_score += ns[next_id]
                _path.append(next_id)
                # _seen.add(next_id)
                _last = id
            completed.append(streets_completed(_path, streets))
            total_scores.append(total_score)
            total_distances.append(total_distance)
            #######
        print(f"{last=}")
        score = max((c / dist) * (1 + s) for c, dist, s in zip(completed, total_distances, total_scores))
        print(completed)
        # print(total_scores)
        # print(total_distances)
        stat = (score, mean(completed), mean(total_scores), -mean(total_distances))
        stats[option] = stat
        if best_option is None or stat > best_score:
            best_option = option
            best_score = stat
    print(stats)
    # if all_equal(stats.values()):
    #     return determine_next_choice_via_random_but_prioritize_new(path, _last, adj_list)
    return best_option

path = [START_NODE_ID]
total_distance = 0
# seen = set(path)
last = -1

while total_distance < 5:
    id = path[-1]
    # next_id = determine_next_choice_via_random_but_prioritize_new(path, seen, adj_list)
    choices = list(adj_list[id])
    # new_choices = [c for c in choices if c not in seen]
    if len(choices) == 1:
        next_id = choices[0]
    # elif len(new_choices) == 1:
    #     next_id = new_choices[0]
    else:
        if last in choices:
            choices.remove(last)
        if len(choices) == 1:
            next_id = choices[0]
        else:
            next_id = determine_next_choice_via_mcts(path, last, adj_list, 50, 1000)
    total_distance += utils.node_dist(id, next_id, nodes)
    path.append(next_id)
    # seen.add(next_id)
    last = id
    print(total_distance)

nodes = []
for i, id in enumerate(path):
    (lat, lon) = filtered_nodes[id]
        # id = e['id']
        # len_cat = 'a' if id in a else 'b' if id in b else 'c' if id in c else 'd'
        # l = lengths[e['id']]
        # if (l < 1):
    nodes.append([float(lat), float(lon), 2, f"\"Name: {id}\"", i])

print(path)
print(len(path))
print(f"{streets_completed(path, streets)=}")

utils.write_nodes_csv(nodes)
