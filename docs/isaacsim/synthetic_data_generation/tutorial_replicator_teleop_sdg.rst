..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_replicator_teleop_sdg:

==========================================
Teleoperation Synthetic Data Generation
==========================================

.. note::

   Work in progress. Provides a brief description of the teleop features for testing.

This tutorial covers the ``isaacsim.replicator.teleop`` and ``isaacsim.replicator.teleop.ui`` extensions. Together they let an operator teleoperate robot arms, grippers, floating end effectors, and mobile bases inside |isaac-sim_short| using VR controllers.

The UI window is opened from **Tools** > **Replicator** > **Teleop**.

There are two ways to run teleop, depending on whether you want the VR headset
to display the simulated viewport or prefer to work from a normal 2D monitor.


Running modes
--------------

**2D monitor (controller tracking only)** --- Launch |isaac-sim_short| with the
standard application. The desktop viewport shows the scene on a flat screen
while the VR headset and controllers are used only for pose tracking via
CloudXR. This is the default mode and requires no special app configuration:

.. code-block:: bash

   ./isaac-sim.sh

**VR headset (stereo rendering)** --- Launch |isaac-sim_short| with the XR VR
experience app (``isaacsim.exp.base.xr.vr.kit``). In this mode the headset
receives a stereo-rendered viewport of the scene, giving the operator a
first-person 3D view inside the simulation. The headset also provides an
in-headset UI to start and stop the simulation, which is equivalent to pressing
**Play** / **Stop** on the desktop timeline. The desktop window stays available
for UI interaction:

.. code-block:: bash

   ./isaac-sim.xr.vr.sh

Both modes include the Teleop UI extension and support the same controller,
grasp, and locomotion features described in this tutorial.

All controllers (Floating, IK, Grasp, Locomotion) are only active while the
timeline is playing. They deactivate automatically when the timeline stops.


Prerequisites
-------------

*   |isaac-sim_short| built and launchable.
*   `Isaac Teleop <https://github.com/NVIDIA/IsaacTeleop>`_ installed --- follow the `install instructions <https://nvidia.github.io/IsaacTeleop/main/getting_started/quick_start.html#install-the-isaacteleop-pip-package>`_.
*   CloudXR server started and headset connected --- follow the `CloudXR server guide <https://nvidia.github.io/IsaacTeleop/main/getting_started/quick_start.html#run-cloudxr-server>`_.
*   A stage with a robot (e.g. a UR3e arm with a gripper on a mobile base).

Start Isaac Teleop CloudXR in another terminal before connecting from the Teleop window:

.. code-block:: bash

   python -m isaacteleop.cloudxr

Keep that process running while using teleop. Then open the hosted
`Isaac Teleop Web Client <https://nvidia.github.io/IsaacTeleop/client/>`_ from the headset browser
and follow the current connection steps in the
`Isaac Teleop Quick Start <https://nvidia.github.io/IsaacTeleop/main/getting_started/quick_start.html>`_.
Connect from Isaac Sim after the CloudXR runtime is running and the headset client is connected.

.. note::

   The prerequisites above apply to VR-connected testing (both 2D and stereo
   modes). Debug mode testing requires only |isaac-sim_short| --- no headset,
   CloudXR, or Isaac Teleop installation is needed. See
   :ref:`Testing the extension (debug mode) <isaac_sim_app_tutorial_replicator_teleop_sdg_debug>`.


Overview
--------

The extension has two layers:

*   ``isaacsim.replicator.teleop`` --- runtime that handles VR input, frame markers, and four controllers (Floating, IK, Grasp, Locomotion).
*   ``isaacsim.replicator.teleop.ui`` --- UI window with six collapsible panels (Profiles, Session, Floating, IK, Grasp, Locomotion) that configure and drive the runtime.

Every controller follows the same lifecycle: **Apply** validates the prim path,
**Enable** arms the controller for the next Play, and **Clear** tears down
resources while keeping the prim path for quick reconfiguration.
All tuning controls (gains, rotation offsets, speed sliders) are live-editable
during Play and persist across sessions. Values can be saved to a teleop profile
YAML for sharing or version control.


.. _isaac_sim_app_tutorial_replicator_teleop_ui:

UI reference
------------

The Teleop window contains six collapsible panels, described here from top to
bottom. Open the window from **Tools** > **Replicator** > **Teleop**.


.. _isaac_sim_app_tutorial_replicator_teleop_ui_profiles:

1. Profiles
^^^^^^^^^^^

The **Profiles** panel saves and restores the complete state of every other
panel as a single YAML file.

*   **Dir** --- working directory for teleop profile files. Defaults to the
    built-in profiles shipped with the extension. Click the folder icon to
    browse for a custom directory.
*   **Profile dropdown** --- lists all ``.yaml`` files found in the working
    directory.
*   **Load** --- reads the selected profile and applies it to all panels. If the
    stage contains the referenced prims, controllers are resolved immediately;
    otherwise the UI fields are populated and unresolved paths are reported.
*   **Save** --- opens an inline **Name** field and **Confirm** button. Enter a
    filename (without ``.yaml``) and click **Confirm** to write the current
    panel state to disk. If a file with that name already exists, click
    **Confirm** a second time to overwrite.
*   **Validate** --- checks all panel settings against the current stage and
    reports error and warning counts in the status line. Detailed issues are
    printed to the console.
*   **Delete** (trash icon) --- permanently removes the selected profile file
    from disk.


.. _isaac_sim_app_tutorial_replicator_teleop_ui_session:

2. Session
^^^^^^^^^^

The **Session** panel manages VR connection, frame markers, coordinate
conversion, tracking-space origin, the XR headset anchor, and the debug
controls.

Connection
###########

*   **Connect** / **Disconnect** --- establishes or tears down the OpenXR
    connection to the Isaac Teleop CloudXR session.
*   **Status** --- displays the current connection state: red
    (**Disconnected**), green (**Connected**), or yellow (intermediate states
    such as **No data**).

Frame Markers
##############

*   **Show** --- creates four frame-axis markers under
    ``/Teleop/Markers/TrackingOrigin`` (origin, Left, Right, Head) and begins
    streaming VR poses to them.
*   **Remove** --- deletes all markers and stops tracking.
*   **Scale** --- adjusts the visual axis length of every marker.

Tracking Space / Custom Origin
###############################

*   **Coordinate Frame** --- selects how incoming VR poses are converted:

    *   **Isaac Sim (Z-up)** --- applies a Y-up to Z-up rotation so poses
        match the |isaac-sim_short| stage convention. This is the default.
    *   **Raw (no conversion)** --- passes poses through unchanged.

*   **Custom Origin** --- optional prim path to use as the tracking-space
    origin. Leave empty to use the built-in origin marker under
    ``/Teleop/Markers/``. Paths under the reserved ``/Teleop/Markers/``
    namespace are rejected. Click the **Apply** button next to the field to
    validate.
*   **Enable** / **Disable** --- activates or deactivates tracking-space
    following after the path has been applied.

XR Anchor (Headset)
####################

These controls position and orient the VR headset camera relative to the
tracking-space prim. They are relevant when using stereo VR rendering.

*   **Offset X / Y / Z** --- position offset in metres. Without a Tracking
    Space prim this is an absolute world position; with one it is relative to
    that prim.
*   **Rotation** --- how the headset camera yaw tracks the Tracking Space prim:

    *   **Fixed** --- ignore prim rotation entirely.
    *   **Follow Prim** --- yaw tracks the prim (roll and pitch are stripped).
    *   **Follow (Smoothed)** --- same as Follow Prim but with slerp damping.

*   **Smooth** --- slerp time constant in seconds (only used in **Smoothed**
    mode). Lower values give snappier tracking; higher values are smoother.
*   **Fixed Height** --- locks the headset camera Z to its initial value,
    preventing vertical bobbing when the Tracking Space prim moves up or down.

Debug
######

Debug mode replaces VR controller input with draggable USD markers and
on-screen sliders, enabling full testing of every controller without VR
hardware. See :ref:`debug mode testing <isaac_sim_app_tutorial_replicator_teleop_sdg_debug>`
for step-by-step procedures.

*   **Write Backend** --- overrides the global ``XformPrim`` backend used for
    all teleop writes. Options: **USD** (plain attribute writes), **USD-RT**
    (Fabric hierarchy), **Fabric** (fastest path, requires FSD).
*   **Debug Tracking** checkbox --- enables synthetic pose input. Mutually
    exclusive with a live VR connection: disconnect first or disable debug
    tracking before connecting.
*   **L Grasp** / **R Grasp** --- sliders (0--1) that simulate VR trigger
    squeeze. Feed directly into the Grasp controller as ``trigger_value``.
*   **Slide X** / **Slide Y** --- sliders (-1 to 1) that simulate the left
    thumbstick for Locomotion lateral and forward/backward slide.
*   **Turn** --- slider (-1 to 1) that simulates the right thumbstick for
    Locomotion yaw.
*   **Up** / **Down** --- hold-buttons that simulate the right-side face
    buttons for vertical motion.
*   **Carry Origin** --- toggle-button that simulates the left primary face
    button, toggling Carry Tracking Space mode in the Locomotion controller.


.. _isaac_sim_app_tutorial_replicator_teleop_ui_floating:

3. Floating Controller
^^^^^^^^^^^^^^^^^^^^^^

The **Floating Controller** drives a free rigid body so that it tracks the VR
controller pose using velocity-based PD control. Use it for end effectors or
grippers that are not part of an articulation chain. Each side (Left / Right)
has its own collapsible sub-panel.

The target prim must be a rigid body. If you want to control an articulated
gripper with the Floating controller, attach the articulation root joint to a
rigid body and point the Floating controller at that rigid body. The gripper
articulation is then carried along as a child, while the Grasp controller
independently drives its finger joints.

*   **Prim Path** --- the rigid body prim to drive. Click **Apply** (check-mark
    button) to validate. The path field, plus-button (pick from viewport), and
    delete-button (clear selection) are locked once configured; click **Clear**
    to reconfigure.
*   **Target Rot X / Y / Z** --- per-axis local rotation offset in 90-degree
    increments (-180, -90, 0, +90, +180). Different grippers and end effectors
    have different local-frame conventions; these offsets let you align the
    controlled body so that its forward axis matches the VR controller pointing
    direction. For example, a gripper whose local Z points sideways instead of
    forward can be corrected with a 90-degree Y offset. All three axes can be
    adjusted at runtime during Play and are saved in teleop profiles.
*   **Pos Kp / Kd** --- position proportional and derivative gains. Higher
    **Kp** makes the body snap to the target faster; **Kd** damps oscillations.
*   **Rot Kp / Kd** --- orientation proportional and derivative gains. Same
    principle as position gains, applied to rotational tracking.
*   **Enable** / **Disable** --- arms or disarms the controller for the next
    Play. Status transitions: *Configured* -> *Standby* -> *Active* (on Play).
*   **Clear** --- destroys controller resources while keeping the prim path.


.. _isaac_sim_app_tutorial_replicator_teleop_ui_ik:

4. IK Controller
^^^^^^^^^^^^^^^^

The **IK Controller** drives an articulated robot arm via inverse kinematics so
that its end effector tracks the VR controller pose. Each side (Left / Right)
has its own collapsible sub-panel.

The target prim must be an articulation. The IK solver operates on the joint
chain from the articulation root down to the selected end-effector link. For a
typical setup --- e.g. a UR3e arm with a gripper attached --- select the wrist
link as the end effector so that IK solves only for the arm joints. The gripper
joints are then driven separately by the Grasp controller.

Articulation and end effector
##############################

*   **Prim Path** --- the articulation root prim. Click **Apply** to validate.
    On success the end-effector dropdown is populated with all body links in the
    kinematic chain.
*   **EE Link** --- selects which link in the chain is the IK target. Choose
    the last arm link (e.g. the wrist) to exclude gripper joints from the IK
    solve. The last link in the chain is selected by default.
*   **Clear** --- destroys the solver and articulation resources (prim path is
    preserved for quick reconfiguration).

Solver selection
#################

*   **Solver** dropdown --- chooses the IK backend. Each solver can be
    hot-swapped during Play without stopping the timeline:

    .. list-table::
       :header-rows: 1
       :widths: 20 80

       * - Solver
         - Description
       * - **Position-based**
         - Single-step Jacobian differential IK. Supports a configurable
           **Method** dropdown.
       * - **Velocity-based**
         - Velocity-space IK with a proportional **Gain** slider that controls
           tracking aggressiveness. Also supports a **Method** dropdown.
       * - **Levenberg-Marquardt**
         - Multi-iteration damped least-squares per frame. No method or gain
           controls.
       * - **PINK**
         - Task-based QP IK using a Pinocchio backend with joint-limit
           enforcement and posture regularisation. Exposes additional tuning
           described below.

*   **Method** dropdown --- visible only for Position-based and Velocity-based
    solvers. Selects the Jacobian inversion strategy:

    *   **Damped LS** --- most stable default; handles singularities well.
    *   **Pseudoinverse** --- direct tracking when well-conditioned; less stable
        near singularities.
    *   **Transpose** --- cheapest update; can be gain-sensitive.
    *   **SVD** --- robust singular-value filtering; typically heaviest compute.

Rotation offset and tuning
###########################

*   **EE Rot X / Y / Z** --- per-axis local rotation offset in 90-degree
    increments (-180, -90, 0, +90, +180). Purpose is the same as for the
    Floating controller: different robot end effectors have different
    local-frame orientations, and these offsets align the IK target so the
    robot's tool tip or gripper faces the same direction as the VR controller.
    Adjustable at runtime and saved in profiles.
*   **VR Target Filter** --- exponential moving average (EMA) low-pass filter
    on the incoming VR target pose. Range 0.0--0.95. Higher values reduce
    jitter but add delay. Default 0.0 (no filtering).
*   **Max Joint Step** --- safety clamp on the maximum joint-angle change per
    simulation step (radians). Prevents sudden joint jumps without acting as a
    true velocity limit. Default 0.0 (disabled).
*   **Gain** --- (Velocity-based solver only) proportional gain controlling
    how aggressively the end effector tracks the VR target. Values of 1--5 give
    smooth conservative tracking; 10--20 are fast; above 30 may oscillate.

PINK-specific tuning
#####################

These controls appear only when the **PINK** solver is selected:

*   **Task Gain** --- PINK FrameTask response gain. Higher values make tracking
    more aggressive; lower values soften it.
*   **Posture** --- posture regularisation cost. Higher values keep the arm
    closer to its current pose; lower values give the end-effector task more
    freedom.
*   **QP** dropdown --- quadratic-program solver backend. Use to compare solve
    quality and performance across backends.
*   **LM Damp** --- FrameTask Levenberg-Marquardt damping. Higher values
    improve stability in difficult configurations but slow response.

Enable / Disable
#################

*   **Enable** / **Disable** --- arms or disarms the IK controller for the next
    Play. During Play the status shows **Active** when the target is reachable
    and **Out of reach** when the VR target leaves the arm's workspace.
    Tracking resumes automatically when the target returns to a reachable pose.


.. _isaac_sim_app_tutorial_replicator_teleop_ui_grasp:

5. Grasp Controller
^^^^^^^^^^^^^^^^^^^

The **Grasp Controller** maps the VR trigger's analog value (0 = open, 1 =
fully closed) to gripper joint drive targets. Because grippers vary widely ---
a simple parallel-jaw gripper has a single drive joint, while a multi-finger
hand can have a dozen joints across several fingers --- the controller relies on
a YAML config file that defines the mapping from the linear 0--1 trigger value
to each joint's target position.

Each config file lists the joints to drive, the input range, and the
corresponding target range in degrees. Users can author custom config files to
support their own grippers or to define alternative grasp styles on the same
hand --- for example, a pinch grasp vs. a full-palm grasp on a five-finger
hand.

**Simple gripper** --- ``xarm_grasp.yaml`` maps a single drive joint:

.. code-block:: yaml

   joints:
     - name: "drive_joint"
       input_range: [0.0, 1.0]
       target_range: [0.0, 48.0]

**Multi-finger hand** --- ``dex3_grasp.yaml`` maps seven joints across three
fingers, each with its own target range:

.. code-block:: yaml

   joints:
     - name: "right_hand_index_0_joint"
       input_range: [0.0, 1.0]
       target_range: [0.0, 90.0]
     - name: "right_hand_index_1_joint"
       input_range: [0.0, 1.0]
       target_range: [0.0, 80.0]
     - name: "right_hand_middle_0_joint"
       input_range: [0.0, 1.0]
       target_range: [0.0, 90.0]
     - name: "right_hand_middle_1_joint"
       input_range: [0.0, 1.0]
       target_range: [0.0, 80.0]
     - name: "right_hand_thumb_0_joint"
       input_range: [0.0, 1.0]
       target_range: [0.0, 0.0]
     - name: "right_hand_thumb_1_joint"
       input_range: [0.0, 1.0]
       target_range: [0.0, -60.0]
     - name: "right_hand_thumb_2_joint"
       input_range: [0.0, 1.0]
       target_range: [0.0, -60.0]

Each side (Left / Right) has its own collapsible sub-panel with independent
configuration.

*   **Prim Path** --- the gripper articulation prim. Click **Apply** to validate
    the path and load the config simultaneously. The field is locked after
    configuration; click **Clear** to reconfigure.
*   **Config** dropdown --- selects a built-in grasp configuration shipped with
    the extension. Selecting an entry immediately updates the **Config path**
    field below.
*   **Config path** --- full path or ``builtin://`` URI to a grasp config YAML.
    You can type a custom path pointing to your own config file for a custom
    gripper or a custom grasp style.
*   **Enable** / **Disable** --- arms or disarms trigger tracking for this side.
*   **Clear** --- destroys grasp resources while keeping paths for quick
    reconfiguration.

During Play, trigger pressure is read from the VR controller or from the
**L Grasp** / **R Grasp** debug sliders. For each joint listed in the config,
the controller interpolates linearly between the open and closed target values
based on the current trigger value.


.. _isaac_sim_app_tutorial_replicator_teleop_ui_locomotion:

6. Locomotion
^^^^^^^^^^^^^

The **Locomotion** controller moves a prim kinematically using VR thumbstick
and face-button input. Horizontal movement is projected onto the world ground
plane using the prim's heading, so axes remain correct regardless of the
target prim's local frame orientation. Two workflows are supported:

*   **Robot base** --- set the prim path to a robot base link. Thumbstick
    input moves the robot, and attached arms and grippers follow. Toggle
    *Carry Tracking Space* (left primary button) to co-move the VR origin
    with the robot.
*   **VR origin** --- set the prim path to the built-in tracking-space origin
    marker (``/Teleop/Markers/TrackingOrigin``). Carry is implicit because the
    locomotion prim *is* the VR origin. Use this for floating grippers that
    have no physical base.

Controls:

*   **Prim Path** --- the prim to move. Click **Apply** to validate.
*   **Slide Speed** --- speed multiplier for thumbstick translation (forward,
    backward, lateral) and face-button vertical motion.
*   **Turn Speed** --- speed multiplier for right-thumbstick yaw rotation.
*   **Enable** / **Disable** --- arms or disarms locomotion for the next Play.
*   **Clear** --- destroys the configured state while keeping the prim path.

During Play the controller reads the following VR inputs:

*   **Left thumbstick** --- forward/backward (Y) and left/right (X) slide in
    the world ground plane.
*   **Right thumbstick** --- left/right yaw turn.
*   **Right face buttons** --- ``A`` (primary) moves down, ``B`` (secondary)
    moves up along world Z (Meta-style controller layout).
*   **Left primary face button** (``X`` on Meta-style controllers) --- toggles
    **Carry Tracking Space** mode. When active, locomotion also moves the
    Session panel's Tracking Space prim with the base, including turn rotation
    around the base pivot. When the locomotion prim *is* the tracking-space
    origin, carry is implicit and the toggle has no additional effect.


.. _isaac_sim_app_tutorial_replicator_teleop_profiles:

Teleop profiles
----------------

A teleop profile is a single YAML file that captures the complete state of every
panel in the Teleop window. Use the **Profiles** panel at the top of the Teleop
window to save, load, and delete profiles.

Built-in profiles ship with the extension under
``source/extensions/isaacsim.replicator.teleop/data/teleop_profiles/``.
You can point the **Dir** field in the **Profiles** panel to a custom
folder to manage your own profiles alongside the built-in ones.

Built-in profiles
^^^^^^^^^^^^^^^^^^

The extension ships two built-in profiles that demonstrate both locomotion
workflows.

Floating grippers (VR origin locomotion)
#########################################

``floating_xarm_dex3.yaml`` configures a dual floating-gripper setup. The
Floating controller drives each gripper as a free rigid body, and Locomotion
targets the VR origin marker so that thumbstick input repositions the entire
VR workspace.

**Session** --- global settings that apply before any controller is configured:

.. code-block:: yaml

   session:
     coordinate_system: isaac_sim       # Z-up coordinate conversion
     tracking_space_enabled: false
     tracking_space_path: ''            # empty = built-in origin marker
     marker_scale: 0.05
     anchor_x: 0.0
     anchor_y: 0.0
     anchor_z: 0.0
     anchor_rotation_mode: fixed
     anchor_smoothing: 1.0
     anchor_fixed_height: true

**Floating** --- per-side rigid body controller with PD gains and rotation
offsets. Both sides are enabled, each pointing at a different gripper root prim:

.. code-block:: yaml

   floating:
     left:
       enabled: true
       settings:
         prim_path: /World/teleop_xarm_dex3/.../xarm_gripper_rigid_root
         pos_kp: 20.0
         pos_kd: 0.5
         orient_kp: 20.0
         orient_kd: 0.2
         target_rot_x_deg: 180
         target_rot_y_deg: 0
         target_rot_z_deg: 90
     right:
       enabled: true
       settings:
         prim_path: /World/teleop_xarm_dex3/.../dex3_1_r_rigid_root
         pos_kp: 20.0
         pos_kd: 0.5
         orient_kp: 20.0
         orient_kd: 0.2
         target_rot_x_deg: -90
         target_rot_y_deg: 0
         target_rot_z_deg: 90

**IK** --- neither side is enabled in this profile because the grippers are
floating rigid bodies rather than articulations. The section is still present
with defaults so that loading the profile resets any prior IK configuration.

**Grasp** --- maps each side to a gripper articulation prim and a built-in
grasp config. ``builtin://`` paths resolve to YAML files shipped with the
extension:

.. code-block:: yaml

   grasp:
     left:
       enabled: true
       prim_path: /World/teleop_xarm_dex3/.../xarm_gripper
       config_path: builtin://xarm_grasp
     right:
       enabled: true
       prim_path: /World/teleop_xarm_dex3/.../dex3_1_r
       config_path: builtin://dex3_grasp

**Locomotion** --- drives the built-in tracking-space origin so that thumbstick
input moves the entire teleop workspace (VR origin workflow):

.. code-block:: yaml

   locomotion:
     enabled: true
     settings:
       prim_path: /Teleop/Markers/TrackingOrigin
       linear_speed: 0.2
       angular_speed: 0.2


Dual-arm IK (robot-base locomotion)
#####################################

``dual_ur3_xarm_dex3.yaml`` configures a dual UR3e arm setup where each arm
is driven by the PINK IK solver. Locomotion targets the robot's root prim so
that thumbstick input moves the entire robot base.

**IK** --- both sides are enabled with the PINK solver. Each side points at a
different UR3e arm within the dual-arm assembly. The ``ee_rot_*`` offsets align
each end effector's local frame with the VR controller pointing direction:

.. code-block:: yaml

   ik:
     left:
       enabled: true
       settings:
         robot_path: /World/teleop_dual_ur3_xarm_dex3/dual_arm/left_arm_ur3e_xarm/ur3e
         ee_link: wrist_3_link
         solver: pink
         gain: 5.0
         pink_qp_solver: osqp
         pink_task_gain: 0.5
         pink_posture_cost: 0.001
         pink_lm_damping: 1.0
         ee_rot_x_deg: 180
         ee_rot_y_deg: 0
         ee_rot_z_deg: -90
     right:
       enabled: true
       settings:
         robot_path: /World/teleop_dual_ur3_xarm_dex3/dual_arm/right_arm_ur3e_dex3/ur3e
         ee_link: wrist_3_link
         solver: pink
         gain: 5.0
         pink_qp_solver: daqp
         pink_task_gain: 0.5
         pink_posture_cost: 0.001
         pink_lm_damping: 1.0
         ee_rot_x_deg: 180
         ee_rot_y_deg: 0
         ee_rot_z_deg: -180

**Floating** --- disabled in this profile because the arms are articulations
controlled by IK.

**Grasp** --- same gripper mapping as the floating profile, with each side
pointing at the corresponding gripper articulation.

**Locomotion** --- drives the robot root prim so that thumbstick input moves
the dual-arm assembly as a whole (robot-base workflow). Carry Tracking Space
can be toggled to co-move the VR origin with the robot:

.. code-block:: yaml

   locomotion:
     enabled: true
     settings:
       prim_path: /World/teleop_dual_ur3_xarm_dex3
       linear_speed: 0.2
       angular_speed: 0.2

Loading a profile
##################

When loaded, the profile applies every section in order: session globals first,
then each controller panel. If the referenced prims exist on the current stage,
the controllers are resolved and ready to enable immediately. If the stage does
not match (different robot or missing prims), the profile still populates the UI
fields and reports which paths could not be resolved.


Testing the extension (VR mode)
--------------------------------

Work through the sections below in order. Each section maps to one panel in the
Teleop window. Refer to the
:ref:`UI reference <isaac_sim_app_tutorial_replicator_teleop_ui>` above for
detailed descriptions of each control.

1. Extension loading
#####################

#. Launch |isaac-sim_short|.
#. Open **Tools** > **Replicator** > **Teleop**.
#. Verify the window appears and docks in the **Property** panel.
#. Verify six collapsible sections: **Profiles**, **Session**, **Floating Controller**, **IK Controller**, **Grasp Controller**, **Locomotion**.

2. Session --- connect and frame markers
#########################################

#. Open a stage with a robot.
#. Expand **Session** and click **Connect**. Verify:

   *   Status turns green (**Connected**).
   *   Four frame markers appear under ``/Teleop/Markers`` (origin, Left, Right, Head).

   If connection fails, confirm the CloudXR process started with
   ``python -m isaacteleop.cloudxr`` is still running in another terminal and
   that the headset client is connected.

#. Move the VR controllers. Verify the **Left** and **Right** markers track in real time.
#. In the **Frame Markers** sub-section, adjust the **Scale** drag field. Verify marker axis length changes in the viewport.

3. Session --- tracking space and XR anchor
############################################

#. In **Tracking Space / Custom Origin**, change the **Coordinate Frame**
   dropdown to **Raw (no conversion)** and back to **Isaac Sim (Z-up)**.
   Verify the marker orientations update.
#. Enter a scene prim path in the **Custom Origin** field (e.g. the robot base)
   and click **Apply**. Click **Enable**. Verify VR poses are now relative to
   that prim.
#. In **XR Anchor (Headset)**, adjust the **Offset X / Y / Z** fields. Verify
   the headset camera position shifts accordingly.
#. Change the **Rotation** dropdown to **Follow Prim**. Rotate the Tracking
   Space prim in the viewport; verify the headset camera yaw follows.
#. Change **Rotation** to **Follow (Smoothed)** and adjust the **Smooth**
   slider. Verify the headset camera yaw follows with damping.
#. Check **Fixed Height**; move the Tracking Space prim vertically. Verify the
   headset camera height stays locked.

4. Floating rigid body controller
###################################

#. Ensure the stage has a free rigid body prim (e.g. an end effector not attached to an articulation).
#. Expand **Floating Controller**. In the **Left** or **Right** sub-panel, enter the prim path and click **Apply**.
#. Click **Enable**, then press **Play**.
#. Move the corresponding VR controller. Verify the rigid body tracks the controller pose.
#. Adjust **Pos Kp** / **Pos Kd** (position gains) and **Rot Kp** / **Rot Kd**
   (orientation gains) during Play. Verify responsiveness changes.
#. Change the **Target Rot X / Y / Z** dropdowns. Verify the rigid body
   orientation shifts. These correct for differing local-frame conventions
   between the VR controller and the target body.
#. Click **Clear** (while stopped). Verify the controller is torn down and the
   prim path is preserved.

5. IK controller
##################

#. Open a stage with an articulated robot arm (e.g. UR3e).
#. Expand **IK Controller**. In the **Left** or **Right** sub-panel, enter the
   articulation prim path and click **Apply**.
#. Verify the **EE Link** dropdown populates with the kinematic chain links.
   Select the desired end-effector link.
#. In the **Solver** dropdown, try each solver: **Position-based**,
   **Velocity-based**, **Levenberg-Marquardt**, **PINK**.
#. When **Position-based** or **Velocity-based** is selected, change the
   **Method** dropdown (Damped LS, Pseudoinverse, Transpose, SVD). Verify the
   method updates.
#. When **Velocity-based** is selected, adjust the **Gain** slider. Verify
   tracking aggressiveness changes.
#. When **PINK** is selected, adjust **Task Gain**, **Posture**, **QP** solver
   dropdown, and **LM Damp**. Verify the arm behavior changes.
#. Click **Enable**, then **Play**.
#. Move the VR controller. Verify the robot arm follows the target pose.
#. Move the target far outside the arm's workspace. Verify the status shows
   **Out of reach**. Return to a reachable pose; verify **Active** resumes.
#. Change the **EE Rot X / Y / Z** dropdowns during Play. Verify the
   end-effector orientation corrects for the robot's local-frame convention.
#. Adjust **VR Target Filter** and **Max Joint Step** during Play. Verify
   filtering and joint-step clamping take effect.
#. Switch the **Solver** dropdown during Play. Verify the arm continues
   tracking with the new backend without stopping the timeline.
#. Click **Clear** (while stopped). Verify solver resources are destroyed and
   the prim path is preserved.

6. Grasp controller
#####################

#. Ensure the stage has a gripper with drive joints.
#. Expand **Grasp Controller**. In the **Left** or **Right** sub-panel, enter
   the gripper prim path.
#. In the **Config** dropdown, select a built-in config (e.g. ``dex3_grasp``).
   Verify the **Config path** field updates immediately.
#. Click **Apply**, then **Enable**. Press **Play**.
#. Squeeze the VR trigger. Verify gripper joints close proportionally
   (0 = open, 1 = fully closed).
#. Release the trigger. Verify the gripper opens.
#. Click **Clear** (while stopped). Verify grasp resources are torn down and
   paths are preserved.

7. Locomotion (robot base)
##########################

#. Ensure the stage has a robot with a kinematic base prim (e.g. the robot's
   root xform).
#. Expand **Locomotion**. Enter the base prim path and click **Apply**.
#. Click **Enable**, then **Play**.
#. Push the **left thumbstick** forward/back/left/right. Verify the robot
   translates horizontally in the world ground plane.
#. Push the **right thumbstick** left/right. Verify the robot rotates (yaw).
#. Press the right face button **B** (secondary). Verify the robot moves up.
   Press **A** (primary). Verify the robot moves down.
#. Adjust **Slide Speed** and **Turn Speed** sliders. Verify movement speed
   changes.
#. Press the left face button **X** (primary) to toggle **Carry Tracking
   Space**. Move the robot via thumbstick; verify the Tracking Space prim
   follows. Toggle off; verify only the robot moves.
#. Click **Clear** (while stopped). Verify the configured state is destroyed
   and the prim path is preserved.

8. Locomotion (VR origin)
##########################

#. Expand **Locomotion**. Enter ``/Teleop/Markers/TrackingOrigin`` as the prim
   path and click **Apply**. Verify the console prints that carry is implicit.
#. Click **Enable**, then **Play**.
#. Push the **left thumbstick**. Verify the origin marker and all child markers
   (Left, Right, Head) move together in the ground plane. Controllers driven by
   the markers (Floating, IK) should follow.
#. Push the **right thumbstick**. Verify the origin rotates (yaw).
#. Press **X** (left primary). Verify the console reports carry is implicit and
   the toggle has no additional effect.

9. Stage close and reopen
##########################

#. While controllers are active and the timeline is playing, close the current
   stage.
#. Verify all panels reset to idle state without errors in the console.
#. Open a new stage and reconfigure a controller. Verify it activates cleanly.

10. Disconnect
###############

#. Click **Disconnect** in the **Session** panel.
#. Verify status turns red (**Disconnected**), markers are removed, and all
   controllers deactivate.


.. _isaac_sim_app_tutorial_replicator_teleop_sdg_debug:

Testing the extension (debug mode)
-----------------------------------

Debug mode lets you test every controller without VR hardware. Instead of live
OpenXR poses, the extension reads poses directly from draggable USD frame
markers and exposes on-screen sliders for trigger, thumbstick, and button
inputs. This makes it possible to manually move the markers to mimic the tracked
VR controllers, and use the UI sliders to mimic thumbstick and analog-button
inputs.

The markers form a parent--child hierarchy under
``/Teleop/Markers/TrackingOrigin``:

*   **TrackingOrigin** (origin) --- parent. Moving it moves all children.
*   **Left**, **Right**, **Head** --- children. Their viewport positions
    compose through the origin, just as in a real VR tracking space.

.. note::

   Debug mode and VR mode are mutually exclusive. You cannot enable
   **Debug Tracking** while a VR session is connected, and you cannot click
   **Connect** while debug tracking is active.


1. Enable debug tracking
#########################

#. Launch |isaac-sim_short| and open a stage with a robot.
#. Open **Tools** > **Replicator** > **Teleop**.
#. Expand the **Session** panel and then the **Debug** sub-section.
#. Check the **Debug Tracking** checkbox. Verify:

   *   Four frame markers appear in the viewport under
       ``/Teleop/Markers/TrackingOrigin`` (origin, Left, Right, Head).
   *   The **Connect** button is disabled.
   *   The debug sliders (**L Grasp**, **R Grasp**, **Slide X**, **Slide Y**,
       **Turn**) and hold-buttons (**Up**, **Down**, **Carry Origin**) become
       visible.

#. Select the origin marker in the viewport and translate it. Verify all child
   markers (Left, Right, Head) move together with the origin.
#. Select an individual child marker (e.g. Left) and translate it. Verify only
   that marker moves; the origin and siblings stay in place.
#. In the **Frame Markers** sub-section, adjust the **Scale** drag field.
   Verify axis lengths change on all markers.


2. Floating controller (debug)
###############################

#. Ensure the stage has a free rigid body prim (not attached to an
   articulation).
#. Expand **Floating Controller**. In the **Left** or **Right** sub-panel,
   enter the prim path and click **Apply**.
#. Click **Enable**, then press **Play**.
#. In the viewport, drag the corresponding marker (Left or Right). Verify the
   rigid body tracks the marker pose in real time.
#. Adjust **Pos Kp** / **Pos Kd** and **Rot Kp** / **Rot Kd** during Play.
   Verify responsiveness changes.
#. Change the **Target Rot X / Y / Z** dropdowns. Different grippers and end
   effectors have different local-frame conventions, and these offsets align the
   controlled body so that its forward axis matches the marker pointing
   direction. Verify the rigid body orientation shifts accordingly.
#. All gain and rotation-offset values can be saved to a teleop profile via the
   **Profiles** panel and restored later.


3. IK controller (debug)
##########################

#. Open a stage with an articulated robot arm (e.g. UR3e).
#. Expand **IK Controller**. In the **Left** or **Right** sub-panel, enter the
   articulation prim path and click **Apply**.
#. Verify the **EE Link** dropdown populates with the kinematic chain links.
   Select the desired end-effector link.
#. In the **Solver** dropdown, try each solver: **Position-based**,
   **Velocity-based**, **Levenberg-Marquardt**, **PINK**. See the
   :ref:`IK Controller UI reference <isaac_sim_app_tutorial_replicator_teleop_ui_ik>`
   for what each solver provides.
#. When **Position-based** or **Velocity-based** is selected, change the
   **Method** dropdown (Damped LS, Pseudoinverse, Transpose, SVD). Verify the
   method updates.
#. When **PINK** is selected, verify the PINK-specific controls appear:
   **Task Gain**, **Posture**, **QP** dropdown, **LM Damp**.
#. Click **Enable**, then **Play**.
#. Drag the corresponding marker in the viewport. Verify the robot arm follows
   the marker pose.
#. Move the marker far outside the arm's workspace. Verify the status shows
   **Out of reach**. Return to a reachable pose; verify the status returns to
   **Active**.
#. Change the **EE Rot X / Y / Z** dropdowns during Play. These correct for
   differing local-frame orientations between the marker and the robot's end
   effector, the same way **Target Rot** works for the Floating controller.
#. Adjust **VR Target Filter** and **Max Joint Step** during Play. Verify
   filtering and joint-step clamping take effect.
#. Switch the **Solver** or **Method** dropdown during Play. Verify the arm
   continues tracking with the new backend without stopping the timeline.


4. Grasp controller (debug)
#############################

#. Ensure the stage has a gripper with drive joints.
#. Expand **Grasp Controller**. In the **Left** or **Right** sub-panel, enter
   the gripper prim path.
#. In the **Config** dropdown, select the first entry (e.g. ``dex3_grasp``).
   Verify the **Config path** field updates immediately without needing to
   deselect and reselect.
#. Click **Apply**, then **Enable**. Press **Play**.
#. In the **Session > Debug** sub-section, slide the **L Grasp** or **R Grasp**
   slider from 0 to 1. Verify the gripper joints close proportionally.
#. Slide back to 0. Verify the gripper opens fully.


5. Locomotion --- robot base (debug)
######################################

#. Ensure the stage has a robot with a kinematic base prim.
#. Expand **Locomotion**. Enter the base prim path and click **Apply**.
#. Click **Enable**, then **Play**.
#. In the **Session > Debug** sub-section, move the **Slide X** and **Slide Y**
   sliders. Verify the robot translates horizontally in the world ground plane.
#. Move the **Turn** slider left and right. Verify the robot rotates in yaw.
#. Adjust **Slide Speed** and **Turn Speed** sliders in the **Locomotion**
   panel. Verify movement speed changes.
#. Hold the **Up** button. Verify the robot moves upward. Hold **Down**; verify
   it moves downward.
#. Hold the **Carry Origin** button while moving **Slide X** or **Slide Y**.
   Verify the origin marker (and its children) translates together with the
   robot.
#. Release **Carry Origin**. Continue sliding; verify only the robot moves and
   the origin stays in place.

6. Locomotion --- VR origin (debug)
#####################################

#. Expand **Locomotion**. Enter ``/Teleop/Markers/TrackingOrigin`` as the prim
   path and click **Apply**. Verify the console prints that carry is implicit.
#. Click **Enable**, then **Play**.
#. Move the **Slide X** and **Slide Y** sliders. Verify the origin marker and
   all child markers move together. Controllers driven by the markers (Floating,
   IK) should follow.
#. Move the **Turn** slider. Verify the origin rotates.
#. Click **Carry Origin**. Verify the console reports carry is implicit.


7. Custom origin (debug)
##########################

#. In the **Tracking Space / Custom Origin** sub-section, enter a valid scene
   prim path (e.g. the robot base link) and click **Apply**. Click **Enable**.
   Verify the status reports the custom prim as the active tracking space.
#. Enable a controller (e.g. Floating or Locomotion), press **Play**, and drag
   markers. Verify controller behavior uses the custom prim as origin.
#. Enter a path under the reserved ``/Teleop/Markers/`` namespace (e.g.
   ``/Teleop/Markers/TrackingOrigin``) and click **Apply**. Verify:

   *   The path is rejected.
   *   A warning appears in the console.

#. Clear the **Custom Origin** field and click **Apply**. Verify the tracking
   space reverts to the built-in origin marker.


8. Cleanup and re-activation
##############################

#. While controllers are active and the timeline is playing, uncheck
   **Debug Tracking**. Verify:

   *   All markers are removed from the viewport.
   *   All controller statuses reset to idle.
   *   Debug sliders and hold-buttons disappear.

#. Close the current stage. Verify no errors appear in the console.
#. Open a new stage. Re-enable **Debug Tracking** and configure a controller.
   Verify it activates cleanly without residual state from the previous
   session.
