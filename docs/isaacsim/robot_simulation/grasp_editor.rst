.. _isaac_sim_app_tutorial_grasp_editor:

=======================
Grasp Editor
=======================

Learning Objectives
===================

This tutorial explains how to use the `Grasp Editor` extension in |isaac-sim| to hand-author and
simulate grasps for a specific gripper/object pair.  These grasps are stored in an `isaac_grasp`
YAML file that can be imported and used with a motion generation algorithm to move the gripper into
place and grasp the desired object.

Getting Started
===============

To get started using the `Grasp Editor` extension, you need to prepare your assets in |isaac-sim|.

- You must have an `Articulation` capable of grasping.  This can be a floating gripper, or it can be a gripper attached to an arm.
- You must have a USD version of the object you want to grasp.

For both the gripper and the object, you must be ready to identify the USD frame that should be used to
represent location.  This is often the frame in the center of the object mesh and at the base of the gripper.

You can download the stage used in this tutorial
:download:`here <../../content/packages/Grasp_Editor_Tutorial_Stage.zip>`
and follow along.

What is an Isaac Grasp File?
=============================

The output of the `Grasp Editor` extension is a YAML in the `isaac_grasp` file format.  A single `isaac_grasp`
file stores a list of grasps for a specific gripper/object pair.  The file follows a simple format:

.. code-block:: yaml
    :linenos:

    format: isaac_grasp
    format_version: 1.0

    object_frame: /World/mug
    gripper_frame: /World/panda_hand

    grasps:
      grasp_0:
          confidence: 1.0
          position: [-0.04346, 0.06759, 0.19895]
          orientation: {w: 0.00332, xyz: [0.98453, 0.16837, 0.04837]}
          cspace_position:
            panda_finger_joint1: 0.00943
          pregrasp_cspace_position:
            panda_finger_joint1: 0.04

`isaac_grasp` files do not need to originate with the `Grasp Editor` extension.  The `Grasp Editor`
extension is useful for both authoring `isaac_grasp` files and importing grasps that were authored
elsewhere for visualization and validation.

A grasp is defined by the relative position of the gripper and object.  In order for this relative
position to have meaning, a representative frame must be chosen for the gripper and object positions.
The `Grasp Editor` writes the USD paths of these representative frames to an `isaac_grasp` file
under the `object_frame` and `gripper_frame` fields.  Because `isaac_grasp` files may be
authored externally (possibly without going through USD at all), the `Grasp Editor` ignores the
`object_frame` and `gripper_frame` fields when importing grasps.  This makes it the user's
responsibility to identify the correct USD frames when using the `Grasp Editor` for importing.

Each grasp in an `isaac_grasp` file has a unique name (e.g. `grasp_0`).  The fields for a named
grasp are:

- `confidence`: A parameter describing the quality of a grasp.
- `position`: The translation of the gripper frame relative to the object frame.
- `orientation`: The orientation of the gripper frame relative to the object frame.
- `cspace_position`: A dictionary of joint positions for every joint that is used to control the gripper.
  These joint positions are the state of the gripper as it is actively grasping the object.
- `pregrasp_cspace_position`: A dictionary of joint positions for every joint that is used to control the gripper.
  These joint positions represent the open position of the gripper.

All together, a grasp may be applied in practice by moving the gripper to the correct relative position and orientation
while in the `pregrasp_cspace_position`, then closing the gripper until the joints are in `cspace_position`.
If the object's position and orientation in the world frame of reference is given by :math:`T_o, R_o`, with
the `position` and `orientation` fields specifying relative transformation :math:`^oT_g, ^o\!\!R_g`
(i.e. the translation and rotation of the gripper according to the object frame of reference),
the desired position of the gripper in the world frame :math:`T_g , R_g` is given by:

.. math::
    T_g = R_o \cdot {^oT_g + T_o} \\
    R_g = R_o \cdot {^o\!R_g}

Using the Grasp Editor
=======================

Selection Frame
----------------

The `Grasp Editor` is a UI-based extension that can be used to author and import `isaac_grasp` files.
In |isaac-sim|, the `Grasp Editor` can be found in the toolbar under **Tools** > **Robotics** > **Grasp Editor**.
The first step is to add an Articulation and an object to the stage.  The Articulation may be an
isolated gripper, or it may be a gripper attached to a robot arm.  The object can be any
non-Articulation that has an associated mesh.

.. image:: /images/isim_4.5_full_ref_gui_grasp_editor_1.png
    :align: center
    :width: 1200
    :alt: Grasp Editor Selection Frame

In the `Selection Frame`, select the Articulation and object of interest.  The prim path for the object
can be copied by right clicking on the desired prim and selecting "Copy Prim Path".  An export path
must be chosen for the `isaac_grasp` file (this should end in '.yaml').  The `Grasp Editor` may be used
to author a sequence of grasps to the selected export file, but it does not support modifying an existing
file.  If an export path is supplied that already exists, the existing file will be overwritten with
a new `isaac_grasp` file.

This tutorial will author grasps between the Panda hand gripper (isolated from the Franka Emika Panda robot)
and a mug.  When "Ready" is clicked, the Grasp Editor will validate each field and perform all necessary
conversions of the selected object prim (the mug) to make it graspable.  Specifically, it applies the
Rigid Body and Collision APIs from Usd Physics so that the object has a collision geometry and can be moved
by external forces.

.. Note:: The Grasp Editor does not revert these changes to the object asset, and so it is best not to save the USD stage unless these changes are specifically desired.

.. Warning:: There is a known issue that the mug may "dissappear", this is a visual bug. You can press "STOP", then "PLAY" again to make it reappear.

.. _isaac_sim_app_tutorial_grasp_editor_reference_frames:

Select Frames of Reference
---------------------------

In this panel, you may select the frames of reference that should be used to describe the position
in space of the gripper and object.  It is critical to understand this panel and to make the proper
selections before moving on.

Most motion generation algorithms do not natively consume USD files.  It is common for motion generation
algorithms to reference a URDF file.  If the Grasp Editor
uses a frame that is not defined in a corresponding URDF file, an authored grasp becomes meaningless from the
perspective of any such motion generation algorithms.

Similarly, the selected frame of reference for the object
must correspond to the existing pipeline in which the object is being manipulated.  For example, if a
camera is being used to identify object pose, there is an implicit frame of reference for the object
associated with that vision system.  In this case, the selected frame for the object must correspond to this
implicit frame of reference.  If there is not already a frame in the USD that represents the correct frame of
reference, a new one should be authored on the stage under the selected object path (e.g. nested under "/World/mug").

In this tutorial, the base frames for the gripper and object are used.  If the entire Franka Panda robot
were being used, the correct frame of reference for the gripper would still be the `panda_hand` frame.
Once "Finalize" is clicked, these frames of reference become global to the output `isaac_grasp` file and
cannot be changed.

**The Grasp Editor will write the USD paths for the frames of reference to the output isaac_grasp file,
but this information will not be interpretable by a motion generation algorithm that does not consume USD.**

.. image:: /images/isim_4.5_full_ref_gui_grasp_editor_2.png
    :align: center
    :width: 800
    :alt: Select Frames of Reference

Joint Settings
---------------

In this menu, you must select which joints in the Articulation are active degrees of freedom (DOFs) in
the gripper.  The Panda hand is a two finger gripper, but one of the joints is a mimic joint.  Observe
in the figure below that changing the value of `panda_finger_joint1` causes `panda_finger_joint_2` to
move at the same time.  This means that the Panda hand gripper is effectively controlled by a single DOF.

.. image:: /images/isim_4.5_full_ref_gui_grasp_editor_1.gif
    :align: center
    :width: 800
    :alt: Select Active Joints in Robot Gripper

Each active DOF in the gripper should be checked as "Part of Gripper".  This will open a new menu of
joint settings that define how the grasp will be simulated and what gets written to the output `isaac_grasp` file.

- Position When Open: The position of DOF that is considered to be open.  Each grasp will be simulated
  by moving from the open position towards the closed position.
- Position When Closed: The position of the DOF that is considered to be fully closed.
- Grasp Speed: The speed at which the DOF will move from the open position towards the closed position when simulating.
- Max Effort Magnitude: The maximum force/torque (N or N*m) that this DOF will be able to apply on the object when simulating.

At least one DOF must be marked as part of the Gripper in order to author a grasp.  Only active gripper DOFs will
be written to the output `isaac_grasp` file.

Utils
-----

The Utils menu has two useful utility functions that assist in using the Grasp Editor.

The Mask Collision button will mask collisions between the gripper and object.  This may be helpful
when moving the object into place in order to test a grasp.  Masked collisions are unmasked when a grasp
is simulated.  When importing a grasp, collisions are masked automatically.

.. image:: /images/isim_4.5_full_ref_gui_grasp_editor_2.gif
    :align: center
    :width: 800
    :alt: Masking Collisions

If the simulated grasp does not appear to have complete contact between the object and gripper,
you can use the "Show Physics Colliders" button to visualize the collision geometry associated
with your assets.  It is outside of the scope of this extension to fix incorrect collider geometry,
but the Grasp Editor does allow you to author grasps without simulating them. In this situation
you can mask collisions and move things into place visually.

.. image:: /images/isim_4.5_full_ref_gui_grasp_editor_3.png
    :align: center
    :width: 800
    :alt: Visualizing Physics Colliders

Author a Grasp
--------------

A grasp may be authored with the aid of simulation.  Moving assets by hand into what appears to be the right
position is imprecise.  In the figure below, the mug is moved into roughly the right position to
be grasped, and the "Simulate" button is clicked to close the gripper according to its joint settings.
This causes the lip of the mug to be pushed into the exact center of the gripper fingers, and it
leaves the gripper fingers in the exact position of contact with the object.  This gives a high
degree of confidence to the grasp that is written to the output file. Once the simulation is complete,
the export panel will populate, and the grasp may be written to file.

.. image:: /images/isim_4.5_full_ref_gui_grasp_editor_3.gif
    :align: center
    :width: 800
    :alt: Simulating a Grasp

There may be reasons that the grasp simulation does not support your use-case such as:

- The physics colliders for your assets are not accurate.
- The mechanics for opening and closing the gripper are more complicated than is represented in the Grasp Editor.

In either case, the best way to make use of the `Grasp Editor` is to move things into place through
external means and export the grasp without simulating by clicking the "Skip Sim" button.  For example,
some real robot grippers have heavily coupled degrees of freedom with somewhat complicated mechanics.
For such a gripper, you would want to replicate the exact movement programmatically and send joint
commands to the USD asset accordingly.  In this case, you could turn on collisions and use an external
script or OmniGraph node to drive your gripper into a grasping position, then use the export function of the
`Grasp Editor` to export the current state of grasp on the USD stage to your `isaac_grasp` file.


Adding External Forces and Torques
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An extra feature of the `Grasp Editor` is that you can apply external forces and torques as part of the
grasp simulation.  This may help to discern which grasps have the best force closure over the object.
The amount of force and torque applied may be selected in the "Add External Rigid Body Forces" panel.
A single scalar value may be chosen for force and for torque.  A non-zero value :math:`v` for force will cause
a force of :math:`\pm v` N along each axis, centered at the base frame of the rigid body.
Likewise for torque, a value :math:`v` will cause a torque of :math:`\pm v` N*m to be applied about each axis, centered
at the base frame of the rigid body.

The figure below demonstrates closing the grasp and then applying forces of `3` N.  This test fails
when the mug flies away under a force of :math:`[3, 0, 0]`.  A smaller force value of `0.5` N is then
chosen, and the mug moves under the force, but the grasp is maintained.

.. image:: /images/isim_4.5_full_ref_gui_grasp_editor_4.gif
    :align: center
    :width: 800
    :alt: Simulating a Grasp

Exporting Grasps
-----------------

The export frame becomes available once a grasp has been fully simulated, or the option to simulate has been declined.
On clicking "Export", the current state of the stage is used to fill in the relevant fields of the
`isaac_grasp` file.

- The `confidence` field takes on the value of the "Confidence" field in the Export panel.
- The `position` and `orientation` fields for the grasp are determined by finding the relative position
  of the gripper in the object's frame of reference.  This uses the frames defined in
  :ref:`isaac_sim_app_tutorial_grasp_editor_reference_frames`.
- The `cspace_position` field is determined based on the current positions of the DOFs that have been marked as
  part of the gripper.
- The `pregrasp_cspace_position` field is taken from the "Position When Open" field of Joint Settings for each
  DOF that has been marked as part of the gripper.

At this stage, multiple grasps may be authored in a row and sequentially exported to the same `isaac_grasp` file.

.. image:: /images/isim_4.5_full_ref_gui_grasp_editor_4.png
    :align: center
    :width: 800
    :alt: Visualizing Physics Colliders

.. _isaac_sim_app_tutorial_grasp_editor_import:

Importing Grasps
-----------------

Apart from authoring grasps, the `Grasp Editor` may be used to validate grasps that were authored
elsewhere.  This can be done in the Import panel by selecting an `isaac_grasp` file and clicking Import.
This tutorial uses the same file that is used for export, but this does not need to be the case.

In the figure below, multiple grasps have been authored and written to file using the `Grasp Editor`.
These grasps are imported, and can now be quickly visualized and simulated in sequence.

.. image:: /images/isim_4.5_full_ref_gui_grasp_editor_5.gif
    :align: center
    :width: 800
    :alt: Visualizing Physics Colliders

Using Authored Grasps in Isaac Sim
===================================

The `Grasp Editor` is primarily a UI-based extension, but it offers some utility for importing and
using authored grasps within |isaac-sim| through a Python API.

This section presents the following stage with the goal of determining where the robot should go
to execute one of the authored grasps.

.. image:: /images/isim_4.5_full_ref_gui_grasp_editor_6.png
    :align: center
    :width: 400
    :alt: Grasping Scenario

The following code snippet imports the grasp file demonstrated in :ref:`isaac_sim_app_tutorial_grasp_editor_import` and
determines where the `panda_hand` frame should be in order to duplicate `grasp_1`.

.. literalinclude:: ../snippets/robot_simulation/grasp_editor/using_authored_grasps_in_isaac_sim.py
    :language: python

.. code-block:: console

    Grasp Names: ['grasp_0', 'grasp_1', 'grasp_2']
    Gripper Translation Target: [ 0.41496072 -0.03612298  0.27738899]
    Gripper Orientation Target: [-0.1690746   0.63886658  0.12752551  0.73959483]

The result of the code snippet shows the name of each grasp in the `isaac_grasp` file, and
the translation and orientation targets that should be set for the
`panda_hand` frame in the full Franka robot.  Note that the code snippet uses the frame of reference
for the mug that was selected in the `Grasp Editor`. It is outside of the scope of this tutorial to
use a motion generation algorithm to achieve this grasp.

Check out the `GraspSpec` class in our |link_ext| to see the complete set of functionality.

.. |link_ext| raw:: html

   <a href="../py/source/extensions/isaacsim.robot_setup.grasp_editor/docs/index.html" target="_blank">API Documentation</a>


