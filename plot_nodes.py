#! /usr/bin/env python3

import pandas as pd
import plotly.express as px
import utils

style  = utils.load_parameters()['map_style']
cities = pd.read_csv("nodes.csv")

fig = px.scatter_mapbox(
    cities,
    lat="lat",
    lon="lon",
    size="sz",
    size_max=6,
    hover_name="names",
    color="len_cat",
    zoom=14,
    height=1300,
)

fig.update_layout(mapbox_style=style)
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
fig.show()
