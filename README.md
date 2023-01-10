![image](https://user-images.githubusercontent.com/36027403/211432442-519763dd-b2d7-42c2-ad55-ec0943e4059f.png)

# How to Use the Python Scripts

1. `git clone https://github.com/codereport/city-strides-hacking.git`

2. Add a file named `cookies_headers.py` with the following contents:

```py
cookies = {
    "_citystrides_session": # ...
    "__stripe_mid": # ...
    "__stripe_sid": # ...
    "remember_user_token": # ...
}

headers = {
    "User-Agent": # ...
    "Accept": # ...
    # ...
}
```
* Generate the above by doing the following:
   * Go to www.citystrides.com
   * `Ctrl + Shift + I` to open the Web Developer Tools
   * Choose a city on CityStrides, and click the 'Show Nodes" button (need to subscride for access to nodes)
   * Copy the `GET` command using the `Copy Value` -> `Copy as Curl` 
   * Paste the curl command to https://curlconverter.com/python/
   * Your `cookies` and `headers` can be found in the generated command
3. Replace the `params` from the generated command in step 2 in the `download_node_csv.py`
4. You can now run:
   * `python3 download_node_csv.py` to scrape all the nodes to `nodes.csv`
   * `python3 plot_nodes.py` to view all of the nodes without a 1000 node limit
  
TODO: Add graph algorithm that builds routes. Need to query "path API" though. Straight lines isn't enough.
