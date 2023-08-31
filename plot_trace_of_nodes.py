#! /usr/bin/env python3

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import dash
import time
from dash import dcc, html
from dash.dependencies import Input, Output
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

csv_changed = False
GIF_GENERATION = False
ZOOM_LEVEL = 13 if GIF_GENERATION else 14

# Function to update the Plotly figure
def update_plot():
    global fig, csv_changed
    if csv_changed:
        csv_changed = False
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
                    zoom=ZOOM_LEVEL,))

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
        zoom=ZOOM_LEVEL,
    ),
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
)

# Define the layout of the Dash app
app.layout = html.Div([
    dcc.Graph(id='map-graph', figure=fig, style={'width': '180vh', 'height': '90vh'}),
    dcc.Interval(
        id='interval-component',
        interval=1000,
        n_intervals=0
    )
])

class CSVFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        global i, fig, csv_changed
        csv_changed = True
        if GIF_GENERATION:
            print("CSV file has changed. Exporting figure...")
            pio.write_image(fig, f'imgs/map_{i}.png', width=1000, height=1000)
            i += 1

i = 0

# Callback to update the plot on an interval
@app.callback(
    Output('map-graph', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_graph(n_intervals):
    update_plot()
    return fig

def start_dash_app():
    app.run_server(debug=True, use_reloader=False)

if __name__ == '__main__':

    # Start Dash app in a separate thread
    dash_thread = threading.Thread(target=start_dash_app)
    dash_thread.daemon = True
    dash_thread.start()

    # Watchdog file monitoring
    observer = Observer()
    event_handler = CSVFileHandler()
    observer.schedule(event_handler, path='nodes.csv', recursive=False)

    # Start the observer
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
