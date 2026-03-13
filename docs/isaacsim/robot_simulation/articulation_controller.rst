..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_articulation_controller:

==================================
Articulation Controller
==================================

Overview
=================


Articulation controller is the low level controller that controls joint position, joint velocity, and joint effort in |isaac-sim_short|. The articulation controller can be interfaced using Python and Omnigraph.

.. Note:: Angular units are expressed in radians while angles in USD are expressed in degrees and will be adjusted accordingly by the articulation controller.


Python Interface
=================

Create the articulation controller
------------------------------------

There are several ways to create the articulation controller. The articulation controller is usually created implicitly by applying articulation on a robot prim through the ``SingleArticulation`` class. 
However, the articulation controller can be created directly by importing the controller class before the simulation starts, but this approach will require you to create or pass in the ``Articulation`` during initialization.

.. tab-set::

    .. tab-item:: Single Articulation
        :sync: articulation

         The snippet below will load and apply articulation on a franka robot.

         .. literalinclude:: ../snippets/robot_simulation/articulation_controller/create_the_articulation_controller.py
             :language: python

    .. tab-item:: Articulation Controller
        :sync: articulation_controller

         .. literalinclude:: ../snippets/robot_simulation/articulation_controller/wrap_the_prim_as_an_articulation.py
             :language: python

Initialize the controller
-------------------------------

After the simulation is started, the robot articulation must be initialized before any commands can be passed to the robot.

.. tab-set::

    .. tab-item:: Single Articulation
         :sync: articulation

            The more common approach is by initializing the single articulation object that you have created earlier, this will initialize the articulation controller and articulation view stored in the SingleArticulation object

            .. literalinclude:: ../snippets/robot_simulation/articulation_controller/initialize_the_controller.py
                :language: python

    .. tab-item:: Articulation Controller
        :sync: articulation_controller

         After the simulation starts, the articulation controller must be initialzied with an articulation view. Articulation view is the backend for selecting the joints and applying joint actions. 

         For example, the code snippet below creates an articulation view with the Franka robot and initializes the articulation controller.

         .. literalinclude:: ../snippets/robot_simulation/articulation_controller/initialize_the_controller_1.py
             :language: python

Articulation Action
----------------------

Joint controls commands are packaged in ``ArticulationAction`` objects first, before sending them to the articulation controller. The articulation controller allows you to specify the command joint postion, velocity and effort, as well as joint indicies of the joints actuated.

If the joint indice is empty, the articulation action will assume the command will apply to all joints of the robot, and if any of the command is 0, articulation action will assume it is unactuated. 

For example, the snippet below creates the command that closes the franka robot fingers: panda_finger_joint1 (7) and panda_finger_joint2 (8) to 0.0

.. literalinclude:: ../snippets/robot_simulation/articulation_controller/articulation_action.py
    :language: python

This snippet creates the command that moves all the robot joints to the indicated position

.. literalinclude:: ../snippets/robot_simulation/articulation_controller/articulation_action_1.py
    :language: python

.. important:: Make sure the joint commands matches the order and the number of joint indices passed in to the articulation action. If joint indice is not passed in, make sure the command matches the number of joints in the robot.

.. note:: A joint can only be controlled by one control method. For example a joint cannot be controlled by both desired position and desired torque

Apply Action
---------------

The ``apply_action`` function in both ``SingleArticulation`` and ``ArticulationController`` classes will apply the ``ArticulationAction`` you created earlier to the robot.

.. tab-set::

    .. tab-item:: Single Articulation
         :sync: articulation

            .. literalinclude:: ../snippets/robot_simulation/articulation_controller/apply_action.py
                :language: python

    .. tab-item:: Articulation Controller
         :sync: articulation_controller

            .. literalinclude:: ../snippets/robot_simulation/articulation_controller/apply_action_1.py
                :language: python

Script Editor Example
---------------------
You can try out basic articulation controller examples by running the following code snippets in the Script Editor. For more advanced usage, it is recommended to follow the :ref:`isaac_sim_core_api_tutorials_page`.

.. tab-set::

    .. tab-item:: Single Articulation
         :sync: articulation

            .. literalinclude:: ../snippets/robot_simulation/articulation_controller/script_editor_example.py
                :language: python

    .. tab-item:: Articulation Controller
         :sync: articulation_controller

            .. literalinclude:: ../snippets/robot_simulation/articulation_controller/run_the_example.py
                :language: python

Omnigraph Interface
====================

The articulation controller can also be accessed through Omnigraph nodes, providing a visual, node-based approach to robot control.

Input Parameters
-----------------

The articulation controller Omnigraph node accepts the following input parameters:

.. list-table:: Articulation Controller Omnigraph Inputs
   :widths: 25 75
   :header-rows: 1

   * - Input Parameter
     - Description
   * - **execIn**
     - Input execution trigger - connects to other nodes to control when the articulation controller runs
   * - **targetPrim**
     - The prim containing the robot articulation root. Leave empty if using robotPath
   * - **robotPath**
     - String path to the robot articulation root. Leave empty if using targetPrim
   * - **jointIndices**
     - Array of joint indices to control. Leave empty to control all joints or use jointNames
   * - **jointNames**
     - Array of joint names to control. Leave empty to control all joints or use jointIndices
   * - **positionCommand**
     - Desired joint positions. Leave empty if not using position control
   * - **velocityCommand**
     - Desired joint velocities. Leave empty if not using velocity control
   * - **effortCommand**
     - Desired joint efforts/torques. Leave empty if not using effort control

Usage Guidelines
-----------------

.. important:: **Parameter Validation**: Ensure joint commands match the order and number of joint indices or joint names. If neither joint indices nor joint names are specified, the command must match the total number of joints in the robot.

.. note:: **Control Method Limitation**: A joint can only be controlled by one method at a time. For example, a joint cannot be controlled by both position and effort commands simultaneously.

Example Usage
--------------

For a complete example of the articulation controller Omnigraph node in action, see the ``mock_robot_rigged`` asset in the Content Browser at **Isaac Sim > Samples > Rigging > MockRobot > mock_robot_rigged.usd**.

.. figure:: /images/isim_4.5_base_ref_gui_rigging_mockrobot_controller.png
    :align: center
    :width: 100%
    :alt: Articulation Controller Omnigraph Node Example

