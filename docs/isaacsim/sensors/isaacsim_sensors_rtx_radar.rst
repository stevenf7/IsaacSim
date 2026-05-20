..
   Copyright (c) 2024-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.





.. _isaacsim_sensors_rtx_radar:

==================
RTX Radar Sensor
==================


.. figure:: /images/isaacsim_sensors_rtx_radar_node_overview_warehouse.png
    :align: center
    :width: 800


RTX Radar sensors are simulated at render time on the GPU with RTX hardware.
Their results are then copied to the ``GenericModelOutput`` AOV for use.

.. warning::

    **Motion BVH Must Be Enabled for RTX Radar**

    RTX Radar requires Motion BVH to be enabled for the Doppler effect—and therefore RTX Radar entirely—to be modeled correctly.
    **Without Motion BVH enabled, RTX Radar will not produce accurate results.**

    Motion BVH is disabled by default in |isaac-sim_short| for performance reasons. You must explicitly enable it before using RTX Radar.

    **To enable Motion BVH**, add the following command line arguments when launching |isaac-sim_short|:

    .. code-block:: bash

        --/renderer/raytracingMotion/enabled=true \
        --/renderer/raytracingMotion/enableHydraEngineMasking=true \
        --/renderer/raytracingMotion/enabledForHydraEngines='0,1,2,3,4'

    Or in standalone Python, pass ``enable_motion_bvh=True`` to the ``SimulationApp`` constructor.

    Refer to :ref:`isaac_sim_sensors_rtx_how_to_enable_motion_bvh` for complete instructions.

.. _isaacsim_sensors_rtx_radar_how_they_work:

Overview
--------

RTX Radars are rendered using ``OmniRadar`` prims, with the ``OmniSensorGenericRadarWpmDmatAPI`` schema applied,
as configured by attributes on the prim. After attaching a render product to the ``OmniRadar`` prim, and setting
the ``GenericModelOutput`` AOV on the render product, the RTXSensor renderer will write Radar render results to the AOV.

.. The ``OmniSensorGenericRadarWpmDmatAPI`` schema is defined in the ``omni.usd.schema.omni_sensors`` extension, documented here.

How to Create an RTX Radar
--------------------------

The ``isaacsim.sensors.experimental.rtx`` extension provides the ``Radar`` class for creating RTX Radars. In addition, the ``omni.replicator.core``
extension provides even lower-level APIs for creating ``OmniRadar`` prims (including batch creation) and attaching render
products to them.

Create an RTX Radar Using the ``Radar`` Class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``Radar`` class creates or wraps an ``OmniRadar`` prim with the appropriate schemas applied.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_radar/create_an_rtx_radar.py
    :language: python

The snippet above creates an ``OmniRadar`` prim at path ``/World/radar`` with ``omni:sensor:tickRate`` set to 10 Hz.

Review the `OmniSensorGenericRadarWpmDmatAPI <https://docs.omniverse.nvidia.com/kit/docs/omni.usd.schema.omni_sensors/107.3.1/omni_sensors_schema.html#omnisensorgenericradarwpmdmatapi>`_
schema in the ``omni.usd.schema.omni_sensors`` extension to learn which attributes can be set on the ``OmniRadar`` prim.

.. note::

   ``Radar.create()`` accepts ``config`` (from
   ``isaacsim.sensors.experimental.rtx.SUPPORTED_RADAR_CONFIGS``) or ``usd_path`` (mutually
   exclusive), plus ``attributes`` for prim-attribute overrides and the plural transform arrays
   (``positions=[[...]]`` / ``translations=[[...]]`` / ``orientations=[[...]]`` / ``scales=[[...]]``;
   ``N=1``). Additional USD schemas via ``schemas=[...]`` are accepted by the ``Radar(...)``
   constructor — pass them through ``Radar(...)`` directly if you need them, since
   ``Radar.create()`` does not currently forward ``schemas``.

.. image:: /images/isim_5.0_full_ext-isaacsim.sensors.rtx-15.1.1_gui_rtx_radar_create_command.png
    :align: center
    :width: 800
    :alt: The Isaac Sim UI after creating an RTX Radar.

Annotators can then be attached to the ``OmniRadar`` prim to collect and visualize the Radar results.
Details about available annotators can be explored :ref:`here<rtx_sensor_annotator_descriptions>`.

Tick Rate
^^^^^^^^^

.. warning::

    In Isaac Sim 6.0 GA, RTX Radar autotriggers regardless of ``omni:sensor:tickRate`` attribute. This will be corrected in a future release.

The ``tick_rate`` parameter (Hz) controls how frequently the sensor renders. A value of ``0``
(the default) enables autotrigger mode, where the sensor renders every simulation frame. This maps to the ``omni:sensor:tickRate`` prim attribute.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_radar/set_radar_tick_rate.py
    :language: python

Auxiliary Output Level
^^^^^^^^^^^^^^^^^^^^^^

RTX Radar exposes auxiliary data through the ``aux_output_level`` constructor parameter.
Valid values are ``"NONE"`` (default) and ``"BASIC"``. Setting ``"BASIC"`` enables radial
velocity (``rv_ms``) in the GMO output.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_radar/set_radar_aux_output_level.py
    :language: python

See :ref:`isaacsim_sensors_rtx_aux_output_level` for the full attribute-flow explanation and the
migration from the removed ``omni:sensor:WpmDmat:auxOutputType`` attribute, and
:ref:`isaacsim_sensors_rtx_known_issue_gmo_channels` for a known issue when multiple RTX sensors
with different auxiliary levels share a stage. See :ref:`rtx_sensor_annotator_descriptions` for
the per-level field listing.

How to Collect Data from an RTX Radar
-------------------------------------

The recommended method for collecting data from an RTX Radar is to use the ``RadarSensor`` runtime class,
which wraps a ``Radar`` authoring object and manages Replicator Annotators, similar to ``LidarSensor``.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_radar/collect_data_with_radar_sensor.py
    :language: python

Refer to :ref:`rtx_sensor_annotator_descriptions` for the full list of available lower-level annotators.

.. _isaacsim_sensors_rtx_radar_visualization:

Visualizing RTX Radar Output
----------------------------

Debug Draw
^^^^^^^^^^

The :ref:`Debug Draw Extension <isaac_debug_draw>` can be used to visualize RTX Radar point cloud output in the viewport.

The standalone example ``create_radar_basic.py`` demonstrates using Debug Draw to visualize RTX Radar output:

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/create_radar_basic.py

For more information on Debug Draw APIs, refer to :ref:`isaac_debug_draw` and :ref:`isaac_sim_app_util_snippets`.

Doppler Effects
^^^^^^^^^^^^^^^

.. important:: Motion BVH must be enabled for the Doppler effect to be modeled correctly in RTX Radar simulations.
    Refer to :ref:`isaac_sim_sensors_rtx_how_to_enable_motion_bvh` for instructions on enabling Motion BVH.

Sensor Materials
----------------

The material system for RTX Radar allows content creators to assign sensor material types to partial material prim names on a USD stage. Radar return behavior depends on material properties (for example, emissivity, reflectivity),
as described below.

.. toctree::
    :maxdepth: 1

    ./isaacsim_sensors_rtx_materials.rst


Standalone Examples
-------------------

For examples of creating and collecting data from RTX Radar, refer to the following:

**Basic Creation and Visualization**

.. code-block:: bash

    # Basic radar creation with debug draw visualization
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/create_radar_basic.py

**Data Collection and Inspection**

.. code-block:: bash

    # Inspect radar GenericModelOutput (GMO) data
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/inspect_radar_gmo.py

**ROS 2 Integration**

For publishing RTX Radar data to ROS 2 as PointCloud2 messages, see the :ref:`isaac_sim_app_tutorial_ros2_rtx_radar` tutorial.

.. note::

    Refer to the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim_short| conventions.
