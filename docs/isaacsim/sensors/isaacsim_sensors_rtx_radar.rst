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

.. Note:: In |isaac-sim_short| 4.5 and earlier, RTX sensors were based on ``Camera`` prims. If the ``Camera`` prim's
    ``sensorModelPluginName`` attribute was set to ``omni.sensors.nv.radar.wpm_dmatapprox.plugin``, then the
    ``Camera`` prim was used to render the Radar. The Radar was configured using a JSON file whose
    filename (without extension) was set in the ``Camera`` prim's ``sensorModelConfig`` attribute, assuming
    the file was present in a folder specified by the ``app.sensors.nv.radar.profileBaseFolder`` setting.
    Support for ``Camera`` prims as RTX Radars was deprecated in |isaac-sim_short| 5.0.

RTX Radars are rendered using ``OmniRadar`` prims, with the ``OmniSensorGenericRadarWpmDmatAPI`` schema applied,
as configured by attributes on the prim. After attaching a render product to the ``OmniRadar`` prim, and setting
the ``GenericModelOutput`` AOV on the render product, the RTXSensor renderer will write Radar render results to the AOV.

.. The ``OmniSensorGenericRadarWpmDmatAPI`` schema is defined in the ``omni.usd.schema.omni_sensors`` extension, documented here.

How to Create an RTX Radar
--------------------------

The ``isaacsim.sensors.rtx`` extension provides one API for creating RTX Radars. In addition, the ``omni.replicator.core``
extension provides even lower-level APIs for creating ``OmniRadar`` prims (including batch creation) and attaching render
products to them.

Create an RTX Radar Using Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``IsaacSensorCreateRtxRadar`` command creates
a generic ``OmniRadar`` prim with the appropriate schemas applied, or a ``Camera`` prim with the appropriate attributes
to support deprecated workflows.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_rtx_radar/create_an_rtx_radar_using_command.py
    :language: python

The example command above creates an ``OmniRadar`` prim in the stage at the
specified ``translation`` with the specified ``orientation``, at path ``/radar``. The prim is set to be invisible
in the stage. The prim's ``omni:sensor:tickRate`` attribute is set to 10 Hz from 20 Hz (default).

Review the `OmniSensorGenericRadarWpmDmatAPI <https://docs.omniverse.nvidia.com/kit/docs/omni.usd.schema.omni_sensors/107.3.1/omni_sensors_schema.html#omnisensorgenericradarwpmdmatapi>`_
schema in the ``omni.usd.schema.omni_sensors`` extension to learn which attributes can be set on the ``OmniRadar`` prim.

.. image:: /images/isim_5.0_full_ext-isaacsim.sensors.rtx-15.1.1_gui_rtx_radar_create_command.png
    :align: center
    :width: 800
    :alt: The Isaac Sim UI after running the ``IsaacSensorCreateRtxRadar`` command shown above.

Setting ``force_camera_prim`` to ``True`` will instead create an invisible ``Camera`` prim at the specified ``translation``
and ``orientation``.

Annotators can then be attached to the ``OmniRadar`` prim to collect and visualize the Radar results.
Details about available annotators can be explored :ref:`here<rtx_sensor_annotator_descriptions>`.

How to Collect Data from an RTX Radar
-------------------------------------

The recommended method for collecting data from an RTX Radar is to use Replicator Annotators, similar to RTX Lidar.

The ``IsaacExtractRTXSensorPointCloudNoAccumulator`` annotator works with both ``OmniLidar`` and ``OmniRadar`` prims,
extracting point cloud data from the ``GenericModelOutput`` buffer every frame.

Refer to :ref:`rtx_sensor_annotator_descriptions` for the full list of available annotators.

.. _isaacsim_sensors_rtx_radar_visualization:

Visualizing RTX Radar Output
----------------------------

Debug Draw
^^^^^^^^^^

The :ref:`Debug Draw Extension <isaac_debug_draw>` can be used to visualize RTX Radar point cloud output in the viewport.

The standalone example ``create_radar_basic.py`` demonstrates using Debug Draw to visualize RTX Radar output:

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.sensors.rtx/create_radar_basic.py

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
    ./python.sh standalone_examples/api/isaacsim.sensors.rtx/create_radar_basic.py

**Data Collection and Inspection**

.. code-block:: bash

    # Inspect radar GenericModelOutput (GMO) data
    ./python.sh standalone_examples/api/isaacsim.sensors.rtx/inspect_radar_gmo.py

.. note::

    Refer to the :ref:`isaac_sim_conventions` documentation for a complete list of |isaac-sim_short| conventions.
