..
   Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _rtx_sensor_annotator_descriptions:

=====================
RTX Sensor Annotators
=====================

The ``isaacsim.sensors.experimental.rtx`` and ``isaacsim.sensors.rtx.nodes`` extensions use Omniverse Replicator to provide Annotators for RTX Lidar and Radar data collection.

The recommended approach is to use the ``LidarSensor`` or ``RadarSensor`` classes, which manage annotators and render products automatically:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_annotators/collect_data_with_lidar_sensor.py
    :language: python

Time Behavior of RTX Sensor Annotators
--------------------------------------

.. warning:: RTX Sensor Annotators rely on the simulation timeline to collect data. If the timeline is not playing (for example, if the simulation is paused or stopped), the annotators will not collect data.

The ``GenericModelOutput`` AOV produced by RTX Sensors contains an internal timestamp, which increases monotonically starting when ``App Ready`` appears in the simulation logs. This timestamp is
independent of the animation timeline (``omni.timeline``), so the sensor timestamp will continue to increase even if the timeline is paused or stopped. This AOV feeds into all other RTX Sensor Annotators.

If the user pauses the timeline, then resumes, timestamps in the ``GenericModelOutput`` point cloud (for example, the ``timestamp`` field of ``IsaacCreateRTXLidarScanBuffer`` below) may be discontinuous. This also means the simulation must be
stepped using ``omni.kit.app.get_app().update`` or ``omni.kit.app.get_app().next_update_async()`` rather than ``omni.replicator.core.orchestrator.step()`` or ``omni.replicator.core.orchestrator.step_async()``
when collecting data using these Annotators.

.. note:: |isaac-sim_short| APIs for controlling the simulation state use the former two methods rather than the latter two.

.. _rtx_sensor_annotators:

Annotators
----------

.. _rtx_sensor_IsaacExtractRTXSensorPointCloud:

IsaacExtractRTXSensorPointCloud
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``IsaacExtractRTXSensorPointCloud`` Annotator extracts the ``GenericModelOutput`` buffer's point cloud data
into a Cartesian (x, y, z) buffer every frame. It is provided by the ``isaacsim.sensors.rtx.nodes`` extension.

This annotator works with both ``OmniLidar`` (RTX Lidar) and ``OmniRadar`` (RTX Radar) prims.
It performs spherical-to-Cartesian conversion when the ``GenericModelOutput`` buffer contains spherical coordinates,
and outputs a sensor-to-world transform matrix.

The ``RtxSensorDebugDrawPointCloud`` Replicator Writer (also from ``isaacsim.sensors.rtx.nodes``)
can be used to visualize the point cloud in the viewport.

**Using with the runtime sensor classes**

When ``isaacsim.sensors.rtx.nodes`` is enabled, a writer named ``"draw-point-cloud"``
becomes available on ``LidarSensor``, ``RadarSensor``, and ``AcousticSensor``.
Pass ``writers=["draw-point-cloud"]`` to attach the debug draw writer:

.. code-block:: python

    from isaacsim.sensors.experimental.rtx import LidarSensor

    sensor = LidarSensor("/World/lidar", annotators=[], writers=["draw-point-cloud"])

**Using with RTX Radar**

The annotator works identically with ``OmniRadar`` prims. Remember that Motion BVH must be enabled for RTX Radar:

.. code-block:: python

    import numpy as np
    import omni.replicator.core as rep
    from isaacsim.sensors.experimental.rtx import Radar

    radar = Radar("/World/radar", tick_rate=20, translations=np.array([0, 0, 1.0]))
    render_product = rep.create.render_product(radar.paths[0], resolution=(1, 1))

    writer = rep.writers.get("RtxSensorDebugDrawPointCloud")
    writer.initialize(size=0.2, color=[1.0, 0.3, 0.1, 1.0])  # orange, larger points
    writer.attach([render_product.path])

**Auxiliary data**

When using the ``LidarSensor`` or ``RadarSensor`` classes, auxiliary data (intensity, emitter IDs, material IDs, etc.)
is available directly through the ``GenericModelOutput`` buffer via ``parse_generic_model_output_data``.
The ``_replicator:rendervar:GenericModelOutput:channels`` attribute on the sensor prim controls which auxiliary fields are populated:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_annotators/create_lidar_sensor_with_aux_output.py
    :language: python

.. _rtx_sensor_reading_gmo_buffer:

Reading Data from the ``GenericModelOutput`` Buffer
---------------------------------------------------

.. note:: |isaac-sim_short| 4.5 included the ``OgnIsaacReadRTXLidarData`` node, which provided an
    example of reading data from the ``GenericModelOutput`` buffer in Python. This node has been removed
    as of |isaac-sim_short| 5.0 and replaced by the utility module and functions described below.

The ``isaacsim.sensors.experimental.rtx.generic_model_output`` Python module provides APIs for inspecting the
``GenericModelOutput`` buffer, generated by the ``GenericModelOutput`` annotator. The ``parse_generic_model_output_data``
utility function from ``isaacsim.sensors.experimental.rtx`` provides a convenient way to parse annotator output.

For more information on the ``GenericModelOutput`` buffer, see |link_ext|.

.. |link_ext| raw:: html

    <a href="../py/docs/source/generic_model_output/generic_model_output.html" target="_blank">the API documentation.</a>

For an example of reading data from the ``GenericModelOutput`` buffer from |isaac-sim_short|, checkout the
standalone examples:

.. code-block:: bash

    # Lidar GMO inspection
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/inspect_lidar_gmo.py --aux-data-level FULL

    # Radar GMO inspection
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/inspect_radar_gmo.py

.. _rtx_sensor_resolving_object_ids:

Semantic Segmentation with RTX Sensor using Object IDs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``GenericModelOutput`` struct includes an ``objId`` field containing per-return object identifiers.

The data is provided as a ``numpy`` array of ``dtype`` ``np.uint8``, and is only populated if ``--/rtx-transient/stableIds/enabled=true`` is set.
This data is meant to be interpreted as a sequence of 128-bit unsigned integers (effectively ``stride`` 16), which are stable, unique IDs corresponding to
unique prim paths in the scene. In other words, the ``i``-th 128-bit unsigned integer in the array corresponds to prim generating the ``i``-th return from the sensor.
This can be used for semantic segmentation of the scene, by mapping the object IDs to prim paths and then retrieving semantic labels from the prims.

The ``isaacsim.sensors.experimental.rtx`` extension provides two utility functions for resolving object IDs as prim paths.

``parse_stable_id_map_data`` resolves the output of the ``StableIdMap`` AOV (which can be generated from an ``OmniLidar`` or ``OmniRadar`` prim)
as a Python ``dict`` mapping stable IDs to prim paths.

``parse_generic_model_output_data`` provides access to the ``objId`` field in the ``GenericModelOutput`` buffer, which contains 128-bit object IDs.

Refer to ``standalone_examples/api/isaacsim.sensors.experimental.rtx/resolve_lidar_object_ids.py`` for an example of using these functions to resolve object IDs as prim paths.

.. _rtx_sensor_deprecated_annotators:

Deprecated Annotators
---------------------

.. warning::

    The following annotators are provided by the deprecated ``isaacsim.sensors.rtx`` extension
    and will be removed in a future release. Use ``IsaacExtractRTXSensorPointCloud`` (from
    ``isaacsim.sensors.rtx.nodes``) with the ``LidarSensor`` and ``RadarSensor`` runtime
    classes (from ``isaacsim.sensors.experimental.rtx``) instead.

.. _rtx_sensor_IsaacCreateRTXLidarScanBuffer:

IsaacCreateRTXLidarScanBuffer *(deprecated)*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``IsaacCreateRTXLidarScanBuffer`` Annotator accumulates frames of data from an ``OmniLidar`` prim into a single scan,
and provides the accumulated scan data as outputs. It is associated with the |IsaacCreateRTXLidarScanBuffer| node.

.. |IsaacCreateRTXLidarScanBuffer| raw:: html

    <a href="../py/source/extensions/isaacsim.sensors.rtx/docs/ogn/OgnIsaacCreateRTXLidarScanBuffer.html">IsaacCreateRTXLidarScanBuffer</a>

.. warning:: The ``IsaacCreateRTXLidarScanBuffer`` Annotator only works with ``OmniLidar`` prims (RTX Lidar). It does not work with ``OmniRadar`` prims (RTX Radar).

By default the node outputs a 3D Cartesian point cloud, and
can optionally output the following data if the user sets the corresponding input flag to ``True`` when initializing the Annotator.

If creating the Annotator directly using the Replicator API, this can be done as follows:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_annotators/isaaccreatertxlidarscanbuffer.py
    :language: python

The node outputs data as pointers to buffers and the table below specifies the data type of each buffer, as well as any attributes to set on the ``OmniLidar`` prim or carb settings that are required for the desired output(s).
If the user does not set the required attributes or carb settings, the annotator will print a warning and will not output the desired data.

.. csv-table::
    :header: "Output", "Type", "Description", "Notes"
    :widths: 15, 10, 40, 35

    "``data``", "``float3``", "3D Cartesian point cloud.", "Always provided."
    "``azimuth``", "``float``", "Azimuth of each return, in degrees.", "Provided if ``outputAzimuth`` is set to ``true``."
    "``elevation``", "``float``", "Elevation of each return, in degrees.", "Provided if ``outputElevation`` is set to ``true``."
    "``distance``", "``float``", "Range of each return, in world units (by default, meters).", "Provided if ``outputDistance`` is set to ``true``."
    "``intensity``", "``float``", "Intensity of each return, normalized as described `here <https://docs.omniverse.nvidia.com/kit/docs/omni.sensors.nv.lidar/latest/lidar_extension.html#intensity-defining-attributes>`_.", "Provided if ``outputIntensity`` is set to ``true``."
    "``timestamp``", "``uint64``", "Timestamp of each return, in nanoseconds since the start of the simulation.", "Provided if ``outputTimestamp`` is set to ``true``."
    "``emitterId``", "``uint32``", "ID of the emitter that emitted the return.", "Provided if ``outputEmitterId`` is set to ``true``, and ``omni:sensor:Core:auxOutputType`` is set to ``BASIC`` (or higher) on the ``OmniLidar`` prim."
    "``channelId``", "``uint32``", "ID of the channel the return was generated on.", "Provided if ``outputChannelId`` is set to ``true``, and ``omni:sensor:Core:auxOutputType`` is set to ``BASIC`` (or higher) on the ``OmniLidar`` prim."
    "``materialId``", "``uint32``", "ID of the material of the object that generated the return.", "Provided if ``outputMaterialId`` is set to ``true``, and ``omni:sensor:Core:auxOutputType`` is set to ``EXTRA`` (or higher) on the ``OmniLidar`` prim. Refer to :ref:`isaacsim_sensors_rtx_materials` for more details on how material IDs are computed."
    "``tickId``", "``uint32``", "ID of the tick the return was generated on.", "Provided if ``outputTickId`` is set to ``true``, and ``omni:sensor:Core:auxOutputType`` is set to ``BASIC`` (or higher) on the ``OmniLidar`` prim."
    "``hitNormal``", "``float3``", "Normal to the surface of the object that generated the return.", "Provided if ``outputHitNormal`` is set to ``true``, ``omni:sensor:Core:auxOutputType`` is set to ``FULL`` on the ``OmniLidar`` prim, and ``--/app/sensors/nv/lidar/publishNormals=true`` is set."
    "``velocity``", "``float3``", "Velocity of the object that generated the return.", "Provided if ``outputVelocity`` is set to ``true``, and ``omni:sensor:Core:auxOutputType`` is set to ``FULL`` on the ``OmniLidar`` prim."
    "``objectId``", "``uint8``", "ID of the object that generated the return.", "Provided if ``outputObjectId`` is set to ``true``, and ``omni:sensor:Core:auxOutputType`` is set to ``EXTRA`` (or higher) on the ``OmniLidar`` prim, and ``--/rtx-transient/stableIds/enabled=true`` is set. Object ID is a stable, unique 128-bit unsigned integer mapping to the prim path of the object that generated the corresponding return. See :ref:`rtx_sensor_resolving_object_ids` for more details."
    "``echoId``", "``uint8``", "Indicates which echo the return represents in a multi-echo Lidar configuration.", "Provided if ``outputEchoId`` is set to ``true``, and ``omni:sensor:Core:auxOutputType`` is set to ``BASIC`` (or higher) on the ``OmniLidar`` prim."
    "``tickState``", "``uint8``", "Indicates the state of the tick the return was generated on.", "Provided if ``outputTickState`` is set to ``true``, and ``omni:sensor:Core:auxOutputType`` is set to ``BASIC`` (or higher) on the ``OmniLidar`` prim."

.. warning:: Enabling nonzero ``normal`` output by setting ``--/app/sensors/nv/lidar/publishNormals=true`` will increase VRAM usage and might negatively impact performance.

.. _rtx_sensor_IsaacComputeRTXLidarFlatScan:

IsaacComputeRTXLidarFlatScan *(deprecated)*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``IsaacComputeRTXLidarFlatScan`` Annotator extracts depth and azimuth data from an accumulated 2D RTX Lidar scan.
It is associated with the |IsaacComputeRTXLidarFlatScan| node.

.. |IsaacComputeRTXLidarFlatScan| raw:: html

    <a href="../py/source/extensions/isaacsim.sensors.rtx/docs/ogn/OgnIsaacComputeRTXLidarFlatScan.html">IsaacComputeRTXLidarFlatScan</a>

.. warning:: The ``IsaacComputeRTXLidarFlatScan`` Annotator only works with ``OmniLidar`` prims (RTX Lidar) configured as 2D lidars, defined as having emitters only at elevation angle zero (0). It does not work with ``OmniRadar`` prims (RTX Radar) or 3D Lidars.

.. _rtx_sensor_IsaacExtractRTXSensorPointCloudNoAccumulator:

IsaacExtractRTXSensorPointCloudNoAccumulator *(deprecated)*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Per-frame point cloud extraction from the ``GenericModelOutput`` buffer. Works with ``OmniLidar`` and ``OmniRadar`` prims.
Replaced by ``IsaacExtractRTXSensorPointCloud`` from ``isaacsim.sensors.rtx.nodes``.

