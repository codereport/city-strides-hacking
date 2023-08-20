import json
import csv
from math import sqrt
from itertools import chain
from collections import defaultdict

with open('data/etobicoke.json', 'r') as f:
    data=f.read() # read file

obj = json.loads(data) # parse file

def node_dict(obj):
    d = {}
    for e in obj['elements']:
        if e['type'] == 'node':
            d[e['id']] = (e['lat'], e['lon'])
    return d

def dist(x1, x2, y1, y2):
    dx, dy = x2 - x1, y2 - y1
    return sqrt(dx * dx + dy * dy) * 111

nodes = node_dict(obj)

def length(l):
    res = 0
    for a, b in zip(l, l[1:], strict=False):
        (x1, y1) = nodes[a]
        (x2, y2) = nodes[b]
        res += dist(x1, x2, y1, y2)
    return res

def total_length(ls):
    return sum(length(l) for l in ls)

streets = defaultdict(list)
for e in obj['elements']:
    if e['type'] == 'way':
        streets[e['tags']['name']].append((e['nodes']))

a, b, c = set(), set(), set()
for s, n in streets.items():
    tl = total_length(n)
    if   tl < 0.05: a |= set(chain(*n))
    elif tl < 0.1:  b |= set(chain(*n))
    elif tl < 0.2:  c |= set(chain(*n))
    print(f"{s}, Number of nodes: {len(set(chain(*n)))}, Length: {round(tl, 3)}")
print(f"# of Streets: {len(streets)}")
print(f"# of Nodes From Streets: {sum(len(s) for s in streets.values())}")
print(f"# of Nodes From Query: {len([e for e in obj['elements'] if e['type'] == 'node'])}")
print(len(nodes))


nodes = []
for e in obj['elements']:
    if e['type'] == 'node':
        id = e['id']
        len_cat = 'a' if id in a else 'b' if id in b else 'c' if id in c else 'd'
        nodes.append([float(e['lat']), float(e['lon']), 2, f"\"Name: {e['id']}\"", len_cat])

# copy and pasted from download_node_csv.py
with open("../nodes.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows([["lat", "lon", "sz", "names", "len_cat"]] + nodes)
