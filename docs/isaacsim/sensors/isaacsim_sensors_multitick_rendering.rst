..
   Copyright (c) 2024-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_sensors_multitick_rendering:

=========================
Multi-Tick Rendering
=========================

Multi-tick rendering decouples each sensor's render rate from the main simulation frame rate.
Instead of rendering every sensor every frame, each sensor ticks independently at its
own configurable rate. This significantly improves performance in scenes with many sensors
by avoiding redundant rendering work.

Multi-tick rendering is **enabled by default** in |isaac-sim_short| 6.0 and later.

.. contents:: On this page
   :local:
   :depth: 2

Overview
========

Before |isaac-sim_short|-6.0, every camera and RTX sensor rendered at the simulation
frame rate. With multi-tick rendering enabled, the renderer maintains independent tick
counters for each sensor and only renders a sensor when its tick interval has elapsed.

The ``omni:sensor:tickRate`` attribute on each sensor prim controls the render frequency
in Hz. A value of ``0`` (the default) puts the sensor in *autotrigger* mode, where it
renders every frame, as if multi-tick rendering was disabled.

Performance Benefits
--------------------

- **Reduced GPU load**: Sensors that do not need to update every frame skip rendering
  entirely, freeing GPU resources for other sensors or simulation work.
- **Independent rates**: A stereoscopic depth camera running at 60 Hz no longer forces a
  30 Hz RGB camera to also render at the same rate.
- **Better scaling**: Scenes with many sensors (for example multi-robot fleets) see
  proportionally larger improvements because each sensor only consumes GPU time when it
  actually ticks.

.. _isaac_sim_sensors_multitick_configuring_per_sensor_tick_rates:

Configuring Per-Sensor Tick Rates
=================================

Sensor tick rates are controlled by the ``omni::sensor::tickRate`` attribute in the ``OmniSensorAPI``
USD schema, which is applied to Camera and OmniLidar prims. The shipped USD assets in |isaac-sim_short| 6.0
already have this schema applied with appropriate default tick rates.

.. note::

    The ``OmniSensorAPI`` schema is also applied to ``OmniRadar`` prims, but in
    |isaac-sim_short| 6.0 GA the RTX Radar renderer ignores ``omni:sensor:tickRate``
    and always autotriggers. See :ref:`isaac_sim_sensors_multitick_known_issue_radar_autotrigger`.

Using the Isaac Sim Extension API
---------------------------------

The ``isaacsim.sensors.experimental.rtx`` extension provides Python APIs for authoring sensor prims and configuring their tick rates.
For example, to author an OmniLidar prim at ``/World/Lidar`` with a tick rate of 10 Hz:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_multitick_rendering/configure_lidar_tick_rate.py
    :language: python

For cameras:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_camera/set_camera_tick_rate.py
    :language: python

Using OmniGraph
---------------

When using the ROS2, UCX, or HSB helper OmniGraph nodes, the sensor tick rate is read
from the ``omni:sensor:tickRate`` attribute on the sensor prim. No additional node
configuration is needed.

For a worked ROS2 example that scales sensor and graph publish rates with simulation frame
rate, see :ref:`isaac_sim_app_tutorial_ros2_publish_rate`.

.. _isaac_sim_sensors_multitick_lidar_tickrate_must_match_scanrate:

OmniLidar Tick Rate Must Equal ``scanRateBaseHz``
-------------------------------------------------

.. warning::

    For ``OmniLidar`` prims, ``omni:sensor:tickRate`` **must** be set equal to
    ``omni:sensor:Core:scanRateBaseHz`` for scan accumulation and multi-tick rendering to
    behave correctly.

If the two values differ, the Lidar model falls back to producing **partial scans every
frame** instead of accumulating to a full rotation (rotary Lidars) or full azimuth sweep
(solid-state Lidars). Downstream pipelines that assume a full scan per tick - including
``ROS2 RTX Lidar Helper`` ``laser_scan`` publishers, ``IsaacComputeRTXLidarFlatScan``, and
any consumer of accumulated ``GenericModelOutput`` data - silently see truncated output.
The renderer does not log an error in this case.

For example, the shipped ``Example_Rotary`` Lidar config has ``scanRateBaseHz = 10``, so
the sensor must tick at 10 Hz:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_lidar/set_lidar_tick_rate.py
    :language: python

The same constraint applies to ``Example_Solid_State`` and to vendor configs in
:ref:`isaac_assets_nonvisual_sensors_rtx_lidar`. When wrapping an existing ``OmniLidar``
prim, read ``omni:sensor:Core:scanRateBaseHz`` from the prim and pass that value as
``tick_rate``.

.. _isaac_sim_sensors_multitick_clock_relationships:

Architecture: Timeline, Physics, and the Renderer
=================================================

With multi-tick rendering enabled, three clocks advance independently per ``omni.kit.app`` update.
This section explains what each clock is, how each one advances,
and how they interact. Code that mixes ``omni.timeline`` time with physics or sensor time can
produce inconsistent timestamps in some configurations, so these relationships matter
when configuring deterministic simulations or interpreting sensor output.

The three clocks
----------------

.. csv-table::
    :header: "Clock", "Source of advance", "Controlled by", "Read by"
    :widths: 25, 30, 25, 20

    "Run-loop / ``omni.timeline`` time", "Wall-clock dt per app update, or a fixed manual dt when set", "``RenderingManager.set_dt(...)`` (manual mode), ``/app/runLoops/main/rateLimitFrequency``", "Timeline UI, ``timeCodesPerSecond``, stage update scheduling"
    "Physics simulation time", "Recomputed on every physics step as ``stepCount / stepsPerSecond``", "``PhysicsScene.set_dt(...)`` or ``SimulationManager.setup_simulation(dt=...)``", "``SimulationManager.get_simulation_time()``, ``IsaacReadSimulationTime``, ROS 2 / UCX / HSB timestamps"
    "Renderer simulation time", "Mirror of physics time, written to the Fabric prim ``/ExternalSimulationTime.omni:time`` after each physics step", "Driven by ``isaacsim.core.simulation_manager``; seeded by ``RenderingManager`` when the simulation manager is absent", "The multi-tick renderer's per-sensor tick scheduler at ``eHydraRendering``"

The renderer no longer reads ``omni.timeline`` to obtain the current simulation time;
it reads the ``omni:time`` attribute on the ``/ExternalSimulationTime`` prim from Fabric. Physics writes that attribute on
every ``onPhysicsStep`` callback at stage-update order ``-10``, so the latest value is
available to Hydra at order ``30`` within the same app update.

Per-frame ordering
------------------

For one ``App.update()`` with the timeline playing:

1. The run loop computes ``loop_dt`` (manual or wall-clock) and ``omni.timeline``
   advances by ``loop_dt``.
2. The physics stage-update phase runs ``N >= 0`` substeps of ``physics_dt`` to catch
   the loop time. Each substep recomputes the physics simulation time and writes it to
   ``/ExternalSimulationTime``.
3. Hydra reads ``/ExternalSimulationTime`` once. The per-sensor tick scheduler compares
   that value to each sensor's last-rendered time and its ``omni:sensor:tickRate`` to
   decide which sensors render this frame.
4. OmniGraph nodes such as ``IsaacReadSimulationTime`` read the same simulation time,
   either directly or, when given a reference frame ``RationalTime``, via interpolation
   from the ``TimeSampleStorage`` ring buffer maintained by
   ``isaacsim.core.simulation_manager``.

Behavior depends on the ratio of ``physics_dt`` to ``loop_dt``
--------------------------------------------------------------

.. csv-table::
    :header: "Configuration", "Physics steps per app update", "End-of-frame ``/ExternalSimulationTime``", "Timeline vs physics time", "Per-sensor ticking"
    :widths: 22, 13, 25, 25, 15

    "``physics_dt == loop_dt``", "1", "Equal to loop time", "Equal each frame", "As scheduled"
    "``physics_dt < loop_dt``", "``N >= 1``", "Equal to loop time within one substep", "Equal each frame", "As scheduled"
    "``physics_dt > loop_dt``", "``0`` or ``1``", "Lags loop time by up to one ``physics_dt``", "Drifts within a physics step, resyncs when physics advances", "Only on frames where ``/ExternalSimulationTime`` advanced"

In the ``physics_dt <= loop_dt`` cases, multiple physics substeps in the same frame all
write to ``/ExternalSimulationTime``, but only the last value is what the renderer
reads. ``TimeSampleStorage`` collapses these writes to a single sample per frame, keyed
by the frame's ``RationalTime``, holding the cumulative physics time.

In the ``physics_dt > loop_dt`` case, frames where no physics step runs leave
``/ExternalSimulationTime`` unchanged. The render pipeline still runs every app update,
but per-sensor tick counters do not advance and no sensor produces a new output on those
frames. When physics finally steps, the prim jumps forward by ``physics_dt`` and due
sensors render on that frame.

.. _isaac_sim_sensors_multitick_clock_relationships_use_fixed_time_stepping:

When ``useFixedTimeStepping=true`` (the full Isaac Sim GUI default)
-------------------------------------------------------------------

The table above describes the substep-to-catch-up behavior that applies when
``/app/player/useFixedTimeStepping`` is **false** (the default in standalone Python).
The full Isaac Sim GUI app sets this carb setting to **true** in
``source/apps/isaacsim.exp.full.kit``. With it true, the timeline ignores the run-loop's
measured ``dt`` and forces ``dt = 1 / timeCodesPerSecond`` per accepted update inside
``Timeline::update()``. Sensor and timeline time then advance at:

.. code-block:: text

    sim_advance_per_wall_sec  =  (1 / timeCodesPerSecond)  *  loop_hz_wall

Consequences:

- If ``loop_hz_wall == timeCodesPerSecond`` (the default 60 Hz on both), ``sim/wall = 1.0``
  and the system runs in real time. This is what
  :py:meth:`isaacsim.core.rendering_manager.RenderingManager.set_dt` configures when called
  alone - it aligns ``rateLimitFrequency``, ``targetFramerate``, and ``timeCodesPerSecond``
  to the same value.
- If ``loop_hz_wall < timeCodesPerSecond`` (e.g. the loop is rate-limited below the
  timeline's per-tick rate), the simulation runs in **slow motion** at ratio
  ``loop_hz_wall / timeCodesPerSecond``. RTX sensors gated by
  ``/ExternalSimulationTime`` publish proportionally slower; OnPlaybackTick-driven
  publishers (``/clock``, OmniGraph ticks) still fire at ``loop_hz_wall``. This is the
  trap when users only set ``/app/runLoops/main/rateLimitFrequency`` without updating
  ``timeCodesPerSecond``: physics step time and wall clock decouple in a non-obvious way.
- If ``loop_hz_wall > timeCodesPerSecond``, the behavior depends on
  ``/app/player/useFastMode`` (also exposed as ``timeline.set_play_every_frame(...)``):

  - **``useFastMode = false`` (the default)**: the timeline subsamples (advances time on
    every Nth run-loop tick where ``N = ceil(targetFramerate / timeCodesPerSecond)``) so
    the timeline stays at its configured rate while the run loop ticks faster. This is
    used to drive higher render-product / OnPlaybackTick rates without speeding up
    sim time.
  - **``useFastMode = true``** (set when, for example, ``timeline.set_play_every_frame(True)``
    is called - some Replicator examples and benchmarks do this): the subsample gate is
    bypassed. Every run-loop tick advances the timeline by ``1 / timeCodesPerSecond``,
    so sim time runs **faster than wall time** (fast-forward) at ratio
    ``loop_hz_wall / timeCodesPerSecond``. This is the intended behavior for offline
    data generation where you want to ingest as much simulated time as possible per
    wall second, but it breaks any code that assumes sim time tracks wall time.

The reference example in
:ref:`isaac_sim_app_tutorial_ros2_publish_rate_set_simulation_frame_rates` uses
:py:meth:`isaacsim.core.simulation_manager.SimulationManager.setup_simulation` plus
:py:meth:`isaacsim.core.rendering_manager.RenderingManager.set_dt` to keep all three
clocks coherent - avoiding all of the above modes by construction. It leaves
``useFastMode`` at its default of ``false``.

Practical implications
----------------------

- Always read simulation time through ``SimulationManager.get_simulation_time()``,
  ``IsaacReadSimulationTime``, or the per-frame ``getSimulationTimeAtTime(rtime)``
  lookup. These return the physics-driven value that the renderer also sees, so sensor
  stamps, TF stamps, and downstream consumers stay consistent.
- Do not use ``omni.timeline`` current time as a sensor or message timestamp. In the
  ``physics_dt > loop_dt`` configuration the two clocks drift each frame and only
  resync on physics steps, producing inconsistent stamps.
- To keep physics, the renderer, and downstream pipelines all advancing once per
  frame, set ``physics_dt == loop_dt`` via
  ``SimulationManager.setup_simulation(dt=1.0 / hz)`` and
  ``RenderingManager.set_dt(1.0 / hz)``. The ``isaacsim.exp.base.zero_delay.kit``
  experience configures this and is the reference setup for deterministic single-frame
  TF / image pairing.

.. _isaac_sim_sensors_multitick_settings_reference:

Settings Reference
==================

The settings, APIs, and USD attributes below configure multi-tick rendering, per-sensor
tick rates, and the underlying loop / physics clocks discussed in
:ref:`isaac_sim_sensors_multitick_clock_relationships`.

.. csv-table::
    :header: "Setting / API / Attribute", "Kind", "Default", "Effect"
    :widths: 30, 10, 12, 48

    "``/rtx/hydra/supportMultiTickRate``", "carb setting", "``true``", "Enables multi-tick rendering. When ``false``, the renderer reverts to per-frame rendering and does not consult ``/ExternalSimulationTime``."
    "``/rtx/rendering/perSensorTickTlas``", "carb setting", "``true``", "Builds a per-sensor Top-Level Acceleration Structure (TLAS) on each sensor tick instead of once per frame."
    "``/app/player/playSimulations``", "carb setting", "``true``", "When ``false``, ``App.update()`` does not step physics, so ``/ExternalSimulationTime`` is frozen even though ``omni.timeline`` may continue to advance. ``RenderingManager.render()`` toggles this around its update to render without ticking the simulation clock."
    "``RenderingManager.set_dt(dt)``", "Python API", "n/a", "Sets ``loop_dt``. Switches the Isaac loop runner to manual mode, sets ``/app/runLoops/main/rateLimitFrequency``, and updates ``omni.timeline.set_target_framerate`` and the stage's ``timeCodesPerSecond``."
    "``PhysicsScene.set_dt(dt)`` / ``SimulationManager.setup_simulation(dt=...)``", "Python API", "1/60 s", "Sets ``physics_dt`` on the physics scene. The physics engine uses an internal accumulator to decide how many substeps to take each app update."
    "``RenderingManager.render()``", "Python API", "n/a", "Render the stage without stepping physics. Temporarily sets ``/app/player/playSimulations=false`` for one app update."
    "``omni:sensor:tickRate`` (Hz)", "USD attribute", "``0`` (autotrigger)", "Per-sensor render rate. Compared against ``/ExternalSimulationTime`` by the per-sensor tick scheduler. Applied to ``Camera`` and ``OmniLidar`` prims; ignored on ``OmniRadar`` in 6.0 GA (see :ref:`isaac_sim_sensors_multitick_known_issue_radar_autotrigger`)."
    "``omni:sensor:Core:scanRateBaseHz`` (Hz)", "USD attribute", "Config-dependent (for example ``10`` for ``Example_Rotary``)", "OmniLidar scan rate. Must equal ``omni:sensor:tickRate`` - see :ref:`isaac_sim_sensors_multitick_lidar_tickrate_must_match_scanrate`."
    "``omni:sensor:Core:accumulateOutputs``", "USD attribute", "``true``", "OmniLidar scan accumulation. When ``true``, full scans accumulate over multiple frames; when ``false``, the GMO carries the per-frame partial scan."

The ``/rtx/hydra/supportMultiTickRate`` and ``/rtx/rendering/perSensorTickTlas`` settings
are configured in ``isaacsim.exp.base.kit`` and are also passed as standard test
arguments to all extension tests.

.. note::

    To reproduce the |isaac-sim_short| 5.x render-every-frame behavior in 6.0 (for
    example to debug a regression), launch with
    ``--/rtx/hydra/supportMultiTickRate=false``. Most other code paths in 6.0 assume the
    global default and have not been validated with the setting disabled.

Migration from Previous Releases
================================

If you are upgrading from a release where multi-tick rendering was not enabled by
default, the following changes may affect your workflow.

General changes
---------------

1. **Update Camera and OmniSensor prims to work with multi-tick rendering.** Apply the
   ``OmniSensorAPI`` schema to ``Camera`` prims. This schema is already applied by
   default to ``OmniLidar``/``OmniRadar`` prims. Set the ``omni:sensor:tickRate``
   attribute to control render frequency. Multi-tick rendering is transparent when
   sensors use the default ``omni:sensor:tickRate`` of ``0`` (autotrigger), which
   renders every frame.

2. **USD assets updated.** Shipped sensor assets now have the ``OmniSensorAPI`` schema
   applied. If you have custom USD assets with ``Camera`` or ``OmniLidar``/``OmniRadar``
   prims, apply the ``OmniSensorAPI`` schema and set ``omni:sensor:tickRate`` to control
   render frequency.

3. **frameSkipCount is deprecated.** Replace usage of ``frameSkipCount`` on
   ROS2/UCX/HSB helper nodes with ``omni:sensor:tickRate`` on the sensor prim. See
   :ref:`isaac_sim_sensors_multitick_frameskipcount_deprecation` below.

4. **RTX Lidar accumulation moved to a USD attribute.** Lidar scan accumulation is now
   controlled by the ``omni:sensor:Core:accumulateOutputs`` attribute on the
   ``OmniLidar`` prim. The deprecated ``isaacsim.sensors.rtx`` extension's
   ``IsaacExtractRTXSensorPointCloudNoAccumulator`` annotator and its
   ``IsaacCreateRTXLidarScanBuffer`` and ``IsaacComputeRTXLidarFlatScan`` nodes have
   been updated to read this attribute. The newer ``IsaacExtractRTXSensorPointCloud``
   annotator and OmniGraph node live in ``isaacsim.sensors.rtx.nodes`` and assume the
   GMO buffer already contains either a full scan or a per-frame partial scan based on
   ``accumulateOutputs``.

5. **Replace single-render-product waits with full app updates.** The
   ``omni.syntheticdata.sensors.next_render_simulation_async`` helper (and any other
   helper that targets a single render product) does not advance per-sensor tick
   counters correctly under multi-tick rendering. Use
   ``isaacsim.core.experimental.utils.app.update_app_async`` instead, which performs
   full application update steps and ensures all sensor ticks are processed.

   *Before:*

   .. literalinclude:: ../snippets/sensors/isaacsim_sensors_multitick_rendering/migration_render_wait_old.py
       :language: python

   *After:*

   .. literalinclude:: ../snippets/sensors/isaacsim_sensors_multitick_rendering/migration_render_wait_new.py
       :language: python

.. _isaac_sim_sensors_multitick_frameskipcount_deprecation:

frameSkipCount Deprecation
--------------------------

In previous releases, publish rates for the ROS2 and UCX helper nodes were controlled by
the ``frameSkipCount`` input on each helper node. This parameter is now **deprecated**.

With multi-tick rendering enabled globally, the correct way to control how often a
sensor publishes data is to set ``omni:sensor:tickRate`` on the sensor prim itself. This
is more efficient because the sensor does not render at all during skipped ticks, rather
than rendering and discarding the output.

The ``frameSkipCount`` parameter still works for backward compatibility, but a
deprecation warning is logged when a non-zero value is used. It will be removed in a
future release.

The deprecation applies to every helper node that previously exposed ``frameSkipCount``:

- ``ROS2 Camera Helper`` (``isaacsim.ros2.bridge.ROS2CameraHelper``)
- ``ROS2 Camera Info Helper`` (``isaacsim.ros2.bridge.ROS2CameraInfoHelper``)
- ``ROS2 RTX Lidar Helper`` (``isaacsim.ros2.bridge.ROS2RtxLidarHelper``)
- ``UCX Camera Helper`` (``isaacsim.ucx.bridge.UCXCameraHelper``)

The newer ``ROS2 RTX Radar Helper`` (``isaacsim.ros2.bridge.ROS2RtxRadarHelper``) was
introduced after this deprecation and does not expose ``frameSkipCount`` at all.

Multi-tick scheduling migration
-------------------------------

The table below lists 5.x rate-control inputs and the recommended 6.0 replacement for
each sensor type. For the broader extension API migration (Kit-command-based sensor
creation, class renames, annotator attach styles, GMO-helper changes), see
:ref:`isaacsim_sensors_rtx_migration`. For the deprecated ``isaacsim.sensors.camera``
extension, see :ref:`isaacsim_sensors_camera_migration`. For ``auxOutputType`` ->
``GenericModelOutput`` channels, see :ref:`isaacsim_sensors_rtx_aux_output_level`.

.. csv-table::
    :header: "Sensor type", "5.x input", "6.0 replacement", "Notes"
    :widths: 18, 30, 30, 22

    "RTX Lidar", "``frameSkipCount`` on ``ROS2 RTX Lidar Helper``", "``omni:sensor:tickRate`` on the ``OmniLidar`` prim", "Must equal ``omni:sensor:Core:scanRateBaseHz``. See :ref:`isaac_sim_sensors_multitick_lidar_tickrate_must_match_scanrate`."
    "RTX Lidar", "``fullScan`` input on ``ROS2 RTX Lidar Helper``", "``omni:sensor:Core:accumulateOutputs`` on the ``OmniLidar`` prim", "Helper input is now ignored and logs a deprecation warning when set to ``False``."
    "Camera (ROS 2)", "``frameSkipCount`` on ``ROS2 Camera Helper`` / ``ROS2 Camera Info Helper``", "``omni:sensor:tickRate`` on the ``Camera`` prim", "Camera prim must have ``OmniSensorAPI`` applied. ``RtxCamera`` applies it automatically."
    "Camera (UCX)", "``frameSkipCount`` on ``UCX Camera Helper``", "``omni:sensor:tickRate`` on the ``Camera`` prim", "Helper still accepts ``frameSkipCount`` and logs a deprecation warning."

RTX Radar is intentionally omitted: ``omni:sensor:tickRate`` is ignored on
``OmniRadar`` in 6.0 GA (see
:ref:`isaac_sim_sensors_multitick_known_issue_radar_autotrigger`). Gate Radar publish
rates downstream instead.

.. _isaac_sim_sensors_multitick_known_issues:

Known Issues
============

.. _isaac_sim_sensors_multitick_known_issue_radar_autotrigger:

RTX Radar autotriggers in 6.0 GA
--------------------------------

In |isaac-sim_short| 6.0 GA, the RTX Radar renderer ignores ``omni:sensor:tickRate``
on ``OmniRadar`` prims and renders every simulation frame. Setting ``tick_rate`` on
:py:class:`isaacsim.sensors.experimental.rtx.Radar` has no effect on the actual
render cadence; the attribute is still authored on the prim, but the multi-tick
scheduler skips Radar prims. This is expected to be corrected in a future release.

The autotrigger limitation does not affect ``OmniLidar`` or ``Camera`` prims.

OmniLidar partial-scan fallback
-------------------------------

If ``omni:sensor:tickRate`` is not equal to ``omni:sensor:Core:scanRateBaseHz`` on an
``OmniLidar`` prim, the sensor falls back to emitting partial scans every frame. See
:ref:`isaac_sim_sensors_multitick_lidar_tickrate_must_match_scanrate` for details and
the recommended remediation.

.. _isaac_sim_sensors_multitick_known_issue_radar_lidar_fif_race:

Radar + Lidar frames-in-flight race
-----------------------------------

A fatal crash from ``rtx.sensors.lidar.core.plugin`` may occur during the first 1-2
wall-clock seconds after starting simulation when a scene combines RTX Radar, RTX Lidar,
and Motion BVH. The crash is caused by a timing-dependent race in the RTX sensor
framework's frames-in-flight (FIF) scheduling, where the Lidar's per-frame trace begins
before its sensor profile has been initialized. Affected configurations crash
deterministically; unaffected hardware does not see the issue. The error appears as a
floating-point exception inside ``LidarRotary::openTrace`` or, less commonly, a
segmentation fault in the v3.0 sensor scheduler:

   .. code-block:: bash

       [Fatal] [carb.crashreporter-breakpad.plugin] Crashing: SIGFPE
       at rtx.sensors.lidar.core.plugin::LidarRotary::openTrace

Once the simulation has been running for ~1-2 wall-clock seconds without crashing, the
session is stable for the remainder of its lifetime.

Standalone Python workaround
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In standalone Python workflows, delay creating the render product for the Radar and
attaching any Annotators or Writers until after the frames-in-flight have stabilized.
Construct the Lidars normally before ``timeline.play()``, but construct only the
Radar's USD authoring object pre-play and defer the ``RadarSensor`` wrap until after a
short warmup window:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_multitick_rendering/defer_radar_after_lidar_warmup.py
    :language: python

The 5-frame warmup is conservative: it is one full rotation of the default 3-slot
frames-in-flight buffer plus a small margin. Heavier scenes may require a larger value.

.. _isaac_sim_sensors_multitick_known_issue_radar_lidar_fif_race_omnigraph_workaround:

OmniGraph workaround
^^^^^^^^^^^^^^^^^^^^

In OmniGraph workflows using the ``ROS2RtxRadarHelper`` node, you can stagger creating
the Radar's render product until after the Lidars have stabilized. Place an
``omni.graph.action.Countdown`` node between the ``OnPlaybackTick`` and the
``ROS2RtxRadarHelper`` node, setting its ``duration`` to ``5`` and its ``period`` to
``1``. The ``Countdown`` node's ``finished`` output triggers downstream graph execution
after ``duration`` ticks have elapsed, analogous to the 5-frame warmup in the standalone
Python workflow. You may need to increase the ``duration`` value based on your scene's
complexity and your hardware configuration.

.. figure:: /images/isim_6.0_ros_tut_gui_rtx_radar_countdown_workaround.png
    :align: center
    :width: 800
    :alt: RTX Radar crash workaround in OmniGraph, using Countdown node to stagger Radar writer attachment
