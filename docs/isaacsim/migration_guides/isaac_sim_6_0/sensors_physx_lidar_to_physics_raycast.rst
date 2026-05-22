..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaacsim_sensors_physx_lidar_migration:

===========
PhysX Lidar
===========

The |physx| Lidar sensor is deprecated. Use the :ref:`Physics Raycast Sensor <isaacsim_sensors_physics_raycast>` (``isaacsim.sensors.experimental.physics.RaycastSensor``) as the replacement for rotating raycast-based lidar.

.. _isaacsim_sensors_physx_lidar_concept_mapping:

Concept mapping
===============

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - |physx| Lidar
     - Physics Raycast Sensor
   * - ``rotationRate``
     - ``rayTimeOffsets``. Distribute rays across azimuthal columns and assign each column a time offset within the sweep period (``1.0 / rotation_rate``). The sensor fires only the rays whose offsets fall within the current physics step.
   * - Horizontal / vertical resolution
     - ``rayDirections``. Compute Cartesian direction vectors for each beam at the desired azimuth and elevation angles.
   * - ``minRange`` / ``maxRange``
     - ``minRange`` / ``maxRange``. Same semantics.
   * - ``drawLines``
     - Use the **Debug Draw RayCast** OmniGraph node connected to the **Isaac Read Physics Raycast Sensor** node outputs.
   * - ``_range_sensor`` Python interface (``get_linear_depth_data``, ``get_point_cloud_data``)
     - ``RaycastSensor.get_sensor_reading()`` returns depths, hit positions, hit normals, and optionally hit prim paths.
   * - ``enable_semantics`` / ``get_prim_data``
     - ``reportHitPrimPaths`` attribute. When enabled, the sensor reading includes the USD prim path of each hit surface.
   * - Setting ``rotationRate`` to ``0.0`` (fire all rays every step)
     - Omit ``rayTimeOffsets``. Without time offsets all rays fire every physics step.

.. _isaacsim_sensors_physx_lidar_interactive_example:

Interactive example
===================

The **Physics Raycast Sensor** example includes a rotating sensor configuration with time offsets that produces a 360-degree sweep:

- **GUI**: Open **Robotics Examples > Sensors > Physics Raycast Sensor** and click **Load Scene**.
- **Source code**: ``source/extensions/isaacsim.sensors.physics.examples/isaacsim/sensors/physics/examples/raycast_sensor.py``

See :ref:`isaacsim_sensors_physics_raycast` for the full documentation, including Python API usage and OmniGraph workflows.
