..
   Copyright (c) 2025-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. meta::
    :title: Isaac Sim Physics Raycast Sensor
    :keywords: lang=en isaac isaac-sim sensors raycast physics

.. _isaacsim_sensors_physics_raycast:


=======================
Physics raycast sensor
=======================

The physics raycast sensor uses physics raycasts to measure distances between a sensor prim and surrounding geometry.
Unlike the fixed-pattern sensors in |isaac-sim_short|, the physics raycast sensor accepts explicit per-ray origin offsets, direction vectors, and optional time offsets, making it suitable for a wide range of configurations, including solid-state sensors, rotating sensors, and beam curtains.

Each physics step, the sensor casts rays from the prim's world-space position (plus per-ray origin offsets) along the specified directions.
When ``rayTimeOffsets`` are provided, only the subset of rays whose time offsets fall within the current physics step's time window are fired, producing a sweeping pattern over multiple steps.

See the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim_short| conventions.

**Physics raycast sensor properties**

#. ``enabled`` parameter determines if the sensor is running or not.
#. ``numRays`` (unsigned int) parameter specifies the authoritative ray count. ``rayOrigins`` and ``rayDirections`` must each have exactly this many elements. This is set automatically when using ``Raycast.create()`` or the ``Raycast`` authoring constructor.
#. ``minRange`` parameter specifies the minimum detection range in stage length units. Rays start at ``origin + direction * minRange``.
#. ``maxRange`` parameter specifies the maximum detection range in stage length units.
#. ``rayOrigins`` parameter specifies per-ray origin translations in the sensor's local coordinate frame.
#. ``rayDirections`` parameter specifies per-ray cast direction vectors in the sensor's local coordinate frame. Vectors are normalized before use.
#. ``rayTimeOffsets`` parameter specifies per-ray time offsets in seconds. When provided, the sensor fires only rays whose offsets fall within the current physics step, enabling sweeping patterns. The sweep period is ``max(rayTimeOffsets)``.
#. ``outputFrameOfReference`` parameter selects the coordinate frame for hit positions and normals. ``SENSOR`` returns results in the sensor's local coordinate frame; ``WORLD`` returns results in world coordinates.
#. ``reportHitPrimPaths`` parameter enables resolving the USD prim path of each hit surface.

For the full USD attribute definitions, see the :ref:`Raycast Sensor schema reference <isaac_sim_sensor_schema_raycast>`.

.. note::

    All sensor properties are read once when the simulation starts. Changing attribute values while the simulation is playing has no effect; stop and restart the simulation to pick up changes.


.. _isaacsim_sensors_physics_raycast_gui:

GUI
===

Creating a physics raycast sensor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create a physics raycast sensor from the GUI:

#. To create a Physics Scene, go to the top Menu Bar and click **Create > Physics > Physics Scene**. Verify that there is now a ``PhysicsScene`` :ref:`isaac_sim_glossary_prim` in the :ref:`isaac_sim_glossary_stage` panel on the right.
#. Optionally select a parent prim in the **Stage** panel.
#. Go to the top Menu Bar and click **Create > Sensors > Physics Raycast Sensor** and choose one of the preset configurations:

   - **Solid State Physics Raycast Sensor**: A rectangular grid of rays with configurable horizontal and vertical field of view.
   - **Rotating Physics Raycast Sensor**: Rays distributed across 360 degrees with time offsets that produce a sweeping pattern at 1 Hz.
   - **Beam Curtain Physics Raycast Sensor**: Parallel rays spread vertically for proximity detection.

#. To change the position and orientation of the sensor, select the sensor prim and modify the **Transform** properties under the **Property** tab.
#. To change sensor properties, expand the **Raw USD Properties** section to modify range, ray geometry, and output frame settings.

Physics raycast sensor example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To run the physics raycast sensor example:

#. Activate **Robotics Examples** tab from **Windows** > **Examples** > **Robotics Examples**.
#. Click **Robotics Examples** > **Sensors** > **Physics Raycast Sensor** > **Load Scene**.
#. Verify that three physics raycast sensors are created: a solid state sensor (green rays), a rotating sensor (blue rays), and a beam curtain sensor (red rays).
#. Press the **Play** button to begin simulating.
#. Observe the debug ray visualization in the viewport and the hit count / min depth readings in the example window.

.. image:: ../images/isim_6.0_full_tut_viewport_physics_raycast_sensor_visualization.gif
   :alt: Physics raycast sensor visualization showing solid state (green), rotating (blue), and beam curtain (red) sensors
   :align: center

OmniGraph workflow
^^^^^^^^^^^^^^^^^^

The following is a tutorial on using OmniGraph to read and visualize physics raycast sensor data.

Scene setup
###########

#. Create a Physics Scene by **Create > Physics > Physics Scene**.
#. Add collision geometry (e.g., **Create > Mesh > Cube** and apply **Add > Physics > Colliders Preset**).
#. Add a ground plane by **Create > Physics > GroundPlane**.
#. Create a physics raycast sensor by **Create > Sensors > Physics Raycast Sensor > Solid State Physics Raycast Sensor**.

OmniGraph setup
###############

To set up the |omnigraph_short| to collect readings from this sensor:

#. Create a new action graph by navigating to **Window > Graph Editors > Action Graph**, and selecting **New Action Graph** in the new tab that opens.
#. Add the following nodes to the graph:

   - **On Playback Tick** (``omni.graph.action.OnPlaybackTick``): Executes the graph every simulation timestep.
   - **Isaac Read Physics Raycast Sensor** (``isaacsim.sensors.physics.IsaacReadRaycastSensor``): Reads the physics raycast sensor. In the **Property** tab, set ``Physics Raycast Sensor Prim`` to the path of your sensor prim (e.g., ``/World/Sensors/Solid_State_Physics_Raycast_Sensor``).
   - **Debug Draw RayCast** (``isaacsim.util.debug_draw.DebugDrawRayCast``): Visualizes the rays in the viewport.

#. Configure the **Debug Draw RayCast** node:

   - Set ``inputs:doTransform`` to **False**. The read node already provides world-space beam origins and endpoints; applying an additional transform will produce incorrect visualization.

#. Connect the nodes with **all five** required connections:

   - **On Playback Tick** ``outputs:tick`` → **Isaac Read Physics Raycast Sensor** ``inputs:execIn``
   - **Isaac Read Physics Raycast Sensor** ``outputs:execOut`` → **Debug Draw RayCast** ``inputs:exec``
   - **Isaac Read Physics Raycast Sensor** ``outputs:beamOrigins`` → **Debug Draw RayCast** ``inputs:beamOrigins``
   - **Isaac Read Physics Raycast Sensor** ``outputs:beamEndPoints`` → **Debug Draw RayCast** ``inputs:beamEndPoints``
   - **Isaac Read Physics Raycast Sensor** ``outputs:numRays`` → **Debug Draw RayCast** ``inputs:numRays``

   .. important::

      The ``numRays`` connection is required. Without it, the Debug Draw node defaults to 0 rays and renders nothing. Similarly, ``doTransform`` must be set to False because the beam origins and endpoints from the read node are already in world coordinates.

#. Press the **Play** button. If set up correctly, ray lines appear from the sensor to hit points in the viewport.

.. image:: ../images/isim_6.0_full_tut_gui_physics_raycast_omnigraph.png
   :alt: OmniGraph setup with Isaac Read Physics Raycast Sensor and Debug Draw nodes
   :align: center

Programmatic OmniGraph setup
############################

The same graph can be created programmatically using ``og.Controller``:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_raycast/omnigraph_setup.py
    :language: python

.. note::

    Key differences from a naive setup that may cause visualization to fail:

    - **``doTransform`` must be False**: The read node outputs world-space coordinates. The Debug Draw node's ``doTransform`` input applies an additional matrix transform by default, which displaces the rays to incorrect positions.
    - **``numRays`` must be connected**: Without this, the draw node doesn't know how many rays to render and defaults to zero.
    - **Execution chain must be complete**: ``execIn`` → ``execOut`` → ``exec`` ensures the draw node fires after the read node has populated its outputs.


.. _isaacsim_sensors_physics_raycast_standalone_python:

Standalone Python
=================

.. _isaacsim_sensors_physics_raycast_standalone_python_create_modify:

Creating a physics raycast sensor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For the example snippets below, prepare the scene using the following snippet by adding a ``PhysicsScene``, collision geometry, and a sensor parent ``Xform``.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_raycast/scene_setup.py
    :language: python

Using the Python API
####################

Physics raycast sensors are created with ``Raycast.create()`` (the authoring class) and the returned authoring object is wrapped with ``RaycastSensor`` for runtime data access. You must provide ``ray_origins`` and ``ray_directions`` arrays of the same length. The path must include the parent prim path.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_raycast/using_python_api.py
    :language: python

Using time offsets
##################

To create a sensor with a sweeping pattern, provide ``ray_time_offsets``. Rays are only fired when their time offset falls within the current physics step's time window. The sweep period equals ``max(ray_time_offsets)``.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_raycast/using_time_offsets.py
    :language: python

Using the RaycastSensor runtime
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``RaycastSensor`` class wraps an existing ``Raycast`` authoring object or an existing ``IsaacRaycastSensor`` prim for runtime data access. Configure and create new prims with ``Raycast.create()``.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_raycast/using_raycast_sensor_wrapper.py
    :language: python

Reading sensor output
^^^^^^^^^^^^^^^^^^^^^

The physics raycast sensor is created dynamically on **Play**. Use ``RaycastSensor.get_sensor_reading()`` to read raw sensor data, or ``RaycastSensor.get_data()`` for a structured dictionary. The reading includes depths, hit positions, hit normals, and optionally hit prim paths.

The following snippet assumes you have created a sensor prim using one of the snippets :ref:`above<isaacsim_sensors_physics_raycast_standalone_python_create_modify>`.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_physics_raycast/reading_sensor_output.py
    :language: python

The ``get_sensor_reading()`` function returns a ``RaycastSensorReading`` object with the following properties:

* ``is_valid``: Whether the reading contains valid data.
* ``ray_count``: Number of rays in the reading.
* ``time``: Simulation time of this reading in seconds.
* ``depths``: Per-ray hit distances in stage length units. Rays that miss return ``maxRange``.
* ``hit_positions``: Per-ray hit positions as an Nx3 array, in the frame specified by ``outputFrameOfReference``.
* ``hit_normals``: Per-ray surface normals at hit points as an Nx3 array.
* ``hit_prim_paths``: Per-ray USD prim paths of hit surfaces (only populated when ``reportHitPrimPaths`` is enabled).
* ``ray_origins_world``: Per-ray world-space origins as an Nx3 array.
* ``ray_end_points_world``: Per-ray world-space end points as an Nx3 array (useful for debug visualization).

The ``get_data()`` function returns a structured dictionary with ``depths``, ``hit_positions``, ``hit_normals``, ``hit_prim_paths``, ``time``, and ``physics_step``. ``ray_origins_world`` and ``ray_end_points_world`` are only available on the raw ``get_sensor_reading()`` result.


API documentation
^^^^^^^^^^^^^^^^^

See the |link_ext| for complete usage information.

.. |link_ext| raw:: html

    <a href="../py/source/extensions/isaacsim.sensors.experimental.physics/docs/index.html" target="_blank">API Documentation</a>
