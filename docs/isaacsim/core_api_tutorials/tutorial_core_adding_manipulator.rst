
..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_tutorial_core_adding_manipulator:

==========================================
Adding a Manipulator Robot
==========================================


Learning Objectives
===================

This tutorial introduces a manipulator robot to the simulation, a Franka Panda.
It describes how to add the robot to the scene and execute a pick-and-place operation.
After this tutorial, you will have more experience using manipulator robots and
controlling them with inverse kinematics in |isaac-sim|.

*15-20 Minute Tutorial*

Getting Started
================

**Prerequisites**

- Review :ref:`isaac_sim_app_tutorial_core_hello_robot` prior to beginning this tutorial.

Begin with the source code open from the :ref:`isaac_sim_app_tutorial_core_hello_robot` tutorial,
by clicking the **Open Source Code** button in the Hello World Example window.

.. Note:: Pressing **STOP**, then **PLAY** in this workflow might not reset the world properly. Use
          the **RESET** button instead.

Creating the Scene with a Franka Robot
======================================

Add a Franka robot and a cube for the robot to pick up using the :code:`FrankaExperimental` class.
This class inherits from :code:`Articulation` and provides high-level control methods including
inverse kinematics and gripper control.

When you set :code:`create_robot=True` in the constructor, :code:`FrankaExperimental` automatically
spawns the Franka robot USD asset at the specified path.

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_adding_manipulator/creating_the_scene.py
    :linenos:
    :emphasize-lines: 5, 17-23

Click the **LOAD** button to see the Franka robot and cube in the scene.

The :code:`FrankaExperimental` class provides these key methods for robot control:

- :code:`set_end_effector_pose(position, orientation)` - Move end-effector using inverse kinematics
- :code:`open_gripper()` / :code:`close_gripper()` - Control the gripper
- :code:`get_current_state()` - Get DOF positions and end-effector pose
- :code:`get_downward_orientation()` - Get quaternion for downward-facing orientation
- :code:`reset_to_default_pose()` - Reset robot to home position


Using FrankaPickPlace for Complete Pick-and-Place
=================================================

For a complete pick-and-place operation, use the :code:`FrankaPickPlace` class. This class has a
:code:`setup_scene()` method that spawns everything needed for pick-and-place: the Franka robot,
ground plane, and a cube to manipulate.

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_adding_manipulator/using_the_pickandplace_controller.py
    :language: python
    :linenos:
    :emphasize-lines: 4, 18-19, 34

Click the **LOAD** button to start the pick-and-place operation. The robot will automatically
execute all phases of picking up and placing the cube.


Customizing the FrankaPickPlace Scene
=====================================

The :code:`setup_scene()` method accepts parameters to customize the cube position, size,
and target position:

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_adding_manipulator/customizing_the_scene.py
    :language: python
    :linenos:


Understanding the Pick-and-Place State Machine
==============================================

The :code:`FrankaPickPlace` class uses a state machine with the following phases:

.. list-table:: Pick-and-Place Phases
   :header-rows: 1

   * - Phase
     - Description
     - Default Steps
   * - 0
     - Move to x,y position above cube
     - 60
   * - 1
     - Approach down to cube
     - 40
   * - 2
     - Close gripper to grasp
     - 20
   * - 3
     - Lift cube upward
     - 40
   * - 4
     - Move cube to target location
     - 80
   * - 5
     - Open gripper to release
     - 20
   * - 6
     - Move up and away
     - 20

You can customize the phase durations by passing :code:`events_dt` to the constructor:

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_adding_manipulator/understanding_the_state_machine.py
    :language: python

.. image:: /images/core_api_tutorials_4_1.webp
    :align: center
    :width: 600


Summary
========
This tutorial covered the following topics:

#. Adding a Franka manipulator robot using :code:`FrankaExperimental` with :code:`create_robot=True`
#. Using the :code:`FrankaPickPlace.setup_scene()` method to spawn a complete pick-and-place scene
#. Executing pick-and-place operations with the :code:`forward()` method
#. Understanding and customizing the pick-and-place state machine phases

Next Steps
^^^^^^^^^^^^^^^^^^^^^^

Continue to the next tutorial in our Essential Tutorials series, :ref:`isaac_sim_app_tutorial_core_adding_multiple_robots`,
to learn how to add multiple robots to the simulation.

