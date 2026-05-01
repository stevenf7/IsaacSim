..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaacsim_sensors_physx_lightbeam:

========================
|physx| lightbeam sensor
========================

.. deprecated:: 6.0
   The |physx| sensor extensions (``isaacsim.sensors.physx``) are deprecated. Use
   ``isaacsim.sensors.experimental.physics.RaycastSensor`` as the replacement for raycast-based sensing.
   For lightbeam/safety-curtain specific functionality, consider using the ``RaycastSensor`` with
   appropriate configuration.
   See the `isaacsim.sensors.experimental.physics API Documentation <../py/source/extensions/isaacsim.sensors.experimental.physics/docs/index.html>`_.

The |physx| lightbeam sensor in |isaac-sim_short| uses |physx| raycasts to determine if an object has intersected a light beam.
You can specify the number of rays and height to create a safety light "curtain" of lightbeam sensors.

See the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim_short| conventions.

.. _isaacsim_sensors_physx_lightbeam_example:

Examples
===================

- |physx| Lightbeam Sensor example: **Robotics Examples > Sensors > Lightbeam**

To run the example:

#. Activate **Robotics Examples** tab from **Windows** > **Examples** > **Robotics Examples**.
#. Click **Robotics Examples > Sensors > Lightbeam**.
#. Verify that you have a window containing empty data for each lightbeam, which populates with data after you press **Play**. It shows if each beam was hit, the linear depth of the hit, and the exact hit position in ``xyz``.
#. Press the **Play** button to begin simulating.
#. Press :code:`SHIFT + LEFT_CLICK` to drag the cube or sensor around and see changes in the readings.

.. image:: /images/isim_4.5_full_tut_viewport_lightbeam_sensor.gif
    :align: center
    :width: 100%
    :alt: Lightbeam sensor example viewport.


.. _isaacsim_sensors_physx_lightbeam_migration:

Migrating to the physics raycast sensor
========================================

The |physx| lightbeam sensor is deprecated. Use the :ref:`Physics Raycast Sensor <isaacsim_sensors_physics_raycast>` (``isaacsim.sensors.experimental.physics.RaycastSensor``) configured as a beam curtain to achieve the same functionality.

.. _isaacsim_sensors_physx_lightbeam_concept_mapping:

Concept mapping
---------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - |physx| Lightbeam Sensor
     - Physics Raycast Sensor
   * - ``numRays``
     - Length of the ``rayOrigins`` / ``rayDirections`` arrays. Create one entry per beam.
   * - ``curtainLength`` / ``curtainAxis``
     - ``rayOrigins``. Spread ray origins along the curtain axis. For example, for a vertical curtain of height *h* with *N* beams: ``origins[i] = [0, 0, -h/2 + h * i / (N-1)]``.
   * - ``forwardAxis``
     - ``rayDirections``. Set all direction vectors to the forward axis. For example, ``[1, 0, 0]`` for a curtain firing along the X axis.
   * - ``minRange`` / ``maxRange``
     - ``minRange`` / ``maxRange``. Same semantics.
   * - Per-beam hit / depth / position data
     - ``RaycastSensor.get_sensor_reading()`` returns per-ray depths, hit positions, and hit normals.

.. _isaacsim_sensors_physx_lightbeam_interactive_example:

Interactive example
-------------------

The **Physics Raycast Sensor** example includes a beam curtain sensor configuration with parallel vertical rays:

- **GUI**: Open **Robotics Examples > Sensors > Physics Raycast Sensor** and click **Load Scene**.
- **Source code**: ``source/extensions/isaacsim.sensors.physics.examples/isaacsim/sensors/physics/examples/raycast_sensor.py``

See :ref:`isaacsim_sensors_physics_raycast` for the full documentation, including Python API usage and OmniGraph workflows.

