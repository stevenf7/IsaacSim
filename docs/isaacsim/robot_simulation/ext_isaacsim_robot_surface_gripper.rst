..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_surface_grippers:

===============================
Surface Gripper Extension
===============================

.. |transform_ico| image::  /images/isaac_transform_gizmo.png

.. _isaac_surface_grippers_about:

About
=================

The :ref:`isaac_surface_grippers` Extension is used to create a suction-cup gripper behavior for an end-effector. It works by parsing the Surface Gripper properties on the USD Surface Gripper Schema, and managing a set of D6 Joints between the parent and child rigid bodies at the gripper points of contact.

The physical properties of the gripper are defined on the D6 Joints properties, such as joint limits across the different degrees of freedom, and the stiffness and damping of the joint. The Surface gripper Object then handles the activation of the constraints, and define which objects to be grasped based on the grip threshold.

This extension is enabled by default. If it is ever disabled, it can be re-enabled from the :doc:`Extension Manager <extensions:ext_core/ext_extension-manager>` by searching for ``isaacsim.robot.surface_gripper``.

To create a surface gripper through the GUI, Go to the menu ``Create`` > ``Robots`` > ``Surface Gripper``. This will create a surface gripper prim in the stage.

.. _isaac_surface_grippers_api_doc:

API Documentation
=================

See the `API Documentation <../py/source/extensions/isaacsim.robot.surface_gripper/docs/index.html>`_ for usage information.

.. _isaac_surface_grippers_tutorials:



Setting up a Surface Gripper
============================

The Surface Gripper Has the following properties:

============================= ====================================================================
Property                      Description
============================= ====================================================================
Attachment Points             | The list of Joints that will be used to attach the gripper to the object
Status                        | (Read-Only) The current state of the gripper
Gripped Objects               | (Read-Only) The list of objects that are currently grasped by the gripper
Max Grip Distance             | Distance from the gripper point that will accept closing contact
Retry Interval                | How long the gripper will remain attempting to close on an object
Shear Force Limit             | The maximum lateral force that the gripper can apply to an object before it will break the constraint
Coaxial Force Limit           | The maximum axial force that the gripper can apply to an object before it will break the constraint
============================= ====================================================================



Attachment Joints
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The joints that will be used to attach the gripper to the object are defined on the ``Attachment Points`` property. This is a list of paths to the D6 Joints that will be used to attach the gripper to the object. These joints must be defined on the USD file at the gripper points of contact, and must be of type ``D6``. Any physical properties for the joint are defined on the D6 Joint Schema, but there are a few properties that are required to be set for the Joint:

- Joint must be enabled
- All joints Body 0 must be the same.
- Joint must have "Exclude from Articulation" set to True. If this is not set, the surface gripper manager will set it to True at runtime.

Attachment Point API
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The joints that are defined on the ``Attachment Points`` property are automatically assigned the ``Attachment API``. This API is responsible for providing additional attributes to the joint, which are necessary for the Surface Gripper Manager to handle the gripper. In the attachment point API, the following attributes are available:

- ClearanceOffset: This registers the distance from the joint to the parent object's surface. Since the surface gripper works by sending a raycast from the joint world position, this offset will be added to the raycast origin to avoid false positive hits with the parent object. If this offset is not defined, it will start at the joint's world position, and whenever it clears the parent object collider, it will author the offset at runtime for future use.
- Forward Axis: This registers which joint axis will be used to attempt to close the gripper. The default value is ``X``.

Adding Attachment Joint API
-----------------------------

To add an attachment joint API, select the joint in the stage, and in the right panel under the `Properties` tab, check the `+ Add` button,  and select ``Edit API Schema``. Search for `AttachmentPointAPI` and apply it to the joint.

.. image:: ../images/isim_5.0_base_ref_gui_robot_schema_add.png
   :width: 150px
   :align: center


Tutorials & Examples
=====================

Activate the ``Robotics Examples`` content browser from **Windows** > **Examples** > **Robotics Examples**. Navigate to **Manipulation**, select the Surface Gripper Example, and click the load button in the information window on the right side of the Robotics Examples content browser.  You may need to adjust the GUI to see the load button.


Surface Gripper Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This example shows a Surface gripper mounted to a gantry, and contains cubes that can be grasped by the gripper. This Surface gripper is Added by code, and also connected throug the surface gripper |omnigraph| node.

To run the Example:

#. Press the **Load** button.  The scene should begin playing.
#. You can move the Gantry with the gamepad axis, or by manually editing the gantry joint target positions.
#. Move the gantry near some cube or set of cubes, and click on the "Open/Close" Button - the button label reflects the current gripper state. The gripper can also be closed by the down face button on the gamepad (e.g X on playstation controllers, or A on Xbox controllers).
#. The gripper will attempt to close on the cubes, and if successful, the cubes will be grasped by the gripper.
#. Lift the gantry, and the cubes will remain grasped by the gripper, or forces may be excessive and break the gripper constraint.


.. image:: ../images/isim_5.0_base_ref_gui_surface_gripper_example.png

.. _isaac_surface_grippers_omnigraph:

|omnigraph| Node
=================

The Surface Gripper extension provides a implementation through |omnigraph|. To use it, Add a surface gripper node to the desired graph, and select the Surface gripper prim it will control.


.. _isaac_surface_grippers_code_snippets:

Creating a Surface Gripper fully on code
=========================================

This section describes how to implement a surface gripper completely from code. These are snippets from the Surface Gripper Example code, and is not complete.


Defining the Surface Gripper Properties
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/robot_simulation/ext_isaacsim_robot_surface_gripper/defining_the_surface_gripper_properties.py
    :language: python

Get Gripper State
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Surface Gripper is updated on every simulation step, and the state can be retrieved at any time through the interface:

.. literalinclude:: ../snippets/robot_simulation/ext_isaacsim_robot_surface_gripper/get_gripper_state.py
    :language: python

Controlling the Gripper
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Gripper State is controlled through the ``open`` and ``close`` methods of the interface. Alternativel, there's also the ``set_gripper_action``, which receives a numeric value between -1 and 1, where ``< -0.3`` will open the gripper, ``> 0.3`` will close it, and anything in between will be ignored.

.. literalinclude:: ../snippets/robot_simulation/ext_isaacsim_robot_surface_gripper/controlling_the_gripper.py
    :language: python
    :linenos:

Keeping USD Scene in Sync
^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to optimize the Surface Gripper Update performance, the USD Scene update is disabled by default. When the USD writeback is disabled, the Properties panel for the Surface Gripper prim will not be updated automatically. The surface gripper status can still be retrieved through `get_gripper_status` method of the surface gripper interface, and objects currently grasped by the gripper can be retrieved through `get_gripped_objects` method of the surface gripper interface.

 The USD writeback can be enabled by setting the ``set_write_to_usd`` property to ``True`` on the Surface Gripper interface. This is a global setting for all surface gripper instances.
