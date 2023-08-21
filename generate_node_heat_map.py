import csv
from itertools import chain
import utils

obj     = utils.load_json('bangkok')
nodes   = utils.node_dictionary(obj)
streets = utils.street_dictionary(obj)

a, b, c = set(), set(), set()
lengths = {}
for s, n in streets.items():
    tl = utils.total_length(n, nodes)
    if   tl < 0.05: a |= set(chain(*n))
    elif tl < 0.1:  b |= set(chain(*n))
    elif tl < 0.2:  c |= set(chain(*n))
    print(f"{s}, Number of nodes: {len(set(chain(*n)))}, Length: {round(tl, 3)}")
    for node in set(chain(*n)):
        lengths[node] = tl

print(f"# of Streets: {len(streets)}")
print(f"# of Nodes From Streets: {sum(len(s) for s in streets.values())}")
print(f"# of Nodes From Query: {len([e for e in obj['elements'] if e['type'] == 'node'])}")
print(len(nodes))

nodes = []
for e in obj['elements']:
    if e['type'] == 'node':
        # id = e['id']
        # len_cat = 'a' if id in a else 'b' if id in b else 'c' if id in c else 'd'
        l = lengths[e['id']]
        if (l < 1):
            nodes.append([float(e['lat']), float(e['lon']), 2, f"\"Name: {e['id']}\"", l])

# copy and pasted from download_node_csv.py
utils.write_nodes_csv(nodes)
