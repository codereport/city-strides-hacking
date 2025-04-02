### Querying Streets from City (in this case Prince George)

Use at: http://overpass-turbo.eu/ <br>
Get city names at: https://www.openstreetmap.org/

```
Cities:
Bangkok: กรุงเทพมหานคร
Nha Trang: Thành phố Nha Trang
```

Note if you get multiple city hits (i.e. many for Hamilton), you can refine your search with info from https://www.openstreetmap.org, such as using `offical_name` or adding `admin_level`, example below.

```
[out:json];
area[official_name = "City of Hamilton"]["admin_level"="6"];
```

Or an even better way is to get the relation id from https://www.openstreetmap.org and use that in the query below.

```
[out:json];
rel(112145);
map_to_area;
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

### Querying ALL Streets from City (in this case Etobicoke)
#### Necessary to build routes correctly

```
[out:json];
area[name = "Etobicoke"];
(
  way(area)
    ['highway']
    // everything below is to exclude certain types of "highways"
    ['foot' !~ 'no']
    ['access' !~ 'private']
    ['access' !~ 'no'];
  >;
);
// node(w); // Uncomment if you want to see just nodes.
out;
```
