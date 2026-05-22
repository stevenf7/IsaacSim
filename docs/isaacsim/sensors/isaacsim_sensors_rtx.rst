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

.. deprecated:: 6.0
   The ``isaacsim.sensors.rtx`` extension is deprecated. Use ``isaacsim.sensors.experimental.rtx`` instead.
   The new extension provides equivalent sensor classes (``Lidar``/``LidarSensor``, ``Radar``/``RadarSensor``,
   plus the new ``Acoustic``/``AcousticSensor``) with a uniform authoring/runtime split.
   See :ref:`isaacsim_sensors_rtx_migration`.

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

    ./isaacsim_sensors_multitick_rendering
    ./isaacsim_sensors_rtx_custom

Extension Architecture
----------------------

RTX sensors are built using the ``omni.sensors`` extension suite. To understand more about how RTX sensors are modeled,
and how to build your own, review the following documentation:

- `Omniverse Common Extension <https://docs.omniverse.nvidia.com/kit/docs/omni.sensors.nv.common/latest/common_extension.html>`_
- `Omniverse Lidar Extension <https://docs.omniverse.nvidia.com/kit/docs/omni.sensors.nv.lidar/latest/lidar_extension.html>`_
- `Omniverse Radar Extension <https://docs.omniverse.nvidia.com/kit/docs/omni.sensors.nv.radar/latest/radar_extension.html>`_
- `Omniverse Acoustic Extension <https://docs.omniverse.nvidia.com/kit/docs/omni.sensors.nv.acoustic/3.0.0/acoustic_extension.html>`_
- `Omniverse Materials Extension <https://docs.omniverse.nvidia.com/kit/docs/omni.sensors.nv.materials/latest/materials_extension.html>`_

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
    "``--/rtx/rtxsensor/useHydraTimeAlways``", "``true``", "Use Hydra time (``omni.timeline``) in RTX sensor models. Applies only if multi-tick rendering is disabled."
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

.. _isaacsim_sensors_rtx_aux_output_level:

Auxiliary Output Level and the GenericModelOutput RenderVar
-----------------------------------------------------------

RTX Lidar, Radar, and Acoustic sensors emit a ``GenericModelOutput`` (GMO) AOV. The
amount of auxiliary data carried in each GMO frame is controlled by the
``_replicator:rendervar:GenericModelOutput:channels`` attribute on the sensor prim.

Setting the channels attribute in the UI
########################################

To set ``_replicator:rendervar:GenericModelOutput:channels`` on an OmniRadar prim from
the Isaac Sim UI:

#. Select the prim in the **Stage** window.
#. Open the **Property** tab.
#. Expand the **Array Properties** widget.
#. Click **Edit** on the ``_replicator:rendervar:GenericModelOutput:channels`` row.
#. Set the first field in the dialog to ``BASIC``.
#. Close the dialog to save the change.

.. figure:: /images/isim_6.0_sensors_multitick_gui_array_properties_channels.png
    :align: center
    :width: 800
    :alt: Setting the GenericModelOutput channels attribute on an OmniRadar prim via the Array Properties widget in the Property tab

How the attribute flows to the RenderVar
########################################

When ``omni.replicator.core`` adds a ``GenericModelOutput`` RenderVar to a render product
that is attached to an RTX sensor prim, it reads
``_replicator:rendervar:GenericModelOutput:channels`` from the sensor prim and copies the
value onto the RenderVar's ``channels`` attribute. The RTX Sensor SDK then uses that
value to decide which auxiliary fields to populate.

The ``aux_output_level`` constructor parameter on
:py:class:`isaacsim.sensors.experimental.rtx.Lidar`,
:py:class:`isaacsim.sensors.experimental.rtx.Radar`, and
:py:class:`isaacsim.sensors.experimental.rtx.Acoustic` is a convenience that authors
``_replicator:rendervar:GenericModelOutput:channels = [level]`` on the sensor prim. The
two paths are interchangeable; reading existing USD scenes is easier if you recognize
the underlying attribute.

Valid values are modality-specific:

.. csv-table::
    :header: "Modality", "Valid values"
    :widths: 30, 70

    "Lidar", "``NONE`` (default), ``BASIC``, ``EXTRA``, ``FULL``"
    "Radar", "``NONE`` (default), ``BASIC``"
    "Acoustic", "``NONE`` (default), ``BASIC``"

See :ref:`rtx_sensor_annotator_descriptions` for the per-level field listing.

Migration from previous releases
################################

Earlier releases used per-modality USD attributes for the same purpose. These attributes
have been removed from the schemas:

.. csv-table::
    :header: "Old attribute (removed)", "Replacement"
    :widths: 50, 50

    "``omni:sensor:Core:auxOutputType`` (Lidar)", "``_replicator:rendervar:GenericModelOutput:channels`` on the ``OmniLidar`` prim, or ``Lidar(..., aux_output_level='FULL')``."
    "``omni:sensor:WpmDmat:auxOutputType`` (Radar)", "``_replicator:rendervar:GenericModelOutput:channels`` on the ``OmniRadar`` prim, or ``Radar(..., aux_output_level='BASIC')``."

USD assets shipped with |isaac-sim_short| 6.0 have already been updated. Custom USD
scenes carrying the old attributes need to be migrated; the old attributes are silently
ignored by the new schemas.

.. note::

    ``RtxCamera`` removes ``_replicator:rendervar:GenericModelOutput:channels`` from the
    Camera prim during construction because cameras do not produce a GMO AOV. Camera
    prims therefore do not participate in the propagation behavior described in
    :ref:`isaacsim_sensors_rtx_known_issue_gmo_channels`.

.. _isaacsim_sensors_rtx_known_issue_gmo_channels:

Known issue: last-attach-wins propagation of GMO channels
#########################################################

.. warning::

    The ``_replicator:rendervar:GenericModelOutput:channels`` attribute is currently
    **effectively global per render-product-attach event**. When two RTX sensors on the
    same stage author different values, only the **last** sensor to have a render product
    attached "wins" - every subsequent ``GenericModelOutput`` RenderVar uses that
    sensor's channels value, regardless of which sensor prim it was created from.

Concrete example. Suppose you have one ``Lidar`` with ``aux_output_level="FULL"`` and
one ``Radar`` with ``aux_output_level="BASIC"`` on the same stage:

- If the **Radar** render product is created second, every GMO consumer (Lidar and
  Radar) sees ``BASIC`` channels. The Lidar silently loses its ``FULL``-level fields.
- If the **Lidar** render product is created second, the Radar GMO RenderVar inherits
  ``FULL``. The Radar pipeline does not recognize ``FULL`` and produces **no auxiliary
  data at all** for that Radar (no ``rv_ms``, no intensity, etc.).

Recommended workarounds:

- Keep all RTX sensors on a stage at the same ``aux_output_level``.
- Order render-product attachment so the sensor whose channels value you want to use is
  attached last.
- Split sensors with conflicting auxiliary-output requirements across separate stages
  or ``SimulationApp`` instances.

This issue is tracked separately and will be addressed in a future release. Cameras are
unaffected: ``RtxCamera`` removes the GMO channels attribute during construction because
Camera prims do not emit GMO AOVs.

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

**Lidar scans are incomplete**
    Ensure ``omni:sensor:Core:accumulateOutputs`` is set to ``true`` on the ``OmniLidar`` prim. ``omni:sensor:tickRate`` must equal ``omni:sensor:Core:scanRateBaseHz`` on the ``OmniLidar`` prim.
    See :ref:`isaac_sim_sensors_multitick_lidar_tickrate_must_match_scanrate`.


**Radar simulation does not show Doppler effects**
    Motion BVH must be enabled for Doppler effects to be modeled correctly. See :ref:`isaac_sim_sensors_rtx_how_to_enable_motion_bvh`.

**Timestamps are discontinuous after pause/resume**
    This should not occur if multi-tick rendering is enabled. If multi-tick rendering is disabled, the ``GenericModelOutput`` AOV timestamp is independent of the animation timeline and continues to increase even when paused.

**One sensor's auxiliary output level overrides another's**
    The ``_replicator:rendervar:GenericModelOutput:channels`` attribute is currently global
    per render-product-attach event. See :ref:`isaacsim_sensors_rtx_known_issue_gmo_channels`.

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
- :ref:`isaac_sim_app_tutorial_ros2_rtx_radar` - Publishing RTX Radar data to ROS2
- :ref:`isaac_sim_sensors_multitick_rendering` - Multi-tick rendering and 5.x → 6.0 migration
- :ref:`isaac_debug_draw` - Visualizing point clouds and geometry
- :ref:`isaac_sim_app_util_snippets` - Rendering and visualization utilities


