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

The ``isaacsim.sensors.rtx`` extension uses Omniverse Replicator to provide Annotators for RTX Lidar and Radar data collection.
Annotators can be attached to render products, attached to ``OmniSensor`` prims (for example, ``OmniLidar`` or ``OmniRadar``); for example,
when run in the *Script Editor*, the following snippet creates an ``OmniLidar`` prim at ``/lidar``, a render product for the sensor,
and attaches an ``IsaacExtractRTXSensorPointCloudNoAccumulator`` annotator to the render product.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_annotators/rtx_sensor_annotators.py
    :language: python

Alternatively, the ``LidarRtx`` class offers a single API for attaching any annotator to an ``OmniLidar`` prim
and collecting data. For example, in a standalone Python workflow, the following snippet creates an ``OmniLidar`` prim at ``/lidar``,
creates a render product for the sensor, and attaches an ``IsaacExtractRTXSensorPointCloudNoAccumulator`` annotator to it, then collects
data from the annotator on each simulation frame. Note that this snippet will not run in the script editor window.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_annotators/attach_the_render_product_after_the_annotator_is_i.py
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

Each ``isaacsim.sensors.rtx`` Annotator is associated with a specific ``isaacsim.sensors.rtx`` OmniGraph node, which is linked
in that Annotator's subsection below. The inputs and outputs of the Annotator are the same as the inputs and outputs of the
corresponding OmniGraph node.

.. note:: In |isaac-sim_short| 5.0, several existing ``isaacsim.sensors.rtx`` annotators were removed in favor of simpler
    annotators that can handle output from the new ``OmniLidar`` or ``OmniRadar`` prims, in addition to the
    deprecated ``Camera``-prim-based workflows. See :ref:`rtx_sensor_deprecated_annotators` for details.

    If the Lidar rotation rate is slower than the frame rate, data from Annotators for accumulated Lidar scans will contain returns from multiple frames. If the Lidar prim moves between frames, or objects
    move in the scene, the buffer might contain returns from before the Lidar or objects moved, causing points to appear as though they are "dragging" behind objects when
    viewed with the ``DebugDrawPointCloud`` or ``DebugDrawPointCloudBuffer`` writers.

    ``isaacsim.sensors.rtx`` annotators rely on the ``GenericModelOutput`` AOV from the ``OmniLidar`` prim being
    provided on device. If ``--/app/sensors/nv/lidar/outputBufferOnGPU`` or ``--/app/sensors/nv/radar/outputBufferOnGPU`` is
    set to ``false``, the annotators will not function correctly.

.. _rtx_sensor_IsaacCreateRTXLidarScanBuffer:

IsaacCreateRTXLidarScanBuffer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

If creating the Annotator through the ``LidarRtx`` class, this can be done as follows:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_annotators/note_this_must_be_done_before_attaching_the_annota.py
    :language: python

The node outputs data as pointers to buffers and the table below specifies the data type of each buffer, as well as any attributes to set on the ``OmniLidar`` prim or carb settings that are required for the desired output(s).
If the user does not set the required attributes or carb settings, the annotator will print a warning and will not output the desired data.

.. warning:: In |isaac-sim_short| 5.1 and earlier, the ``IsaacCreateRTXLidarScanBuffer`` node  included an ``outputNormal`` field, which has been deprecated. Use the ``outputHitNormal`` input instead.

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

IsaacComputeRTXLidarFlatScan
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``IsaacComputeRTXLidarFlatScan`` Annotator extracts depth and azimuth data from an accumulated 2D RTX Lidar scan.
It is associated with the |IsaacComputeRTXLidarFlatScan| node.

.. |IsaacComputeRTXLidarFlatScan| raw:: html

    <a href="../py/source/extensions/isaacsim.sensors.rtx/docs/ogn/OgnIsaacComputeRTXLidarFlatScan.html">IsaacComputeRTXLidarFlatScan</a>

.. warning:: The ``IsaacComputeRTXLidarFlatScan`` Annotator only works with ``OmniLidar`` prims (RTX Lidar) configured as 2D lidars, defined as having emitters only at elevation angle zero (0). It does not work with ``OmniRadar`` prims (RTX Radar) or 3D Lidars.

Even if ``--/app/sensors/nv/lidar/outputBufferOnGPU=true`` is set, ``IsaacComputeRTXLidarFlatScanSimulationTime`` output data will be on host memory.

.. _rtx_sensor_IsaacExtractRTXSensorPointCloud:

IsaacExtractRTXSensorPointCloudNoAccumulator
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``IsaacExtractRTXSensorPointCloud`` Annotator extracts the ``GenericModelOutput`` buffer's point cloud data
into a Cartesian vector ``data`` buffer every frame. It is associated with the |IsaacCreateRTXLidarScanBuffer| node, with ``enablePerFrameOutput`` set to ``true``.

.. note::

    * The ``IsaacExtractRTXSensorPointCloudNoAccumulator`` Annotator works with ``OmniLidar`` prims (RTX Lidar) and ``OmniRadar`` prims (RTX Radar).
    * |isaac-sim_short| 5.0 previously used the ``IsaacExtractRTXSensorPointCloud`` node for this annotator, but that node was removed after performance improvements were made to the ``IsaacCreateRTXLidarScanBuffer`` node.

.. _rtx_sensor_reading_gmo_buffer:

Reading Data from the ``GenericModelOutput`` Buffer
---------------------------------------------------

.. note:: |isaac-sim_short| 4.5 included the ``OgnIsaacReadRTXLidarData`` node, which provided an
    example of reading data from the ``GenericModelOutput`` buffer in Python. This node has been removed
    as of |isaac-sim_short| 5.0 and replaced by the utility module and functions described below.

The ``isaacsim.sensors.rtx.generic_model_output`` Python module provides APIs for inspecting the
``GenericModelOutput`` buffer, generated by the ``GenericModelOutput`` annotator.

For more information on the ``GenericModelOutput`` buffer, see |link_ext|.

.. |link_ext| raw:: html

    <a href="../py/docs/source/generic_model_output/generic_model_output.html" target="_blank">the API documentation.</a>

For an example of reading data from the ``GenericModelOutput`` buffer from |isaac-sim_short|, checkout the
standalone examples:

.. code-block:: bash

    # Lidar GMO inspection
    ./python.sh standalone_examples/api/isaacsim.sensors.rtx/inspect_lidar_gmo.py --aux-data-level FULL

    # Radar GMO inspection
    ./python.sh standalone_examples/api/isaacsim.sensors.rtx/inspect_radar_gmo.py

.. _rtx_sensor_resolving_object_ids:

Semantic Segmentation with RTX Sensor using Object IDs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``GenericModelOutput`` struct includes a ``objId`` field and the ``IsaacCreateRTXLidarScanBuffer`` node outputs an optional ``objectId`` output.

In both cases, the data is provided as a ``numpy`` array of ``dtype`` ``np.uint8``, and is only populated if ``--/rtx-transient/stableIds/enabled=true`` is set.
This data is meant to be interpreted as a sequence of 128-bit unsigned integers (effectively ``stride`` 16), which are stable, unique IDs corresponding to
unique prim paths in the scene. In other words, the ``i``-th 128-bit unsigned integer in the array corresponds to prim generating the ``i``-th return from the sensor.
This can be used for semantic segmentation of the scene, by mapping the object IDs to prim paths and then retrieving semantic labels from the prims.

The ``isaacsim.sensors.rtx.LidarRtx`` class provides two utility functions for resolving object IDs as prim paths.

First, ``LidarRtx.decode_stable_id_mapping`` resolves the output of the ``StableIdMap`` AOV (which can be generated from an ``OmniLidar``, ``OmniRadar``, or ``Camera`` prim)
as a Python ``dict`` mapping 128-bit unsigned integers to prim paths.

Second, ``LidarRtx.get_object_ids`` resolves the object ID array output from ``GenericModelOutput`` or ``IsaacCreateRTXLidarScanBuffer`` as 128-bit unsigned integers.

Refer to ``standalone_examples/api/isaacsim.sensors.rtx/resolve_lidar_object_ids.py`` for an example of using these functions to resolve object IDs as prim paths.

.. _rtx_sensor_deprecated_annotators:

Deprecated Annotators
---------------------

Several annotators have been removed and or replaced by the annotators described above, as of |isaac-sim_short| 5.0.

New annotator outputs are not guaranteed to be the same as the outputs of the deprecated annotators;
the table below describes affected annotators and how to replace them.

.. csv-table::
    :header: "Deprecated |isaac-sim_short| 4.5 Annotator", "Replacement", "Details"
    :widths: 35, 30, 35

    "``IsaacComputeRTXLidarFlatScanSimulationTime``", "``IsaacComputeRTXLidarFlatScan``", "The new annotator outputs the same data as the old annotator. To get an associated timestamp, use the ``IsaacReadSimulationTime`` annotator."
    "``IsaacComputeRTXLidarFlatScanSystemTime``", "``IsaacComputeRTXLidarFlatScan``", "The new annotator outputs the same data as the old annotator. To get an associated timestamp, use the ``IsaacReadSystemTime`` annotator."
    "``RtxSensorCpuIsaacComputeRTXLidarPointCloud``", "``IsaacExtractRTXSensorPointCloudNoAccumulator``", "The new annotator outputs the same data as the old annotator, excluding ``azimuth``, ``elevation``, and ``range``. These values can be computed from the Cartesian ``data`` buffer. The new annotator also automatically supports CPU or GPU output based on the ``--/app/sensors/nv/lidar/outputBufferOnGPU`` and ``--/app/sensors/nv/radar/outputBufferOnGPU`` settings, rather than Annotator type."
    "``RtxSensorGpuIsaacComputeRTXLidarPointCloud``", "``IsaacExtractRTXSensorPointCloudNoAccumulator``", "See above."
    "``RtxSensorCpuIsaacComputeRTXRadarPointCloud``", "``IsaacExtractRTXSensorPointCloudNoAccumulator``", "See above."
    "``RtxSensorGpuIsaacComputeRTXRadarPointCloud``", "``IsaacExtractRTXSensorPointCloudNoAccumulator``", "See above."
    "``IsaacReadRTXLidarData``", "``isaacsim.sensors.rtx.get_gmo_data`` utility.", "See :ref:`rtx_sensor_reading_gmo_buffer` for details."

