import utils
from collections import deque

obj      = utils.load_json('bangkok')
streets  = utils.street_dictionary(obj)

obj_all      = utils.load_json('bangkok_all')
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
            curr    = path[-1]
            prev    = path[-2] if len(path) > 1 else None
            choices = list(adj_list_all[curr])

            removed = False
            if prev in choices and len(choices) > 1:
                removed = True
                choices.remove(prev)

            dist_to_next = None
            for next in choices:
                dist_to_next = utils.node_geodist(curr, next, nodes_all)
                queue.append((path + [next],
                              dist + dist_to_next,
                              steps_left - (len(choices) > 1)))

            if removed and len(choices) == 1 and dist_to_next > 0.1:
                queue.append((path + [prev],
                              dist + utils.node_geodist(curr, prev, nodes_all),
                              steps_left - 1))

    return best_path

def node_list_for_csv(path):
    res = []
    for i, id in enumerate(path):
        lat, lon = nodes_all[id]
        res.append([float(lat), float(lon), 2, f"\"Name: {id}\"", i])
    return res

START_NODE_ID = 9038489299 # 21098692 # 9038489299 # 702209198
MAX_DISTANCE  = 15

total_distance = 0
path = [START_NODE_ID]

while total_distance < MAX_DISTANCE:
    path = path_bfs(path, 8)[:-3]
    total_distance = utils.distance_of_path(path, nodes_all)
    print(f"{total_distance=}")
    utils.write_nodes_csv(node_list_for_csv(path))
