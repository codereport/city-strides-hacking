#! /usr/bin/env python3

import pandas as pd
import plotly.express as px
import utils

style = utils.load_parameters()["map_style"]
cities = pd.read_csv("nodes.csv")

# Calculate center point for better initial view
center_lat = cities["lat"].mean()
center_lon = cities["lon"].mean()

fig = px.scatter_mapbox(
    cities,
    lat="lat",
    lon="lon",
    size="sz",
    size_max=10,
    hover_name="names",
    color="len_cat",
    zoom=12,  # Slightly zoomed out for better overview
    center={"lat": center_lat, "lon": center_lon},  # Center on data
)

# Configure map style and layout for better responsiveness
fig.update_layout(
    mapbox_style=style,
    margin={"r": 5, "t": 30, "l": 5, "b": 5},  # Small margins
    showlegend=True,
    autosize=True,  # Enable responsive sizing
    height=None,  # Let CSS control height completely
    title={
        "text": "City Strides Heat Map",
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
        "filename": "heat_map",
        "height": 600,
        "width": 1000,
        "scale": 2,
    },
}

# Generate HTML with custom styling
html_content = fig.to_html(include_plotlyjs="cdn", config=config, div_id="heat-map-div")

# Add custom CSS for better responsive behavior
custom_css = """
<style>
    body {
        margin: 10px;
        font-family: Arial, sans-serif;
        background-color: #f8f9fa;
    }
    
    /* Force all plotly elements to fill the container */
    .plotly-graph-div {
        border: 2px solid #e1e5e9;
        border-radius: 8px;
        background-color: white;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        height: 85vh !important;
        max-height: 800px !important;
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
    
    /* Remove any default plotly margins/padding that might create gaps */
    .plotly-graph-div .plot-container,
    .plotly-graph-div .plot-container .svg-container {
        margin: 0 !important;
        padding: 0 !important;
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
        .plotly-graph-div {
            height: 70vh !important;
            min-height: 400px !important;
        }
        .controls-info {
            font-size: 12px;
            padding: 8px;
        }
        body {
            margin: 5px;
        }
    }
    
    /* Enhance plotly toolbar */
    .modebar {
        background: rgba(255,255,255,0.9) !important;
        border: 1px solid #ddd !important;
        border-radius: 4px !important;
    }
</style>

<script>
    // Ensure proper resizing
    window.addEventListener('resize', function() {
        var plots = document.querySelectorAll('.js-plotly-plot');
        plots.forEach(function(plot) {
            Plotly.Plots.resize(plot);
        });
    });
    
    // Better scroll zoom handling
    document.addEventListener('DOMContentLoaded', function() {
        var plotDiv = document.querySelector('.js-plotly-plot');
        if (plotDiv) {
            plotDiv.addEventListener('wheel', function(e) {
                e.preventDefault();
            }, { passive: false });
        }
    });
</script>
"""

# Insert custom CSS and info before closing head tag
html_content = html_content.replace("</head>", custom_css + "\n</head>")

# Add helpful controls info after body tag
controls_info = """
<div class="controls-info">
    <strong>🗺️ Interactive Heat Map Controls</strong><br>
    🖱️ Click & drag to pan • 🔍 Scroll to zoom • 📱 Double-click to reset • 🛠️ Use toolbar for tools
</div>
"""

html_content = html_content.replace("<body>", "<body>\n" + controls_info)

# Write the improved HTML file
with open("heat_map.html", "w", encoding="utf-8") as f:
    f.write(html_content)
