.. _isaac_sim_cumotion_tutorial_graph_planner:

===================================
Graph-Based Motion Planner Tutorial
===================================

This tutorial demonstrates how to use the :class:`GraphBasedMotionPlanner` class in the |cumotion| integration to find collision-free paths using sampling-based algorithms (RRT variants).

By the end of this tutorial, you'll understand:

* How to set up the graph-based motion planner with world state management
* How to plan to C-space, task-space, and translation-only targets
* How to execute planned paths using trajectories
* How to update world state for accurate planning

**Prerequisites**

- Review the :ref:`Robot Configuration tutorial <isaac_sim_cumotion_tutorial_robot_configuration>` to understand how to load robot configurations.
- Review the :ref:`World Interface tutorial <isaac_sim_cumotion_tutorial_world_interface>` to understand how to set up :class:`CumotionWorldInterface`.
- Review the :doc:`Trajectory Planning and Execution <../motion_generation/trajectory_planning>` tutorial to understand the Trajectory interface.

To follow along with the tutorial, run your |isaac-sim_short| instance. Then open **Window > Extensions**, search for **cuMotion Examples** (``isaacsim.robot_motion.cumotion.examples``), and enable it. If you cannot find it, remove ``@feature`` from the Extensions search bar and search again.
Within the ``isaacsim.robot_motion.cumotion.examples`` extension, there is a fully functional example of graph-based motion planning being used to plan collision-free paths.

Key Concepts
============

The |cumotion| graph-based motion planner provides:

* **Sampling-Based Planning**: Uses RRT variants to find collision-free paths
* **Multiple Target Types**: Supports C-space, task-space pose, and translation-only targets
* **Shared World State**: Uses the same :class:`CumotionWorldInterface` as other algorithms (often managed via :class:`WorldBinding`)
* **Path Interface**: Returns :class:`Path` objects from the Motion Generation API, which are directly convertible to :class:`Trajectory` objects (see the :doc:`Trajectory Planning and Execution <../motion_generation/trajectory_planning>` tutorial)

Initializing the Planner
========================

First, set up a :class:`CumotionWorldInterface` as described in the :ref:`World Interface tutorial <isaac_sim_cumotion_tutorial_world_interface>`. 
For convenience, we initialize the :class:`CumotionWorldInterface` with a :class:`WorldBinding` instance.
Once you have a :class:`CumotionWorldInterface`, you can create the planner:

.. literalinclude:: ../snippets/cumotion/graph_planner_example.py
   :start-after: <start-setup-planner-snippet>
   :end-before: <end-setup-planner-snippet>
   :language: python

Configuring Planner Parameters
==============================

Access the underlying cuMotion planner configuration to modify parameters:

.. literalinclude:: ../snippets/cumotion/graph_planner_example.py
   :start-after: <start-configure-planner-parameters-snippet>
   :end-before: <end-configure-planner-parameters-snippet>
   :language: python

Updating World State
=====================

The world binding must be updated before planning if obstacles or the robot base have moved:

.. literalinclude:: ../snippets/cumotion/graph_planner_example.py
   :start-after: <start-update-world-state-snippet>
   :end-before: <end-update-world-state-snippet>
   :language: python

Planning to C-Space Targets
=============================

The simplest planning target is a configuration space (joint space) position:

.. literalinclude:: ../snippets/cumotion/graph_planner_example.py
   :start-after: <start-plan-to-cspace-target-snippet>
   :end-before: <end-plan-to-cspace-target-snippet>
   :language: python

The planner returns a ``Path`` object containing waypoints that form a collision-free path.

Planning to Task-Space Targets
===============================

The planner can also plan to task-space pose targets. The ``plan_to_pose_target`` method takes world-frame coordinates directly:

.. literalinclude:: ../snippets/cumotion/graph_planner_example.py
   :start-after: <start-plan-to-pose-target-snippet>
   :end-before: <end-plan-to-pose-target-snippet>
   :language: python

Planning to Translation-Only Targets
=====================================

For cases where only position matters (not orientation), use translation-only planning. The ``plan_to_translation_target`` method takes world-frame coordinates directly:

.. literalinclude:: ../snippets/cumotion/graph_planner_example.py
   :start-after: <start-plan-to-translation-target-snippet>
   :end-before: <end-plan-to-translation-target-snippet>
   :language: python

Executing Planned Paths
========================

Planned paths are returned as :class:`Path` objects from the Motion Generation API. Paths cannot be executed directly - they must first be converted to :class:`Trajectory` objects. The :class:`Path` class provides a method to convert paths to minimal-time trajectories that respect velocity and acceleration limits.

First, convert the path to a trajectory:

.. literalinclude:: ../snippets/cumotion/graph_planner_example.py
   :start-after: <start-convert-path-to-trajectory-snippet>
   :end-before: <end-convert-path-to-trajectory-snippet>
   :language: python

.. note::
   These trajectory objects are not statefully tied to the :class:`Articulation` class in Isaac Sim. Therefore, the user must generally make sure to design trajectories that start at the current configuration space of the robot, *if* they intend to immediately execute that trajectory.

Once you have a trajectory, you can execute it in two ways:

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
   To experiment with this tutorial interactively, see the ``scenario.py`` file in the ``isaacsim.robot_motion.cumotion.examples`` extension at ``isaacsim/robot_motion/cumotion/examples/graph_planner/scenario.py``.

The following videos demonstrate graph-based motion planning as shown in the ``isaacsim.robot_motion.cumotion.examples`` extension.

The first video shows graph-based motion planning controlling the robot to reach a joint-space and task-space targets while avoiding obstacles in the scene.

.. figure:: images/graph_planner/isim_6.0_full_tut_viewport_graph_planner_normal_usage.webp
   :align: center
   :width: 100%

   Graph-based motion planning tracking joint-space and task-space targets while avoiding obstacles

The second video demonstrates adding a new obstacle to the scene, resetting the world state, and running the graph planner again. 
Objects are added in the same way as described in the :ref:`World Interface tutorial <isaac_sim_cumotion_tutorial_world_interface>`.
Inside the ``scenario.py`` file, a new ``CumotionWorldInterface`` is created for every plan. This is not generally necessary
if objects are not being added or removed from the scene.

.. figure:: images/graph_planner/isim_6.0_full_tut_viewport_graph_planner_adding_capsule.webp
   :align: center
   :width: 100%

   Adding an obstacle, resetting the cumotion world, and running the graph planner again

Summary
=======

This tutorial demonstrated:

1. **Planner Initialization**: Creating the :class:`GraphBasedMotionPlanner` with a :class:`CumotionWorldInterface` for world state management
2. **Planner Parameters**: Configuring the planner parameters for advanced behavior
3. **World Updates**: Keeping world state synchronized for accurate planning
4. **C-Space Planning**: Planning to joint configuration targets
5. **Task-Space Planning**: Planning to pose and translation-only targets
6. **Trajectory Execution**: Converting planned paths to trajectories and executing them directly or using TrajectoryFollower

The cuMotion graph-based motion planner provides powerful collision-free path planning capabilities while maintaining consistency with the centralized world state architecture.

Next Steps
----------

* :ref:`Trajectory Generator tutorial <isaac_sim_cumotion_tutorial_trajectory_generator>` - Smooth path execution
* :ref:`Trajectory Optimizer tutorial <isaac_sim_cumotion_tutorial_trajectory_optimizer>` - Optimization-based trajectory planning
* :ref:`World Interface tutorial <isaac_sim_cumotion_tutorial_world_interface>` - World state management
* :ref:`RMPflow tutorial <isaac_sim_cumotion_tutorial_rmpflow>` - Reactive control
* |cumotion| library documentation - Advanced planner configuration
