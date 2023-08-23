#! /usr/bin/env python3

import requests
from enum import Enum
import sys
import argparse
from pathlib import Path
from dataclasses import dataclass, fields, asdict
from typing import Dict, Any
import json
from ast import literal_eval
import pandas as pd

NODES_FILE = Path(__file__).parent / "nodes.csv"

@dataclass
class Node:
    lat: float
    lon: float
    sz: int = 2
    names: str = ''
    len_cat: str = 'a'

class City(str, Enum):
    OLD_TORONTO = 38121  # 🇨🇦
    EAST_YORK   = 38114  # 🇨🇦
    YORK        = 38102  # 🇨🇦
    NORTH_YORK  = 38108  # 🇨🇦
    WROCLAW     = 191289 # 🇵🇱
    KRAKOW      = 190608 # 🇵🇱
    ROME        = 94322  # 🇮🇹
    VENICE      = 93031  # 🇮🇹
    FOLKESTONE  = 131165 # 🇬🇧
    MEAFORD     = 39015  # 🇨🇦
    ALL_TORONTO = 0      # 🇨🇦

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

def cache_filename(city: City):
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
    City.YORK:        CityGrid(-79.3829, 43.7206, -79.5560, 43.6424),
    City.WROCLAW:     CityGrid(17.078224311098552, 51.13988879756559,  17.00226573206399,  51.09263199227115 ),
    City.KRAKOW:      CityGrid(19.979436306324942, 50.08859858611942,  19.90053987336441,  50.034804024531525),
    City.ROME:        CityGrid(12.519622013860925, 41.91439535724936,  12.443743029831694, 41.85439499689079 ),
    City.VENICE:      CityGrid(12.357666134722393, 45.451386491714715, 12.316599314442499, 45.42077976598716 ),
    City.FOLKESTONE:  CityGrid(1.2028963028344322, 51.11176465501126,  1.1199095563368644, 51.05639602006997 ),
    City.MEAFORD:     CityGrid(-80.49028489574928, 44.754231277837675, -80.94388807383417, 44.44134084860639 ),
    City.OLD_TORONTO: CityGrid(-79.20, 43.8, -79.556, 43.61),
    City.NORTH_YORK:  CityGrid(-79.20, 43.8, -79.556, 43.61),
    City.EAST_YORK:   CityGrid(-79.20, 43.8, -79.556, 43.61),
    City.ALL_TORONTO: CityGrid(-79.20, 43.8, -79.556, 43.61)
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


def download_nodes_of_city(city: City, cookies: Dict[str, Any]):
    grid= CityGrids[city]

    nodes = []
    cache = set()
    cache_file = Path(__file__).parent / f"./cache/{cache_filename(city)}.csv"
    cache_file.touch()

    with open(cache_file, "r") as f:
        for line in f.read().splitlines():
            cache.add(CityGrid(*line.strip().split(',')))

    delta = 0.004 if city == City.VENICE else 0.02 if city == City.MEAFORD else 0.012

    for coordinates in make_grid_steps(grid, delta):
        if coordinates not in cache:
            params = { "city": city.value, **citygrid_to_str(coordinates) }
            response = requests.get(
                "https://citystrides.com/nodes.json",
                params=params,
                cookies=cookies
            )

            temp = parse_nodes(response.text)
            print(len(temp))
            if len(temp) == 0:
                cache.add(coordinates)
            nodes.extend(temp)

    return nodes, cache, cache_file


if __name__ == '__main__':
    args = parse_options()
    with open(args.cookies_path, 'r') as f:
        cookies = json.load(f)

    city = get_city_from_user()
    nodes, cache, cache_file = download_nodes_of_city(city, cookies)

    df = pd.DataFrame(nodes)
    df.to_csv(NODES_FILE, index=True)

    df = pd.DataFrame(cache)
    df.to_csv(cache_file, index=False, header=False)
