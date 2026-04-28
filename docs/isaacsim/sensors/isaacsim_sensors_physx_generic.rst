..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaacsim_sensors_physx_generic:

======================
|physx| Generic Sensor
======================

.. deprecated:: 6.0
   The |physx| sensor extensions (``isaacsim.sensors.physx``) are deprecated. Use
   ``isaacsim.sensors.experimental.physics.RaycastSensor`` as the replacement.
   See the `isaacsim.sensors.experimental.physics API Documentation <../py/source/extensions/isaacsim.sensors.experimental.physics/docs/index.html>`_.

The |physx| generic sensor in |isaac-sim_short| uses |physx| raycasts to measure depth between two prims. It demonstrates
how to build a |physx|-based sensor in Isaac Sim to measure ground truth depth.

See the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim_short| conventions.

GUI
===

.. _isaacsim_sensors_physx_generic_example:

|physx| Generic Sensor Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To run the |physx| generic sensor example:

#. Activate **Robotics Examples** tab from **Windows** > **Examples** > **Robotics Examples**.
#. Click **Robotics Examples** > **Sensors** > **Custom Pattern Range Sensor**.
#. Press the **Load Sensor** button.
#. Press the **Load Scene** button.
#. Press the **Set Sensor Pattern** button to load the example sensor pattern.
#. Press the **Open Source Code** button to view the source code. The source code illustrates how to create, add, and control the sensor using the Python API.
#. Press the **PLAY** button to begin simulating.

.. image:: ../images/isim_4.5_full_tut_viewport_generic_sensor.webp
    :align: center
    :height: 400

#. To visualize the pattern, you can save the image imprinted on the wall from the rays that hit it. To do so, select or type out the desired output directory and press **Save Pattern Image**. Open the saved image file, verify that you have a zigzag pattern.

.. image:: /images/isaac_tutorial_advanced_generic_sensor_pattern.png
    :align: center
    :height: 300


Script Editor
^^^^^^^^^^^^^

The following sections describe how to customize the |physx| generic sensor through the **Script Editor**, opened from **Window > Script Editor**.

**Customizing Scanning Pattern**

To customize scanning patterns, these are the parameters that need to be filled or modified:

- **streaming:** Set to ``True`` if streaming data continuously, ``False`` if sending a batch of data once in the beginning and repeating it.
- **sampling_rate:** Number of scans per second.
- **batch_size:** The number of scans each batch of data contains. The size needs be large enough to run a few rendering frames without running out. For example, if you want to scan at a sampling rate of 2400 scans per second, and your frame rendering rate is at 120 fps, then each frame will render 20 scans. If you send a batch size 12000, you must be able to render 600 frames or five seconds at 120 fps before you run out of data. If batch_size is less than what is needed to satisfy the desired sampling rate (that is, ``batch_size`` less than ``sampling_rate/fps``), then the sensor will scan at a rate that equals the ``batch_size`` per frame, which likely means you will be scanning slower than desired.
- **sensor_pattern:** a Nx2 size NumPy array. N is ``batch_size``, and the columns are [azimuth, zenith] angles of each scanning ray. Azimuth is the ray's horizontal angle measured from the x-axis, and zenith angle is the vertical angle measured from the z-axis.
- **origin_offsets:** (Optional) an Nx3 size NumPy array, N is the batch size, and each row is the individual ray's offset from origin in [x,y,z] coordinates.


**Example Scanning Patterns**

Let's take a closer look at our example code to see how to produce the zigzag scanning pattern.
The pattern in the example is generated programmatically inside the same script that runs the example. Click on the **Open Source Code** icon in the upper right-hand corner of the example window and open the Python source code for this example.

There are two test patterns in the script, one for testing continuous streaming data mode, the other one for testing a repeating pattern mode.

**Streaming Generated Pattern**

The pattern is sweeping horizontally 10 times for each round of up and down, resulting in the zigzag.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physx_generic/generic_sensor.py
    :language: python
    :start-after: # [streaming-pattern]
    :end-before: # [/streaming-pattern]

Origin offset is optional. For the example, a small random offset was added, as seen below. For no offsets, you can either use an array of zeros or skip setting the ``origin_offsets`` parameter.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physx_generic/generic_sensor.py
    :language: python
    :start-after: # [origin-offsets]
    :end-before: # [/origin-offsets]

**Streaming Pattern Through File**

If you do not have a programmatic way to generate the scanning pattern from scratch, or if you do not want to disclose the generation method of the scanning pattern, you can also import data from the file. The example below shows importing data from a ``.csv`` file and converting it to match the format of the **sensor_pattern** parameter.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physx_generic/generic_sensor.py
    :language: python
    :start-after: # [csv-import]
    :end-before: # [/csv-import]

**Repeating Pattern**

To better visualize the repetitiveness of the pattern, you use a zigzag motion, but this time instead a smooth movement going up and down, it is split into two modes, one set scanning high and the other set scanning low. If correctly executed, verify that it repeats itself without any additional data being pulled in.


.. image:: /images/isaac_tutorial_advanced_generic_repeat.gif
    :align: center
    :height: 400

To change the example to run in non-streaming mode, set variable ``self._streaming = False`` and save the change. Verify that it then automatically use the following code the generate the pattern. Wait for the example to restart and reload before trying to run it.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physx_generic/generic_sensor.py
    :language: python
    :start-after: # [repeating-pattern]
    :end-before: # [/repeating-pattern]

**Setting Scanning Pattern**

When the sensor processes each batch of ``[azimuth, zenith]`` pairs, just before it is about to run out of data, it will set the variable ``send_next_batch()`` to ``True``, at which point, you can send the next batch through ``set_next_batch_rays(prim_path, sensor_pattern)``, plus ``set_next_batch_offsets(prim_path, sensor_pattern)`` if there are any origin offsets. Like shown below.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physx_generic/generic_sensor.py
    :language: python
    :start-after: # [batch-callback]
    :end-before: # [/batch-callback]


.. _isaacsim_sensors_physx_generic_migration:

Migrating to the Physics Raycast Sensor
========================================

The |physx| generic sensor is deprecated. Use the :ref:`Physics Raycast Sensor <isaacsim_sensors_physics_raycast>` (``isaacsim.sensors.experimental.physics.RaycastSensor``) as the replacement. The raycast sensor accepts explicit per-ray origin offsets and direction vectors, making it a direct replacement for custom scanning patterns.

Concept mapping
---------------

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
     - ``RaycastSensor`` / ``RaycastSensorBackend`` classes.
   * - ``send_next_batch()`` / ``set_next_batch_rays()``
     - Not needed. All rays are defined at creation time and the sensor handles timing internally via ``rayTimeOffsets``.

Interactive example
-------------------

The **Physics Raycast Sensor** example demonstrates all three sensor configurations (solid state, rotating, and beam curtain) in a single scene:

- **GUI**: Open **Robotics Examples > Sensors > Physics Raycast Sensor** and click **Load Scene**.
- **Source code**: ``source/extensions/isaacsim.sensors.physics.examples/isaacsim/sensors/physics/examples/raycast_sensor.py``

See :ref:`isaacsim_sensors_physics_raycast` for the full documentation, including Python API usage and OmniGraph workflows.