.. _isaac_sim_app_tutorial_advanced_rigging_complex:

=======================================
Tutorial 10: Rig Closed-Loop Structures
=======================================

Some models are challenging to represent. Robots and grippers still have unique features and structures that are uncommon. In this document you learn some techniques to model these unique features and learn a general approach for managing these unique configurations.

Learning Objectives
===================

In this tutorial, you will:

- Use USD Layers to edit and test assets
- Add materials and adjust joints post CAD import
- Break a closed loop articulation chain
- Add joint drives, including mimic joints
- Adjust collision shapes
- Test grippers by building a test setup and using a gripper controller OmniGraph

*30 Minutes Tutorial*

Start with a `Robotiq 2F-85 Parallel Gripper <https://robotiq.com/products/2f85-140-adaptive-robot-gripper>`_ STP file imported into an `Onshape document <https://cad.onshape.com/documents/02712153b53a69118b4e5c99/w/e4160a7cfa8bb14f2585a92f/e/6d63d85251b40eee71da6b56>`_ and with joints modeled. This tutorial does not directly cover tuning the joints. Instead, tuned parameters are provided when configuring the asset. To learn more about gains tuning see :ref:`isaac_sim_app_tutorial_advanced_joint_tuning` and :ref:`isaac_gain_tuner`.

Getting Started
===============

**Prerequisite**

- Complete the :ref:`isaac_sim_intro_quickstart_series` series to learn the basic core concepts of how to navigate inside |isaac-sim|.
- Complete the :ref:`Assemble a Simple Robot <isaac_sim_app_tutorial_gui_simple_robot>` and :ref:`Adding Sensors and Cameras <isaac_sim_app_tutorial_gui_camera_sensors>` tutorials to learn the concepts of rigid body API, collision API, joints, drives, and articulations.
- Read :doc:`extensions:ext_onshape` and watch the videos on rigging the robot in Onshape.
- Have a version of the Robotiq 2F-85 Gripper imported in Onshape and model the joints that connect the fingers together and to the body.

.. Note:: The Onshape document used in this tutorial is publicly available. The imported USD asset is located at ``Samples/Rigging/Gripper/Robotiq 2F-85`` to get started.

Rigging the Robot
=================

Using Layers to Edit and Test an Asset
--------------------------------------

All the rigid body, masses, and joint definition are done in `Onshape <https://docs.omniverse.nvidia.com/extensions/latest/ext_onshape.html#configuring-mates-for-physics>`_. After they are imported to |isaac-sim_short|, the asset contains basic joint information and rigid bodies setup. You must complete a few additional steps to make the asset fully functional.

Instead of opening the original asset, edit the asset using **layers**. Layers allow for building a scene on top of a root asset and saving it without changing the underlying root layer assets. For example, you can add a ground plane and objects used to test the gripper, save the testing setup in the layers, while keeping the original gripper asset free of any extraneous items used for testing.

#. Create a new stage without the reference added during import. 
#. Save this stage with the name :code:`Robotiq_2F_85_config.usd` at the same folder as the imported assets (you can locate the source file in the Reference or Payload section on the Property panel, and click the "Locate file" icon). 
#. Open the layer tab and drag the :code:`Robotiq_2F_85_edit.usd` in the **Root Layer**.

There is also a file named :code:`Robotiq_2F_85_base.usd` in the source folder. This is the clean stage post import from Onshape and must not be directly edited to facilitate updates when the asset is re-imported from Onshape.

.. image:: /images/isaac_robotiq_layer.png

The *Authoring layer* is where changes are saved. To switch between layers, double click on the choice. 

If changes are made in the wrong authoring layer you can drag the prims with the delta between layers to merge them into the receiving layer. Use this to your benefit by first authoring everything in the Root layer. After you are satisfied, you can drag your updates to the :code:`Robotiq_2F_85_edit.usd` layer.

This is how the joints were named for this asset:

.. image:: /images/isaac_robotiq_joints.png
    :width: 800

.. note:: Remember to combine parts that make rigid bodies on Group Mates before importing, to simplify the rigid bodies on stage (also useful for renaming the fingers to ``left_finger_...`` and ``right_finger_...``).


Adjusting Joints Post Import
============================

Sometimes a limitation with the Onshape Client API causes the joints to become flipped 180 degrees from the drawing. To fix that, select the joints that are flipped, and apply an equal 180 degrees offset in Rotation 0 and Rotation 1 X axis. With the asset you imported, this was the case on the four joints.

The joints :code:`[left, right]_outer_finger_joint` require limits [0,180] and :code:`[finger_joint, right_outer_knuckle_joint]` require limits [0, 75]. Leave all other joints unconstrained.

Add fingertip physics material to increase the friction contact:

#. Open the Menu **Create** > **Physics** > **Physics Material**.
#. Select **Rigid Body Material**.
#. Rename the material to ``fingertip_material``.
#. Set both friction coefficients to 0.8 (default rubber) and friction **Combine Mode** ``Max``.
#. Select ``right_inner_finger`` and ``left_inner_finger``. Scroll down to **Physics**, in Physics materials on selected models pick the created material.

.. Note:: you may need to de-select instanceable for the two xforms in ``right/left_inner_finger``, and set the physics materials on the mesh ``Defeatured_2F_85_PAD_OPEN_fingertipsstep`` directly.

Breaking the Articulation Loop
==============================

If you try to simulate this asset now, you'll get two big warnings on the screen:

.. image:: /images/isaac_robotiq_loop_error.png
    :width: 600

For more information see :ref:`simulation_fundamentals`. Articulations must be kinematic trees, but there is no need to delete any joints. To eliminate those warnings you must choose one joint to exclude from the Articulation and have it be treated as a maximal coordinate joint. Because maximal coordinate joints are treated with a lower priority by the solver, it is the joint that accumulates the most error in simulation. 

In terms of simulation efficiency, the best choice of joint to exclude from articulation is the one that minimizes the length of articulations. However, you must also consider utility. The best joint to remove is the one that interferes the least with the robot functionality. In an ideal scenario, the joint to exclude from articulation only serves as a spatial constraint. Identify a joint with no limits, no resistance, and no drive. If there are no joints that fit this criteria, transfer these attributes to the adjacent joints before removing it from articulation.

In the case of this gripper, the best option to remove from the articulation are the joints that connect the inner shafts to the gripper body - the ``inner_knuckle_joint`` - highlighted in orange in the image.

1. To remove the joint from the articulation, select the ``left_inner_knuckle_joint`` prim.
2. In the Joint section under physics, select **Exclude From Articulation**.
#. Repeat for the ``right_inner_knuckle_joint``.

.. image:: /images/isaac_robotiq_loop.png
    :width: 800

.. Note:: The fully completed asset is located in the ``Samples/Rigging/Gripper/Robotiq 2F-85_complete`` folder.

Preparing For Tests
===================

Because the gripper is not connected to anything to move it and test its physical properties, add a structure to later help us test the stability of the gripper:

#. Create two Xforms and add the Rigid Body API to them. 
#. Add a fixed joint from world to the first Xform.
#. Add a Prismatic Joint from the first Xform to the second Xform. 
#. Add a second prismatic joint from the second Xform to `base_link`. 
#. Add a Joint drive to the prismatic joints so that you can lift and move forward with a position command. 
#. In the drives set the following:

    - In the Advanced properties for the joint, set a maximum joint velocity of 5.0. 
    - Set the joint limits to [0, 1]. 
    - In the joint drive, set the following:

        * Damping: 10000.0
        * Stiffness: 10000.0

Make sure to move all joints that were just created outside of the `Robotiq_2f_85` prim.

To assist in checking the grip:

#. Create a Cylinder and scale it to ``[0.05, 0.05, 0.2]``.
#. Place the cylinder at ``X=0.12``.
#. Set the cylinder collider to ``Convex Hull``.
#. Create a ground plane and move it to ``Z=-0.1``.

To assist in creating these prims, use the following script. You can run them by opening a Script Editor (**Window > Script Editor**) and pasting the code below.

.. literalinclude:: ../snippets/robot_setup_tutorials/rig_closed_loop_structures/create_a_ground_plane_and_move_it_to_z_01.py
    :language: python

#. Set the target position for Joint X to 1 in the property panel, by going to the Joint Drive section and setting the target position to 1.
#. Set the target position for Joint Z to 1 in the property panel, by going to the Joint Drive section and setting the target position to 1.
#. Verify that you see the fingers ragdoll on the screen. It's still necessary to Tune the Joint Drives for the fingers.

You can see in the video below that the gripper will move forward and lift up.

.. image:: /images/isim_6.0_full_tut_viewport_rig_closed_loop_struct.webp
    :width: 800


Until this point, if you start simulation you will see the fingers rotate freely, and also you will notice collision clipping between the fingers. This is because the fingers do not have drivers that tell them how to move, and because the finger components are connected with joints, there is a natural collision filter between them. This is normal and expected, and you fix it in the next sections.

Adding Joint Drives
===================

Add the Joint Drive API to all joints: 

1. Select all joints on the gripper, then, in the Properties panel, **Add** > **Physics** > **Angular Drive** ( or **Linear Drive** for prismatic joints).

    - In this gripper, the joints that drive the fingers are :code:`finger_joint` and :code:`right_outer_knuckle_joint`. 
    - Additionally, you have to flip the direction of :code:`finger_joint` and :code:`right_outer_knuckle_joint`, by setting lower limit to -75, and upper limit to 0

#. Select all the joints on the gripper, then, in the Properties panel, **Add** > **Physics** > **Joint State** ( or **Joint State Linear** for prismatic joints).

#. Model this gripper as a force-driven grasp. For that, position control must be disabled. Select :code:`finger_joint` and :code:`right_outer_knuckle_joint`, then set **Stiffness** to 10. The **Damping** is set to 0.1. 

#. To control how much pressure is applied when the grippers close, set the :code:`Max Force` to 16.5 (N). 

    - These grippers also have a limit speed at which they can operate. Converting from the data sheet to angular speed at the fingertips, the angular limit speed is 130 degrees per second. 
    
#. In the joint section, under the **Advanced** tab, set the **Maximum Joint Velocity** to 130.0 (deg/s). 

   
Summarizing the changes:

    * Maximum Joint Velocity: 130
    * Max Force: 16.5 (N)
    * Damping: 0.1
    * Stiffness: 10

When trying to control the fingers now, notice that they instantly bulge inwards instead of moving parallel. The system still needs stability to maintain the parallel motion when closing without resistance. 

The Robotiq hand has a spring mechanism at the outer knuckle to keep the fingers parallel until an object is grasped. 

#. Set the stiffness of :code:`[left, right]_inner_finger_joint` to 0.0002, damping to 0.00001 and max force to 0.5 (N) to achieve this behavior.


Adding Mimic Joint
==================

This gripper is controlled with a single input command that moves both fingers concurrently. This is achieved by combining the drive joints together with a Mimic Joint specification. 

#. Select :code:`right_outer_knuckle_joint`.
#. Remove or set all values to zero in the joint drive we just added.
#. On the Properties Panel, click on **Add** > **Physics** > **Mimic Joint**.

    .. note:: Because this is a single degree of freedom revolute joint, the schema axis is not relevant. The UI will show rotX as the default axis, despite the joint being defined in the Z axis.
        
#. In the Mimic settings, set gearing to -1.0 to make it act in the opposite direction of the reference joint.
#. Set the reference Joint to :code:`finger_joint`.

    All drive features are copied over from the reference joint and having an authored joint drive would negatively impact the drive outcome.

    .. note:: The Rotation Axis for the mimic joint only makes a difference, if the joint where mimic is applied contains multiple Degrees of Freedom (for Example Spherical Joint). For Prismatic and Revolute joints any selection will work just the same. It is still recommended to maintain it aligned with the DOF axis.

#. Run the simulation again.


Collision Meshes
==================

The default setting for collision meshes at import is `Convex Hull`. This is a good balance between performance and accuracy. However, for grippers, you often want the fingertips to have a collision mesh that closely follows the contour of fingertips' geometry, so that there won't be any gaps between the fingertips and the objects being grasped. 

To visualize the collision meshes:

#. Find the eye icon on top of the viewport, and click **Show By Type** > **Physics** > **Colliders** > **All**. 
#. Verify that outlines show up surrounding any objects that have collision meshes. 
#. Optionally, to change any collision meshes, select the part of the object associated with that mesh by clicking on it in the viewport, and then in the Physics section of the Property panel, change the Collider Approximation type to `Convex Decomposition`, or any other type that's appropriate for your use case. 
#. If you don't see a Physics or Collider section, then you might need to go down or up the stage tree from the selected item. 
#. The collision API can be applied to a nested child Xform, or the parent of the selected object.



Self-Collision
--------------------------------------

During your tests you may notice that the fingers are not colliding against each other. This is the default behavior when importing from Onshape. To disable that:

#. Select :code:`/World/Robotiq_2F85`.
#. Check **Self-Collision Enabled** in the Articulation Root Options.

.. Note:: For more details on how to tune the articulation, refer to `Joint Parameter Tuning Example: 2F-85 <https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.3/dev_guide/guides/gripper_tuning_example.html>`_.

Saving Results
==============

After you are satisfied with the configuration, push the changes to the original asset:

#. Open the **Layer** tab. 
#. Select the ``Robotiq_2F_85`` prim, and all children prims in it.
#. Drag the selection into :code:`Robotiq_2F_85_edit.usd`.
#. Click the **Save Layer** button on both Layers.

.. Note:: The fully completed asset is located in the ``Samples/Rigging/Gripper/Robotiq 2F-85_complete`` folder.

Test the Gripper
=================

Now we can test the gripping by lifting the gripper and moving it forward, while closing the gripper to grasp the cylinder.

#. Set the target position for 
    - Joint X to 0.1 in the property panel, by going to the Joint Drive section and setting the target position to 0.1.
    - Joint Z to 0.1 in the property panel, by going to the Joint Drive section and setting the target position to 0.1.
    - Finger joints to -40 degrees in the property panel, by going to the Joint Drive section and setting the target position to -40.

You can see in the video below that the gripper will move forward and lift up.

.. image:: /images/isim_6.0_full_tut_viewport_rig_closed_loop_struct_grasp.webp
    :width: 800

Control the Gripper with OmniGraph
=====================================

We can also use an OmniGraph to control the gripper, by writting the target position of the finger joints directly in the graph.

We have already prepared the graph in the ``Samples/Rigging/Gripper/Robotiq 2F-85/Robotiq_2F_85_complete/Robotiq_2F_75_controller.usd`` file, insert it as a layer to your Robotiq_2F_85_config.usd layer.

#. Open the **Layer** tab. 
#. Select the Insert Sub-Layer layer.
#. Find the ``Robotiq_2F_75_controller.usd`` file in the ``Samples/Rigging/Gripper/Robotiq 2F-85/Robotiq_2F_85_complete`` folder, and click ``Open``.

.. image:: /images/isim_6.0_full_tut_viewport_rig_closed_loop_struct_omnigraph.png
    :width: 800

Explaining the graph:

In this graph, the read upper and lower limit of the finger joints are used to calculate the range of motion of the gripper to map the input signal to the joint target position in degrees. The target position is set to the prim using  ``Write Prim Attribute`` (Write Target) node.

Variables:

    - ``input_signal``: A input signal (float) where 1 means open the gripper and 0 means close the gripper.

Nodes:
    - ``Read Upper Limit`` / ``Read Lower Limit``: A node that reads the upper and lower limit of the finger joint joint.
    - ``Isaac Read Simulation Time``: A node that reads the simulation time, with reset on stop enabled.
    - ``On Playback Tick``: A node that ticks the graph on every frame.
    - ``Write Prim Attribute``: A node that writes the target position to the finger joint prim.

Set the input signal to 0.5 and press the **Play** button to start the simulation. You should see the gripper move forward and lift up.

.. image:: /images/isim_6.0_full_tut_viewport_rig_closed_loop_struct_grasp_ogn.webp
    :width: 800

.. Note:: The fully completed asset is located in the ``Samples/Rigging/Gripper/Robotiq 2F-85_complete`` folder.

Summary
=======

In this tutorial, you experienced a comprehensive workflow for importing assets from a rigged Onshape document, performed post-processing adjustments to enable correct simulation hierarchy, and configured effort drives with Mimic Joints. You conducted validation and troubleshooting to address simulation behavior issues, optimizing performance. Additionally, you utilized layered editing to prepare a ready-to-use asset while retaining a test environment for validating gripper functionality.
