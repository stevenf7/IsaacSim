..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.





.. meta::
    :title: Isaac Sim RTX Sensors
    :keywords: lang=en isaac isaac-sim sensors rtx

.. _isaacsim_sensors_rtx:

===========
RTX Sensors
===========

RTX sensors in |isaac-sim_short| use the |rtx|'s RTX Sensor SDK to sense the environment, enabling interaction with materials in visual and non-visual spectra.
This means an RTX-based Lidar can model returns from light interaction with transparent or reflective surfaces, and an RTX-based Radar can model returns accounting for
material emissivity and reflectivity in the radio spectrum.

|isaac-sim_short| organizes utilities supporting RTX sensors into the ``isaacsim.sensors.experimental.rtx`` extension.

Getting Started
---------------

To get started with RTX sensors:

1. **Add a sensor to your scene**: Use **Create** > **Isaac** > **Sensors** > **RTX Lidar** or **RTX Radar** from the menu, or use the Python APIs described in the sensor-specific pages below.

2. **Collect data**: Attach :ref:`annotators <rtx_sensor_annotator_descriptions>` to the sensor to extract point cloud data, scan buffers, or raw ``GenericModelOutput`` data.

3. **Visualize output**: Use the :ref:`Debug Draw Extension <isaac_debug_draw>` to visualize point clouds, or configure viewport debug views.

4. **Integrate with ROS2**: Follow the :ref:`RTX Lidar ROS2 Tutorial <isaac_sim_app_tutorial_ros2_rtx_lidar>` to publish sensor data as ``PointCloud2`` or ``LaserScan`` messages.

Sensor Types
------------

.. toctree::
    :maxdepth: 1

    ./isaacsim_sensors_rtx_lidar
    ./isaacsim_sensors_rtx_radar
    ./isaacsim_sensors_rtx_acoustic

Data Collection and Materials
-----------------------------

.. toctree::
    :maxdepth: 1

    ./isaacsim_sensors_rtx_annotators
    ./isaacsim_sensors_rtx_materials

Advanced Topics
---------------

.. toctree::
    :maxdepth: 1

    ./isaacsim_sensors_rtx_custom

Extension Architecture
----------------------

RTX sensors are built using the ``omni.sensors`` extension suite. To understand more about how RTX sensors are modeled,
and how to build your own, review the following documentation:

- `Omniverse Common Extension <http://omniverse-docs.s3-website-us-east-1.amazonaws.com/omni.sensors.nv.common/2.7.0-coreapi/common_extension.html>`_
- `Omniverse Lidar Extension <http://omniverse-docs.s3-website-us-east-1.amazonaws.com/omni.sensors.nv.lidar/2.7.0-coreapi/lidar_extension.html>`_
- `Omniverse Radar Extension <http://omniverse-docs.s3-website-us-east-1.amazonaws.com/omni.sensors.nv.radar/2.8.0-coreapi/radar_extension.html>`_
- `Omniverse Materials Extension <http://omniverse-docs.s3-website-us-east-1.amazonaws.com/omni.sensors.nv.materials/1.6.0-coreapi/materials_extension.html>`_

.. _isaacsim_sensors_rtx_settings:

Important Settings
------------------

The following settings affect RTX sensor behavior and performance:

.. csv-table::
    :header: "Setting", "Default", "Description"
    :widths: 40, 15, 45

    "``--/app/sensors/nv/lidar/outputBufferOnGPU``", "``false``", "Keep Lidar return buffer on GPU for post-processing. Must be ``false`` for annotators to work correctly."
    "``--/app/sensors/nv/radar/outputBufferOnGPU``", "``false``", "Keep Radar return buffer on GPU for post-processing. Must be ``false`` for annotators to work correctly."
    "``--/app/sensors/nv/lidar/publishNormals``", "``false``", "Enable hit normal output. Increases VRAM usage."
    "``--/rtx/materialDb/nonVisualMaterialCSV/enabled``", "``false``", "Enable non-visual materials using USD attributes."
    "``--/rtx/materialDb/nonVisualMaterialSemantics/prefix``", "``omni:simready:nonvisual``", "Specify the non-visual material USD attribute prefix."
    "``--/rtx/rtxsensor/useHydraTimeAlways``", "``true``", "Use Hydra time (``omni.timeline``) in RTX sensor models."
    "``--/rtx-transient/stableIds/enabled``", "``false``", "Enable stable 128-bit object IDs for semantic segmentation."
    "``--/renderer/raytracingMotion/enabled``", "``false``", "Enable Motion BVH for motion compensation and Doppler effects."

Motion BVH
----------

RTX sensors use Motion BVH to improve accuracy when modeling motion-related sensor effects, for example, the motion of objects during sensor exposure, or the motion of the sensor itself as it collects data.

By default, Motion BVH is disabled in |isaac-sim_short| to improve performance. The following RTX Sensor features are affected by Motion BVH:

- RTX Lidar

  - Motion BVH must be enabled for RTX Lidar motion compensation to work correctly.

- RTX Radar

  - Motion BVH must be enabled for the Doppler effect, and therefore RTX Radar entirely, to be modeled correctly.

.. _isaac_sim_sensors_rtx_how_to_enable_motion_bvh:

How to Enable Motion BVH
########################

.. note:: Enabling Motion BVH can significantly increase rendering time by increasing VRAM usage for all sensors and must be left disabled when not needed.

There are two ways to enable Motion BVH:

1. In standalone Python workflows, you can enable Motion BVH by specifying ``enable_motion_bvh`` as ``True`` in the ``SimulationApp`` constructor:

  .. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx/how_to_enable_motion_bvh.py
      :language: python

2. In all workflows, you can enable Motion BVH by specifying the following settings on the command line:

  .. code-block:: bash

    --/renderer/raytracingMotion/enabled=true \
    --/renderer/raytracingMotion/enableHydraEngineMasking=true \
    --/renderer/raytracingMotion/enabledForHydraEngines='0,1,2,3,4'

.. _isaacsim_sensors_rtx_troubleshooting:

Troubleshooting and Known Issues
--------------------------------

Common Issues
#############

**Annotators return empty data**
    Ensure the simulation timeline is playing. RTX Sensor Annotators rely on the timeline to collect data.
    Also verify that ``--/app/sensors/nv/lidar/outputBufferOnGPU`` or ``--/app/sensors/nv/radar/outputBufferOnGPU`` is left at its default value of ``false`` — annotators read return data from host buffers, so forcing the GPU-resident path will leave the annotator outputs empty.

**Point cloud appears to "drag" behind moving objects**
    If the Lidar rotation rate is slower than the frame rate, accumulated scan data may contain returns from multiple frames.
    This is expected behavior for rotating Lidars. Consider using per-frame output instead of accumulated scans.

**Lidar scans are incomplete in standalone Python workflows**
    Consider setting ``--/app/player/useFixedTimeStepping=true`` to force frames to have a fixed time step, ensuring the Lidar model does not discard points if a frame has a slightly
    longer simulated time than the Lidar scan period. This setting is ``true`` by default in the full Isaac Sim app, but ``false`` by default in standalone Python workflows.

**Radar simulation does not show Doppler effects**
    Motion BVH must be enabled for Doppler effects to be modeled correctly. See :ref:`isaac_sim_sensors_rtx_how_to_enable_motion_bvh`.

**Timestamps are discontinuous after pause/resume**
    The ``GenericModelOutput`` AOV timestamp is independent of the animation timeline and continues to increase even when paused.
    This is expected behavior.

Performance Considerations
##########################

- **VRAM Usage**: Each RTX sensor requires GPU memory. Multiple sensors or high-resolution configurations increase VRAM usage.
- **Motion BVH**: Enabling Motion BVH significantly increases VRAM usage and rendering time.
- **Normal Output**: Enabling ``--/app/sensors/nv/lidar/publishNormals=true`` increases VRAM usage.
- **Stable IDs**: Enabling ``--/rtx-transient/stableIds/enabled=true`` has minimal performance impact but requires additional processing for object ID resolution.

Hardware Requirements
#####################

RTX sensors require an NVIDIA RTX GPU with ray tracing support. Performance scales with GPU capabilities, particularly:

- VRAM capacity (affects number of sensors and resolution)
- Ray tracing cores (affects simulation speed)

Related Tutorials
-----------------

- :ref:`isaac_sim_app_tutorial_ros2_rtx_lidar` - Publishing RTX Lidar data to ROS2
- :ref:`isaac_debug_draw` - Visualizing point clouds and geometry
- :ref:`isaac_sim_app_util_snippets` - Rendering and visualization utilities
