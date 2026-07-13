#! /usr/bin/env python3

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import utils

style = utils.load_parameters()["map_style"]
cities = pd.read_csv("nodes.csv")

# Calculate center point for better initial view
center_lat = cities["lat"].mean()
center_lon = cities["lon"].mean()

# `nodes.csv` contains only the *to-do* (incomplete) nodes. Newer downloads also
# carry per-street metadata (street id, total node count, unique node id) which
# lets us show useful hover info: how many nodes a street has and % completed.
HAS_STATS = {"street_id", "street_nodes", "node_id"}.issubset(cities.columns)

if HAS_STATS:
    # De-dup by node id so grid-boundary duplicates don't inflate the to-do count.
    uniq = cities.drop_duplicates(subset="node_id")
    todo = uniq.groupby("street_id")["node_id"].size()
    total = uniq.groupby("street_id")["street_nodes"].first()
    done = (total - todo).clip(lower=0)
    pct = (done / total * 100).where(total > 0, 0)

    cities["street_total"] = cities["street_id"].map(total)
    cities["street_todo"] = cities["street_id"].map(todo)
    cities["street_done"] = cities["street_id"].map(done)
    cities["street_pct"] = cities["street_id"].map(pct)

    # Count to-do nodes that sit on the exact same coordinate within one street.
    # CityStrides sometimes places several node ids at a single point (e.g. where
    # street segments join), so they render as one dot but count separately.
    stack = (
        uniq.groupby(["street_id", "lat", "lon"])["node_id"].size().rename("stack")
    )
    cities = cities.merge(stack, on=["street_id", "lat", "lon"], how="left")

    name_col = "street"
    # Declutter dense streets by the number of to-do nodes they still contribute.
    per_street = cities["street_todo"]
else:
    # Fall back to the older schema: derive the street name from `names` and count
    # rows per street name.
    cities["street"] = cities["names"].str.replace(r"\s*\(\d+\)\s*$", "", regex=True)
    name_col = "street"
    per_street = cities["street"].map(cities["street"].value_counts())

# The filter hides long streets (> 100 to-do nodes) to reduce clutter.
MAX_NODES = 100
cities_filtered = cities[per_street <= MAX_NODES]

# Keep colors consistent between the two views regardless of which categories
# survive filtering.
category_orders = {"len_cat": sorted(cities["len_cat"].dropna().unique())}

if HAS_STATS:
    hover_data = ["street_total", "street_done", "street_pct"]
    hovertemplate = (
        "<b>%{hovertext}</b><br>"
        "Nodes in street: %{customdata[0]}<br>"
        "Done: %{customdata[1]} / %{customdata[0]} (%{customdata[2]:.1f}%)"
        "<extra></extra>"
    )
else:
    hover_data = []
    hovertemplate = None


def scatter_kwargs(df):
    return dict(
        data_frame=df,
        lat="lat",
        lon="lon",
        size="sz",
        size_max=6,  # Slightly smaller nodes
        hover_name=name_col,
        custom_data=hover_data,
        color="len_cat",
        category_orders=category_orders,
        zoom=12,  # Slightly zoomed out for better overview
        center={"lat": center_lat, "lon": center_lon},  # Center on data
    )


def stacked_overlay(df):
    """A red, enlarged marker (with the count in its center) for every location
    where more than one to-do node is hidden behind a single dot."""
    if not HAS_STATS or "stack" not in df:
        return []
    s = df[df["stack"] > 1].sort_values("stack", ascending=False)
    s = s.drop_duplicates(subset=["lat", "lon"])  # one marker per visible dot
    if s.empty:
        return []
    # Color by how many to-do nodes are stacked: 2=yellow, 3=orange, 4+=red.
    colors = s["stack"].map(lambda n: "gold" if n == 2 else "orange" if n == 3 else "red")
    return [
        go.Scattermap(
            lat=s["lat"],
            lon=s["lon"],
            mode="markers+text",
            marker=dict(size=18, color=colors.tolist()),
            text=s["stack"].astype(int).astype(str),
            textfont=dict(size=11, color="black"),
            textposition="middle center",
            name="stacked to-do nodes",
            customdata=s[["street", "stack"]].to_numpy(),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "%{customdata[1]} to-do nodes stacked on this spot"
                "<extra></extra>"
            ),
        )
    ]


def build_layer(df):
    """Base per-node scatter plus the stacked-node overlay for one dataframe."""
    layer = px.scatter_map(**scatter_kwargs(df))
    if hovertemplate:
        layer.update_traces(hovertemplate=hovertemplate)
    return list(layer.data) + stacked_overlay(df)


all_traces = build_layer(cities)
filtered_traces = build_layer(cities_filtered)

fig = go.Figure()
for trace in all_traces:
    fig.add_trace(trace)
# Append the filtered view's traces (hidden initially) so a button can toggle
# between the two without needing a server (Dash).
for trace in filtered_traces:
    trace.visible = False
    fig.add_trace(trace)

n_all = len(all_traces)
n_filtered = len(filtered_traces)
visible_all = [True] * n_all + [False] * n_filtered
visible_filtered = [False] * n_all + [True] * n_filtered

# Configure map style and layout for better responsiveness
fig.update_layout(
    map={
        # Leave style unset (default basemap) to match the original appearance.
        "center": {"lat": center_lat, "lon": center_lon},
        "zoom": 12,
    },
    margin={"r": 5, "t": 30, "l": 5, "b": 5},  # Small margins
    showlegend=True,
    autosize=True,  # Enable responsive sizing
    height=875,  # Increased by 25% from 700
    title={
        "text": "City Strides Node Plot",
        "x": 0.5,
        "xanchor": "center",
        "font": {"size": 16},
    },
    updatemenus=[
        dict(
            type="buttons",
            x=0.01,
            xanchor="left",
            y=0.99,
            yanchor="top",
            showactive=True,
            buttons=[
                dict(
                    label=f"Hide streets > {MAX_NODES} nodes",
                    method="update",
                    args=[{"visible": visible_filtered}],  # pressed: filtered
                    args2=[{"visible": visible_all}],  # released: all
                ),
            ],
        )
    ],
)

# Enable zoom, pan, and other interactive controls
config = {
    "displayModeBar": True,  # Show the toolbar
    "displaylogo": False,  # Hide plotly logo
    "modeBarButtonsToAdd": ["pan2d", "select2d", "lasso2d", "resetScale2d"],
    "scrollZoom": True,  # Enable scroll to zoom
    "doubleClick": "reset",  # Double-click to reset view
    "showTips": True,  # Show helpful tips
    "responsive": True,  # Make plot responsive to window size
    "toImageButtonOptions": {
        "format": "png",
        "filename": "node_plot",
        "height": 600,
        "width": 1000,
        "scale": 2,
    },
}

# Show the plot with the interactive configuration
fig.show(config=config)
