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
Physics-Based Sensors
=====================

|isaac-sim_short|'s physics-based sensors are based on CPU physics simulations and are run after the rendering is finished.  They have access to a prim's physics properties, like mass and velocity.

These sensors output the exact measurements from the physics engine and the sensor readings can be augmented in post processing.
By default, the highest rate that the sensors can output data is the physics rate and you must provide additional interpolation options to generate data beyond this rate. Furthermore, ground truth readings from the simulator might
already have some noise; additional noise can be augmented to the sensor readings in post process to make them more realistic.

The physics-based sensors are organized in the `isaacsim.sensors.physics` extension.

|isaac-sim_short| supports the following physics-based ground truth sensors:

.. toctree::
    :maxdepth: 1

    ./isaacsim_sensors_physics_articulation_force
    ./isaacsim_sensors_physics_contact
    ./isaacsim_sensors_physics_effort
    ./isaacsim_sensors_physics_imu
    ./isaacsim_sensors_physics_proximity
    ./isaacsim_sensors_physics_raycast

