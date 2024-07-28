#! /usr/bin/env python3

import requests
from enum import Enum
import sys
import argparse
from pathlib import Path
from dataclasses import dataclass, fields, asdict
from typing import Dict
import json
from ast import literal_eval
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from tqdm import tqdm
import time

NODES_FILE = Path(__file__).parent / "nodes.csv"

@dataclass
class Node:
    lat: float
    lon: float
    sz: int = 2
    names: str = ''
    len_cat: str = 'a'

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

def parse_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('cookies_path', type=Path, help='path to cookie')
    return parser.parse_args()

def parse_nodes(r: str):
    nodes = []
    for node in literal_eval(r):
        nodes.append(Node(lat=node[0], lon=node[1], names=f'{node[3]} ({str(node[2])[-3:]})'))
    return nodes

def enum_to_cityname(city: City):
    return city.name.title().replace('_', ' ')

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
    City.TINY:         CityGrid(-79.81303437561235,  44.863870741308716, -80.14136564528225,  44.56840772951833)

}


def get_city_from_user():
    print("Choose a city:")
    for i, c in enumerate(City):
        print(f"{i + 1}. {enum_to_cityname(c)}")

    try:
        city = list(City)[int(input("\nChoice: ")) - 1]
    except:
        print(f"Invalid input: Number must be <= {len(City)}")
        sys.exit()

    return city


def citygrid_to_str(g: CityGrid) -> Dict[str, str]:
    return {k:str(v) for k, v in asdict(g).items()}


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
    response = requests.get(
        "https://citystrides.com/nodes.json",
        params=params,
        cookies=cookies
    )

    try:
        lat_lons = parse_nodes(response.text)
        if len(lat_lons) == 0:
            cache.add(coordinates)
        elif len(lat_lons) > 1000:
            print(len(lat_lons))
        return lat_lons
    except Exception:
        time.sleep(1)
        return download_nodes_of_coordinates(city, coordinates, cache)

def download_nodes_of_city(city: City):
    grid = CityGrids[city]

    nodes = []
    cache = set()
    cache_file = Path(__file__).parent / f"./cache/{filename(city)}.csv"
    cache_file.touch()

    with open(cache_file, "r") as f:
        for line in f.read().splitlines():
            cache.add(CityGrid(*line.strip().split(',')))

    delta = 0.012
    if city == City.VENICE:  delta = 0.004
    if city == City.MEAFORD: delta = 0.02
    if city == City.BANGKOK: delta = 0.006

    with ThreadPoolExecutor(max_workers=12) as executor:  # Adjust max_workers as needed
        download_func = partial(download_nodes_of_coordinates, city, cache=cache)
        futures = [executor.submit(download_func, coordinates) for coordinates in make_grid_steps(grid, delta)]

        with tqdm(total=len(futures), desc="Downloading Nodes") as pbar:
            for future in futures:
                lat_lons = future.result()
                nodes.extend(lat_lons)
                pbar.update(1)

    return nodes, cache, cache_file


if __name__ == '__main__':
    args = parse_options()
    with open(args.cookies_path, 'r') as f:
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
