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


The ``isaacsim.anim.robot.core`` extension provides functionality for generating animated robots in Isaac Sim Replicator Agent (IRA). This extension is powered by `Behavior Script <https://docs.omniverse.nvidia.com/extensions/latest/ext_python-scripting-component/user_manual.html>`__ , which enables reactive behavior based on USD stage events.

``isaacsim.anim.robot.core`` generates animated robots by first simulating the robot, capturing its motion data, and then playing it back in the form of commands. Robots are simulated by ``isaacsim.robot.wheeled_robots`` for motions such as moving forward and turning round, which is recorded by ``omni.kit.stagerecorder.core``. Then, these motion capture data are converted into commands such as ``GoTo`` and ``Idle``.

``isaacsim.anim.robot.core`` supports Nova Carter and iw.hub robots, However, custom actors can be added by setting up its ``dataclass``.

Customization
---------------

Robot behavior and animation can be customized by modifying the agent configuration YAML file located at:
``{isaacsim.anim.robot.core extension path}/isaacsim/anim/robot/agent/configs/{robot type}.yaml``

Robot Attributes
------------------

The following attributes can be configured for each robot actor (based on the `BaseAgentConfig` schema):

- **agent_name** (str): Display name of the agent (default: "BaseAgent").
- **linear_velocity** (float): Forward movement speed in meters per second (m/s).
- **angular_velocity** (float): Turning speed in degrees per second (deg/s).
- **forward_vec** (list[float]): Initial forward direction vector (default: [1.0, 0.0, 0.0]).
- **joints** (list[str]): List of joint prim relative paths that can be animated.
- **drive_base** (str): Robot's drive system type. Supported values: ``differential``, ``omni_directional``.
- **path_planner** (str): Path planner type. Supported values: ``navmesh``, ``base`` (default: ``navmesh``).
- **states** (list[str]): List of Finite State Machine (FSM) state names (e.g., ``["idle", "turn_left", "turn_right", "forward"]``).
- **transitions** (dict[str, list[str]]): State transition graph defining valid transitions between states.
- **animation_paths** (dict[str, str]): Mapping of state names to folder paths containing animation USDs.
- **asset_path** (str | null): Relative or absolute path/URL to the agent USD. If relative, it tries local file first, then Isaac Sim asset root.
- **radius** (float | null): Override the radius of the agent for path planning. If not provided, the radius is calculated from the agent's bounding box.

**Example Configuration (iw_hub.yaml):**

.. code-block:: yaml

    agent_name: "iw_hub"
    linear_velocity: 0.5
    angular_velocity: 30.0
    forward_vec: [1.0, 0.0, 0.0]
    joints:
      - "/chassis/lift"
      - "/chassis/left_wheel"
      - "/chassis/right_wheel"
      - "/chassis/left_swivel/left_caster"
      - "/chassis/right_swivel/right_caster"
      - "/chassis/left_swivel"
      - "/chassis/right_swivel"
    drive_base: "differential"
    path_planner: "navmesh"
    animation_paths:
      turn_left: "${ext_path}/data/iw_hub/turn_left"
      turn_right: "${ext_path}/data/iw_hub/turn_right"
      forward: "${ext_path}/data/iw_hub/forward"
      lift_up: "${ext_path}/data/iw_hub/lift_up"
      lift_down: "${ext_path}/data/iw_hub/lift_down"
    states: ["idle", "turn_left", "turn_right", "forward", "lift_up", "lift_down"]
    transitions:
      idle: ["turn_left", "turn_right", "idle", "forward", "lift_up", "lift_down"]
      turn_left: ["forward"]
      turn_right: ["forward"]
      forward: ["turn_left", "turn_right", "idle"]
      lift_up: ["idle"]
      lift_down: ["idle"]
    asset_path: "Isaac/Samples/AnimRobot/iw_hub.usd"

Customizing Animations
------------------------

To create custom animations:

1. Simulate the robot in Isaac Sim.
2. Use ``omni.kit.stagerecorder.core`` to capture motion data.
3. Update the ``animation_paths`` attribute with new animation file paths.

Animation files should be organized in state-specific folders. For example, ``iw.hub``'s turn-left animation is located at:
``{Isaac Sim App Path}/extcache/isaacsim.anim.robot.core/data/iw_hub/turn_left/``

Store each joint's animation data in a file named after the joint.

