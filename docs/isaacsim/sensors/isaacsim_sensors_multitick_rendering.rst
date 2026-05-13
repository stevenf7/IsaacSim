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

How It Works
============

Before |isaac-sim_short|-6.0, every camera and RTX sensor rendered at the
simulation frame rate. With multi-tick rendering enabled, the renderer maintains independent
tick counters for each sensor and only renders a sensor when its tick interval has elapsed.

The ``omni:sensor:tickRate`` attribute on each sensor prim controls the render frequency in Hz.
A value of ``0`` (the default) puts the sensor in *autotrigger* mode, where it renders every
frame — the same behavior as before multi-tick rendering existed.

Performance Benefits
--------------------

- **Reduced GPU load**: Sensors that do not need to update every frame skip rendering entirely,
  freeing GPU resources for other sensors or simulation work.
- **Independent rates**: A safety-camera LiDAR running at 10 Hz no longer forces a navigation
  camera to also render at the physics rate.
- **Better scaling**: Scenes with many sensors (e.g. multi-robot fleets) see proportionally
  larger improvements because each sensor only consumes GPU time when it actually ticks.

Settings
========

Multi-tick rendering is controlled by two Carbonite settings that are set at application
startup in the base ``.kit`` file:

.. csv-table::
    :header: "Setting", "Default", "Description"
    :widths: 40, 10, 50

    "``/rtx/hydra/supportMultiTickRate``", "``true``", "Enable multi-tick rendering. Each sensor can render at its own tick rate."
    "``/rtx/rendering/perSensorTickTlas``", "``true``", "Build a per-sensor Top-Level Acceleration Structure (TLAS) on each sensor tick instead of once per frame."

These settings are set in ``isaacsim.exp.base.kit`` and are also passed as standard test
arguments to all extension tests.

To reproduce the |isaac-sim_short| 5.x render-every-frame behavior in 6.0 (for example to debug
a regression), launch with ``--/rtx/hydra/supportMultiTickRate=false``. Most other code paths
in 6.0 assume the global default and have not been validated with the setting disabled.

.. _isaac_sim_sensors_multitick_configuring_per_sensor_tick_rates:

Configuring Per-Sensor Tick Rates
=================================

Sensor tick rates are controlled through the ``OmniSensorAPI`` USD schema, which is applied
to Camera, OmniLidar, and OmniRadar prims. The shipped USD assets in |isaac-sim_short| 6.0
already have this schema applied with appropriate default tick rates.

Using the Isaac Sim Extension API
---------------------------------

The ``isaacsim.sensors.experimental.rtx`` extension provides Python APIs for creating
sensors with tick rates already configured:

.. code-block:: python

    from isaacsim.sensors.experimental.rtx import Lidar

    lidar = Lidar(
        path="/World/Lidar",
        tick_rate=10.0,
    )

For cameras:

.. code-block:: python

    from isaacsim.sensors.experimental.rtx import RtxCamera

    camera = RtxCamera(
        path="/World/Camera",
        tick_rate=30.0,
    )

Using OmniGraph
---------------

When using the ROS2, UCX, or HSB helper OmniGraph nodes, the sensor tick rate is read
from the ``omni:sensor:tickRate`` attribute on the sensor prim. No additional node
configuration is needed.

.. _isaac_sim_sensors_multitick_lidar_tickrate_must_match_scanrate:

OmniLidar Tick Rate Must Equal ``scanRateBaseHz``
-------------------------------------------------

.. warning::

    For ``OmniLidar`` prims, ``omni:sensor:tickRate`` **must** be set equal to
    ``omni:sensor:Core:scanRateBaseHz`` for scan accumulation and multi-tick rendering to
    behave correctly.

If the two values differ, the lidar model falls back to producing **partial scans every
frame** instead of accumulating to a full rotation (rotary lidars) or full azimuth sweep
(solid-state lidars). Downstream pipelines that assume a full scan per tick — including
``ROS2 RTX Lidar Helper`` ``laser_scan`` publishers, ``IsaacComputeRTXLidarFlatScan``, and
any consumer of accumulated ``GenericModelOutput`` data — silently see truncated output.
The renderer does not log an error in this case.

For example, the shipped ``Example_Rotary`` lidar config has ``scanRateBaseHz = 10``, so the
sensor must tick at 10 Hz:

.. code-block:: python

    from isaacsim.sensors.experimental.rtx import Lidar

    # Example_Rotary scans at 10 Hz; tick_rate must match.
    lidar = Lidar.create("/World/Lidar", config="Example_Rotary", tick_rate=10.0)

The same constraint applies to ``Example_Solid_State`` and to vendor configs in
:ref:`isaac_assets_nonvisual_sensors_rtx_lidar`. When wrapping an existing ``OmniLidar`` prim,
read ``omni:sensor:Core:scanRateBaseHz`` from the prim and pass that value as
``tick_rate``.

.. _isaac_sim_sensors_multitick_aux_output_level:

Auxiliary Output Level and the GenericModelOutput RenderVar
===========================================================

RTX Lidar, Radar, and Acoustic sensors emit a ``GenericModelOutput`` (GMO) AOV. The amount
of auxiliary data carried in each GMO frame is controlled by the
``_replicator:rendervar:GenericModelOutput:channels`` attribute on the sensor prim.

Setting the channels attribute in the UI
----------------------------------------

To set ``_replicator:rendervar:GenericModelOutput:channels`` on an OmniRadar prim from
the Isaac Sim UI:

#. Select the prim in the **Stage** window.
#. Open the **Property** tab.
#. Expand the **Array Properties** widget.
#. Click **Edit** on the ``_replicator:rendervar:GenericModelOutput:channels`` row.
#. Set the first field in the dialog to ``BASIC``.
#. Close the dialog to save the change.

.. figure:: /images/isim_6.0_sensors_multitick_gui_array_properties_channels.png
    :align: center
    :width: 800
    :alt: Setting the GenericModelOutput channels attribute on an OmniRadar prim via the Array Properties widget in the Property tab

How the attribute flows to the RenderVar
----------------------------------------

When ``omni.replicator.core`` adds a ``GenericModelOutput`` RenderVar to a render product
that is attached to an RTX sensor prim, it reads
``_replicator:rendervar:GenericModelOutput:channels`` from the sensor prim and copies the
value onto the RenderVar's ``channels`` attribute. The RTX Sensor SDK then uses that value
to decide which auxiliary fields to populate.

The ``aux_output_level`` constructor parameter on
:py:class:`isaacsim.sensors.experimental.rtx.Lidar`,
:py:class:`isaacsim.sensors.experimental.rtx.Radar`, and
:py:class:`isaacsim.sensors.experimental.rtx.Acoustic` is a convenience that authors
``_replicator:rendervar:GenericModelOutput:channels = [level]`` on the sensor prim. The
two paths are interchangeable; reading existing USD scenes is easier if you recognize the
underlying attribute.

Valid values are modality-specific:

.. csv-table::
    :header: "Modality", "Valid values"
    :widths: 30, 70

    "Lidar", "``NONE`` (default), ``BASIC``, ``EXTRA``, ``FULL``"
    "Radar", "``NONE`` (default), ``BASIC``"
    "Acoustic", "``NONE`` (default), ``BASIC``"

See :ref:`rtx_sensor_annotator_descriptions` for the per-level field listing.

Migration from previous releases
--------------------------------

Earlier releases used per-modality USD attributes for the same purpose. These attributes
have been removed from the schemas:

.. csv-table::
    :header: "Old attribute (removed)", "Replacement"
    :widths: 50, 50

    "``omni:sensor:Core:auxOutputType`` (Lidar)", "``_replicator:rendervar:GenericModelOutput:channels`` on the ``OmniLidar`` prim, or ``Lidar(..., aux_output_level='FULL')``."
    "``omni:sensor:WpmDmat:auxOutputType`` (Radar)", "``_replicator:rendervar:GenericModelOutput:channels`` on the ``OmniRadar`` prim, or ``Radar(..., aux_output_level='BASIC')``."

USD assets shipped with |isaac-sim_short| 6.0 have already been updated. Custom USD
scenes carrying the old attributes need to be migrated; the old attributes are silently
ignored by the new schemas.

.. note::

    ``RtxCamera`` removes ``_replicator:rendervar:GenericModelOutput:channels`` from the
    Camera prim during construction because cameras do not produce a GMO AOV. Camera prims
    therefore do not participate in the propagation behavior described in
    :ref:`isaac_sim_sensors_multitick_known_issue_gmo_channels`.

frameSkipCount Deprecation
==========================

In previous releases, publish rates for ROS2/UCX/HSB helper nodes were controlled by the
``frameSkipCount`` input on each helper node. This parameter is now **deprecated**.

With multi-tick rendering enabled globally, the correct way to control how often a sensor
publishes data is to set ``omni:sensor:tickRate`` on the sensor prim itself. This is more
efficient because the sensor does not render at all during skipped ticks, rather than
rendering and discarding the output.

The ``frameSkipCount`` parameter still works for backward compatibility, but a deprecation
warning is logged when a non-zero value is used. It will be removed in a future release.

The deprecation applies to every helper node that previously exposed ``frameSkipCount``:

- ``ROS2 Camera Helper`` (``isaacsim.ros2.bridge.ROS2CameraHelper``)
- ``ROS2 Camera Info Helper`` (``isaacsim.ros2.bridge.ROS2CameraInfoHelper``)
- ``ROS2 RTX Lidar Helper`` (``isaacsim.ros2.bridge.ROS2RtxLidarHelper``)
- ``UCX Camera Helper`` (``isaacsim.ucx.bridge.UCXCameraHelper``)
- ``HSB Camera Helper`` (``isaacsim.hsb.bridge.HSBCameraHelper``)

The newer ``ROS2 RTX Radar Helper`` (``isaacsim.ros2.bridge.ROS2RtxRadarHelper``) was
introduced after this deprecation and does not expose ``frameSkipCount`` at all.

Migration from Previous Releases
=================================

If you are upgrading from a release where multi-tick rendering was not enabled by default,
the following changes may affect your workflow.

General changes
---------------

1. **Update Camera and OmniSensor prims to work with multi-tick rendering.** Apply the
   ``OmniSensorAPI`` schema to ``Camera`` prims. This schema is already applied by default
   to ``OmniLidar``/``OmniRadar`` prims. Set the ``omni:sensor:tickRate`` attribute to
   control render frequency. Multi-tick rendering is transparent when sensors use the
   default ``omni:sensor:tickRate`` of ``0`` (autotrigger), which renders every frame.

2. **USD assets updated.** Shipped sensor assets now have the ``OmniSensorAPI`` schema
   applied. If you have custom USD assets with ``Camera`` or ``OmniLidar``/``OmniRadar``
   prims, apply the ``OmniSensorAPI`` schema and set ``omni:sensor:tickRate`` to control
   render frequency.

3. **frameSkipCount is deprecated.** Replace usage of ``frameSkipCount`` on ROS2/UCX/HSB
   helper nodes with ``omni:sensor:tickRate`` on the sensor prim.

4. **Test arguments updated.** Extension tests now include
   ``--/rtx/hydra/supportMultiTickRate=true`` and ``--/rtx/rendering/perSensorTickTlas=true``
   as standard arguments. Custom test configurations that previously added these arguments
   in dedicated ``[[test]]`` blocks can remove them.

5. **RTX Lidar accumulation moved to a USD attribute.** Lidar scan accumulation is now
   controlled by the ``omni:sensor:Core:accumulateOutputs`` attribute on the ``OmniLidar``
   prim. The deprecated ``isaacsim.sensors.rtx`` extension's
   ``IsaacExtractRTXSensorPointCloudNoAccumulator`` annotator and its
   ``IsaacCreateRTXLidarScanBuffer`` and ``IsaacComputeRTXLidarFlatScan`` nodes have been
   updated to read this attribute. The newer
   ``IsaacExtractRTXSensorPointCloud`` annotator and OmniGraph node live in
   ``isaacsim.sensors.rtx.nodes`` and assume the GMO buffer already contains either a full
   scan or a per-frame partial scan based on ``accumulateOutputs``.

6. **Replace single-render-product waits with full app updates.** The
   ``omni.syntheticdata.sensors.next_render_simulation_async`` helper (and any other helper
   that targets a single render product) does not advance per-sensor tick counters
   correctly under multi-tick rendering. Use
   ``isaacsim.core.experimental.utils.app.update_app_async`` instead, which performs full
   application update steps and ensures all sensor ticks are processed.

   *Before:*

   .. code-block:: python

       await omni.syntheticdata.sensors.next_render_simulation_async(
           [render_product_path], N
       )

   *After:*

   .. code-block:: python

       import isaacsim.core.experimental.utils.app as app_utils

       await app_utils.update_app_async(steps=N)

Per-modality migration
----------------------

The tables below list 5.x APIs/attributes/inputs and the recommended 6.0 replacement.

RTX Lidar
^^^^^^^^^

.. csv-table::
    :header: "5.x", "6.0 replacement", "Notes"
    :widths: 35, 40, 25

    "``IsaacSensorCreateRtxLidar`` Kit command", "``isaacsim.sensors.experimental.rtx.Lidar.create(path, config=...)``", "Returns a typed authoring object."
    "``omni:sensor:Core:auxOutputType`` USD attribute", "``_replicator:rendervar:GenericModelOutput:channels = [level]``, or ``Lidar(..., aux_output_level=level)``", "See :ref:`isaac_sim_sensors_multitick_aux_output_level`."
    "``omni.replicator.core`` writer name ``RtxLidar + ROS2PublishPointCloud``", "``RtxLidarROS2PublishPointCloud``", "Single-token writer name; same parameters."
    "``frameSkipCount`` on ``ROS2 RTX Lidar Helper``", "``omni:sensor:tickRate`` on the ``OmniLidar`` prim", "See :ref:`isaac_sim_sensors_multitick_lidar_tickrate_must_match_scanrate`."
    "``fullScan`` input on ``ROS2 RTX Lidar Helper``", "``omni:sensor:Core:accumulateOutputs`` on the ``OmniLidar`` prim", "Helper input is now ignored and logs a deprecation warning when set to ``False``."
    "``isaacsim.ros2.nodes.build_rtx_sensor_pointcloud_writer`` helper", "Set ``selectedMetadata`` on ``ROS2 RTX Lidar Helper``, or attach an ``RtxLidarROS2PublishPointCloud`` writer with the desired ``output*`` parameters", "The helper has been removed."
    "``IsaacExtractRTXSensorPointCloudNoAccumulator`` annotator", "``IsaacCreateRTXLidarScanBuffer`` (deprecated extension) with ``accumulateOutputs=False`` on the prim, or ``IsaacExtractRTXSensorPointCloud`` (``isaacsim.sensors.rtx.nodes``)", "Accumulation is now a USD attribute, not an annotator switch."

RTX Radar
^^^^^^^^^

.. csv-table::
    :header: "5.x", "6.0 replacement", "Notes"
    :widths: 35, 40, 25

    "``IsaacSensorCreateRtxRadar`` Kit command", "``isaacsim.sensors.experimental.rtx.Radar(path, ...)``", "Authoring class; supports ``aux_output_level``, ``tick_rate``."
    "``omni:sensor:WpmDmat:auxOutputType`` USD attribute", "``_replicator:rendervar:GenericModelOutput:channels = [level]``, or ``Radar(..., aux_output_level=level)``", "See :ref:`isaac_sim_sensors_multitick_aux_output_level`."
    "Manual ``frameSkipCount`` rate control", "``omni:sensor:tickRate`` on the ``OmniRadar`` prim", "``ROS2 RTX Radar Helper`` does not expose ``frameSkipCount``."

Cameras
^^^^^^^

.. csv-table::
    :header: "5.x", "6.0 replacement", "Notes"
    :widths: 35, 40, 25

    "Plain ``UsdGeom.Camera`` prim", "``isaacsim.sensors.experimental.rtx.RtxCamera(path, ...)``", "Authoring class applies ``OmniSensorAPI`` automatically."
    "``frameSkipCount`` on ``ROS2 Camera Helper`` / ``ROS2 Camera Info Helper``", "``omni:sensor:tickRate`` on the Camera prim (with ``OmniSensorAPI`` applied)", "Cameras must have ``OmniSensorAPI`` to participate in multi-tick scheduling."

UCX and HSB camera helpers
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. csv-table::
    :header: "5.x", "6.0 replacement", "Notes"
    :widths: 35, 40, 25

    "``frameSkipCount`` on ``UCX Camera Helper``", "``omni:sensor:tickRate`` on the Camera prim", "Helper still accepts ``frameSkipCount`` and logs a deprecation warning."
    "``frameSkipCount`` on ``HSB Camera Helper``", "``omni:sensor:tickRate`` on the Camera prim", "Helper still accepts ``frameSkipCount`` and logs a deprecation warning."

Custom render-rate scheduling
-----------------------------

When wiring up custom rendering schedules outside of the ``OmniSensorAPI`` workflow, set
the renderer dt directly:

.. code-block:: python

    from isaacsim.core.rendering_manager import RenderingManager

    RenderingManager.set_dt(1.0 / 60.0)

This sets the application's render-loop rate independently of the physics dt configured by
``SimulationManager.setup_simulation``. Per-sensor tick rates remain the recommended way to
control how often a specific sensor's GMO/Camera output is produced.

.. _isaac_sim_sensors_multitick_known_issues:

Known Issues
============

.. _isaac_sim_sensors_multitick_known_issue_gmo_channels:

Last-attach-wins propagation of GMO channels
--------------------------------------------

.. warning::

    The ``_replicator:rendervar:GenericModelOutput:channels`` attribute is currently
    **effectively global per render-product-attach event**. When two RTX sensors on the
    same stage author different values, only the **last** sensor to have a render product
    attached "wins" — every subsequent ``GenericModelOutput`` RenderVar uses that sensor's
    channels value, regardless of which sensor prim it was created from.

Concrete example. Suppose you have one ``Lidar`` with ``aux_output_level="FULL"`` and one
``Radar`` with ``aux_output_level="BASIC"`` on the same stage:

- If the **Radar** render product is created second, every GMO consumer (lidar and radar)
  sees ``BASIC`` channels. The lidar silently loses its ``FULL``-level fields.
- If the **Lidar** render product is created second, the radar GMO RenderVar inherits
  ``FULL``. The radar pipeline does not recognize ``FULL`` and produces **no auxiliary
  data at all** for that radar (no ``rv_ms``, no intensity, etc.).

Recommended workarounds:

- Keep all RTX sensors on a stage at the same ``aux_output_level``.
- Order render-product attachment so the sensor whose channels value you want to use is
  attached last.
- Split sensors with conflicting auxiliary-output requirements across separate stages or
  ``SimulationApp`` instances.

This issue is tracked separately and will be addressed in a future release. Cameras are
unaffected: ``RtxCamera`` removes the GMO channels attribute during construction because
Camera prims do not emit GMO AOVs.

OmniLidar partial-scan fallback
-------------------------------

If ``omni:sensor:tickRate`` is not equal to ``omni:sensor:Core:scanRateBaseHz`` on an
``OmniLidar`` prim, the sensor falls back to emitting partial scans every frame. See
:ref:`isaac_sim_sensors_multitick_lidar_tickrate_must_match_scanrate` for details and the
recommended remediation.

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
Construct the Lidars normally before ``timeline.play()``, but construct only the Radar's
USD authoring object pre-play and defer the ``RadarSensor`` wrap until after a short
warmup window:

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
Python workflow.

.. figure:: /images/isim_6.0_ros_tut_gui_rtx_radar_countdown_workaround.png
    :align: center
    :width: 800
    :alt: RTX Radar crash workaround in OmniGraph, using Countdown node to stagger Radar writer attachment
