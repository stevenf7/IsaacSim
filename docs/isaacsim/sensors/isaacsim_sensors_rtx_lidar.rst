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

.. _isaacsim_sensors_rtx_lidar_how_they_work:

Overview
--------

.. Note:: In |isaac-sim_short| 4.5 and earlier, RTX sensors were based on ``Camera`` prims. If the ``Camera`` prim's
    ``sensorModelPluginName`` attribute was set to ``omni.sensors.nv.lidar.lidar_core.plugin``, then the
    ``Camera`` prim was used to render the Lidar. The Lidar was configured using a JSON file whose
    filename (without extension) was set in the ``Camera`` prim's ``sensorModelConfig`` attribute, assuming
    the file was present in a folder specified by the ``app.sensors.nv.lidar.profileBaseFolder`` setting.
    Support for ``Camera`` prims as RTX Lidars was deprecated in |isaac-sim_short| 5.0.

    Refer to :ref:`isaacsim_sensors_rtx_lidar_convert_json_to_omni_lidar` for details on how to convert a JSON file to a USD file containing an equivalent ``OmniLidar`` prim.

RTX Lidars are rendered using ``OmniLidar`` prims, with the ``OmniSensorGenericLidarCoreAPI`` schema applied,
as configured by attributes on the prim. After attaching a render product to the ``OmniLidar`` prim, and setting
the ``GenericModelOutput`` AOV on the render product, the RTXSensor renderer will write Lidar render results to the AOV.

The ``OmniSensorGenericLidarCoreAPI`` schema is defined in the ``omni.usd.schema.omni_sensors`` extension, documented `here <http://omniverse-docs.s3-website-us-east-1.amazonaws.com/omni.usd.schema.omni_sensors/107.3.0/omni_sensors_schema.html>`_.

How to Create an RTX Lidar
--------------------------

The ``isaacsim.sensors.rtx`` extension provides two APIs for creating RTX Lidars. In addition, the ``omni.replicator.core``
extension provides even lower-level APIs for creating ``OmniLidar`` prims (including batch creation) and attaching render
products to them.

Create an RTX Lidar Using Commands
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The lower-level ``IsaacSensorCreateRtxLidar`` command creates a reference on the stage to a known Lidar USD or USDA asset,
a generic ``OmniLidar`` prim with the appropriate schemas applied, or a ``Camera`` prim with the appropriate attributes
to support deprecated workflows.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_lidar/create_an_rtx_lidar_through_command.py
    :language: python

.. image:: /images/isim_5.0_full_ext-isaacsim.sensors.rtx-15.1.1_gui_rtx_lidar_create_command.png
    :align: center
    :width: 800
    :alt: The Isaac Sim UI after running the ``IsaacSensorCreateRtxLidar`` command shown above.


The example command above creates a reference to ``Example_Rotary.usda`` as an ``OmniLidar`` prim in the stage at the
specified ``translation`` with the specified ``orientation``, at path ``/lidar``. The prim is set to be invisible
in the stage. The ``Example_Rotary`` config does not support variant sets, so ``variant`` is unused. The prim's
``omni:sensor:Core:scanRateBaseHz`` attribute is set from 10 Hz (default) to 20 Hz.

Setting ``force_camera_prim`` to ``True`` will instead create an invisible ``Camera`` prim at the specified ``translation``
and ``orientation``, with the ``sensorModelConfig`` attribute set to ``Example_Rotary``.

Setting ``config`` to ``None`` will create a generic ``OmniLidar`` prim with the ``OmniSensorGenericLidarCoreAPI`` schema applied;
any additional keyword arguments will be passed through and set as attributes on the ``OmniLidar`` prim.

Review the `OmniSensorGenericLidarCoreAPI <https://docs.omniverse.nvidia.com/kit/docs/omni.usd.schema.omni_sensors/107.3.1/omni_sensors_schema.html#omnisensorgenericlidarcoreapi>`_
schema and `OmniSensorGenericLidarCoreEmitterStateAPI <https://docs.omniverse.nvidia.com/kit/docs/omni.usd.schema.omni_sensors/107.3.1/omni_sensors_schema.html#omnisensorgenericlidarcoreemitterstateapi>`_
schema in the ``omni.usd.schema.omni_sensors`` extension to learn what attributes can be set on the ``OmniLidar`` prim.

If you are specifying emitter state attributes, the attribute names must be prefixed with the appropriate emitter state count, for example,
``OmniSensorGenericLidarCoreEmitterStateAPI:s001:elevationDeg`` or ``OmniSensorGenericLidarCoreEmitterStateAPI:s002:azimuthDeg``.

Create an RTX Lidar Using the ``LidarRtx`` Class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The higher-level ``LidarRtx`` class provides a Python interface for creating and configuring RTX Lidars.
In addition to passing constructor arguments to the ``IsaacSensorCreateRtxLidar`` command, the ``LidarRtx``
class automatically wraps around the resulting ``OmniLidar`` prim and attaches a render product to it.

It includes APIs to attach appropriate ``isaacsim.sensors.rtx``, :ref:`annotators<rtx_sensor_annotator_descriptions>`, and any writers to the render product. It also includes APIs to read annotator and writer results each frame through a data dictionary returned by the
``get_data`` method.

An example of creating an RTX Lidar through the ``LidarRtx`` class is:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_lidar/create_an_rtx_lidar_through_the_lidarrtx_class.py
    :language: python

.. image:: /images/isim_5.0_full_ext-isaacsim.sensors.rtx-15.1.1_gui_rtx_lidar_create_lidar_rtx.png
    :align: center
    :width: 800
    :alt: The Isaac Sim UI after running the ``LidarRtx`` snippet shown above.

Similar to the command above, the specified call to ``LidarRtx`` creates a reference to ``Example_Rotary.usda`` as
an ``OmniLidar`` prim in the stage at the specified ``translation`` with the specified ``orientation``, at path
``/lidar``. The prim is set to be invisible in the stage. The ``Example_Rotary`` config does not support variant sets,
so ``variant`` is unused. The prim's ``omni:sensor:Core:scanRateBaseHz`` attribute is set from 10 Hz (default) to 20 Hz.

How to Collect Data from an RTX Lidar
-------------------------------------

The recommended method for collecting data from an RTX Lidar is to use Replicator Annotators.

|isaac-sim_short| offers multiple :ref:`rtx_sensor_annotator_descriptions`. The ``LidarRtx`` class
described above offers APIs for attaching any of those annotators to the ``OmniLidar`` prim it wraps,
as well as the ``GenericModelOutput`` annotator. Refer to :ref:`rtx_sensor_reading_gmo_buffer` for
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
    ./python.sh standalone_examples/api/isaacsim.sensors.rtx/create_lidar_basic.py

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
onto the stage by specifying the ``config`` and ``variant`` parameters of the ``IsaacSensorCreateRtxLidar`` command,
or the ``config_file_name`` parameter of the ``LidarRtx`` constructor. The ``config``  or ``config_file_name``  parameter can be the following:

* The exact name of a Lidar model USD file without extension, as provided in the *Content Browser* and noted in the :ref:`isaac_assets_nonvisual_sensors_rtx_lidar` library (for example, ``HESAI_XT32_SD10``).
* The exact name of a Lidar model USD file as noted above, but with spaces replacing underscore (for example, ``HESAI XT32 SD10``).
* The exact name of a Lidar model USD file as noted above, omitting the vendor name (for example, ``XT32_SD10``).
* The exact name of a Lidar model USD file as noted above, omitting the vendor name and replacing underscores with spaces (for example, ``XT32 SD10``). This option matches the name of the Lidar in the **Create** > **Isaac** > **Sensors** menu.

The optional ``variant`` will select the specific variant of the provided Lidar configuration, as noted in the model's documentation. For example,
the snippet below will load a SICK picoScan150 Lidar with the ``Profile_11`` variant selected.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_lidar/rtx_lidar_asset_library.py
    :language: python

Sensor Materials
----------------

The material system for RTX Lidar allows content creators to assign sensor material types to partial material prim names on a USD stage. Lidar return behavior depends on material properties (for example, emissivity, reflectivity),
as described below.

.. toctree::
    :maxdepth: 1

    ./isaacsim_sensors_rtx_materials.rst

.. _isaacsim_sensors_rtx_lidar_convert_json_to_omni_lidar:

Convert a JSON File to an OmniLidar USD File
--------------------------------------------

|isaac-sim_short| includes a utility tool to automatically convert legacy JSON Lidar configuration files to USD files containing OmniLidar prims.

The tool can be run as a standalone application using:

.. code-block:: bash

    ./python.sh tools/isaacsim.sensors.rtx/convert_lidar_json_to_usda.py

Providing the ``-h`` or ``--help`` flag will display the usage information for the tool.

The tool will automatically convert multiple provided JSON files to corresponding USD files containing an equivalent ``OmniLidar`` prim,
and can compile JSON files associated with variant configurations or profiles of the same Lidar model into a single USD, using
`USD variant sets <https://docs.omniverse.nvidia.com/usd/latest/learn-openusd/terms/variant-set.html>`_ to allow the user to select the appropriate profile when creating an ``OmniLidar`` prim.

Standalone Examples
-------------------

For examples of creating and/or collecting data from a RTX Lidar, refer to the following:

**Basic Creation and Visualization**

.. code-block:: bash

    # Basic lidar creation with debug draw visualization
    ./python.sh standalone_examples/api/isaacsim.sensors.rtx/create_lidar_basic.py

    # Lidar with vendor configs (Ouster, SICK, HESAI) and variants
    ./python.sh standalone_examples/api/isaacsim.sensors.rtx/create_lidar_with_config_and_variants.py

**Data Collection and Inspection**

.. code-block:: bash

    # Inspect GenericModelOutput (GMO) data at different auxiliary levels
    ./python.sh standalone_examples/api/isaacsim.sensors.rtx/inspect_lidar_gmo.py --aux-data-level FULL

    # Resolve object IDs to USD prim paths for semantic segmentation
    ./python.sh standalone_examples/api/isaacsim.sensors.rtx/resolve_lidar_object_ids.py

**Robot Integration**

.. code-block:: bash

    # LidarRtx class integration with a wheeled robot
    ./python.sh standalone_examples/api/isaacsim.sensors.rtx/lidar_robot_integration.py

**ROS2 Integration**

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.ros2.bridge/rtx_lidar.py

.. note::

        Refer to the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim_short| conventions.
