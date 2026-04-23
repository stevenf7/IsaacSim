..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




====================================================================================
Animated Robot Behavior Tree Nodes
====================================================================================


The ``isaacsim.anim.robot.bt_nodes`` extension ships a small library of behavior-tree action and modifier nodes that drive an ``AnimRobot`` from within an ``omni.behavior.tree`` tree. These are the nodes the robot-side generator targets and the ones a hand-authored tree should use to command a robot.

Each node binds to a USD prim carrying ``AnimRobotAPI`` and operates on the live runtime agent resolved for that prim. If the runtime is not yet ready (for example, the timeline has just started or the agent's configuration is still loading), the node returns ``RUNNING`` while it waits; if the agent never becomes available, the node ultimately returns ``FAILURE``.


Action Nodes
--------------

Action nodes schedule work on the robot. They return ``RUNNING`` while the underlying action ticks, ``SUCCESS`` when the action completes, and ``FAILURE`` when the bound prim is missing its ``AnimRobotAPI``, the agent cannot be resolved, or a required input is missing.

**RobotMoveTo**
    Moves the agent to a target position using the configured path planner and drive base.

    Inputs:

    - ``target_object`` (``str``, default ``""``) -- path of a USD prim to move to. When non-empty, the node tracks the prim as it moves and replans if it drifts past the follow threshold. Takes precedence over ``target_position``.
    - ``target_position`` (``Float3``, default ``(0, 0, 0)``) -- world-space coordinate to move to. Used only when ``target_object`` is empty.

**RobotTurn**
    Rotates the agent in place (yaw-only) to face a given world-space direction.

    Inputs:

    - ``direction`` (``Float3``, default ``(1, 0, 0)``) -- direction vector the agent should face. The Z component is ignored.

**RobotIdle**
    Holds the agent in its idle state for a fixed duration.

    Inputs:

    - ``duration`` (``float``, default ``0.0``) -- seconds to remain idle.

**RobotPlayAnimation**
    Plays a named FSM state on the agent.

    Inputs:

    - ``state_name`` (``str``, default ``""``) -- name of the FSM state to play. Required; the node returns ``FAILURE`` immediately if left empty or if the name is not declared in the agent's ``states`` list.
    - ``duration`` (``float``, default ``0.0``) -- seconds to hold the state. When ``0``, the state plays once to its last animation sample and the node completes.


Modifier Nodes
----------------

**RobotIsInState**
    Decorator that gates its child subtree on the agent's current FSM state. The child only ticks when the state machine reports that it is in the named state; otherwise the condition reads as unmet and the child is skipped for that tick.

    Inputs:

    - ``state_name`` (``str``, default ``""``) -- name of the FSM state to match. An empty value or a mismatched state blocks the child from ticking.
