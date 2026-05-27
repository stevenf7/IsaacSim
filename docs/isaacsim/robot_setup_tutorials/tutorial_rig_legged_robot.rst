..
   Copyright (c) 2025, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_rig_legged_robot:

=============================================================
Tutorial 13: Rigging a Legged Robot for a Locomotion Policy
=============================================================

This tutorial explains how to rig a legged robot to match the configuration specified by a locomotion policy.
The Isaac Sim :ref:`isaac_sim_policy_controller_class` already handles robot rigging at runtime for inference in Isaac Sim,
so this tutorial is only relevant when you want to run the robot policy from an external process, such as ROS.

Learning Objectives
===================

In this tutorial, you will walk through the process of rigging an H1 humanoid robot to match the configuration specified by the H1 flat terrain locomotion policy.

1. Setting the initial robot position
2. Setting the joint configuration
3. Verifying the joint configuration

.. note:: The H1 flat terrain policy environment definition file is available `here <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/H1_Policies/h1_env.yaml>`_.


.. _isaac_sim_tutorial_rig_legged_robot_initial_position:

Setting the Initial Robot Position
==================================

The initial joint position of the robot is specified under the ``robot:init_state:joint_pos`` section of the environment definition file. The joint names are specified using the ``.*`` wildcard.

.. code-block:: yaml
    :linenos:

    robot:
      init_state:
        joint_pos:
          .*_hip_yaw: 0.0
          .*_hip_roll: 0.0
          .*_hip_pitch: -0.28
          .*_knee: 0.79
          .*_ankle: -0.52
          torso: 0.0
          .*_shoulder_pitch: 0.28
          .*_shoulder_roll: 0.0
          .*_shoulder_yaw: 0.0
          .*_elbow: 0.52
        joint_vel:
          .*: 0.0

.. note:: The joint positions are specified in radians, whereas USD joint positions are specified in degrees.

To store the initial state of the robot:

1. Open the ``h1.usd`` file from the Content Browser at ``Isaac Sim/Robots/Unitree/H1``.
2. In the upper-right corner of the stage, select the ``funnel`` icon and click ``Physics Joints`` to filter the joint list.

   .. image:: /images/isim_5.0_full_tut_gui_rigging_humanoid_1.png
       :align: center
       :width: 80%

3. Left-click the first joint (``left_hip_yaw``), then Shift-left-click the last joint (``right_elbow``) to select all joints.
4. Right-click any selected joint and click **Add** > **Physics** > **Joint State Angular** to create a Joint State API attribute on the joints.
5. Right-click any selected joint and click **Add** > **Physics** > **Angular drive** to create a joint drive API attribute on the joints.

.. note:: The ``Joint State Angular`` API reports the joint position and velocity, and the ``Angular drive`` API drives the joint. If the joint already has a ``Joint State Angular`` API or ``Angular drive`` API, you can skip the previous two steps.

6. For each active joint, convert the ``joint_pos`` and ``joint_vel`` values from radians to degrees.
7. Left-click the joint you are changing.
8. In the Property panel, scroll down to the ``Target Position`` attribute.
9. Set the ``Target Position`` attribute to the converted value from the ``joint_pos`` attribute in the environment definition file.
10. Set the ``Target Velocity`` attribute to the converted value from the ``joint_vel`` attribute in the environment definition file.
11. Repeat the previous steps for each active joint.

12. Press play.

.. note:: When using Newton, physics initialization might fail because reversed joints are not supported for ``/h1/Joints/torso``. If this happens, select the ``torso`` joint. In the Property panel, go to **Physics** > **Joint** and swap the joint bodies so ``Body 0`` is ``/h1/torso_link`` and ``Body 1`` is ``/h1/pelvis``.

13. Verify that the robot moves to the initial position specified in the environment definition file. To make the robot start in the initial position when the simulation starts, store the data in the Joint State API.
14. To prevent the robot from falling indefinitely, add a fixed joint between the robot and the world by right-clicking ``/h1/torso_link`` and selecting **Create** > **Physics** > **Joint** > **Fixed Joint**.

.. image:: /images/isim_5.0_full_tut_gui_rigging_humanoid_2.webp
    :align: center
    :width: 80%

To prevent the Joint State API values from resetting, change the simulation setting so the robot state does not reset on stop.

1. In the upper-left corner of the stage, click **Edit** > **Preferences**.
2. In the **Preferences** window, click the **Physics** tab in the left sidebar.
3. Uncheck **Reset Simulation on Stop**.

   .. image:: /images/isim_5.0_full_tut_gui_rigging_humanoid_3.png
       :align: center
       :width: 80%

Now you can play the simulation, and when you stop the simulation, the robot will remain in the last state. When you play the simulation again, the robot will start from the last state.

4. Delete the fixed joint between the robot and the world.
5. Press **Ctrl+S** to save the USD file.
6. Check **Reset Simulation on Stop** again.

.. _isaac_sim_tutorial_rig_legged_robot_joint_configuration:

Setting the Joint Configuration
===============================

Set the joint configuration to match the policy's robot configuration. This may be different from the values stored in the USD file.
The joint drive configuration is specified under the ``scene:robot:actuators`` section of the environment definition file.

The following snippet shows the actuator configuration for the H1 robot legs.

.. code-block:: yaml
    :linenos:

    actuators:k
      legs:
        class_type: omni.isaac.lab.actuators.actuator_pd:ImplicitActuator
        joint_names_expr:
        - .*_hip_yaw
        - .*_hip_roll
        - .*_hip_pitch
        - .*_knee
        - torso
        effort_limit: 300
        velocity_limit: 100.0
        stiffness:
          .*_hip_yaw: 150.0
          .*_hip_roll: 150.0
          .*_hip_pitch: 200.0
          .*_knee: 200.0
          torso: 200.0
        damping:
          .*_hip_yaw: 5.0
          .*_hip_roll: 5.0
          .*_hip_pitch: 5.0
          .*_knee: 5.0
          torso: 5.0
        armature: null
        friction: null

The ``joint_names_expr`` is a list of joint names to be controlled by the actuator. The ``class_type`` is the actuator type.
The ``effort_limit`` is the maximum effort that can be applied to the joint. The ``velocity_limit`` is the maximum velocity that can be applied to the joint.
The ``stiffness`` defines the joint stiffness. The ``damping`` defines the joint damping. The ``armature`` defines the joint armature, and the ``friction`` defines the joint friction.

To set the joint configurations:

1. Left-click a joint, such as ``left_hip_yaw``.
2. In the Property panel, scroll down to the ``Joint Drive`` attribute and set ``stiffness`` and ``damping`` to the values specified in the environment definition file.

.. note:: Remember to convert stiffness and damping to degree-based units.

The USD file stiffness is in :math:`\frac{kg \cdot m^2}{deg \cdot s^2}` and the damping is in :math:`\frac{kg \cdot m^2}{deg \cdot s}`.
To convert radians to degrees, you can use the following formulas:

.. math::

    S_{deg} = S_{rad} \times \frac{\pi}{180}

.. math::

    D_{deg} = D_{rad} \times \frac{\pi}{180}

The ``effort_limit`` is the maximum effort that can be applied to the joint. Set that value to the ``Max Force`` attribute of the joint drive API.


Scroll down to **Raw USD Properties** under the **Advanced** tab, and set the **Armature** and **Joint Friction** attributes to the values specified in the environment definition file.

For the **Maximum Joint Velocity** attribute, set it to the **velocity_limit** value specified in the environment definition file. Remember to convert it to degrees.

.. math::

    \omega_{deg} = \omega_{rad} \times \frac{180}{\pi}

.. image:: /images/isim_5.0_full_tut_gui_rigging_humanoid_4.png
    :align: center
    :width: 80%

.. note:: Remember to set the joint configurations for all active joints in the robot, such as the arms and legs.

Verifying the Joint Configuration
=================================

To verify the joint configuration, you can play the simulation and run the following snippet in Script Editor to print the joint configuration.

1. Play the simulation.
2. Open Script Editor by clicking **Window** > **Script Editor**.
3. Copy and paste the following snippet into Script Editor.
4. Run the snippet by clicking the **Run** button.

   .. literalinclude:: ../snippets/robot_setup_tutorials/tutorial_rig_legged_robot/run_the_snippet_by_clicking_on_the_run_button.py
       :language: python
       :start-after: # -- End test setup --

5. Verify that you see console output similar to the following:

.. code-block:: console

  ['left_hip_yaw', 'right_hip_yaw', 'torso', 'left_hip_roll', 'right_hip_roll', 'left_shoulder_pitch', 'right_shoulder_pitch', 'left_hip_pitch', 'right_hip_pitch', 'left_shoulder_roll', 'right_shoulder_roll', 'left_knee', 'right_knee', 'left_shoulder_yaw', 'right_shoulder_yaw', 'left_ankle', 'right_ankle', 'left_elbow', 'right_elbow']
    left_hip_yaw: lower=-0.4300, upper=0.4300, maxVelocity=100.00, maxEffort=300, stiffness=149.54, damping=5.00
    right_hip_yaw: lower=-0.4300, upper=0.4300, maxVelocity=100.00, maxEffort=300, stiffness=149.54, damping=5.00
    torso: lower=-2.3500, upper=2.3500, maxVelocity=100.00, maxEffort=300, stiffness=200.00, damping=4.98
    left_hip_roll: lower=-0.4300, upper=0.4300, maxVelocity=100.00, maxEffort=300, stiffness=149.54, damping=5.00
    right_hip_roll: lower=-0.4300, upper=0.4300, maxVelocity=100.00, maxEffort=300, stiffness=149.54, damping=5.00
    left_shoulder_pitch: lower=-2.8700, upper=2.8700, maxVelocity=100.00, maxEffort=300, stiffness=40.00, damping=10.00
    right_shoulder_pitch: lower=-2.8700, upper=2.8700, maxVelocity=100.00, maxEffort=300, stiffness=40.00, damping=10.00
    left_hip_pitch: lower=-3.1400, upper=2.5300, maxVelocity=100.00, maxEffort=300, stiffness=199.96, damping=5.00
    right_hip_pitch: lower=-3.1400, upper=2.5300, maxVelocity=100.00, maxEffort=300, stiffness=199.96, damping=5.00
    left_shoulder_roll: lower=-0.3400, upper=3.1100, maxVelocity=100.00, maxEffort=300, stiffness=40.00, damping=10.00
    right_shoulder_roll: lower=-3.1100, upper=0.3400, maxVelocity=100.00, maxEffort=300, stiffness=40.00, damping=10.00
    left_knee: lower=-0.2600, upper=2.0500, maxVelocity=100.00, maxEffort=300, stiffness=200.00, damping=4.98
    right_knee: lower=-0.2600, upper=2.0500, maxVelocity=100.00, maxEffort=300, stiffness=200.00, damping=4.98
    left_shoulder_yaw: lower=-1.3000, upper=4.4500, maxVelocity=100.00, maxEffort=300, stiffness=40.00, damping=10.00
    right_shoulder_yaw: lower=-4.4500, upper=1.3000, maxVelocity=100.00, maxEffort=300, stiffness=40.00, damping=10.00
    left_ankle: lower=-0.8700, upper=0.5200, maxVelocity=100.00, maxEffort=100, stiffness=20.00, damping=4.00
    right_ankle: lower=-0.8700, upper=0.5200, maxVelocity=100.00, maxEffort=100, stiffness=20.00, damping=4.00
    left_elbow: lower=-1.2500, upper=2.6100, maxVelocity=100.00, maxEffort=300, stiffness=40.00, damping=10.00
    right_elbow: lower=-1.2500, upper=2.6100, maxVelocity=100.00, maxEffort=300, stiffness=40.00, damping=10.00


The limit values in the console output are in radians. Each line shows the properties for a single DOF.
Verify that the ``maxVelocity``, ``maxEffort``, ``stiffness``, and ``damping`` values match the values specified in the environment definition file.

For example, for ``left_hip_yaw``, the max velocity is ``100.0``, the max effort is ``300.0``, the stiffness is ``150.0``, and the damping is ``5.0``.

.. note:: The rigged H1 robot is available in the Content Browser at ``Isaac/Samples/Rigging/H1/h1_rigged.usd``.

Summary
=======================

This tutorial covers the following topics:

* Setting the initial robot position
* Setting the joint configuration
* Verifying the joint configuration
