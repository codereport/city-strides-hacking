extern crate csv;
extern crate haversine;
extern crate itertools;
extern crate serde;
extern crate serde_derive;
extern crate serde_json;

pub mod cs {

    use haversine::Location;
    use itertools::Itertools;
    use serde_derive::Deserialize;
    use std::collections::{BTreeMap, HashMap, HashSet};
    use std::error::Error;
    use std::fs::File;
    use std::io::Read;
    use std::vec::Vec;

    #[derive(Debug, Deserialize)]
    #[allow(dead_code)]
    struct Element {
        version: f64,
        generator: String,
        osm3s: Osm3s,
        elements: Vec<JsonElement>,
    }

    #[derive(Debug, Deserialize)]
    #[allow(dead_code)]
    struct Osm3s {
        timestamp_osm_base: String,
        timestamp_areas_base: String,
        copyright: String,
    }

    #[derive(Debug, Deserialize)]
    pub struct JsonElement {
        r#type: String,
        id: i64,
        lat: Option<f64>,
        lon: Option<f64>,
        nodes: Option<Vec<i64>>,
        tags: Option<BTreeMap<String, String>>,
    }

    type NodeHashMap = HashMap<i64, (f64, f64)>;
    type StreetHashMap = HashMap<String, Vec<Vec<i64>>>;

    // Function to load JSON data
    pub fn load_json(city: &str) -> Result<Vec<JsonElement>, Box<dyn Error>> {
        let mut data = String::new();
        let filename = format!("data/{}.json", city);
        File::open(filename)?.read_to_string(&mut data)?;
        let elements: Element = serde_json::from_str(&data)?;
        // println!("{:?}", elements.elements);
        Ok(elements.elements)
    }

    // Function to create a dictionary of streets
    pub fn street_dictionary(elements: &[JsonElement]) -> StreetHashMap {
        let mut streets = HashMap::new();
        for e in elements {
            if e.r#type == "way" {
                if let Some(tags) = &e.tags {
                    if let Some(name) = tags.get("name") {
                        streets
                            .entry(name.to_string())
                            .or_insert_with(Vec::new)
                            .push(e.nodes.clone().unwrap_or_default());
                    } else {
                        streets
                            .entry(format!("unnamed_{}", e.id))
                            .or_insert_with(Vec::new)
                            .push(e.nodes.clone().unwrap_or_default());
                    }
                }
            }
        }
        streets
    }

    pub fn node_dictionary(elements: &[JsonElement]) -> NodeHashMap {
        let mut node_dict = HashMap::new();
        for e in elements {
            if e.r#type == "node" {
                if let (Some(lat), Some(lon)) = (e.lat, e.lon) {
                    node_dict.insert(e.id, (lat, lon));
                }
            }
        }
        node_dict
    }

    pub fn adjacency_list(streets: &StreetHashMap) -> HashMap<i64, HashSet<i64>> {
        let mut adj_list = HashMap::new();
        for snodes in streets.values() {
            for ssnodes in snodes {
                for (a, b) in ssnodes.iter().tuple_windows() {
                    adj_list.entry(*a).or_insert_with(HashSet::new).insert(*b);
                    adj_list.entry(*b).or_insert_with(HashSet::new).insert(*a);
                }
            }
        }
        adj_list
    }

    pub fn streets_completed_names(
        path: &[i64],
        streets: &StreetHashMap,
        nodes: &NodeHashMap,
    ) -> HashSet<String> {
        let in_path = |x: &Vec<Vec<i64>>| x.iter().all(|ns| ns.iter().all(|n| path.contains(n)));

        streets
            .iter()
            .filter(|(_, snodes)| in_path(snodes) && total_distance_of_paths(&snodes, nodes) < 0.2)
            .map(|(name, _)| name.clone())
            .collect()
    }

    pub fn streets_completed(path: &[i64], streets: &StreetHashMap) -> usize {
        let in_path = |x: &Vec<Vec<i64>>| x.iter().all(|ns| ns.iter().all(|n| path.contains(n)));

        streets.values().filter(|snodes| in_path(snodes)).count()
    }

    pub fn dist_node_lat_lon(node: i64, lat: f64, lon: f64, nodes: &NodeHashMap) -> f64 {
        let haversine_location = |node_id| Location {
            latitude: nodes[&node_id].0,
            longitude: nodes[&node_id].1,
        };

        haversine::distance(
            haversine_location(node),
            Location {
                latitude: lat,
                longitude: lon,
            },
            haversine::Units::Kilometers,
        )
    }

    fn hot_spot_count(
        lat: f64,
        lon: f64,
        nodes: &NodeHashMap,
        streets: &StreetHashMap,
        streets_done: &HashSet<String>,
    ) -> usize {
        let filtered_nodes: Vec<i64> = nodes
            .keys()
            .filter(|&&node_id| dist_node_lat_lon(node_id, lat, lon, nodes) < 0.75)
            .cloned()
            .collect();

        streets_completed_names(&filtered_nodes, streets, &nodes)
            .difference(&streets_done)
            .count()
    }

    pub fn hot_spots(
        node: i64,
        nodes: &NodeHashMap,
        streets: &StreetHashMap,
        path: &[i64],
        n: i32,
    ) -> Vec<(usize, (f64, f64))> {
        let (lat, lon) = nodes[&node];
        let mut hot_spot_counts = Vec::new();

        let streets_done = streets_completed_names(path, streets, &nodes);

        println!("Calcuating hotspots...");
        for (idx, i) in (-n..=n).map(|x| x as f64 / 100.0).enumerate() {
            println!("{:.2} % done", idx as f64 * 100.0 / 10.0);
            for j in (-n..=n).map(|y| y as f64 / 100.0) {
                let new_lat = lat + i;
                let new_lon = lon + j;

                let hot_spot_count =
                    hot_spot_count(new_lat, new_lon, nodes, streets, &streets_done);
                hot_spot_counts.push((hot_spot_count, (new_lat, new_lon)));
            }
        }

        hot_spot_counts.sort_by(|a, b| b.0.cmp(&a.0));
        hot_spot_counts
    }

    pub fn dist(a: i64, b: i64, nodes: &NodeHashMap) -> f64 {
        let haversine_location = |node_id| Location {
            latitude: nodes[&node_id].0,
            longitude: nodes[&node_id].1,
        };

        haversine::distance(
            haversine_location(a),
            haversine_location(b),
            haversine::Units::Kilometers,
        )
    }

    // Function to calculate the distance of a path using Haversine formula
    pub fn distance_of_path_precise(p: &[i64], nodes: &NodeHashMap) -> f64 {
        p.iter()
            .tuple_windows()
            .map(|(&a, &b)| dist(a, b, nodes))
            .sum()
    }

    // Function to calculate the distance of a path using Euclidean distance
    // pub fn distance_of_path(l: &[i64], nodes: &NodeHashMap) -> f64 {
    //     let mut res = 0.0;
    //     for (&a, &b) in l.iter().tuple_windows() {
    //         let (x1, y1) = nodes[&a];
    //         let (x2, y2) = nodes[&b];
    //         res += haversine::distance(
    //             Location {
    //                 latitude: x1,
    //                 longitude: y1,
    //             },
    //             Location {
    //                 latitude: x2,
    //                 longitude: y2,
    //             },
    //             haversine::Units::Kilometers,
    //         );
    //     }
    //     res
    // }

    // Function to calculate the total distance of paths
    fn total_distance_of_paths(ls: &[Vec<i64>], nodes: &NodeHashMap) -> f64 {
        ls.iter().map(|l| distance_of_path_precise(l, nodes)).sum()
    }

    // Function to write nodes to CSV
    pub fn write_nodes_csv(nodes: &[Vec<String>]) -> Result<(), Box<dyn Error>> {
        let file = File::create("nodes.csv")?;
        let mut writer = csv::Writer::from_writer(file);
        writer.write_record(["lat", "lon", "sz", "names", "len_cat"])?;

        for row in nodes.iter() {
            let row_as_slice: Vec<&str> = row.iter().map(|s| s.as_str()).collect();
            writer.write_record(&row_as_slice)?;
        }

        writer.flush()?;
        Ok(())
    }
}
