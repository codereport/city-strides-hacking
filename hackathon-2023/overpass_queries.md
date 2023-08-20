### Querying Streets from City (in this case Prince George)

Use at: http://overpass-turbo.eu/ <br>
Get city names at: https://www.openstreetmap.org/

```
Cities:
Bangkok: กรุงเทพมหานคร
Nha Trang: Thành phố Nha Trang
```

```
[out:json];
area[name = "Prince George"];
(
  way(area)
    ['name'] // this is essential (only want named roads)
    ['highway']
    // everything below is to exclude certain types of "highways"
    ['highway' !~ 'path']
    ['highway' !~ 'steps']
    ['highway' !~ 'motorway']
    ['highway' !~ 'motorway_link']
    ['highway' !~ 'raceway']
    ['highway' !~ 'bridleway']
    ['highway' !~ 'proposed']
    ['highway' !~ 'construction']
    ['highway' !~ 'elevator']
    ['highway' !~ 'bus_guideway']
    ['highway' !~ 'footway']
    ['highway' !~ 'cycleway']
    ['highway' !~ 'trunk']
    ['foot' !~ 'no']
    ['access' !~ 'private']
    ['access' !~ 'no'];
  >;
);
// node(w); // Uncomment if you want to see just nodes.
out;
```