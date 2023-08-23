#! /usr/bin/env python3

import pandas as pd
import plotly.express as px

style = "stamen-terrain"

cities = pd.read_csv("nodes.csv")

color_map = {"a": "red", "b": "orange", "c": "yellow", "d": "gray"}

fig = px.scatter_mapbox(
    cities,
    lat="lat",
    lon="lon",
    size="sz",
    size_max=6,
    hover_name="names",
    color="len_cat",
    # color_discrete_map=color_map,
    zoom=14,
    height=1300,
)
# 'open-street-map', 'white-bg', 'carto-positron',
# 'carto-darkmatter', 'stamen-terrain', 'stamen-toner', 'stamen-watercolor'
fig.update_layout(mapbox_style=style)
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
fig.show()
