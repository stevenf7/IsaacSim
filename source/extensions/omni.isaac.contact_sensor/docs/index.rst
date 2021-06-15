Contact Sensor Extension [omni.isaac.contact_sensor]
######################################################


The Contact Sensor Extension provides a set of utilities to read Contact data, and set up simulated load sensors. 


Basic Usage
===========

Setting Up a Sensor
-------------------

First, aquire the sensor interface:

.. code-block:: python
    :linenos:

    from omni.isaac.contact_sensor import _contact_sensor
    _cs = _contact_sensor.acquire_contact_sensor_interface()


Then, Create a ``SensorProperties`` object, and set the values according to the sensor specifications:

.. code-block:: python
    :linenos:

    props = _contact_sensor.SensorProperties()
    props.radius = 12 # cover the body tip
    props.minThreshold = 0
    props.maxThreshold = 1000000000000
    props.sensorPeriod = 1 / 100.0
    props.position = carb.Float3(40, 0, 0) # Offset sensor 40cm in X direction from rigid body center

Finally, add it to the desired rigid body using its prim path:

.. code-block:: python
    :linenos:
    
    sensor_handle = _cs.add_sensor_on_body("/path/to/rigid_body", props)


To collect the readings, call the interface `get_sensor_sim_reading`. the result will be the accumulated readings since last time the sensor was read. Each reading is timestamped, and contains a boolean flag to tell if the sensor is triggered.

.. code-block:: python
    :linenos:

    readings = _cs.get_sensor_readings(sensor_handle)


Acquiring Extension Interface
==============================

.. automethod:: omni.isaac.contact_sensor._contact_sensor.acquire_contact_sensor_interface
.. automethod:: omni.isaac.contact_sensor._contact_sensor.release_contact_sensor_interface

Contact Sensor API
====================

Input Types
------------

.. autoclass:: omni.isaac.contact_sensor._contact_sensor.SensorProperties
    :members:
    :undoc-members:
    :exclude-members: 



Output Types
-------------


.. autoclass:: omni.isaac.contact_sensor._contact_sensor.SensorReading
    :members:
    :undoc-members:
    :exclude-members: 



.. autoclass:: omni.isaac.contact_sensor._contact_sensor.CsRawData
    :members:
    :undoc-members:
    :exclude-members: 


Interface Methods
------------------

.. autoclass:: omni.isaac.contact_sensor._contact_sensor.ContactSensorInterface
    :members:
    :undoc-members:


.. .. automodule:: omni.isaac.contact_sensor._contact_sensor
..    :platform: Windows-x86_64, Linux-x86_64
..    :members:
..    :undoc-members:
..    :show-inheritance:
..    :imported-members:
..    :exclude-members: