#! /usr/bin/env python3

from itertools import chain
import math
import utils
from tqdm import tqdm

obj     = utils.load_json('bangkok')
nodes   = utils.node_dictionary(obj)
streets = utils.street_dictionary(obj)

lengths = {}
for s, n in streets.items():
    tl = utils.total_distance_of_paths(n, nodes)
    print(f"{s}, Number of nodes: {len(set(chain(*n)))}, Length: {round(tl, 3)}")
    for node in set(chain(*n)):
        lengths[node] = tl

print(f"# of Streets: {len(streets)}")
print(f"# of Nodes From Streets: {sum(len(s) for s in streets.values())}")
print(f"# of Nodes From Query: {len([e for e in obj['elements'] if e['type'] == 'node'])}")
print(len(nodes))

def is_close_to_node(node):
    for lat, lon in nodes.values():
        if math.isclose(node[0], lat, rel_tol=1e-6, abs_tol=1e-6) and \
           math.isclose(node[1], lon, rel_tol=1e-6, abs_tol=1e-6):
            return True
    return False

nodes_to_write = []
points_d = utils.load_cache()
print("Determining which nodes to show...")
for e in tqdm(obj['elements']):
    if e['type'] == 'node':
        id = e['id']
        l = lengths[id]
        point = (float(e['lat']), float(e['lon']))
        if (l < 1) and utils.is_close(points_d, point, 0.01):
            nodes_to_write.append([float(e['lat']), float(e['lon']), 2, f"\"Name: {id}\"", l])

utils.write_nodes_csv(nodes_to_write)
