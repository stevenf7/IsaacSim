..
   Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaacsim_sensors_physics_joint_state:

====================
Joint state sensor
====================

The joint state sensor reads the full per-DOF state of an articulation in a single call: positions, velocities, and efforts for every degree of freedom, plus the DOF names and per-DOF type (revolute or prismatic). It is analogous to a ROS 2 ``JointState`` message and is backed by the C++ ``IJointStateSensor`` Carbonite interface in the ``isaacsim.sensors.experimental.physics`` extension.

Unlike the per-joint :ref:`Effort Sensor <isaacsim_sensors_physics_effort>`, a single joint state sensor returns data for the entire articulation. The sensor is attached to the articulation root prim, not to an individual joint.

See the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim_short| conventions.

**Joint state sensor properties**

#. ``enabled`` instance attribute determines whether the sensor returns data. When ``False``, ``get_sensor_reading()`` and ``get_data()`` return invalid readings without touching the C++ backend.
#. The sensor binds to a single articulation root path provided at construction time. To re-target the sensor to a different articulation, construct a new ``JointStateSensor``.

The ``JointStateSensor`` reads every physics step.


.. _isaacsim_sensors_physics_joint_state_standalone_python:

Standalone Python
=================

.. _isaacsim_sensors_physics_joint_state_standalone_python_create_modify:

Creating the joint state sensor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following snippet adds a Simple Articulation reference and creates a ``JointStateSensor`` bound to the articulation root. The articulation must already be in the stage when the sensor is constructed.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_joint_state/joint_state_sensor.py
    :language: python
    :start-after: # [create-sensor]
    :end-before: # [/create-sensor]

.. note::
    The articulation root prim you pass in **is** the sensor's prim — ``JointStateSensor`` does not author a separate USD prim in the **Stage** panel on construction. DOF readings become available via ``get_sensor_reading()`` once the simulation is playing; check ``reading.is_valid`` after pressing **Play** to confirm the sensor is active.


Reading sensor output
^^^^^^^^^^^^^^^^^^^^^

The sensor is created dynamically on **Play**. Moving or replacing the articulation root prim while the simulation is running invalidates the sensor; stop the simulator, make the changes, and restart.

There are two methods for reading the sensor output:

* ``JointStateSensor.get_sensor_reading()`` — returns a :class:`JointStateSensorReading` object with the per-DOF arrays as attributes.
* ``JointStateSensor.get_data()`` — returns a structured dictionary with the same data plus ``physics_step``, suitable for direct serialization.

**JointStateSensor.get_sensor_reading()**

Returns a :class:`JointStateSensorReading` exposing ``is_valid``, ``time``, ``dof_names`` (``list[str]``), ``positions`` / ``velocities`` / ``efforts`` (``np.ndarray`` of length ``dof_count``), ``dof_types`` (``np.ndarray`` of ``uint8``: ``0 = revolute``, ``1 = prismatic``), and ``stage_meters_per_unit``.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_joint_state/joint_state_sensor.py
    :language: python
    :start-after: # [read-sensor]
    :end-before: # [/read-sensor]

**JointStateSensor.get_data()**

Returns a dictionary with keys ``dof_names``, ``positions``, ``velocities``, ``efforts``, ``dof_types``, ``stage_meters_per_unit``, ``is_valid``, ``time``, and ``physics_step``. The numpy arrays in this dict are the same objects exposed by ``get_sensor_reading()``; the dict form simply makes the data easier to log, plot, or pass to downstream consumers.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_joint_state/joint_state_sensor.py
    :language: python
    :start-after: # [read-frame]
    :end-before: # [/read-frame]


.. _isaacsim_sensors_physics_joint_state_api_documentation:

API documentation
=================

See the |link_ext| for the full ``JointStateSensor`` API.

.. |link_ext| raw:: html

    <a href="../py/source/extensions/isaacsim.sensors.experimental.physics/docs/index.html" target="_blank">isaacsim.sensors.experimental.physics API Documentation</a>
