..
   Copyright (c) 2025, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_rig_legged_robot:

=============================================================
Tutorial 13: Rigging a Legged Robot for Locomotion Policy
=============================================================

The objective of this tutorial is to explain the process of rigging a legged robot to match the configuration specified by the locomotion policy.
The Isaac Sim :ref:`isaac_sim_policy_controller_class` for inference in Isaac Sim is already handling the process of rigging the robot at run time,
so this tutorial is only relevant if you want to run the robot policy with an external process like ROS.

Learning Objectives
===================

In this tutorial, you will walk through the process of rigging a H1 humanoid robot to match the configuration specified by the H1 flat terrain locomotion policy.

1. Setting initial robot position
2. Setting joint configuration
3. Verifying joint configuration

.. Note:: The H1 flat terrain policy environment definition file is available `here <https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Policies/H1_Policies/h1_env.yaml>`_.


.. _isaac_sim_tutorial_rig_legged_robot_initial_position:

Setting Initial Robot Position
==============================

The initial joint position of the robot is specified under `robot:init_state:joint_pos` section of the environment definition file. The joint names are specified using the `.*` wildcard.

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

.. Note:: The joint positions are specified in radians, where as in USD, the joint positions are specified in degrees.

To store the initial state of the robot:

#. Open the ``h1.usd`` file from the content browser present at ``Isaac Sim/Robots/Unitree/H1``.
#. Create a joint state api for reporting the robot joint position and velocity.

#. On the top right corner of the stage, select the ``funnel`` icon and click ``Physics Joints`` to filter the joint list.

  .. image:: /images/isim_5.0_full_tut_gui_rigging_humanoid_1.png
      :align: center
      :width: 80%

#. Left click on the first joint (``left_hip_yaw``), shift left click on the last joint (``right_elbow``) to select all the joints.
#. Right click on any selected joint, and click **Add** > **Physics** > **Joint State Angular** to create a joint state API attribute to the joints
#. Right click on any selected joint, and click **Add** > **Physics** > **Angular drive** to create a joint drive API attribute to the joints

  .. Note:: The ``Joint State Angular`` API is used to report the joint position and velocity, and the ``Angular drive`` API is used to drive the joint. If the joint already has a ``Joint State Angular`` API or ``Angular drive`` API, you can skip the above steps.

#. Go to each joint and set the ``Target Position`` attribute in the joint drive API to the value specified in the environment definition file above on the ``joint_pos`` attribute.
#. Similarly, set the ``Target Velocity`` attribute in the joint drive API to the value specified in the environment definition file above on the ``joint_vel`` attribute.
#. Make sure you convert the joint positions and velocities from radians to degrees.

#. Left click on the joint you are changing.
#. In the property panel below, scroll down to the ``Target Position`` attribute.
#. Set the ``Target Position`` attribute to the value specified in the environment definition file above on the ``joint_pos`` attribute
#. Repeat the same for the ``Target Velocity`` attribute

#. Press play.
#. Verify that you see the robot moving to the initial position specified in the environment definition file. To make the robot start in the initial position when the simulation starts, store the data in the joint state API.

#. To prevent the robot from falling infinitely, you can add a Fixed Joint between the robot and the world by right clicking on the ``/h1/torso_link`` and click **Create** > **Physics** > **Joint** > **Fixed Joint**.

.. image:: /images/isim_5.0_full_tut_gui_rigging_humanoid_2.webp
    :align: center
    :width: 80%

To prevent the joint state API values from resetting, you need to change the simulation setting to not reset the robot state on stop.

#. On the top left corner of the stage, click on the **Edit** and click **Preferences**.
#. Select the **Preferences** window at the bottom, on the left side, click on the **Physics** tab.
#. Uncheck **Reset Simulation on Stop**.

  .. image:: /images/isim_5.0_full_tut_gui_rigging_humanoid_3.png
      :align: center
      :width: 80%

  Now you can play the simulation, and when you stop the simulation, the robot will remain in the last state. When you play the simulation again, the robot will start from the last state.

#. Delete the Fixed Joint between the robot and the world.
#. Press **Ctrl+S** to save the USD file.
#. Check **Reset Simulation on Stop** again.

.. _isaac_sim_tutorial_rig_legged_robot_joint_configuration:

Setting Joint Configuration
===========================

Set the joint configuration to match the policy's robot configuration, this maybe different from the value stored in the USD file.
The joint drive configuration is specified under ``scene:robot:actuators`` section of the environment definition file.

The snippet below shows the actuator configuration for the H1 robot legs.

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

The ``joint_names_expr`` is a list of joint names to be controlled by the actuator. The ``class_type`` is the type of the actuator to be used.
The ``effort_limit`` is the maximum effort that can be applied to the joint. The ``velocity_limit`` is the maximum velocity that can be applied to the joint.
The ``stiffness`` is the stiffness of the joint. The ``damping`` is the damping of the joint. The ``armature`` is the armature of the joint. The ``friction`` is the friction of the joint.

To set the joint configurations:

#. Left click on a joint such as ``left_hip_yaw`` for example.
#. In the property panel, scroll down to ``joint drive`` attribute, and set the ``stiffness``, ``damping`` to the values specified in the environment definition file.

.. Note:: Remember to convert stiffness and damping to degrees.

The USD file stiffness is in :math:`\frac{Kg \cdot m^2}{Deg \cdot s^2}` and the damping is in :math:`\frac{Kg \cdot m^2}{Deg \cdot s}`.
To convert radians to degrees, you can use the following formulas:

.. math::

    S_{deg} = S_{rad} \times \frac{\pi}{180}

.. math::

    D_{deg} = D_{rad} \times \frac{\pi}{180}

The ``effort_limit`` is the maximum effort that can be applied to the joint, set that value to the ``Max Force`` attribute of the joint drive API.


Scroll down to **Raw USD Properties** under the **Advanced** tab, set the **Armature**, **Joint Friction** attribute to the value specified in the environment definition file.

For the **Maximum Joint Velocity** attribute, set it to the **velocity_limit** value specified in the environment definition file, remember to convert it to degrees.

.. math::

    \omega_{deg} = \omega_{rad} \times \frac{180}{\pi}

.. image:: /images/isim_5.0_full_tut_gui_rigging_humanoid_4.png
    :align: center
    :width: 80%

.. note:: Remember to set the joint configurations for all active joints in the robot. For example, arms and legs.

Verify Joint Configuration
===========================

To verify the joint configuration, you can play the simulation and run the following snippet in script editor to print the joint configuration.

#. Play the simulation.
#. Open the script editor by clicking on **Window** > **Script Editor**.
#. Copy and paste the following snippet into the script editor.
#. Run the snippet by clicking on the **Run** button.

  .. literalinclude:: ../snippets/robot_setup_tutorials/tutorial_rig_legged_robot/run_the_snippet_by_clicking_on_the_run_button.py
      :language: python
      :start-after: # -- End test setup --

#. Verify that you see the console output like the following:

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

.. Note:: The rigged H1 robot is available in the content browser at ``Isaac/Samples/Rigging/H1/h1_rigged.usd``.

Summary
=======================

This tutorial covered the following topics:

* Setting initial robot position
* Setting joint configuration
* Verifying joint configuration

