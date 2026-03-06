.. _isaac_sim_cumotion_tutorial_trajectory_generator:

============================================
Trajectory Generator Tutorial
============================================

This tutorial explores how the :class:`TrajectoryGenerator` in the |cumotion| integration can be used to create smooth, time-optimal trajectories from waypoints or path specifications.

By the end of this tutorial, you'll understand:

* How to generate trajectories from C-space waypoints
* How to create and use path specifications
* How to convert between world coordinates and robot base frame coordinates
* How to execute trajectories using the :class:`Trajectory` interface

**Prerequisites**

- Review the :ref:`Robot Configuration tutorial <isaac_sim_cumotion_tutorial_robot_configuration>` to understand how to load robot configurations.
- Review the :doc:`Trajectory Planning and Execution <../motion_generation/trajectory_planning>` tutorial to understand the Trajectory interface.

To follow along with the tutorial, you can search and enable the **cuMotion Examples** extension within your running |isaac-sim_short| instance.
Within the ``isaacsim.robot_motion.cumotion.examples`` extension, there is an example of the :class:`TrajectoryGenerator` being used to generate trajectories
from C-space waypoints and path specifications.

Key Concepts
============

The :class:`TrajectoryGenerator` provides:

* **Unified Interface**: Single :class:`TrajectoryGenerator` class handles both C-space and task-space trajectory generation
* **Path Specifications**: Uses |cumotion|'s native path specification API directly
* **Time-Optimal**: Generates trajectories that are time-optimal while respecting joint velocity and acceleration limits
* **Direct API Access**: Full access to |cumotion|'s trajectory generator for parameter modification
* **Motion Generation API Integration**: Generated trajectories implement the :class:`Trajectory` interface

Initializing the Generator
==========================

Create a :class:`TrajectoryGenerator` with a robot configuration:

.. literalinclude:: ../snippets/cumotion/trajectory_generator_example.py
   :start-after: <start-initialize-generator-snippet>
   :end-before: <end-initialize-generator-snippet>
   :language: python

Configuring Trajectory Parameters
==================================

Access the underlying cuMotion trajectory generator to modify parameters. See the |cumotion| Python API documentation for available parameters and methods:

.. literalinclude:: ../snippets/cumotion/trajectory_generator_example.py
   :start-after: <start-configure-trajectory-parameters-snippet>
   :end-before: <end-configure-trajectory-parameters-snippet>
   :language: python

Generating from C-Space Waypoints
===================================

The simplest approach is to generate trajectories directly from C-space waypoints:

.. literalinclude:: ../snippets/cumotion/trajectory_generator_example.py
   :start-after: <start-generate-from-cspace-waypoints-snippet>
   :end-before: <end-generate-from-cspace-waypoints-snippet>
   :language: python

Generating from Path Specifications
====================================

For more complex paths, use |cumotion|'s path specification API. See the |cumotion| Python API documentation for available path specification methods:

.. literalinclude:: ../snippets/cumotion/trajectory_generator_example.py
   :start-after: <start-generate-from-path-spec-snippet>
   :end-before: <end-generate-from-path-spec-snippet>
   :language: python

Task-Space Path Specifications
================================

Task-space paths require coordinate conversion from Isaac Sim world frame to robot base frame. The |cumotion| integration includes helper functions to convert between Isaac Sim world-frame representation (position, quaternion tuple) to :class:`cumotion.Pose3` types in the robot base frame, since |cumotion| works entirely in the base frame:

.. literalinclude:: ../snippets/cumotion/trajectory_generator_example.py
   :start-after: <start-task-space-path-spec-snippet>
   :end-before: <end-task-space-path-spec-snippet>
   :language: python

Executing Trajectories
=======================

Once you have a trajectory, you can execute it in two ways:

.. note::
   These trajectory objects are not statefully tied to the :class:`Articulation` class in Isaac Sim. Therefore, the user must generally make sure to design trajectories that start at the current configuration space of the robot, *if* they intend to immediately execute that trajectory.

**Direct execution**: Sample the trajectory at each time step and apply the joint states directly to the articulation:

.. literalinclude:: ../snippets/cumotion/graph_planner_example.py
   :start-after: <start-execute-trajectory-directly-snippet>
   :end-before: <end-execute-trajectory-directly-snippet>
   :language: python

**Using TrajectoryFollower**: Use the :class:`TrajectoryFollower` controller from the Motion Generation API to integrate trajectory execution into a larger control system:

.. literalinclude:: ../snippets/cumotion/graph_planner_example.py
   :start-after: <start-execute-trajectory-with-follower-snippet>
   :end-before: <end-execute-trajectory-with-follower-snippet>
   :language: python

The :class:`TrajectoryFollower` follows the standard controller interface (``reset`` and ``forward``) and can be composed with other controllers in the Motion Generation API. For more details on trajectory execution, see the :doc:`Trajectory Planning and Execution <../motion_generation/trajectory_planning>` tutorial.

.. note::
   The ``scenario.py`` example uses :meth:`Articulation.set_dof_positions` to directly set physics state for perfect demonstration of the planned trajectory. Real robots require controllers to follow joint targets instead,
   and should use one of the aforementioned methods to execute the trajectory.

Example Usage
=============

.. note::
   To experiment with this tutorial interactively, see the ``scenario.py`` file in the ``isaacsim.robot_motion.cumotion.examples`` extension at ``isaacsim/robot_motion/cumotion/examples/trajectory_generator/scenario.py``.

The following video demonstrates trajectory generation as shown in the ``isaacsim.robot_motion.cumotion.examples`` extension.

.. figure:: images/trajectory_generator/isim_6.0_full_tut_viewport_trajectory_generator_normal_usage.webp
   :align: center
   :width: 100%

   Trajectory generator generating trajectories from C-space waypoints and path specifications

Summary
=======

This tutorial demonstrated:

1. **Generator Initialization**: Creating the :class:`TrajectoryGenerator` with a robot configuration
2. **Parameter Configuration**: Configuring trajectory generator parameters for advanced behavior
3. **C-Space Waypoints**: Generating trajectories directly from joint space waypoints
4. **Path Specifications**: Using |cumotion|'s native path specification API
5. **Task-Space Paths**: Converting world coordinates to base frame for task-space planning
6. **Trajectory Execution**: Using the :class:`Trajectory` interface to evaluate and apply trajectories over time

The |cumotion| trajectory generator provides a unified interface for both C-space and task-space trajectory generation while maintaining direct access to |cumotion|'s powerful features.

Next Steps
----------

* :ref:`Trajectory Optimizer tutorial <isaac_sim_cumotion_tutorial_trajectory_optimizer>` - Optimization-based trajectory planning
* :ref:`Graph Planner tutorial <isaac_sim_cumotion_tutorial_graph_planner>` - Collision-free path planning
* :ref:`RMPflow tutorial <isaac_sim_cumotion_tutorial_rmpflow>` - Reactive control
* |cumotion| library documentation - Complete path specification API
