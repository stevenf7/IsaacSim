..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaacsim_sensors_rtx_migration:

===========
RTX Sensors
===========

The deprecated ``isaacsim.sensors.rtx`` extension is replaced by ``isaacsim.sensors.experimental.rtx``. The replacement keeps the same sensor concepts (RTX Lidar, RTX Radar) but reshapes the Python API to mirror ``isaacsim.sensors.experimental.physics`` — array-form transforms, no command-based creation, and a split between authoring (``Lidar``/``Radar``/``Acoustic``) and runtime (``LidarSensor``/``RadarSensor``/``AcousticSensor``) classes. The previously-named "Ultrasonic" plugin is now exposed as ``Acoustic``/``AcousticSensor``.

.. _isaacsim_sensors_rtx_concept_mapping:

Concept mapping
===============

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - ``isaacsim.sensors.rtx`` (deprecated)
     - ``isaacsim.sensors.experimental.rtx``
   * - ``omni.kit.commands.execute("IsaacSensorCreateRtxLidar", path=..., parent=..., config=..., translation=..., orientation=..., variant=...)``
     - ``Lidar.create(path, config=..., translations=..., orientations=..., variant=...)`` (no command registration; authoring class only). Wrap with the runtime: ``LidarSensor(Lidar.create(...))``.
   * - ``omni.kit.commands.execute("IsaacSensorCreateRtxRadar", ...)``
     - ``Radar.create(path, ...)`` and wrap with ``RadarSensor(...)``.
   * - ``omni.kit.commands.execute("IsaacSensorCreateRtxUltrasonic", ...)``
     - ``Acoustic.create(path, ...)`` and wrap with ``AcousticSensor(...)``. The Omniverse plugin was renamed from "Ultrasonic"/"USS" to "Acoustic" (see :ref:`isaacsim_sensors_rtx_acoustic`); the new class authors ``OmniAcoustic`` prims with the ``OmniSensorGenericAcousticWpmAPI`` schema.
   * - ``omni.kit.commands.execute("IsaacSensorCreateRtxIDS", ...)``
     - **No equivalent in ``isaacsim.sensors.experimental.rtx`` today; may be supported in a future release.** In the meantime, continue to use the deprecated command or author the IDS occupancy prim directly in USD.
   * - ``LidarRtx(prim_path, name=..., position=..., orientation=..., config_file_name=...)``
     - ``LidarSensor(Lidar.create(path, config=..., translations=[[...]], orientations=[[...]]))``.
   * - Singular ``position=``, ``orientation=``, ``translation=`` constructor args
     - Plural ``positions=[[...]]``, ``translations=[[...]]``, ``orientations=[[...]]`` arrays. Shape ``(N, 3)`` / ``(N, 4)``; only ``N=1`` is supported per sensor.
   * - ``name=`` constructor parameter
     - Removed (was unused).
   * - ``LidarRtx.get_current_frame()``
     - ``LidarSensor.get_data("generic-model-output")`` (returns ``(wp.array, dict)``).
   * - ``LidarRtx.attach_annotator("IsaacComputeRTXLidarFlatScan" / "IsaacExtractRTXSensorPointCloudNoAccumulator" / "IsaacCreateRTXLidarScanBuffer" / "StableIdMap" / "GenericModelOutput")``
     - ``LidarSensor(..., annotators=[...])`` with short names ``"generic-model-output"`` / ``"stable-id-map"``. The deprecated Replicator annotators ``IsaacCreateRTXLidarScanBuffer`` and ``IsaacComputeRTXLidarFlatScan`` ship with the deprecated ``isaacsim.sensors.rtx`` extension; the active replacement annotator ``IsaacExtractRTXSensorPointCloud`` ships with the still-active ``isaacsim.sensors.rtx.nodes`` extension and is what ``LidarSensor`` / ``RadarSensor`` use under the hood. See :ref:`rtx_sensor_annotator_descriptions`.
   * - ``LidarRtx.initialize() / pause() / resume() / is_paused()``
     - Driven by ``omni.timeline.get_timeline_interface()``; not duplicated on ``LidarSensor``.
   * - ``LidarRtx.enable_visualization() / disable_visualization()``
     - ``LidarSensor.attach_writer("draw-point-cloud")`` / ``LidarSensor.detach_writer("draw-point-cloud")`` (registered by ``isaacsim.sensors.rtx.nodes``).
   * - ``LidarRtx.decode_stable_id_mapping()`` / ``LidarRtx.get_object_ids()`` (static)
     - ``parse_stable_id_map_data(...)`` and ``parse_object_ids(...)`` from ``isaacsim.sensors.experimental.rtx``.
   * - ``from isaacsim.sensors.rtx import get_gmo_data; gmo = get_gmo_data(rawPtr)``
     - ``data, info = sensor.get_data("generic-model-output"); gmo = parse_generic_model_output_data(data)``.
   * - ``isaacsim.sensors.rtx.nonvisual_materials`` (Python helpers + CSV-driven mapping)
     - USD attributes (``omni:simready:nonvisual:*``); see :ref:`isaacsim_sensors_rtx_materials`.

.. _isaacsim_sensors_rtx_code_examples:

Code examples
=============

**RTX Lidar — create and read**

Old (``isaacsim.sensors.rtx``):

.. literalinclude:: ../../snippets/sensors/isaacsim_sensors_rtx/migration_lidar_old.py
   :language: python

New (``isaacsim.sensors.experimental.rtx``):

.. literalinclude:: ../../snippets/sensors/isaacsim_sensors_rtx/migration_lidar_new.py
   :language: python

**RTX Radar — replace the create command**

Old:

.. literalinclude:: ../../snippets/sensors/isaacsim_sensors_rtx/migration_radar_old.py
   :language: python

New:

.. literalinclude:: ../../snippets/sensors/isaacsim_sensors_rtx/migration_radar_new.py
   :language: python

**Ultrasonic → Acoustic**

Old (Ultrasonic plugin):

.. literalinclude:: ../../snippets/sensors/isaacsim_sensors_rtx/migration_ultrasonic_old.py
   :language: python

New (``Acoustic`` class authors an ``OmniAcoustic`` prim with the WPM schema):

.. literalinclude:: ../../snippets/sensors/isaacsim_sensors_rtx/migration_acoustic_new.py
   :language: python

**Reading raw GMO data**

Old (helper that took a raw GMO pointer):

.. literalinclude:: ../../snippets/sensors/isaacsim_sensors_rtx/migration_gmo_old.py
   :language: python

New (runtime sensor owns the buffer; ``parse_*`` helpers are module-level):

.. literalinclude:: ../../snippets/sensors/isaacsim_sensors_rtx/migration_gmo_new.py
   :language: python

For the per-sensor APIs, see :ref:`isaacsim_sensors_rtx_lidar`, :ref:`isaacsim_sensors_rtx_radar`, and :ref:`isaacsim_sensors_rtx_acoustic`. For the non-visual materials migration (CSV → USD attributes), see :ref:`isaacsim_sensors_rtx_materials`. For the camera migration (deprecated ``isaacsim.sensors.camera`` → ``RtxCamera``/``CameraSensor``), see :ref:`isaacsim_sensors_camera_migration`.
