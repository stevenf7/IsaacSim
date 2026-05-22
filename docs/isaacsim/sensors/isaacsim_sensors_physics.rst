..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.





.. meta::
    :title: Isaac Sim Physics-Based Sensors
    :keywords: lang=en isaac isaac-sim sensors

.. _isaacsim_sensors_physics:

=====================
Physics-based sensors
=====================

|isaac-sim_short|'s physics-based sensors use CPU physics simulations and run after rendering finishes. They have access to a prim's physics properties, like mass and velocity.

These sensors output the exact measurements from the physics engine, and you can augment the sensor readings in post-processing.
By default, sensors output data at the physics rate. To generate data beyond this rate, provide additional interpolation options. Ground truth readings from the simulator might
already have some noise; you can add more noise in post-processing to make sensor readings more realistic.

The physics-based sensors are organized in the ``isaacsim.sensors.experimental.physics`` extension.

.. deprecated:: 6.0
   The ``isaacsim.sensors.physics`` extension is deprecated. Use ``isaacsim.sensors.experimental.physics`` instead.
   The new extension provides equivalent sensor classes (``ContactSensor``, ``IMUSensor``, ``EffortSensor``, etc.) with the same core functionality.
   See :ref:`isaacsim_sensors_physics_migration` for step-by-step migration instructions, or the `API Documentation <../py/source/extensions/isaacsim.sensors.experimental.physics/docs/index.html>`_ for the replacement APIs.

|isaac-sim_short| supports the following physics-based ground truth sensors:

.. toctree::
    :maxdepth: 1

    ./isaacsim_sensors_physics_articulation_force
    ./isaacsim_sensors_physics_contact
    ./isaacsim_sensors_physics_effort
    ./isaacsim_sensors_physics_imu
    ./isaacsim_sensors_physics_joint_state
    ./isaacsim_sensors_physics_raycast



