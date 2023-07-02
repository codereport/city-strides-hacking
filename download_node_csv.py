import requests
from cookies_headers import cookies, headers
from enum import Enum
import sys

def parse_nodes(r):
    nodes = []
    for i, data in enumerate(str(response.content).split("],[")):
        try:
            lon, lat, id, name = data.split(",")[:4]
            start = 4 if i == 0 else 0
            nodes.append(
                [float(lon[start:]), float(lat), 2, f"{name} ({int(id[-3:])})"]
            )
        except:
            continue
    return nodes


class City(Enum):
    OLD_TORONTO = 1  # 🇨🇦
    EAST_YORK   = 2  # 🇨🇦
    YORK        = 3  # 🇨🇦
    NORTH_YORK  = 4  # 🇨🇦
    WROCLAW     = 5  # 🇵🇱
    KRAKOW      = 6  # 🇵🇱
    ROME        = 7  # 🇮🇹
    VENICE      = 8  # 🇮🇹
    FOLKESTONE  = 9  # 🇬🇧
    ALL_TORONTO = 10 # 🇨🇦

def name(city: City):
    return str(city)[5:].title().replace('_', ' ')

def file_name(city: City):
    return str(city)[5:].lower()

print("Choose a city:")
for i, c in enumerate(City):
    print(f"{i + 1}. {name(c)}")

try:
    city = City(int(input("Choice: ")))
except:
    print(f"Invalid input: Number must be <= {City.ALL_TORONTO.value}")
    sys.exit()
city_ids = {1: "38121", 2: "38114", 3: "38102", 4: "38108", 5: "191289", 6: "190608", 7: "94322", 8: "93031", 9: "131165", 10: "0"}

if   city == City.YORK:        lon_lats = [-79.3829, 43.7206, -79.5560, 43.6424]
elif city == City.WROCLAW:     lon_lats = [17.078224311098552, 51.13988879756559, 17.00226573206399, 51.09263199227115]
elif city == City.KRAKOW:      lon_lats = [19.979436306324942, 50.08859858611942, 19.90053987336441, 50.034804024531525]
elif city == City.ROME:        lon_lats = [12.519622013860925, 41.91439535724936, 12.443743029831694, 41.85439499689079]
elif city == City.VENICE:      lon_lats = [12.357666134722393, 45.451386491714715, 12.316599314442499, 45.42077976598716]
elif city == City.FOLKESTONE:  lon_lats = [1.2028963028344322, 51.11176465501126, 1.1199095563368644, 51.05639602006997]
else:                          lon_lats = [-79.27, 43.75, -79.49, 43.61]

[start_nelng, start_nelat, start_swlng, start_swlat] = lon_lats

delta = 0.004 if city == City.VENICE else 0.012
lng_tile = int(abs(start_nelng - start_swlng) // delta) + 1
lat_tile = int(abs(start_nelat - start_swlat) // delta) + 1

print(lng_tile, lat_tile)

city_id = city_ids[city.value]

cache = set()
cache_file = f"./cache/{file_name(city)}.csv"
open(cache_file, 'a').close()

with open(cache_file, "r", newline="") as f:
    for line in f:
        [a, b, c, d] = line.strip().split(',')
        cache.add((a, b, c, d))

nodes = []
for x in range(0, lat_tile):
    for y in range(0, lng_tile):

        a = start_nelng - y * delta
        b = start_nelat - x * delta
        c = a - delta
        d = b - delta

        params = {
            "city": city_id,
            "nelng": str(a),
            "nelat": str(b),
            "swlng": str(c),
            "swlat": str(d),
        }

        grid = (str(a), str(b), str(c), str(d))
        if grid not in cache:

            response = requests.get(
                "https://citystrides.com/nodes.json",
                params=params,
                cookies=cookies,
                headers=headers,
            )

            temp = parse_nodes(response)
            print(len(temp))
            if len(temp) == 0:
                cache.add(grid)

            nodes = nodes + temp

titles = [["lat", "lon", "sz", "names"]]

import csv

with open("nodes.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(titles + nodes)

with open(cache_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows([list(grid) for grid in cache])
