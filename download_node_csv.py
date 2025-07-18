#! /usr/bin/env python3

import argparse
import json
import shutil
import sys
import time
from ast import literal_eval
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, fields
from enum import Enum
from functools import partial
from math import ceil
from pathlib import Path
from typing import Dict

import pandas as pd
import requests
from tqdm import tqdm

NODES_FILE = Path(__file__).parent / "nodes.csv"


@dataclass
class Node:
    lat: float
    lon: float
    sz: int = 2
    names: str = ""
    len_cat: str = "a"


# fmt: off
class City(str, Enum):
    ALL_TORONTO  = 131268 # 🇨🇦
    OLD_TORONTO  = 38121  # 🇨🇦
    EAST_YORK    = 38114  # 🇨🇦
    YORK         = 38102  # 🇨🇦
    NORTH_YORK   = 38108  # 🇨🇦
    CALGARY      = 171388 # 🇨🇦
    WROCLAW      = 191289 # 🇵🇱
    KRAKOW       = 190608 # 🇵🇱
    ROME         = 94322  # 🇮🇹
    VENICE       = 93031  # 🇮🇹
    FOLKESTONE   = 131165 # 🇬🇧
    MEAFORD      = 39015  # 🇨🇦
    BANGKOK      = 223551 # 🇹🇭
    KUALA_LUMPUR = 225540 # 🇲🇾
    YELLOWKNIFE  = 188033 # 🇨🇦
    MANHATTAN    = 171333 # 🇺🇸
    TINY         = 38936  # 🇨🇦
    CAMBRIDGE    = 131115 # 🇬🇧
    VANCOUVER    = 37612  # 🇨🇦
    BURNABY      = 37754  # 🇨🇦
    SQUAMISH     = 38119  # 🇨🇦
    CADIZ        = 115116 # 🇪🇸
    SEVILLE      = 110445 # 🇪🇸
    GIBRALTAR    = 216411 # 🇬🇮
    TARIFA       = 115036 # 🇪🇸
    AMSTERDAM    = 97421  # 🇳🇱
    BREDA        = 95743  # 🇳🇱
    HAMILTON     = 132379 # 🇨🇦
    OTTAWA       = 131267 # 🇨🇦
    ETOBICOKE    = 38014  # 🇨🇦
    VAUGHAN      = 37668  # 🇨🇦
    SUNNYVALE    = 2105   # 🇺🇸
    SANTA_CLARA  = 2592   # 🇺🇸
    TOKYO        = 0      # 🇯🇵
    KYOTO        = 86675  # 🇯🇵
    HIROSHIMA    = 88900  # 🇯🇵
    MIDLAND      = 38950  # 🇨🇦
# fmt: on


def parse_options():
    parser = argparse.ArgumentParser()
    parser.add_argument("cookies_path", type=Path, help="path to cookie")
    return parser.parse_args()


def parse_nodes(r: str):
    nodes = []
    for node in literal_eval(r):
        nodes.append(
            Node(lat=node[0],
                 lon=node[1],
                 names=f"{node[3]} ({str(node[2])[-3:]})"))
    return nodes


def enum_to_cityname(city: City):
    return city.name.title().replace("_", " ")


def filename(city: City):
    return city.name.lower()


@dataclass
class CityGrid:
    nelng: float
    nelat: float
    swlng: float
    swlat: float

    def __post_init__(self):
        for k in fields(self):
            value = getattr(self, k.name)
            if not isinstance(value, k.type):
                setattr(self, k.name, k.type(value))

    def __hash__(self):
        return hash((self.nelng, self.nelat, self.swlng, self.swlat))


# fmt: off
CityGrids = {
    City.YORK:         CityGrid(-79.3829, 43.7206, -79.5560, 43.6424),
    City.WROCLAW:      CityGrid(17.078224311098552, 51.13988879756559,  17.00226573206399,  51.09263199227115 ),
    City.KRAKOW:       CityGrid(19.979436306324942, 50.08859858611942,  19.90053987336441,  50.034804024531525),
    City.ROME:         CityGrid(12.519622013860925, 41.91439535724936,  12.443743029831694, 41.85439499689079 ),
    City.VENICE:       CityGrid(12.357666134722393, 45.451386491714715, 12.316599314442499, 45.42077976598716 ),
    City.FOLKESTONE:   CityGrid(1.2028963028344322, 51.11176465501126,  1.1199095563368644, 51.05639602006997 ),
    City.MEAFORD:      CityGrid(-80.49028489574928, 44.754231277837675, -80.94388807383417, 44.44134084860639 ),
    City.BANGKOK:      CityGrid(100.63077252004365, 13.847639730527689, 100.43201063327376, 13.638682174742826),
    City.KUALA_LUMPUR: CityGrid(101.77057184116842, 3.2535737239631857, 101.60542181002302, 3.019316817120796),
    City.OLD_TORONTO:  CityGrid(-79.20, 43.8, -79.556, 43.61),
    City.NORTH_YORK:   CityGrid(-79.20, 43.8, -79.556, 43.61),
    City.EAST_YORK:    CityGrid(-79.20, 43.8, -79.556, 43.61),
    City.YELLOWKNIFE:  CityGrid(-114.27992785264068, 62.54634422107276,  -114.53535016375272, 62.40108397535985),
    City.MANHATTAN:    CityGrid(-73.85718821472695,  40.88516054351777,  -74.06031270089198,  40.695918553464935),
    City.ALL_TORONTO:  CityGrid(-79.10207774524551,  43.874371274629254, -79.64422630796089,  43.553523478901695),
    City.CALGARY:      CityGrid(-113.84035843838264, 51.21489889420778,  -114.31427300643004, 50.83873600399619),
    City.TINY:         CityGrid(-79.81303437561235,  44.863870741308716, -80.14136564528225,  44.56840772951833),
    City.CAMBRIDGE:    CityGrid(0.1811570169931258,  52.23740346269025,  0.07287138362812584, 52.15811587311657),
    City.VANCOUVER:    CityGrid(-123.02909090201416, 49.31212916727142,  -123.21873640899457, 49.19487875418696),
    City.BURNABY:      CityGrid(-122.88970118186715, 49.29967340000033,  -123.02696911813251, 49.18019190000055),
    City.SQUAMISH:     CityGrid(-123.00275292414716, 49.872944599999016, -123.27484497585226, 49.63859249999908),
    City.CADIZ:        CityGrid(-6.2157077258520985, 36.54331932565229,  -6.32122728321167,   36.44340232630665),
    City.SEVILLE:      CityGrid(-5.883170845478531,  37.461184756279934, -6.027356115149104,  37.30844723005012),
    City.GIBRALTAR:    CityGrid(-5.3294080533749195, 36.155189618243924, -5.372301431021356,  36.1090038077334),
    City.TARIFA:       CityGrid(-5.589701126793301,  36.034916173782904, -5.619875614059367,  36.00237863180827),
    City.AMSTERDAM:    CityGrid(4.987117281815472,   52.44980292925038,   4.807865173264588,  52.30391661971481),
    City.BREDA:        CityGrid(4.859945675727062,   51.64319800000035,   4.669720224275039,  51.485548200000665),
    City.HAMILTON:     CityGrid(-79.57586910948109,  43.4981101475974,   -80.28768504749316,  43.02415307269649),
    City.OTTAWA:       CityGrid(-75.59735626950922,  45.47238781891815,  -75.7510099560269,   45.328554089178425),
    City.ETOBICOKE:    CityGrid(-79.47007784409307,  43.756274990960634, -79.63802401620521,  43.594333920454034),
    City.VAUGHAN:      CityGrid(-79.46907989509845,  43.91808423753184,  -79.6438153757494,   43.7500430310711),
    City.SANTA_CLARA:  CityGrid(-121.92742512901083, 37.41852740000034, -122.00712367099024, 37.32300270000002),
    City.SUNNYVALE:    CityGrid(-121.98569587889338, 37.42523313647796, -122.06250038385679, 37.33318752018717),
    City.TOKYO:        CityGrid(139.88900661317638, 35.746960291813835, 139.63511863498388, 35.60431963567605),
    City.KYOTO:        CityGrid(135.87139975892916, 35.0922704545566, 135.60905189575635, 34.86600122511402),
    City.HIROSHIMA:    CityGrid(132.5776755786111, 34.495663440816756, 132.34632233314363, 34.294713844366186),
    City.MIDLAND:      CityGrid(-79.81294917205652, 44.80296510000011, -79.94869932794363, 44.70148789999999),
}
# fmt: on


def get_city_from_user():
    terminal_size = shutil.get_terminal_size((80, 20))
    max_width = terminal_size.columns
    cities = [enum_to_cityname(c) for c in City]
    max_city_name_length = max(len(city) for city in cities) + 7
    num_columns = max(1, max_width // max_city_name_length)
    num_rows = ceil(len(cities) / num_columns)

    table = []
    for i in range(num_rows):
        row = []
        for j in range(num_columns):
            idx = i + j * num_rows
            to_add = f"{idx + 1}. {cities[idx]}" if idx < len(cities) else ""
            row.append(to_add)
        table.append(row)

    for row in table:
        print("  ".join(f"{cell:<{max_city_name_length}}" for cell in row
                        if cell))

    try:
        city = list(City)[int(input("\nChoice: ")) - 1]
    except:
        print(f"Invalid input: Number must be <= {len(City)}")
        sys.exit()

    return city


def citygrid_to_str(g: CityGrid) -> Dict[str, str]:
    return {k: str(v) for k, v in asdict(g).items()}


def make_grid_steps(grid: CityGrid, delta: float):
    lng_tile = int(abs(grid.nelng - grid.swlng) // delta) + 1
    lat_tile = int(abs(grid.nelat - grid.swlat) // delta) + 1

    print(lng_tile, lat_tile)
    for x in range(0, lat_tile):
        for y in range(0, lng_tile):
            nelng = grid.nelng - y * delta
            nelat = grid.nelat - x * delta
            swlng = nelng - delta
            swlat = nelat - delta
            yield CityGrid(nelng=nelng, nelat=nelat, swlng=swlng, swlat=swlat)


def download_nodes_of_coordinates(city, coordinates, cache):
    if coordinates in cache:
        return []
    params = {"city": city.value, **citygrid_to_str(coordinates)}
    response = requests.get("https://citystrides.com/nodes.json",
                            params=params,
                            cookies=cookies)

    try:
        lat_lons = parse_nodes(response.text)
        if len(lat_lons) == 0:
            cache.add(coordinates)
        elif len(lat_lons) > 1000:
            print(len(lat_lons))
        return lat_lons
    except Exception:
        time.sleep(10)
        return download_nodes_of_coordinates(city, coordinates, cache)


def download_nodes_of_city(city: City):
    grid = CityGrids[city]

    nodes = []
    cache = set()
    cache_file = Path(__file__).parent / f"./cache/{filename(city)}.csv"
    cache_file.touch()

    with open(cache_file) as f:
        for line in f.read().splitlines():
            cache.add(CityGrid(*line.strip().split(",")))

    # fmt: off
    delta = 0.012
    if city == City.VENICE:  delta = 0.004
    if city == City.MEAFORD: delta = 0.02
    if city == City.BANGKOK: delta = 0.006
    # fmt: on

    with ThreadPoolExecutor(
            max_workers=12) as executor:  # Adjust max_workers as needed
        download_func = partial(download_nodes_of_coordinates,
                                city,
                                cache=cache)
        futures = [
            executor.submit(download_func, coordinates)
            for coordinates in make_grid_steps(grid, delta)
        ]

        with tqdm(total=len(futures), desc="Downloading Nodes") as pbar:
            for future in futures:
                lat_lons = future.result()
                nodes.extend(lat_lons)
                pbar.update(1)

    return nodes, cache, cache_file


if __name__ == "__main__":
    args = parse_options()
    with open(args.cookies_path) as f:
        cookies = json.load(f)

    city = get_city_from_user()
    nodes, cache, cache_file = download_nodes_of_city(city)

    # Write to nodes.csv
    df = pd.DataFrame(nodes)
    df.to_csv(NODES_FILE, index=True)

    # Write to csnodes/<city>.csv
    csnodes_file = Path(__file__).parent / "csnodes" / f"{filename(city)}.csv"
    df.to_csv(csnodes_file, index=True)

    # Write to cache/<city>.csv
    df = pd.DataFrame(cache)
    df.to_csv(cache_file, index=False, header=False)
