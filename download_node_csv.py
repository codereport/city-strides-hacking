import requests
from cookies_headers import cookies, headers


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


# Smaller toronto
# start_nelng = -79.3957
# start_nelat = 43.686
# start_swlng = -79.4511
# start_swlat = 43.655

# Larger toronto
# start_nelng = -79.280
# start_nelat = 43.72040452083706
# start_swlng = -79.475302381091
# start_swlat = 43.63008386434698

# All old toronto
start_nelng = -79.27
start_nelat = 43.75
start_swlng = -79.49
start_swlat = 43.61

delta = 0.012
lng_tile = int(abs(start_nelng - start_swlng) // delta) + 1
lat_tile = int(abs(start_nelat - start_swlat) // delta) + 1

print("Choose a city:")
print("1. Old Toronto")
print("2. East York")
print("3. All\n")

city = int(input("Choice: "))
city_ids = {1: "38121", 2: "38114", 3: "0"}

print(lng_tile, lat_tile)

if city not in [1, 2, 3]:
    print("Invalid input")
else:
    city_id = city_ids[city]

    cache = set()
    cache_file = "./cache/" + city_id + "_cache.csv"
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
