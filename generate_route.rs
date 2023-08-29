extern crate city_strides_utils;
extern crate serde_derive;
extern crate serde_yaml;

use city_strides_utils::cs;
use serde_derive::Deserialize;
use std::collections::VecDeque;
use std::collections::{HashMap, HashSet};
use std::error::Error;
use std::fs::File;
use std::io::Read;
use std::vec::Vec;

fn path_bfs(
    starting_path: &[i64],
    params: &Parameters,
    adj_list_all: &HashMap<i64, HashSet<i64>>,
    nodes_all: &HashMap<i64, (f64, f64)>,
    streets: &HashMap<String, Vec<Vec<i64>>>,
    hot_spot: &(f64, f64),
) -> Vec<i64> {
    let mut best_path = Vec::new();
    let mut best_completed;
    let mut best_score = 0.0;
    let mut queue = VecDeque::new();
    let start_dist_to_hot_spot = cs::dist_node_lat_lon(
        *starting_path.last().unwrap(),
        hot_spot.0,
        hot_spot.1,
        nodes_all,
    );
    let done_at_start = cs::streets_completed(starting_path, streets);

    queue.push_back((starting_path.to_vec(), 0.0, params.steps));

    while let Some((mut path, dist, steps_left)) = queue.pop_front() {
        let done = cs::streets_completed(&path, streets);
        let done_delta = done - done_at_start;
        let dist_to_hot_spot =
            cs::dist_node_lat_lon(*path.last().unwrap(), hot_spot.0, hot_spot.1, nodes_all);
        let hot_spot_adj = if params.hot_spots {
            (start_dist_to_hot_spot - dist_to_hot_spot) / dist
        } else {
            0.0
        };
        let score = done_delta as f64 / dist + hot_spot_adj;

        if steps_left == 0 {
            if score >= best_score {
                best_completed = done;
                best_path = path.clone();
                best_score = score;

                if best_score > 0.0 {
                    println!(
                        "{:.2} {} {} / {:.2} | {:.2} | {:.2}",
                        best_score,
                        best_completed,
                        done_delta,
                        dist,
                        dist_to_hot_spot,
                        (start_dist_to_hot_spot - dist_to_hot_spot)
                    );
                }
            }
        } else if best_score == 0.0 || best_score - score < 1.0 {
            let curr = path.last().cloned().unwrap_or_default();
            let prev = path.iter().rev().nth(1).cloned().unwrap_or_default();
            let mut choices: Vec<i64> = adj_list_all[&curr].iter().cloned().collect();
            let mut removed = false;

            if choices.contains(&prev) && choices.len() > 1 {
                if let Some(pos) = choices.iter().position(|&x| x == prev) {
                    choices.remove(pos);
                }
                removed = true;
            }

            let mut dist_to_next = 0.0;

            for next in choices.iter() {
                path.push(*next);
                dist_to_next = cs::dist(curr, *next, nodes_all);
                queue.push_back((
                    path.clone(),
                    dist + dist_to_next,
                    steps_left - (choices.len() > 1) as i32,
                ));
                path.pop();
            }

            const DIST_TO_ALLOW_BACKTRACK: f64 = 0.02; // PARAMTER TO PLAY WITH
            if removed && choices.len() == 1 && dist_to_next > DIST_TO_ALLOW_BACKTRACK {
                path.push(prev);
                queue.push_back((
                    path.clone(),
                    dist + cs::dist(curr, prev, nodes_all),
                    steps_left - 1,
                ));
            }
        }
    }

    // if best_score == 0.0 {
    //     println!("increasing steps to {}", params.steps + 2);
    //     best_path = path_bfs(
    //         starting_path,
    //         params.steps + 2,
    //         adj_list_all,
    //         nodes_all,
    //         streets,
    //         hot_spot,
    //     );
    // }

    best_path
}

fn node_list_for_csv_from_hot_spots(hot_spots: &[(usize, (f64, f64))]) -> Vec<Vec<String>> {
    hot_spots
        .iter()
        .map(|(streets, (lat, lon))| {
            vec![
                lat.to_string(),
                lon.to_string(),
                format!("{}", streets / 10),
                format!("\"Streets Completed: {}\"", streets),
                "5".to_string(),
            ]
        })
        .collect()
}

fn node_list_for_csv(path: &[i64], nodes: &HashMap<i64, (f64, f64)>) -> Vec<Vec<String>> {
    path.iter()
        .enumerate()
        .map(|(i, id)| {
            let (lat, lon) = nodes[id];
            vec![
                lat.to_string(),
                lon.to_string(),
                "2".to_string(),
                format!("\"Name: {}\"", id),
                i.to_string(),
            ]
        })
        .collect()
}

#[derive(Debug, Deserialize)]
struct Parameters {
    city: String,
    start_node: i64,
    max_distance: f64,
    steps: i32,
    hot_spots: bool,
    hot_spot_n: i32,
}

fn read_parameters_from_yaml() -> Result<Parameters, Box<dyn std::error::Error>> {
    // Open and read the JSON file
    let mut file = File::open("parameters.yaml")?;
    let mut json_data = String::new();
    file.read_to_string(&mut json_data)?;

    // Deserialize the JSON into your struct and return it
    let parameters: Parameters = serde_yaml::from_str(&json_data)?;
    Ok(parameters)
}

fn main() -> Result<(), Box<dyn Error>> {
    let params = read_parameters_from_yaml()?;

    let elements = cs::load_json(&params.city)?;
    let streets = cs::street_dictionary(&elements);

    let elems_all = cs::load_json(format!("{}_all", params.city).as_str())?;
    let nodes_all = cs::node_dictionary(&elems_all);
    let alist_all = cs::adjacency_list(&cs::street_dictionary(&elems_all));

    let mut total_distance = 0.0;
    let mut path = vec![params.start_node];

    let hot_spots = cs::hot_spots(
        params.start_node,
        &nodes_all,
        &streets,
        &path,
        params.hot_spot_n,
    );
    let (_, mut hottest_spot) = hot_spots.first().unwrap();

    let _ = cs::write_nodes_csv(&node_list_for_csv_from_hot_spots(&hot_spots));

    while total_distance < params.max_distance {
        path = path_bfs(
            &path,
            &params,
            &alist_all,
            &nodes_all,
            &streets,
            &hottest_spot,
        );
        total_distance = cs::distance_of_path_precise(&path, &nodes_all);
        println!("\ntotal_distance = {}\n", total_distance);

        if cs::dist_node_lat_lon(
            *path.last().unwrap(),
            hottest_spot.0,
            hottest_spot.1,
            &nodes_all,
        ) < 0.5
        {
            let hot_spots = cs::hot_spots(
                *path.last().unwrap(),
                &nodes_all,
                &streets,
                &path,
                params.hot_spot_n,
            );
            (_, hottest_spot) = *hot_spots.first().unwrap();
            // cs::write_nodes_csv(&node_list_for_csv_from_hot_spots(&hot_spots));
            // return Ok(());
        }

        // Write nodes to CSV
        cs::write_nodes_csv(&node_list_for_csv(&path, &nodes_all))?;
    }

    Ok(())
}
