..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaacsim_sensors_physics_imu:

==================
IMU Sensor
==================

.. deprecated:: 6.0
   The ``isaacsim.sensors.physics`` IMU Sensor extension is deprecated.
   Use ``isaacsim.sensors.experimental.physics.IMUSensor`` instead.
   See the `API Documentation`_ section below for links.

The IMU sensor in |isaac-sim_short| tracks the motion of the body and outputs simulated accelerometer and gyroscope readings.
Like real IMU sensors, simulated IMUs gives acceleration and angular velocity measurements in local ``x, y, z`` axis with stage units.

See the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim_short| conventions.

**IMU Sensor Properties**

#. ``enabled`` parameter determines if the sensor is running or not.
#. ``sensorPeriod`` parameter specifies the time in between sensor measurement. **Deprecated** since ``isaacsim.robot.schema`` 6.2.0 -- only used by the deprecated ``isaacsim.sensors.physx`` extension. The new ``isaacsim.sensors.experimental.physics`` extension reads every physics step.
#. ``angularVelocityFilterWidth`` parameter specifies the size of the angular velocity rolling average. Increasing this parameter will result in smoother angular velocity output.
#. ``linearAccelerationFilterWidth`` parameter specifies the size of the linear acceleration rolling average. Increasing this parameter will result in smoother linear acceleration output.
#. ``orientationFilterWidth`` parameter specifies the size of the orientation rolling average. Increasing this parameter will result in smoother orientation output.

The size of the data buffer used in interpolation is two times the max of the filter width or 20, whichever is greater.

For the full USD attribute definitions, see the :ref:`IMU Sensor schema reference <isaac_sim_sensor_schema_imu>`.

GUI
===

Creating and Modifying the IMU
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Assuming there is a prim present in the scene to which you want to add an IMU sensor, the following steps will let you create and modify an IMU sensor:

#. To create a Physics Scene, go to the top Menu Bar and click **Create > Physics > Physics Scene**. Verify that you have a ``PhysicsScene`` :ref:`isaac_sim_glossary_prim` in the :ref:`isaac_sim_glossary_stage` panel on the right.
#. To create an IMU, left click on the prim to attach the IMU on the stage, then go to the top Menu Bar and click **Create > Sensors > Imu Sensor**.
#. To change the position and orientation of the IMU, left click on the ``Imu_Sensor`` prim, then modify the **Transform** properties under the **Property** tab.
#. To change other IMU properties, expand the **Raw USD Properties** section, and properties such as filter width, enable/disable sensor, and sensor period will be available to modify.

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
#. Press the **PLAY** button to begin simulating.
#. Press :code:`SHIFT + LEFT_CLICK` over the ant to drag it around and see changes in the readings.

.. image:: /images/isim_4.5_full_tut_gui_create_imu_sensor.webp
    :align: center
    :width: 100%

OmniGraph Workflow
^^^^^^^^^^^^^^^^^^

The following is a tutorial on using OmniGraph to interact with the IMU Sensor.

Scene Setup
###########

Begin by adding a Simple Articulation to the scene. The articulation file can be accessed through a :ref:`isaac_sim_glossary_nucleus` server in the content window.
Connecting to this server allows allows you to access the library of |isaac-sim_short| robots, sensors, and environments.

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

.. Note:: In general, sensors must be added to rigid body prims to correctly report data. The prims in this robot are already rigid bodies, so nothing must be done for this case.

OmniGraph Setup
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

Standalone Python
=================

.. _isaacsim_sensors_physics_imu_standalone_python_create_modify:

Creating and Modifying the IMU
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are two ways to create an IMU Sensor in Python:

* using the ``IMUSensor.create()`` class method
* using the ``IMUSensor`` wrapper class constructor directly
 
This section provides snippets to be executed using standalone Python; these snippets are intended as a references, and must be modified to suit your purposes. The following snippet adds a ground plane, cube prim with collision and rigid body physics, and physics scene to an |isaac-sim_short| scene, which are required for the reference snippets further below to work correctly.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_imu/creating_and_modifying_the_imu.py
    :language: python

Using the Python API
####################

You can add an IMU to the cube prim created above using ``IMUSensor.create()``, as demonstrated in the following snippet. The path must include the parent prim path; the remaining arguments are optional.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_imu/imu_sensor.py
    :language: python
    :start-after: # [create-python-api]
    :end-before: # [/create-python-api]

Using Python Wrapper
####################

You can also add an IMU to the cube prim, created above, using the ``IMUSensor`` constructor directly when wrapping an existing sensor prim, as demonstrated in the following snippet. The wrapper class provides additional helper functions to set the IMU sensor properties and retrieve sensor data.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_imu/imu_sensor.py
    :language: python
    :start-after: # [create-python-wrapper]
    :end-before: # [/create-python-wrapper]

.. note::
    ``translation`` and ``position`` cannot both be provided as input arguments. ``frequency`` and ``dt`` also cannot both be provided as input arguments.
    The ``IMUSensor`` Python API documentation specifies the usage of each input argument.

To modify sensor parameters, you can use built-in class API calls such as ``set_frequency``, ``set_dt``, or USD attribute API calls.

Reading Sensor Output
^^^^^^^^^^^^^^^^^^^^^

The sensors are created dynamically on PLAY. Moving the sensor prim while the simulation is running will invalidate the sensor. If you need to make hierarchical changes to the IMU like changing its rigid body parent, stop the simulator, make the changes, and then restart the simulation.

There are also three methods for reading the sensor output: 

* using ``get_sensor_reading()`` in the sensor interface
* ``get_current_frame()`` in the IMU Python class
*  OmniGraph node ``Isaac Read IMU Node``

The following snippets assume you have created a ``/World/Cube`` prim and IMU sensor prim using one of the two snippets :ref:`above<isaacsim_sensors_physics_imu_standalone_python_create_modify>`.

**get_sensor_reading(sensor_path, interpolation_function = None, use_latest_data = False, read_gravity = True)**

The ``get_sensor_reading`` function takes in three parameters: 

* the ``prim_path`` to any IMU sensor prim
* an interpolation function (optional) to use in place of the default linear interpolation function
* the ``useLatestValue`` flag (optional) for retrieving the data point from the current physics step if the sensor is running at a slower rate than physics rate
  
The function will return an ``IsSensorReading`` object, which has ``is_valid``, ``time``, ``lin_acc_x``, ``lin_acc_y``, ``lin_acc_z``, ``ang_vel_x``, ``ang_vel_y``, ``ang_vel_z``, and ``orientation`` properties.

Sample usage to get the reading from the current physics step with gravitational effects:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_imu/imu_sensor.py
    :language: python
    :start-after: # [reading-backend-gravity]
    :end-before: # [/reading-backend-gravity]

Sample usage with custom interpolation function without gravitational effects:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_imu/imu_sensor.py
    :language: python
    :start-after: # [reading-backend-no-gravity]
    :end-before: # [/reading-backend-no-gravity]

.. note::
    When custom interpolation is used and the read gravity flag is enabled, the sensor will pass raw acceleration measurements to the custom interpolation function and apply gravitational transforms after.

**get_current_frame(read_gravity = True)**

The ``get_current_frame()`` function is a wrapper around ``get_sensor_reading(path_to_current_sensor)`` function and a member function of the IMU class. This function returns a dictionary with ``lin_acc``, ``ang_vel``, ``orientation``, ``time``, and ``physics_step`` as ``keys`` for the IMU measurement.
The ``get_current_frame()`` function uses the default parameters of ``get_sensor_reading``, so it utilizes linear interpolation and last sensor reading at reading time.

Sample usage:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_imu/imu_sensor.py
    :language: python
    :start-after: # [reading-interpolation]
    :end-before: # [/reading-interpolation]

API Documentation
^^^^^^^^^^^^^^^^^

.. deprecated:: 6.0
   The ``isaacsim.sensors.physics`` extension is deprecated. Use ``isaacsim.sensors.experimental.physics.IMUSensor`` instead.

See the |link_ext| for the current API and |link_ext_deprecated| for the deprecated API.

.. |link_ext| raw:: html

    <a href="../py/source/extensions/isaacsim.sensors.experimental.physics/docs/index.html" target="_blank">isaacsim.sensors.experimental.physics API Documentation</a>

.. |link_ext_deprecated| raw:: html

    <a href="../py/source/extensions/isaacsim.sensors.physics/docs/index.html" target="_blank">isaacsim.sensors.physics API Documentation (deprecated)</a>
