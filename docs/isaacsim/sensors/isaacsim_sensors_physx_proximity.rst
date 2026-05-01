..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.





.. _isaacsim_sensors_physx_proximity:

==================
Proximity sensor
==================

.. deprecated:: 6.0
   The Proximity Sensor (``isaacsim.sensors.physx.ProximitySensor``) is part of the deprecated ``isaacsim.sensors.physx`` extension.
   For collision detection, consider using the :ref:`Contact Sensor <isaacsim_sensors_physics_contact>` or physics contact callbacks directly.

The proximity sensor wraps a physics callback that can be attached to any prim in the scene. During simulation execution,
the sensor records collisions between the prim it is attached to and other prims in the scene each frame; you can access that data
using a callback function.

.. _isaacsim_sensors_physx_proximity_standalone_python:

Standalone Python
=================

.. note::
   The code below uses the deprecated ``isaacsim.sensors.physx`` extension. See the deprecation notice above for the replacement API.

Execute the following script using ``python.sh``. This creates a scene with two cubes and attaches a proximity sensor to one of the cubes.
At the start of the simulation, the two cubes overlap and then move apart; the callback function in the script prints the proximity
sensor's output to the screen.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physx_proximity/standalone_python.py
    :language: python

Example proximity sensor output is shown below; there might be small numerical differences in your output run-to-run.

.. code-block:: bash

    distance: 0.8995118804137266, duration: 0.03952527046203613
    distance: 0.9490971672498862, duration: 0.04244112968444824
    distance: 0.9978315307718298, duration: 0.045195579528808594
    distance: 1.0952793930211249, duration: 0.00010466575622558594
    distance: 1.0952880909233123, duration: 0.004382610321044922
    distance: 1.0952874949586842, duration: 0.008539199829101562
    distance: 1.095288806188406, duration: 0.012722015380859375

After the cubes land, the scene looks like the following image:

.. figure:: /images/isaac_proximity_sensor_example.png
    :align: center
    :width: 800
    :alt: Proximity sensor example scene with two cubes.
