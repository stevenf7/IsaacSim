..
   Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.





.. meta::
    :title: Isaac Sim |physx| Sensors
    :keywords: lang=en isaac isaac-sim sensors

.. _isaacsim_sensors_physx:

===============
|physx| Sensors
===============

|isaac-sim_short|'s |physx| sensors use raycasts provided by  `PhysX SDK <https://nvidia-omniverse.github.io/PhysX/physx/5.3.0/>`_ to measure the range between
objects in the simulation.

These sensors will output the exact measurements from |physx|. By default, the highest rate that the sensors can output data is the render rate.

The |physx| sensors are organized in the ``isaacsim.sensors.physx`` extension.

.. deprecated:: 6.0
   The ``isaacsim.sensors.physx`` extension is deprecated. Use ``isaacsim.sensors.experimental.physics`` instead,
   which provides the ``RaycastSensor`` as the replacement for PhysX-based range sensors.
   See the `API Documentation <../py/source/extensions/isaacsim.sensors.experimental.physics/docs/index.html>`_ for the replacement APIs.
   See individual sensor pages below for specific migration guidance.

|isaac-sim_short| supports the following |physx| sensors:

.. toctree::
    :maxdepth: 1

    ./isaacsim_sensors_physx_generic
    ./isaacsim_sensors_physx_lidar
    ./isaacsim_sensors_physx_lightbeam
    ./isaacsim_sensors_physx_proximity
