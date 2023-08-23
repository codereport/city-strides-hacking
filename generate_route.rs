extern crate city_strides_utils;

use city_strides_utils::cs_utils;
use std::collections::VecDeque;
use std::collections::{HashMap, HashSet};
use std::error::Error;
use std::vec::Vec;

fn path_bfs(
    starting_path: &[i64],
    steps: i32,
    adj_list_all: &HashMap<i64, HashSet<i64>>,
    nodes_all: &HashMap<i64, (f64, f64)>,
    streets: &HashMap<String, Vec<Vec<i64>>>,
) -> Vec<i64> {
    let mut best_path = Vec::new();
    let mut best_completed;
    let mut best_score = 0.0;
    let mut queue = VecDeque::new();
    let done_at_start = cs_utils::streets_completed(starting_path, streets);

    queue.push_back((starting_path.to_vec(), 0.0, steps));

    while let Some((mut path, dist, steps_left)) = queue.pop_front() {
        if steps_left == 0 {
            let done = cs_utils::streets_completed(&path, streets);
            let score = (done - done_at_start) as f64 / dist;

            if score >= best_score {
                best_completed = done;
                best_score = score;
                best_path = path.clone();

                if best_score > 0.0 {
                    println!("{} {}", best_score, best_completed);
                }
            }
        } else {
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
                dist_to_next = cs_utils::node_geodist(curr, *next, nodes_all);
                path.push(*next);
                queue.push_back((
                    path.clone(),
                    dist + dist_to_next,
                    steps_left - (choices.len() > 1) as i32,
                ));
                path.pop();
            }

            if removed && choices.len() == 1 && dist_to_next > 0.1 {
                path.push(prev);
                queue.push_back((
                    path.clone(),
                    dist + cs_utils::node_geodist(curr, prev, nodes_all),
                    steps_left - 1,
                ));
            }
        }
    }

    best_path
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

fn main() -> Result<(), Box<dyn Error>> {
    let city = "bangkok"; // Replace with the desired city name.

    // Load JSON data and build dictionaries
    let elements = cs_utils::load_json(city)?;
    let streets = cs_utils::street_dictionary(&elements);
    let elements_all = cs_utils::load_json(format!("{}_all", city).as_str())?;
    let nodes_all = cs_utils::node_dictionary(&elements_all);
    let adj_list_all = cs_utils::adjacency_list(&cs_utils::street_dictionary(&elements_all));

    // Define constants
    const START_NODE_ID: i64 = 702209198;
    const MAX_DISTANCE: f64 = 15.0;

    let mut total_distance = 0.0;
    let mut path = vec![START_NODE_ID];

    while total_distance < MAX_DISTANCE {
        // Calculate the best path using BFS
        path = path_bfs(&path, 5, &adj_list_all, &nodes_all, &streets);
        total_distance = cs_utils::distance_of_path_precise(&path, &nodes_all);
        println!("total_distance={}", total_distance);

        // Write nodes to CSV
        cs_utils::write_nodes_csv(&node_list_for_csv(&path, &nodes_all))?;
    }

    Ok(())
}
