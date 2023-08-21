import pandas as pd
import plotly.graph_objects as go

# Load your CSV data
cities = pd.read_csv("nodes.csv")

# Create a Plotly figure
fig = go.Figure()

# Add lines between successive lon-lat points
fig.add_trace(go.Scattermapbox(
    lat=cities["lat"],
    lon=cities["lon"],
    mode="lines+markers",  # Use "lines+markers" to display both lines and markers
    line=dict(width=4, color="white"),  # Customize line properties here
    hoverinfo="none",  # Disable hover info for lines
))

# Add scatter points
fig.add_trace(go.Scattermapbox(
    lat=cities["lat"],
    lon=cities["lon"],
    mode="markers",
    marker=dict(
        size=10,
        sizemode="diameter",
        color=cities["len_cat"],
        colorscale="Jet",  # You can change the colorscale
        colorbar=dict(title="len_cat"),
    ),
    text=cities["names"],
))

# Set map layout
fig.update_layout(
    mapbox=dict(
        style="stamen-terrain",
        center=dict(lat=cities["lat"].mean(), lon=cities["lon"].mean()),
        zoom=14,
    ),
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
)

# Show the figure
fig.show()


# Export the figure as a PNG or JPEG image
fig.write_image("map.png")  # Change the file extension to ".jpg" for JPEG format
