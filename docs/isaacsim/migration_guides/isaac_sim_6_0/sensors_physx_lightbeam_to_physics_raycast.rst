..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaacsim_sensors_physx_lightbeam_migration:

===============
PhysX Lightbeam
===============

The |physx| lightbeam sensor is deprecated. Use the :ref:`Physics Raycast Sensor <isaacsim_sensors_physics_raycast>` (``isaacsim.sensors.experimental.physics.RaycastSensor``) configured as a beam curtain to achieve the same functionality.

.. _isaacsim_sensors_physx_lightbeam_concept_mapping:

Concept mapping
===============

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - |physx| Lightbeam Sensor
     - Physics Raycast Sensor
   * - ``numRays``
     - Length of the ``rayOrigins`` / ``rayDirections`` arrays. Create one entry per beam.
   * - ``curtainLength`` / ``curtainAxis``
     - ``rayOrigins``. Spread ray origins along the curtain axis. For a vertical curtain of height *h* with *N* ≥ 2 beams: ``origins[i] = [0, 0, -h/2 + h * i / (N-1)]``. For the single-beam case (``N == 1``, the legacy default in ``SensorSchema.usda``) use ``origins = [[0, 0, 0]]``.
   * - ``forwardAxis``
     - ``rayDirections``. Set all direction vectors to the forward axis. For example, ``[1, 0, 0]`` for a curtain firing along the X axis.
   * - ``minRange`` / ``maxRange``
     - ``minRange`` / ``maxRange``. Same semantics.
   * - Per-beam hit / depth / position data
     - ``RaycastSensor.get_sensor_reading()`` returns per-ray depths, hit positions, and hit normals.

.. _isaacsim_sensors_physx_lightbeam_interactive_example:

Interactive example
===================

The **Physics Raycast Sensor** example includes a beam curtain sensor configuration with parallel vertical rays:

- **GUI**: Open **Robotics Examples > Sensors > Physics Raycast Sensor** and click **Load Scene**.
- **Source code**: ``source/extensions/isaacsim.sensors.physics.examples/isaacsim/sensors/physics/examples/raycast_sensor.py``

See :ref:`isaacsim_sensors_physics_raycast` for the full documentation, including Python API usage and OmniGraph workflows.
