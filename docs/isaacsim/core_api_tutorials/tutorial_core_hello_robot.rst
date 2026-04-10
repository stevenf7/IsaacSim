..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_core_hello_robot:

==========================================
Hello Robot
==========================================

Learning Objectives
===================

This tutorial details how to add and move a mobile robot in |isaac-sim| in an extension application.
After this tutorial, you will understand how to add a robot to the simulation and apply actions to
its wheels using Python.

*10-15 Minute Tutorial*

Getting Started
================

**Prerequisites**

- Review :ref:`isaac_sim_app_tutorial_core_hello_world` prior to beginning this tutorial.

Begin with the source code of the **Hello World** example developed in the previous tutorial:
:ref:`isaac_sim_app_tutorial_core_hello_world`.

Adding a Robot
===================

Begin by adding a NVIDIA Jetbot to the scene, which allows you to access the library of |isaac-sim|
robots, sensors, and environments located on a :ref:`isaac_sim_glossary_nucleus` Server using Python,
as well as navigate through it using the **Content** window.

.. Note:: The server shown in these steps has been connected to in :ref:`isaac_sim_install_workstation`. Follow these steps first before proceeding.

.. image:: /images/core_api_tutorials_2_1.webp
    :align: center
    :width: 600


#. Add the assets by simply dragging them to the stage window or the viewport.
#. Try to do the same thing through Python in the **Hello World** example.
#. Create a new stage: **File > new > Don't Save**
#. Open the ``hello_world.py`` file by clicking the **Open Source Code**
   button in the **Hello World** window.

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_hello_robot/open_the_extension_examplesuser_exampleshello_worl.py
    :language: python
    :linenos:
    :emphasize-lines: 1-5, 14-27, 31

Click the **LOAD** button to load the scene and see the Jetbot appear. Although it is being simulated,
it is not moving. The next section walks through how to make the robot move.


Move the Robot
=================

In |isaac-sim|, Robots are constructed of physically accurate articulated joints. Applying actions
to these articulations make them move.

Next, apply random velocities to the Jetbot's wheel joints to get it moving.

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_hello_robot/move_the_robot.py
    :language: python
    :linenos:
    :emphasize-lines: 4, 37-40, 42-46


Click the **LOAD** button to load the scene and watch the Jetbot move with random velocities.

.. Note:: Pressing **STOP**, then **PLAY** in this workflow might not reset the world properly. Use
          the **RESET** button instead.


Extra Practice
^^^^^^^^^^^^^^

This example applies random velocities to the Jetbot articulation controller. Try the following
exercises:

#. Make the Jetbot move backwards (hint: use negative velocities).
#. Make the Jetbot turn right (hint: apply different velocities to each wheel).
#. Make the Jetbot stop after 5 seconds (hint: track elapsed time in the callback).


Controlling Specific Joints
===========================

You can also control specific joints by their names or indices. Here's how to get the wheel
joint indices and apply velocities only to specific joints:

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_hello_robot/using_the_wheeledrobot_class.py
    :language: python
    :linenos:
    :emphasize-lines: 32-38, 48-52

.. image:: /images/core_api_tutorials_2_2.webp
    :align: center
    :width: 600

Summary
========

This tutorial covered the following topics:

#. Adding |isaac-sim| library components from a Nucleus Server
#. Adding a robot to the stage using :code:`stage_utils.add_reference_to_stage()`
#. Wrapping a robot with the :code:`Articulation` class for control
#. Using :code:`set_dof_velocity_targets()` to apply velocity control
#. Registering physics callbacks with :code:`SimulationManager`
#. Controlling specific joints by name or index


Next Steps
^^^^^^^^^^^^^^^^^^^^^^

Continue on to the next tutorial in the Essential Tutorials series, :ref:`isaac_sim_app_tutorial_core_adding_manipulator`,
to learn how to add a manipulator robot to the simulation.


Further Learning
^^^^^^^^^^^^^^^^^^^^^^

**Nucleus Server**

- For an overview of how to best leverage a Nucleus Server, see the `Nucleus Overview in NVIDIA Omniverse <https://youtu.be/JaoIQ4YBnBE>`_
  tutorial.

**Robot Specific Extensions**

- |isaac-sim| provides several robot extensions, including ``isaacsim.robot.experimental.wheeled_robots``,
  and ``isaacsim.robot.experimental.manipulators.examples``.
  To learn more, check out the standalone examples located at ``standalone_examples/api/isaacsim.robot.experimental.manipulators/franka``
  and ``standalone_examples/api/isaacsim.robot.experimental.manipulators/universal_robots/``.

