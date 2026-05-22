..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaacsim_sensors_camera_migration:

==============
Camera Sensors
==============

The deprecated ``isaacsim.sensors.camera`` extension is replaced by ``isaacsim.sensors.experimental.rtx``. The replacement keeps the same camera concepts (single camera, batched camera views, single-view depth sensor) but reshapes the Python API to mirror ``isaacsim.sensors.experimental.physics`` — array-form transforms, no command-based creation, and a split between authoring (``RtxCamera``) and runtime (``CameraSensor``, ``TiledCameraSensor``, ``SingleViewDepthCameraSensor``) classes.

.. _isaacsim_sensors_camera_concept_mapping:

Concept mapping
===============

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - ``isaacsim.sensors.camera`` (deprecated)
     - ``isaacsim.sensors.experimental.rtx``
   * - ``Camera(prim_path, name, frequency, dt, resolution, position, orientation, translation, render_product_path, annotator_device)``
     - ``CameraSensor(RtxCamera(path, ...), resolution=(W, H), annotators=[...])``. The ``frequency`` / ``dt`` knobs map to ``RtxCamera(tick_rate=...)`` (Hz). ``annotator_device`` maps to the CPU vs CUDA selection ``CameraSensor`` performs in ``attach_annotators``.
   * - Singular ``position=`` / ``orientation=`` / ``translation=`` constructor args
     - Plural ``positions=[[...]]`` / ``orientations=[[...]]`` / ``translations=[[...]]`` arrays on ``RtxCamera``. Shape ``(N, 3)`` / ``(N, 4)``; only ``N=1`` is supported per camera.
   * - ``name=`` constructor parameter
     - Removed (was unused).
   * - ``Camera.add_*_to_frame()`` / ``Camera.get_current_frame()`` (legacy frame-dict APIs)
     - ``CameraSensor(annotators=[...])`` plus ``CameraSensor.get_data("annotator-name")``. Each annotator is requested explicitly; data is returned per annotator instead of as a frame dict.
   * - ``Camera`` ``fisheyePolynomial`` distortion APIs
     - ``RtxCamera(schemas=["OmniLensDistortionOpenCvFisheyeAPI"], attributes={...})`` (or the OpenCV pinhole equivalent). See :ref:`isaacsim_sensors_camera_calibration_and_camera_lens_distortion_models` for the supported schemas and the deprecation note on the legacy distortion attributes.
   * - ``CameraView(prim_paths_expr, name, camera_resolution, output_annotators, positions, translations, orientations, scales, visibilities, reset_xform_properties)``
     - ``TiledCameraSensor(paths=[...], resolution=(W, H), annotators=[...])``. The ``prim_paths_expr`` regex selection becomes an explicit list of camera prim paths (or an ``isaacsim.core.experimental.objects.Camera`` instance). ``output_annotators`` maps directly to ``annotators=``.
   * - ``SingleViewDepthSensor(prim_path, asset_path, position, translation, orientation)``
     - ``SingleViewDepthCameraSensor(RtxCamera.create(path, usd_path=asset_path, translations=[[...]], orientations=[[...]]), resolution=(W, H), annotators=["depth_sensor_distance", "depth_sensor_imager", "depth_sensor_point_cloud_color", "depth_sensor_point_cloud_position"])``. Post-processing setters (``set_sensor_baseline``, ``set_sensor_disparity_confidence``, etc.) keep the same names.

.. _isaacsim_sensors_camera_code_examples:

Code examples
=============

**Camera — create and read RGB**

Old (``isaacsim.sensors.camera``):

.. literalinclude:: ../../snippets/sensors/isaacsim_sensors_camera/migration_camera_old.py
   :language: python

New (``isaacsim.sensors.experimental.rtx``):

.. literalinclude:: ../../snippets/sensors/isaacsim_sensors_camera/migration_camera_new.py
   :language: python

**CameraView → TiledCameraSensor — batched read**

Old (``isaacsim.sensors.camera``):

.. literalinclude:: ../../snippets/sensors/isaacsim_sensors_camera/migration_cameraview_old.py
   :language: python

New (``isaacsim.sensors.experimental.rtx`` — explicit path list, or pass a ``Camera`` object):

.. literalinclude:: ../../snippets/sensors/isaacsim_sensors_camera/migration_tiledcamera_new.py
   :language: python

For the per-class API surface, see the **Overview** and **How to Collect Data from a Camera** sections in :ref:`isaacsim_sensors_camera`. For the broader RTX-sensor migration (``isaacsim.sensors.rtx`` → ``isaacsim.sensors.experimental.rtx`` for Lidar / Radar / Acoustic), see :ref:`isaacsim_sensors_rtx_migration`.
