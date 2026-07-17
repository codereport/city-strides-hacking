### Node Preview 

![image](https://github.com/codereport/city-strides-hacking/assets/36027403/ef99afe0-82e4-49a1-9358-1b741179635b)

# How to Use the Python Scripts

1. `git clone https://github.com/codereport/city-strides-hacking.git`

2. Add a file named `cookies.json` with the following contents:

```json
{
    "_citystrides_session": "...",
    "remember_user_token": "..."
}
```
* Generate the above by doing the following:
   * Go to www.citystrides.com (on Firefox)
   * `Ctrl + Shift + I` to open the Web Developer Tools
   * Choose a city on CityStrides, and click the "Show Nodes" button (a
     subscription is required for node access)
   * Copy the `GET` command using the `Copy Value` -> `Copy as Curl` 
   * Paste the curl command to https://curlconverter.com/python/
   * Your `cookies` can be found in the generated command

3. Add a `parameters.yaml`. Example below.

```yaml
map_style: 'open-street-map'
heat_map_max_length: 1
heat_map_exclude_csnodes: false
```
4. You can now run:
   * `./download_node_csv.py cookies.json` to scrape all the nodes to `nodes.csv`
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
git -c submodule.city-strides-route-planner.update=checkout \
  submodule update --init city-strides-route-planner
cd city-strides-route-planner
python3 route_planner.py serve --city scarborough
```

The committed submodule update policy is `none` so public GitHub Pages builds
skip the private repository. The command above explicitly opts authorized local
development checkouts back into cloning it.

See the submodule README for setup, data acquisition, CLI usage, and tests.

Phone-ready route exports from the private planner are written to the public
`upcoming_runs/` directory and automatically listed by the repository-root
`index.html` page. When that page is opened locally with a `file://` URL, it
shows controls for moving a run to the completion-sorted `past_runs.html` page
or deleting it. Keep the planner server running on its default port while using
those local controls; the published Pages site remains read-only.

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
