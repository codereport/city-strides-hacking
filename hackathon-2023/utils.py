import json
from math import sqrt
from collections import defaultdict

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

def dist(x1, x2, y1, y2):
    dx, dy = x2 - x1, y2 - y1
    return sqrt(dx * dx + dy * dy) * 111

def length(l, nodes):
    res = 0
    for a, b in zip(l, l[1:], strict=False):
        (x1, y1) = nodes[a]
        (x2, y2) = nodes[b]
        res += dist(x1, x2, y1, y2)
    return res

def total_length(ls, nodes):
    return sum(length(l, nodes) for l in ls)
