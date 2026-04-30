.. _isaac_sim_cumotion_tutorial_robot_configuration:

==================================
Robot Configuration Tutorial
==================================

This tutorial covers configuring robots for use with the |cumotion| integration — from generating the required XRDF file to loading it into your application.

By the end of this tutorial, you'll understand:

* What XRDF files contain and how to generate them using the Robot Description Editor
* How to edit and merge existing XRDF files
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

|cumotion| uses a set of spheres attached to each robot link for collision avoidance. These spheres must roughly cover the robot's surface. The Robot Description Editor provides tools to generate and tune this sphere set for any robot.

A :class:`CumotionRobot` encapsulates all data needed to work with |cumotion|:

* ``robot_description``: The |cumotion| robot description loaded from URDF/XRDF files, including default joint positions and tool frame names
* ``kinematics``: The |cumotion| kinematics solver for forward kinematics and Jacobian computation
* ``controlled_joint_names``: List of joint names controlled by |cumotion|
* ``directory``: Path to the robot configuration directory (useful for loading related config files)

.. note::
   The Robot Description Editor also supports exporting to the Lula robot description format (``.yaml``), though Lula is deprecated as of Isaac Sim 6.0.

Generating an XRDF File
========================

The **Robot Description Editor** (extension: ``isaacsim.robot_setup.xrdf_editor``) is the primary tool for generating XRDF files. For a full step-by-step walkthrough using a UR10e and Robotiq 2F-140 gripper, see the :ref:`isaac_sim_app_tutorial_generate_robot_config_lula` tutorial.

Enable the Extension
--------------------

* Go to **Window > Extensions**.
* Search for ``isaacsim.robot_setup.xrdf_editor`` and enable it, checking **AUTOLOAD**.

Prepare the Robot Asset
-----------------------

The Robot Description Editor does not support instanceable meshes.

* Open your robot's USD file.
* Select all ``visuals`` and ``collisions`` prims on the stage.
* In the **Property** panel, uncheck the **Instanceable** checkbox for each.

.. figure:: /manipulators/images/isim_6.0_full_tut_gui_lula_description_editor_instanceable_disable.png
   :align: center
   :alt: Property panel showing the Instanceable checkbox that should be unchecked

   The **Instanceable** checkbox (highlighted in red) should be unchecked for all geometry prims.

Configure Joint Properties
--------------------------

* Press **Play** to start the simulation.
* Open the editor via **Tools > Robotics > Robot Description Editor**.
* In the **Selection Panel**, set **Select Articulation** to your robot's articulation prim path.
* In **Set Joint Properties**, assign each joint a **Joint Status** and **Joint Position**:

  * Mark arm joints as **Active Joint** — these are directly controlled by |cumotion|.
  * Mark end-effector/gripper joints as **Fixed Joint** — |cumotion| holds these at the specified position.
  * Choose fixed-joint positions that represent a reasonable open or rest configuration.

.. image:: /images/isim_6.0_full_tut_gui_robot_description_editor.png
   :width: 80%
   :align: center

Generate Collision Spheres
--------------------------

.. important::
   Do not stop the simulation or exit the Robot Description Editor during this step.

Repeat the following for each link in the articulation:

* Select the link from **Selection Panel > Select Link**.
* In **Link Sphere Editor > Generate Spheres**, select a mesh from the **Select Mesh** dropdown.
* Set **Radius Offset** and **Number of Spheres**, then click **GENERATE SPHERES**.
* Spheres turn cyan when finalized.

.. image:: /images/isim_6.0_full_tut_gui_link_sphere_editor.png
   :width: 80%
   :align: center

.. image:: /images/isim_6.0_full_tut_gui_link_sphere_editor_add_spheres.png
   :width: 80%
   :align: center

Tuning tips:

* Size spheres to cover the link without being oversized — large spheres cause solver conservatism.
* More spheres improves accuracy but reduces solver performance.
* For long cylindrical links, generate spheres on the ends and use **Connect Spheres** to fill the middle.
* Use **Scale Spheres in Link** to resize spheres uniformly across a link.
* The auto-generator requires water-tight triangle meshes; otherwise, add and connect spheres manually.

Export to XRDF
--------------

.. important::
   Do not stop the simulation or exit the Robot Description Editor before exporting.

* At the bottom of the editor, expand **Export To File > Export to cuMotion XRDF**.
* Click the file icon and specify a path ending in ``.xrdf`` or ``.yaml``.
* Select the XRDF version to export (version 2.0 is recommended).
* Click **Save**.

Editing an XRDF File
====================

An existing XRDF file can be imported back into the Robot Description Editor for inspection or modification.

Importing an XRDF File
----------------------

* Open **Import From File > Import XRDF File** in the editor.
* Both XRDF format version 1.0 and 2.0 are supported.
* Only collision-group spheres are imported; modifiers, tool frames, and self-collision groups are not used.
* Importing overwrites all current editor state.

Merging with an Existing XRDF File
-----------------------------------

Because XRDF files can contain more information than the editor represents (tool frames, modifiers, custom self-collision rules), the editor can merge its output into an existing file rather than overwriting it.

When exporting, if you select a path to an existing XRDF file, an option to **Merge With Existing XRDF** appears. When merging, the editor:

* Copies tool frames from the existing file.
* Copies modifiers from the existing file.
* Copies ``self_collision > ignore`` from the existing file if the collision geometry matches.
* Copies collision spheres from the existing file for any links not represented in the editor.

Loading Robot Configurations
=============================

Once you have URDF and XRDF files, load them into your application using the |cumotion| robot loading utilities.


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

Robot Configuration Directory Structure
-----------------------------------------

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

Loading Configuration Files
-----------------------------

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


Using the Configuration Files
-----------------------------

The configuration files are subsequently used by the :class:`CumotionRobot` class for all |cumotion| components:

* :class:`RmpFlowController` - Reactive motion control
* :class:`GraphBasedMotionPlanner` - Path planning
* :class:`TrajectoryGenerator` - Trajectory generation
* :class:`TrajectoryOptimizer` - Trajectory optimization

See the following tutorials in the Isaac Sim |cumotion| documentation for more information.

Summary
=======

This tutorial covered:

1. **XRDF Overview**: The structure of XRDF files and the concepts of active/fixed joints and collision spheres
2. **Generating XRDF Files**: Using the Robot Description Editor to configure joints, generate collision spheres, and export
3. **Editing XRDF Files**: Importing and merging XRDF files in the editor
4. **Loading Supported Robots**: Using :func:`load_cumotion_supported_robot` for pre-configured robots
5. **Custom Robots**: Using :func:`load_cumotion_robot` for your own URDF/XRDF files
6. **Directory Structure**: Required files and optional configuration files
7. **Accessing Robot Data**: Using the robot description and kinematics objects directly

Robot configurations are foundational for all |cumotion| motion planning and control. Once you have a configuration, you can use it with any |cumotion| component to generate motions for your robot.

Next Steps
----------

* :ref:`World Interface tutorial <isaac_sim_cumotion_tutorial_world_interface>` - Setting up world state for motion planning
* :ref:`RMPflow tutorial <isaac_sim_cumotion_tutorial_rmpflow>` - Using robot configurations with reactive control
* :ref:`Graph Planner tutorial <isaac_sim_cumotion_tutorial_graph_planner>` - Using robot configurations with path planning
* :ref:`Trajectory Generator tutorial <isaac_sim_cumotion_tutorial_trajectory_generator>` - Using robot configurations for trajectory generation
* :ref:`Trajectory Optimizer tutorial <isaac_sim_cumotion_tutorial_trajectory_optimizer>` - Using robot configurations for trajectory optimization
* |cumotion| library documentation - Understanding URDF/XRDF requirements and kinematics API
