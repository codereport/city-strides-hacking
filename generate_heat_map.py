#! /usr/bin/env python3

from itertools import chain
from pathlib import Path
import os
import utils
from tqdm import tqdm

city    = utils.load_parameters()['city']
obj     = utils.load_json(city)
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

nodes_to_write = []

csnodes_file = Path(__file__).parent / "csnodes" / f"{city}.csv"
remove_nodes = os.path.exists(csnodes_file)
if remove_nodes:
    points_done = utils.load_completed_csnodes(csnodes_file)
print("Determining which nodes to show...")
for e in tqdm(obj['elements']):
    if e['type'] == 'node':
        id = e['id']
        l = lengths[id]
        point = (float(e['lat']), float(e['lon']))
        if (l < 1) and (not remove_nodes or points_done and utils.is_close(points_done, point, 0.01)):
            nodes_to_write.append([float(e['lat']), float(e['lon']), 2, f"\"Name: {id}\"", l])

utils.write_nodes_csv(nodes_to_write)
