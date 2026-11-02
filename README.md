### Node Preview 

![image](https://github.com/codereport/city-strides-hacking/assets/36027403/ef99afe0-82e4-49a1-9358-1b741179635b)

# How to Use the Python Scripts

1. `git clone https://github.com/codereport/city-strides-hacking.git`

2. Install the dependencies:

```bash
python3 -m pip install -r requirements.txt
```

If `cookies.json` is missing or expired, the downloader checks your local
Chrome, Chromium, Firefox, Brave, and Edge profiles for a CityStrides session.
If needed, it opens CityStrides in your usual browser. Sign in there normally;
the downloader verifies Node Hunter access, saves the cookies locally with
owner-only permissions, and continues automatically. Browser cookie writes
can take a short time to appear. Later downloads reuse the saved session and
retain cookie updates. CityStrides may occasionally require a new login.

Only CityStrides cookies are imported; Garmin and other provider credentials
stay in your browser. Node Hunter requires a CityStrides subscription. Cookies
are ignored by Git. Stop the command to cancel a pending login.

3. Add a `parameters.yaml`. Example below.

```yaml
map_style: 'open-street-map'
heat_map_max_length: 1
heat_map_exclude_csnodes: false
```
4. You can now run:
   * `./download_node_csv.py --city scarborough` to scrape the nodes to `nodes.csv`
   * `./plot_nodes.py` to view all of the nodes without a 1000 node limit
   * `./create_heat_map.py scarborough` to build
     `heat_maps/scarborough.html`
   * Pass several cities, such as `./create_heat_map.py tiny midland`, to create
     a combined heat map. Use `--output path.html` to choose another destination.

For a city without an OSM dataset, `./get_data_for_new_city.py CITY` downloads
it. `./add_new_city.py CITY` registers a new CityStrides city and bounding box
with the node downloader.

The two repository-root download commands are compatibility launchers. Their
single canonical implementations live in `city-strides-route-planner/`, so
fixes and city configuration must be made there rather than copied between the
parent repository and submodule.

# Private route planner

The closed-loop route planner is maintained in the private
`city-strides-route-planner` submodule. Contributors with access can initialize
it with:

```bash
git submodule update --init --recursive
python3 route_planner.py serve --city richmond_hill
```

The repository-root `route_planner.py` launches the private planner, so it can
be run directly from this directory. Public GitHub Pages builds use a sparse
checkout that excludes the private submodule.

See the submodule README for setup, data acquisition, CLI usage, and tests.

In the planner, **E** toggles satellite imagery and **H** toggles street-length
heatmap colours using `create_heat_map.py`'s blue/purple palette. Nodes on streets
over 500 m stay blue.
During a manual route, **Ctrl + click** adds a straight crossing to the exact
clicked point, including areas without an OSM path. **Undo last** removes it.

Phone-ready route exports from the private planner are written to the public
`upcoming_runs/` directory and automatically listed by the repository-root
`index.html` page. Open **Upcoming runs** from Route Lab to mark a run completed
and move it to the completion-sorted `past_runs.html` page. These controls also
work when opening `index.html` with a `file://` URL; keep the planner server
running on its default port for that option. The published Pages site remains
read-only.

## GitHub Pages

The Pages workflow deploys only the run indexes, their small management script,
and the `upcoming_runs/` and `past_runs/` directories. It uses a
partial, sparse clone so the runner does not download the repository's large
route-planning datasets or initialize the private planner submodule.

Set **Settings → Pages → Build and deployment → Source** to **GitHub Actions**
once. Thereafter, Pages runs only when the public site or its workflow changes;
data-only commits do not trigger a deployment.

### Useful Links

* [Details about CS OSM Data](https://community.citystrides.com/t/about-the-node-street-and-city-data/19802)
* [OSM Tag Info](https://taginfo.openstreetmap.org/keys)
* [Overpass](http://overpass-turbo.eu/)
* [Data by Region/Country](https://download.geofabrik.de/)
