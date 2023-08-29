import pandas as pd
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Function to update the Plotly figure
def update_plot():
    global fig
    cities = pd.read_csv("nodes.csv")  # Load the updated CSV data

    for trace in fig.data:
        trace.update(lat=cities["lat"], lon=cities["lon"])
        if trace.name == "MARKERS":
            trace.update(
                marker=dict(
                    size=10,
                    sizemode="diameter",
                    color=cities["len_cat"],
                    colorscale="Jet",
                    colorbar=dict(title="len_cat")))

        fig.update_layout(
            mapbox=dict(
                style="stamen-terrain",
                center=dict(lat=cities["lat"].mean(), lon=cities["lon"].mean()),
                zoom=14,))

# Create a Dash app
app = dash.Dash(__name__)

# Load your CSV data
cities = pd.read_csv("nodes.csv")

# Create a Plotly figure
fig = go.FigureWidget()

# Add lines between successive lon-lat points
fig.add_trace(go.Scattermapbox(
    name="LINE",
    lat=cities["lat"],
    lon=cities["lon"],
    mode="lines+markers",
    line=dict(width=4, color="white"),
    hoverinfo="none",
))

# Add scatter points
fig.add_trace(go.Scattermapbox(
    name="MARKERS",
    lat=cities["lat"],
    lon=cities["lon"],
    mode="markers",
    marker=dict(
        size=10,
        sizemode="diameter",
        color=cities["len_cat"],
        colorscale="Jet",
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

# Define the layout of the Dash app
app.layout = html.Div([
    dcc.Graph(id='map-graph', figure=fig, style={'width': '180vh', 'height': '90vh'}),
    dcc.Interval(
        id='interval-component',
        interval=1 * 1000,  # Update every 5 seconds
        n_intervals=0
    )
])

# Callback to update the plot on an interval
@app.callback(
    Output('map-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_graph(n_intervals):
    update_plot()
    return fig

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)
