.. _isaac_sim_cumotion_tutorial_robot_configuration:

==================================
Robot Configuration Tutorial
==================================

This tutorial covers configuring robots for use with the |cumotion| integration — from generating the required XRDF file to loading it into your application.

By the end of this tutorial, you'll understand:

* How to load pre-configured or custom robot configurations using :func:`load_cumotion_supported_robot` and :func:`load_cumotion_robot`
* How to use robot configurations with |cumotion| components

**Prerequisites**

- Basic understanding of URDF and XRDF file formats

Overview
========

An `XRDF <https://nvidia-isaac-ros.github.io/concepts/manipulation/xrdf.html>`_ file is the main configuration file required by |cumotion| for a specific robot.
It supplements the robot's URDF with |cumotion|-specific data: collision-sphere geometries, self-collision settings, joint properties, tool frames, and modifiers.

**Active and Fixed Joints**

A key aspect of the XRDF is defining the robot's configuration space. Joints are classified as either *active* or *fixed*. Active joints are directly controlled by |cumotion|; fixed joints are held at a specified default position. For example, on a seven-DOF arm with an attached gripper, the arm joints are active and the gripper joints are fixed. The fixed-joint positions define the robot's default configuration, which is used for null-space behavior in reactive control.

**Collision Spheres**

|cumotion| uses a set of spheres attached to each robot link for collision avoidance. These spheres must roughly cover the robot's surface. The *cuMotion/Lula Robot Description Editor* provides tools to generate and tune this sphere set for any robot.
For a full tutorial on XRDF and URDF file generation, see :ref:`isaac_sim_app_tutorial_generate_robot_config_lula`.

Robot Configuration Files
=========================

|cumotion| expects the following files for each robot, organized in a single directory:

.. code-block:: text

    robot_config/
    ├── robot.urdf
    ├── robot.xrdf
    ├── rmp_flow.yaml                          (optional)
    ├── graph_based_motion_planner_config.yaml (optional)
    └── meshes/
        ├── link_0.stl
        ├── link_1.stl
        └── ...

* ``robot.urdf`` — The URDF file describing the robot's kinematic structure, joint limits, and link geometries.
* ``robot.xrdf`` — The XRDF file containing |cumotion|-specific configuration: collision-sphere geometries, active/fixed joint assignments, default joint positions, tool frames, and self-collision rules.
* ``meshes/`` — Directory containing the mesh files referenced by the URDF.
* ``rmp_flow.yaml`` (optional) — RMPflow configuration for reactive control.
* ``graph_based_motion_planner_config.yaml`` (optional) — Graph-based motion planner configuration.

Both the URDF and XRDF files can be generated directly from a robot USD asset using extensions provided with Isaac Sim:

* The :ref:`Isaac Sim USD to URDF Exporter <isaac_sim_app_extension_urdf_exporter>` exports a URDF file from a USD asset.
* The :ref:`Robot Description Editor <isaac_sim_app_tutorial_motion_generation_robot_description_editor>` (extension: ``isaacsim.robot_setup.xrdf_editor``) generates the XRDF file, including collision spheres, joint properties, tool frames, and self-collision rules.

.. note::
   For a complete step-by-step walkthrough generating XRDF and URDF files for a UR10e with a Robotiq 2F-140 gripper, see :ref:`isaac_sim_app_tutorial_generate_robot_config_lula`.


Loading Robot Configurations
=============================

Once you have URDF and XRDF files, load them into a :class:`CumotionRobot` object, which encapsulates all data needed to work with |cumotion|:

* ``robot_description``: The |cumotion| robot description loaded from URDF/XRDF files, including default joint positions and tool frame names
* ``kinematics``: The |cumotion| kinematics solver for forward kinematics and Jacobian computation
* ``controlled_joint_names``: List of joint names controlled by |cumotion|
* ``directory``: Path to the robot configuration directory (useful for loading related config files)

The provided functions for loading a :class:`CumotionRobot` object are:

* :func:`load_cumotion_supported_robot` - Load a pre-configured robot from the extension's robot_configurations directory.
* :func:`load_cumotion_robot` - Load a custom robot from a given directory.

Loading Supported Robots
------------------------

The easiest way to get started is to use a pre-configured robot that comes with the extension. Currently supported robots include:

* **franka** - Franka Emika Panda robot
* **ur10** - Universal Robots UR10 robot

.. literalinclude:: ../snippets/cumotion/robot_configuration_example.py
   :start-after: <start-load-supported-robot-snippet>
   :end-before: <end-load-supported-robot-snippet>
   :language: python

The function automatically locates the robot configuration directory within the extension and loads the URDF and XRDF files. If the robot name is not supported, a :class:`FileNotFoundError` will be raised.

Creating Custom Robot Configurations
--------------------------------------

If you have your own robot with URDF and XRDF files, load it using :func:`load_cumotion_robot`:

.. literalinclude:: ../snippets/cumotion/robot_configuration_example.py
   :start-after: <start-load-custom-robot-default-snippet>
   :end-before: <end-load-custom-robot-default-snippet>
   :language: python

If your URDF or XRDF files have different names, specify them explicitly:

.. literalinclude:: ../snippets/cumotion/robot_configuration_example.py
   :start-after: <start-load-custom-robot-custom-snippet>
   :end-before: <end-load-custom-robot-custom-snippet>
   :language: python

The function will raise a :class:`FileNotFoundError` if the specified files cannot be found.

Accessing Robot Description and Kinematics
-------------------------------------------

The robot configuration provides direct access to the underlying |cumotion| objects:

.. literalinclude:: ../snippets/cumotion/robot_configuration_example.py
   :start-after: <start-access-robot-description-snippet>
   :end-before: <end-access-robot-description-snippet>
   :language: python

The controlled joint names are automatically extracted from the robot description and represent all joints in the configuration space:

.. literalinclude:: ../snippets/cumotion/robot_configuration_example.py
   :start-after: <start-access-controlled-joints-snippet>
   :end-before: <end-access-controlled-joints-snippet>
   :language: python

Loading Configuration Files for Reactive Control and Path Planning
------------------------------------------------------------------

The ``directory`` attribute of the :class:`CumotionRobot` object is useful for loading related configuration files.

For RMPflow controllers:

.. literalinclude:: ../snippets/cumotion/robot_configuration_example.py
   :start-after: <start-load-rmpflow-relative-snippet>
   :end-before: <end-load-rmpflow-relative-snippet>
   :language: python

Or specify an absolute path:

.. literalinclude:: ../snippets/cumotion/robot_configuration_example.py
   :start-after: <start-load-rmpflow-absolute-snippet>
   :end-before: <end-load-rmpflow-absolute-snippet>
   :language: python

For graph-based motion planners:

.. literalinclude:: ../snippets/cumotion/robot_configuration_example.py
   :start-after: <start-load-graph-planner-relative-snippet>
   :end-before: <end-load-graph-planner-relative-snippet>
   :language: python

Or specify an absolute path:

.. literalinclude:: ../snippets/cumotion/robot_configuration_example.py
   :start-after: <start-load-graph-planner-absolute-snippet>
   :end-before: <end-load-graph-planner-absolute-snippet>
   :language: python

The configuration files are subsequently used by all of the integrated |cumotion| planners and controllers:

* :class:`RmpFlowController`
* :class:`GraphBasedMotionPlanner`
* :class:`TrajectoryGenerator`
* :class:`TrajectoryOptimizer`

See the relevant tutorials under *Next Steps* at the end of this tutorial for more information on each of the |cumotion| components.

Summary
=======

This tutorial covered:

1. **XRDF Overview**: The structure of XRDF files and the concepts of active/fixed joints and collision spheres
2. **Robot Configuration Files**: The URDF, XRDF, and optional configuration files required by |cumotion|, and the Isaac Sim tools used to generate them from a USD asset
3. **Loading Supported Robots**: Using :func:`load_cumotion_supported_robot` for pre-configured robots
4. **Custom Robots**: Using :func:`load_cumotion_robot` for your own URDF/XRDF files
5. **Accessing Robot Data**: Using the robot description and kinematics objects directly

Robot configurations are foundational for all |cumotion| motion planning and control. Once you have a configuration, you can use it with any |cumotion| component to generate motions for your robot.

Next Steps
----------

* :ref:`World Interface tutorial <isaac_sim_cumotion_tutorial_world_interface>` - Setting up world state for motion planning
* :ref:`RMPflow tutorial <isaac_sim_cumotion_tutorial_rmpflow>` - Using robot configurations with reactive control
* :ref:`Graph Planner tutorial <isaac_sim_cumotion_tutorial_graph_planner>` - Using robot configurations with path planning
* :ref:`Trajectory Generator tutorial <isaac_sim_cumotion_tutorial_trajectory_generator>` - Using robot configurations for trajectory generation
* :ref:`Trajectory Optimizer tutorial <isaac_sim_cumotion_tutorial_trajectory_optimizer>` - Using robot configurations for trajectory optimization
* |cumotion| library documentation - Understanding URDF/XRDF requirements and kinematics API
