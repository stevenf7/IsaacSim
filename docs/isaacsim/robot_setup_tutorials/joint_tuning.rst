..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_advanced_joint_tuning:

==========================================
Tutorial: Tuning joint drive gains
==========================================

Learning Objectives
===================

In this tutorial, you use the Gain Tuner to bring an un-tuned UR10 manipulator from zero gains to a working set of stiffness and damping values. Along the way you learn how to:

- Diagnose missing or insufficient gains with the **Snap-to-Limits** test.
- Distinguish **Fail** from **Blocked** results using the **Disable Self-Collisions** toggle.
- Validate tuned gains with the **Stress Test** and observe how velocity limits contribute to solver stability.

For a full explanation of how the Gain Tuner works, the physics behind joint drives, and the complete parameter reference for each test, see :ref:`isaac_gain_tuner`.

*10-15 Minute Tutorial*


Prerequisites
=============

- Complete the :ref:`isaac_sim_app_tutorial_advanced_import_urdf` tutorial to import the UR10 onto the stage. The URDF importer sets all joint stiffness and damping to zero by default, so the robot has no active drives.
- Read the :ref:`isaac_gain_tuner` reference for background on the parameters, physics, and detailed result interpretation guide.


Step 1: Open the Gain Tuner and observe zero gains
====================================================

#. Go to **Tools** > **Robotics** > **Asset Editors** > **Gain Tuner**.
#. Select the UR10 from the **Select Robot** dropdown.
#. Ensure that **Mode** is set to **Position** for each joint.
#. Observe that all six joints --- ``shoulder_pan_joint``, ``shoulder_lift_joint``, ``elbow_joint``, ``wrist_1_joint``, ``wrist_2_joint``, ``wrist_3_joint`` --- have **Stiffness** and **Damping** set to ``0``. With zero gains the robot has no active drives and will collapse under gravity when the simulation is played.

.. image:: /images/isim_6.0_full_tut_gui_gain_tuner_ur10_zero_gains.png
    :align: center
    :alt: Gain Tuner with the UR10 selected and all gains at zero


Step 2: Snap-to-Limits with weak gains
========================================

Set initial gains to see how the robot responds with deliberately low stiffness and no damping:

#. In the **Stiffness** column, set all six joints to ``10``. Leave **Damping** at ``0``.
#. Select the **Snap-to-Limits** test mode (the default).
#. Enable the **Test** checkbox for all joints.
#. Press **Play**, then press **Run Test**.

With stiffness at only 10 Nm/rad and no damping, expect:

- ``shoulder_lift_joint`` and ``elbow_joint`` are likely to **Fail**. These joints bear the full weight of the arm and 10 Nm/rad of stiffness is far too low to drive them to their limits.
- Wrist joints may also **Fail** or show long settling times with oscillation, since there is no damping to absorb overshoot.
- Some joints may report **Blocked** if the collision geometry prevents them from reaching a limit.

.. image:: /images/isim_6.0_full_tut_gui_gain_tuner_ur10_snap_to_limits_weak_gains.png
    :align: center
    :alt: Gain Tuner with the UR10 selected and stiffness set to 10 Nm/rad

.. note::
   If a joint reports **Blocked**, re-run with **Disable Self-Collisions** enabled. If the joint then passes, the joint limit extends beyond what the collision geometry allows --- tighten the joint limit in USD rather than adjusting gains.


.. _tuned_ur10_gains_table:

Step 3: Tuned parameters
==========================

Before adjusting gains, check the joint force limits. The UR10's URDF defines max effort values (330 Nm for the shoulder joints, 150 Nm for the elbow, 56 Nm for the wrist joints) that are imported as the joint **Max Force** in USD. With high stiffness, the PD controller may need to apply forces that exceed these limits to drive the heavy shoulder and elbow links to their targets. If a joint still fails Snap-to-Limits after increasing stiffness, select the joint in the **Properties** panel and set **Max Force** to a higher value or to ``inf`` (infinite) under **Joint** > **Advanced** > **Maximum Force**. For the UR10, ``shoulder_pan_joint`` and ``shoulder_lift_joint`` require infinite max force to pass.

The following gains produce a UR10 that passes Snap-to-Limits. They were found using the position-drive tuning heuristic described in the :ref:`Tuning Workflow <isaac_gain_tuner_tuning_workflow>` section of the Gain Tuner reference:

.. list-table::
   :header-rows: 1
   :widths: 30 20 20

   * - Joint
     - Stiffness
     - Damping
   * - ``shoulder_pan_joint``
     - 500000
     - 50
   * - ``shoulder_lift_joint``
     - 500000
     - 50
   * - ``elbow_joint``
     - 50000
     - 50
   * - ``wrist_1_joint``
     - 500
     - 0.5
   * - ``wrist_2_joint``
     - 500
     - 0.5
   * - ``wrist_3_joint``
     - 50
     - 0.0

.. note::
   These values are starting-point examples. Fine-tune them for your specific application by iterating with the Gain Tuner tests. The shoulder and elbow joints require higher gains because they bear the weight of the full arm, while the lighter wrist joints respond well at lower values.

Enter these values, re-run the Snap-to-Limits test, and confirm that all joints now **Pass**.

.. image:: /images/isim_6.0_full_tut_gui_gain_tuner_ur10_snap_to_limits_tuned_gains.png
    :align: center
    :alt: Gain Tuner with the UR10 selected and gains set to the values in the table

You can further validate tracking quality with the **Sinusoidal** and **Step Function** test modes. For configuration details and result interpretation, see :ref:`isaac_gain_tuner_sinusoidal` and :ref:`isaac_gain_tuner_step_function`.


Step 4: Stress Test with tuned gains
======================================

With the tuned gains from :ref:`tuned_ur10_gains_table` applied, run the Stress Test to verify the robot is stable under the extreme commands typical of reinforcement learning training:

#. Select the **Stress Test** mode and choose the **Random Walk** sub-mode.
#. Set **Sequence** for all joints to ``1`` so that the joints are tested in parallel.
#. Leave **Disable Velocity Limits** off (the default).
#. Press **Play**, then press **Run Test**.
#. All joints should report **Stable**.

.. image:: /images/isim_6.0_full_tut_gui_gain_tuner_ur10_stress_test_stable.png
    :align: center
    :alt: Stress Test results showing Stable joints

Now observe what happens without velocity limits:

#. Enable **Disable Velocity Limits**.
#. Press **Run Test** again.
#. Some joints now report **Unstable**.

.. image:: /images/isim_6.0_full_tut_gui_gain_tuner_ur10_stress_test_unstable.png
    :align: center
    :alt: Stress Test results showing Unstable joints

Without velocity limits, the PD controller responds to the stress test's large position errors by generating forces that accelerate joints to extreme speeds within a single simulation timestep. At these speeds the discrete-time solver can fail to converge, leading to energy blowup or NaN values.

Velocity limits serve two purposes:

- **Physical fidelity** --- real actuators have maximum speeds defined by the manufacturer. The UR10's URDF specifies velocity limits of approximately 2--3 rad/s per joint. Setting these in simulation reproduces the real robot's motion envelope.
- **Solver stability** --- by capping joint speed, velocity limits keep per-step displacements within the range where the PhysX implicit integrator remains numerically stable.

If your application requires higher velocity limits than the manufacturer specification, increase them incrementally and re-run the Stress Test after each change to confirm the solver remains stable at the new limits.

Repeat the comparison in **Adversarial** sub-mode to confirm the same behavior under worst-case correlated configurations.

.. note::
   A **Stable** result is meaningful only at the sigma and snap interval values used. When assessing readiness for Isaac Lab training, record these parameters alongside results. See :ref:`isaac_gain_tuner_stress_test` for a full explanation of how to interpret each result combination.


Summary
=======

This tutorial covered:

#. Starting from an un-tuned UR10 imported from URDF with zero gains.
#. Using Snap-to-Limits to identify joints with insufficient stiffness and distinguishing Fail from Blocked results.
#. Applying tuned gains and confirming all joints pass Snap-to-Limits.
#. Using the Stress Test to demonstrate why velocity limits are important for solver stability.
