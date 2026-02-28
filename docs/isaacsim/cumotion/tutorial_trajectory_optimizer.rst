.. _isaac_sim_cumotion_tutorial_trajectory_optimizer:

===========================================
Trajectory Optimizer Tutorial
===========================================

.. note::
   **Windows Support**: The :class:`TrajectoryOptimizer` is not currently available on Windows.

This tutorial demonstrates how to use the :class:`TrajectoryOptimizer` class in the |cumotion| integration to plan collision-free, kinematically constrained trajectories to configuration space or task space targets.

By the end of this tutorial, you'll understand:

* How to create and configure the :class:`TrajectoryOptimizer`
* How to plan trajectories to configuration space targets
* How to plan trajectories to task-space targets
* How to execute optimized trajectories
* How to configure optimization parameters

**Prerequisites**

- Review the :ref:`Robot Configuration tutorial <isaac_sim_cumotion_tutorial_robot_configuration>` to understand how to load robot configurations.
- Review the :doc:`Trajectory Planning and Execution <../motion_generation/trajectory_planning>` tutorial to understand the :class:`Trajectory` interface.
- Review the :ref:`World Interface tutorial <isaac_sim_cumotion_tutorial_world_interface>` to understand how to set up :class:`CumotionWorldInterface`.

To follow along with the tutorial, you can search and enable the **cuMotion Examples** extension within your running |isaac-sim_short| instance.
Within the ``isaacsim.robot_motion.cumotion.examples`` extension, there is a fully functional example of trajectory optimization including collision-free planning and trajectory execution.

Key Concepts
============

The :class:`TrajectoryOptimizer` provides global optimization-based trajectory planning that:

* **Plans collision-free trajectories**: Uses obstacle information from :class:`CumotionWorldInterface` to avoid collisions
* **Respects kinematic constraints**: Generates trajectories that respect joint limits, velocity, and acceleration constraints
* **Supports multiple target types**: Can plan to configuration space targets, task space targets, or task space goalsets
* **Returns Trajectory objects**: Optimized trajectories implement the :class:`Trajectory` interface, enabling use with :class:`TrajectoryFollower`

The optimizer requires a :class:`CumotionWorldInterface` instance to provide obstacle information for collision avoidance. The :ref:`World Interface tutorial <isaac_sim_cumotion_tutorial_world_interface>` shows how to set up a :class:`CumotionWorldInterface`, often using :class:`WorldBinding` for convenience.

Initializing the Optimizer
===========================

First, set up a :class:`CumotionWorldInterface` as described in the :ref:`World Interface tutorial <isaac_sim_cumotion_tutorial_world_interface>`. Once you have a :class:`CumotionWorldInterface`, you can create the optimizer:

.. literalinclude:: ../snippets/cumotion/trajectory_optimizer_example.py
   :start-after: <start-setup-optimizer-snippet>
   :end-before: <end-setup-optimizer-snippet>
   :language: python

The optimizer needs:

* **Robot configuration**: A |cumotion| robot configuration (retrieved via :func:`load_cumotion_supported_robot`). See the :ref:`Robot Configuration tutorial <isaac_sim_cumotion_tutorial_robot_configuration>` for details on loading robot configurations.
* **World interface**: A :class:`CumotionWorldInterface` instance
* **Joint space**: The controlled joint names (use ``cumotion_robot.controlled_joint_names``, not ``articulation.dof_names``)

Accessing cuMotion Parameters
==============================

The optimizer provides access to the underlying |cumotion| trajectory optimizer configuration for parameter modification:

.. literalinclude:: ../snippets/cumotion/trajectory_optimizer_example.py
   :start-after: <start-access-parameters-snippet>
   :end-before: <end-access-parameters-snippet>
   :language: python

For a complete list of available parameters and their usage, see the |cumotion| Python and C++ API documentation.

Updating World State
=====================

The world interface must be updated before planning if obstacles or the robot base have moved:

.. literalinclude:: ../snippets/cumotion/trajectory_optimizer_example.py
   :start-after: <start-update-world-state-snippet>
   :end-before: <end-update-world-state-snippet>
   :language: python

Planning to Configuration Space Targets
========================================

The optimizer can plan to configuration space targets using :class:`cumotion.TrajectoryOptimizer.CSpaceTarget`:

.. literalinclude:: ../snippets/cumotion/trajectory_optimizer_example.py
   :start-after: <start-plan-to-cspace-target-snippet>
   :end-before: <end-plan-to-cspace-target-snippet>
   :language: python

The :meth:`plan_to_goal` method returns a :class:`CumotionTrajectory` if planning succeeds, or ``None`` if planning fails. The trajectory implements the :class:`Trajectory` interface.

Planning to Task-Space Targets
================================

The optimizer can also plan to task-space targets using :class:`cumotion.TrajectoryOptimizer.TaskSpaceTarget`. Task-space targets require converting from Isaac Sim world frame to the robot base frame:

.. literalinclude:: ../snippets/cumotion/trajectory_optimizer_example.py
   :start-after: <start-plan-to-task-space-target-snippet>
   :end-before: <end-plan-to-task-space-target-snippet>
   :language: python

The |cumotion| integration includes helper functions (like :func:`isaac_sim_to_cumotion_pose`) to convert between Isaac Sim world-frame representation (position, quaternion tuple) and |cumotion| types in the robot base frame, since |cumotion| works entirely in the base frame.

Optional: Checking for Collisions
===================================

Before planning, you can check if the initial or target configurations are in collision:

.. literalinclude:: ../snippets/cumotion/trajectory_optimizer_example.py
   :start-after: <start-check-collisions-snippet>
   :end-before: <end-check-collisions-snippet>
   :language: python

Executing Trajectories
======================

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

Example Usage
=============

.. note::
   To experiment with this tutorial interactively, see the ``scenario.py`` file in the ``isaacsim.robot_motion.cumotion.examples`` extension at ``isaacsim/robot_motion/cumotion/examples/trajectory_optimizer/scenario.py``.

The following videos demonstrate trajectory optimization as shown in the ``isaacsim.robot_motion.cumotion.examples`` extension.

The first video shows trajectory optimization planning trajectories to configuration space and task space targets while avoiding obstacles in the scene.

.. figure:: images/trajectory_optimizer/isim_6.0_full_tut_viewport_trajectory_optimizer_normal_usage.webp
   :align: center
   :width: 100%

   Trajectory optimizer planning trajectories to configuration space and task space targets while avoiding obstacles

The second video demonstrates adding a new obstacle to the scene, resetting the world state, and running the graph planner again. 
Objects are added in the same way as described in the :ref:`World Interface tutorial <isaac_sim_cumotion_tutorial_world_interface>`.
Inside the ``scenario.py`` file, a new ``CumotionWorldInterface`` is created for every plan. This is not generally necessary
if objects are not being added or removed from the scene.

.. figure:: images/trajectory_optimizer/isim_6.0_full_tut_viewport_trajectory_optimizer_adding_sphere.webp
   :align: center
   :width: 100%

   Adding an obstacle, resetting the cumotion world, and running the trajectory optimizer again

Summary
=======

This tutorial demonstrated:

1. **Optimizer Initialization**: Creating the :class:`TrajectoryOptimizer` with a :class:`CumotionWorldInterface` for obstacle awareness
2. **Parameter Access**: Accessing underlying |cumotion| objects for advanced configuration
3. **World Updates**: Keeping world state synchronized for accurate planning
4. **Configuration Space Planning**: Planning trajectories to configuration space targets using :class:`CSpaceTarget`
5. **Task-Space Planning**: Planning trajectories to task-space targets using :class:`TaskSpaceTarget`
6. **Collision Checking**: Optionally checking for collisions before planning
7. **Trajectory Execution**: Executing optimized trajectories using the :class:`Trajectory` interface

The :class:`TrajectoryOptimizer` provides global, optimization-based trajectory planning that generates smooth, collision-free trajectories while respecting kinematic constraints.

.. note::
   This tutorial covers the basic usage of the :class:`TrajectoryOptimizer` for configuration space and task-space targets. The |cumotion| library provides many additional capabilities including task-space goalsets, path constraints, axis constraints, and advanced optimization parameters. For complete documentation of all available features, see the official |cumotion| Python and C++ API documentation.

Next Steps
----------

* :ref:`World Interface tutorial <isaac_sim_cumotion_tutorial_world_interface>` - World state management
* :ref:`RMPflow tutorial <isaac_sim_cumotion_tutorial_rmpflow>` - Reactive control
* :ref:`Trajectory Generator tutorial <isaac_sim_cumotion_tutorial_trajectory_generator>` - Time-optimal trajectory generation
* :ref:`Graph Planner tutorial <isaac_sim_cumotion_tutorial_graph_planner>` - Sampling-based path planning
* |cumotion| library documentation - Advanced parameter configuration and task space planning
