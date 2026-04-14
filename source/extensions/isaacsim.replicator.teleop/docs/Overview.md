# Overview

The isaacsim.replicator.teleop extension provides the runtime for VR-driven teleoperation of robots in Isaac Sim. It manages OpenXR session connectivity, coordinate-frame conversion, visual frame markers, unified teleop profiles, and a set of controllers that translate VR headset and controller poses into robot joint targets, rigid-body velocities, or base movements.

## Key Components

### {class}`TeleopManager <isaacsim.replicator.teleop.TeleopManager>`

**Central orchestrator for the teleop session.** Manages the OpenXR connection lifecycle, distributes VR controller poses and input signals to all downstream controllers each simulation step, and exposes a command bus (`CONNECT`, `START`, `STOP`, `RESET`, `DISCONNECT`) that can be driven from the UI or programmatically via {func}`dispatch_command <isaacsim.replicator.teleop.dispatch_command>`.

### {class}`RobotIKController <isaacsim.replicator.teleop.RobotIKController>`

**Inverse-kinematics controller for articulated robot arms.** Takes a 6-DOF VR target pose and computes joint position targets. Supports per-side (left/right) configuration and four solver back-ends selectable via {class}`IKSolverType <isaacsim.replicator.teleop.IKSolverType>`:

- **Position-based** — single-iteration Jacobian differential IK
- **Velocity-based** — velocity-space IK with position integration
- **Levenberg–Marquardt** — multi-iteration LM solver per frame
- **PINK** — Pinocchio-based QP IK with a teleop-specific minimal USD-to-URDF export and selectable `daqp` / `osqp` QP back-ends

### {class}`FloatingRigidBodyController <isaacsim.replicator.teleop.FloatingRigidBodyController>`

**PD velocity controller for free rigid bodies** not attached to any articulation. Per-side configuration with tunable position/orientation gains and rotation offsets.

### {class}`GraspController <isaacsim.replicator.teleop.GraspController>`

**Maps VR trigger analog values to gripper joint targets** (0 = open, 1 = fully closed). Uses {class}`GraspConfig <isaacsim.replicator.teleop.GraspConfig>` and {class}`JointMapping <isaacsim.replicator.teleop.JointMapping>` loaded from YAML presets.

### {class}`LocomotionController <isaacsim.replicator.teleop.controllers.LocomotionController>`

**Kinematic base movement driven by VR thumbstick input.** Left thumbstick translates, right thumbstick rotates (yaw). Configurable speed multipliers and optional Tracking Space carry.

### {class}`MarkersManager <isaacsim.replicator.teleop.MarkersManager>`

**Visual frame markers** created on a session sublayer under `/Teleop/Markers` (origin, left, right, head). Visualize real-time VR controller poses in the viewport.

### {class}`XrAnchorManager <isaacsim.replicator.teleop.XrAnchorManager>`

**Headset camera anchor** at `/World/XRAnchor`. Supports a position offset, three rotation-tracking modes ({class}`AnchorRotationMode <isaacsim.replicator.teleop.AnchorRotationMode>`), and fixed-height lock.

### Coordinate Utilities

{func}`transform_pose <isaacsim.replicator.teleop.transform_pose>` and {func}`transform_pose_openxr_to_isaacsim <isaacsim.replicator.teleop.transform_pose_openxr_to_isaacsim>` convert OpenXR Y-up poses to Isaac Sim Z-up coordinates. The {class}`CoordinateSystem <isaacsim.replicator.teleop.CoordinateSystem>` enum selects the active conversion.

## Integration

The teleop session requires the Isaac Teleop CloudXR runtime to be running and the headset client
to be connected before {func}`TeleopManager.connect <isaacsim.replicator.teleop.TeleopManager.connect>`
is called. Start the runtime in another terminal with:

```bash
python -m isaacteleop.cloudxr
```

Keep that process running while using teleop. Then open the hosted
[Isaac Teleop Web Client](https://nvidia.github.io/IsaacTeleop/client/) from the headset browser and
follow the current connection steps in the
[Isaac Teleop Quick Start](https://nvidia.github.io/IsaacTeleop/main/getting_started/quick_start.html).
Connect from Isaac Sim after the CloudXR runtime is running and the headset client is connected.

## Functionality

### Teleop Profiles

{class}`TeleopProfile <isaacsim.replicator.teleop.TeleopProfile>` captures the complete state of a teleop session — session settings, floating/IK/grasp/locomotion controller configurations, and desired enabled states — in a single YAML file. The on-disk format mirrors the dataclass hierarchy, so adding or removing fields automatically updates the file format with no manual parsers or version checks. Profiles store the user's **intent** (desired enabled state) rather than runtime state, so a profile loaded before the stage is ready preserves its enable flags for later activation.

The profile hierarchy consists of:

- {class}`TeleopSettingsProfile <isaacsim.replicator.teleop.TeleopSettingsProfile>` — coordinate system, tracking space, marker scale, XR anchor offset/rotation/smoothing
- {class}`BimanualControllerProfile <isaacsim.replicator.teleop.BimanualControllerProfile>` — left/right {class}`ControllerSideProfile <isaacsim.replicator.teleop.ControllerSideProfile>` (enabled flag + settings dict), used by both Floating and IK controllers
- {class}`GraspControllerProfile <isaacsim.replicator.teleop.GraspControllerProfile>` — left/right {class}`GraspSideProfile <isaacsim.replicator.teleop.GraspSideProfile>` (enabled flag, prim path, config path)
- {class}`LocomotionProfile <isaacsim.replicator.teleop.LocomotionProfile>` — enabled flag + settings dict (prim path, speed multipliers)

```python
from isaacsim.replicator.teleop import (
    TeleopProfile,
    load_teleop_profile,
    save_teleop_profile,
    scan_teleop_profiles,
    get_builtin_teleop_profiles_dir,
)

# List built-in profiles
profiles = scan_teleop_profiles(get_builtin_teleop_profiles_dir())

# Load a profile
profile, errors = load_teleop_profile(profiles[0][1])

# Save a profile
save_teleop_profile("/path/to/my_profile.yaml", profile)
```

### Profile Validation

{func}`resolve_teleop_profile <isaacsim.replicator.teleop.resolve_teleop_profile>` validates a {class}`TeleopProfile` against the current USD stage, checking that referenced prims exist, carry the expected APIs (RigidBodyAPI, ArticulationRootAPI, Xformable), and that enum values and grasp configs are well-formed. It returns a {class}`TeleopResolutionReport <isaacsim.replicator.teleop.TeleopResolutionReport>` with structured {class}`TeleopResolverIssue <isaacsim.replicator.teleop.TeleopResolverIssue>` entries at error or warning severity. Validation is always explicit and user-triggered — opening the window or loading persistent settings does not produce terminal output.

### Programmatic Session Control

The teleop session can be controlled from scripts without the UI:

```python
from isaacsim.replicator.teleop import TeleopManager, dispatch_command

# Via command bus (fire-and-forget)
dispatch_command("connect")

# Via manager instance (direct control)
manager = TeleopManager()
manager.connect()
```
