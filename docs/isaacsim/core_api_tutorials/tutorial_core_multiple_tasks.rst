..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_core_multiple_tasks:

==========================================
Multiple Robot Scenarios
==========================================

Learning Objectives
===================

This tutorial describes how to create and manage multiple robot scenarios in |isaac-sim|.
It explains how to use parameterization and Python classes to scale your simulations with
multiple instances of robots performing similar tasks. After this tutorial, you will have
more experience building scalable multi-robot simulations in |isaac-sim|.

*15-20 Minute Tutorial*

Getting Started
================

**Prerequisites**

- Review :ref:`isaac_sim_app_tutorial_core_adding_multiple_robots` prior to beginning this tutorial.

Begin with the source code open from the previous tutorial, :ref:`isaac_sim_app_tutorial_core_adding_multiple_robots`.

.. Note:: Pressing **STOP**, then **PLAY** in this workflow might not reset the world properly. Use
          the **RESET** button instead.

Organizing Robot Scenarios with Classes
=======================================

When working with multiple robots performing similar tasks, it's helpful to encapsulate the
robot setup and control logic into reusable classes. This approach allows you to easily
create multiple instances with different parameters (like position offsets).

Create a :code:`RobotScenario` class that manages a Jetbot pushing a cube to a Franka:

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_multiple_tasks/parameterizing_tasks.py
    :language: python
    :linenos:

.. image:: /images/core_api_tutorials_6_1.webp
    :align: center
    :width: 600


Scaling to Multiple Scenarios
=============================

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_multiple_tasks/scaling_to_many_tasks.py
    :language: python
    :linenos:
    :emphasize-lines: 20, 30-34, 38-39, 48-49, 53-54, 60

.. image:: /images/core_api_tutorials_6_2.webp
    :align: center
    :width: 600


Adding Randomization
====================

To make simulations more interesting, you can add randomization to the scenario parameters.
Modify the :code:`RobotScenario` class to accept randomization options:

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_multiple_tasks/adding_randomization.py
    :language: python
    :linenos:

Then create scenarios with randomization enabled:

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_multiple_tasks/adding_randomization_2.py
    :language: python
    :linenos:

Best Practices for Scaling
==========================

When creating large-scale multi-robot simulations:

#. **Use unique paths**: Each scenario should use unique USD prim paths to avoid conflicts.
   The :code:`RobotScenario` class uses the scenario name to create unique paths like
   :code:`/World/scenario_0/Jetbot`.

#. **Manage state independently**: Each scenario instance maintains its own state variables,
   allowing scenarios to progress independently.

#. **Clean up properly**: The :code:`physics_cleanup` method ensures callbacks are deregistered
   and scenario lists are cleared when the simulation is stopped.

#. **Consider performance**: With many scenarios, consider reducing physics step frequency
   or using GPU-accelerated simulation for better performance.


Summary
========

This tutorial covered the following topics:

#. Organizing robot scenarios into reusable Python classes
#. Using the :code:`offset` parameter to position multiple scenarios in the world
#. Scaling to multiple parallel scenarios with a simple loop
#. Adding randomization to scenario parameters
#. Best practices for managing multiple robot instances

