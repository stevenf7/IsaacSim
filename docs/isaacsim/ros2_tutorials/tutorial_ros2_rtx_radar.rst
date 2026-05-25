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

.. warning::

    In Isaac Sim 6.0 GA, RTX Radar autotriggers regardless of ``omni:sensor:tickRate`` attribute. This will be corrected in a future release.

.. note::

    The ``ROS2 RTX Radar Helper`` node does not expose a
    ``frameSkipCount`` input. See :ref:`isaac_sim_sensors_multitick_rendering` for the multi-tick
    migration guide.

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
#. Add a Radar sensor by going to **Create > Sensors > RTX Radar > NVIDIA > Generic RTX Radar**.
#. To place the radar sensor on the robot, drag the Radar prim under ``/World/tb3_burger_processed/Geometry/base_footprint/base_link/base_scan``. Modify the **Transform** fields inside the **Property** tab as follows:

    #. Zero out any displacement.
    #. Set **Rotate Z** to ``90.0``, so the Radar prim is pointing forward.
    #. Set **Translate Z** to ``1.0``, so the Radar prim is slightly above the robot base and returns are more visible.

#. Connect the ROS 2 bridge with the sensor output using OmniGraph nodes. In the **Stage** panel, select ``/World/tb3_burger_processed/Geometry/base_footprint/base_link/base_scan`` so the new Action Graph is created adjacent to the radar sensor link, then open the visual scripting editor by going to **Window > Graph Editors > Action Graph**. Click **New Action Graph** and name it ``ROS_RadarRTX``; the resulting graph path is ``/World/tb3_burger_processed/Geometry/base_footprint/base_link/base_scan/ROS_RadarRTX``. Parenting the graph to the sensor link it publishes for keeps the robot asset composable: when the Turtlebot is referenced into another scene, the radar graph travels with it instead of being stranded at the stage root. Add the following nodes to the graph:

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

.. warning:: Some users may experience a fatal crash when running the example. A description of the crash and a workaround are documented in :ref:`isaac_sim_sensors_multitick_known_issue_radar_lidar_fif_race`.

After the graph has been set correctly, press **Play** to begin the simulation.

For RViz2 visualization:

#. Run RViz2 (``rviz2``) in a sourced terminal.
#. Set the **Fixed Frame** to ``base_scan`` to match the radar's frame ID.
#. Add a **PointCloud2** visualization and set the topic to ``/radar_point_cloud``.
#. To observe the RViz image below, make sure the simulation is playing. In a ROS2-sourced terminal, open with the configuration provided using the command:

     ``ros2 run rviz2 rviz2 -d <ros2_ws>/src/isaac_tutorials/rviz2/camera_lidar.rviz``

 After the RViz window finishes loading, you can enable and disable the sensor streams inside the **Display** panel on the left hand side.
 Modify the PointCloud2 visualization topic to ``/radar_point_cloud`` to show the Radar point cloud, rather than the Lidar point cloud. Set **Size (m)** to ``0.1`` so the points are more visible.

.. note:: In the RViz2 image below, the **Camera 1 - RGB** window was closed because it was hiding one of the Radar returns.

.. note:: The generic RTX Radar sensor is configured to generate few points by default, hence typically only 1-2 points are picked up in this specific scene. Other environments and Radar configurations will generate different point clouds with possibly more points; this example is used for tutorial purposes only.

.. figure:: /images/isim_6.0_ros_tut_external_rtx_radar_multisensor_rviz2.png
    :align: center
    :width: 800
    :alt: Example Multisensor RViz2 configuration

.. important:: Ensure that the ``use_sim_time`` ROS2 param is set to true after running the RViz2 node.
               This ensures that the RViz2 node is synchronized with the simulation data especially when RViz2 interpolates position of Lidar data points.
               Set the parameter using the following command in a new ROS2-sourced terminal:

               .. code-block:: bash

	                ros2 param set /rviz use_sim_time true

Programmatic Setup (Script Editor)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can also set up the radar ROS 2 bridge programmatically. The following example creates an RTX Radar sensor and publishes its detections to ROS 2 (see :ref:`isaac_sim_app_tutorial_ros2_rtx_radar_velocity_example` below for a standalone script that additionally publishes per-point radial velocity).

.. note::

    Run this snippet from **Window > Script Editor** inside an already-running |isaac-sim_short| session — it relies on an active ``omni.kit.app`` instance and stage and is **not** a self-contained standalone script. To run it via ``./python.sh`` instead, wrap it in a ``SimulationApp`` boilerplate (see :ref:`isaac_sim_app_tutorial_ros2_rtx_lidar_script_sample` for an example).

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_rtx_radar/programmatic_setup.py
    :language: python

.. _isaac_sim_app_tutorial_ros2_rtx_radar_velocity_example:

Exposing Radar Metadata
=======================

The ``ROS2 RTX Radar Helper`` node supports optional per-point metadata fields in the PointCloud2 message:

- **outputRadialVelocityMS**: Include per-point radial velocity (m/s). Requires the OmniRadar prim to be created with ``Radar(path, aux_output_level="BASIC")`` (or have ``_replicator:rendervar:GenericModelOutput:channels = ["BASIC"]`` authored on it). See :ref:`isaacsim_sensors_rtx_aux_output_level` for known issues and more details, including how to set the attribute via the UI.
- **outputIntensity**: Include per-point intensity values.
- **outputTimestamp**: Include per-point timestamps.

Standalone Example: Radial Velocity
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The example below shows how to create an RTX Radar sensor and publish radial velocity metadata to ROS 2, such that the point cloud can be colored by the radial velocity when visualized. The example creates two rigid bodies moving cyclically towards and away from the radar, such that the radial velocity is non-zero for each point in the point cloud.

- Run the sample script:

    .. code-block:: bash

        ./python.sh standalone_examples/api/isaacsim.ros2.bridge/rtx_radar.py

- In a new terminal with your ROS2 environment sourced, run the following command to start RViz and show the Radar point cloud. Replace ``ros2_ws`` with ``humble_ws`` or ``jazzy_ws`` as appropriate.

    .. code-block:: bash

        rviz2 -d <ros2_ws>/src/isaac_tutorials/rviz2/rtx_radar.rviz

After the scene finishes loading, verify that you observe the point cloud returns colored by the radial velocity and changing over time as the rigid bodies accelerate and decelerate cyclically.

.. image:: /images/isim_6.0_ros_tut_rtx_radar_standalone.webp
    :alt: RTX Radar publishing PointCloud2 with radial velocity, visualized in RViz2
    :align: center
    :width: 80%


Summary
=======================

This tutorial covered:

- How to create an RTX Radar sensor and attach it to a robot in |isaac-sim_short|.
- Publishing radar detections to ROS 2 as PointCloud2 messages using the ``ROS2 RTX Radar Helper`` OmniGraph node.
- Enabling per-point radial velocity metadata in the published messages.
- Visualizing radar data in RViz2.

Next Steps
^^^^^^^^^^^^^^^^^^^^^^
Continue on to the next tutorial in our ROS2 Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_qos`, to learn about setting QoS Profiles for ROS 2 |omnigraph_short| nodes in |isaac-sim|.

Further Learning
^^^^^^^^^^^^^^^^^^^^^^

- Auto-generated topic namespaces driven by the radar prim path (via ``renderProductPath``) are covered in :ref:`isaac_sim_app_tutorial_ros2_auto_namespace`.
