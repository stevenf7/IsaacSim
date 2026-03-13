..
   Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaacsim_sensors_physx_lidar:

=============
|physx| Lidar
=============

The |physx| Lidar sensor in |isaac-sim_short| uses |physx| raycasts to simulate a Lidar.
You can set horizontal and vertical beam resolution, rotation rate, and other Lidar parameters; the
|physx| Lidar will then report depth information from each beam. The |physx| Lidar cannot interact with
non-visual materials, it will always report ground truth information. For example, the Lidar will measure depth
of a transparent object with respect to the Lidar, even if a beam would normally pass through the transparent
object in real life.

See the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim_short| conventions.


GUI
===

.. _isaacsim_sensors_physx_lidar_example:

|physx| Lidar Sensor Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To run the example:

#. Activate ``Robotics Examples`` tab from **Windows** > **Examples** > **Robotics Examples**.
#. Click **Robotics Examples** > **Sensors** > **Physx Lidar Sensor**.
#. Press the **Load Sensor** button.
#. Press the **Load Scene** button.
#. Press the **Open Source Code** button to view the source code. The source code illustrates how to add and control the sensor using the Python API.
#. Press the **PLAY** button to begin simulating.


.. image:: ../images/isim_4.5_full_tut_viewport_rotating_sensor.webp
    :align: center
    :width: 100%

Adding |physx| Lidar Sensor to Simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Scene Setup
###########

Let's begin setting up the scene by creating a ``PhysicsScene`` and a ``PhysX Lidar`` in the environment:

#. To create a Physics Scene, go to the top Menu Bar and click **Create > Physics > Physics Scene**. Verify that there is now be a ``PhysicsScene`` :ref:`isaac_sim_glossary_prim` in the :ref:`isaac_sim_glossary_stage` panel on the right.
#. To create a LIDAR, go to the top Menu Bar and click **Create > Sensors > PhysX Lidar > Rotating**.
   Next, let's set some of the LIDAR properties for rotation and visualization:
#. Select the newly created LIDAR prim from the :ref:`isaac_sim_glossary_stage` panel.
#. After selected, the **Property** panel to the bottom left will populate with all the available properties of the LIDAR.
#. Scroll down in the **Property** panel to the **Raw USD Properties** section.
#. Enable the **drawLines** checkbox to enable line rendering.
#. Set the revolutions per second to ``1 Hz`` by setting ``rotationRate`` to ``1.0``.

   - To fire LIDAR rays in all directions at once, set the ``rotationRate`` to ``0.0``.

.. image:: ../images/isim_4.5_full_tut_gui_rotating_sensor_2.webp
    :align: center
    :width: 100%

.. note::
    You can update all of the Lidar parameters on the fly while the stage is running.
    When the rotation rate reaches zero or less, the Lidar prim will cast rays in all directions based on your FOV and resolution.

Setup Collision Detection
#########################

The LIDAR can only detect objects with **Collisions Enabled**. Let's add an object for the LIDAR to detect:

1. Go to the top Menu Bar and click **Create > Mesh > Cube**.
#. Translate the cube to ``(2, 0, 0)``.

Next, add a Physics Collider to the Cube:

10. With the Cube selected, go to the **Property** panel and click the **+ Add** button.
#. Select **+ Add > Physics > Collider**.

.. image:: ../images/isim_4.5_full_tut_viewport_rotating_sensor_3.webp
    :align: center
    :width: 100%


- Use the mouse and move the Cube around the scene to see how the LIDAR rays interact with the geometry.

Attach a LIDAR to Geometry
##########################

For most use cases, LIDARs will be attached to other more complex assemblies — such as cars or robots.
Let's learn how to attach a LIDAR to a parent geometry.
We are going to use a Cylinder as a placeholder for a more complex prim.
Add a Cylinder to the scene and nest the LIDAR prim under it:

#. Right click in the viewport and select **Create > Mesh > Cylinder**.
#. Set the translation of the Cylinder to ``(0, 0, 0)``.
#. In the :ref:`isaac_sim_glossary_stage` panel, drag-and-drop the ``LIDAR`` prim onto the ``Cylinder``.
#. This makes the ``Cylinder`` the parent of the ``LIDAR``. Now when the ``Cylinder`` moves, the ``LIDAR`` moves with it. Moreover, all information reported by the LIDAR is now relative to the ``Cylinder``.
#. Add a offset to ``LIDAR`` to precisely position it relative to the ``Cylinder``. Select the ``LIDAR`` prim from the :ref:`isaac_sim_glossary_stage` and move it to ``(0.5, 0.5, 0)``.
#. Now move the ``Cylinder`` around the environment. The LIDAR maintains this relative transform.
#. Re-select the ``LIDAR`` prim and reset its `Translate` value to its default setting ``(0, 0, 0)``.

.. image:: ../images/isim_4.5_full_tut_viewport_rotating_sensor_4.webp
    :align: center
    :width: 100%


Attach a LIDAR to a Moving Robot
################################

You can attach a LIDAR prim to a robot. You can use the Carter V1 robot as an example.

#. Open the Isaac Sim **Content Browser**, navigate to ``Robots/NVIDIA/Carter/carter_v1.usd``, and open the ``carter_v1.usd`` file.
#. Open the left wheel joint at `carter/chassis_link/left_wheel`, scroll down on the property panel, and set the `Target Velocity` to `100`.
#. Repeat the same process for the right wheel joint at `carter/chassis_link/right_wheel`.
#. Press **play** and the Carter robot should drive forward automatically.
#. Create a ``LIDAR``, go to the top Menu Bar and click **Create > Sensors > PhysX LIDAR > Rotating**. The ``LIDAR`` prim will be created as a child of the selected prim.
#. In the :ref:`isaac_sim_glossary_stage` panel, select your ``LIDAR`` prim and drag it onto ``/carter/chassis_link``.
#. Set the translation of the PhysX lidar to `-0.06, 0.0, 0.38` to move it to the correct location.
#. Enable draw lines and set the rotation rate to zero for easier debugging.

.. image:: ../images/isim_4.5_full_tut_viewport_rotating_sensor_3.gif
    :align: center
    :width: 100%

Script Editor
^^^^^^^^^^^^^

The LIDAR Python API is used to interact programmatically with a LIDAR through scripts and extensions.
It can be used to create, control, and query the sensor through scripts and extensions.
Let's use the **Script Editor** and Python API to retrieve the data from the LIDAR's last sweep:

1. Go to the top menu bar and click **Window > Script Editor** to open the **Script Editor** window.
2. Add the necessary imports:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physx_lidar/script_editor.py
    :language: python

3. Grab the Stage, Simulation Timeline, and LIDAR interface:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physx_lidar/script_editor_1.py
    :language: python

4. Create an obstacle for the LIDAR:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physx_lidar/these_commands_are_the_python_equivalent_of_the_fi.py
    :language: python

5. Get the LIDAR data:

    The Lidar needs a frame of simulation to get data for the first frame, so start
    the simulation by calling ``timeline.play`` and waiting for a frame to complete, and then pause simulation using ``timeline.pause()`` to populate the depth buffers in the Lidar.
    Because the simulation is running asynchronously with our script, use ``asyncio`` and ``ensure_future`` to wait for our script to complete
    calling ``timeline.pause()`` is optional, data from the sensor can be gathered anytime while simulating.

    .. literalinclude:: ../snippets/sensors/isaacsim_sensors_physx_lidar/these_commands_are_the_python_equivalent_of_the_fi_1.py
        :language: python

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
#. The Cube and Sphere prims are assigned different `semantic labels`.
#. ``get_point_cloud_data`` and ``get_prim_data`` are used to retrieve the Point Cloud data and Semantic IDs.

The segmented point cloud from Lidar sensor should look like the image below:

.. figure:: /images/isim_5.1_full_tut_viewport_range_sensor_lidar_segmented_point_cloud.png
    :align: center
    :alt: Segmented Lidar Point Cloud
    :width: 100%
