..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_tutorial_core_adding_multiple_robots:

==========================================
Adding Multiple Robots
==========================================

Learning Objectives
===================

This tutorial integrates two different types of robots into the same simulation:
a mobile robot (Jetbot) and a manipulator (Franka), working together to accomplish a task.
The Jetbot pushes a cube towards the Franka, which then picks it up.
After this tutorial, you will have experience building multi-robot simulations with object interaction.

*15-20 Minute Tutorial*

Getting Started
================

**Prerequisites**

- Review :ref:`isaac_sim_app_tutorial_core_adding_manipulator` prior to beginning this tutorial.

Begin with the source code open from the previous tutorial, :ref:`isaac_sim_app_tutorial_core_adding_manipulator`.

.. Note:: Pressing **STOP**, then **PLAY** in this workflow might not reset the world properly. Use
          the **RESET** button instead.

Creating the Scene
=============================

Begin by adding the Jetbot, Franka Panda, and the Cube from the previous tutorials to the scene.

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_adding_multiple_robots/creating_the_scene.py
    :language: python
    :linenos:

Click the **LOAD** button to see both robots and the cube in the scene.


Controlling Multiple Robots
===========================

Now add physics callbacks to control both robots simultaneously. The Jetbot will push the cube
forward while the Franka prepares to receive it.

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_adding_multiple_robots/controlling_multiple_robots.py
    :language: python
    :linenos:
    :start-after: # -- Begin control Jetbot -- #
    :end-before: # -- End of control Jetbot -- #

Complete code:

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_adding_multiple_robots/controlling_multiple_robots.py
    :language: python
    :linenos:

Watch as the Jetbot pushes the cube towards the Franka!

.. image:: /images/core_api_tutorials_5_1.webp
    :align: center
    :width: 600


Adding State Machine Logic
==========================

Create a state machine to coordinate the robots: first the Jetbot pushes the cube towards Franka,
then backs up to give space, and finally Franka executes a full pick-and-place sequence using
the :code:`Franka` class for IK-based end-effector control:

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_adding_multiple_robots/adding_state_machine_logic.py
    :language: python
    :linenos:
    :start-after: # -- Begin state machine -- #
    :end-before: # -- End of state machine -- #

Complete code:

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_adding_multiple_robots/adding_state_machine_logic.py
    :language: python
    :linenos:

.. image:: /images/core_api_tutorials_5_2.webp
    :align: center
    :width: 600


Summary
========
This tutorial covered the following topics:

#. Adding multiple robots and objects (cube) to the scene
#. Using :code:`Cube`, :code:`GeomPrim`, and :code:`RigidPrim` to create pushable objects
#. Using the :code:`Articulation` class to control different robot types
#. Having a mobile robot (Jetbot) push objects towards a manipulator (Franka)
#. Building state machine logic to coordinate pushing, backing up, and picking
#. Using :code:`Franka` for IK-based end-effector control and gripper operations


Next Steps
^^^^^^^^^^^^^^^^^^^^^^

Continue on to the next tutorial in our Essential Tutorials series, :ref:`isaac_sim_app_tutorial_core_multiple_tasks`,
to learn how to add multiple tasks and manage them.
