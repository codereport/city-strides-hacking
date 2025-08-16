#! /usr/bin/env python3

import pandas as pd
import plotly.express as px
import utils

style = utils.load_parameters()["map_style"]
cities = pd.read_csv("nodes.csv")

# Calculate center point for better initial view
center_lat = cities["lat"].mean()
center_lon = cities["lon"].mean()

fig = px.scatter_map(
    cities,
    lat="lat",
    lon="lon",
    size="sz",
    size_max=6,  # Slightly smaller nodes
    hover_name="names",
    color="len_cat",
    zoom=12,  # Slightly zoomed out for better overview
    center={"lat": center_lat, "lon": center_lon},  # Center on data
)

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
