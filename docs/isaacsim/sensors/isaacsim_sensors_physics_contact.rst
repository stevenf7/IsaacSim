..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaacsim_sensors_physics_contact:


===============
Contact sensor
===============

.. deprecated:: 6.0
   The ``isaacsim.sensors.physics`` Contact Sensor extension is deprecated.
   Use ``isaacsim.sensors.experimental.physics.ContactSensor`` instead.
   See the `API Documentation`_ section below for links.

The contact sensor uses the PhysX Contact Report API to generate a sensor reading similar to contact cells or pressure-based sensors placed on the surface of an object.
The Contact Sensor API builds on the Contact Report API by providing contact data filtered by the object it was placed in, along with an optional filter that only considers contacts in a specific region of the object. For example, imagine a quadruped robot with sensors in its feet. While the simulation treats the entire leg as a rigid body, you can only measure contact on the foot pads, so you can add a region filter that discards contacts outside that boundary.
The Contact Sensor API also provides persistent contact data, even when the PhysX engine stops streaming contacts to preserve compute time. While the simulation provides full information about contacts, such as contact pairs, normals, and contact points, the Contact Sensor API matches real data obtained by single-cell contact pads. If you need full contact data, the Contact Sensor API gets you filtered contact information without changes to the data acquired in PhysX.

See the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim_short| conventions.

**Contact sensor properties**

#. ``radius`` parameter specifies the distance of the contact force that it would detect. A value of ``-1`` uses the prim's collision geometry.
#. ``enabled`` parameter determines if the sensor is running or not.
#. ``min threshold`` parameter specifies the minimum amount of force to trigger a contact.
#. ``max threshold`` parameter specifies the maximum amount of force the sensor outputs.
#. ``sensorPeriod`` parameter specifies the time in between sensor measurement. **Deprecated** since ``isaacsim.robot.schema`` 6.2.0 --- only used by the deprecated ``isaacsim.sensors.physics`` extension. The new ``isaacsim.sensors.experimental.physics`` extension reads every physics step.

For the full USD attribute definitions, see the :ref:`Contact Sensor schema reference <isaac_sim_sensor_schema_contact>`.


.. _isaacsim_sensors_physics_contact_gui:

GUI
===

Creating and modifying the contact sensor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create and modify a contact sensor, start with a prim in the scene that you want to attach the sensor to.

#. To create a Physics Scene, go to the top Menu Bar and click **Create > Physics > Physics Scene**. Verify that there is now a ``PhysicsScene`` :ref:`isaac_sim_glossary_prim` in the :ref:`isaac_sim_glossary_stage` panel on the right.
#. To create a contact sensor, left click on the prim to attach the contact sensor on the stage, then go to the top Menu Bar and click **Create > Sensors > Contact_sensor**.
#. To change the position and orientation of the contact sensor, use **Translate and Orientate** tab.
#. To change other contact sensor properties, click **Raw USD Properties** and modify properties such as min/max force threshold, enable/disable sensor, and sensor period.

Contact sensor example
^^^^^^^^^^^^^^^^^^^^^^

To run the Contact Sensor Example:

#. Activate **Robotics Examples** tab from **Windows** > **Examples** > **Robotics Examples**.
#. Click **Robotics Examples** > **Sensors** > **Contact Sensor**.
#. Verify that you see a window containing the sensor's force readings color coded by each ant's arm.
#. Press the **Open Source Code** button to view the source code. The source code illustrates how to load an Ant body into the scene and then add sensors to it using the Python API.
#. Press the **Play** button to begin simulating.
#. Press ``SHIFT + LEFT_CLICK`` to drag the ant around  and see changes in the readings.

.. image:: /images/isim_4.5_full_tut_gui_create_contact_sensor.webp
    :align: center
    :width: 100%
    :alt: Contact sensor example window with force readings.

OmniGraph workflow
^^^^^^^^^^^^^^^^^^

The following tutorial shows how to use OmniGraph to interact with and visualize the contact sensor readings.

Scene setup
###########

#. Add a cube to the stage by **Create > Mesh > Cube**, select the cube and drag it up. Then select the cube and right click **Add > Physics > Rigid Body with Colliders Preset**.
#. Add a physics scene by **Create > Physics > PhysicsScene**.
#. Add a ground plane by **Create> Physics > GroundPlane**.
#. Add a contact sensor by selecting the cube, and select on the top menu **Create > Sensors > Contact Sensor**.

.. image:: /images/isim_4.5_full_tut_gui_create_contact_sensor_1.webp
    :align: center
    :width: 100%
    :alt: Read Contact Sensor Action Graph set up

OmniGraph setup
###############

To set up the |omnigraph_short| to collect readings from this sensor:

#. Create the new action graph by navigating to **Window > Graph Editors > Action Graph**, and selecting New Action Graph in the new tab that opens.
#. Add the following nodes to the graph:

  - *On Playback Tick*: Executes the graph every simulation timestep.
  - *Isaac Read Contact Sensor*: Reads the contact sensor. In the **Property** tab, set `Contact Sensor Prim` to */World/Cube/Contact_Sensor* to point to the location of the contact sensor prim.
  - *To String*: Converts the contact sensor readings to string format.
  - *Print Text*: Prints the string readings to console. In the **Property** tab, set `Log Level` to *Warning* so that messages are visible in the terminal or console by default.

#. Connect the above nodes as follows to print out the contact sensor reading:

    .. image:: /images/isaac_tutorial_advanced_read_contact_graph.png
        :align: center
        :width: 800
        :alt: Read Contact Sensor Action Graph set up

#. Press the **Play** button on the GUI. If set up correctly, verify that the |isaac-sim_short| internal *Console* reads out the contact sensor's force output.

    .. image:: /images/isim_4.5_full_tut_gui_contact_sensor_ogn.webp
        :align: center
        :width: 100%
        :alt: Read Contact Sensor Action Graph set up

**Contact sensor visualization**

You can visualize the contact sensor position and radius using the ``Isaac xPrim Radius Visualizer Node``. Connect the xPrim input to the contact sensor prim and connect ``Tick`` to ``Exec in``. Then set the radius, color, and line thickness. The contact sensor appears when you press **Play**.

.. note:: The spherical region only determines the boundary for contacts that are counted. All contacts still only happen at the surface of the object bounded by the spherical region.

.. image:: /images/isaac_tutorial_visualize_contact.png
    :align: center
    :width: 800
    :alt: Contact Sensor Visualization Action Graph set up


.. _isaacsim_sensors_physics_contact_standalone_python:

Standalone Python
=================

.. _isaacsim_sensors_physics_contact_standalone_python_create_modify:

Creating and modifying the contact sensor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For the example snippets below, prepare the scene using the following snippet by adding a ``PhysicsScene``, ``GroundPlane``, and a ``Cube`` prim with collision and rigid body physics.
Attach the contact sensor to the latter.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_contact/creating_and_modifying_the_contact_sensor.py
    :language: python

Using the Python API
####################

Contact sensors are created with Python by calling ``Contact.create()`` (the authoring class) and wrapping the returned authoring object with ``ContactSensor`` for runtime data access. Available parameters and their defaults are listed below; the path must include the parent prim path.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_contact/contact_sensor.py
    :language: python
    :start-after: # [create-python-api]
    :end-before: # [/create-python-api]

Using the Python wrapper
########################

The contact sensor can also be created by constructing a ``Contact`` authoring object directly and wrapping it with ``ContactSensor`` for runtime data access. The ``Contact`` constructor wraps an existing sensor prim or creates a new one with default attributes; the ``ContactSensor`` runtime exposes ``get_sensor_reading()``, ``get_data()``, and ``get_raw_data()`` for reading sensor output. Property setters (``set_min_threshold`` / ``set_max_threshold`` / ``set_radius`` / corresponding getters) live on the ``Contact`` authoring object, accessible as ``sensor.contact`` after construction.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_contact/contact_sensor.py
    :language: python
    :start-after: # [create-python-wrapper]
    :end-before: # [/create-python-wrapper]

.. note::
    ``translations`` (local-frame) and ``positions`` (world-frame) cannot both be defined — they are mutually exclusive.

Creating a contact sensor requires an enabled rigid-body ancestor, and the body depends on a Contact Report API. Contact-producing geometry still needs collision APIs. ``Contact.create()`` applies the Contact Report API on the rigid-body ancestor when it creates the sensor prim; when wrapping an existing sensor prim with ``Contact(path)`` the API is not applied by Python, but the C++ runtime ensures contact reporting is enabled when the sensor goes live on **Play**. You can also manually add a Contact Report API to a prim through:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_contact/contact_sensor.py
    :language: python
    :start-after: # [contact-report-api]
    :end-before: # [/contact-report-api]

To modify sensor parameters at runtime, use the authoring object exposed via ``sensor.contact``: ``sensor.contact.set_min_threshold(value)``, ``sensor.contact.set_max_threshold(value)``, ``sensor.contact.set_radius(value)``. The previous shorthand methods on ``ContactSensor`` itself were removed in 3.0.0 — call them on ``sensor.contact``.

Reading sensor output
^^^^^^^^^^^^^^^^^^^^^

The contact sensors are created dynamically on **Play**. Moving the sensor prim while the simulation is running invalidates the sensor. If you need to make hierarchical changes to the contact sensor like changing its rigid body parent, stop the simulator, make the changes, and then restart the simulation.

There are three methods for reading the sensor output:

* ``ContactSensor.get_sensor_reading()`` — returns the cached :class:`ContactSensorReading`
* ``ContactSensor.get_data()`` — returns a structured dictionary
* OmniGraph node ``Isaac Read Contact Sensor``

The following snippets assume you have created a ``/World/Cube`` prim and contact sensor prim using one of the two snippets :ref:`above<isaacsim_sensors_physics_contact_standalone_python_create_modify>`.

**ContactSensor.get_sensor_reading()**

Returns a :class:`ContactSensorReading` with ``is_valid``, ``time``, ``value`` (force magnitude), and ``in_contact``.

Sample usage to get the reading from the current frame:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_contact/contact_sensor.py
    :language: python
    :start-after: # [reading-backend]
    :end-before: # [/reading-backend]

**ContactSensor.get_data()**

The ``get_data()`` member function on the ``ContactSensor`` runtime class returns a structured dictionary with ``time``, ``physics_step``, ``in_contact``, ``force``, and ``number_of_contacts``. Internally it calls :meth:`get_sensor_reading` for the contact state and :meth:`get_raw_data` to compute ``number_of_contacts``. When ``add_raw_contact_data_to_frame()`` has been called, the dictionary additionally contains a ``contacts`` list whose entries provide ``body0``, ``body1``, ``position``, ``normal``, and ``impulse`` per contact point.

Sample usage:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_contact/contact_sensor.py
    :language: python
    :start-after: # [reading-wrapper]
    :end-before: # [/reading-wrapper]

**ContactSensor.get_raw_data()**

Returns a list of raw contact records (one per contact event in the current physics step). Each record contains ``time``, ``dt``, ``body0``, ``body1``, ``position``, ``normal``, and ``impulse``. Raw data disregards the sensor's ``min_threshold``/``max_threshold`` filtering: contacts that fall below the threshold are still reported here, even though they would be discarded by the filtered ``ContactSensorReading``. To pass through to a frame call instead, enable the ``contacts`` list with ``ContactSensor.add_raw_contact_data_to_frame()``.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_contact/contact_sensor.py
    :language: python
    :start-after: # [reading-raw-data]
    :end-before: # [/reading-raw-data]


API documentation
^^^^^^^^^^^^^^^^^

.. deprecated:: 6.0
   The ``isaacsim.sensors.physics`` extension is deprecated. Use ``isaacsim.sensors.experimental.physics.ContactSensor`` instead.

See the |link_ext| for the current API and |link_ext_deprecated| for the deprecated API.

.. |link_ext| raw:: html

    <a href="../py/source/extensions/isaacsim.sensors.experimental.physics/docs/index.html" target="_blank">isaacsim.sensors.experimental.physics API Documentation</a>

.. |link_ext_deprecated| raw:: html

    <a href="../py/source/extensions/isaacsim.sensors.physics/docs/index.html" target="_blank">isaacsim.sensors.physics API Documentation (deprecated)</a>
