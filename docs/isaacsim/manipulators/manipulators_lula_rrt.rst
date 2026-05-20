.. _isaac_sim_app_tutorial_motion_generation_rrt:

============================
Lula RRT
============================

.. admonition:: Deprecated
   :class: warning

   For new development, consider using the newer :doc:`Robot Motion (Experimental) <../../robot_motion_experimental/index>` API, which provides improved interfaces and additional features over Lula.

This tutorial shows how the :ref:`isaac_sim_motion_generation_rrt` class in the :ref:`isaac_sim_motion_generation` extension can be used to
produce a collision free path from a starting configuration space (c-space) position to a c-space or task-space target.


Getting Started
===============

**Prerequisites**

- Complete the :ref:`isaac_sim_app_tutorial_core_adding_manipulator` tutorial prior to beginning this tutorial.
- You can reference the Lula Robot Description Editor to understand how to generate your own robot_description.yaml file to be able to use RRT on unsupported robots.
- Review the :ref:`Loaded Scenario Extension Template <isaac_sim_app_tutorial_extension_templates_loaded_scenario>` to understand how this tutorial is structured and run.

To follow along with the tutorial, run your Isaac Sim 6.0 instance. Then open **Window > Extensions**, search for **Motion Generation Examples** (``isaacsim.robot_motion.motion_generation.examples``), and enable it. If you cannot find it, remove ``@feature`` from the Extensions search bar and search again.
Within the `isaacsim.robot_motion.motion_generation.examples` extension, there is a fully functional example of RRT being used to plan to a task-space target.
The sections of this tutorial build up the file ``scenario.py`` from basic functionality to the completed code.

.. note::
   **Motion Generation Examples** (``isaacsim.robot_motion.motion_generation.examples``) are deprecated **since Isaac Sim 6.0.0**. In the Isaac Sim source repository they live under ``source/deprecated/isaacsim.robot_motion.motion_generation.examples``; the extension id is unchanged.

   **Replacement:** Use the ``isaacsim.robot_motion.cumotion.examples`` extension and the :doc:`cuMotion Integration <../../cumotion/index>` tutorials.

Generating a Path Using an RRT Instance
========================================

Required Configuration Files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:ref:`isaac_sim_motion_generation_rrt` requires three configuration files to identify a specific robot in
:ref:`isaac_sim_motion_generation_rrt_configuration`.  Paths to these configuration files are used to initialize the ``RRT``
class along with an end effector name matching a frame in the robot URDF.

One of the required files contains parameters for the RRT algorithm specifically, and is not shared with any other Lula algorithms.
This tutorial loads the following RRT config file for the Franka robot:

.. code-block:: yaml
    :linenos:

    seed: 123456
    step_size: 0.05
    max_iterations: 50000
    max_sampling: 10000
    distance_metric_weights: [3.0, 2.0, 2.0, 1.5, 1.5, 1.0, 1.0]
    task_space_frame_name: "panda_rightfingertip"
    task_space_limits: [[0.0, 0.7], [-0.6, 0.6], [0.0, 0.8]]
    cuda_tree_params:
        max_num_nodes: 10000
        max_buffer_size: 30
        num_nodes_cpu_gpu_crossover: 3000
    c_space_planning_params:
        exploration_fraction: 0.5
    task_space_planning_params:
        translation_target_zone_tolerance: 0.05
        orientation_target_zone_tolerance: 0.09
        translation_target_final_tolerance: 1e-4
        orientation_target_final_tolerance: 0.005
        translation_gradient_weight: 1.0
        orientation_gradient_weight: 0.125
        nn_translation_distance_weight: 1.0
        nn_orientation_distance_weight: 0.125
        task_space_exploitation_fraction: 0.4
        task_space_exploration_fraction: 0.1
        max_extension_substeps_away_from_target: 6
        max_extension_substeps_near_target: 50
        extension_substep_target_region_scale_factor: 2.0
        unexploited_nodes_culling_scalar: 1.0
        gradient_substep_size: 0.025

You can reference the ``docstring`` to the function ``RRT.set_param()`` in our |link_ext| for a description of each parameter.

.. |link_ext| raw:: html

   <a href="../py/source/deprecated/isaacsim.robot_motion.motion_generation/docs/index.html" target="_blank">API Documentation</a>

RRT Example
^^^^^^^^^^^^

The file ``/RRT_Example_python/scenario.py`` loads the Franka robot and uses ``RRT`` to move it around obstacles to a target.
Every 60 frames, the planner replans to move to the current target position (if possible).  In this example, the planner does
not attempt to plan to the same target multiple times if a failure is encountered.  The returned plan will be ``None`` and no actions will be taken.

Initialize RRT:

.. literalinclude:: ../snippets/manipulators/manipulators_lula_rrt/rrt_example.py
    :language: python
    :linenos:
    :start-after: # -- Begin initializing RRT -- #
    :end-before: # -- End of initializing RRT -- #

For supported robots, this can be simplified:

.. literalinclude:: ../snippets/manipulators/manipulators_lula_rrt/rrt_example.py
    :language: python
    :linenos:
    :start-after: # -- Begin simplified initialization of RRT -- #
    :end-before: # -- End of simplified initialization of RRT -- #

To make ``RRT`` aware of the obstacle it needs to watch the obstacles:

.. literalinclude:: ../snippets/manipulators/manipulators_lula_rrt/rrt_example.py
    :language: python
    :linenos:
    :start-after: # -- Begin adding obstacle -- #
    :end-before: # -- End of adding obstacle -- #

Any time ``RRT.update_world()`` is called, it will query the current position
of watched obstacles.

``RRT`` outputs sparse plans that, when linearly interpolated, form a collision-free path to the goal position.
As an instance of the ``PathPlanner`` interface, ``RRT`` can be passed to a :ref:`isaac_sim_path_planner_visualizer` to convert its output
to a form that is directly usable by the robot ``Articulation``:

.. literalinclude:: ../snippets/manipulators/manipulators_lula_rrt/rrt_example.py
    :language: python
    :linenos:
    :start-after: # -- Begin setting PathPlannerVisualizer -- #
    :end-before: # -- End of setting PathPlannerVisualizer -- #

Complete code:

.. literalinclude:: ../snippets/manipulators/manipulators_lula_rrt/rrt_example.py
    :language: python
    :linenos:

In this example, ``RRT`` replans every second if the target has been moved. The replanning is performed as follows:

.. literalinclude:: ../snippets/manipulators/manipulators_lula_rrt/rrt_example.py
    :language: python
    :linenos:
    :start-after: # -- Begin computing plan -- #
    :end-before: # -- End of computing plan -- #

* First, ``RRT`` is informed of the new target position.
* Then it is told to query the position of watched obstacles.
* Finally, the ``path_planner_visualizer`` wrapping ``RRT`` is used to generate a plan in the form of a list of ``ArticulationAction``.

The ``max_cspace_dist`` argument passed to the ``path_planner_visualizer`` interpolates the sparse output with a maximum l2 norm of ``.01``
between any two commanded robot positions.  On every frame, one of the actions in the plan is removed from the plan and sent to the
robot.

.. figure:: /images/isim_4.5_full_tut_gui_rrt.webp
   :align: center

Current Limitations
===================

Following a Plan with Exactness
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The ``PathPlannerVisualizer`` class is called a "Visualizer" because it is only meant to give a visualization of an output plan, but it is not likely to be useful
beyond this.  By densely linearly interpolating an ``RRT`` plan, the resulting trajectory is far from time-optimal or smooth.  To follow a plan in a
more theoretically sound way, the output of ``RRT`` can be combined with the ``LulaTrajectoryGenerator``.  This is demonstrated in the |isaac-sim| Path Planning Example
in the **Robotics Examples** tab. You can activate **Robotics Examples** tab from **Windows** > **Examples** > **Robotics Examples**.

Summary
=======

This tutorial reviews using the ``RRT`` class to generate a collision-free path through an environment from a starting position to a task-space target.

Further Learning
^^^^^^^^^^^^^^^^

To understand the motivation behind the structure and usage of ``RRT`` in |isaac-sim|, reference the :ref:`isaac_sim_motion_generation`
page.
