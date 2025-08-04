#!/usr/bin/env python3

import argparse
import shutil
import subprocess
import sys
import yaml
from pathlib import Path


def update_parameters_yaml(city_name):
    """Update the city field in parameters.yaml"""
    params_file = Path(__file__).parent / "parameters.yaml"
    
    with open(params_file, 'r') as f:
        params = yaml.safe_load(f)
    
    params['city'] = city_name
    
    with open(params_file, 'w') as f:
        yaml.safe_dump(params, f, default_flow_style=False)
    
    print(f"✓ Updated parameters.yaml with city: {city_name}")


def run_script(script_name):
    """Run a Python script and handle errors"""
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, check=True)
        print(f"✓ Successfully ran {script_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error running {script_name}:")
        print(f"  stdout: {e.stdout}")
        print(f"  stderr: {e.stderr}")
        return False


def move_heat_map(city_name):
    """Move heat_map.html to heat_maps/{city}.html"""
    source = Path(__file__).parent / "heat_map.html"
    dest_dir = Path(__file__).parent / "heat_maps"
    dest = dest_dir / f"{city_name}.html"
    
    if not source.exists():
        print(f"✗ heat_map.html not found")
        return False
    
    if not dest_dir.exists():
        dest_dir.mkdir(exist_ok=True)
    
    try:
        shutil.move(str(source), str(dest))
        print(f"✓ Moved heat_map.html to heat_maps/{city_name}.html")
        return True
    except Exception as e:
        print(f"✗ Error moving file: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Create a heat map for a city")
    parser.add_argument("city", help="City name (e.g., 'gravenhurst', 'toronto', etc.)")
    
    args = parser.parse_args()
    city_name = args.city.lower()
    
    print(f"Creating heat map for: {city_name}")
    print("=" * 50)
    
    # Step 1: Update parameters.yaml
    try:
        update_parameters_yaml(city_name)
    except Exception as e:
        print(f"✗ Error updating parameters.yaml: {e}")
        sys.exit(1)
    
    # Step 2: Run generate_heat_map.py
    if not run_script("generate_heat_map.py"):
        sys.exit(1)
    
    # Step 3: Run generate_html.py
    if not run_script("generate_html.py"):
        sys.exit(1)
    
    # Step 4: Move heat_map.html to heat_maps/
    if not move_heat_map(city_name):
        sys.exit(1)
    
    print("=" * 50)
    print(f"🎉 Heat map for {city_name} created successfully!")
    print(f"📍 Location: heat_maps/{city_name}.html")


if __name__ == "__main__":
    main()