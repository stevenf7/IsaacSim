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


Then, Create a ``Contact Sensor`` prim as a child of a valid rigid body parent, and set the sensor attributes according to the sensor specifications. Please note that the sensor's transformations are impacted by its parents.

.. code-block:: python
    :linenos:

    import omni.isaac.IsaacSensorSchema as sensorSchema
    from omni.isaac.contact_sensor import _contact_sensor
    from pxr import Gf

    stage = omni.usd.get_context().get_stage()
    sensorGeom = sensorSchema.IsaacContactSensor.Define(stage,  "/World/Cube/sensor")

    sensorGeom.CreateEnabledAttr().Set(True)
    sensorGeom.CreateVisualizeAttr().Set(True)
    sensorGeom.CreateThresholdAttr().Set((0, 100000))
    sensorGeom.CreateColorAttr().Set((1,1,0,1))
    sensorGeom.CreateSensorPeriodAttr().Set(-1)
    sensorGeom.CreateRadiusAttr().Set(0.12)
    sensorGeom.AddTranslateOp().Set(Gf.Vec3d(40, 0, 0))

To collect the most recent reading, call the interface `get_sensor_sim_reading(/path/to/sensor)`. The result will be most recent sensor reading.

.. code-block:: python

    reading = _cs.get_sensor_sim_reading("/World/Cube/sensor")

To collect the readings, call the interface `get_sensor_readings(/path/to/sensor)`. The result will be the accumulated readings since last frame of the simulator. Each reading is timestamped, and contains a boolean flag to tell if the sensor is triggered.

.. code-block:: python

    readings = _cs.get_sensor_readings("/World/Cube/sensor")

To collect raw reading, call the interface `get_contact_sensor_raw_data(/path/to/sensor)`. The result will return a list of raw contact data for that body.

.. code-block:: python

    raw_Contact = _cs.get_contact_sensor_raw_data("/World/Cube/sensor")


Acquiring Extension Interface
==============================

.. automethod:: omni.isaac.contact_sensor._contact_sensor.acquire_contact_sensor_interface
.. automethod:: omni.isaac.contact_sensor._contact_sensor.release_contact_sensor_interface

Contact Sensor API
====================

Attribute Types
---------------
.. code-block:: python
    
    sensorGeom.CreateEnabledAttr().Set(True) 

True to enable the sensor, False to disable the sensor

.. code-block:: python
    
    sensorGeom.CreateVisualizeAttr().Set(True)

True to visualize the sensor, False to hide debug visualization

.. code-block:: python
    
    sensorGeom.CreateThresholdAttr().Set((0, 100000))

Gf.Vec2f datatype for (minThreshold, maxThreshold) of the contact sensor

.. code-block:: python
    
    sensorGeom.CreateColorAttr().Set((1,1,0,1))

Gf.Vec4f datatype for the color of the debug visualization, in the order of (R, G, B, A) where (1.0, 1.0, 1.0, 1.0) represents white, (0.0, 0.0, 0.0, 1.0) represents black.

.. code-block:: python
    
    sensorGeom.CreateSensorPeriodAttr().Set(-1)

float datatype for the sensor period in seconds. 0 or negative numbers means sync with simulator timestype

.. code-block:: python
    
    sensorGeom.CreateRadiusAttr().Set(-1)

float datatype the radius of the sensor in stage units. 0 or negative number means full body sensor

.. code-block:: python
    
    sensorGeom.AddTranslateOp().Set(Gf.Vec3d(40, 0, 0))

Gf.Vec3d datatype for the relative position between the contact sensor and its parent. Note, this translation is also impacted by its parents transformations.

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