# Overview

The isaacsim.replicator.teleop.ui extension provides the desktop UI for VR teleoperation in Isaac Sim. It creates a window accessible from **Tools > Replicator > Teleop** that exposes all configuration and control surfaces for the `isaacsim.replicator.teleop` runtime.

## Key Components

### {class}`TeleopUIExtension <isaacsim.replicator.teleop.ui.TeleopUIExtension>`

**Kit extension entry point.** Registers the **Tools > Replicator > Teleop** menu item and manages the lifecycle of the {class}`TeleopWindow`.

### {class}`TeleopWindow <isaacsim.replicator.teleop.ui.teleop_window.TeleopWindow>`

**Main window** that composes six panels in a scrollable layout: Profiles, Session, Floating, IK, Grasp, and Locomotion. It instantiates {class}`TeleopManager <isaacsim.replicator.teleop.TeleopManager>`, {class}`MarkersManager <isaacsim.replicator.teleop.MarkersManager>`, and all four controllers, then wires them to the corresponding panels. All panel settings persist under `/persistent/exts/isaacsim.replicator.teleop/`.

## UI Panels

### Profiles Panel

Save, load, delete, and validate unified {class}`TeleopProfile <isaacsim.replicator.teleop.TeleopProfile>` YAML files that capture the complete state of every panel — including each controller's desired enabled state. Profiles are stored in a configurable directory (defaults to the built-in `data/teleop_profiles/`).

- **Load** restores all panel values and optionally resolves prim paths against the current stage. If the stage is not ready, values are applied with deferred activation — the desired enabled state is preserved so controllers activate once the stage becomes available.
- **Save** collects the current panel state (using desired-enabled intent, not runtime state) with overwrite confirmation.
- **Delete** removes a selected profile from disk.
- **Validate** runs {func}`resolve_teleop_profile <isaacsim.replicator.teleop.resolve_teleop_profile>` and reports errors and warnings inline.

The last-used profile is automatically restored when the window opens. Profile validation is user-triggered and does not produce terminal output during passive operations like window open or stage load.

### Session Panel

OpenXR connection controls (**Connect** / **Disconnect**), frame marker management (**Show** / **Remove** with adjustable scale), Tracking Space prim selection with coordinate system dropdown, XR Anchor configuration (position offset, rotation mode, smoothing, fixed-height lock), and a **Debug** section with synthetic input controls (thumbstick sliders, trigger sliders, locomotion buttons) and a **Write Backend** dropdown to override the global XformPrim backend (USD / USD-RT / Fabric).

### Floating Controller Panel

Per-side (left/right) controls for {class}`FloatingRigidBodyController <isaacsim.replicator.teleop.FloatingRigidBodyController>`: prim path field with auto-validation, position and orientation PD gain sliders (live-editable during Play), rotation offset dropdown, enable/disable toggle, and YAML preset save/load.

### IK Controller Panel

Per-side controls for {class}`RobotIKController <isaacsim.replicator.teleop.RobotIKController>`: articulation prim path with auto-populated end-effector link dropdown, solver selection across the four IK back-ends, method / gain / damping controls where applicable, PINK QP solver selection (`daqp` or `osqp`) with advanced PINK tuning rows, rotation offset dropdown, enable/disable toggle, and YAML preset save/load.

### Grasp Controller Panel

Per-side controls for {class}`GraspController <isaacsim.replicator.teleop.GraspController>`: prim path field, built-in YAML config selector, and configure/enable/disable buttons.

### Locomotion Panel

Controls for {class}`LocomotionController <isaacsim.replicator.teleop.controllers.LocomotionController>`: target prim path, slide and turn speed multipliers, Carry Tracking Space toggle, and enable/disable toggle. Horizontal movement is projected onto the world ground plane using the prim's heading, so axes remain correct regardless of the target prim's local frame orientation. Two workflows are supported:

- **Robot base** — set the prim path to a robot base link. Carry Tracking Space can be toggled to co-move the VR origin with the robot.
- **VR origin** — set the prim path to the built-in tracking-space origin marker. Carry is implicit because the locomotion prim *is* the VR origin. Use this for floating grippers that have no physical base.
