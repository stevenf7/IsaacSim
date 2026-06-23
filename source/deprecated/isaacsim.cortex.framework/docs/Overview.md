# Overview

```{deprecated} 6.0.0
This extension has been deprecated and will be replaced by open source equivalents and simple examples.
```

`**isaacsim.cortex.framework**` provides a robotics behavior framework for building reactive manipulation applications in Isaac Sim. It combines decider networks, state machines, motion commanders, robot command APIs, object pose tracking, and a Cortex-specific world loop into one coordinated control pipeline.

The framework is centered on writing behaviors that observe logical state, choose actions, and send commands to robots every simulation cycle. It is especially useful for task-level robot logic where motion, gripper control, obstacle handling, and perception-derived object state need to work together.

## Concepts

### Cortex Pipeline

`CortexWorld` extends `**isaacsim.core.api.World**` with a Cortex processing pipeline. Each simulation step processes:

1. Logical state monitors
2. Behaviors
3. Robot commanders
4. The underlying simulation step

This ordering lets behaviors make decisions from updated logical state before commands are applied to robots.

### Decider Networks

Decider networks are behavior trees built from `DfDecider` nodes. Each decider chooses one child by returning a `DfDecision`, and the framework tracks the active path from the root to the leaf.

The active path is treated as a decision session. When the path changes, nodes that leave the path receive `exit()`, and nodes that enter the new path receive `enter()`. Nodes that remain active continue receiving `decide()` each step.

`DfAction` is the leaf-style decider used for actions. It automatically calls `step()` from `decide()`, so action nodes can focus on what they do each cycle.

### Logical State

`DfLogicalState` represents context shared across a behavior. It owns logical state monitors, which are ordered callback functions used to update state before decisions are made.

A context can hold robot handles, perception state, task flags, obstacle monitors, or any other information needed by decider nodes and state machines.

### Commanders

A `Commander` controls a subset of articulation joints. Behavior code sends commands into a commander, and the commander processes the latest command during the robot command phase.

This separates high-level decisions from low-level command processing. For example, a behavior can send an end-effector target to `MotionCommander`, while the commander handles policy stepping and articulation actions.

## Key Components

### CortexWorld

`CortexWorld` is the main runtime container for Cortex applications. It manages logical state monitors, behaviors, and commandable robots.

Common additions include:

- `add_logical_state_monitor()` for adding logical state update objects.
- `add_behavior()` for adding a `DfBehavior`.
- `add_decider_network()` for adding a `DfNetwork` and its monitors together.
- `add_robot()` for adding a `CommandableArticulation`.

`CortexWorld.step()` runs the Cortex pipeline before stepping the simulator.

### DfNetwork

`DfNetwork` is the main behavior object for decider networks. It takes a root `DfDecider`, optional parameters, optional logical state monitors, and an optional context.

Each call to `step()` processes monitors first, then descends the decider network from the root to a leaf. The active context is either the context passed into `step()` or the context previously bound with `bind_context()`.

### State Machines

The framework includes state machine primitives for behavior logic that is easier to express as transitions:

- `DfState` defines `enter()`, `step()`, `exit()`, and `process_step()`.
- `DfStateSequence` runs terminal states in order, optionally looping.
- `DfHierarchicalState` runs an internal state machine from inside one state.
- `DfStateMachineDecider` wraps a state machine so it can be used as a decider node.
- `DfHsmAction` wraps a state machine as a `DfAction`.

These can be mixed with decider networks when part of a task needs sequential or hierarchical execution.

### MotionCommander

`MotionCommander` sends end-effector targets to an `ArticulationMotionPolicy`. It supports full pose targets, position-only targets, optional approach behavior, posture configuration, and optional command smoothing.

Targets are represented by `MotionCommand`:

- `target_pose` for full position and orientation targets.
- `target_position` for position-only targets.
- `approach_params` for funnel-style approach behavior.
- `posture_config` for null-space posture biasing.

`MotionCommander` also tracks obstacles added to the underlying motion policy. Obstacles added through `add_obstacle()` are re-added after reset so the obstacle set remains consistent.

### Robot Command APIs

`CortexRobot` wraps a commandable articulation and lets users attach named commanders, such as `arm` or `gripper`.

Built-in robot helpers include:

- `MotionCommandedRobot`, a robot with a motion commander available as `arm`.
- `CortexFranka`, a Franka robot with arm and gripper commanders.
- `CortexUr10`, a UR10 robot with end-effector and suction gripper support.
- `add_franka_to_stage()` and `add_ur10_to_stage()` for adding supported robot assets to the stage and wrapping them.

`CortexGripper` provides a base API for parallel grippers, including `open()`, `close()`, `move_to()`, and `close_to_grasp()`. `FrankaGripper` implements the width-to-joint mapping for the Franka finger joints.

### CortexObject

`CortexObject` wraps a `SingleXFormPrim` and stores perception-style measured pose data. It can report whether a measured pose is still valid, expose measured pose as `(p, q)` or a transform matrix, and synchronize the underlying USD object to the measured pose.

`CortexMeasuredPose` stores the measured pose, timestamp, and timeout used to determine whether a measurement is still valid.

### Obstacle Monitors

`ObstacleMonitor` manages when a collection of obstacles should be enabled or disabled in a `MotionCommander`. Derived classes implement `is_obstacle_required()` to define the condition for enabling obstacles.

`ObstacleMonitorContext` is a logical state context that tracks obstacle monitors and automatically adds their `step()` methods as logical state monitors.

## Functionality

### Reactive Behavior Authoring

The framework supports reactive task plans through decider networks. A decider can choose different child behaviors every cycle based on the current context, allowing task execution to adapt when state changes.

`DfRldsDecider` and `DfRldsNode` implement a Robust Logical Dynamical System style decision protocol. Nodes are ordered by priority, and the decider chooses the highest-priority node whose enterable or runnable condition is satisfied.

### End-Effector Targeting

The framework provides reusable deciders for common manipulation motions:

- `DfGoTarget` sends a `MotionCommand` to `context.robot.arm`.
- `DfApproachTarget` computes approach parameters for a target transform.
- `DfApproachTargetLinearly` interpolates targets so the end-effector moves in a straight line.
- `DfLift` lifts the end-effector along a selected base-frame axis.
- `DfMoveEndEffectorRel` moves relative to the end-effector pose measured on entry.
- `make_go_home()` creates a decider that sends the robot to its home position.

### Gripper Actions

Simple gripper actions are provided as decider nodes:

- `DfOpenGripper`
- `DfCloseGripper`
- `DfMoveGripper`

These actions assume the context exposes a robot with a gripper command API.

### Math and Timing Utilities

The framework includes utilities for transform math, quaternion conversion, projection, unit conversion, and cycle timing.

Common math utilities include:

- `pq2T()` and `T2pq()` for pose conversion.
- `pack_Rp()` and `unpack_T()` for transform construction and decomposition.
- `invert_T()` for homogeneous transform inversion.
- `transforms_are_close()` for threshold-based pose comparison.
- `proj_R()` and `proj_T()` for projecting approximate rotations back to valid rotations.

Timing helpers include `SteadyRate`, `CycleTimer`, and `Profiler`.

## Usage Examples

### Create a Basic Decider Action

```python
from isaacsim.cortex.framework.df import DfAction
from isaacsim.cortex.framework.dfb import DfBasicContext

class OpenGripperAction(DfAction):
    def enter(self):
        self.context.robot.gripper.open()

context = DfBasicContext(robot)
action = OpenGripperAction()
action.bind(context, params=None)
action.enter()
action.step()
```

### Build and Add a Decider Network

```python
from isaacsim.cortex.framework.df import DfNetwork, DfDecider, DfDecision
from isaacsim.cortex.framework.cortex_world import CortexWorld

class RootDecider(DfDecider):
    def __init__(self):
        super().__init__()
        self.add_child("open", OpenGripperAction())

    def decide(self):
        return DfDecision("open")

world = CortexWorld()
network = DfNetwork(root=RootDecider(), context=context)

world.add_decider_network(network, name="example_behavior")
```

### Send an End-Effector Command

```python
import numpy as np
from isaacsim.cortex.framework.motion_commander import MotionCommand

target_position = np.array([0.4, 0.0, 0.3])

command = MotionCommand(target_position=target_position)
robot.arm.send(command)
```

Or use the convenience method:

```python
robot.arm.send_end_effector(target_position=target_position)
```

## Integration

`**isaacsim.cortex.framework**` builds directly on Isaac Sim robot and world abstractions.

- `CortexWorld` extends `**isaacsim.core.api.World**` to add the logical-state, behavior, and commander pipeline.
- `CortexRobot` and `CommandableArticulation` build on `SingleArticulation` for robot control.
- `CortexObject` wraps `SingleXFormPrim` for pose access and measured-pose synchronization.
- `MotionCommander` uses `ArticulationMotionPolicy` and its underlying `MotionPolicy` to process end-effector motion commands.
- Robot initialization methods accept `**omni.physics.tensors.SimulationView**` where needed by the underlying articulation initialization.

## Considerations

Decider network topology should be acyclic. The descent algorithm expects termination, but the topology is not explicitly verified.

`MotionCommand` expects either `target_pose` or `target_position`, but not both. Supplying both, or supplying neither, raises a `TypeError`.

Several components assume a conventional Cortex context shape. For example, manipulation deciders such as `DfGoTarget`, `DfLift`, and gripper actions expect access to robot APIs through fields like `context.robot.arm` and `context.robot.gripper`.
