..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_tutorial_tuning_openusd_module_3:

================================
Tutorial 4: Collider Pairs
================================

We inspected the asset structure and collision meshes. Now we tackle a question that makes or breaks this dexterous hand simulation: **which parts of the hand are allowed to collide with each other?** In the real world, a finger can't pass through the palm, but in simulation, overlapping collision geometry between links can create phantom contacts, jitter, and forces that blow the hand apart. **Filtered Pairs** in Isaac Sim let you turn off collision between specific rigid bodies so you keep the contacts that matter (finger on object, intentional finger-to-finger) and remove the ones that cause instability.

Learning Objectives
===================

In this tutorial, you will:

- **Explain** how **Filtered Pairs** work and when to use them.
- **Identify** problematic collision pairs using the **Physics Debugger**.
- **Add** filtered pairs for the palm and pinky.

Prerequisites
=============

- Complete :ref:`isaac_sim_tutorial_tuning_openusd_module_2` (Tutorial 3: Inspect Asset).
- Have the Inspire Hand scene open in Isaac Sim with joint and collider visualization familiar from the previous tutorial.

Module 3.1: Understanding Filtered Pairs
========================================

**Filtered Pairs** explicitly tell the physics engine: "Do not detect collision between these two rigid bodies." In Isaac Sim, adjacent links (two links connected by a joint) in an articulation don't self-collide by default, but **non-adjacent** links do. As you will see, many of those non-adjacent links can have overlapping or very close collision geometry. In these scenarios, you can get:

- **Unrealistic forces** — The solver tries to resolve interpenetration between links that would never actually touch in the real mechanism.
- **Instability** — The hand can jitter, jump, or blow apart as conflicting contacts fight each other.
- **Wasted compute** — Simulating every anatomically possible self-contact is rarely necessary for grasping or manipulation.

So the goal is to **filter the problematic pairs** while keeping contacts that you care about (e.g. finger–object, or specific finger–finger contacts). Use filtered pairs judiciously: over-filtering can allow unrealistic interpenetration; under-filtering can cause instability. We'll use the **Physics Debugger** to see exactly which pairs are causing trouble, then disable only those.

Module 3.2: Identifying Problematic Collision Pairs
===================================================

**Which pairs should you filter?** It's not always obvious from simple inspection. The **Physics Debugger** is a helpful tool to see solid collision meshes while stepping through the simulation to understand which collision shapes are overlapping.

Here we'll turn on self-collisions, watch the hand become unstable, then use the debugger to guide the filtering.

.. note:: For this tutorial we focus on the **pinky** (little finger) as a clear example; the same workflow applies to other fingers or links.

Step 1: Reproduce the problem
-----------------------------

#. Press **Play**. With self-collisions disabled, the simulation is stable. Press **Stop**.

.. figure:: ../images/isim_6.0_full_tut_gui_simulation_self_collisions_disabled_stable.gif
   :align: center
   :alt: GIF showing simulation with self-collisions disabled (stable).

#. Because enabling **Articulation Root** is a PhysX-specific API, we want to make sure we are authoring on the **physx.usda** layer. In the **Layer** tab, click the **Insert Sublayer** icon to add a new sublayer beneath the current layer stack.

.. figure:: ../images/isim_6.0_full_tut_gui_layer_panel_insert_sublayer_icon.png
   :align: center
   :alt: The Layer panel with the Insert Sublayer icon highlighted.

#. In the file dialog, navigate to your asset's folder and select ``IsaacSim/Samples/Rigging/Inspire/module_1_start/payloads/Physics/physx.usda``. Click **Open** to insert it as a sublayer.

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
   :alt: Layer panel with physx.usda highlighted green as the current authoring layer.

#. In the *Stage* panel, select ``r_base_link``. In the *Property* panel, scroll to **Articulation Root** and check **Self Collisions Enabled**.

.. figure:: ../images/isim_6.0_full_tut_gui_articulation_root_self_collisions_enabled.png
   :align: center
   :alt: Articulation Root with Self Collisions Enabled option.

#. Press **Play** again. Links move erratically as overlapping collision geometry between non-adjacent links is now colliding, and the solver can't resolve it cleanly.

.. figure:: ../images/isim_6.0_full_tut_gui_simulation_instability_self_collisions_enabled.gif
   :align: center
   :alt: GIF showing simulation instability with self-collisions enabled.

Step 2: Visualize solid collision meshes and find overlapping pairs
-------------------------------------------------------------------

We use the pinky as the example: visualize its collision meshes, find the overlaps, then filter those pairs in the next section.

#. Open **Utilities > Physics Debugger** to show the *Physics Debug* panel.

.. figure:: ../images/isim_6.0_full_tut_gui_utilities_physics_debugger_panel.png
   :align: center
   :alt: Open the Physics Debug panel.

#. Have the root prim ``inspire_hand`` selected. In **Collision Mesh Debug Visualization**, enable **Solid Collision Mesh Visualization**.

.. figure:: ../images/isim_6.0_full_tut_gui_solid_collision_mesh_visualization_enable.png
   :align: center
   :alt: Enable Solid Collision Mesh Visualization.

.. tip:: **Solid Collision Mesh Visualization** shows only the collision meshes for the currently selected prim. Ensure the ``inspire_hand`` prim is selected in the *Stage* panel so all collision meshes are visible.

#. Open **Eye > Show by Type > Meshes** and turn **Meshes** off so the solid collision meshes are easier to see.

.. figure:: ../images/isim_6.0_full_tut_gui_solid_collision_mesh_viewport.png
   :align: center
   :alt: Solid collision mesh visualization viewport with meshes hidden.

#. In the *Stage* panel, deactivate the ``right_little_1`` link (lower pinky) to expose the overlapping collision shapes underneath—the rubber pad and surrounding links.

.. figure:: ../images/isim_6.0_full_tut_gui_deactivate_link_rubber_pad_overlap.png
   :align: center
   :alt: Deactivate link to see rubber pad collision shapes overlap.

#. Identify where ``right_little_rubber_1`` (lower pinky rubber pad) overlaps with ``r_base_link`` (palm)—that is where a problematic self-collision is likely to occur.

.. figure:: ../images/isim_6.0_full_tut_gui_viewport_pinky_rubber_palm_overlap.png
   :align: center
   :alt: Viewport showing solid collision meshes; pinky rubber pad and second link overlapping.

In the image above, with the lower pinky link hidden, the lower pinky rubber pad (tan/sand color) overlaps and collides with the palm (yellow). This is an example of a pair we will filter out to ensure stable simulation.

The schematic below shows which rigid body pairs of the pinky we will filter in this tutorial:

.. figure:: ../images/isim_6.0_full_tut_gui_schematic_rigid_bodies_filtered_pairs.png
   :align: center
   :alt: Schematic of rigid bodies and which collision pairs to filter.

#. Open **Eye > Show by Type > Meshes** and toggle **Meshes** on to re-enable mesh visualization.

.. figure:: ../images/isim_6.0_full_tut_gui_solid_collision_mesh_viewport.png
   :align: center
   :alt: Solid collision mesh visualization viewport with meshes visible.

Module 3.3: Adding Filtered Pairs
==================================

Next, we'll filter out two specific collision pairs to prevent problematic self-collisions in the pinky. The pairs to filter are: (1) the palm and the pinky's lower rubber pad, and (2) the lower pinky link and the pinky's upper rubber pad.

.. note:: It doesn't matter whether the filtered pair is a parent or child link; USD's Physics Filtered Pairs will block collisions between the specified pairs in both directions.

Palm and Pinky Link 1 Rubber Pad
---------------------------------

First, let's prevent the palm and the pinky's lower rubber pad from colliding. To follow Asset Structure 3.0 best practices, Filtered Pairs use the neutral Physics API, so we should apply these changes to the appropriate layer—**physics.usda**.

#. In the **Layer** tab, expand **physx.usda**. You should see **physics.usda** listed in the hierarchy.

.. figure:: ../images/isim_6.0_full_tut_gui_layer_tab_physics_usda_under_physx.png
   :align: center
   :alt: Layer tab expanded to show physics.usda under physx.usda.

#. **Right-click on physics.usda** and select **Set Authoring Layer**.

.. figure:: ../images/isim_6.0_full_tut_gui_rightclick_set_authoring_layer_physics_usda.png
   :align: center
   :alt: Right-click context menu to set authoring layer on physics.usda.

You should now see the **physics.usda** layer highlighted green, indicating it is the active authoring layer.

.. figure:: ../images/isim_6.0_full_tut_gui_physics_usda_highlighted_green_authoring_layer.png
   :align: center
   :alt: physics.usda highlighted green, showing it is the active authoring layer.

#. In the *Stage* tab, select the ``r_base_link`` prim. In the *Property* panel, click **Add > Physics > Filtered Pairs**.

.. figure:: ../images/isim_6.0_full_tut_gui_add_physics_filtered_pair_r_base_link.png
   :align: center
   :alt: Right-click on r_base_link to add a Physics Filtered Pair.

#. With ``r_base_link`` still selected, go to the *Property* panel. Find the **Filtered Pairs** section and click **Add Target** to add a new filtered collision pair.

.. figure:: ../images/isim_6.0_full_tut_gui_filtered_pairs_add_target_button.png
   :align: center
   :alt: Property panel showing Filtered Pairs, with Add Target button highlighted.

#. In the pop-up that appears, browse or type to select ``right_little_rubber_1``.

.. figure:: ../images/isim_6.0_full_tut_gui_popup_select_right_little_rubber_1.png
   :align: center
   :alt: Popup window to select right_little_rubber_1 as the filtered pair target.

After completing these steps, collisions between the palm (``r_base_link``) and the pinky's lower rubber pad (``right_little_rubber_1``) are filtered out. This means the overlapping contact points between them are disabled, helping stabilize the simulation and preventing unwanted self-collisions.

Pinky Link 1 and Pinky Link 2 Rubber Pad
----------------------------------------

Now, let's filter collisions between the lower pinky link (``right_little_1``) and the pinky's upper rubber pad (``right_little_rubber_2``).

#. In the *Stage* panel, select the ``right_little_1`` prim (lower link of the pinky). In the *Property* panel, click **Add > Physics > Filtered Pairs**.

.. figure:: ../images/isim_6.0_full_tut_gui_add_physics_filtered_pair_right_little_1.png
   :align: center
   :alt: Right-click on right_little_1 to add a Physics Filtered Pair.

#. With ``right_little_1`` still selected, go to the *Property* panel. Find the **Filtered Pairs** section and click **Add Target** to add a new filtered collision pair.
#. In the pop-up window, browse or type to select ``right_little_rubber_2`` (the upper pinky rubber pad), and confirm the selection.

.. figure:: ../images/isim_6.0_full_tut_gui_right_little_1_filtered_pairs_add_target.png
   :align: center
   :alt: Property panel on right_little_1 prim, Filtered Pairs section with Add Target button.

#. Press **Play**. The pinky (little finger) should now move more stably; the other fingers will still be unstable until their collision pairs are filtered the same way.

.. figure:: ../images/isim_6.0_full_tut_gui_pinky_stable_after_filtered_pairs.gif
   :align: center
   :alt: GIF showing pinky moving stably after filtering its collision pairs.

#. Click on the blue files icon next to **physx.usda (Authoring Layer)** to save the changes to **physx.usda**.

.. figure:: ../images/isim_6.0_full_tut_gui_layer_panel_save_physx_usda.png
   :align: center
   :alt: Layer panel for saving to physx.usda.

.. note:: Open the checkpoint at ``IsaacSim/Samples/Rigging/Inspire/module_3_end-checkpoint_1/inspire_hand.usda`` before starting Tutorial 5. It includes all collision filters for stability, plus additional filtered pairs (e.g. finger tips and pads) for computational performance.

Summary
=======

This tutorial covered:

- How **Filtered Pairs** work and when to use them to prevent invalid self-collisions.
- Using the **Physics Debugger** to visualize collision meshes and identify which pairs were causing instability.
- Adding **filtered pairs** for the palm and pinky so the problematic pairs no longer produce invalid self-collisions.

Next Steps
^^^^^^^^^^

Continue to :ref:`isaac_sim_tutorial_tuning_openusd_module_4` (Tutorial 5: Joint Drive Tuning) to set drive limits (max force, max velocity) from the Inspire Hand specs, then to Tutorial 6 for stiffness and damping with the Gain Tuner.
