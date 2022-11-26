import pandas as pd
import plotly.express as px

# TODO: https://plotly.com/python/lines-on-mapbox/
#       Update to "go" so I can do traces & markers at same time

# style = ("carto-darkmatter", "blue")
style = ("stamen-terrain", "red")

cities = pd.read_csv("nodes.csv")

fig = px.scatter_mapbox(
    cities,
    lat="lat",
    lon="lon",
    size="sz",
    size_max=11,
    hover_name="names",
    color_discrete_sequence=[style[1]],
    zoom=14,
    height=1300,
)
# 'open-street-map', 'white-bg', 'carto-positron',
# 'carto-darkmatter', 'stamen-terrain', 'stamen-toner', 'stamen-watercolor'
fig.update_layout(mapbox_style=style[0])
fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
fig.show()
