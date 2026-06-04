..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.





.. _isaac_sim_app_tutorial_ros2_rtx_lidar:

====================================
RTX Lidar Sensors
====================================

|isaac-sim_short| RTX or Raytraced Lidar supports both Solid State and Rotating Lidar configurations.
Each RTX Sensor must be attached to its own viewport to simulate properly.

.. Warning:: Docking windows in the Isaac Sim UI when an RTX Lidar simulation is running will likely lead to a crash. Pause the simulation before re-docking the window.

.. note::

    In |isaac-sim_short| 6.0, RTX Lidar publish rates are governed by the ``omni:sensor:tickRate``
    attribute on the ``OmniLidar`` prim, not by ``frameSkipCount`` on the helper node. For
    ``OmniLidar`` prims, ``omni:sensor:tickRate`` must equal ``omni:sensor:Core:scanRateBaseHz``
    for scan accumulation to behave correctly. See :ref:`isaac_sim_sensors_multitick_rendering`
    for the migration guide and a list of related known issues.

Learning Objectives
=======================

In this example, you:

- Briefly introduce how to use RTX Lidar sensors.
- Create an RTX Lidar sensor.
- Publish sensor data to ROS2 as LaserScan and PointCloud2 messages.
- Use the menu shortcut to create RTX Lidar sensor publishers.
- Put it all together and visualize multiple sensors in RViz2.

Getting Started
=============================

.. important:: Make sure to source ROS 2 appropriately from the terminal before running |isaac-sim_short|.

**Prerequisites**

- Completed the :ref:`isaac_sim_app_tutorial_ros2_camera` tutorial.
- ``FASTRTPS_DEFAULT_PROFILES_FILE`` environment variable is set prior to launching |isaac-sim_short| and ROS2 bridge is enabled.
- OPTIONAL: Explore the inner workings of RTX Lidar sensors by reviewing :ref:`isaacsim_sensors_rtx_lidar_how_they_work` and how to get :ref:`rtx_sensor_annotator_descriptions`.
- Completed the :ref:`isaac_sim_app_tutorial_ros2_turtlebot` tutorial so that Turtlebot is loaded and moving around.
- The optional portion of this tutorial requires the ``isaac_tutorials`` ROS 2 package, which is provided in `IsaacSim-ros_workspaces <https://github.com/isaac-sim/IsaacSim-ros_workspaces>`_ repo.
- Complete :ref:`isaac_sim_app_install_ros` to make sure the ROS 2 workspace environment is set up correctly.


.. note:: In Windows 11, depending on your machine's configuration, RViz2 might not open properly. Some bandwidth-heavy topics might not be available to visualize in RViz2 in WSL.

.. _isaac_sim_app_tutorial_ros2_rtx_lidar_basic:

Adding a RTX Lidar ROS 2 Bridge
===================================================

#. Add a 2D Lidar sensor. Go to **Create > Sensors > RTX Lidar > NVIDIA > Example Rotary 2D**.
#. To place the synthetic Lidar sensor at the same place as the robot's Lidar unit, drag the Lidar prim under ``/World/tb3_burger_processed/Geometry/base_footprint/base_link/base_scan``. Zero out any displacement in the **Transform** fields inside the **Property** tab. The Lidar prim should now be overlapping with the scanning unit of the robot.
#. Add a 3D Lidar sensor. Go to **Create > Sensors > RTX Lidar > NVIDIA > Example Rotary**.
#. To place the synthetic Lidar sensor at the same place as the robot's Lidar unit, drag the Lidar prim under ``/World/tb3_burger_processed/Geometry/base_footprint/base_link/base_scan``. Zero out any displacement in the **Transform** fields inside the **Property** tab. The Lidar prim should now be overlapping with the scanning unit of the robot.
#. Connect the ROS 2 bridge using OmniGraph nodes. Select ``/World/tb3_burger_processed/Geometry/base_footprint/base_link/base_scan`` in the **Stage** panel — lidar publisher graphs are tied to a specific sensor, so they belong next to the sensor prim rather than under the robot root. Open **Window > Graph Editors > Action Graph**, click **New Action Graph**, and name it ``ROS_LidarRTX``. Add the following nodes to the graph:

    #. **On Playback Tick** — triggers downstream nodes when **Play** is pressed.
    #. **ROS 2 Context Node** — sets the ROS 2 `Domain ID <https://docs.ros.org/en/humble/Concepts/Intermediate/About-Domain-ID.html>`_ (defaults to 0; check ``Use Domain ID Env Var`` to inherit ``ROS_DOMAIN_ID`` from the launch environment).
    #. **Isaac Run One Simulation Frame** — runs the render-product pipeline once at startup for performance.
    #. **Isaac Create Render Product** — set ``cameraPrim`` to the 2D Lidar from step 1.
    #. **Isaac Create Render Product** (second instance) — set ``cameraPrim`` to the 3D Lidar from step 3.
    #. **ROS 2 RTX Lidar Helper** — connect the 2D render product output. Set ``topicName`` to ``scan`` and ``frameId`` to ``base_scan``.
    #. **ROS 2 RTX Lidar Helper** (second instance) — connect the 3D render product output. Set ``type`` to ``point_cloud``, ``topicName`` to ``point_cloud``, ``frameId`` to ``base_scan``, and check **Publish Full Scan**.

    .. figure:: /images/isim_5.0_ros_tut_gui_rtx_lidar_graph.png
        :align: center
        :width: 800
        :alt: Action Graph Layout

.. note::
    When **type** is set to ``laser_scan`` in the `ROS2 RTX Lidar Helper` node, the LaserScan message will only be published when the RTX Lidar generates a full scan.
    For a rotary Lidar this is a full 360-degree rotation, while for a solid state Lidar this is the full azimuth of the Lidar, as configured in its profile.
    Depending on Lidar rotation rate and time step size, it can take multiple frames to complete the full rotary scan; that is, for render step size 1/60s, a rotary Lidar with
    rotation rate 10Hz would take six frames to complete a full scan, meaning the LaserScan message would be published once every six frames. Solid state Lidars
    complete the full scan in a single frame, so the corresponding LaserScan message would be published every frame.

    PointCloud messages are published either every frame or after the full scan has been accumulated, based on the value of the `Publish Full Scan` setting in
    the `ROS2 RTX Lidar Helper` node.

After the graph has been set correctly, hit **Play** to begin simulation.
Verify that the RTX Lidar is sending the LaserScan and PointCloud2 messages and can be visualized in RViz.

For RViz visualization:

#. Run RViz2 (``rviz2``) in a sourced terminal.
#. The lidar frame in |isaac-sim_short| for the RTX Lidar is set to `base_scan`, update the fixed frame name in RViz accordingly.
#. Add LaserScan visualization and set topic to `/scan`.
#. Add PointCloud2 visualization and set topic to `/point_cloud`.

    .. figure:: /images/isim_5.0_ros_tut_gui_rtx_lidar_graph_rviz.png
        :align: center
        :width: 800
        :alt: RViz Visualization for RTX Lidar


Graph Shortcut
^^^^^^^^^^^^^^^^^^^

There is a menu shortcut to build multiple Lidar sensor graphs. Go to **Tools > Robotics > ROS 2 OmniGraphs > RTX Lidar**.

If you don't observe any ROS2 graphs listed, you need to enable the ROS2 bridge. A popup will appear asking for the parameters needed to populate the graphs. You must provide the Graph Path, the Lidar Prim, frameId, any Node Namespaces if you have one, and check the boxes for the data you want to publish. If you want to add the graphs to an existing graph, check the **Add to an existing graph?** box. This will append the nodes to the existing graph, and use the existing tick node, context node, and simulation time node if they exist.


Running the Example
===================

- In a new terminal with your ROS2 environment sourced, run the following command to start RViz and show the Lidar point cloud. Replace ``ros2_ws`` with ``humble_ws`` as appropriate.

    .. code-block:: bash

        rviz2 -d <ros2_ws>/src/isaac_tutorials/rviz2/rtx_lidar.rviz


- Run the sample script:

    .. code-block:: bash

        ./python.sh standalone_examples/api/isaacsim.ros2.bridge/rtx_lidar.py

After the scene finishes loading, verify that you observe the point cloud for the rotating Lidar sensor being simulated.

.. _isaac_sim_app_tutorial_ros2_rtx_lidar_script_sample:

RTX Lidar Script Sample
=========================
While most of the sample code is fairly generic, there are a few specific pieces needed to create and simulate the sensor. In this sample, you create a 2D and 3D RTX Lidar sensor using the ``isaacsim.sensors.experimental.rtx`` Python API.

Create the 3D RTX Lidar Sensor:

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_rtx_lidar/rtx_lidar_script_sample.py
    :language: python

Here ``Example_Rotary`` selects the 3D Lidar configuration USD. To switch the Lidar to the example solid-state configuration, replace ``config="Example_Rotary"`` with ``config="Example_Solid_State"`` and update ``tick_rate`` to that asset's ``omni:sensor:Core:scanRateBaseHz`` value (see :ref:`isaac_sim_sensors_multitick_lidar_tickrate_must_match_scanrate`).

Create a render product and attach this sensor to it:

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_rtx_lidar/rtx_lidar_script_sample_1.py
    :language: python

Create the post process pipeline that takes the rendered RTX Lidar point cloud data and publishes it to ROS:

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_rtx_lidar/rtx_lidar_script_sample_2.py
    :language: python

Create the 2D RTX Lidar Sensor:

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_rtx_lidar/rtx_lidar_script_sample_3.py
    :language: python

``Example_Rotary_2D`` selects the 2D Lidar configuration USD.

Similar to the 3D Lidar sensor, create a render product and the post process pipeline that publishes the rendered RTX Lidar laser scan data to ROS:

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_rtx_lidar/rtx_lidar_script_sample_4.py
    :language: python

.. note::
    For details on additional parameters supported by ``Lidar.create``, including ``aux_output_level`` and ``accumulate_outputs``, see :ref:`isaacsim_sensors_rtx_lidar` and the |link_ext|.

.. |link_ext| raw:: html

    <a href="../py/source/extensions/isaacsim.ros2.bridge/docs/index.html" target="_blank">API Documentation</a>

(Optional) Exposing RTX Lidar Metadata in ROS2 PointCloud2
============================================================

RTX Lidar sensors can optionally expose metadata beyond the Cartesian point cloud, including return intensity and timestamp, materials of the objects generating individual returns, and prim paths of the prims generating individual returns.
The full list of metadata that can be exposed is described in the :ref:`rtx_sensor_IsaacCreateRTXLidarScanBuffer` Annotator.

To generate the metadata, you must set the ``_replicator:rendervar:GenericModelOutput:channels`` attribute on the ``OmniLidar`` prim to include ``BASIC`` (or a higher level) - equivalently, construct the prim with ``Lidar(..., aux_output_level="BASIC")`` (or higher). See :ref:`isaacsim_sensors_rtx_aux_output_level` for how to set the attribute from the **Array Properties** widget. Some metadata fields require additional ``carb`` settings at runtime; refer to the table in the :ref:`rtx_sensor_IsaacCreateRTXLidarScanBuffer` Annotator documentation.

Isaac Sim must then be configured to write the metadata to the PointCloud2 message. There are multiple ways to do this.

Exposing Metadata through ROS2 OmniGraphs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Follow the steps in the :ref:`isaac_sim_app_tutorial_ros2_rtx_lidar_basic` section to create a RTX Lidar sensor and add the ROS2 OmniGraphs nodes to the action graph. Then:

#. Stop the simulation if it is running.
#. Save the scene as a USD.
#. Close Isaac Sim.
#. Start or restart Isaac Sim, adding ``--/rtx-transient/stableIds/enabled=true`` to the run command. This setting enables the RTX renderer to generate the 128-bit Object IDs as part of the RTX Lidar metadata.
#. Reopen the USD you just saved.
#. Open the visual scripting editor by going to **Window > Graph Editors > Action Graph**.
#. Select the action graph you created earlier.
#. Add a `ROS2 RTX Lidar Point Cloud Config` node to the graph.
#. Tick the **Include the Intensity** and **Include the ObjectId** checkboxes. This will write the intensity and object ID metadata to the PointCloud2 message.
#. Connect the ``selectedMetadata`` output of the `ROS2 RTX Lidar Point Cloud Config` node to the ``selectedMetadata`` input of the `ROS2 RTX Lidar Helper` node for the 3D Lidar sensor.
#. Tick the **enableObjectIdMap** checkbox on the `ROS2 RTX Lidar Helper` node for the 3D Lidar sensor. This will enable Isaac Sim to publish a ``String`` message containing the Object ID map, on the ``/object_id_map`` topic.
#. Tick the **enabled** checkbox on the `ROS2 RTX Lidar Helper` node for the 3D Lidar sensor, if not already selected.
#. Select the `Example_Rotary` Lidar prim, and set its ``_replicator:rendervar:GenericModelOutput:channels`` attribute to ``["FULL"]`` - see :ref:`isaacsim_sensors_rtx_aux_output_level` for the step-by-step **Array Properties** workflow.
#. Press **Play** to start the simulation.

.. figure:: /images/isim_6.0_ros_tut_gui_rtx_lidar_graph_metadata.png
    :align: center
    :width: 800
    :alt: Action Graph Layout with Metadata


For RViz visualization:

#. Run RViz2 (``rviz2``) in a sourced terminal.
#. The lidar frame in |isaac-sim_short| for the RTX Lidar is set to `base_scan`, update the fixed frame name in RViz accordingly.
#. Add PointCloud2 visualization and set topic to `/point_cloud`.

    .. figure:: /images/isim_6.0_ros_tut_gui_rtx_lidar_graph_metadata_rviz.png
        :align: center
        :width: 800
        :alt: RViz Visualization for RTX Lidar

Verify that RViz2 automatically sets the ``Channel Name`` under the ``PointCloud2`` visualization to ``intensity``, and the ``Color Transformer`` to ``Intensity``,
enabling visualization of the intensity channel in the PointCloud2 message. Most other metadata channels are not visualized by default, except
``HitNormal``, which when selected will visualize the normal vector of the surface of the object that generated the return.

Exposing Metadata Through Python Script
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create the 3D RTX Lidar Sensor with ``aux_output_level="FULL"``, a render product, and the
``RtxLidarROS2PublishPointCloud`` writer with the ``output*`` flags that select which auxiliary
fields end up in the PointCloud2 message:

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_rtx_lidar/exposing_metadata_through_python_script.py
    :language: python

The snippet authors ``_replicator:rendervar:GenericModelOutput:channels = ["FULL"]`` on the lidar
prim via ``Lidar.create(..., aux_output_level="FULL")``. See
:ref:`isaacsim_sensors_rtx_aux_output_level` for the attribute-flow explanation and a known
issue when multiple RTX sensors with different auxiliary levels share a stage.

In addition, specify ``--/rtx-transient/stableIds/enabled=true`` when invoking ``SimulationApp``, like so:

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_rtx_lidar/create_a_separate_writer_for_the_objectid_mapping.py
    :language: python

When the timeline is played, the PointCloud2 message will be published to the ``/point_cloud`` topic with the desired metadata.

Interpreting Timestamp Metadata
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If ``Timestamp`` is included in the metadata, the PointCloud2 message will contain
two ``uint32`` fields named ``timestamp_0`` and ``timestamp_1``. These hold the low
and high 32 bits, respectively, of a single ``uint64`` value representing the per-point
timestamp in nanoseconds since the start of the simulation. Reconstruct the
``uint64`` value as:

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_rtx_lidar/interpreting_timestamp_metadata.py
    :language: python

.. note::

    This encoding was introduced in |isaac-sim_short| 6.0. In earlier versions,
    ``timestamp`` was emitted as a single ``float32`` field (``datatype=7, count=1``).
    Subscribers written against the previous encoding must be updated to read the
    two ``uint32`` fields and recombine them.

Interpreting Object ID Metadata
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As described in :ref:`rtx_sensor_resolving_object_ids`, the Object ID metadata is a stable, unique 128-bit unsigned integer mapping to the prim path of the object that generated the corresponding return.
This can be used for semantic segmentation of the scene, by mapping the object IDs to prim paths and then retrieving semantic labels from the prims. If ``ObjectId`` is included in the metadata,
the PointCloud2 message will contain 4 ``uint32`` fields: ``object_id_0``, ``object_id_1``, ``object_id_2``, and ``object_id_3``.

After playing the timeline in one of the examples above, in a new terminal verify that your Isaac Sim ROS workspace is sourced, and run the following node to print the prim paths of the objects generating individual returns:

.. code-block:: bash

    ros2 run isaac_tutorials ros2_object_id_subscriber.py

Refer to the subscriber script for more details on how to interpret the Object ID metadata. The relevant portion is copied below for reference; it will `not` run in Isaac Sim Script Editor or standalone Python by itself.

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_rtx_lidar/interpreting_object_id_metadata.py
    :language: python

Summary
=======================

This tutorial covered creating and using the RTX Lidar Sensor with ROS2:

#. Adding a RTX Lidar sensor.
#. Adding a RTX Lidar and PointCloud ROS2 nodes.
#. (Optional) Exposing RTX Lidar metadata (intensity, Object IDs, timestamps) in the published PointCloud2 message.


Next Steps
^^^^^^^^^^^^^^^^^^^^^^

Continue on to the next tutorial in our ROS2 Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_tf`, to learn how to add global and relative transforms to a transform tree.


Further Learning
^^^^^^^^^^^^^^^^^^^^^^

- Explore the inner workings of RTX Lidar sensors by learning :ref:`isaacsim_sensors_rtx_lidar_how_they_work` and how to get :ref:`rtx_sensor_annotator_descriptions`.
- Auto-generated topic namespaces driven by the lidar prim path (via ``renderProductPath``) are covered in :ref:`isaac_sim_app_tutorial_ros2_auto_namespace`.
