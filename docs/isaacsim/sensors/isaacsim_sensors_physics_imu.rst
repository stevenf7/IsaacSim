..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaacsim_sensors_physics_imu:

==================
IMU sensor
==================

.. deprecated:: 6.0
   The ``isaacsim.sensors.physics`` IMU Sensor extension is deprecated.
   Use ``isaacsim.sensors.experimental.physics.IMUSensor`` instead.
   See the `API Documentation`_ section below for links.

The IMU sensor in |isaac-sim_short| tracks body motion and outputs simulated accelerometer and gyroscope readings.
Like real IMU sensors, simulated IMUs give acceleration and angular velocity measurements in the local ``x, y, z`` axes with stage units.

See the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim_short| conventions.

**IMU sensor properties**

#. ``enabled`` parameter determines if the sensor is running or not.
#. ``sensorPeriod`` parameter specifies the time in between sensor measurement. **Deprecated** since ``isaacsim.robot.schema`` 6.2.0 --- only used by the deprecated ``isaacsim.sensors.physics`` extension. The new ``isaacsim.sensors.experimental.physics`` extension reads every physics step.
#. ``angularVelocityFilterWidth`` parameter specifies the size of the angular velocity rolling average. Increasing this parameter smooths angular velocity output.
#. ``linearAccelerationFilterWidth`` parameter specifies the size of the linear acceleration rolling average. Increasing this parameter smooths linear acceleration output.
#. ``orientationFilterWidth`` parameter specifies the size of the orientation rolling average. Increasing this parameter smooths orientation output.

The size of the data buffer used in interpolation is two times the max of the filter width or 20, whichever is greater.

For the full USD attribute definitions, see the :ref:`IMU Sensor schema reference <isaac_sim_sensor_schema_imu>`.

.. _isaacsim_sensors_physics_imu_gui:

GUI
===

Creating and modifying the IMU
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create and modify an IMU sensor, start with a prim in the scene that you want to attach the sensor to:

#. To create a Physics Scene, go to the top Menu Bar and click **Create > Physics > Physics Scene**. Verify that you have a ``PhysicsScene`` :ref:`isaac_sim_glossary_prim` in the :ref:`isaac_sim_glossary_stage` panel on the right.
#. To create an IMU, left click on the prim to attach the IMU on the stage, then go to the top Menu Bar and click **Create > Sensors > Imu Sensor**.
#. To change the position and orientation of the IMU, left click on the ``Imu_Sensor`` prim, then modify the **Transform** properties under the **Property** tab.
#. To change other IMU properties, expand the **Raw USD Properties** section and modify properties such as filter width, enable/disable sensor, and sensor period.

.. image:: /images/isim_4.5_full_tut_gui_create_imu_sensor_2.webp
    :align: center
    :width: 100%
    :alt: Add IMU with GUI


IMU Example
^^^^^^^^^^^

To run the IMU example:

#. Activate **Robotics Examples** tab from **Windows** > **Examples** > **Robotics Examples**.
#. Click **Robotics Examples** > **Sensors** > **IMU Sensor** > **Load Scene**.
#. Verify that you have a window containing each axis of the accelerometer and gyro readings being displayed.
#. Press the **Open Source Code** button to view the source code. The source code illustrates how to load an Ant body into the scene and then add the sensor to it using the Python API.
#. Press the **Play** button to begin simulating.
#. Press :code:`SHIFT + LEFT_CLICK` over the ant to drag it around and see changes in the readings.

.. image:: /images/isim_4.5_full_tut_gui_create_imu_sensor.webp
    :align: center
    :width: 100%
    :alt: IMU sensor example window with accelerometer and gyroscope readings.

OmniGraph workflow
^^^^^^^^^^^^^^^^^^

The following tutorial shows how to use OmniGraph to interact with the IMU sensor.

Scene setup
###########

Begin by adding a Simple Articulation to the scene. Access the articulation file through a :ref:`isaac_sim_glossary_nucleus` server in the content window.
Connecting to this server gives you access to the library of |isaac-sim_short| robots, sensors, and environments.

After connecting to the server:

#. Navigate to ``Robots/IsaacSim/SimpleArticulation/simple_articulation.usd`` in the **Content Browser**.
#. Drag ``simple_articulation`` onto the *World* prim in the **Stage** UI window on the right hand side to add an instance into the environment.
#. To drive the revolute joint, in the **Stage** window, select the RevoluteJoint prim at */World/simple_articulation/Arm/RevoluteJoint*, and scroll down to **Drive** in the **Property** window. Set the target velocity to ``90 deg/s`` and stiffness to ``0``.

.. image:: /images/isim_4.5_full_tut_gui_create_imu_sensor_1.webp
    :align: center
    :width: 100%
    :alt: Read IMU Sensor Action Graph set up

To add an IMU sensor to your robot and collect some data:

#. In the **Stage** tab, navigate to the */World/simple_articulation/Arm* prim and select it.
#. Add the sensor to the prim by **Create > Sensors > Imu Sensor**.
#. The newly added IMU sensor can be viewed by hitting the **+** button next to the Arm prim.

.. note:: In general, sensors must be added to rigid body prims to correctly report data. The prims in this robot are already rigid bodies, so no extra setup is required for this case.

OmniGraph setup
###############

To set up the |omnigraph_short| to collect readings from this sensor:

#. Create the new action graph by navigating to **Window > Graph Editors > Action Graph**, and selecting **New Action Graph** in the new tab that opens.
#. Add the following nodes to the graph, and set their properties as follows:

  - **On Playback Tick**: Executes the graph nodes every simulation timestep.
  - **Isaac Read IMU Node**: Reads the IMU sensor. In the **Property** tab, set `IMU Prim` to */World/simple_articulation/Arm/Imu_Sensor*, to point to the location of the IMU sensor prim. Select **read gravity** to read gravitational acceleration.
  - **To String**: Converts the IMU readings to string format.
  - **Print Text**: Prints the string readings to console. In the **Property** tab, set **Log Level** to **Warning** so that messages are visible in the terminal/console by default.

#. Connect the above nodes as follows to print out the IMU sensor reading:

    .. image:: /images/isaac_tutorial_advanced_read_imu_graph.png
        :align: center
        :width: 800
        :alt: Read Imu Action Graph set up

#. Press the **Play** button on the GUI. If set up correctly, verify that the |isaac-sim_short| internal *Console* reads out the IMU sensor's angular velocity.

    .. image:: /images/isim_4.5_full_tut_gui_create_imu_sensor_omnigraph.webp
        :align: center
        :width: 100%
        :alt: Read Imu Action Graph set up

.. _isaacsim_sensors_physics_imu_standalone_python:

Standalone Python
=================

.. _isaacsim_sensors_physics_imu_standalone_python_create_modify:

Creating and modifying the IMU
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are two ways to create an IMU Sensor in Python:

* Use the ``IMU.create()`` authoring class method, then wrap with ``IMUSensor`` for runtime reads.
* Use the ``IMU`` authoring class constructor directly, then wrap with ``IMUSensor``.
 
This section provides snippets to execute with standalone Python. Modify them to suit your use case. The following snippet adds a ground plane, cube prim with collision and rigid body physics, and physics scene to an |isaac-sim_short| scene. The reference snippets below require these objects.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_imu/creating_and_modifying_the_imu.py
    :language: python

Using the Python API
####################

You can add an IMU to the cube prim created above using ``IMU.create()`` and then wrap it with ``IMUSensor`` for runtime data access, as demonstrated in the following snippet. The path must include the parent prim path; the remaining arguments are optional.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_imu/imu_sensor.py
    :language: python
    :start-after: # [create-python-api]
    :end-before: # [/create-python-api]

Using the Python wrapper
########################

You can also add an IMU to the cube prim, created above, by constructing an ``IMU`` authoring object directly and wrapping it with ``IMUSensor`` for runtime data access, as demonstrated in the following snippet. The ``IMU`` constructor wraps an existing sensor prim or creates a new one with default attributes; the ``IMUSensor`` runtime then exposes ``get_sensor_reading()`` and ``get_data()`` for reading sensor output. Modify USD attributes (e.g., filter widths) via the authoring object reachable as ``sensor.imu`` after construction.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_imu/imu_sensor.py
    :language: python
    :start-after: # [create-python-wrapper]
    :end-before: # [/create-python-wrapper]

.. note::
    ``translations`` and ``positions`` cannot both be provided as input arguments — they are mutually exclusive (local-frame vs world-frame).
    The ``IMUSensor`` Python API documentation specifies the usage of each input argument.

To set filter widths at construction time, pass them to ``IMU.create()`` (or ``IMU(path, ...)``) — see the snippet above. To modify them after construction, set the underlying USD attributes (``linearAccelerationFilterWidth``, ``angularVelocityFilterWidth``, ``orientationFilterWidth``) on the sensor prim — the prim is reachable as ``sensor.imu.prims[0]``. Filter widths are captured by the C++ runtime when the sensor is created at simulation start; stop and restart the simulation to pick up changes. The ``IMUSensor`` reads every physics step.

Reading sensor output
^^^^^^^^^^^^^^^^^^^^^

The sensors are created dynamically on **Play**. Moving the sensor prim while the simulation is running invalidates the sensor. If you need to make hierarchical changes to the IMU, such as changing its rigid body parent, stop the simulator, make the changes, and then restart the simulation.

There are three methods for reading the sensor output:

* ``IMUSensor.get_sensor_reading(read_gravity=True)`` — returns the raw C++ struct directly
* ``IMUSensor.get_data(read_gravity=True)`` — returns a structured dictionary
* OmniGraph node ``Isaac Read IMU Node``

The following snippets assume you have created a ``/World/Cube`` prim and IMU sensor prim using one of the two snippets :ref:`above<isaacsim_sensors_physics_imu_standalone_python_create_modify>`.

**IMUSensor.get_sensor_reading(read_gravity=True)**

Returns an ``ImuSensorReading`` C++ struct exposing ``is_valid``, ``time``, ``linear_acceleration_x``/``_y``/``_z``, ``angular_velocity_x``/``_y``/``_z``, and ``orientation_w``/``_x``/``_y``/``_z`` properties. The sensor reads the C++ backend every physics step; pass ``read_gravity=False`` to exclude gravitational acceleration.

Sample usage to get the reading from the current physics step with gravitational effects:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_imu/imu_sensor.py
    :language: python
    :start-after: # [reading-backend-gravity]
    :end-before: # [/reading-backend-gravity]

Sample usage without gravitational effects:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_imu/imu_sensor.py
    :language: python
    :start-after: # [reading-backend-no-gravity]
    :end-before: # [/reading-backend-no-gravity]

**IMUSensor.get_data(read_gravity=True)**

The ``get_data()`` member function on the ``IMUSensor`` runtime class wraps :meth:`get_sensor_reading` and returns a dictionary with ``time``, ``physics_step``, ``linear_acceleration`` (``np.ndarray`` shape ``(3,)``), ``angular_velocity`` (``np.ndarray`` shape ``(3,)``), and ``orientation`` (``np.ndarray`` shape ``(4,)``, ``wxyz``).

Sample usage:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_imu/imu_sensor.py
    :language: python
    :start-after: # [reading-frame]
    :end-before: # [/reading-frame]

API documentation
^^^^^^^^^^^^^^^^^

.. deprecated:: 6.0
   The ``isaacsim.sensors.physics`` extension is deprecated. Use ``isaacsim.sensors.experimental.physics.IMUSensor`` instead.

See the |link_ext| for the current API and |link_ext_deprecated| for the deprecated API.

.. |link_ext| raw:: html

    <a href="../py/source/extensions/isaacsim.sensors.experimental.physics/docs/index.html" target="_blank">isaacsim.sensors.experimental.physics API Documentation</a>

.. |link_ext_deprecated| raw:: html

    <a href="../py/source/extensions/isaacsim.sensors.physics/docs/index.html" target="_blank">isaacsim.sensors.physics API Documentation (deprecated)</a>
