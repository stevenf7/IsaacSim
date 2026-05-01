..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaacsim_sensors_physics_effort:

==================
Effort sensor
==================

.. deprecated:: 6.0
   The ``isaacsim.sensors.physics`` Effort Sensor extension is deprecated.
   Use ``isaacsim.sensors.experimental.physics.EffortSensor`` instead.
   See the `API Documentation`_ section below for links.

The effort sensor in |isaac-sim_short| tracks the torque or force applied to individual joints. Torque is measured for revolute joints and magnitude of force is measured for linear joints.

See the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim_short| conventions.

.. _isaacsim_sensors_physics_effort_gui:

GUI
===

Scene setup
^^^^^^^^^^^

Begin by adding a Simple Articulation to the scene, which can be accessed in the Content Browser.

#. In the *Content Browser*, search for ``simple_articulation`` or navigate to ``Isaac Sim/Robots/IsaacSim/SimpleArticulation/simple_articulation.usd``.
#. Drag ``simple_articulation`` onto the *World* prim in the **Stage** UI window on the right hand side to add an instance into the environment.
#. To drive the revolute joint, in the **Stage** window, select the RevoluteJoint prim at */World/simple_articulation/Arm/RevoluteJoint*, and scroll down to **Drive** in the **Property** window. Set the target velocity to ``90 deg/s``, and stiffness to ``0``.


Creating and modifying the effort sensor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following section describes how to create the effort sensor using the **Script Editor**, opened from **Window > Script Editor**.
The effort sensor is created by constructing an ``isaacsim.sensors.experimental.physics.EffortSensor`` directly with the joint prim path. The class exposes ``get_sensor_reading()`` and ``get_data()`` for reading sensor output, plus ``update_dof_name()`` and ``change_buffer_size()`` for runtime reconfiguration. (Unlike the contact, IMU, and raycast sensors, ``EffortSensor`` has no separate authoring class because it has no schema-bearing prim of its own.)

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_effort/creating_and_modifying_the_effort_sensor.py
    :language: python
    :start-after: # [create-sensor]
    :end-before: # [/create-sensor]

To modify sensor parameters, change class member variables such as ``enabled`` directly. To change the ``dof_name`` and ``buffer_size`` for readings, use the corresponding member functions, ``update_dof_name`` and ``change_buffer_size``.


Reading sensor output with Python
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are two methods for reading the sensor output:

* ``EffortSensor.get_sensor_reading()`` — returns an ``EffortSensorReading`` object with ``is_valid``, ``time``, and ``value``.
* ``EffortSensor.get_data()`` — returns a structured dictionary with ``value``, ``is_valid``, ``time``, and ``physics_step``.

After you create the effort sensor, press **Play** to start the simulation and call the function below to get the sensor reading for the current frame:

**EffortSensor.get_sensor_reading()**

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_effort/creating_and_modifying_the_effort_sensor.py
    :language: python
    :start-after: # [read-sensor]
    :end-before: # [/read-sensor]

**EffortSensor.get_data()**

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_effort/creating_and_modifying_the_effort_sensor.py
    :language: python
    :start-after: # [read-frame]
    :end-before: # [/read-frame]

OmniGraph workflow
^^^^^^^^^^^^^^^^^^

Set up |omnigraph_short| to create the effort sensor and collect readings from it:

#. Create the new action graph by navigating to **Window > Graph Editors > Action Graph**, and selecting **New Action Graph** in the new tab that opens.
#. Add the following nodes to the graph:

    - **On Playback Tick**: Executes the graph nodes every simulation timestep.
    - **Isaac Read Effort Node**: Reads the effort sensor. In the **Property** tab, set Effort Prim to the exact joint of measurement. For example */World/simple_articulation/Arm/RevoluteJoint* in ``simple_articulation.usd``.
    - **To String**: Converts the effort sensor readings to string format.
    - **Print Text**: Prints the string readings to console. In the **Property** tab, set `Log Level` to *Warning* so that messages are visible in the terminal/console by default. Additionally, check *To Screen* to print directly to screen.

Connect the nodes as follows to print the effort sensor reading:

.. image:: /images/isim_4.5_full_tut_gui_effort_sensor_omnigraph.png
    :align: center
    :width: 800
    :alt: Read Effort Sensor Action Graph set up

.. note::
    Configure the joints to the correct axis to get the expected readings.


.. _isaacsim_sensors_physics_effort_api_documentation:

API documentation
=================

.. deprecated:: 6.0
   The ``isaacsim.sensors.physics`` extension is deprecated. Use ``isaacsim.sensors.experimental.physics.EffortSensor`` instead.

See the |link_ext| for the current API and |link_ext_deprecated| for the deprecated API.

.. |link_ext| raw:: html

    <a href="../py/source/extensions/isaacsim.sensors.experimental.physics/docs/index.html" target="_blank">isaacsim.sensors.experimental.physics API Documentation</a>

.. |link_ext_deprecated| raw:: html

    <a href="../py/source/extensions/isaacsim.sensors.physics/docs/index.html" target="_blank">isaacsim.sensors.physics API Documentation (deprecated)</a>
