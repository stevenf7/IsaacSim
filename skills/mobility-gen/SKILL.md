---
name: mobility-gen
description: >
  Generate synthetic sensor datasets for mobile robots using Isaac Sim's MobilityGen
  extension. Two-phase pipeline: headless trajectory recording → replay-and-render
  for RGB/depth/seg/normals/pose data. Covers `RandomPathFollowingScenario`,
  `RandomAccelerationScenario`, and custom robot subclassing
  (`WheeledMobilityGenRobot`, `PolicyMobilityGenRobot`, holonomic). Use when generating
  mobile-robot training data, recording sim trajectories, replaying with sensors, or
  implementing a custom MobilityGenRobot. Distinct from `data-collection-sim`
  (static-scene SDG) — this skill is robot-trajectory-driven. See `navigation-primitives`
  for shared occupancy-map / A* / kinematics substrate; `isaac-sim-robot-navigation`
  for non-SDG runtime nav.
---

# MobilityGen Synthetic Data Generation

Two-phase pipeline: **record trajectories** (physics, no rendering) → **replay & render** (sensors added).

## Read These Skills First

- **navigation-primitives** — `OccupancyMap`, A* planner, robot footprints (Spot Z=0.69), differential/holonomic kinematics, look-at chase cameras, shared gotchas. MobilityGen consumes this substrate; this skill assumes you know it.
- **occupancy-map** — produces the `map.yaml` consumed by `OccupancyMap.from_ros_yaml`
- **data-collection-sim** — sibling SDG path for static scenes with randomized object/camera poses (no robot trajectory)

## When To Use This Skill (vs siblings)

| Goal | Use |
|---|---|
| Record trajectories then re-render with sensors for SDG (training data) | **this skill** |
| Drive a robot through a scene in real time, see it move | `isaac-sim-robot-navigation` |
| Annotated frames with no robot motion (object pose randomization) | `data-collection-sim` |

## Related Skills

- `navigation-primitives` — shared navigation substrate (read first)
- `data-collection-sim` — static-scene SDG sibling
- `isaac-sim-sensor` — sensor primitives (camera, LiDAR, IMU, contact)
- `isaac-sim-robot-navigation` — runtime navigation sibling
- `isaac-sim-headless-deployment` — `--no-window` headless launch and `SimulationApp` batch pattern

## Environment

- **Isaac Sim source tree**: `$ISAAC_SIM_DIR/source/` for source builds. The variable `$ISAAC_SIM_SRC` is a convenience alias for that path; declare it once at the top of your launcher (e.g. `ISAAC_SIM_SRC="$ISAAC_SIM_DIR/source"`).
- **Python launcher**: `$ISAAC_SIM_DIR/python.sh`
- **Replay script**: `$ISAAC_SIM_SRC/standalone_examples/replicator/mobility_gen/replay_directory.py`
- **Extension examples**: `$ISAAC_SIM_SRC/extensions/isaacsim.replicator.mobility_gen.examples/`
- **Data dir**: `$MOBILITY_GEN_DATA` (env var). Default to a workspace-local path such as `$WORKSPACE_DIR/MobilityGenData` or `$HOME/MobilityGenData`.
  - `recordings/` — timestamped trajectory dirs
  - `replays/` — rendered output
  - `maps/` — occupancy map YAML + PNG files

## Extension Loading (Critical)

Extensions are **not auto-loaded**. Always pass `--enable` flags when running `python.sh`:

```bash
"$ISAAC/python.sh" my_script.py --enable isaacsim.replicator.mobility_gen.examples

"$ISAAC/python.sh" my_script.py \
  --enable isaacsim.asset.gen.omap \
  --enable isaacsim.replicator.mobility_gen.examples
```

Enabling `isaacsim.replicator.mobility_gen.examples` auto-loads `isaacsim.replicator.mobility_gen` as a dependency. All extension-dependent imports must come AFTER `SimulationApp(...)` is initialized.

## Phase 1: Automated Trajectory Recording (Headless)

`KeyboardTeleoperationScenario` and `GamepadTeleoperationScenario` require an interactive UI. For headless batch recording use `RandomPathFollowingScenario` or `RandomAccelerationScenario`.

> **API note (Kit 110):** the snippet below uses `isaacsim.core.api.objects`, `isaacsim.core.utils.stage`, and the MobilityGen `get_world` / `new_world` helpers. These wrap the legacy `isaacsim.core.api.World` flow that MobilityGen's scenario/writer plumbing expects. For new code outside MobilityGen, prefer the experimental APIs (`isaacsim.core.experimental.utils.stage`, the `isaacsim.core.simulation_manager.SimulationManager` lifecycle, and `isaacsim.core.experimental.objects` for primitives) — see the cheatsheet. Do not mix the two within a single MobilityGen session.
>
> **Migration:** for the full `omni.isaac.*` → `isaacsim.*` mapping when porting scripts off the legacy World flow, see [Renaming Extensions](https://docs.isaacsim.omniverse.nvidia.com/latest/migration_guides/isaac_sim_4_5/extensions_renaming.html).

`record_trajectories(scene_usd, omap_yaml, robot_type, scenario, num_episodes, max_steps, data_dir)` — headless SimulationApp loop that builds a robot and scenario, records each episode with a `MobilityGenWriter`, and saves to `$MOBILITY_GEN_DATA/recordings/`.

See [`scripts/record_trajectories.py`](scripts/record_trajectories.py).

## Phase 2: Replay & Render

Replay all recordings in `$MOBILITY_GEN_DATA/recordings/` and write sensor data to `replays/`.

```bash
: "${MOBILITY_GEN_DATA:=${WORKSPACE_DIR:-$HOME}/MobilityGenData}"
ISAAC="$ISAAC_SIM_DIR"
SRC="$ISAAC_SIM_DIR/source"

CUDA_VISIBLE_DEVICES=0 DISPLAY=:99 nohup \
  "$ISAAC/python.sh" \
  "$SRC/standalone_examples/replicator/mobility_gen/replay_directory.py" \
  --input  "$MOBILITY_GEN_DATA/recordings" \
  --output "$MOBILITY_GEN_DATA/replays" \
  --render_interval 40 \
  --rgb_enabled True \
  --depth_enabled True \
  --segmentation_enabled True \
  --normals_enabled False \
  --render_rt_subframes 1 \
  --enable isaacsim.replicator.mobility_gen.examples \
  > /tmp/mobility_gen_replay.log 2>&1 &
```

`--render_interval 40` = 1 frame per 40 physics steps (~5 Hz at 200 Hz physics). Increase `--render_rt_subframes` for better quality at the cost of speed.

### Replay Output Structure

```
replays/<recording_name>/
  config.json
  stage.usd
  occupancy_map/map.yaml, map.png
  state/
    common/<step>.npy          # robot pose, joint positions, velocities
    rgb/<camera_name>/<step>.jpg
    segmentation/<camera_name>/<step>.png
    depth/<camera_name>/<step>.png   # 16-bit inverse depth
    normals/<camera_name>/<step>.npy
```

## Available Robots

| Name | Type | Notes |
|---|---|---|
| `JetbotRobot` | Wheeled (differential) | Small, `physics_dt=0.005`, Jetbot USD |
| `CarterRobot` | Wheeled (differential) | Nova Carter, `physics_dt=0.005` |
| `H1Robot` | Humanoid (policy) | Unitree H1, flat-terrain RL policy |
| `SpotRobot` | Quadruped (policy) | Boston Dynamics Spot, flat-terrain RL policy |

## Available Scenarios

| Name | Mode | Headless? |
|---|---|---|
| `KeyboardTeleoperationScenario` | Manual (WASD) | No — needs UI |
| `GamepadTeleoperationScenario` | Manual (gamepad) | No — needs UI |
| `RandomAccelerationScenario` | Automated (brownian) | Yes |
| `RandomPathFollowingScenario` | Automated (A* path following) | Yes |

`RandomPathFollowingScenario` plans an A* path from the robot's current position to a random free-space goal and follows it with proportional steering. Episode ends when goal is reached or robot collides.

## Add a Custom Robot

Two base classes exist depending on robot type. Both handle `build()` and `write_action()` — set class-level attributes only.

### Wheeled (differential drive)

Subclass `WheeledMobilityGenRobot`. No need to override `build()` or `write_action()`:

`MyRobot(WheeledMobilityGenRobot)` — example class showing all required class-level attributes (camera offsets, occupancy-map params, velocity ranges, wheel geometry) with no method overrides needed.

See [`scripts/wheeled_robot_subclass.py`](scripts/wheeled_robot_subclass.py).

Reference implementations in `isaacsim.replicator.mobility_gen.examples.robots`:
- `JetbotRobot`: NVIDIA Jetbot, `wheel_base=0.1125`, `wheel_radius=0.03`, `chassis_subpath="chassis"`
- `CarterRobot`: Nova Carter, `wheel_base=0.413`, `wheel_radius=0.14`, `chassis_subpath="chassis_link"`

### Holonomic (e.g. Kaya 3-wheel)

Override `build()` to use a different controller and `write_action()` to remap the 2D action:

`KayaRobot(WheeledMobilityGenRobot)` — overrides `build()` to configure a `HolonomicController` from `HolonomicRobotUsdSetup`, and `write_action()` to map `[lin, ang]` to `[forward, lateral=0, yaw]`.

See [`scripts/holonomic_robot_subclass.py`](scripts/holonomic_robot_subclass.py).

### Policy-based (legged robots)

Subclass `PolicyMobilityGenRobot` and implement `build_policy()`. `write_action()` converts the 2D action `[lin_vel, ang_vel]` into the 3D command `[x, 0, yaw]` automatically.

```python
from isaacsim.replicator.mobility_gen.examples.robots import PolicyMobilityGenRobot
from isaacsim.replicator.mobility_gen.impl.robot import ROBOTS
from isaacsim.robot.policy.examples.robots import H1FlatTerrainPolicy
import numpy as np

@ROBOTS.register()
class MyLegedRobot(PolicyMobilityGenRobot):
    physics_dt: float = 0.005
    z_offset: float = 1.05
    usd_url = "/path/to/robot.usd"
    articulation_path = "pelvis"
    controller_z_offset: float = 1.05
    # ... same occupancy_map_*, random_action_*, path_following_* attrs as Wheeled ...

    @classmethod
    def build_policy(cls, prim_path: str):
        return H1FlatTerrainPolicy(prim_path=prim_path, position=np.array([0.0, 0.0, cls.controller_z_offset]))
```

Reference implementations: `H1Robot` (`articulation_path="pelvis"`) and `SpotRobot` (`articulation_path="/"`) in the same module.

### Replay with a custom robot

`replay_directory.py` calls `load_scenario()` which does `ROBOTS.get(config.robot_type)`. If the robot isn't in the built-in extension, this raises `KeyError`. **You cannot pass `--enable` to load an ad-hoc Python file** — either create a proper Isaac extension, or copy the replay loop into your own script and register the robot class before calling `load_scenario()`:

`replay_with_custom_robot(input_dir, custom_robot_class)` — register a custom robot class at runtime, then call `load_scenario()` for each recording directory.

See [`scripts/replay_custom_robot.py`](scripts/replay_custom_robot.py).

## Config / Data Format

`config.json` per recording:
```json
{
  "scenario_type": "RandomPathFollowingScenario",
  "robot_type": "CarterRobot",
  "scene_usd": "/path/to/warehouse.usd"
}
```

`state/common/<step>.npy` is a numpy dict: `position`, `orientation`, `joint_positions`, `joint_velocities`, `linear_velocity`, `angular_velocity`.

## Common Pitfalls

- **`ModuleNotFoundError: No module named 'isaacsim.replicator.mobility_gen'`**: Extensions aren't auto-loaded. Pass `--enable isaacsim.replicator.mobility_gen.examples` to `python.sh`. All extension imports must come AFTER `SimulationApp(...)`.
- **`AttributeError: 'World' object has no attribute 'initialize_simulation_context'`**: Only the async version exists (`initialize_simulation_context_async`). For standalone scripts, call `world.reset()` instead.
- **Replay `KeyError: 'MyRobot'`**: `replay_directory.py` only knows built-in robots. Write a wrapper script that registers your robot class before calling `load_scenario()`.
- **Custom robot produces no images during replay**: Missing `front_camera_*` attributes, or `build()` passes `front_camera=None`. Add the attributes and call `cls.build_front_camera(prim_path)` in `build()`.
- **`AttributeError: 'MyRobot' has no attribute 'chase_camera_base_path'`**: `chase_camera_base_path`, `chase_camera_x_offset`, `chase_camera_z_offset`, `chase_camera_tilt_angle` are required by `load_scenario()` even for headless recording.
- **Built-in replay fails to find robot class**: Pass `--enable isaacsim.replicator.mobility_gen.examples` so the examples extension registers its robots/scenarios before `load_scenario()` runs.
- **`physics_dt` mismatch**: Recording stores the physics timestep in `config.json`; replay uses the same `robot_type.physics_dt`. Do not change robot params between record and replay.
- **Occupancy map scale**: MobilityGen consumes the `OccupancyMap` produced by `occupancy-map`. Ensure `map.yaml` origin and resolution match the USD world coordinates.
- **Headless GPU**: Set `CUDA_VISIBLE_DEVICES=0 DISPLAY=:99` to avoid GPU contention with vLLM on GPUs 1-3.
