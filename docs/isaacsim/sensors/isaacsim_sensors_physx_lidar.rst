..
   Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaacsim_sensors_physx_lidar:

=============
|physx| lidar
=============

.. deprecated:: 6.0
   The |physx| Lidar sensor (``isaacsim.sensors.physx``) is deprecated. Use
   ``isaacsim.sensors.experimental.physics.RaycastSensor`` as the replacement, which provides
   configurable raycast-based sensing.
   See the `isaacsim.sensors.experimental.physics API Documentation <../py/source/extensions/isaacsim.sensors.experimental.physics/docs/index.html>`_.

The |physx| lidar sensor in |isaac-sim_short| uses |physx| raycasts to simulate a Lidar.
You can set horizontal and vertical beam resolution, rotation rate, and other Lidar parameters; the
|physx| lidar then reports depth information from each beam. The |physx| lidar cannot interact with
non-visual materials, and it always reports ground truth information. For example, the Lidar measures depth
of a transparent object with respect to the Lidar, even if a beam would normally pass through the transparent
object in real life.

See the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim_short| conventions.


.. _isaacsim_sensors_physx_lidar_gui:

GUI
===

.. _isaacsim_sensors_physx_lidar_example:

|physx| lidar sensor example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To run the example:

#. Activate ``Robotics Examples`` tab from **Windows** > **Examples** > **Robotics Examples**.
#. Click **Robotics Examples** > **Sensors** > **Physx Lidar Sensor**.
#. Press the **Load Sensor** button.
#. Press the **Load Scene** button.
#. Press the **Open Source Code** button to view the source code. The source code illustrates how to add and control the sensor using the Python API.
#. Press the **Play** button to begin simulating.


.. image:: ../images/isim_4.5_full_tut_viewport_rotating_sensor.webp
    :align: center
    :width: 100%
    :alt: PhysX rotating Lidar sensor example viewport.

Adding a |physx| lidar sensor to a simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Scene setup
###########

Begin setting up the scene by creating a ``PhysicsScene`` and a ``PhysX Lidar`` in the environment:

#. To create a Physics Scene, go to the top Menu Bar and click **Create > Physics > Physics Scene**. Verify that there is now a ``PhysicsScene`` :ref:`isaac_sim_glossary_prim` in the :ref:`isaac_sim_glossary_stage` panel on the right.
#. To create a Lidar, go to the top Menu Bar and click **Create > Sensors > PhysX Lidar > Rotating**.
   Next, set the Lidar properties for rotation and visualization:
#. Select the newly created Lidar prim from the :ref:`isaac_sim_glossary_stage` panel.
#. After selecting it, the **Property** panel in the lower left populates with all available Lidar properties.
#. Scroll down in the **Property** panel to the **Raw USD Properties** section.
#. Enable the **drawLines** checkbox to enable line rendering.
#. Set the revolutions per second to ``1 Hz`` by setting ``rotationRate`` to ``1.0``.

   - To fire LIDAR rays in all directions at once, set the ``rotationRate`` to ``0.0``.

.. image:: ../images/isim_4.5_full_tut_gui_rotating_sensor_2.webp
    :align: center
    :width: 100%
    :alt: PhysX Lidar raw USD properties.

.. note::
    You can update all of the Lidar parameters on the fly while the stage is running.
    When the rotation rate reaches zero or less, the Lidar prim casts rays in all directions based on your FOV and resolution.

Set up collision detection
##########################

The Lidar can only detect objects with **Collisions Enabled**. Add an object for the Lidar to detect:

1. Go to the top Menu Bar and click **Create > Mesh > Cube**.
#. Translate the cube to ``(2, 0, 0)``.

Next, add a Physics Collider to the Cube:

#. With the Cube selected, go to the **Property** panel and click the **+ Add** button.
#. Select **+ Add > Physics > Collider**.

.. image:: ../images/isim_4.5_full_tut_viewport_rotating_sensor_3.webp
    :align: center
    :width: 100%
    :alt: PhysX Lidar rays intersecting a cube.


- Use the mouse to move the Cube around the scene and see how the Lidar rays interact with the geometry.

Attach a Lidar to geometry
##########################

For most use cases, attach Lidars to more complex assemblies, such as cars or robots.
Use a Cylinder as a placeholder for a more complex prim.
Add a Cylinder to the scene and nest the Lidar prim under it:

#. Right click in the viewport and select **Create > Mesh > Cylinder**.
#. Set the translation of the Cylinder to ``(0, 0, 0)``.
#. In the :ref:`isaac_sim_glossary_stage` panel, drag-and-drop the ``LIDAR`` prim onto the ``Cylinder``.
#. This makes the ``Cylinder`` the parent of the ``LIDAR``. When the ``Cylinder`` moves, the ``LIDAR`` moves with it. All information reported by the LIDAR is now relative to the ``Cylinder``.
#. Add an offset to ``LIDAR`` to precisely position it relative to the ``Cylinder``. Select the ``LIDAR`` prim from the :ref:`isaac_sim_glossary_stage` and move it to ``(0.5, 0.5, 0)``.
#. Move the ``Cylinder`` around the environment. The LIDAR maintains this relative transform.
#. Re-select the ``LIDAR`` prim and reset its ``Translate`` value to its default setting ``(0, 0, 0)``.

.. image:: ../images/isim_4.5_full_tut_viewport_rotating_sensor_4.webp
    :align: center
    :width: 100%
    :alt: PhysX Lidar nested under a cylinder prim.


Attach a Lidar to a moving robot
################################

You can attach a LIDAR prim to a robot. You can use the Carter V1 robot as an example.

#. Open the Isaac Sim **Content Browser**, navigate to ``Robots/NVIDIA/Carter/carter_v1.usd``, and open the ``carter_v1.usd`` file.
#. Open the left wheel joint at `carter/chassis_link/left_wheel`, scroll down on the property panel, and set the `Target Velocity` to `100`.
#. Repeat the same process for the right wheel joint at `carter/chassis_link/right_wheel`.
#. Press **Play** and the Carter robot drives forward automatically.
#. Create a ``LIDAR`` by going to the top Menu Bar and clicking **Create > Sensors > PhysX LIDAR > Rotating**. The ``LIDAR`` prim is created as a child of the selected prim.
#. In the :ref:`isaac_sim_glossary_stage` panel, select your ``LIDAR`` prim and drag it onto ``/carter/chassis_link``.
#. Set the translation of the PhysX lidar to `-0.06, 0.0, 0.38` to move it to the correct location.
#. Enable draw lines and set the rotation rate to zero for easier debugging.

.. image:: ../images/isim_4.5_full_tut_viewport_rotating_sensor_3.gif
    :align: center
    :width: 100%
    :alt: PhysX Lidar attached to a moving Carter robot.

Script Editor
^^^^^^^^^^^^^

Use the Lidar Python API to create, control, and query the sensor through scripts and extensions.
Use the **Script Editor** and Python API to retrieve data from the Lidar's last sweep:

1. Go to the top menu bar and click **Window > Script Editor** to open the **Script Editor** window.
2. Add the necessary imports:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physx_lidar/lidar_scripting.py
    :language: python
    :start-after: # [imports]
    :end-before: # [/imports]

3. Grab the Stage, Simulation Timeline, and LIDAR interface:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physx_lidar/lidar_scripting.py
    :language: python
    :start-after: # [setup]
    :end-before: # [/setup]

4. Create an obstacle for the LIDAR:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physx_lidar/lidar_scripting.py
    :language: python
    :start-after: # [create-obstacle]
    :end-before: # [/create-obstacle]

5. Get the LIDAR data:

    The Lidar needs one simulation frame to get data for the first frame, so start
    the simulation by calling ``timeline.play``, wait for a frame to complete, and then pause simulation using ``timeline.pause()`` to populate the depth buffers in the Lidar.
    Because the simulation is running asynchronously with our script, use ``asyncio`` and ``ensure_future`` to wait for our script to complete
    calling ``timeline.pause()`` is optional, data from the sensor can be gathered anytime while simulating.

    .. literalinclude:: ../snippets/sensors/isaacsim_sensors_physx_lidar/lidar_scripting.py
        :language: python
        :start-after: # [get-lidar-data]
        :end-before: # [/get-lidar-data]

#. Run the full script:

.. raw:: html

    <details>
    <summary>Expand to display full code</summary>

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physx_lidar/run_the_full_script.py
    :language: python

Verify that you have the following:

.. figure:: /images/isaac_range_sensor_lidar_python.png
    :align: center
    :alt: Segmented Lidar Point Cloud

Segment a Point Cloud
#####################

This code snippet shows how to add semantic labels to the depth data for segmenting its resulting point cloud.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physx_lidar/segment_a_point_cloud.py
    :language: python

The main differences between this example and the previous are as follows:

#. The LIDAR's ``enable_semantics`` flag is set to ``True`` on creation.
#. The Cube and Sphere prims have different ``semantic labels``.
#. Use ``get_point_cloud_data`` and ``get_prim_data`` to retrieve the point cloud data and semantic IDs.

The segmented point cloud from the Lidar sensor looks like the image below:

.. figure:: /images/isim_5.1_full_tut_viewport_range_sensor_lidar_segmented_point_cloud.png
    :align: center
    :alt: Segmented Lidar Point Cloud
    :width: 100%


.. _isaacsim_sensors_physx_lidar_migration:

Migrating to the physics raycast sensor
========================================

The |physx| Lidar sensor is deprecated. Use the :ref:`Physics Raycast Sensor <isaacsim_sensors_physics_raycast>` (``isaacsim.sensors.experimental.physics.RaycastSensor``) as the replacement for rotating raycast-based lidar.

.. _isaacsim_sensors_physx_lidar_concept_mapping:

Concept mapping
---------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - |physx| Lidar
     - Physics Raycast Sensor
   * - ``rotationRate``
     - ``rayTimeOffsets``. Distribute rays across azimuthal columns and assign each column a time offset within the sweep period (``1.0 / rotation_rate``). The sensor fires only the rays whose offsets fall within the current physics step.
   * - Horizontal / vertical resolution
     - ``rayDirections``. Compute Cartesian direction vectors for each beam at the desired azimuth and elevation angles.
   * - ``minRange`` / ``maxRange``
     - ``minRange`` / ``maxRange``. Same semantics.
   * - ``drawLines``
     - Use the **Debug Draw RayCast** OmniGraph node connected to the **Isaac Read Physics Raycast Sensor** node outputs.
   * - ``_range_sensor`` Python interface (``get_linear_depth_data``, ``get_point_cloud_data``)
     - ``RaycastSensor.get_sensor_reading()`` returns depths, hit positions, hit normals, and optionally hit prim paths.
   * - ``enable_semantics`` / ``get_prim_data``
     - ``reportHitPrimPaths`` attribute. When enabled, the sensor reading includes the USD prim path of each hit surface.
   * - Setting ``rotationRate`` to ``0.0`` (fire all rays every step)
     - Omit ``rayTimeOffsets``. Without time offsets all rays fire every physics step.

.. _isaacsim_sensors_physx_lidar_interactive_example:

Interactive example
-------------------

The **Physics Raycast Sensor** example includes a rotating sensor configuration with time offsets that produces a 360-degree sweep:

- **GUI**: Open **Robotics Examples > Sensors > Physics Raycast Sensor** and click **Load Scene**.
- **Source code**: ``source/extensions/isaacsim.sensors.physics.examples/isaacsim/sensors/physics/examples/raycast_sensor.py``

See :ref:`isaacsim_sensors_physics_raycast` for the full documentation, including Python API usage and OmniGraph workflows.
