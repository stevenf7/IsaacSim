.. _isaac_sim_cumotion_tutorial_robot_configuration:

==================================
Robot Configuration Tutorial
==================================

This tutorial demonstrates how to configure robots for use with the |cumotion| integration. You'll learn how to load robot configurations from supported robots or create custom robot configurations from URDF and XRDF files.

By the end of this tutorial, you'll understand:

* How to load pre-configured robots using :func:`load_cumotion_supported_robot`
* How to load custom robot configurations using :func:`load_cumotion_robot`
* The structure of robot configuration directories
* How to use robot configurations with |cumotion| components

**Prerequisites**

- Basic understanding of URDF and XRDF file formats

Key Concepts
============

A :class:`CumotionRobot` encapsulates all the necessary data for a robot to work with |cumotion|:

* ``robot_description``: The |cumotion| robot description loaded from URDF/XRDF files, which includes some key properties such as the default joint positions and the tool frame names
* ``kinematics``: The |cumotion| kinematics solver for forward kinematics and Jacobian computation
* ``controlled_joint_names``: List of joint names that are controlled by |cumotion| software
* ``directory``: Path to the robot configuration directory (useful for loading related config files)

.. note::
   For generating new XRDF files, the :ref:`Robot Description Editor tutorial <isaac_sim_app_tutorial_motion_generation_robot_description_editor>` is still valid.

The configuration is used by all |cumotion| components including:

* :class:`RmpFlowController` - Reactive motion control
* :class:`GraphBasedMotionPlanner` - Path planning
* :class:`TrajectoryGenerator` - Trajectory generation
* :class:`TrajectoryOptimizer` - Trajectory optimization

Loading Supported Robots
========================

The easiest way to get started is to use a pre-configured robot that comes with the extension. Currently supported robots include:

* **franka** - Franka Emika Panda robot
* **ur10** - Universal Robots UR10 robot

To load a supported robot configuration:

.. literalinclude:: ../snippets/cumotion/robot_configuration_example.py
   :start-after: <start-load-supported-robot-snippet>
   :end-before: <end-load-supported-robot-snippet>
   :language: python

The function automatically locates the robot configuration directory within the extension and loads the URDF and XRDF files. If the robot name is not supported, a :class:`FileNotFoundError` will be raised.

Creating Custom Robot Configurations
=====================================

If you have your own robot with URDF and XRDF files, you can load it using :func:`load_cumotion_robot`:

.. literalinclude:: ../snippets/cumotion/robot_configuration_example.py
   :start-after: <start-load-custom-robot-default-snippet>
   :end-before: <end-load-custom-robot-default-snippet>
   :language: python

If your URDF or XRDF files have different names, you can specify them explicitly:

.. literalinclude:: ../snippets/cumotion/robot_configuration_example.py
   :start-after: <start-load-custom-robot-custom-snippet>
   :end-before: <end-load-custom-robot-custom-snippet>
   :language: python

The function will raise a :class:`FileNotFoundError` if the specified files cannot be found.

Robot Configuration Directory Structure
=======================================

A robot configuration directory should contain:

* **robot.urdf** - The URDF file describing the robot's kinematic structure
* **robot.xrdf** - The XRDF file containing additional |cumotion|-specific configuration
* **meshes/** - Directory containing mesh files referenced by the URDF
* **rmp_flow.yaml** (optional) - RMPflow configuration file for reactive control
* **graph_based_motion_planner_config.yaml** (optional) - Graph planner configuration

Example directory structure:

.. code-block:: text

    robot_configurations/
    └── franka/
        ├── robot.urdf
        ├── robot.xrdf
        ├── rmp_flow.yaml
        ├── graph_based_motion_planner_config.yaml
        └── meshes/
            ├── panda_link0.stl
            ├── panda_link1.stl
            └── ...

The URDF file describes the robot's kinematic structure, joint limits, and link geometries. The XRDF file provides |cumotion|-specific information such as collision-sphere geometries and self-collision settings.

Accessing Robot Description and Kinematics
==========================================

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

Loading Configuration Files
===========================

The ``directory`` attribute of the :class:`CumotionRobot` object is useful for loading related configuration files. 
For example, RMPflow controllers can load their configuration from the robot directory:

.. literalinclude:: ../snippets/cumotion/robot_configuration_example.py
   :start-after: <start-load-rmpflow-relative-snippet>
   :end-before: <end-load-rmpflow-relative-snippet>
   :language: python

Or specify an absolute path:

.. literalinclude:: ../snippets/cumotion/robot_configuration_example.py
   :start-after: <start-load-rmpflow-absolute-snippet>
   :end-before: <end-load-rmpflow-absolute-snippet>
   :language: python

Similarly, graph-based motion planners can load their configuration using the same pattern:

.. literalinclude:: ../snippets/cumotion/robot_configuration_example.py
   :start-after: <start-load-graph-planner-relative-snippet>
   :end-before: <end-load-graph-planner-relative-snippet>
   :language: python

Or specify an absolute path:

.. literalinclude:: ../snippets/cumotion/robot_configuration_example.py
   :start-after: <start-load-graph-planner-absolute-snippet>
   :end-before: <end-load-graph-planner-absolute-snippet>
   :language: python

Summary
=======

This tutorial demonstrated:

1. **Loading Supported Robots**: Using :func:`load_cumotion_supported_robot` to load pre-configured robots
2. **Custom Robots**: Using :func:`load_cumotion_robot` to load robots from your own URDF/XRDF files
3. **Directory Structure**: Understanding the required files and optional configuration files
4. **Using Configurations**: Integrating robot configurations with |cumotion| components
5. **Accessing Robot Data**: Using the robot description and kinematics objects directly

Robot configurations foundational for all |cumotion| motion planning and control. 
Once you have a configuration, you can use it with any |cumotion| component to generate motions for your robot.

Next Steps
----------

* :ref:`World Interface tutorial <isaac_sim_cumotion_tutorial_world_interface>` - Setting up world state for motion planning
* :ref:`RMPflow tutorial <isaac_sim_cumotion_tutorial_rmpflow>` - Using robot configurations with reactive control
* :ref:`Graph Planner tutorial <isaac_sim_cumotion_tutorial_graph_planner>` - Using robot configurations with path planning
* :ref:`Trajectory Generator tutorial <isaac_sim_cumotion_tutorial_trajectory_generator>` - Using robot configurations for trajectory generation
* :ref:`Trajectory Optimizer tutorial <isaac_sim_cumotion_tutorial_trajectory_optimizer>` - Using robot configurations for trajectory optimization
* |cumotion| library documentation - Understanding URDF/XRDF requirements and kinematics API
