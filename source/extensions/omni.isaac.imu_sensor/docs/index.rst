IMU Sensor Extension [omni.isaac.imu_sensor]
######################################################


The IMU Sensor Extension provides a set of utilities to simulate inertial sensors and read sensor data. 
The API of the IMU sensor is a lot like that of the contact sensor.


Basic Usage
===========

Setting Up a Sensor
-------------------

First, aquire the sensor interface. This sensor interface governs all IMU sensors installed on various prims in the stage.

.. code-block:: python
    :linenos:

    from omni.isaac.imu_sensor import _imu_sensor
    _is = _imu_sensor.acquire_imu_sensor_interface()


Then, Create a ``SensorProperties`` object, and set the values according to the sensor specifications:

.. code-block:: python
    :linenos:

    props = _imu_sensor.SensorProperties()     
    props.position = carb.Float3(0, 0, 0)          # Position relative to the parent body where the sensor is placed
    props.orientation = carb.Float4(0, 0, 0, 1)    # Quaternion orientation (x,y,z,w) relative to the parent body where the sensor is placed
    props.sensorPeriod = 1 / 500                   # Sensor reading period in seconds. zero means sync with simulation timestep

Finally, add it to the desired rigid body using its prim path:

.. code-block:: python
    :linenos:
    
    sensor_handle = _is.add_sensor_on_body("/path/to/rigid_body", props)


To collect the readings, call the interface `get_sensor_sim_reading`. the result will be the accumulated readings since last time the sensor was read. Each reading is timestamped, and contains a boolean flag to tell if the sensor is triggered.

.. code-block:: python
    :linenos:

    readings = _is.get_sensor_readings(sensor_handle)


Acquiring Extension Interface
==============================

.. automethod:: omni.isaac.imu_sensor._imu_sensor.acquire_imu_sensor_interface
.. automethod:: omni.isaac.imu_sensor._imu_sensor.release_imu_sensor_interface

IMU Sensor API
====================

Input Types
------------

.. autoclass:: omni.isaac.imu_sensor._imu_sensor.SensorProperties
    :members:
    :undoc-members:
    :exclude-members: 



Output Types
-------------


.. autoclass:: omni.isaac.imu_sensor._imu_sensor.SensorReading
    :members:
    :undoc-members:
    :exclude-members: 


Interface Methods
------------------

.. autoclass:: omni.isaac.imu_sensor._imu_sensor.IMUSensorInterface
    :members:
    :undoc-members:


.. .. automodule:: omni.isaac.imu_sensor._imu_sensor
..    :platform: Windows-x86_64, Linux-x86_64
..    :members:
..    :undoc-members:
..    :show-inheritance:
..    :imported-members:
..    :exclude-members: