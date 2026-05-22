..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaacsim_sensors_physx_generic_migration:

====================
PhysX Generic Sensor
====================

The |physx| generic sensor is deprecated. Use the :ref:`Physics Raycast Sensor <isaacsim_sensors_physics_raycast>` (``isaacsim.sensors.experimental.physics.RaycastSensor``) as the replacement. The raycast sensor accepts explicit per-ray origin offsets and direction vectors, making it a direct replacement for custom scanning patterns.

.. _isaacsim_sensors_physx_generic_concept_mapping:

Concept mapping
===============

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - |physx| Generic Sensor
     - Physics Raycast Sensor
   * - ``sensor_pattern`` (Nx2 azimuth/zenith array)
     - ``rayDirections`` (Nx3 Cartesian direction vectors). Convert azimuth/zenith to Cartesian: ``dx = cos(zenith) * cos(azimuth)``, ``dy = cos(zenith) * sin(azimuth)``, ``dz = sin(zenith)``.
   * - ``origin_offsets`` (Nx3 array)
     - ``rayOrigins`` (Nx3 array). Same semantics.
   * - ``batch_size`` / ``sampling_rate`` / streaming mode
     - ``rayTimeOffsets`` (per-ray time offsets in seconds). The sensor fires only rays whose time offsets fall within the current physics step, producing a sweeping pattern without manual batching.
   * - ``_range_sensor`` Python interface
     - ``RaycastSensor`` class.
   * - ``send_next_batch()`` / ``set_next_batch_rays()``
     - Not needed. All rays are defined at creation time and the sensor handles timing internally via ``rayTimeOffsets``.

.. _isaacsim_sensors_physx_generic_interactive_example:

Interactive example
===================

The **Physics Raycast Sensor** example demonstrates all three sensor configurations (solid state, rotating, and beam curtain) in a single scene:

- **GUI**: Open **Robotics Examples > Sensors > Physics Raycast Sensor** and click **Load Scene**.
- **Source code**: ``source/extensions/isaacsim.sensors.physics.examples/isaacsim/sensors/physics/examples/raycast_sensor.py``

See :ref:`isaacsim_sensors_physics_raycast` for the full documentation, including Python API usage and OmniGraph workflows.
