..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_tutorial_tuning_openusd_module_4:

====================================
Tutorial 5: Joint Drive Tuning
====================================

Collision pairs are filtered (Tutorial 4). The next question: **with how much torque and velocity can each joint move?** If the simulated hand can apply more torque than the real hardware, or spin faster than the real motors, your grasps and controllers will behave differently in sim than on the robot. Conversely, limits that are too low make the hand feel weak or sluggish. In this tutorial we set the **drive limits**—max torque and max velocity—from the Inspire Hand specs. Stiffness and damping (how the joint *responds* to position commands) are tuned in Tutorial 6.

Learning Objectives
===================

In this tutorial, you will:

- **Configure** mimic joints to be non-compliant for initial gains tuning.
- **Compute and set** max joint torque derived from Inspire specifications.
- **Set** max joint velocity directly from Inspire specifications.

Inspire Hand specs used in this tutorial (palm fingers): Max palm finger grip force 10 N; max palm finger bend speed 260 deg/s.

Prerequisites
=============

- Complete :ref:`isaac_sim_tutorial_tuning_openusd_module_3`.
- Open ``/path/to/Inspire/module_3_end-checkpoint_1/inspire_hand.usda`` in Isaac Sim (or have your own filtered-pairs version open).

Module 4.1: Mimic Joints
=========================

In the Inspire Hand model, the fingers use PhysX **mimic joints** to replicate the underactuated mechanism found in the real robotic hand. In this approach, a single motor drives multiple joints using a fixed gear ratio, allowing for coordinated finger movement and more realistic simulation of the physical hand.

A mimic joint links two degrees of freedom, establishing a relationship (via gear ratio and offset) so that when one joint moves, the other follows accordingly. These mimic joints can be either **compliant** (allowing some "softness" or flexibility, like a spring) or **non-compliant** (rigidly enforcing the kinematic constraint). For this tutorial, we'll configure **non-compliant** mimic joints to initially tune the driven joints. (You can add compliance for "softer" mimic behavior later, if needed.)

Follow these steps to configure the mimic joints:

#. Open ``/path/to/Inspire/module_3_end-checkpoint_1/inspire_hand.usda`` in Isaac Sim if you haven't already.
#. Mimic joints are a PhysX-specific feature, so set your authoring layer to **physx.usda**. In the **Layer** tab, click the **Insert Sublayer** icon if the sublayer is not already there.

.. figure:: ../images/isim_6.0_full_tut_gui_layer_panel_insert_sublayer_icon.png
   :align: center
   :alt: The Layer panel with the Insert Sublayer icon highlighted.

#. In the file dialog, navigate to ``/path/to/Inspire/module_3_end-checkpoint_1/payloads/Physics/``, select ``physx.usda``, and click **Open**.

.. figure:: ../images/isim_6.0_full_tut_gui_file_dialog_physx_usda_sublayer.png
   :align: center
   :alt: File dialog with physx.usda selected as the sublayer to insert.

#. Once **physx.usda** appears in the layer stack, **Right-click on physx.usda** and select **Set Authoring Layer**.

.. figure:: ../images/isim_6.0_full_tut_gui_context_menu_set_authoring_layer_physx.png
   :align: center
   :alt: Context menu with Set Authoring Layer highlighted for physx.usda.

You should now see the **physx.usda** layer highlighted green, indicating it is the active authoring layer.

.. figure:: ../images/isim_6.0_full_tut_gui_layer_panel_physx_usda_highlighted_green.png
   :align: center
   :alt: Layer tab with physx.usda highlighted green.

#. In the *Stage* panel, multi-select the mimic joints for the Inspire Hand palm fingers (hold **CTRL** and left-click each):

   - ``right_thumb_3_joint``
   - ``right_thumb_4_joint``
   - ``right_index_2_joint``
   - ``right_middle_2_joint``
   - ``right_ring_2_joint``
   - ``right_little_2_joint``

.. figure:: ../images/isim_6.0_full_tut_gui_stage_panel_mimic_joints_multiselected.png
   :align: center
   :alt: Stage panel with all mimic joints multi-selected.

#. With the joints selected, go to the *Property* panel. Find the **Mimic Joint** section and set **Damping Ratio** to **0.0** and **Natural Frequency** to **0.0** to make the constraint non-compliant.

.. figure:: ../images/isim_6.0_full_tut_gui_mimic_joint_damping_ratio_natural_frequency_non_compliant.png
   :align: center
   :alt: Setting Damping Ratio and Natural Frequency for non-compliant mimic joints.

.. tip:: Setting natural frequency or damping ratio to **0.0** tells PhysX to make this a non-compliant mimic joint. Setting both of them to **0.0** makes the intent clear.

#. Click on the blue files icon next to **physx.usda (Authoring Layer)** to save the changes to **physx.usda**.

.. figure:: ../images/isim_6.0_full_tut_gui_layer_panel_save_physx_usda.png
   :align: center
   :alt: Layer panel for saving to physx.usda.

After these steps, the mimic joints in your Inspire Hand model will behave as a stiff, non-compliant mechanism, giving you precise control for gains tuning in the next module.

Module 4.2: Configure Max Joint Torque
======================================

The maximum drive force (torque for revolute joints) caps how much force the finger can apply at the contact. Too low and the hand cannot hold the specified load; too high and you risk unrealistic forces or instability. We derive the value from the manufacturer's grip force and the distance from joint to fingertip so the sim matches the real hand's capability.

**Torque = Force × Distance**

For the palm finger, max force is 10 N. The distance between ``right_little_1_joint`` and the tip of the little finger is 0.045 m + 0.039 m.

**Little finger:** Torque = 10 × (0.045 + 0.039) = 0.84 Nm

There are two joints in the mimic chain, so multiply by 2:

**Little finger max drive force:** 0.84 × 2 = 1.68 Nm

#. Max Force drive parameters are a neutral physics attribute, so author on the **physics.usda** layer. In the **Layer** tab, expand the **physx.usda** layer.

.. figure:: ../images/isim_6.0_full_tut_gui_layer_tab_physics_usda_under_physx.png
   :align: center
   :alt: Expand physx.usda.

#. **Right-click on physics.usda** and select **Set Authoring Layer**.

.. figure:: ../images/isim_6.0_full_tut_gui_rightclick_set_authoring_layer_physics_usda.png
   :align: center
   :alt: Set physics.usda as the authoring layer.

You should now see the **physics.usda** layer highlighted green, indicating it is the active authoring layer.

.. figure:: ../images/isim_6.0_full_tut_gui_physics_usda_highlighted_green_authoring_layer.png
   :align: center
   :alt: physics.usda highlighted green, showing it is the active authoring layer.

#. In the *Stage* panel, find and select ``inspire_hand/Physics/right_little_1_joint``.
#. In the *Property* panel, scroll to **Drive** and set **Max Force** to **1.68** based on our calculations.

.. figure:: ../images/isim_6.0_full_tut_gui_drive_max_force_1_68_right_little_1_joint.png
   :align: center
   :alt: Drive section with Max Force set to 1.68 for right_little_1_joint.

#. Click on the blue files icon next to **physics.usda (Authoring Layer)** to save the changes to **physics.usda**.

.. figure:: ../images/isim_6.0_full_tut_gui_layer_panel_save_physics_usda.png
   :align: center
   :alt: Layer panel for saving to physics.usda.

Module 4.3: Apply Max Velocity
===============================

Maximum joint velocity limits how fast the joint can move. Without a cap, the solver can command velocities that no real motor could achieve, leading to unrealistic motion or numerical instability. We set the limit from the Inspire Hand's palm finger bend speed (260 deg/s) so the simulated hand moves within the same envelope as the hardware.

- **Realism** — Simulated motion matches real hardware.
- **Stability** — Avoids velocity spikes that cause instability.

#. Maximum joint velocity is a PhysX-specific attribute, so author on the **physx.usda** layer. In the **Layer** tab, **Right-click on physx.usda** and select **Set Authoring Layer**.

.. figure:: ../images/isim_6.0_full_tut_gui_context_menu_set_authoring_layer_physx.png
   :align: center
   :alt: physx.usda set as authoring layer.

You should now see the **physx.usda** layer highlighted green, indicating it is the active authoring layer.

.. figure:: ../images/isim_6.0_full_tut_gui_layer_panel_physx_usda_highlighted_green.png
   :align: center
   :alt: Layer tab with physx.usda highlighted green.

#. In the *Stage* panel, find and select ``inspire_hand/Physics/right_little_1_joint``.
#. In the *Property* panel, scroll to **Raw USD Properties**, expand **Advanced**, and set **Maximum Joint Velocity** to **260** (deg/s).

.. figure:: ../images/isim_6.0_full_tut_gui_drive_advanced_max_joint_velocity_260.png
   :align: center
   :alt: Drive Advanced section with Maximum Joint Velocity set to 260.

#. Click on the blue files icon next to **physx.usda (Authoring Layer)** to save the changes to **physx.usda**.

.. figure:: ../images/isim_6.0_full_tut_gui_layer_panel_save_physx_usda.png
   :align: center
   :alt: Layer panel for saving to physx.usda.

.. note:: A checkpoint with all mimic joints and all joint drive maximums configured is ``/path/to/Inspire/module_4_end-checkpoint_2/inspire_hand.usda``. Open this file before starting Tutorial 6.

Summary
=======

This tutorial covered:

- Configuring **mimic joints** as non-compliant so the solver enforces the finger kinematics without adding compliance—setting you up for clean gain tuning in Tutorial 6.
- **Computing and setting max joint torque** from Inspire Hand specs (force × distance, then × 2 for the mimic chain) so the hand's grip capability matches the real robot.
- Setting **max joint velocity** from specs (260 deg/s) so motion is realistic and the simulation stays stable.

Next Steps
^^^^^^^^^^

Continue to :ref:`isaac_sim_tutorial_tuning_openusd_module_5` to tune drive stiffness and damping with the Gain Tuner and analyze the results.
