import utils
from collections import deque

obj      = utils.load_json('bangkok')
nodes    = utils.node_dictionary(obj)
streets  = utils.street_dictionary(obj)
adj_list = utils.adjacency_list(streets)

START_NODE_ID = 702209198
MAX_DISTANCE  = 40

def path_bfs(starting_path, steps):
    best_path, best_completed, best_score = [], 0, 0
    queue = deque([(starting_path[:], 0, steps)])
    done_at_start = utils.streets_completed(starting_path, streets)

    while queue:
        path, dist, steps_left = queue.popleft()

        if steps_left == 0:
            done = utils.streets_completed(path, streets)
            done_delta = done - done_at_start
            score = done_delta / dist

            if score > best_score:
                best_completed = done
                best_score = score
                best_path = path[:]
                print(best_score, best_completed)
            continue

        curr = path[-1]
        prev = path[-2] if len(path) > 1 else None

        choices = list(adj_list[curr])
        if len(choices) > 1 and prev in choices:
            choices.remove(prev)

        delta = 0 if len(choices) == 1 else 1

        for next in choices:
            queue.append((path + [next],
                          dist + utils.node_dist(curr, next, nodes),
                          steps_left - delta))

    return best_path

def node_list_for_csv(path):
    res = []
    for i, node_id in enumerate(path):
        lat, lon = nodes[node_id]
        res.append([float(lat), float(lon), 2, f"\"Name: {node_id}\"", i])
    return res

current_node = START_NODE_ID
current_distance = 0
path = [current_node]

while current_distance < MAX_DISTANCE:
    path = path_bfs(path[:], 8)[:-3]
    print(f"{path=}")
    current_distance = utils.distance_of_path(path, nodes)
    print(current_distance)
    utils.write_nodes_csv(node_list_for_csv(path))

print(path)
print(len(path))
print(best_completed)
