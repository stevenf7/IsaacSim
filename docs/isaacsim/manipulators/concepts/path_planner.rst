..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



Path Planner Algorithm
+++++++++++++++++++++++

.. note::
   For new development, consider using the newer experimental motion generation API in :doc:`Motion Generation (Experimental) <../../motion_generation/index>` and :doc:`cuMotion Integration <../../cumotion/index>`, which provide improved interfaces and additional features.

A :ref:`isaac_sim_path_planner` is an algorithm that outputs a series of configuration space waypoints, which
when linearly interpolated, produce a collision-free path from a starting c-space pose to a c-space or task-space target pose.
The `PathPlanner` class provides an interface that specifies the necessary functions that must be fulfilled to specify a path planning algorithm that can interface with |isaac-sim|.

An implementation is provided using the NVIDIA-developed **Lula** library (see :ref:`isaac_sim_motion_generation_rrt`).


.. _isaac_sim_path_planner:

Path Planner
===============

The `PathPlanner` interface specifies functions for computing a series of configuration space waypoints, which
when linearly interpolated, produce a collision-free path from a starting c-space pose to a c-space or task-space target pose.
A `PathPlanner` uses the same set of functions to interface with the USD world as a :ref:`isaac_sim_motion_policy`.
Like a :ref:`isaac_sim_motion_policy`,
an instance of the `PathPlanner` class is not expected to use the same USD robot representation as |isaac-sim|.  A `PathPlanner` can have its own internal
representation of the robot, and there are necessary interface functions for performing the mapping between the internal robot representation and the robot
`Articulation`.

Active and Watched Joints
--------------------------------

The robot `Articulation` in Isaac Sim comes from a loaded USD file.  This robot specification is not expected to perfectly match the specification used internally by a `PathPlanner`.

To perform the appropriate mapping, a `PathPlanner` has two functions it must fulfill: 

*  ``PathPlanner.get_active_joints()``: joints that the `PathPlanner` is going to directly control to achieve the desired end effector target.
*  ``PathPlanner.get_watched_joints()``: joints that the `PathPlanner` observes to plan motions, but will not actively control. These are assumed to remain constant when generating a path.
  
Both functions return a list of joint names in the order that the `PathPlanner` expects to receive them.    

For example, the Franka robot has nine degrees of freedom (DOFs): 

* seven revolute joints for controlling the arm
* two prismatic joints for controlling its gripper  
 
The robot `Articulation` exposes all nine degrees of
freedom, but :ref:`isaac_sim_motion_generation_rrt` only cares about the seven revolute joints when navigating the robot to a position target.  It is not appropriate for RRT to take
control of the gripper DOFs, because those DOFs can be controlled separately when performing a task such as pick-and-place.  ``RRT.get_active_joints()`` returns the names of the seven revolute joints
in the Franka robot.  ``RRT.get_watched_joints()`` returns an empty list because the joint states of the gripper DOFs are irrelevant when navigating the Franka's hand to a target position.
Every time `RRT` returns joint targets for the Franka, it is returning arrays of length seven.  When `RRT` is passed an argument such as ``active_joint_positions``,
it is expecting a vector of seven numbers that describe the joint positions of the Franka robot in the order specified by ``RRT.get_active_joints()``.

.. _isaac_sim_path_planner_world_state:

Inputs: World State
--------------------------------

|isaac-sim| provides a set of objects in ``isaacsim.core.api.objects`` that are intended to fully describe the simulated world. Only object primitives such as sphere and cone
are supported.  More advanced objects defined by meshes and point clouds will be added in a future release.  A `PathPlanner` has an  for each type of object that exists in
``isaacsim.core.api.objects`` for example:

.. math:: 
   
   PathPlanner.add_sphere(sphere: isaacsim.core.api.objects.sphere.*)
   
Objects in `isaacsim.core.api.objects` wrap objects that exist on the USD stage.
As objects move around on the stage, their location can be retrieved on each frame using the representative object from ``isaacsim.core.api.objects``.  This means that after a
`PathPlanner` has been passed an object, it can internally query the position of that object on the stage over time as needed.  A `PathPlanner` queries all relevant obstacle positions
from the ``isaacsim.core.api.objects`` that have been passed in when ``PathPlanner.update_world()`` is called, and passes the information to its internal world state.

It is not required that a specific `PathPlanner` actually implement an adder for every type of object that exists in ``isaacsim.core.api.objects``.  When a class inherits from `PathPlanner`,
any unimplemented adder functions will throw warnings.  For example, :ref:`isaac_sim_motion_generation_rrt`  supports spheres, capsules, and cuboids in its world representation.
In environments with cones, `RRT` will ignore the cone objects, and a warning will be printed for each cone object that gets added.

.. _isaac_sim_path_planner_robot_state:

Inputs: Robot State
--------------------------------

There are two methods for specifying robot state in a PathPlanner:

   * The base pose of the robot can be specified to a `PathPlanner` using ``PathPlanner.set_robot_base_pose()``.  If this function is never called, the policy implementation can make a reasonable assumption about the position of the robot.  :ref:`isaac_sim_motion_generation_rrt` assumes that the robot is at the origin of the stage until it is told otherwise.

   * ``PathPlanner.compute_path(active_joint_positions, watched_joint_positions)`` expects robot joint positions and velocities to be passed in using the order specified by ``PathPlanner.get_active_joints()`` and ``PathPlanner.get_watched_joints()``.

.. _isaac_sim_path_planner_output:

Outputs: Path
--------------------------------

``PathPlanner.compute_path(active_joint_positions, watched_joint_positions)`` returns a set of configuration space waypoints that can be linearly interpolated to produce a collision free trajectory to reach a target-pose.  The c-space configurations output by a PathPlanner will correspond only to the active joints returned by ``PathPlanner.get_active_joints()``.  The path output by a `PathPlanner` is difficult to use on its own; a linearly interpolated path will have sharp corners in c-space. But, a `PathPlanner` can be a useful component in generating a high-quality trajectory through difficult environments.

A helper class is provided with the `PathPlanner` interface to enable easy visualization of planned paths connected by linear interpolation in the :ref:`isaac_sim_path_planner_visualizer` class.

.. _isaac_sim_path_planner_visualizer:

Path Planner Visualizer
========================

The `PathPlannerVisualizer` class is provided to make it easy to visualize the path output by a `PathPlanner`.  This class handles the mapping between controllable DOFs in the robot `Articulation` and the active joints considered by the `PathPlanner`.

The main function of the class is ``PathPlannerVisualizer.compute_plan_as_articulation_actions(max_c-space_dist)``.  Calling this function queries the robot state from the robot `Articulation`, extracts and arranges the appropriate joints from the joint state
to use the ``PathPlanner.compute_path()`` function, linearly interpolates the result, and then creates a valid list of `ArticulationAction` that can be passed to the robot `Articulation` one by one to produce the planned path.  The `max_c-space_dist` function determines the density of the linear interpolation such that the L2 norm between any two c-space positions in the output is less than or equal to `max_c-space_dist`.
