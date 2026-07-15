#!/usr/bin/env python3
"""Compatibility entry point for the canonical planner OSM downloader."""

from _planner_entrypoint import run_planner_script


if __name__ == "__main__":
    run_planner_script("get_data_for_new_city.py")
