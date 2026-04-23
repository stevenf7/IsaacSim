..
   Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_sim_app_tutorial_ros2_rtx_radar:

====================================
RTX Radar Sensors
====================================

|isaac-sim_short| supports RTX Radar sensors that simulate radar detections including per-point radial velocity.
RTX Radar requires Motion BVH to be enabled for Doppler velocity estimation.

Learning Objectives
=======================

In this tutorial, you:

- Introduce RTX Radar sensors and their requirements.
- Create an RTX Radar sensor and attach it to a robot.
- Publish radar detections to ROS 2 as PointCloud2 messages with optional radial velocity metadata.
- Visualize radar point clouds in RViz2.

Getting Started
=============================

.. important:: Make sure to source ROS 2 appropriately from the terminal before running |isaac-sim_short|.

**Prerequisites**

- Completed the :ref:`isaac_sim_app_tutorial_ros2_camera` and :ref:`isaac_sim_app_tutorial_ros2_rtx_lidar` tutorials.
- ``FASTRTPS_DEFAULT_PROFILES_FILE`` environment variable is set prior to launching |isaac-sim_short| and ROS2 bridge is enabled.
- Review the :ref:`isaacsim_sensors_rtx_radar` documentation for details on RTX Radar sensor configuration.

.. warning::

    RTX Radar requires **Motion BVH** to be enabled. In |isaac-sim_short|, go to **Rendering > Settings > Common** and enable **Motion BVH**, or set the carb setting ``/renderer/raytracingMotion/enabled`` to ``true``. Without this, the radar sensor will fail to initialize.


.. _isaac_sim_app_tutorial_ros2_rtx_radar_basic:

Adding a RTX Radar ROS 2 Bridge
===================================================

#. Start with the turtlebot scene from the :ref:`isaac_sim_app_tutorial_ros2_turtlebot` tutorial.
#. Add a Radar sensor by going to **Create > Sensors > RTX Radar > Generic**.
#. To place the radar sensor on the robot, drag the Radar prim under ``/World/turtlebot3_burger/base_scan``. Zero out any displacement in the **Transform** fields inside the **Property** tab.
#. Connect the ROS 2 bridge with the sensor output using OmniGraph nodes. Open the visual scripting editor by going to **Window > Graph Editors > Action Graph**. Add the following nodes to the graph:

    #. ``On Playback Tick``: Triggers all downstream nodes after **Play** is pressed.
    #. ``ROS2 Context Node``: Creates a ROS 2 context with a given Domain ID (default 0).
    #. ``Isaac Run One Simulation Frame``: Runs the create render product pipeline once at the start.
    #. ``Isaac Create Render Product``: Set the ``cameraPrim`` input to the RTX Radar prim created in step 2.
    #. ``ROS2 RTX Radar Helper``: Publishes radar detections as a PointCloud2 message. Connect the render product output from step d. Set ``frameId`` to ``base_scan`` and ``topicName`` to ``radar_point_cloud``.

#. Connect the nodes:

    - ``On Playback Tick > outputs:tick`` → ``Isaac Run One Simulation Frame > inputs:execIn``
    - ``Isaac Run One Simulation Frame > outputs:step`` → ``Isaac Create Render Product > inputs:execIn``
    - ``Isaac Create Render Product > outputs:execOut`` → ``ROS2 RTX Radar Helper > inputs:execIn``
    - ``Isaac Create Render Product > outputs:renderProductPath`` → ``ROS2 RTX Radar Helper > inputs:renderProductPath``

Exposing Radar Metadata
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``ROS2 RTX Radar Helper`` node supports optional per-point metadata fields in the PointCloud2 message:

- **outputRadialVelocityMS**: Include per-point radial velocity (m/s). Requires setting the ``_replicator:rendervar:GenericModelOutput:channels`` attribute on the OmniRadar prim to ``["BASIC"]``.
- **outputIntensity**: Include per-point intensity values.
- **outputTimestamp**: Include per-point timestamps.

Running the Example
^^^^^^^^^^^^^^^^^^^^^^^^

After the graph has been set correctly, press **Play** to begin the simulation.

For RViz2 visualization:

#. Run RViz2 (``rviz2``) in a sourced terminal.
#. Set the **Fixed Frame** to ``base_scan`` to match the radar's frame ID.
#. Add a **PointCloud2** visualization and set the topic to ``/radar_point_cloud``.
#. If radial velocity is enabled, you can color the point cloud by the ``radial_velocity_ms`` field to visualize Doppler data.


Standalone Python
^^^^^^^^^^^^^^^^^

You can also set up the radar ROS 2 bridge programmatically. The following example creates an RTX Radar sensor with radial velocity metadata and publishes it to ROS 2:

.. code-block:: python

    import omni.graph.core as og
    from isaacsim.sensors.experimental.rtx import Radar

    # Create radar with auxiliary output for radial velocity
    radar = Radar("/World/Radar", aux_output_level="BASIC")

    # Create the OmniGraph
    og.Controller.edit(
        {"graph_path": "/ActionGraph", "evaluator_name": "execution"},
        {
            og.Controller.Keys.CREATE_NODES: [
                ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                ("CreateRenderProduct", "omni.isaac.core_nodes.IsaacCreateRenderProduct"),
                ("RadarHelper", "isaacsim.ros2.bridge.ROS2RtxRadarHelper"),
            ],
            og.Controller.Keys.SET_VALUES: [
                ("CreateRenderProduct.inputs:cameraPrim", radar.paths[0]),
                ("RadarHelper.inputs:topicName", "radar_point_cloud"),
                ("RadarHelper.inputs:frameId", "radar"),
                ("RadarHelper.inputs:outputRadialVelocityMS", True),
            ],
            og.Controller.Keys.CONNECT: [
                ("OnPlaybackTick.outputs:tick", "CreateRenderProduct.inputs:execIn"),
                ("CreateRenderProduct.outputs:execOut", "RadarHelper.inputs:execIn"),
                ("CreateRenderProduct.outputs:renderProductPath", "RadarHelper.inputs:renderProductPath"),
            ],
        },
    )


Summary
=======================

This tutorial covered:

- How to create an RTX Radar sensor and attach it to a robot in |isaac-sim_short|.
- Publishing radar detections to ROS 2 as PointCloud2 messages using the ``ROS2 RTX Radar Helper`` OmniGraph node.
- Enabling per-point radial velocity metadata in the published messages.
- Visualizing radar data in RViz2.

Next Steps
^^^^^^^^^^^^^^^^^^^^^^
Continue on to the next tutorial in our ROS2 Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_tf` to learn about publishing TF data from |isaac-sim_short| to ROS 2.
