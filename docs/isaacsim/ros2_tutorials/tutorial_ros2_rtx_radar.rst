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

    RTX Radar requires **Motion BVH** to be enabled. Launch |isaac-sim_short| from the command line with ``--/renderer/raytracingMotion/enabled=true`` (and the related flags). See :ref:`isaac_sim_sensors_rtx_how_to_enable_motion_bvh` for the full set of flags and the standalone-Python equivalent. Without this, the radar sensor will fail to initialize.


.. _isaac_sim_app_tutorial_ros2_rtx_radar_basic:

Adding a RTX Radar ROS 2 Bridge
===================================================

#. Start with the turtlebot scene from the :ref:`isaac_sim_app_tutorial_ros2_turtlebot` tutorial.
#. Add a Radar sensor by going to **Create > Sensors > RTX Radar**.
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

..
    TODO: Replace the placeholder below with a screenshot of the expected RViz2
    visualization (radar PointCloud2 on the turtlebot scene), styled to match the
    figure in the RTX Lidar tutorial. See NVBug 6116050.

.. .. figure:: /images/TODO_rtx_radar_rviz2_expected.png
..    :align: center
..    :width: 800
..    :alt: Expected RViz2 visualization of the RTX Radar PointCloud2 output on the turtlebot scene.


Programmatic Setup (Script Editor)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can also set up the radar ROS 2 bridge programmatically. The following example creates an RTX Radar sensor with radial velocity metadata and publishes it to ROS 2.

.. note::

    Run this snippet from **Window > Script Editor** inside an already-running |isaac-sim_short| session — it relies on an active ``omni.kit.app`` instance and stage and is **not** a self-contained standalone script. To run it via ``./python.sh`` instead, wrap it in a ``SimulationApp`` boilerplate (see :ref:`isaac_sim_app_tutorial_ros2_rtx_lidar_script_sample` for an example).

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_rtx_radar/programmatic_setup.py
    :language: python


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
