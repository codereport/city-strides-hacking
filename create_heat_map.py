#!/usr/bin/env python3

"""Build one interactive heat map from one or more city datasets."""

import argparse
import csv
import json
from collections import defaultdict
from itertools import chain
from math import sqrt
from pathlib import Path

import pandas as pd
import plotly.express as px
import yaml
from geopy.distance import geodesic
from tqdm import tqdm

ROOT = Path(__file__).resolve().parent
NODE_COLUMNS = ["lat", "lon", "sz", "names", "len_cat"]

# City aliases used by CityStrides CSV filenames.
CITY_ALIASES = {
    "aarhus": "aarhus_kommune",
    "copenhagen": "københavns_kommune",
}


def normalized_city_name(city: str) -> str:
    return city.lower().replace(" ", "_").replace("-", "_")


def citystrides_city_name(city: str) -> str:
    normalized = normalized_city_name(city)
    return CITY_ALIASES.get(normalized, normalized)


def load_settings(path: Path) -> dict:
    defaults = {
        "map_style": "open-street-map",
        "heat_map_max_length": 1.0,
        "heat_map_exclude_csnodes": False,
    }
    if not path.exists():
        print(f"ℹ {path.name} not found; using heat-map defaults")
        return defaults

    with path.open(encoding="utf-8") as handle:
        supplied = yaml.safe_load(handle) or {}
    if not isinstance(supplied, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return defaults | supplied


def load_city_data(city: str) -> dict:
    path = ROOT / "data" / f"{city}.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def node_dictionary(data: dict) -> dict[int, tuple[float, float]]:
    return {
        element["id"]: (float(element["lat"]), float(element["lon"]))
        for element in data["elements"]
        if element["type"] == "node"
    }


def street_dictionary(data: dict) -> dict[str, list[list[int]]]:
    streets = defaultdict(list)
    for element in data["elements"]:
        if element["type"] != "way":
            continue
        name = element.get("tags", {}).get("name", "unnamed")
        streets[name].append(element["nodes"])
    return streets


def distance_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Retain the inexpensive distance approximation used by the old pipeline."""

    dx = b[0] - a[0]
    dy = b[1] - a[1]
    return sqrt(dx * dx + dy * dy) * 111


def total_distance_km(
    paths: list[list[int]], nodes: dict[int, tuple[float, float]]
) -> float:
    return sum(
        distance_km(nodes[a], nodes[b])
        for path in paths
        for a, b in zip(path, path[1:])
        if a in nodes and b in nodes
    )


def point_bucket(point: tuple[float, float]) -> tuple[float, float]:
    return round(point[0], 3), round(point[1], 3)


def load_citystrides_points(path: Path) -> dict:
    points = defaultdict(set)
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.reader(handle):
            if not row or row[0] == "lat":
                continue
            point = float(row[0]), float(row[1])
            points[point_bucket(point)].add(point)
    return points


def is_close_to_citystrides_node(
    points: dict,
    point: tuple[float, float],
    threshold_km: float = 0.01,
) -> bool:
    nearby = points.get(point_bucket(point), ())
    return bool(nearby) and min(geodesic(point, other).km for other in nearby) < threshold_km


def find_citystrides_file(city: str) -> Path | None:
    normalized = normalized_city_name(city)
    candidates = [
        ROOT / "csnodes" / f"{citystrides_city_name(city)}.csv",
        ROOT / "csnodes" / f"{normalized}.csv",
        ROOT / "csnodes" / f"{normalized}_kommune.csv",
    ]
    return next((path for path in candidates if path.exists()), None)


def process_city_data(city: str, settings: dict) -> list[list]:
    """Return the short-street nodes that should appear for one city."""

    print(f"Processing {city}...")
    data = load_city_data(city)
    nodes = node_dictionary(data)
    streets = street_dictionary(data)

    lengths_by_node = {}
    for paths in streets.values():
        length = total_distance_km(paths, nodes)
        for node_id in set(chain.from_iterable(paths)):
            lengths_by_node[node_id] = length

    citystrides_file = find_citystrides_file(city)
    citystrides_points = {}
    if citystrides_file:
        citystrides_points = load_citystrides_points(citystrides_file)
        print(f"  ✓ CityStrides targets: {citystrides_file.relative_to(ROOT)}")
    else:
        print("  ℹ No CityStrides target CSV found")

    max_length = float(settings["heat_map_max_length"])
    filter_to_citystrides = bool(settings["heat_map_exclude_csnodes"])
    rows = []

    for element in tqdm(data["elements"], desc=f"  Selecting {city} nodes"):
        if element["type"] != "node" or element["id"] not in lengths_by_node:
            continue

        length = lengths_by_node[element["id"]]
        if length >= max_length:
            continue

        point = float(element["lat"]), float(element["lon"])
        if (
            filter_to_citystrides
            and citystrides_file
            and not is_close_to_citystrides_node(citystrides_points, point)
        ):
            continue

        rows.append(
            [point[0], point[1], 2, f"Name: {element['id']} ({city})", length]
        )

    print(
        f"  ✓ {len(streets):,} streets, {len(nodes):,} OSM nodes, "
        f"{len(rows):,} heat-map nodes"
    )
    return rows


def write_nodes_csv(rows: list[list], path: Path) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=NODE_COLUMNS)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return frame


def original_data_json(frame: pd.DataFrame) -> str:
    data = {
        column: json.loads(frame[column].to_json(orient="values"))
        for column in NODE_COLUMNS
    }
    # Prevent a malicious or unusual OSM name from closing the script element.
    return json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")


CUSTOM_PAGE = """
<style>
    body {
        margin: 10px;
        font-family: Arial, sans-serif;
        background-color: #f8f9fa;
    }
    .plotly-graph-div {
        border: 2px solid #e1e5e9;
        border-radius: 8px;
        background-color: white;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        height: 100vh !important;
        max-height: 860px !important;
        min-height: 500px !important;
    }
    .plotly-graph-div .js-plotly-plot,
    .plotly-graph-div .plotly,
    .plotly-graph-div > div,
    .plotly-graph-div .svg-container,
    .plotly-graph-div .main-svg {
        width: 100% !important;
        height: 100% !important;
    }
    .controls-info {
        margin-bottom: 15px;
        padding: 12px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 6px;
        font-size: 14px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    @media (max-width: 768px) {
        .plotly-graph-div { height: 70vh !important; min-height: 400px !important; }
        .controls-info { font-size: 12px; padding: 8px; }
        body { margin: 5px; }
    }
    .modebar {
        background: rgba(255,255,255,0.9) !important;
        border: 1px solid #ddd !important;
        border-radius: 4px !important;
    }
</style>
<script>
    window.addEventListener('resize', function() {
        document.querySelectorAll('.js-plotly-plot').forEach(function(plot) {
            Plotly.Plots.resize(plot);
        });
    });

    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(filterByLength, 500);
    });

    function filterByLength() {
        const maxLength = parseFloat(document.getElementById('maxLengthFilter').value);
        const filtered = {lat: [], lon: [], size: [], color: [], hovertext: []};

        for (let i = 0; i < window.originalData.lat.length; i++) {
            if (window.originalData.len_cat[i] <= maxLength) {
                filtered.lat.push(window.originalData.lat[i]);
                filtered.lon.push(window.originalData.lon[i]);
                filtered.size.push(window.originalData.sz[i]);
                filtered.color.push(window.originalData.len_cat[i]);
                filtered.hovertext.push(window.originalData.names[i]);
            }
        }

        Plotly.restyle('heat-map-div', {
            lat: [filtered.lat],
            lon: [filtered.lon],
            'marker.size': [filtered.size],
            'marker.color': [filtered.color],
            hovertext: [filtered.hovertext]
        }, 0);
    }
</script>
"""

CONTROLS = """
<div class="controls-info">
    <strong>🗺️ Interactive Heat Map Controls</strong> | Max Street Length:
    <select id="maxLengthFilter" onchange="filterByLength()" style="padding: 4px 8px; border-radius: 4px; border: 1px solid #ccc; margin-left: 8px;">
        <option value="0.5" selected>0.5 km</option>
        <option value="1">1.0 km</option>
        <option value="2">2.0 km</option>
    </select>
</div>
"""


def write_heat_map_html(frame: pd.DataFrame, map_style: str, output: Path) -> None:
    if frame.empty:
        raise ValueError("No nodes matched the configured heat-map filters")

    figure = px.scatter_map(
        frame,
        lat="lat",
        lon="lon",
        size="sz",
        size_max=10,
        hover_name="names",
        color="len_cat",
        zoom=12,
        center={"lat": frame["lat"].mean(), "lon": frame["lon"].mean()},
        map_style=map_style,
    )
    figure.update_layout(
        margin={"r": 5, "t": 30, "l": 5, "b": 5},
        showlegend=True,
        autosize=True,
        height=None,
        title={
            "text": "City Strides Heat Map",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 16},
        },
    )
    config = {
        "displayModeBar": True,
        "displaylogo": False,
        "modeBarButtonsToAdd": ["pan2d", "select2d", "lasso2d", "resetScale2d"],
        "scrollZoom": True,
        "doubleClick": "reset",
        "showTips": True,
        "responsive": True,
        "toImageButtonOptions": {
            "format": "png",
            "filename": "heat_map",
            "height": 600,
            "width": 1000,
            "scale": 2,
        },
    }

    html = figure.to_html(
        include_plotlyjs="cdn", config=config, div_id="heat-map-div"
    )
    data_script = f"<script>window.originalData = {original_data_json(frame)};</script>"
    html = html.replace("</head>", f"{CUSTOM_PAGE}\n{data_script}\n</head>")
    html = html.replace("<body>", f"<body>\n{CONTROLS}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create one interactive heat map from one or more cities"
    )
    parser.add_argument("cities", nargs="+", help="city dataset names")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "parameters.yaml",
        help="heat-map YAML settings (default: parameters.yaml)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="output HTML path (default: heat_maps/<cities>.html)",
    )
    parser.add_argument(
        "--nodes-output",
        type=Path,
        default=ROOT / "nodes.csv",
        help="intermediate node CSV path (default: nodes.csv)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cities = [normalized_city_name(city) for city in args.cities]
    missing = [city for city in cities if not (ROOT / "data" / f"{city}.json").exists()]
    if missing:
        print(f"✗ Missing city data: {', '.join(missing)}")
        return 1

    try:
        settings = load_settings(args.config)
        rows = [
            row
            for city in cities
            for row in process_city_data(city, settings)
        ]
        frame = write_nodes_csv(rows, args.nodes_output)
        output = args.output or ROOT / "heat_maps" / f"{'_'.join(cities)}.html"
        write_heat_map_html(frame, settings["map_style"], output)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"✗ Could not create heat map: {error}")
        return 1

    print(f"✓ Created {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
