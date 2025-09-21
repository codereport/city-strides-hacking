#!/usr/bin/env python3

import argparse
import shutil
import subprocess
import sys
import os
from pathlib import Path
from itertools import chain
from tqdm import tqdm
import utils

# City name aliases mapping - maps common names to their official City Strides names
# Keep this in sync with add_new_city.py
CITY_ALIASES = {
    "aarhus": "aarhus_kommune",
    "copenhagen": "københavns_kommune",
}


def resolve_city_name(user_input: str) -> str:
    """
    Resolve a user input city name to the official name used for files.
    Returns the official name if an alias exists, otherwise returns the input unchanged.
    """
    normalized_input = user_input.lower().replace(" ", "_").replace("-", "_")
    return CITY_ALIASES.get(normalized_input, user_input)


def process_city_data(city_name):
    """Process data for a single city and return nodes to include in heat map"""
    print(f"Processing {city_name}...")

    try:
        obj = utils.load_json(city_name)
    except FileNotFoundError:
        print(f"✗ Error: Could not find data/{city_name}.json")
        return []

    nodes = utils.node_dictionary(obj)
    streets = utils.street_dictionary(obj)

    # Calculate street lengths (same logic as generate_heat_map.py)
    lengths = {}
    for s, n in streets.items():
        tl = utils.total_distance_of_paths(n, nodes)
        print(
            f"  {s}, Number of nodes: {len(set(chain(*n)))}, Length: {round(tl, 3)}"
        )
        for node in set(chain(*n)):
            lengths[node] = tl

    print(f"  # of Streets: {len(streets)}")
    print(
        f"  # of Nodes From Streets: {sum(len(s) for s in streets.values())}")
    print(
        f"  # of Nodes From Query: {len([e for e in obj['elements'] if e['type'] == 'node'])}"
    )

    # Determine which nodes to include (same logic as generate_heat_map.py)
    nodes_to_include = []

    # Resolve city name to handle aliases (e.g., copenhagen -> københavns_kommune)
    official_city_name = resolve_city_name(city_name)

    # Try different naming patterns for csnodes file
    csnodes_file = Path(
        __file__).parent / "csnodes" / f"{official_city_name}.csv"
    if not csnodes_file.exists():
        # Try with the original city name if official name didn't work
        csnodes_file = Path(__file__).parent / "csnodes" / f"{city_name}.csv"
        if not csnodes_file.exists():
            # Try with _kommune suffix (for cities like aarhus)
            csnodes_file = Path(
                __file__).parent / "csnodes" / f"{city_name}_kommune.csv"

    remove_nodes = os.path.exists(csnodes_file)
    if remove_nodes:
        points_done = utils.load_completed_csnodes(csnodes_file)
        print(f"  ✓ Found csnodes file: {csnodes_file}")
        print(f"  ✓ Loaded {len(points_done)} completed csnode groups")
    else:
        print(f"  ℹ No csnodes file found for {city_name}")

    max_len = utils.load_parameters()["heat_map_max_length"]
    exclude_csnodes = utils.load_parameters()["heat_map_exclude_csnodes"]

    for e in tqdm(obj["elements"], desc=f"Processing {city_name} nodes"):
        if e["type"] == "node":
            id = e["id"]
            if id in lengths:  # Only include nodes that are part of streets
                l = lengths[id]
                point = (float(e["lat"]), float(e["lon"]))
                if (l < max_len) and (not remove_nodes or not exclude_csnodes
                                      or points_done and utils.is_close(
                                          points_done, point, 0.01)):
                    nodes_to_include.append([
                        float(e["lat"]),
                        float(e["lon"]),
                        2,
                        f'"Name: {id} ({city_name})"',
                        l,
                    ])

    print(f"  ✓ Included {len(nodes_to_include)} nodes from {city_name}")
    return nodes_to_include


def generate_fused_heat_map(cities):
    """Generate heat map data for multiple cities combined"""
    print("Generating fused heat map data...")

    all_nodes = []

    # Process each city and combine the nodes
    for city in cities:
        city_nodes = process_city_data(city)
        all_nodes.extend(city_nodes)

    print(f"✓ Total nodes across all cities: {len(all_nodes)}")

    # Write combined nodes to CSV
    utils.write_nodes_csv(all_nodes)
    print("✓ Written combined nodes to nodes.csv")


def run_script(script_name):
    """Run a Python script and handle errors"""
    try:
        result = subprocess.run([sys.executable, script_name],
                                capture_output=True,
                                text=True,
                                check=True)
        print(f"✓ Successfully ran {script_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error running {script_name}:")
        print(f"  stdout: {e.stdout}")
        print(f"  stderr: {e.stderr}")
        return False


def move_heat_map(cities):
    """Move heat_map.html to heat_maps/{cities}.html"""
    source = Path(__file__).parent / "heat_map.html"
    dest_dir = Path(__file__).parent / "heat_maps"

    # Create a filename from the city list
    cities_str = "_".join(cities)
    dest = dest_dir / f"{cities_str}.html"

    if not source.exists():
        print(f"✗ heat_map.html not found")
        return False

    if not dest_dir.exists():
        dest_dir.mkdir(exist_ok=True)

    try:
        shutil.move(str(source), str(dest))
        print(f"✓ Moved heat_map.html to heat_maps/{cities_str}.html")
        return True
    except Exception as e:
        print(f"✗ Error moving file: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Create a fused heat map for multiple cities")
    parser.add_argument(
        "cities",
        nargs="+",
        help="List of city names (e.g., 'tiny midland gravenhurst')",
    )

    args = parser.parse_args()
    cities = [city.lower() for city in args.cities]

    print(f"Creating fused heat map for: {', '.join(cities)}")
    print("=" * 50)

    # Check that all city data files exist
    missing_cities = []
    for city in cities:
        data_file = Path(__file__).parent / "data" / f"{city}.json"
        if not data_file.exists():
            missing_cities.append(city)

    if missing_cities:
        print(
            f"✗ Error: Missing data files for cities: {', '.join(missing_cities)}"
        )
        sys.exit(1)

    # Step 1: Generate fused heat map data (replaces generate_heat_map.py)
    try:
        generate_fused_heat_map(cities)
    except Exception as e:
        print(f"✗ Error generating fused heat map data: {e}")
        sys.exit(1)

    # Step 2: Run generate_html.py
    if not run_script("generate_html.py"):
        sys.exit(1)

    # Step 3: Move heat_map.html to heat_maps/
    if not move_heat_map(cities):
        sys.exit(1)

    print("=" * 50)
    cities_str = "_".join(cities)
    print(f"🎉 Fused heat map for {', '.join(cities)} created successfully!")
    print(f"📍 Location: heat_maps/{cities_str}.html")


if __name__ == "__main__":
    main()
