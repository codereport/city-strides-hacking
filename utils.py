import csv
import json
from math import sqrt
from itertools import chain
from collections import defaultdict
from geopy.distance import geodesic

def load_json(city):
    with open(f"data/{city}.json", 'r') as f:
        data=f.read()
    return json.loads(data)

def street_dictionary(obj):
    streets = defaultdict(list)
    for e in obj['elements']:
        if e['type'] == 'way':
            streets[e['tags']['name']].append((e['nodes']))
    return streets

def node_dictionary(obj):
    d = {}
    for e in obj['elements']:
        if e['type'] == 'node':
            d[e['id']] = (e['lat'], e['lon'])
    return d

def adjacency_list(streets):
    adj_list = defaultdict(set)
    for _, snodes in streets.items():
        for ssnodes in snodes:
            for a, b in zip(ssnodes, ssnodes[1:]):
                adj_list[a].add(b)
                adj_list[b].add(a)
    return adj_list

def streets_completed(path, streets):
    count = 0
    for _, snodes in streets.items():
        if all(node in path for node in chain(*snodes)):
            count += 1
    return count

def dist(x1, x2, y1, y2):
    dx, dy = x2 - x1, y2 - y1
    return sqrt(dx * dx + dy * dy) * 111

def node_dist(a, b, nodes):
    (x1, y1) = nodes[a]
    (x2, y2) = nodes[b]
    return dist(x1, x2, y1, y2)

def distance_of_path(p, nodes):
    return sum(geodesic(nodes[a], nodes[b]).kilometers for a, b in zip(p, p[1:]))

def length(l, nodes):
    res = 0
    for a, b in zip(l, l[1:], strict=False):
        (x1, y1) = nodes[a]
        (x2, y2) = nodes[b]
        res += dist(x1, x2, y1, y2)
    return res

def total_length(ls, nodes):
    return sum(length(l, nodes) for l in ls)

def write_nodes_csv(nodes):
    with open("nodes.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows([["lat", "lon", "sz", "names", "len_cat"]] + nodes)
