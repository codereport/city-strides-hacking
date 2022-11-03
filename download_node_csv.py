import requests
from cookies_headers import cookies, headers

def parse_nodes(r):
    nodes = []  
    for i, data in enumerate(str(response.content).split("],[")):
        try:
            lon, lat, id, name = data.split(',')[:4]
            start = 4 if i == 0 else 0
            nodes.append([float(lon[start:]), float(lat), 2, f"{name} ({int(id[-3:])})"])
        except:
            continue
    return nodes

start_nelng = -79.33955958805103
start_nelat = 43.72040452083706
start_swlng = -79.46570302381091
start_swlat = 43.63008386434698

nodes = []

delta    = 0.012 
lng_tile = int(abs(start_nelng - start_swlng) // delta) + 1
lat_tile = int(abs(start_nelat - start_swlat) // delta) + 1

print(lng_tile, lat_tile)

for x in range(0, lat_tile):
    for y in range(0, lng_tile):

        a = start_nelng - y * delta
        b = start_nelat - x * delta
        c = a - delta
        d = b - delta

        params = {
            'city': '0',
            'nelng': str(a),
            'nelat': str(b),
            'swlng': str(c),
            'swlat': str(d),
        }

        response = requests.get('https://citystrides.com/nodes.json', params=params, cookies=cookies, headers=headers)

        temp = parse_nodes(response)
        print(len(temp))

        nodes = nodes + temp

# TODO: add titles to nodes: ['lat', 'lon', 'sz', 'names']

import csv

with open("nodes.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(nodes)
