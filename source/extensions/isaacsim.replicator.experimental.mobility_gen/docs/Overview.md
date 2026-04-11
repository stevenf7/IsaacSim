```{csv-table}
**Extension**: {{ extension_version }},**Documentation Generated**: {sub-ref}`today`
```

# Overview

**MobilityGen** (`isaacsim.replicator.experimental.mobility_gen`) is an experimental toolkit for building **synthetic mobility datasets** in Isaac Sim: wheeled robots, **2D occupancy maps** in ROS map format, and **time-synchronized sensor and state dumps** suitable for navigation and mobility research. It sits alongside Omni **Replicator**—on-robot cameras use Replicator render products and annotators for RGB, segmentation, depth, and normals.

The extension is **pluggable by design**. You register concrete `MobilityGenRobot` and `MobilityGenScenario` types in the `ROBOTS` and `SCENARIOS` registries; run configuration (`scenario_type`, `robot_type`, source USD scene) is serialized in each dataset’s `config.json`. Playback and inspection use the same layout: `load_scenario()` opens the recorded stage, sets up simulation, spawns the robot and ground plane, attaches a chase camera to the active viewport, and rebuilds the scenario with the saved occupancy map.

## What’s in a dataset

A typical recording directory contains:

- **`config.json`** — `Config` (`scenario_type`, `robot_type`, `scene_usd`)
- **`stage.usd`** or **`stage.usdz`** — copied scene for reproducibility
- **`occupancy_map/`** — ROS-style `map.yaml` and `map.png` via `OccupancyMap`
- **`state/`** — per-frame outputs from `MobilityGenWriter`: shared NumPy payloads under `state/common/`, plus optional `rgb/`, `segmentation/`, `depth/`, and `normals/` trees keyed by camera name

`MobilityGenReader` walks that tree to list time steps and load RGB, depth (decoded from stored inverse-depth PNGs), segmentation, normals, and common state.

## Main building blocks

- **`MobilityGenRobot`** — Abstract articulation-backed robot: chase and front cameras, velocity/command buffers, 2D pose helpers, keyboard/gamepad hooks, and hooks for writing actions vs. replaying recorded state. Concrete robots are registered on `ROBOTS`.
- **`MobilityGenScenario`** — Abstract scenario tying a robot to a buffered region of the occupancy map (`from_robot_occupancy_map`). Concrete scenarios are registered on `SCENARIOS`.
- **`MobilityGenCamera`** — Replicator-based rendering module (annotators for RGB, instance/semantic segmentation, depth, normals) with `Buffer` integration for dataset export.
- **`OccupancyMap`** — Load/save and freespace masks from ROS map conventions; used for planning and visualization.
- **Path utilities** — Grid path generation and simplification (`generate_paths`, `compress_path`) backed by the extension’s native path-planner bindings for efficient coverage of freespace.

## Dependencies (high level)

The extension builds on **Isaac Sim core experimental** prims/objects/utils, **simulation manager**, **Replicator** (`omni.replicator.core`), **occupancy map** generation (`isaacsim.asset.gen.omap`), and kit services such as viewport utilities and USDZ export where needed.

## Enabling the extension

1. Open Isaac Sim.
2. Go to **Window → Extensions** (Extension Manager).
3. Search for **`isaacsim.replicator.experimental.mobility_gen`** and enable it.

## API reference

Generated Python API documentation is in **`docs/api.rst`** (module `isaacsim.replicator.experimental.mobility_gen`).
