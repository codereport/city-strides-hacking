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
    pub fn street_dictionary(elements: &[JsonElement]) -> HashMap<String, Vec<Vec<i64>>> {
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

    // Function to create a dictionary of nodes
    pub fn node_dictionary(elements: &[JsonElement]) -> HashMap<i64, (f64, f64)> {
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

    // Function to create an adjacency list
    pub fn adjacency_list(streets: &HashMap<String, Vec<Vec<i64>>>) -> HashMap<i64, HashSet<i64>> {
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

    // Function to count completed streets
    pub fn streets_completed(path: &[i64], streets: &HashMap<String, Vec<Vec<i64>>>) -> usize {
        let mut count = 0;
        for snodes in streets.values() {
            if snodes
                .iter()
                .all(|nodes| nodes.iter().all(|node| path.contains(node)))
            {
                count += 1;
            }
        }
        count
    }

    pub fn dist(a: i64, b: i64, nodes: &HashMap<i64, (f64, f64)>) -> f64 {
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
    pub fn distance_of_path_precise(p: &[i64], nodes: &HashMap<i64, (f64, f64)>) -> f64 {
        p.iter()
            .tuple_windows()
            .map(|(&a, &b)| dist(a, b, nodes))
            .sum()
    }

    // Function to calculate the distance of a path using Euclidean distance
    // pub fn distance_of_path(l: &[i64], nodes: &HashMap<i64, (f64, f64)>) -> f64 {
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
    // fn total_distance_of_paths(ls: &[Vec<i64>], nodes: &HashMap<i64, (f64, f64)>) -> f64 {
    //     ls.iter().map(|l| distance_of_path(l, nodes)).sum()
    // }

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
