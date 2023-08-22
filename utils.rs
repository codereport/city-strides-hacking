extern crate csv;
extern crate haversine;
extern crate itertools;
extern crate serde;
extern crate serde_derive;
extern crate serde_json;

use csv::Writer;
use haversine::Location;
use itertools::Itertools;
use serde_derive::Deserialize;
use std::collections::{BTreeMap, HashMap, HashSet};
use std::error::Error;
use std::fs::File;
use std::io::{self, Read};
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
struct JsonElement {
    r#type: String,
    id: i64,
    lat: Option<f64>,
    lon: Option<f64>,
    nodes: Option<Vec<i64>>,
    tags: Option<BTreeMap<String, String>>,
}

// Function to load JSON data
fn load_json(city: &str) -> Result<Vec<JsonElement>, Box<dyn Error>> {
    let mut data = String::new();
    let filename = format!("data/{}.json", city);
    File::open(filename)?.read_to_string(&mut data)?;
    let elements: Element = serde_json::from_str(&data)?;
    // println!("{:?}", elements.elements);
    Ok(elements.elements)
}

// Function to create a dictionary of streets
fn street_dictionary(elements: &[JsonElement]) -> HashMap<String, Vec<Vec<i64>>> {
    let mut streets = HashMap::new();
    for e in elements {
        if e.r#type == "way" {
            if let Some(tags) = &e.tags {
                if let Some(name) = tags.get("name") {
                    streets
                        .entry(name.to_string())
                        .or_insert_with(Vec::new)
                        .push(e.nodes.clone().unwrap_or_default());
                }
            }
        }
    }
    streets
}

// Function to create a dictionary of nodes
fn node_dictionary(elements: &[JsonElement]) -> HashMap<i64, (f64, f64)> {
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
fn adjacency_list(streets: &HashMap<String, Vec<Vec<i64>>>) -> HashMap<i64, HashSet<i64>> {
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
fn streets_completed(path: &[i64], streets: &HashMap<String, Vec<Vec<i64>>>) -> usize {
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

// Function to calculate the distance of a path using Haversine formula
fn distance_of_path_precise(p: &[i64], nodes: &HashMap<i64, (f64, f64)>) -> f64 {
    let haversine_location = |node_id| Location {
        latitude: nodes[&node_id].0,
        longitude: nodes[&node_id].1,
    };

    p.iter()
        .tuple_windows()
        .map(|(&a, &b)| {
            haversine::distance(
                haversine_location(a),
                haversine_location(b),
                haversine::Units::Kilometers,
            )
        })
        .sum()
}

// Function to calculate the distance of a path using Euclidean distance
fn distance_of_path(l: &[i64], nodes: &HashMap<i64, (f64, f64)>) -> f64 {
    let mut res = 0.0;
    for (&a, &b) in l.iter().tuple_windows() {
        let (x1, y1) = nodes[&a];
        let (x2, y2) = nodes[&b];
        res += haversine::distance(
            Location {
                latitude: x1,
                longitude: y1,
            },
            Location {
                latitude: x2,
                longitude: y2,
            },
            haversine::Units::Kilometers,
        );
    }
    res
}

// Function to calculate the total distance of paths
fn total_distance_of_paths(ls: &[Vec<i64>], nodes: &HashMap<i64, (f64, f64)>) -> f64 {
    ls.iter().map(|l| distance_of_path(l, nodes)).sum()
}

// Function to write nodes to CSV
fn write_nodes_csv(nodes: &HashMap<i64, (f64, f64)>) -> Result<(), Box<dyn Error>> {
    let mut writer = Writer::from_writer(io::stdout());
    writer.write_record(["lat", "lon", "sz", "names", "len_cat"])?;

    for (_, (lat, lon)) in nodes.iter() {
        writer.write_record(&[
            lat.to_string(),
            lon.to_string(),
            "".to_string(),
            "".to_string(),
            "".to_string(),
        ])?;
    }
    writer.flush()?;
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    let city = "bangkok"; // Replace with the desired city name.
    println!("Loading JSON...");
    let elements = load_json(city)?;
    println!("Done Loading JSON.");
    println!("Building Street Dictionary...");
    let streets = street_dictionary(&elements);
    println!("Done Building Street Dictionary.");
    println!("Building Node Dictionary...");
    let nodes = node_dictionary(&elements);
    println!("Done Building Node Dictionary.");
    println!("Building Adjacency List...");
    let _adj_list = adjacency_list(&streets);
    println!("Done Building Adjacency List.");
    let path = vec![9038489299, 702209198]; // Replace with your desired path.
    let completed_streets = streets_completed(&path, &streets);

    // Example of calculating distance using Haversine formula
    let distance_precise = distance_of_path_precise(&path, &nodes);
    let distance = distance_of_path(&path, &nodes);
    let total_distance = total_distance_of_paths(&[path.clone()], &nodes);

    println!("Completed Streets: {}", completed_streets);
    println!("Distance (Precise): {:.2} km", distance_precise);
    println!("Distance: {:.2} km", distance);
    println!("Total Distance: {:.2} km", total_distance);

    // Write nodes to CSV
    write_nodes_csv(&nodes)?;

    Ok(())
}
