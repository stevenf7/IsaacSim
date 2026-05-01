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
   See the `API Documentation <../py/source/extensions/isaacsim.sensors.experimental.physics/docs/index.html>`_ for the replacement APIs.

|isaac-sim_short| supports the following physics-based ground truth sensors:

.. toctree::
    :maxdepth: 1

    ./isaacsim_sensors_physics_articulation_force
    ./isaacsim_sensors_physics_contact
    ./isaacsim_sensors_physics_effort
    ./isaacsim_sensors_physics_imu
    ./isaacsim_sensors_physics_joint_state
    ./isaacsim_sensors_physics_raycast


.. _isaacsim_sensors_physics_migration:

Migrating from ``isaacsim.sensors.physics`` to ``isaacsim.sensors.experimental.physics``
========================================================================================

The deprecated ``isaacsim.sensors.physics`` extension is replaced by ``isaacsim.sensors.experimental.physics``. The replacement keeps the same sensor concepts (``ContactSensor``, ``IMUSensor``, ``EffortSensor``, ``RaycastSensor``, ``JointStateSensor``) but reshapes the Python API to mirror ``isaacsim.sensors.experimental.rtx`` — array-form transforms, no command-based creation, and a single runtime class per sensor.

.. _isaacsim_sensors_physics_concept_mapping:

Concept mapping
---------------

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - ``isaacsim.sensors.physics`` (deprecated)
     - ``isaacsim.sensors.experimental.physics``
   * - ``omni.kit.commands.execute("IsaacSensorCreateImuSensor", ...)`` (and the contact/raycast equivalents)
     - ``IMU.create(path, ...)``, ``Contact.create(...)``, ``Raycast.create(...)`` authoring class methods, then wrap with the runtime: ``IMUSensor(IMU.create(...))``. No command registration. Mirrors ``isaacsim.sensors.experimental.rtx`` where ``create()`` lives only on authoring classes.
   * - Singular ``translation=Gf.Vec3d(x, y, z)``, ``orientation=Gf.Quatd(w, x, y, z)`` constructor args
     - Plural ``translations=[[x, y, z]]`` (or ``positions=...`` for world-frame), ``orientations=[[w, x, y, z]]`` arrays. Shape ``(N, 3)`` / ``(N, 4)``; only ``N=1`` is supported per sensor.
   * - ``position`` (world-frame) and ``translation`` (local-frame) accepted on the same call
     - ``positions`` and ``translations`` are mutually exclusive — passing both raises ``ValueError``.
   * - ``name=`` constructor parameter
     - Removed (was unused).
   * - ``sensor.get_current_frame()``
     - ``sensor.get_data()`` (returns the same dict). ``get_current_frame()`` was removed in 3.0.0.
   * - ``ImuSensorBackend(path)``, ``ContactSensorBackend(path)``, ``RaycastSensorBackend(path)``, ``EffortSensorBackend(path)``, ``JointStateSensorBackend(path)`` (lightweight reader handles)
     - Removed in 3.0.0. Construct the runtime sensor directly: ``IMUSensor(path)``, ``ContactSensor(path)``, ``RaycastSensor(path)``, ``EffortSensor(path)``, ``JointStateSensor(path)``. Each runtime now owns the C++ interface and exposes both ``get_data()`` (dict) and ``get_sensor_reading()`` (raw C++ struct).
   * - ``ContactSensor.set_min_threshold(v)`` / ``set_max_threshold(v)`` / ``set_radius(v)`` (and matching getters)
     - Removed in 3.0.0. Use the authoring object: ``sensor.contact.set_min_threshold(v)``, ``sensor.contact.get_radius()``, etc.

.. _isaacsim_sensors_physics_code_examples:

Code examples
-------------

**IMU sensor — create and read**

.. code-block:: python

   # Old (isaacsim.sensors.physics)
   from pxr import Gf
   import omni.kit.commands

   _, sensor = omni.kit.commands.execute(
       "IsaacSensorCreateImuSensor",
       path="/Imu_Sensor",
       parent="/World/Cube",
       translation=Gf.Vec3d(0, 0, 0),
       orientation=Gf.Quatd(1, 0, 0, 0),
       linear_acceleration_filter_size=10,
   )

   frame = sensor.get_current_frame()

.. code-block:: python

   # New (isaacsim.sensors.experimental.physics)
   import numpy as np
   from isaacsim.sensors.experimental.physics import IMU, IMUSensor

   sensor = IMUSensor(
       IMU.create(
           "/World/Cube/Imu_Sensor",
           translations=np.array([[0.0, 0.0, 0.0]]),
           orientations=np.array([[1.0, 0.0, 0.0, 0.0]]),
           linear_acceleration_filter_size=10,
       )
   )

   frame = sensor.get_data()

**Contact sensor — create**

.. code-block:: python

   # Old
   omni.kit.commands.execute(
       "IsaacSensorCreateContactSensor",
       path="/Contact_Sensor",
       parent="/World/Cube",
       min_threshold=0.0,
       max_threshold=100000.0,
       translation=Gf.Vec3d(0, 0, 0),
   )

.. code-block:: python

   # New
   from isaacsim.sensors.experimental.physics import Contact

   Contact.create(
       "/World/Cube/Contact_Sensor",
       min_threshold=0.0,
       max_threshold=100000.0,
       translations=[[0.0, 0.0, 0.0]],
   )

**Reading raw sensor data**

.. code-block:: python

   # Old (separate Backend class for low-level reads)
   from isaacsim.sensors.experimental.physics import ImuSensorBackend  # before 3.0.0

   backend = ImuSensorBackend("/World/Cube/Imu")
   reading = backend.get_sensor_reading(read_gravity=True)

.. code-block:: python

   # New (runtime sensor owns the C++ interface)
   from isaacsim.sensors.experimental.physics import IMUSensor

   sensor = IMUSensor("/World/Cube/Imu")
   reading = sensor.get_sensor_reading(read_gravity=True)   # raw C++ struct
   frame = sensor.get_data(read_gravity=True)               # structured dict

For the full per-sensor API, see :ref:`isaacsim_sensors_physics_imu`, :ref:`isaacsim_sensors_physics_contact`, :ref:`isaacsim_sensors_physics_raycast`, :ref:`isaacsim_sensors_physics_effort`, and :ref:`isaacsim_sensors_physics_joint_state`. For migrating from the older |physx| raycast sensors (``isaacsim.sensors.physx``), see :ref:`isaacsim_sensors_physx_lidar_migration`, :ref:`isaacsim_sensors_physx_generic_migration`, and :ref:`isaacsim_sensors_physx_lightbeam_migration`.

