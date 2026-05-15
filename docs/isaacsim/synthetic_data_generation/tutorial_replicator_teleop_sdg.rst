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
*   `Isaac Teleop <https://github.com/NVIDIA/IsaacTeleop>`_ installed from PyPI with
    ``python -m pip install "isaacteleop[cloudxr,retargeters]~=1.0.0"``.
*   CloudXR server started and headset connected. Follow the connection steps shown in the
    `Isaac Teleop Web Client <https://nvidia.github.io/IsaacTeleop/client/>`_.
*   A stage with a robot (e.g. ``omniverse://isaac-dev.ov.nvidia.com/Isaac/Samples/Replicator/Teleop/teleop_scenario_floating_xarm_dex3.usd``).

Start Isaac Teleop CloudXR in another terminal before connecting from the Teleop window:

.. code-block:: bash

   python -m isaacteleop.cloudxr

Keep that process running while using teleop. Then open the hosted
`Isaac Teleop Web Client <https://nvidia.github.io/IsaacTeleop/client/>`_ from the headset browser
and follow the displayed connection steps. Connect from Isaac Sim after the CloudXR runtime is
running and the headset client is connected.

.. note::

   The prerequisites above apply to VR-connected testing (both 2D and stereo
   modes). Debug mode testing requires only |isaac-sim_short| --- no headset,
   CloudXR, or Isaac Teleop installation is needed. See
   :ref:`Testing the extension (debug mode) <isaac_sim_app_tutorial_replicator_teleop_sdg_debug>`.

.. note::

   Teleop has only been tested with the Meta Quest 3, and the controller button
   mappings documented in this tutorial (for example, the left-Y recording
   button) target that device. Other CloudXR-compatible headsets may work, but
   their controller button mappings can differ and are not guaranteed.


Overview
--------

The extension has two layers:

*   ``isaacsim.replicator.teleop`` --- runtime that handles VR input, frame markers, and four controllers (Floating, IK, Grasp, Locomotion). On construction, :class:`TeleopManager <isaacsim.replicator.teleop.TeleopManager>` automatically installs a session injector with ``isaacsim.replicator.episode_recorder`` (teleop controller / head-pose channels are appended to any open recorder session) and auto-attaches a :class:`VRRecordingButton <isaacsim.replicator.teleop.VRRecordingButton>` bound to the Meta Quest left-Y button so recording can be started / stopped from VR.
*   ``isaacsim.replicator.teleop.ui`` --- UI window with six collapsible panels (Profiles, Session, Floating, IK, Grasp, Locomotion) that configure and drive the runtime.

Every controller follows the same lifecycle: **Apply** validates the prim path,
**Enable** arms the controller for the next Play, and **Clear** tears down
resources while keeping the prim path for quick reconfiguration.
All tuning controls (gains, rotation offsets, speed sliders) are live-editable
during Play and persist across sessions. Values can be saved to a teleop profile
YAML for sharing or version control.

Recording and replay are handled by the standalone Episode Recorder window
(``isaacsim.replicator.episode_recorder.ui``, opened from *Tools > Replicator >
Episode Recorder* --- see :ref:`Record and replay
<isaac_sim_app_tutorial_replicator_teleop_episode_recorder>`). The window
produces multi-episode HDF5 files using an :class:`EpisodeRecorder
<isaacsim.replicator.episode_recorder.EpisodeRecorder>` and plays them back
through the Kit timeline using :class:`EpisodeReplayer
<isaacsim.replicator.episode_recorder.EpisodeReplayer>`. While a live
:class:`TeleopManager <isaacsim.replicator.teleop.TeleopManager>` is running,
every session opened from that window automatically captures teleop
controller / aim-pose / headset channels in addition to the articulation /
rigid-body / xform channels selected in the UI. For scripted workflows,
:func:`build_teleop_recorder <isaacsim.replicator.teleop.build_teleop_recorder>`
returns an equivalent recorder preconfigured with both teleop and scene
recordables. The recorded HDF5 files feed the offline
:ref:`synthetic-data pipeline
<isaac_sim_app_tutorial_replicator_teleop_sdg_replay>`.


.. _isaac_sim_app_tutorial_replicator_teleop_ui:

UI reference
------------

The Teleop window contains six collapsible panels, described here from top to
bottom. Open the window from **Tools** > **Replicator** > **Teleop**.

Recording and replay live in a separate window (**Tools** > **Replicator** >
**Episode Recorder**, provided by ``isaacsim.replicator.episode_recorder.ui``);
see :ref:`Record and replay <isaac_sim_app_tutorial_replicator_teleop_episode_recorder>`.


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

The **Session** panel manages VR connection, frame markers, the
**XR Anchor** (custom-anchor prim plus headset offset / rotation), and
the debug controls.

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

XR Anchor
##########

The **XR Anchor** collapsable groups every control that determines where
the VR headset and controllers appear in the scene: the prim the anchor
follows (**Custom Anchor**), the per-pose **Coordinate Frame** conversion,
and the headset offset / rotation / fixed-height controls applied on top
of that anchor. The naming mirrors Kit's VR Profile menu, where this same
concept is exposed under **Navigation Settings > Physical World USD
Anchor > Custom USD Anchor**.

*   **Coordinate Frame** --- selects how incoming VR poses are converted:

    *   **Isaac Sim (Z-up)** --- applies a Y-up to Z-up rotation so poses
        match the |isaac-sim_short| stage convention. This is the default.
    *   **Raw (no conversion)** --- passes poses through unchanged.

*   **Custom Anchor** --- scene prim that the VR headset and controllers
    are anchored to. Click **Set** to validate the path and activate
    anchoring immediately (live, every-frame following of the prim from
    its world transform). After a custom path is active, the same row
    button changes to **Clear**. **Clear** reverts the active anchor to
    the built-in origin marker under ``/Teleop/Markers/`` and resets the
    marker to world (0, 0, 0); the typed path is preserved in the field.
    To retarget the active anchor, click **Clear**, edit the path if
    needed, and click **Set** again. Use the bin glyph in the row to clear
    the field text. Paths under the reserved ``/Teleop/Markers/``
    namespace fall back to the built-in origin on **Set**.

*   **Offset** --- position offset in metres for the VR headset camera.
    The UI shows one **Offset** row with **X**, **Y**, and **Z** fields;
    there is no separate **XR Headset** row label. Without a Custom Anchor
    this is an absolute world position; with one it is relative to that
    prim.
*   **Rotation** --- how the headset camera yaw tracks the Custom Anchor
    prim:

    *   **Fixed** --- ignore prim rotation entirely.
    *   **Follow Prim** --- yaw tracks the prim (roll and pitch are stripped).
    *   **Follow (Smoothed)** --- same as Follow Prim but with slerp damping.

*   **Smooth** --- slerp time constant in seconds (only used in **Smoothed**
    mode). Lower values give snappier tracking; higher values are smoother.
*   **Fixed Height** --- locks the headset camera Z to its initial value,
    preventing vertical bobbing when the Custom Anchor prim moves up or down.

.. note::

    The teleop extension owns Kit's XR profile anchor (set under
    **VR Profile > Navigation Settings > Physical World USD Anchor**) for
    the duration of a session. On Connect it switches Kit to
    ``custom anchor`` mode pointing at ``/World/XRAnchor`` and drives that
    prim every frame from the **Custom Anchor** prim plus the offset,
    rotation, smoothing, and coordinate-frame controls above. To retarget
    an active custom anchor, clear it first and then set the new path.
    Kit's profile-level **Adjust for User Height** setting (under
    **Navigation Settings**) is unrelated --- it shifts the camera at
    scene-entry time, while **Fixed Height** here locks Z to its
    first-frame value during the teleop session.

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


.. _isaac_sim_app_tutorial_replicator_teleop_episode_recorder:

Record and replay (Episode Recorder)
------------------------------------

Recording and replay are handled by the standalone Episode Recorder window
from the ``isaacsim.replicator.episode_recorder.ui`` extension (**Tools** >
**Replicator** > **Episode Recorder**). The window is fully independent of
teleop --- it works on any stage --- but when a live
:class:`TeleopManager <isaacsim.replicator.teleop.TeleopManager>` is running,
teleop controller / aim-pose / headset channels are automatically appended to
any session opened from the window via the session-injector hook installed by
:func:`install_teleop_session_injector
<isaacsim.replicator.teleop.install_teleop_session_injector>`.

Under the hood, the window captures per-physics-step simulation state (and
optionally teleop inputs) into a multi-episode HDF5 file and replays those
episodes through the Kit timeline via
:class:`EpisodeRecorder <isaacsim.replicator.episode_recorder.EpisodeRecorder>`
and :class:`EpisodeReplayer <isaacsim.replicator.episode_recorder.EpisodeReplayer>`.
All recorder commands (**Start**, **End**, **toggle**) are dispatched on the
shared ``EPISODE_CMD_EVENT`` event bus, so the window, the auto-bound VR
button, and any scripted caller drive the same underlying session.

A recording *session* is one HDF5 file that contains many *episodes*. Episodes
auto-start on timeline **Play** and auto-end on timeline **Stop**; the window
buttons and the VR button add a manual start / end / toggle edge on top of
that.

.. rubric:: HDF5 layout

Each session produces a single HDF5 file with one group per episode. Datasets
are preallocated per episode and trimmed to their true length on
``end_episode``.

.. code-block:: text

    <file>.hdf5                             # one file per open_session()
    ├── @schema_version, @stage_snapshot, manifest/, ...  # file-level attrs + manifest
    └── episodes/
        ├── episode_00000/                  # @episode_index, @started_at, @ended_at,
        │   │                               # @num_frames, @success, @start_sim_time,
        │   │                               # @end_sim_time, ...
        │   ├── meta/time/
        │   │   ├── sim_time            (N,)     float64
        │   │   ├── physics_step        (N,)     int64
        │   │   └── wall_time           (N,)     float64
        │   ├── state/<name>/                  # articulation, xform, or rigid body (UI naming)
        │   │   ├── dof_positions       (N, dof)  float32   # articulation
        │   │   ├── dof_velocities      (N, dof)  float32
        │   │   ├── dof_targets         (N, dof)  float32
        │   │   ├── root_position       (N, 3)    float32   # articulation root
        │   │   ├── root_orientation    (N, 4)    float32   # wxyz
        │   │   ├── position            (N, 3)    float32   # xform / rigid body
        │   │   ├── orientation         (N, 4)    float32   # wxyz
        │   │   ├── linear_velocity     (N, 3)    float32   # rigid body
        │   │   └── angular_velocity    (N, 3)    float32
        │   └── teleop/                        # present when a live TeleopManager is active
        │       ├── <side>/{trigger, squeeze, thumbstick_x, thumbstick_y}     (N,)    float32
        │       ├── <side>/{primary_click, secondary_click, thumbstick_click} (N,)    uint8
        │       ├── <side>/aim_position          (N, 3)  float32   # record_aim_pose=True
        │       ├── <side>/aim_orientation       (N, 4)  float32   # wxyz
        │       └── head/{position, orientation} (N, 3 | 4)  float32   # record_head_pose=True
        ├── episode_00001/ ...
        └── episode_00002/ ...

:meth:`EpisodeReplayer.list_episodes
<isaacsim.replicator.episode_recorder.EpisodeReplayer.list_episodes>` iterates
the ``episodes/episode_NNNNN`` groups for per-episode playback.

.. rubric:: Recorded data vs. replayed data

The recorder captures two kinds of data per frame:

*   **World state** (under ``state/<name>/`` --- one HDF5 group per recorded
    articulation, Xform, or rigid body): articulation DOF positions /
    velocities, articulation root pose, prim poses, and rigid-body velocities
    where enabled. This is the *only* data the replayer applies. Every
    gripper-drive joint is part of ``dof_positions``, so replaying correctly
    reproduces open / closed grippers without running any teleop logic.
*   **Teleop input channels** (under ``teleop/<side>/...``, present only when
    a live :class:`TeleopManager` is active at record time): trigger,
    squeeze, thumbstick, button clicks, and optional OpenXR aim-pose /
    headset-pose channels. These are recorded for offline analysis, policy
    learning, and re-simulation, but the replayer *ignores* them entirely.

Aim-pose / head-pose capture is controlled by carb settings
``/persistent/exts/isaacsim.replicator.teleop/record/record_aim_pose`` and
``.../record_head_pose`` (both default ``True``). Toggle them from the Script
Editor (``carb.settings.get_settings().set_bool(...)``) before opening a
session if you want to skip them.

On replay, :meth:`EpisodeReplayer.apply_frame
<isaacsim.replicator.episode_recorder.EpisodeReplayer.apply_frame>` teleports
each articulation via :meth:`Articulation.set_dof_positions
<isaacsim.core.prims.Articulation.set_dof_positions>` and
:meth:`set_world_poses <isaacsim.core.prims.Articulation.set_world_poses>`
and each prim via :meth:`XformPrim.set_world_poses
<isaacsim.core.prims.XformPrim.set_world_poses>`. The teleop controllers
(**IK**, **Grasp**, **Floating**, **Locomotion**) are **not** active during
replay --- no IK is solved, no trigger command is re-dispatched, no OpenXR
input is consumed. Replay is strictly a world-state playback.

Targets and options
^^^^^^^^^^^^^^^^^^^

*   **USD Root** --- prim path scanned by the discovery helpers.
    ``/World`` is a sensible default.
*   **Discover** --- lists every articulation (via ArticulationRootAPI),
    rigid body (via RigidBodyAPI), and plain Xform prim under the root.
    Plain Xforms are always included so a locomotion-driven robot-base
    cube, a hand-placed tracker, or a visual tool tip under an articulation
    show up without extra opt-in. Untick individual rows in the
    **Discovered Targets** list for anything you don't want recorded.
*   **Discovered Targets** (collapsible, scrollable) --- articulations and
    prims found under the root. Tick the boxes for every target you want
    recorded. Each tick maps to a group or dataset inside the HDF5 file.
*   **Output Dir** --- directory where the HDF5 file is written (defaults to
    ``<cwd>/_episode_recorder``). Created if missing.
*   **Export Scene** --- button next to the Output Dir field. Writes a
    flattened USD of the current stage as ``<output_dir>/stage_snapshot.usd``
    together with ``stage_snapshot.sidecar.json`` describing the export. The
    snapshot is scene-level, so one click per scene is enough: subsequent
    **Open Session** calls detect the file and stamp its basename into the
    HDF5 ``stage_snapshot`` attribute automatically, with no per-session
    flatten-export cost.
*   **File Prefix** --- filename prefix. The final path is
    ``{prefix}_{timestamp}.hdf5``.

Session and episode control
^^^^^^^^^^^^^^^^^^^^^^^^^^^

*   **Open Session** / **Close Session** --- single toggle button. On open,
    the recorder creates the HDF5 file, subscribes to simulation events,
    and the filename appears below. All configuration options are locked
    while a session is open.
*   **Start** / **End** --- single toggle button that manually starts or
    ends an episode inside the open session. Only enabled while a session
    is open. Also driven by the VR left-Y button (see below) and by the
    automatic timeline PLAY / STOP hooks.
*   Status label --- colour-coded feedback: *Idle* (dim), *Session open*
    (yellow), *Recording episode #K* (green), *Standby - K episode(s)
    captured* (yellow), *Session closed* (green). Errors and warnings are
    shown in red / yellow.

VR recording button
^^^^^^^^^^^^^^^^^^^

:class:`TeleopManager <isaacsim.replicator.teleop.TeleopManager>`
auto-attaches the Meta Quest left-Y button
(:class:`VRButton.LEFT_SECONDARY <isaacsim.replicator.teleop.VRButton>`) to
the ``toggle`` command via :class:`VRRecordingButton
<isaacsim.replicator.teleop.VRRecordingButton>` on construction and keeps the
binding alive for its lifetime. One press starts a new episode; a second
press ends it. The binding is rising-edge triggered, so holding the button
does not retrigger. When no session is open the dispatch is a no-op.

.. note::

   Button mappings (and the recording-button binding above) have only been
   tested with the Meta Quest 3 - other headsets may surface different button
   semantics through the same OpenXR action. See the headset-support note at
   the start of this tutorial.

Replay
^^^^^^

The **Replay** section (collapsible, collapsed by default) plays any
previously recorded HDF5 back through the Kit timeline. Replay is mutually
exclusive with recording: while a session is open the Replay controls are
locked, and while replay is attached the recording controls are locked.

*   **File** --- full path to an HDF5 session file. Use **Latest** to fill in
    the newest ``{prefix}_*.hdf5`` in the current **Output Dir**.
*   **Load** --- opens the HDF5 and populates the **Episode** dropdown with
    every episode name and its frame count. The info label next to the
    dropdown also shows ``success=True/False`` for the selected episode, so
    abandoned takes are visible at a glance.
*   **Start Replay** / **Stop Replay** --- single toggle button that drives
    :meth:`EpisodeReplayer.start_replay
    <isaacsim.replicator.episode_recorder.EpisodeReplayer.start_replay>`.
    Each Kit app update applies one recorded frame and seeks (never plays)
    the Kit timeline to the recorded ``sim_time``, so any stage-authored
    USD animations play back in lockstep without stepping physics. Pose
    writes land in an anonymous USD sublayer so the root stage is never
    mutated. Pressing **Stop Replay** (or reaching the last frame in
    non-loop mode) pops that sublayer, returning every prim to its
    pre-replay pose; the HDF5 session stays loaded so a fresh replay can
    be started immediately.
*   **Pause Replay** / **Resume Replay** --- toggle button next to **Start
    Replay**. Pauses the replay on the current frame; the last applied
    frame stays on the stage. Pressing it again resumes from where it left
    off. **Stop Replay** still pops the anonymous sublayer.
*   **Step Backward** / **Step Forward** --- single-frame buttons that apply
    the previous or next recorded frame and auto-pause the replay. Use them
    to inspect the recording one frame at a time or to seek to a specific
    moment before resuming.
*   **Seek timeline** checkbox --- when checked (default), each applied
    frame also seeks the Kit timeline to that frame's recorded ``sim_time``
    so stage-authored USD animations stay in sync with the recording.
    Uncheck it to replay only the recorded prim poses and leave the
    timeline untouched (useful when the stage has no authored animation
    or when you want to scrub the timeline manually).

.. rubric:: Pure-USD visual replay

The replayer never plays the Kit timeline and never calls into the physics
engine --- it only authors recorded poses onto the anonymous sublayer and
seeks the timeline so animations advance with the recording. This keeps
teleop controllers (Floating, IK, Locomotion) dormant during replay and
avoids the ``Simulation view object is invalidated`` errors that playing
the timeline against a stopped simulation would otherwise trigger. The
start / stop lifecycle emits ``[EpisodeRecorder][UI] Replay: starting
(episode ..., N frames, file=...)`` and ``Replay: stopped`` / ``Replay:
finished.`` on the terminal.

For the replay to work, every prim path recorded in the HDF5 must exist on
the currently loaded stage. The Replay panel uses a lenient replayer
(``strict=False``) that skips missing paths with a warning rather than
erroring. To guarantee a reproducible setup, click **Export Scene** once
before recording; the resulting ``stage_snapshot.usd`` can be opened on any
machine to reproduce the authored stage before replaying.


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

The extension ships four built-in profiles that pair each locomotion workflow
(VR-origin or robot-base) with a solo and a bimanual robot configuration:

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Profile
     - Matching stage
     - Configuration
   * - ``floating_xarm.yaml``
     - ``teleop_scenario_floating_xarm.usd``
     - Solo floating xArm gripper (right side); VR-origin locomotion.
   * - ``floating_xarm_dex3.yaml``
     - ``teleop_scenario_floating_xarm_dex3.usd``
     - Bimanual floating grippers (xArm left + Dex3 right); VR-origin locomotion.
   * - ``ik_solo_ur3_xarm.yaml``
     - ``teleop_scenario_solo_ur3_xarm.usd``
     - Single UR3e arm with xArm gripper (right side); robot-base locomotion.
   * - ``ik_dual_ur3_xarm_dex3.yaml``
     - ``teleop_scenario_dual_ur3_xarm_dex3.usd``
     - Bimanual UR3e arms (xArm gripper left + Dex3 right); robot-base locomotion.

The two bimanual profiles are described in detail below; the solo variants
share the same structure with one side disabled and the locomotion target
adjusted for the simpler robot.

Bimanual floating grippers (VR origin locomotion)
###################################################

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

``ik_dual_ur3_xarm_dex3.yaml`` configures a dual UR3e arm setup where each arm
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

.. _isaac_sim_app_tutorial_replicator_teleop_test_stages:

Built-in scenario stages
^^^^^^^^^^^^^^^^^^^^^^^^^

The four built-in profiles described in
:ref:`Built-in profiles <isaac_sim_app_tutorial_replicator_teleop_profiles>`
each ship with a matching stage on the Isaac Sim assets server. Substitute
any of these URLs when a step below calls for a stage URL --- the panel-level
behaviour is the same:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Scenario
     - Stage URL
   * - Floating, solo (right xArm)
     - ``http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Replicator/Teleop/teleop_scenario_floating_xarm.usd``
   * - Floating, bimanual (xArm left + Dex3 right)
     - ``http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Replicator/Teleop/teleop_scenario_floating_xarm_dex3.usd``
   * - IK, solo (xArm on UR3e, right side)
     - ``http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Replicator/Teleop/teleop_scenario_solo_ur3_xarm.usd``
   * - IK, bimanual (xArm left + Dex3 right on dual UR3e)
     - ``http://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0/Isaac/Samples/Replicator/Teleop/teleop_scenario_dual_ur3_xarm_dex3.usd``

The Floating Controller steps below assume one of the two floating stages;
the IK Controller steps assume one of the two IK stages.

1. Extension loading
^^^^^^^^^^^^^^^^^^^^

#. Launch |isaac-sim_short|.
#. Open **Tools** > **Replicator** > **Teleop**.
#. Verify the window appears and docks in the **Property** panel.
#. Verify six collapsible sections: **Profiles**, **Session**, **Floating Controller**, **IK Controller**, **Grasp Controller**, **Locomotion**.
#. Open **Tools** > **Replicator** > **Episode Recorder** and verify the separate recorder / replay window also appears.

2. Session --- connect and frame markers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Open one of the
   :ref:`built-in scenario stages <isaac_sim_app_tutorial_replicator_teleop_test_stages>`.
#. Expand **Session** and click **Connect**. Verify:

   *   Status turns green (**Connected**).
   *   Four frame markers appear under ``/Teleop/Markers`` (origin, Left, Right, Head).

   If connection fails, confirm the CloudXR process started with
   ``python -m isaacteleop.cloudxr`` is still running in another terminal and
   that the headset client is connected.

#. Move the VR controllers. Verify the **Left** and **Right** markers track in real time.
#. In the **Frame Markers** sub-section, adjust the **Scale** drag field. Verify marker axis length changes in the viewport.

3. Session --- XR anchor
^^^^^^^^^^^^^^^^^^^^^^^^

#. Expand the **XR Anchor** sub-panel.
#. Change the **Coordinate Frame** dropdown to **Raw (no conversion)** and
   back to **Isaac Sim (Z-up)**. Verify the marker orientations update.
#. Enter a scene prim path in the **Custom Anchor** field (e.g. the robot
   base) and click **Set**. Verify VR poses are now relative to that prim.
#. Adjust the **Offset** row's **X**, **Y**, and **Z** fields. Verify the
   headset camera position shifts accordingly.
#. Change the **Rotation** dropdown to **Follow Prim**. Rotate the Custom
   Anchor prim in the viewport; verify the headset camera yaw follows.
#. Change **Rotation** to **Follow (Smoothed)** and adjust the **Smooth**
   slider. Verify the headset camera yaw follows with damping.
#. Check **Fixed Height**; move the Custom Anchor prim vertically. Verify the
   headset camera height stays locked.

4. Floating rigid body controller
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Ensure the stage has a free rigid body prim (e.g. an end effector not attached to an articulation).
#. Expand **Floating Controller**. In the **Left** or **Right** sub-panel, enter the prim path and click **Apply**.
#. Click **Enable**, then press **Play**.
#. Move the corresponding VR controller. Verify the rigid body tracks the controller pose.
#. Adjust **Pos Kp** / **Pos Kd** (position gains) and **Rot Kp** / **Rot Kd**
   (orientation gains) during Play. Verify responsiveness changes.
#. Change the **Target Rot X / Y / Z** dropdowns. Verify the rigid body
   orientation shifts. These correct for differing local-frame conventions
   between the VR controller and the target body.
#. Test single-side configuration. Click **Clear** on the side you do not
   want, leaving only **Left** or only **Right** configured and enabled.
   Press **Play** and move both VR controllers. Verify only the configured
   rigid body tracks while the other side is ignored.
#. Click **Clear** (while stopped). Verify the controller is torn down and the
   prim path is preserved.

5. IK controller
^^^^^^^^^^^^^^^^^

#. Open one of the IK
   :ref:`built-in scenario stages <isaac_sim_app_tutorial_replicator_teleop_test_stages>`
   (solo or bimanual UR3e).
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
#. With **PINK** selected during Play, cycle through every entry in the
   **QP** dropdown (``daqp``, ``osqp``). Verify the arm keeps tracking
   with each backend and any unavailable solver is greyed out with an
   explanatory tooltip rather than throwing.
#. Test single-side configuration. **Clear** one side so only **Left** or
   only **Right** is enabled. Move both VR controllers and verify only the
   configured arm tracks.
#. Click **Clear** (while stopped). Verify solver resources are destroyed and
   the prim path is preserved.

6. Grasp controller
^^^^^^^^^^^^^^^^^^^^

#. Ensure the stage has a gripper with drive joints.
#. Expand **Grasp Controller**. In the **Left** or **Right** sub-panel, enter
   the gripper prim path.
#. In the **Config** dropdown, select a built-in config (e.g. ``dex3_grasp``).
   Verify the **Config path** field updates immediately.
#. Click **Apply**, then **Enable**. Press **Play**.
#. Squeeze the VR trigger. Verify gripper joints close proportionally
   (0 = open, 1 = fully closed).
#. Release the trigger. Verify the gripper opens.
#. Test single-side configuration. **Clear** one side so only **Left** or
   only **Right** is enabled. Squeeze both VR triggers and verify only the
   configured gripper responds.
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

9. Profiles --- save, load, validate, delete
#############################################

The **Profiles** panel persists the complete state of every other panel
to a YAML file. Test it after configuring at least one controller in the
sections above.

#. Expand **Profiles** at the top of the Teleop window.
#. Click the folder icon next to **Dir** and pick a writable directory
   (or paste an absolute path). Verify the **Profile** dropdown rescans
   and lists any ``.yaml`` files in that directory.
#. Click **Save**. Type a profile name (without ``.yaml``) into the inline
   **Name** field and click **Confirm**. Verify:

   *   A ``<name>.yaml`` file appears in the chosen directory.
   *   The dropdown refreshes to include the new profile.
   *   The status line reports ``Saved '<name>'``.

#. Click **Save** again, type the same name, and click **Confirm** twice.
   Verify the first **Confirm** warns that the file exists and the second
   **Confirm** overwrites it.
#. Open the saved YAML in a text editor and confirm it contains the
   ``session``, ``floating``, ``ik``, ``grasp``, and ``locomotion``
   sections matching the panels you configured.
#. Change a few panel values (gains, prim paths, speeds), then select your
   saved profile in the dropdown and click **Load**. Verify the panels
   revert to the saved values and the status line reports any unresolved
   prim paths.
#. Click **Validate**. Verify the status line reports ``0 error(s),
   0 warning(s)`` for a fully resolved profile, and that the console lists
   detailed issues when something is missing.
#. Open a stage that does not contain the prims referenced by the profile
   (e.g. switch from the dual-arm scene to the floating-gripper scene) and
   click **Load** again. Verify:

   *   The UI fields are still populated.
   *   The status line reports a non-zero error / warning count.
   *   The console lists the unresolved paths.

#. Reopen the original matching stage. Select the profile and click the
   **Delete** (trash) button. Verify the YAML file is removed from disk and
   the dropdown refreshes.
#. Switch **Dir** back to the default (built-in profiles) and verify the
   built-in profiles reappear in the dropdown.

10. Record and replay
######################

#. Open the Episode Recorder window from **Tools** > **Replicator** >
   **Episode Recorder**. Keep the Teleop window open in the background so
   :class:`TeleopManager` is alive and its session injector is active.
#. Set **USD Root** to a prim path that contains the robot and the prims you
   want recorded (e.g. ``/World``). Click **Discover**. Verify:

   *   The status line reports the number of articulations and prims found.
   *   The **Discovered Targets** section lists each target with a checkbox.

#. Tick the checkboxes next to the targets you want to record.
#. Keep the default **Output Dir** (``<cwd>/_episode_recorder``) and **File
   Prefix** (``episode``), or set custom values. If you plan to replay on a
   different stage later, click **Export Scene** once --- it writes
   ``stage_snapshot.usd`` into the output dir and subsequent sessions
   auto-link it.
#. Click **Open Session**. Verify:

   *   The status turns yellow with ``Session open - N articulation(s), M prim(s)``.
   *   The session label below shows ``File: episode_<timestamp>.hdf5``.
   *   The configuration options above are greyed out.

#. Press **Play** on the timeline. Verify the status turns green with
   ``Recording episode #1``. Drive the robot with the VR controllers (or
   debug sliders) for a few seconds.
#. Press **Stop** on the timeline. Verify the status turns yellow with
   ``Standby - 1 episode(s) captured``.
#. Press **Play** again and drive a second episode. Press **Stop**. Verify
   ``Standby - 2 episode(s) captured``.
#. Optional --- press the VR left-**Y** button during Play to manually
   toggle start / end instead of using the timeline. Each rising edge flips
   the recording state; the **Start** / **End** button text updates
   accordingly.
#. Click **Close Session**. Verify the status turns green with
   ``Session closed (K episode(s))``.
#. Expand the **Replay** section. Click **Latest**. Verify the **File**
   field is populated with the HDF5 you just wrote.
#. Click **Load**. Verify:

   *   Status: ``Loaded episode_<timestamp>.hdf5 (K episode(s))``.
   *   The **Episode** dropdown lists every episode with its frame count.
   *   The info label next to the dropdown shows ``success=True/False``
       for the selected episode.

#. Select an episode and click **Start Replay**. Verify:

   *   The timeline automatically starts playing.
   *   After one or two ticks, the status turns green with
       ``Replaying episode_00000 (N frames)``.
   *   The articulation / prim states track the recorded motion in real
       time.
   *   The terminal prints::

          [EpisodeRecorder][UI] Replay: freezing dynamics (articulation velocities zeroed + drive targets pinned per frame)
          [EpisodeRecorder][UI] Replay: starting (episode episode_00000, N frames, file=...)

   *   No articulation drifts despite the timeline (and therefore PhysX)
       still running --- freezes are applied every tick.

#. Click the **Pause Replay** button (next to **Start Replay**). Verify the
   stage freezes on the current frame while the timeline keeps running.
   Click **Resume Replay** and verify replay continues from the same frame.
#. Click **Step Backward** and **Step Forward**. Verify the stage jumps to
   the previous / next recorded frame and the replay stays paused.
#. Uncheck **Seek timeline**, click **Resume Replay**, and verify the prim
   poses still update but the timeline is no longer seeked to the recorded
   ``sim_time`` (any stage-authored USD animations are now frozen). Re-check
   the box and verify the timeline catches back up.
#. Press **Pause** on the Kit timeline. Verify the stage freezes on the
   current frame. Scrub the timeline left / right and verify the stage
   jumps to the nearest recorded frame.
#. Click **Stop Replay**. Verify the timeline stops, the status returns to
   ``Replay stopped.``, and the terminal prints::

       [EpisodeRecorder][UI] Replay: stopped
       [EpisodeRecorder][UI] Replay: dynamics restored

11. Stage close and reopen
###########################

#. While controllers are active and the timeline is playing, close the current
   stage.
#. Verify all panels reset to idle state without errors in the console.
#. Open a new stage and reconfigure a controller. Verify it activates cleanly.

12. Disconnect
###############

#. Click **Disconnect** in the **Session** panel.
#. Verify status turns red (**Disconnected**), markers are removed, and all
   controllers deactivate.


.. _isaac_sim_app_tutorial_replicator_teleop_sdg_episode_recorder:

Testing the extension (Episode Recorder)
-----------------------------------------

The standalone Episode Recorder window can be tested independently of the Teleop extension, though they integrate seamlessly when both are active.

1. Record a session
^^^^^^^^^^^^^^^^^^^

#. Open a stage with some articulations or rigid bodies (any of the
   :ref:`built-in scenario stages <isaac_sim_app_tutorial_replicator_teleop_test_stages>`
   works).
#. Open **Tools** > **Replicator** > **Episode Recorder**.
#. Set **USD Root** to ``/World`` and click **Discover**.
#. Verify the **Discovered Targets** list populates with the articulations and prims found under the root.
#. Tick the checkboxes next to the targets you want to record.
#. Click **Export Scene** to save a snapshot of the current stage. Verify ``stage_snapshot.usd`` is created in the output directory.
#. Click **Open Session**. Verify the status turns yellow with ``Session open`` and the filename appears below.
#. Press **Play** on the timeline. Verify the status turns green with ``Recording episode #1``.
#. Move the robot or wait a few seconds, then press **Stop** on the timeline. Verify the status turns yellow with ``Standby - 1 episode(s) captured``.
#. Click **Close Session**. Verify the status turns green with ``Session closed (1 episode(s))``.

2. Replay a session
^^^^^^^^^^^^^^^^^^^

#. Expand the **Replay** section in the Episode Recorder window.
#. Click **Latest**. Verify the **File** field is populated with the HDF5 file you just recorded.
#. Click **Load**. Verify the **Episode** dropdown lists the recorded episode with its frame count.
#. Click **Start Replay** (the play icon). Verify:
   * The timeline starts playing.
   * The articulation / prim states track the recorded motion.
   * The Replay button icon changes to a stop icon.
#. While replaying, click the **Pause** button. Verify the stage freezes on the current frame and the timeline continues playing.
#. Click the **Step Forward** and **Step Backward** buttons. Verify the stage updates to the next/previous recorded frame.
#. Click the **Pause** button again to resume the replay.
#. Uncheck the **Seek timeline** checkbox. Verify the replay continues, but the timeline is no longer seeked to the recorded ``sim_time``.
#. Click **Stop Replay** (the stop icon). Verify the timeline stops and the prims return to their pre-replay poses.


.. _isaac_sim_app_tutorial_replicator_teleop_sdg_debug:

Testing the extension (debug mode)
-----------------------------------

Debug mode lets you test every controller without VR hardware. Instead of live
OpenXR poses, the extension reads poses directly from draggable USD frame
markers and exposes on-screen sliders for trigger, thumbstick, and button
inputs. This makes it possible to manually move the markers to mimic the tracked
VR controllers, and use the UI sliders to mimic thumbstick and analog-button
inputs.

Pick any of the four
:ref:`built-in scenario stages <isaac_sim_app_tutorial_replicator_teleop_test_stages>`
when a step below calls for a stage URL --- the floating stages exercise
the Floating Controller, and the UR3e stages exercise the IK Controller.

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
^^^^^^^^^^^^^^^^^^^^^^^^

#. Launch |isaac-sim_short| and open one of the
   :ref:`built-in scenario stages <isaac_sim_app_tutorial_replicator_teleop_test_stages>`.
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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
#. Test single-side configuration. **Clear** one side so only **Left** or
   only **Right** is enabled. Drag both markers and verify only the
   configured rigid body tracks.
#. Switch the **Write Backend** dropdown in the **Debug** sub-section between
   **USD**, **USD-RT**, and **Fabric** during Play. Verify the rigid body
   keeps tracking with no errors. **Fabric** requires Fabric Scene Delegate
   (``/app/useFabricSceneDelegate=true``); skip it on apps without FSD.
#. All gain and rotation-offset values can be saved to a teleop profile via the
   **Profiles** panel and restored later.


3. IK controller (debug)
^^^^^^^^^^^^^^^^^^^^^^^^^

#. Open one of the IK
   :ref:`built-in scenario stages <isaac_sim_app_tutorial_replicator_teleop_test_stages>`
   (solo or bimanual UR3e).
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
#. With **PINK** selected during Play, cycle through every entry in the
   **QP** dropdown (``daqp``, ``osqp``). Verify the arm keeps tracking
   with each backend and any unavailable solver is greyed out rather than
   throwing.
#. Test single-side configuration. **Clear** one side so only **Left** or
   only **Right** is enabled. Drag both markers and verify only the
   configured arm tracks.


4. Grasp controller (debug)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
#. Test single-side configuration. **Clear** one side so only **Left** or
   only **Right** is enabled. Move both **L Grasp** and **R Grasp** sliders
   and verify only the configured gripper responds.


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


7. Custom anchor (debug)
########################

#. Expand the **XR Anchor** sub-panel, enter a valid scene prim path
   (e.g. the robot base link) in the **Custom Anchor** field, and click
   **Set**. Verify the status reports the custom prim as the active anchor.
#. Enable a controller (e.g. Floating or Locomotion), press **Play**, and drag
   markers. Verify controller behavior uses the custom prim as the VR
   origin anchor.
#. Click **Clear**. Verify the anchor reverts to the built-in origin marker
   at world (0, 0, 0), while the typed path stays in the field.
#. Enter a path under the reserved ``/Teleop/Markers/`` namespace (e.g.
   ``/Teleop/Markers/TrackingOrigin``) and click **Set**. Verify the path
   falls back to the built-in origin marker (status notes the substitution).
#. Click **Clear** again. Verify the headset and controllers stay anchored to
   the built-in origin marker. The typed path stays in the field so it can be
   re-applied with **Set**; click the bin glyph in the row if you want to
   clear the text as well.


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


.. _isaac_sim_app_tutorial_replicator_teleop_sdg_replay:

Synthetic data generation from recorded episodes
-------------------------------------------------

The UI replay discussed in :ref:`Record and replay <isaac_sim_app_tutorial_replicator_teleop_episode_recorder>`
is a quick visual preview that drives the Kit timeline. For offline synthetic
data generation you drive
:class:`EpisodeReplayer <isaacsim.replicator.episode_recorder.EpisodeReplayer>` frame by
frame and call ``rep.orchestrator.step_async`` after each
:meth:`apply_frame <isaacsim.replicator.episode_recorder.EpisodeReplayer.apply_frame>`.
That detaches recording time from rendering time, so an expensive writer or
DLSS mode can run per frame without slowing teleop and without time drift.

Prerequisites:

*   An HDF5 session produced by the :ref:`Episode Recorder window <isaac_sim_app_tutorial_replicator_teleop_episode_recorder>`
    (or any :class:`EpisodeRecorder <isaacsim.replicator.episode_recorder.EpisodeRecorder>`
    subclass).
*   A USD stage to replay against; every prim path in the HDF5 must resolve on
    this stage. Point ``STAGE_PATH`` at the original authored scene used for
    recording, or at an exported snapshot - click **Export Scene** in the
    Episode Recorder window, or call
    :func:`export_stage_snapshot <isaacsim.replicator.episode_recorder.export_stage_snapshot>`
    from a script, to produce ``stage_snapshot.usd`` next to the HDF5.
*   |isaac-sim_short| running (VR / CloudXR connection not required for replay).

The script below opens ``STAGE_PATH``, resolves the cameras listed in
``CAMERA_PATHS`` (or falls back to a default camera if none resolve), attaches
both a :class:`BasicWriter <omni.replicator.core.BasicWriter>` (RGB PNGs) and a
:class:`CosmosWriter <omni.replicator.core.CosmosWriter>` (video clips) to the
camera render products, and then iterates every recorded frame, calling
``rep.orchestrator.step_async`` after each
:meth:`apply_frame <isaacsim.replicator.episode_recorder.EpisodeReplayer.apply_frame>`.
Outputs land under ``_out_teleop_replay/basic/`` and
``_out_teleop_replay/cosmos/`` next to the current working directory.

Before running either variant below, edit ``HDF5_PATH`` and ``STAGE_PATH`` at
the top of the script to point at your recorded session and its matching USD
stage.

.. tab-set::

    .. tab-item:: Standalone Application

        The example can be run as a standalone application using the following commands in the terminal (on Windows use ``python.bat`` instead of ``python.sh``):

        .. code-block:: bash

            ./python.sh standalone_examples/api/isaacsim.replicator.teleop/sdg_teleop_replay.py

        .. raw:: html

            <details closed>
            <summary>Full Standalone Script</summary>

        .. literalinclude:: ../../../source/standalone_examples/api/isaacsim.replicator.teleop/sdg_teleop_replay.py
            :language: python
            :lines: 16-
            :end-before: # <start-sdg-teleop-replay-test>

        .. raw:: html

            </details>

    .. tab-item:: Script Editor

        Paste the snippet below into the **Script Editor** (``Window > Script Editor``).

        .. raw:: html

            <details closed>
            <summary>Full Script Editor Script</summary>

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_teleop/sdg_teleop_replay_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

Adapt the script to your pipeline by swapping or adding any other Replicator
writer (depth, semantic segmentation, instance segmentation, normals, motion
vectors, etc.) or by inserting randomizers between ``apply_frame`` and
``step_async`` to produce scene variants per recorded trajectory.
