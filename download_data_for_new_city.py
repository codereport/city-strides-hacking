#!/usr/bin/env python3

import argparse
import json
import os
import requests
import shutil
import sys
from pathlib import Path
from urllib.parse import quote


# City name aliases mapping - maps common names to their official City Strides names
# Add aliases manually as needed
CITY_ALIASES = {
    "aarhus": "aarhus_kommune",
    "copenhagen": "københavns_kommune",
}


def find_city_alias(user_input):
    """
    Try to find the official city name for a user input.
    Returns tuple of (official_name, display_name) or (None, None) if not found.
    """
    normalized_input = user_input.lower().replace(" ", "_").replace("-", "_")

    # Check direct alias mapping
    if normalized_input in CITY_ALIASES:
        official_name = CITY_ALIASES[normalized_input]
        print(f"Found alias mapping: '{user_input}' -> '{official_name}'")
        return official_name, user_input

    # No alias found, return None
    return None, None


def find_osm_relation(city_name, original_name=None):
    """
    Search for a city on OpenStreetMap using Nominatim API.
    Returns a list of potential matches with their relation IDs.

    Args:
        city_name: The city name to search for
        original_name: The original user input (for display purposes)
    """
    display_name = original_name if original_name else city_name
    print(f"Searching for '{display_name}' on OpenStreetMap...")

    # Use Nominatim API to search for the city
    nominatim_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city_name,
        "format": "json",
        "addressdetails": 1,
        "extratags": 1,
        "limit": 10,
        "polygon_geojson": 1,
    }

    headers = {"User-Agent": "CityStrides-Heatmap-Generator/1.0"}

    try:
        response = requests.get(nominatim_url, params=params, headers=headers)
        response.raise_for_status()
        results = response.json()

        # Filter for administrative boundaries (cities, towns, etc.)
        city_results = []
        for result in results:
            if result.get("osm_type") == "relation" and result.get("type") in [
                "administrative",
                "city",
                "town",
                "municipality",
            ]:
                city_results.append(
                    {
                        "relation_id": result["osm_id"],
                        "display_name": result["display_name"],
                        "type": result.get("type", "unknown"),
                        "admin_level": result.get("extratags", {}).get(
                            "admin_level", "unknown"
                        ),
                    }
                )

        return city_results

    except requests.RequestException as e:
        print(f"Error searching for city: {e}")
        return []


def build_overpass_query(relation_id, query_type="named"):
    """
    Build an Overpass API query for fetching street data.

    Args:
        relation_id: OpenStreetMap relation ID for the city
        query_type: 'named' for only named streets, 'all' for all streets
    """
    if query_type == "named":
        # Query for named streets only (similar to Prince George example)
        query = f"""[out:json];
rel({relation_id});
map_to_area;
(
  way(area)
    ['name'] // this is essential (only want named roads)
    ['highway']
    // everything below is to exclude certain types of "highways"
    ['highway' !~ 'path']
    ['highway' !~ 'steps']
    ['highway' !~ 'motorway']
    ['highway' !~ 'motorway_link']
    ['highway' !~ 'raceway']
    ['highway' !~ 'bridleway']
    ['highway' !~ 'proposed']
    ['highway' !~ 'construction']
    ['highway' !~ 'elevator']
    ['highway' !~ 'bus_guideway']
    ['highway' !~ 'footway']
    ['highway' !~ 'cycleway']
    ['highway' !~ 'trunk']
    ['foot' !~ 'no']
    ['access' !~ 'private']
    ['access' !~ 'no'];
  >;
);
out;"""
    else:
        # Query for all streets (similar to Etobicoke example)
        query = f"""[out:json];
rel({relation_id});
map_to_area;
(
  way(area)
    ['highway']
    // everything below is to exclude certain types of "highways"
    ['foot' !~ 'no']
    ['access' !~ 'private']
    ['access' !~ 'no'];
  >;
);
out;"""

    return query


def fetch_overpass_data(query):
    """
    Execute an Overpass API query and return the JSON data.
    """
    print("Executing Overpass API query...")

    overpass_url = "https://overpass-api.de/api/interpreter"
    headers = {"User-Agent": "CityStrides-Heatmap-Generator/1.0"}

    try:
        response = requests.post(overpass_url, data=query, headers=headers, timeout=300)
        response.raise_for_status()

        # Parse JSON response
        data = response.json()
        print(f"✓ Retrieved {len(data.get('elements', []))} elements from Overpass API")
        return data

    except requests.RequestException as e:
        print(f"Error fetching data from Overpass API: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return None


def save_city_data(city_name, data, original_name=None):
    """
    Save the fetched data to the data directory.
    Uses original_name for filename if provided, otherwise uses city_name.
    """
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Use original name for filename if provided, otherwise use city_name
    filename = original_name if original_name else city_name
    filename = filename.lower().replace(" ", "_").replace("-", "_")
    output_file = data_dir / f"{filename}.json"

    try:
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)
        print(f"✓ Data saved to {output_file}")
        return True
    except IOError as e:
        print(f"Error saving data: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download OpenStreetMap data for a new city"
    )
    parser.add_argument("city_name", help="Name of the city to download data for")
    parser.add_argument(
        "--relation-id", type=int, help="Specific OpenStreetMap relation ID to use"
    )
    parser.add_argument(
        "--query-type",
        choices=["named", "all"],
        default="named",
        help="Type of streets to query: 'named' (default) or 'all'",
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite existing data file if it exists"
    )

    args = parser.parse_args()

    # Try to find alias for the city name
    official_city_name, user_city_name = find_city_alias(args.city_name)

    # Normalize the user input for filename
    normalized_user_input = args.city_name.lower().replace(" ", "_").replace("-", "_")

    # Determine which name to use for search and which for filename
    if official_city_name:
        # Found an alias or existing city
        search_name = official_city_name
        filename_base = normalized_user_input
        print(
            f"Using official name '{search_name}' for search, will save as '{filename_base}'"
        )
    else:
        # No alias found, use original input
        search_name = normalized_user_input
        filename_base = normalized_user_input

    # Check if data already exists (check both possible filenames)
    data_file = Path(__file__).parent / "data" / f"{filename_base}.json"
    alt_data_file = (
        Path(__file__).parent / "data" / f"{search_name}.json"
        if search_name != filename_base
        else None
    )

    if data_file.exists() and not args.force:
        print(
            f"Data file for '{filename_base}' already exists. Use --force to overwrite."
        )
        print(f"To generate a heatmap, run: python3 create_heat_map.py {filename_base}")
        return True
    elif alt_data_file and alt_data_file.exists() and not data_file.exists():
        # We have data with the official name but not the user's preferred name
        # Copy the official data to the user's preferred filename
        try:
            shutil.copy2(alt_data_file, data_file)
            print(
                f"Found existing data for '{search_name}', copied to '{filename_base}.json'"
            )
            print(
                f"To generate a heatmap, run: python3 create_heat_map.py {filename_base}"
            )
            return True
        except IOError as e:
            print(f"Warning: Could not copy {alt_data_file} to {data_file}: {e}")
            print(
                f"Data exists as '{search_name}.json' but couldn't create '{filename_base}.json'"
            )
            print(
                f"To generate a heatmap, run: python3 create_heat_map.py {search_name}"
            )
            return True
    elif (
        alt_data_file
        and alt_data_file.exists()
        and data_file.exists()
        and not args.force
    ):
        print(
            f"Data files for both '{filename_base}' and '{search_name}' already exist. Use --force to overwrite."
        )
        print(f"To generate a heatmap, run: python3 create_heat_map.py {filename_base}")
        return True

    relation_id = args.relation_id

    # If no relation ID provided, search for the city
    if not relation_id:
        # Use the search name (official name if alias found) for the actual search
        search_city_name = search_name if official_city_name else args.city_name
        city_results = find_osm_relation(search_city_name, args.city_name)

        if not city_results:
            print(f"No administrative boundaries found for '{args.city_name}'")
            if official_city_name:
                print(f"(Searched using alias: '{search_city_name}')")
            print("Please provide a specific relation ID using --relation-id")
            return False

        if len(city_results) == 1:
            relation_id = city_results[0]["relation_id"]
            print(
                f"Found: {city_results[0]['display_name']} (Relation ID: {relation_id})"
            )
        else:
            print(f"Found {len(city_results)} potential matches:")
            for i, result in enumerate(city_results):
                print(
                    f"  {i+1}. {result['display_name']} (ID: {result['relation_id']}, "
                    f"Type: {result['type']}, Admin Level: {result['admin_level']})"
                )

            try:
                choice = int(input(f"\nSelect option (1-{len(city_results)}): ")) - 1
                if 0 <= choice < len(city_results):
                    relation_id = city_results[choice]["relation_id"]
                    print(f"Selected: {city_results[choice]['display_name']}")
                else:
                    print("Invalid selection")
                    return False
            except (ValueError, KeyboardInterrupt):
                print("Invalid input or cancelled")
                return False

    # Build and execute Overpass query
    query = build_overpass_query(relation_id, args.query_type)
    print(f"Using relation ID: {relation_id}")
    print(f"Query type: {args.query_type}")

    # Fetch data
    data = fetch_overpass_data(query)
    if not data:
        return False

    # Save data using the user's original input as filename
    if not save_city_data(search_name, data, filename_base):
        return False

    print(f"\n✓ Successfully downloaded data for {args.city_name}")
    if official_city_name:
        print(f"   (Used official name '{search_name}' for search)")
    print(f"   Saved as: {filename_base}.json")
    print(f"Next steps:")
    print(f"  1. Generate heatmap: python3 create_heat_map.py {filename_base}")
    print(f"  2. Optionally add to download_node_csv.py for future processing")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
