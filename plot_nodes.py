#! /usr/bin/env python3

import pandas as pd
import plotly.express as px
import utils

style = utils.load_parameters()["map_style"]
cities = pd.read_csv("nodes.csv")

# Calculate center point for better initial view
center_lat = cities["lat"].mean()
center_lon = cities["lon"].mean()

# The `names` field is per-node ("Street Name (node_id)"); the street is the text
# before the parenthetical. Count nodes per street so we can offer a filter that
# hides long streets (> 100 nodes).
MAX_NODES = 100
street = cities["names"].str.replace(r"\s*\(\d+\)\s*$", "", regex=True)
nodes_per_street = street.map(street.value_counts())
cities_filtered = cities[nodes_per_street <= MAX_NODES]

# Keep colors consistent between the two views regardless of which categories
# survive filtering.
category_orders = {"len_cat": sorted(cities["len_cat"].dropna().unique())}


def scatter_kwargs(df):
    return dict(
        data_frame=df,
        lat="lat",
        lon="lon",
        size="sz",
        size_max=6,  # Slightly smaller nodes
        hover_name="names",
        color="len_cat",
        category_orders=category_orders,
        zoom=12,  # Slightly zoomed out for better overview
        center={"lat": center_lat, "lon": center_lon},  # Center on data
    )


fig = px.scatter_map(**scatter_kwargs(cities))

# Append the filtered view's traces (hidden initially) so a button can toggle
# between the two without needing a server (Dash).
n_all = len(fig.data)
filtered_fig = px.scatter_map(**scatter_kwargs(cities_filtered))
for trace in filtered_fig.data:
    trace.visible = False
    fig.add_trace(trace)
n_filtered = len(filtered_fig.data)

visible_all = [True] * n_all + [False] * n_filtered
visible_filtered = [False] * n_all + [True] * n_filtered

# Configure map style and layout for better responsiveness
fig.update_layout(
    mapbox_style="open-street-map",  # Changed to OpenStreetMap for less bright theme
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
