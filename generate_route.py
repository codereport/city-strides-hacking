import utils
from collections import deque

obj      = utils.load_json('etobicoke')
streets  = utils.street_dictionary(obj)

obj_all      = utils.load_json('etobicoke_all')
nodes_all    = utils.node_dictionary(obj_all)
adj_list_all = utils.adjacency_list(utils.street_dictionary(obj_all))

def path_bfs(starting_path, steps):
    best_path, best_completed, best_score = [], 0, 0
    queue = deque([(starting_path[:], 0, steps)])
    done_at_start = utils.streets_completed(starting_path, streets)

    while queue:
        path, dist, steps_left = queue.popleft()

        if steps_left == 0:
            done  = utils.streets_completed(path, streets)
            score = (done - done_at_start) / dist

            if score > best_score:
                best_completed, best_score, best_path = done, score, path[:]
                print(best_score, best_completed)
        else:
            curr = path[-1]
            prev = path[-2] if len(path) > 1 else None

            choices = list(adj_list_all[curr])
            if len(choices) > 1 and prev in choices:
                choices.remove(prev)

            for next in choices:
                queue.append((path + [next],
                            dist + utils.node_dist(curr, next, nodes_all),
                            steps_left - (len(choices) > 1)))

    return best_path

def node_list_for_csv(path):
    res = []
    for i, id in enumerate(path):
        lat, lon = nodes_all[id]
        res.append([float(lat), float(lon), 2, f"\"Name: {id}\"", i])
    return res

START_NODE_ID = 21098692 # 9038489299 # 702209198
MAX_DISTANCE  = 10

total_distance = 0
path = [START_NODE_ID]

while total_distance < MAX_DISTANCE:
    path = path_bfs(path, 10)
    total_distance = utils.distance_of_path(path, nodes_all)
    print(f"{total_distance=}")
    utils.write_nodes_csv(node_list_for_csv(path))
