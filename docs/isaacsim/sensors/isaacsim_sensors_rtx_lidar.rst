..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.





.. _isaacsim_sensors_rtx_lidar:

==================
RTX Lidar Sensor
==================


.. figure:: /images/isim_4.5_full_ref_viewport_rtx_lidar_warehouse.png
    :align: center
    :width: 800


RTX Lidar sensors are simulated at render time on the GPU with RTX hardware.
Their results are then copied to the ``GenericModelOutput`` AOV for use.

.. warning::

    **Multi-GPU setups and RTX Lidar**

    On systems with multiple GPUs (MGPU), some RTX Lidar assets can sometimes cause a fatal
    application crash accompanied by CUDA error 700 messages in the log.

    If you encounter this issue, switch to single-GPU rendering by launching
    |isaac-sim_short| with:

    .. code-block:: bash

        ./isaac-sim.sh --/renderer/multiGpu/enabled=false

    In standalone Python, pass ``multi_gpu=False`` to the ``SimulationApp`` constructor.

.. _isaacsim_sensors_rtx_lidar_how_they_work:

Overview
--------

RTX Lidars are rendered using ``OmniLidar`` prims, with the ``OmniSensorGenericLidarCoreAPI`` schema applied,
as configured by attributes on the prim. After attaching a render product to the ``OmniLidar`` prim, and setting
the ``GenericModelOutput`` AOV on the render product, the RTXSensor renderer will write Lidar render results to the AOV.

The ``OmniSensorGenericLidarCoreAPI`` schema is defined in the ``omni.usd.schema.omni_sensors`` extension, documented `here <http://omniverse-docs.s3-website-us-east-1.amazonaws.com/omni.usd.schema.omni_sensors/107.3.0/omni_sensors_schema.html>`_.

How to Create an RTX Lidar
--------------------------

The ``isaacsim.sensors.experimental.rtx`` extension provides Python APIs for creating RTX Lidars. In addition, the ``omni.replicator.core``
extension provides even lower-level APIs for creating ``OmniLidar`` prims (including batch creation) and attaching render
products to them.

Create an RTX Lidar Using the ``Lidar`` Class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``Lidar`` class provides a high-level Python interface for creating and wrapping ``OmniLidar`` prims.
Use ``Lidar.create()`` to create a new sensor from a known configuration name or USD file, or ``Lidar(path)``
to wrap an existing ``OmniLidar`` prim on the stage.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_lidar/create_an_rtx_lidar_through_the_lidar_class.py
    :language: python

.. image:: /images/isim_5.0_full_ext-isaacsim.sensors.rtx-15.1.1_gui_rtx_lidar_create_lidar_rtx.png
    :align: center
    :width: 800
    :alt: The Isaac Sim UI after creating a Lidar with the snippet shown above.

The snippet above creates a reference to ``Example_Rotary.usda`` as an ``OmniLidar`` prim in the stage at the
specified ``translations`` with the specified ``orientations``, at path ``/World/lidar``. The ``Example_Rotary``
config does not support variant sets, so ``variant`` is unused. The prim's ``omni:sensor:Core:scanRateBaseHz``
attribute is set from 10 Hz (default) to 20 Hz via the ``attributes`` dictionary.

Review the `OmniSensorGenericLidarCoreAPI <https://docs.omniverse.nvidia.com/kit/docs/omni.usd.schema.omni_sensors/107.3.1/omni_sensors_schema.html#omnisensorgenericlidarcoreapi>`_
schema and `OmniSensorGenericLidarCoreEmitterStateAPI <https://docs.omniverse.nvidia.com/kit/docs/omni.usd.schema.omni_sensors/107.3.1/omni_sensors_schema.html#omnisensorgenericlidarcoreemitterstateapi>`_
schema in the ``omni.usd.schema.omni_sensors`` extension to learn what attributes can be set on the ``OmniLidar`` prim.

.. note::

   ``Lidar.create()`` accepts either ``config`` (a registered configuration name from
   ``isaacsim.sensors.experimental.rtx.SUPPORTED_LIDAR_CONFIGS``) **or** ``usd_path`` (a direct path
   to an ``OmniLidar`` USD asset) — the two are mutually exclusive. Both ``Lidar.create()`` and
   ``Lidar(...)`` accept ``schemas`` (a list of additional USD schemas to apply) and ``attributes``
   (a dict of prim attributes to author). Transforms are passed as plural arrays
   (``positions=[[...]]`` / ``translations=[[...]]`` / ``orientations=[[...]]`` / ``scales=[[...]]``);
   only ``N=1`` is supported per sensor.

Tick Rate
^^^^^^^^^

The ``tick_rate`` parameter (Hz) controls how frequently the sensor renders. A value of ``0``
(the default) enables autotrigger mode, where the sensor renders every simulation frame. Setting a
nonzero value causes the sensor to render at the specified frequency independently of the simulation
step rate. This maps to the ``omni:sensor:tickRate`` prim attribute.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_lidar/set_lidar_tick_rate.py
    :language: python

.. warning::

    For ``OmniLidar`` prims, ``tick_rate`` (i.e. ``omni:sensor:tickRate``) **must** equal
    ``omni:sensor:Core:scanRateBaseHz`` for scan accumulation and multi-tick rendering to behave
    correctly. Mismatched values cause the lidar to emit partial scans every frame instead of
    accumulating to a full scan, which silently breaks LaserScan publishing and any pipeline that
    expects a full scan per tick. See
    :ref:`isaac_sim_sensors_multitick_lidar_tickrate_must_match_scanrate` for details.

.. note::

    ``tick_rate`` is the recommended replacement for the deprecated ``frameSkipCount`` parameter
    on ROS2 helper nodes. For the full migration story, see
    :ref:`isaac_sim_sensors_multitick_rendering`.

Auxiliary Output Level
^^^^^^^^^^^^^^^^^^^^^^

RTX Lidar exposes auxiliary data through the ``aux_output_level`` constructor parameter.
Valid values are ``"NONE"`` (default), ``"BASIC"``, ``"EXTRA"``, ``"FULL"``.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_lidar/set_lidar_aux_output_level.py
    :language: python

See :ref:`isaacsim_sensors_rtx_aux_output_level` for the full attribute-flow explanation and the
migration from the removed ``omni:sensor:Core:auxOutputType`` attribute, and
:ref:`isaacsim_sensors_rtx_known_issue_gmo_channels` for a known issue when multiple RTX sensors
with different auxiliary levels share a stage. See :ref:`rtx_sensor_annotator_descriptions` for
the per-level field listing.

Scan Accumulation
^^^^^^^^^^^^^^^^^
The ``accumulate_outputs`` parameter (default ``True``) controls the
``omni:sensor:Core:accumulateOutputs`` prim attribute. When ``True``, the lidar accumulates data
over multiple frames until a full scan is complete. For rotary lidars, a full scan corresponds to a
360-degree rotation; for solid-state lidars, a full scan covers the full azimuth sweep.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_lidar/disable_lidar_scan_accumulation.py
    :language: python

.. warning::

    Scan accumulation only behaves correctly when ``omni:sensor:tickRate`` equals
    ``omni:sensor:Core:scanRateBaseHz`` on the prim. With mismatched values the lidar produces
    partial scans every frame regardless of ``accumulate_outputs``. See
    :ref:`isaac_sim_sensors_multitick_lidar_tickrate_must_match_scanrate`.

How to Collect Data from an RTX Lidar
-------------------------------------

The recommended method for collecting data from an RTX Lidar is to use the ``LidarSensor`` runtime class,
which wraps a ``Lidar`` authoring object and manages Replicator Annotators.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_lidar/collect_data_with_lidar_sensor_basic.py
    :language: python

|isaac-sim_short| also offers lower-level :ref:`rtx_sensor_annotator_descriptions` that can be attached
directly to render products. Refer to :ref:`rtx_sensor_reading_gmo_buffer` for
more details on how to use the ``GenericModelOutput`` annotator.

.. _isaacsim_sensors_rtx_lidar_visualization:

Visualizing RTX Lidar Output
----------------------------

There are several ways to visualize RTX Lidar point cloud data in |isaac-sim_short|:

Debug Draw
^^^^^^^^^^

The :ref:`Debug Draw Extension <isaac_debug_draw>` provides a performance-efficient method for visualizing point clouds directly in the viewport.
The geometry drawn with Debug Draw remains persistent across frames and does not interact with the physics scene.

The standalone example ``create_lidar_basic.py`` demonstrates using Debug Draw to visualize RTX Lidar output:

.. code-block:: bash

    # Basic lidar creation with debug draw visualization
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/create_lidar_basic.py

For more information on Debug Draw APIs, refer to :ref:`isaac_debug_draw` and :ref:`isaac_sim_app_util_snippets`.

Viewport Debug Views
^^^^^^^^^^^^^^^^^^^^

You can visualize non-visual material IDs in the viewport by selecting **RTX - Real-Time** > **Debug View** > **Non-Visual Material ID**.
This shows how materials appear to RTX sensors, which is useful for debugging material configurations.
Refer to :ref:`isaacsim_sensors_rtx_materials` for details.

RViz2 Visualization
^^^^^^^^^^^^^^^^^^^

When using ROS2, point cloud data can be visualized in RViz2. Refer to the :ref:`ROS2 Integration <isaacsim_sensors_rtx_lidar_ros2>` section below.

.. _isaacsim_sensors_rtx_lidar_ros2:

ROS2 Integration
----------------

|isaac-sim_short| provides full support for publishing RTX Lidar data to ROS2 as standard message types.

Supported Message Types
^^^^^^^^^^^^^^^^^^^^^^^

- ``sensor_msgs/PointCloud2`` - Full 3D point cloud data
- ``sensor_msgs/LaserScan`` - 2D laser scan data (for 2D Lidar configurations)

For a comprehensive guide on integrating RTX Lidar sensors with ROS2, including:

- Adding RTX Lidar ROS2 bridge nodes via OmniGraph
- Publishing LaserScan and PointCloud2 messages
- Using the menu shortcut to create RTX Lidar sensor publishers
- Visualizing multiple sensors in RViz2
- Exposing RTX Lidar metadata (intensity, object IDs) in PointCloud2 messages

Refer to the :ref:`RTX Lidar ROS2 Tutorial <isaac_sim_app_tutorial_ros2_rtx_lidar>`.

Quick Start
^^^^^^^^^^^

To add ROS 2 publishing for an RTX Lidar sensor:

1. Create an RTX Lidar sensor using the methods described above.
2. Go to **Tools** > **Robotics** > **ROS 2 OmniGraphs** > **RTX Lidar**.
3. Configure the graph path, Lidar prim, frame ID, and select the data types to publish.
4. Press **Play** to begin publishing.

.. _isaacsim_sensors_rtx_lidar_config_library:

RTX Lidar Asset Library
-----------------------

|isaac-sim_short| includes a library of :ref:`isaac_assets_nonvisual_sensors_rtx_lidar` that can be loaded
onto the stage by specifying the ``config`` and ``variant`` parameters of ``Lidar.create()``. The ``config`` parameter can be the following:

* The exact name of a Lidar model USD file without extension, as provided in the *Content Browser* and noted in the :ref:`isaac_assets_nonvisual_sensors_rtx_lidar` library (for example, ``HESAI_XT32_SD10``).
* The exact name of a Lidar model USD file as noted above, omitting the vendor name (for example, ``XT32_SD10``).

The optional ``variant`` parameter selects a specific variant of the provided Lidar configuration. ``variant`` accepts two forms:

* A flat string for USDs that author a single variant set named ``sensor`` (most configurations, including the Ouster OS family). The string is applied against that ``sensor`` set.
* A ``dict[str, str]`` mapping ``{variant_set: variant_name, ...}`` for USDs that author multiple variant sets (notably the SICK family, which uses ``Product`` and ``Profile`` sets). Pairs are applied in dict insertion order, so outer variant sets must come first.

The full set of supported configs and their variant shapes is exposed via ``isaacsim.sensors.experimental.rtx.SUPPORTED_LIDAR_CONFIGS``; iterate over it to enumerate the available ``(config, variant)`` combinations programmatically.

The snippet below loads a SICK picoScan100 Lidar with the ``picoScan150Pro`` product and the ``Profile11_15Hz_1p0deg`` profile selected.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_lidar/create_lidar_from_config.py
    :language: python

Sensor Materials
----------------

The material system for RTX Lidar allows content creators to assign sensor material types to partial material prim names on a USD stage. Lidar return behavior depends on material properties (for example, emissivity, reflectivity),
as described below.

.. toctree::
    :maxdepth: 1

    ./isaacsim_sensors_rtx_materials.rst

Standalone Examples
-------------------

For examples of creating and/or collecting data from a RTX Lidar, refer to the following:

**Basic Creation and Visualization**

.. code-block:: bash

    # Basic lidar creation with debug draw visualization
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/create_lidar_basic.py

    # Lidar with vendor configs (Ouster, SICK, HESAI) and variants
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/create_lidar_with_config_and_variants.py

**Data Collection and Inspection**

.. code-block:: bash

    # Inspect GenericModelOutput (GMO) data at different auxiliary levels
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/inspect_lidar_gmo.py --aux-data-level FULL

    # Resolve object IDs to USD prim paths for semantic segmentation
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/resolve_lidar_object_ids.py

**Robot Integration**

.. code-block:: bash

    # Lidar + LidarSensor integration with a wheeled robot
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/lidar_robot_integration.py

**ROS2 Integration**

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.ros2.bridge/rtx_lidar.py

.. note::

        Refer to the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim_short| conventions.
