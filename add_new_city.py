#!/usr/bin/env python3

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import requests
from tqdm import tqdm


# City name aliases mapping - maps common names to their official City Strides names
# Add aliases manually as needed
CITY_ALIASES = {
    "aarhus": "aarhus_kommune",
    "copenhagen": "københavns_kommune",
}


def find_city_alias(user_input: str) -> Tuple[Optional[str], Optional[str]]:
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


def load_cookies() -> Dict[str, str]:
    """Load cookies from cookies.json file"""
    cookies_file = Path(__file__).parent / "cookies.json"
    try:
        with open(cookies_file) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: cookies.json not found at {cookies_file}")
        print(
            "Please ensure cookies.json exists with your City Strides session cookies"
        )
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {cookies_file}")
        sys.exit(1)


def search_city_on_nominatim(city_name: str) -> Optional[Dict[str, Any]]:
    """
    Search for a city using Nominatim API to get preliminary information
    """
    print(f"Searching for '{city_name}' on OpenStreetMap...")

    nominatim_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": city_name,
        "format": "json",
        "addressdetails": 1,
        "extratags": 1,
        "limit": 10,
        "polygon_geojson": 1,
    }

    headers = {"User-Agent": "CityStrides-AddNewCity/1.0"}

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
                city_results.append(result)

        if not city_results:
            print(f"No administrative boundaries found for '{city_name}'")
            return None

        if len(city_results) == 1:
            selected = city_results[0]
            print(f"Found: {selected['display_name']}")
            return selected
        else:
            print(f"Found {len(city_results)} potential matches:")
            for i, result in enumerate(city_results):
                print(
                    f"  {i+1}. {result['display_name']} (Type: {result.get('type', 'unknown')})"
                )

            try:
                choice = int(input(f"\nSelect option (1-{len(city_results)}): ")) - 1
                if 0 <= choice < len(city_results):
                    selected = city_results[choice]
                    print(f"Selected: {selected['display_name']}")
                    return selected
                else:
                    print("Invalid selection")
                    return None
            except (ValueError, KeyboardInterrupt):
                print("Invalid input or cancelled")
                return None

    except requests.RequestException as e:
        print(f"Error searching for city: {e}")
        return None


def search_city_on_citystrides(
    city_name: str, cookies: Dict[str, str]
) -> Optional[Tuple[int, Dict[str, float]]]:
    """
    Search for a city on City Strides to get the city ID and bounding box.

    This function tries to find the city by making a search request to City Strides
    and parsing the response to extract the city ID and bounding box coordinates.

    Returns:
        Tuple of (city_id, bounding_box) where bounding_box is a dict with
        'nelng', 'nelat', 'swlng', 'swlat' keys, or None if not found
    """
    print(f"Searching for '{city_name}' on City Strides...")

    # Try to search for the city on City Strides
    search_url = "https://citystrides.com/cities"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Referer": "https://citystrides.com/",
    }

    try:
        # First, get the main cities page to look for the city
        response = requests.get(search_url, headers=headers, cookies=cookies)
        response.raise_for_status()

        # Look for the city name in the HTML response
        # This is a simplified approach - in reality, we might need to parse the HTML more carefully
        city_pattern = rf'href="/cities/(\d+)"[^>]*>.*?{re.escape(city_name)}.*?</a>'
        match = re.search(city_pattern, response.text, re.IGNORECASE)

        if match:
            city_id = int(match.group(1))
            print(f"Found city ID: {city_id}")

            # Now try to get the bounding box by accessing the city's node page
            # This simulates what happens when you go to the node search
            nodes_url = f"https://citystrides.com/cities/{city_id}/nodes"
            nodes_response = requests.get(nodes_url, headers=headers, cookies=cookies)
            nodes_response.raise_for_status()

            # Look for bounding box in the JavaScript or HTML
            # The bounding box might be in various formats, so we'll try multiple patterns
            bbox_patterns = [
                r'nelng["\']?\s*:\s*([+-]?\d+\.?\d*)',
                r'nelat["\']?\s*:\s*([+-]?\d+\.?\d*)',
                r'swlng["\']?\s*:\s*([+-]?\d+\.?\d*)',
                r'swlat["\']?\s*:\s*([+-]?\d+\.?\d*)',
            ]

            bbox = {}
            for i, pattern in enumerate(bbox_patterns):
                match = re.search(pattern, nodes_response.text)
                if match:
                    key = ["nelng", "nelat", "swlng", "swlat"][i]
                    bbox[key] = float(match.group(1))

            if len(bbox) == 4:
                print(f"Found bounding box: {bbox}")
                return city_id, bbox
            else:
                print("Could not extract complete bounding box from City Strides")
                return city_id, None
        else:
            print(f"Could not find '{city_name}' on City Strides cities page")
            return None

    except requests.RequestException as e:
        print(f"Error searching City Strides: {e}")
        return None


def estimate_bbox_from_nominatim(nominatim_result: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract bounding box from Nominatim result and convert to City Strides format
    """
    if "boundingbox" not in nominatim_result:
        raise ValueError("No bounding box found in Nominatim result")

    # Nominatim returns [south, north, west, east]
    bbox = nominatim_result["boundingbox"]
    south, north, west, east = map(float, bbox)

    return {"nelng": east, "nelat": north, "swlng": west, "swlat": south}


def format_city_name_for_enum(city_name: str) -> str:
    """
    Format city name for use in the City enum (uppercase, underscores)
    """
    return city_name.upper().replace(" ", "_").replace("-", "_")


def format_city_name_for_file(city_name: str) -> str:
    """
    Format city name for use in filenames (lowercase, underscores)
    """
    return city_name.lower().replace(" ", "_").replace("-", "_")


def update_download_node_csv(
    city_name: str, city_id: int, bbox: Dict[str, float], force: bool = False
):
    """
    Update download_node_csv.py to add the new city to the enum and grid
    """
    download_file = Path(__file__).parent / "download_node_csv.py"

    if not download_file.exists():
        print(f"Error: {download_file} not found")
        return False

    # Read the current file
    with open(download_file, "r") as f:
        content = f.read()

    enum_name = format_city_name_for_enum(city_name)

    # Check if the city already exists
    if enum_name in content:
        print(f"City {enum_name} already exists in download_node_csv.py")
        if not force:
            print("Use --force to update the existing entry")
            return True

    # Add to the City enum
    # Find the last entry in the enum (before the # fmt: on comment)
    enum_pattern = r"(class City\(str, Enum\):.*?)(# fmt: on)"
    enum_match = re.search(enum_pattern, content, re.DOTALL)

    if not enum_match:
        print("Error: Could not find City enum in download_node_csv.py")
        return False

    # Add new city entry
    new_city_line = f"    {enum_name:<12} = {city_id}  # 🌍\n"
    new_enum_content = enum_match.group(1) + new_city_line + enum_match.group(2)
    content = content.replace(enum_match.group(0), new_enum_content)

    # Add to CityGrids dictionary
    # Find the CityGrids dictionary
    grid_pattern = r"(CityGrids = \{.*?)(# fmt: on)"
    grid_match = re.search(grid_pattern, content, re.DOTALL)

    if not grid_match:
        print("Error: Could not find CityGrids dictionary in download_node_csv.py")
        return False

    # Add new grid entry
    new_grid_line = f"    City.{enum_name}:<spaces>CityGrid({bbox['nelng']}, {bbox['nelat']}, {bbox['swlng']}, {bbox['swlat']}),\n"
    # Calculate spacing to align with existing entries
    spaces_needed = max(0, 15 - len(enum_name))
    new_grid_line = new_grid_line.replace("<spaces>", " " * spaces_needed)

    new_grid_content = grid_match.group(1) + new_grid_line + grid_match.group(2)
    content = content.replace(grid_match.group(0), new_grid_content)

    # Write back to file
    try:
        with open(download_file, "w") as f:
            f.write(content)
        print(f"✓ Added {enum_name} to download_node_csv.py")
        return True
    except Exception as e:
        print(f"Error writing to download_node_csv.py: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Add a new city to the City Strides download system"
    )
    parser.add_argument("city_name", help="Name of the city to add")
    parser.add_argument(
        "--city-id", type=int, help="Specific City Strides city ID (if known)"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force update even if city already exists"
    )

    args = parser.parse_args()

    print(f"Adding new city: {args.city_name}")
    print("=" * 50)

    # Load cookies for City Strides API calls
    cookies = load_cookies()

    # Try to find alias for the city name
    official_city_name, user_city_name = find_city_alias(args.city_name)
    
    # Determine which name to use for City Strides search
    search_name = official_city_name if official_city_name else args.city_name
    display_name = args.city_name  # Always use original input for display

    city_id = args.city_id
    bbox = None

    # Step 1: Try to find city on City Strides
    if not city_id:
        result = search_city_on_citystrides(search_name, cookies)
        if result:
            city_id, bbox = result

    # Step 2: If not found on City Strides or no bbox, try Nominatim
    if not bbox:
        nominatim_result = search_city_on_nominatim(search_name)
        if nominatim_result:
            bbox = estimate_bbox_from_nominatim(nominatim_result)
            print(f"Using bounding box from Nominatim: {bbox}")
            if official_city_name:
                print(f"   (Used official name '{search_name}' for search)")

            # If we still don't have a city_id, we'll need to make an educated guess
            # or prompt the user to provide it
            if not city_id:
                print(
                    f"\nWarning: Could not automatically determine City Strides ID for '{display_name}'"
                )
                print("You can find the city ID by:")
                print("1. Going to citystrides.com")
                print("2. Searching for the city")
                print("3. Looking at the URL (e.g., /cities/12345)")

                try:
                    city_id = int(input("Please enter the City Strides city ID: "))
                except (ValueError, KeyboardInterrupt):
                    print("Invalid input or cancelled")
                    return False

    if not city_id or not bbox:
        print("Error: Could not determine city ID and/or bounding box")
        return False

    print(f"\nCity Information:")
    print(f"  Name: {display_name}")
    if official_city_name:
        print(f"  Official Name: {search_name}")
    print(f"  City ID: {city_id}")
    print(f"  Bounding Box: {bbox}")

    # Step 3: Update download_node_csv.py - use the search name (official name if available)
    city_name_for_enum = search_name
    if not update_download_node_csv(city_name_for_enum, city_id, bbox, args.force):
        return False

    print("\n" + "=" * 50)
    print(f"✓ Successfully added {display_name} to the system!")
    if official_city_name:
        print(f"   (Used official name '{search_name}' for City Strides integration)")
    print(f"\nNext steps:")
    file_name = format_city_name_for_file(display_name)
    print(
        f'  1. Download OpenStreetMap data: python3 download_data_for_new_city.py "{display_name}"'
    )
    print(
        f"  2. Download City Strides nodes: python3 download_node_csv.py cookies.json"
    )
    print(f"     (Select {format_city_name_for_enum(city_name_for_enum)} from the list)")
    print(f"  3. Generate heat map: python3 create_heat_map.py {file_name}")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
