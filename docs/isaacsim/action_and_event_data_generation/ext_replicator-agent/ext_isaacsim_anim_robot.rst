..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




====================================================================================
Animated Robot Controller
====================================================================================


The ``isaacsim.anim.robot.core`` extension enables realistic robot animation through the playback of captured simulation motion data. It bridges physics-based simulation and animation, allowing users to recreate precise robot movements without the computational overhead of real-time physics calculations. The extension converts physics-enabled robot models into animated representations while preserving their kinematic accuracy and visual fidelity.

``isaacsim.anim.robot.core`` integrates with the ``omni.metropolis.pipeline`` agent framework. Each robot is an ``AnimRobot`` -- a Metro Agent with a finite state machine that drives animation playback. Robots are configured through YAML files that define their kinematics, states, transitions, and animation data.


Supported Robots
------------------

The extension ships with sample configurations for the following robots:

- **Nova Carter** -- differential drive mobile robot
- **iw.hub** -- differential drive warehouse robot with lift capability
- **Forklift** -- differential drive forklift

Custom robots can be added by creating a new YAML configuration file (see `Customization`_).


Architecture
--------------

The extension is composed of several key modules:

- **AnimRobot** -- the agent class that integrates with ``omni.metropolis.pipeline``. It parses USD schema attributes, loads configuration, sets up the state machine, and manages the robot's lifecycle.
- **StateMachine** -- a finite state machine that manages animation states and transitions. Each state can have associated animation data that is played back on the robot's joints.
- **Actions** -- high-level commands (``MoveTo``, ``Idle``, ``Turn``, ``Sequence``) that drive the robot by updating the state machine and applying motion each frame.
- **Drive** -- drive-base implementations (``OmniDirectionalDrive``, ``DifferentialDrive``) that translate navigation paths into per-frame position and orientation updates.
- **PathPlanner** -- path planning backends. The ``NavMeshPathPlanner`` computes obstacle-avoiding paths using the navmesh; the base ``PathPlanner`` returns straight-line paths.
- **Behaviors** -- runtime behaviors (``Wander``, ``Patrol``, ``Halt``) and triggers (``Event``, ``Time``, ``Collision``) that compose actions into autonomous agent routines.


Customization
---------------

Robot behavior and animation can be customized by modifying or creating a YAML agent configuration file. Sample configurations are located at:
``{isaacsim.anim.robot.core extension path}/data/sample_configs/{robot type}.yaml``


Robot Attributes
------------------

The following attributes can be configured for each robot (based on the ``BaseAgentConfig`` schema):

- **agent_name** (str): Display name of the agent (default: ``"BaseAgent"``). Spaces are automatically replaced with underscores.
- **linear_velocity** (float): Forward movement speed in meters per second (default: ``1.0``, must be >= 0).
- **angular_velocity** (float): Turning speed in degrees per second (default: ``45.0``, must be >= 0).
- **forward_vec** (list[float]): Initial forward direction vector, exactly 3 elements (default: ``[1.0, 0.0, 0.0]``).
- **joints** (list[str]): List of joint prim relative paths that can be animated.
- **drive_base** (str): Robot's drive system type. Supported values: ``differential``, ``omni_directional`` (default: ``omni_directional``).
- **path_planner** (str): Path planner type. Supported values: ``navmesh``, ``base`` (default: ``navmesh``).
- **states** (list[str]): List of FSM state names (default: ``["idle", "turn_left", "turn_right", "forward"]``).
- **transitions** (dict[str, list[str]]): State transition graph defining valid transitions between states. Source and destination states are validated against the ``states`` list.
- **animation_paths** (dict[str, str]): Mapping of state names to folder paths containing animation USDs. Paths may use the ``${ext_path}`` variable to reference the extension's install directory.
- **asset_path** (str | null): Relative or absolute path/URL to the agent USD. If relative, it tries local file first, then the Isaac Sim asset root. If omitted, the prim's existing references are used.
- **radius** (float | null): Override the radius of the agent for path planning (must be >= 0). If not provided, the radius is calculated from the agent's bounding box.

**Example Configuration (iw_hub.yaml):**

.. code-block:: yaml

    agent_name: iw_hub
    linear_velocity: 0.5
    angular_velocity: 30.0
    forward_vec: [1.0, 0.0, 0.0]
    joints:
      - /chassis/lift
      - /chassis/left_wheel
      - /chassis/right_wheel
      - /chassis/left_swivel/left_caster
      - /chassis/right_swivel/right_caster
      - /chassis/left_swivel
      - /chassis/right_swivel
    drive_base: differential
    path_planner: navmesh
    animation_paths:
      turn_left: ${ext_path}/data/sample_animations/iw_hub/turn_left
      turn_right: ${ext_path}/data/sample_animations/iw_hub/turn_right
      forward: ${ext_path}/data/sample_animations/iw_hub/forward
      lift_up: ${ext_path}/data/sample_animations/iw_hub/lift_up
      lift_down: ${ext_path}/data/sample_animations/iw_hub/lift_down
    states: [idle, turn_left, turn_right, forward, lift_up, lift_down]
    transitions:
      idle: [turn_left, turn_right, idle, forward, lift_up, lift_down]
      turn_left: [forward, idle]
      turn_right: [forward, idle]
      forward: [turn_left, turn_right, idle]
      lift_up: [idle]
      lift_down: [idle]
    asset_path: Isaac/Samples/AnimRobot/iw_hub.usd
    radius: 0.8


Actions
---------

The extension provides the following action types for controlling robots programmatically:

- **MoveTo** -- moves the agent to a target ``[x, y, z]`` position using the configured path planner and drive base. The agent plans a path, then follows it by transitioning through turn and forward states.
- **Idle** -- keeps the agent in the idle state for a specified duration (in seconds).
- **Turn** -- rotates the agent in place to face a given 3D direction vector (yaw-only).
- **Sequence** -- executes a list of actions in order, one after another.

Actions can be created using functional APIs:

.. code-block:: python

    from isaacsim.anim.robot.core.action import move_to, idle, turn, sequence

    # Move to a position
    action = move_to(agent, state_machine, [10.0, 5.0, 0.0])

    # Idle for 3 seconds
    action = idle(agent, state_machine, 3.0)

    # Turn to face a direction
    action = turn(agent, state_machine, [0.0, 1.0, 0.0])

    # Execute a sequence of actions
    action = sequence([
        move_to(agent, state_machine, [10.0, 5.0, 0.0]),
        idle(agent, state_machine, 2.0),
        turn(agent, state_machine, [0.0, -1.0, 0.0]),
    ])

Each action can also be injected into a running agent through the ``execute()`` method, which finds the target agent in the ``AgentsManager`` and sets the action as the current command.


Behaviors
-----------

Behaviors define higher-level autonomous routines that compose actions. They are configured through the USD schema and run within the ``omni.metropolis.pipeline`` trigger system.

- **Wander** -- the robot moves to random navmesh-reachable points within a configurable distance range, then idles for a random duration. Configurable attributes include navigation areas, idle time range, and movement distance range.
- **Patrol** -- the robot visits a sequence of waypoints (specified as either ``[x, y, z]`` coordinates or USD prim targets) in order. Unreachable waypoints are skipped with a warning.
- **Halt** -- the robot idles for a random duration within a configurable time range.

These behaviors can be triggered by:

- **Event triggers** -- activated by external events
- **Time triggers** -- activated on a time schedule


Drive Types
-------------

The extension supports different drive-base implementations that control how the robot physically moves and turns:

- **OmniDirectionalDrive** -- the agent can move in any direction without needing to turn first. It navigates along a path with constant linear velocity and can independently rotate to face a target direction.
- **DifferentialDrive** -- the agent must turn in place to face the target direction before driving forward. It follows a turn-then-drive pattern: first rotating toward the next waypoint, then moving forward in a straight line.

The drive type is selected based on the ``drive_base`` field in the YAML configuration.


Customizing Animations
------------------------

To create custom animations:

1. Simulate the robot in Isaac Sim.
2. Use ``omni.kit.stagerecorder.core`` to capture motion data.
3. Update the ``animation_paths`` field in the YAML configuration with new animation folder paths.

Animation files should be organized in state-specific folders. Each joint's animation data is stored as a separate USD file named after the joint. For example, ``iw.hub``'s turn-left animation is located at:
``{isaacsim.anim.robot.core extension path}/data/sample_animations/iw_hub/turn_left/``

