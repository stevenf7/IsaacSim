..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



Trajectory Generation
+++++++++++++++++++++++++++++

In the Motion Generation extension, a workflow is provided for defining c-space and task-space trajectories.  An interface is provided for a :ref:`isaac_sim_trajectory` class:

* Trajectory Interface
* Articulation Trajectory
* Lula Trajectory Generator



.. _isaac_sim_trajectory:

Trajectory Interface
====================
An interface is provided in the Motion Generation extension for defining a robot trajectory.
An instance of the `Trajectory` interface must return robot c-space position as a continuous function of time within a specified time horizon.  A `Trajectory` has four basic accessors:

*   **start_time**: The earliest time at which this `Trajectory` will return a robot c-space position.

*   **end_time**: The latest time at which this `Trajectory` will return a robot c-space position.

*   **active_joints**: The names of the joints that this `Trajectory` is intended to control corresponding to the order the joint targets are returned.

*   **joint_targets(time)**: Joint position/velocity targets as a function of time between `start_time` and `end_time`.

An instance of the `Trajectory` class can be used to directly control a robot by using it to initialize an :ref:`isaac_sim_articulation_trajectory`.

.. _isaac_sim_articulation_trajectory:

Articulation Trajectory
=======================

The `ArticulationTrajectory` class is initialized using a robot `Articulation` and an instance of the `Trajectory` class.
This class handles the mapping from a defined `Trajectory` to controlling a simulated robot `Articulation`.  The `ArticulationTrajectory` class has two main functions:

*   **get_action_at_time(time)**: Return an `ArticulationAction` at a time that is within the time horizon of the provided `Trajectory` object.

*   **get_action_sequence(timestep)**: Return a list of `ArticulationAction` that interpolates between the provided `Trajectory` `start_time` and `end_time` by the specified timestep.  This is a convenience method for when the timestep of the physics simulator is known to be fixed.

As a `Trajectory` only defines the robot behavior within the provided time horizon, it is necessary to bring the robot `Articulation` to the initial state of the `Trajectory` before attempting to follow a sequence of generated `ArticultionAction`.

.. _isaac_sim_lula_trajectory_generator:

Lula Trajectory Generator
=========================

We provide a **Lula** implementation of a trajectory generator that can generate a `Trajectory` given c-space or task-space waypoints.  Two classes are provided:

* `LulaCSpaceTrajectoryGenerator`
* `LulaTaskSpaceTrajectoryGenerator`  
 
Both classes share the same required configuration information.

To configure Lula Trajectory Generators for a specific robot you must have the following files:

   * A URDF (universal robot description file), used for specifying robot kinematics as well as joint and link names. Position limits for each joint are also required. Other properties in the URDF are ignored and can be omitted; these include masses, moments of inertia, visual and collision meshes.

   * A supplemental robot description file in YAML format. In addition to enumerating the list of actuated joints that define the configuration space (c-space) for the robot, this file also includes sections for specifying the default c-space configuration, acceleration limits, or jerk limits. This file can also be used to specify fixed positions for unactuated joints.

Lula C-Space Trajectory Generator
--------------------------------------

The ``LulaCSpaceTrajectoryGenerator`` class takes in a series of c-space waypoints that correspond to the c-space coordinates listed in the required robot description YAML file.
The generator will use spline-based interpolation to connect the waypoints with an initial and final velocity of 0.
The trajectory is time-optimal -- that is, either the velocity, acceleration, or jerk limits are saturated at any given time to produce a trajectory with as short a duration as possible.
The generator will return an instance of the `Trajectory` interface.

Lula Task-Space Trajectory Generator
--------------------------------------

The ``LulaTaskSpaceTrajectoryGenerator`` class takes in a sequence of task-space targets and an end effector frame name (which must be a valid frame in the provided URDF file), and it returns an instance of the `Trajectory` interface if possible.

Task-space trajectories can be defined as a series of position and orientation targets.  In this case, the generated trajectory will linearly interpolate in task-space between the provided targets.

Task-space trajectories can also be defined using the ``lula.TaskSpacePathSpec`` class, which provides a set of useful primitives to connect task-space waypoints such as creating an arc, pure rotation, pure translation.

Internally, a task-space trajectory is converted to a c-space trajectory using the
:ref:`isaac_sim_lula_kinematics_solver`, and is then passed through the ``LulaCSpaceTrajectoryGenerator``.  For this reason, the ``LulaTaskSpaceTrajectoryGenerator`` class shares the same set of parameters as the ``LulaCSpaceTrajectoryGenerator`` class, with added parameters that affect how the task-space trajectory is converted to c-space.
