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

print("Choose a city:")
print("1. Old Toronto")
print("2. East York")
print("3. York")
print("4. North York")
print("5. Wroclaw")
print("6. Kraków")
print("7. Rome")
print("8. Venice")
print("9. Folkestone")
print("10. All\n")

city = int(input("Choice: "))
city_ids = {1: "38121", 2: "38114", 3: "38102", 4: "38108", 5: "191289", 6: "190608", 7: "94322", 8: "93031", 9: "131165", 10: "0"}

if city == 3:
    # York
    start_nelng = -79.3829
    start_nelat = 43.7206
    start_swlng = -79.5560
    start_swlat = 43.6424
elif city == 5:
    start_nelng=17.078224311098552
    start_nelat=51.13988879756559
    start_swlng=17.00226573206399
    start_swlat=51.09263199227115
elif city == 6:
    start_nelng=19.979436306324942
    start_nelat=50.08859858611942
    start_swlng=19.90053987336441
    start_swlat=50.034804024531525
elif city == 7:
    start_nelng=12.519622013860925
    start_nelat=41.91439535724936
    start_swlng=12.443743029831694
    start_swlat=41.85439499689079
elif city == 8:
    start_nelng=12.357666134722393
    start_nelat=45.451386491714715
    start_swlng=12.316599314442499
    start_swlat=45.42077976598716
elif city == 9:
    start_nelng=1.2028963028344322
    start_nelat=51.11176465501126
    start_swlng=1.1199095563368644
    start_swlat=51.05639602006997
else:
    # All old toronto
    start_nelng = -79.27
    start_nelat = 43.75
    start_swlng = -79.49
    start_swlat = 43.61

delta = 0.004 if city == 8 else 0.012
lng_tile = int(abs(start_nelng - start_swlng) // delta) + 1
lat_tile = int(abs(start_nelat - start_swlat) // delta) + 1

print(lng_tile, lat_tile)

if city not in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
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
