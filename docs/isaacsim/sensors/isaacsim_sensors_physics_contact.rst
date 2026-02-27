..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaacsim_sensors_physics_contact:


===============
Contact Sensor
===============

The Contact Sensor uses the PhysX Contact Report API to generate a sensor reading similar to what you would have with contact cells, or pressure based sensors placed on the surface of an object.
The Contact Sensor API builds on the Contact Report API by providing contact data filtered by the object it was placed in, along with an optional filter only consider contacts in a specific region of the object. For example, imagine a quadruped robot with sensors in its feet. While in the simulation the entire leg is treated as a rigid body, the only place you can measure contact are on the foot pads, so you can add a region filter that will discard any contacts outside of that boundary.
The Contact Sensor API also provides persistent contact data, even when the PhysX engine stops streaming contacts to preserve compute time. While the simulation provides full information about the contacts, such as contact pairs, normals and contact points, the Contact Sensor API was designed to match real-data obtained by single-cell contact pads. Ultimately, if full contact data is needed, the Contact Sensor API gets you the filtered contact information without any changes from what was acquired in PhysX.

See the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim_short| conventions.

**Contact Sensor Properties**

#. ``radius`` parameter specifies the distance of the contact force that it would ``sensor_period``.
#. ``enabled`` parameter determines if the sensor is running or note.
#. ``min threshold`` parameter specifies the minimum amount of force to trigger a contact.
#. ``max threshold`` parameter specifies the maximum amount of force the sensor will output.
#. ``sensor period`` parameter specifies the time in between sensor measurement. A sensor period that's lower than the physics downtime will always output the latest physics data. The sensor frequency cannot go beyond the physics frequency.


GUI
===

Creating and Modifying the Contact Sensor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Assuming there is a prim present in the scene to which you want to add a contact sensor, the following steps will let you create and modify a contact sensor.

#. To create a Physics Scene, go to the top Menu Bar and click **Create > Physics > Physics Scene**. Verify that there is now a ``PhysicsScene`` :ref:`isaac_sim_glossary_prim` in the :ref:`isaac_sim_glossary_stage` panel on the right.
#. To create a contact sensor, left click on the prim to attach the contact sensor on the stage, then go to the top Menu Bar and click **Create > Sensors > Contact_sensor**.
#. To change the position and orientation of the contact sensor, use **Translate and Orientate** tab.
#. To change other contact sensor properties, click **Raw USD Properties** and properties such as min/max force threshold, enable/disable sensor, sensor period will be available to modify.

Contact Sensor Example
^^^^^^^^^^^^^^^^^^^^^^

To run the Contact Sensor Example:

#. Activate **Robotics Examples** tab from **Windows** > **Examples** > **Robotics Examples**.
#. Click **Robotics Examples** > **Sensors** > **Contact Sensor**.
#. Verify that you see a window containing the sensor's force readings color coded by each ant's arm.
#. Press the **Open Source Code** button to view the source code. The source code illustrates how to load an Ant body into the scene and then add sensors to it using the Python API.
#. Press the **PLAY** button to begin simulating.
#. Press ``SHIFT + LEFT_CLICK`` to drag the ant around  and see changes in the readings.

.. image:: /images/isim_4.5_full_tut_gui_create_contact_sensor.webp
    :align: center
    :width: 100%

OmniGraph Workflow
^^^^^^^^^^^^^^^^^^

The following is a tutorial on using OmniGraph to interact with and visualize the Contact Sensor's readings.

Scene Setup
###########

#. Add a cube to the stage by **Create > Mesh > Cube**, select the cube and drag it up. Then select the cube and right click **Add > Physics > Rigid Body with Colliders Preset**.
#. Add a physics scene by **Create > Physics > PhysicsScene**.
#. Add a ground plane by **Create> Physics > GroundPlane**.
#. Add a contact sensor by selecting the cube, and select on the top menu **Create > Sensors > Contact Sensor**.

.. image:: /images/isim_4.5_full_tut_gui_create_contact_sensor_1.webp
    :align: center
    :width: 100%
    :alt: Read Contact Sensor Action Graph set up

OmniGraph Setup
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

**Contact Sensor Visualization**

The Contact sensor position and radius can be visualized using the ``Isaac xPrim Radius Visualizer Node``, connect the xPrim input to the Contact Sensor Prim, connect ``Tick`` to ``Exec in``. Then insert the correct radius and configure the desired color and line thickness visualization, and the Contact sensor will be visible on **PLAY**.

.. note:: The spherical region only determines the boundary for contacts that will be accounted for. All contacts still only happen at the surface of the object bounded by the spherical region.

.. image:: /images/isaac_tutorial_visualize_contact.png
    :align: center
    :width: 800
    :alt: Contact Sensor Visualization Action Graph set up


Standalone Python
=================

.. _isaacsim_sensors_physics_contact_standalone_python_create_modify:

Creating and Modifying the Contact Sensor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For the example snippets below, prepare the scene using the following snippet by adding a ``PhysicsScene``, ``GroundPlane``, and ``DynamicCuboid`` prim.
The contact sensor will be attached to the latter.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_contact/creating_and_modifying_the_contact_sensor.py
    :language: python

Using Python Command
####################

Contact sensors can be created with Python using the ``IsaacSensorCreateContactSensor`` command, with available parameters to set, specified below, with default values. The only required parameter is the parent path.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_contact/using_python_command.py
    :language: python

Using Python Wrapper
####################

The contact sensor can also be created using the ``isaacsim.sensors.physics.ContactSensor`` Python wrapper class. The benefit of using the wrapper class is that it comes with additional helper functions to set the contact sensor properties and retrieve sensor data.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_contact/using_python_wrapper.py
    :language: python

.. note::
    Translation and position cannot both be defined, frequency, and ``dt`` also cannot both be defined.

Creating a contact sensor can only be done on a prim with a collider API, and it depends on a Contact Report API. Both the command and the wrapper class automatically add a Contact Report API to the parent prim. You can also manually add a Contact Report API to a prim through:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_contact/using_python_wrapper.py
    :language: python

To modify sensor parameters, you can use built-in class API calls such as ``set_frequency``, ``set_dt``, or USD attribute API calls.

Reading Sensor Output
^^^^^^^^^^^^^^^^^^^^^

The contact sensors are created dynamically on **Play**. Moving the sensor prim while the simulation is running invalidates the sensor. If you need to make hierarchical changes to the contact sensor like changing its rigid body parent, stop the simulator, make the changes, and then restart the simulation.

There are also three methods for reading the sensor output:

* using ``get_sensor_reading()`` in the sensor interface (recommended)
* ``get_current_frame()`` in the contact sensor Python class
* the OmniGraph node ``Isaac Read Contact Sensor``

The following snippets assume you have created a ``/World/Cube`` prim and contact sensor prim using one of the two snippets :ref:`above<isaacsim_sensors_physics_contact_standalone_python_create_modify>`.

**get_sensor_reading(sensor_path, use_latest_data = False)**

The get sensor reading function takes in two parameters, the ``prim_path`` to any contact sensor prim and it uses the latest data flag (optional) for retrieving the data point from the current physics step if the sensor is running at a slower rate than physics rate.
The function returns an ``CsSensorReading`` object, which contains ``is_valid``, ``time``, ``value``, and ``in_contact``.

Sample usage to get the reading from the current frame:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_contact/reading_sensor_output.py
    :language: python

**get_current_frame()**

The ``get_current_frame()`` function is a wrapper around ``get_sensor_reading(path_to_current_sensor)`` function and ``get_contact_sensor_raw_data``, and it is also a member function of the ContactSensor class. This function returns a dictionary with ``in_contact``, ``force``, ``number_of_contacts``, ``time``, ``body0``, ``body1``, ``position``, ``normal``, ``impulse``, ``contacts``, and ``physics_step`` as ``keys`` for the IMU measurement.
The ``get_current_frame()`` function uses the default parameters of ``get_sensor_reading``, so it gives you the sensor measurement at reading time.

Sample usage:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_contact/reading_sensor_output.py
    :language: python

**get_contact_sensor_raw_data()**

The contact sensor raw data will output a list of raw contact API data ``CsRawData``, which contains ``time``, ``dt``, ``body0``, ``body1``, ``position``, ``normal``, and ``impulse``. The raw data disregards sensor thresholds. Contacts with the parent body below the force threshold appear here even though they are discarded in the processed sensor reading ``CsSensorReading``.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_contact/reading_sensor_output.py
    :language: python

.. warning::
    This function is deprecated and will be replaced in a future release.


API Documentation
^^^^^^^^^^^^^^^^^

See the |link_ext| for complete usage information.

.. |link_ext| raw:: html

    <a href="../py/source/extensions/isaacsim.sensors.physics/docs/index.html" target="_blank">API Documentation</a>
