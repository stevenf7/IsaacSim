.. meta::
    :title: Asset optimization
    :keywords: lang=en 

.. _isaac_asset_optimization:

===============================
Tutorial 12: Asset Optimization
===============================

Learning Objectives
====================

This tutorial details how to make robot assets more performant and where to find tradeoffs to achieve a faster simulation or rendering time. 

*30 Minutes Tutorial*

Getting Started
===============

**Prerequisites**

- Complete the :ref:`isaac_sim_intro_quickstart_series` series to learn the basic core concepts of how to navigate inside |isaac-sim|.
- Complete the :ref:`Assemble a Simple Robots <isaac_sim_app_tutorial_gui_simple_robot>` tutorial to learn the concepts of rigid body API, collision API, joints, drives, and articulations.
- Read :doc:`extensions:ext_onshape` and watch the videos on rigging the robot in Onshape.
- Familiarity with :ref:`Mesh Merge Tool<isaac_merge_mesh>`.

**Loading the Robot**

This tutorial explores the NVIDIA Jetbot Robot asset which improve performance. 
If you import the asset from a different source, for example from custom CAD, you might end up with numerous meshes per rigid body and this can severely impact performance.

From the recording of this Jetbot asset imported from CAD that on the right side we have an unoptimized asset, and it's achieving 40 FPS, while the asset on the left was optimized, and now achieves 64 FPS.

.. image:: /images/isim_5.0_full_tut_gui_asset_optimization_1.webp
    :width: 100%
    :align: center
    :alt: Jetbot Optimized comparison

Asset Structure Optimization
============================

In this activity, you use a workflow with the multi-layered asset structure introduced in an earlier module, 
and create an optimized version of an asset.
Use the Jetbot robot as a starting place. This model was imported from a CAD model made in Onshape. 
Although the physics layer is already in place, the bodies contain a significant number of meshes, which leads to suboptimal simulation performance.
Begin with an empty stage to learn several useful tricks for asset authoring. 
By the end of this activity, you transform the initial Jetbot model into a well-structured, optimized asset ready for efficient simulation.

Set Up Reparenting and Layers
------------------------------

#. In Isaac Sim, go to **Edit** > **Preferences** to open the Preferences panel.
#. Under **Stage** > **Authoring**, next to the ** Keep Prim World Transform When reparenting**, ensure that **Inherit Parent Transform** is selected.

    .. image:: /images/isim_5.0_full_tut_gui_asset_optimization_2.png
        :width: 100%
        :align: center
        :alt: Preferences panel

#. Open the Jetbot located at ``Isaac Sim/Samples/Rigging/Jetbot/Jetbot_Optimized/Jetbot_optimized.usd``, verify that you have an empty USD.
#. Select the **Layers** panel, click the **Insert Sublayer** button at the bottom of the tab, select ``Isaac Sim/Samples/Rigging/Jetbot/Jetbot_Base/Jetbot_base.usd``, and click **Open**.

    .. image:: /images/isim_5.0_full_tut_gui_asset_optimization_3.png
        :width: 100%
        :align: center
        :alt: Insert Sub Layer

Create Asset Structure
-----------------------------
The Jetbot asset is already close to the final goal, but to work on a retargeting of the structure to get the merged meshes, 
create a new prim to be set as default.

#. On the right side menu of the Stage panel, select **Show Root**.

    .. image:: /images/isim_5.0_full_tut_gui_asset_optimization_4.png
        :width: 100%
        :align: center
        :alt: Jetbot asset

#. Create a new Xform called ``Jetbot_Sim`` and drag it onto Root.
#. Right click on ``Jetbot_Sim`` and choose **Set as Default Prim**.
#. Right click and choose **Create** > **Scope** and name it ``Visuals``.
#. Drag this scope onto Root so it's unparented from ``Jetbot_Sim``.
#. Select the prims under ``Jetbot`` and drag them onto ``Jetbot_Sim``.

    .. image:: /images/isim_5.0_full_tut_gui_asset_optimization_5.png
        :width: 100%
        :align: center
        :alt: Jetbot asset

    .. note::
        To select multiple prims, use shift-select or control-select standards. For example: select one prim, then hold shift and another to choose all prims listed between them. 

#. Verify that instead of being deleted from Jetbot, they were instead deactivated.
#. Select them all, then right-click and choose **Activate**.

    .. image:: /images/isim_5.0_full_tut_gui_asset_optimization_6.png
        :width: 100%
        :align: center
        :alt: Jetbot asset

#. Delete the contents inside the prims in ``Jetbot_Sim``.

    .. image:: /images/isim_5.0_full_tut_gui_asset_optimization_6a.png
        :width: 100%
        :align: center
        :alt: Jetbot asset

Merge Meshes
------------

With the stage ready, you can begin merging the meshes.

.. note:: The Mesh Merge Tool is deprecated and will be removed in a future release. Use the Scene Optimizer extension instead.

First, enable the merge mesh tool by going to **Window** > **Extensions** and search for **Isaac Sim Mesh Merge** or **isaacsim.util.merge_mesh** in the deprecated extensions and toggle it on.

#. Open the Mesh Merge Tool by going to **Tools** > **Robotics** > **Asset Editors** > **Mesh Merge Tool**.
#. Select ``Jetbot/left_wheel`` prim.
#. Check the **Combine Materials** box, insert ``Jetbot_Sim/Looks`` to save the material in the Jetbot Sim xform.

    .. image:: /images/isim_5.0_full_tut_gui_asset_optimization_7.png
        :width: 100%
        :align: center
        :alt: Mesh Merge Tool

#. Click on **Merge**.
#. Select the resulting mesh on ``/Merged/left_wheel`` and clear the transform on the properties panel.

    .. image:: /images/isim_5.0_full_tut_gui_asset_optimization_8.png
        :width: 100%
        :align: center
        :alt: Mesh Merge Tool

#. Right-click on the **Visuals** scope, create an xform called ``left_wheel`` and drag the resulting mesh into it. Remove the ``/Merged`` xform from the stage.

    .. image:: /images/isim_5.0_full_tut_gui_asset_optimization_9.png
        :width: 100%
        :align: center
        :alt: Mesh Merge Tool

#. To create an internal reference to the wheel, create a **Visuals** Xform inside ``left_wheel``, then right-click it and choose **Add** > **Reference**.

    .. image:: /images/isim_5.0_full_tut_gui_asset_optimization_10.png
        :width: 100%
        :align: center
        :alt: Mesh Merge Tool

#. Select ``Isaac Sim/Samples/Rigging/Jetbot/Jetbot_Base/Jetbot_base.usd`` in the dialog.

    .. image:: /images/isim_5.0_full_tut_gui_asset_optimization_11.png
        :width: 100%
        :align: center
        :alt: Mesh Merge Tool

#. For ``prim_path``, type in ``/Visuals/left_wheel``.

    .. image:: /images/isim_5.0_full_tut_gui_asset_optimization_12.png
        :width: 100%
        :align: center
        :alt: Mesh Merge Tool

#. Back in the **Stage** panel, select the ``/Jetbot_Sim/Visuals/left_wheel`` prim, which you just added a reference onto. Then in the **Property** panel, scroll down to the **References** section. The prim path is in red, select the Asset Path entry and **clear** it.
#. This will make the reference point to the internal ``/Jetbot_Sim/Visuals/left_wheel`` prim. The mesh for ``left_wheel`` shows as a child. Verify that a **Looks** scope was created in ``Jetbot_Sim``, with the materials for this mesh.

    .. image:: /images/isim_5.0_full_tut_gui_asset_optimization_12a.png
        :width: 100%
        :align: center
        :alt: Mesh Merge Tool

#. Verify that the wheel is referenced correctly in place, along with the base mesh that is at the origin. You can hide the Visuals scope so base meshes won't be visible.

    .. image:: /images/isim_5.0_full_tut_gui_asset_optimization_13.png
        :width: 100%
        :align: center
        :alt: Mesh Merge Tool

#. Save the file with CTRL+S.
#. To complete the mesh optimization,  repeat the previous steps for other bodies.

.. note::
    The finished USD with all mesh merges is available for you at ``Isaac Sim/Samples/Rigging/Jetbot/Jetbot_Optimized/Jetbot_optimized_post_merge.usd``.


Scenegraph Instancing
=============================

Scenegraph instancing enables sharable, composed representations of subgraphs of prims. It is a directive that instructs the scene composer that a certain component of the scene is a repeatable pattern. While this allows for a leaner overall scene, it does require a few rules to be followed.

Any children of an instance cannot have attributes modified, because they all inherit from the same asset in memory.
Instances must be applied on Referenced assets, so that the scenegraph composer knows that from the reference and downwards, things are expected to remain the same and it needs to create a pointer to the asset data to be used anywhere it's referenced.

#. Start by opening the USD file ``Isaac Sim/Samples/Rigging/Jetbot/Jetbot_Optimized/Jetbot_optimized_post_merge.usd``, if you have not merged all the meshes.
#. The left and right wheel meshes are identical. Further simplify the asset by having left and right wheel reference the same mesh. Select ``Visuals/left_wheel`` and rename it to ``Visuals/wheel``.
#. Delete ``Visuals/right_wheel``. Verify that the Jetbot wheel disappears.
#. Select ``Jetbot_Sim/right_wheel/Visuals``.
#. Under the References section of the **Property** panel, replace the reference Prim Path from ``/Visuals/right_wheel`` to ``/Visuals/wheel``.

    .. image:: /images/isim_5.0_full_tut_gui_asset_optimization_14.png
        :width: 100%
        :align: center
        :alt: scenegraph instancing

   At this point, all meshes are still considered unique elements because the assets are only defined as a reference.

#. To leverage memory savings, shift-select all Visuals prims under ``/Jetbot_Sim`` and check **Instanceable** in the Property panel.
#. On the Visuals prims, notice the reference icon now has a blue “I” on it. This indicates they are instantiable meshes and effectively applying any memory savings.

    .. image:: /images/isim_5.0_full_tut_gui_asset_optimization_16.png
        :width: 100%
        :align: center
        :alt: scenegraph instancing

#. Save the file with CTRL+S.

.. note::
    The finished USD with all mesh merges and scenegraph instancing is available for you at ``Isaac Sim/Samples/Rigging/Jetbot/Jetbot_Optimized/Jetbot_optimized_final.usd``.

Other Considerations
====================

* **Minimize Number of Lights**: Each light negatively impacts the performance of the rendering. By default, if the scene has more than 10 lights, the rendering reverts to sample-based lighting to avoid severe slowdown in performance.
* **Reduce Translucent Materials**: Each translucent material generates a larger performance bottleneck than the default OmniPBR material.
* **Optimize Physics Performance**: Search for simulation aspects that you can modify to reduce computational cost. Typically, colliders have high computational costs. The more basic that you can make a collision shape, the more performant the simulation behaves. Reducing the number of contact points can also bring huge performance benefits. Tuning this can take several experiments to achieve the best precision versus performance point for your situation.
* **Approximate Wheel Colliders**: If you have a wheel collider, consider using a simple cylinder or sphere collider instead of a mesh collider. This can significantly improve performance and allows the robot to drive smoothly over terrains.