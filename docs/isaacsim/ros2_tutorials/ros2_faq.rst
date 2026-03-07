..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_ros2_faq:


=================================
ROS 2 Frequently Asked Questions
=================================

This page addresses common questions about using ROS 2 with |isaac-sim|. Many of these topics come up when users are getting started with ROS 2 integration and encounter differences between how ROS 2 typically operates and how it works within a simulated environment.


.. _isaac_sim_ros2_faq_topics_not_visible:

ROS 2 Topics Are Not Visible Outside Isaac Sim
================================================

**Q: I have ROS 2 installed and the ROS 2 Bridge extension enabled in Isaac Sim, but when I run** ``ros2 topic list`` **in a terminal, no topics from Isaac Sim appear. What is wrong?**

This is one of the most common issues encountered when first setting up the ROS 2 Bridge. There are several potential causes:

1. **Internal ROS libraries not configured**: If you do not have a native ROS 2 installation sourced, |isaac-sim_short| uses its own internal ROS 2 libraries. You may need to explicitly enable and configure these libraries. Follow the steps in :ref:`isaac_sim_app_no_system_installed_ros` to set the required environment variables before launching |isaac-sim_short|.

2. **ROS 2 environment not sourced in the external terminal**: The terminal where you run ``ros2 topic list`` must have the same ROS 2 distribution sourced. For example:

    .. code-block:: bash

        source /opt/ros/jazzy/setup.bash
        ros2 topic list

3. **DDS middleware mismatch**: |isaac-sim_short| and your external terminal must use the same DDS middleware and configuration. If you are communicating across Docker containers or multiple machines, make sure ``FASTRTPS_DEFAULT_PROFILES_FILE`` is set correctly in **all** terminals. Refer to the multi-machine setup in :ref:`isaac_sim_app_enable_ros`.

4. **ROS_DOMAIN_ID mismatch**: If ``ROS_DOMAIN_ID`` is set in one environment but not the other, topics will not be visible across the two. Ensure the same domain ID is used in both |isaac-sim_short| and any external ROS 2 terminals.

5. **Simulation is not playing**: ROS 2 topics are only published while the simulation is actively running. Click **Play** in |isaac-sim_short| before checking for topics.

If none of the above steps resolve the issue, try a clean reinstallation of |isaac-sim_short| and re-follow the :ref:`ROS 2 installation guide <isaac_sim_app_install_ros>` from the beginning.


.. _isaac_sim_ros2_faq_publish_rate_mismatch:

ROS 2 Publish Rate Does Not Match Physics Rate
================================================

**Q: I increased the simulation frame rate to 100 Hz, but the ROS topic publish rate is still around 60 Hz. How do I make them match?**

There are a few important concepts to understand when working with publish rates in |isaac-sim_short|:

Simulation Time vs. Wall Time
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

|isaac-sim_short| distinguishes between **simulation time** and **wall time** (real-world clock time):

- **Simulation time** advances based on the configured physics time step. If physics is set to run at 100 Hz, each step advances simulation time by 10 ms.
- **Wall time** is the actual elapsed time on your machine.

The **Real-Time Factor (RTF)** describes the ratio between these two: ``RTF = simulation_elapsed_time / wall_elapsed_time``. When RTF < 1.0, the simulation is running slower than real-time, meaning the physics engine cannot keep up with the target rate on your hardware. In this case, even though you configured 100 Hz, the actual throughput measured in wall time may be lower.

You can monitor the RTF using the :ref:`RTF publisher tutorial <isaac_sim_app_tutorial_ros2_rtf>`.

Using the Correct Trigger Node
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The event node driving your ROS 2 publishers determines when messages are sent:

- **On Playback Tick**: Fires once per **render frame**. The render frame rate is often limited by GPU performance and may not match the physics rate.
- **On Physics Step**: Fires once per **physics step**. Use this node if you want your ROS 2 publish rate to be aligned with the physics rate.

If you need your ROS 2 messages to publish at the physics rate, replace **On Playback Tick** with **On Physics Step** as the execution trigger in your Action Graph.

For more details on configuring publish rates, see the :ref:`Setting Publish Rates <isaac_sim_app_tutorial_ros2_publish_rate>` tutorial.

Hardware Limitations
^^^^^^^^^^^^^^^^^^^^^

Even when using **On Physics Step**, the actual wall-clock publish rate depends on your machine's ability to run the simulation at the target rate. If the system is under heavy load (complex scenes, multiple sensors, high-resolution cameras), the effective rate may be lower.

To diagnose performance bottlenecks:

1. Enable the FPS display via **(eye icon) > Heads Up Display > FPS** in the viewport.
2. Check CPU/GPU utilization.

For quick fixes (e.g., clearing persistent settings with ``--reset-user``), see the :ref:`ROS 2 Publish Rate Issues <isaac_sim_ros2_troubleshooting>` section in Troubleshooting.


.. _isaac_sim_ros2_faq_occupancy_map_empty:

Occupancy Map Tool Generates an Empty Map
==========================================

**Q: Why does the occupancy map tool generate an empty map even though there are obstacles in the scene?**

The :ref:`occupancy map tool <ext_isaacsim_asset_generator_occupancy_map>` projects objects onto a 2D plane to generate the map. This is commonly used alongside ROS 2 navigation stacks (e.g., Nav2) to provide a static map via the ``map_server`` node. If the map appears empty despite having obstacles in the scene, check the following:

1. **Objects are at the coordinate origin**: If your obstacles are placed at or very near the world origin, they might overlap with the map origin and not register correctly. Try moving obstacles away from the origin to verify.

2. **The ground plane is included in the map Z range**: The occupancy map is generated by sweeping a height range along the Z axis. If the lower Z bound of the map includes the ground plane, the entire map may be marked as occupied (appearing as a solid block) or the ground may obscure the obstacles. Adjust the **Origin Z** and **Z range** parameters so that the sweep starts slightly above the ground plane.

    For example, if your ground plane is at ``Z = 0``, set the lower Z bound to a small positive value (e.g., ``0.05``) so that only actual obstacles are captured.

3. **Map resolution is too coarse**: If the cell size is too large relative to the obstacle sizes, small obstacles may not appear. Reduce the cell size for finer resolution.

4. **Map extents do not cover the obstacle area**: Verify that the map's XY bounds include the region where obstacles are located.


.. _isaac_sim_ros2_faq_sim_time_vs_wall_time:

Understanding Simulation Time vs. Wall Time
=============================================

**Q: What is the difference between simulation time and wall time, and why does it matter for ROS 2?**

In a physical robot system, there is only one notion of time: the system clock. In simulation, there are two:

- **Wall time** (also called system time or real time): The time reported by your computer's clock. It always advances at the normal rate.
- **Simulation time**: A virtual clock maintained by the simulator. It advances based on the configured physics time step and may run faster or slower than wall time depending on scene complexity and hardware performance.

Why This Matters for ROS 2
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Many ROS 2 nodes (e.g., Nav2, RViz2, TF listeners) rely on consistent timestamps. When running with a simulator, you generally want these nodes to use **simulation time** rather than wall time so that everything stays synchronized, especially if the simulation is running slower or faster than real-time.

To enable this:

1. Publish a ``/clock`` topic from |isaac-sim_short| using the :ref:`ROS 2 Clock publisher <isaac_sim_app_tutorial_ros2_clock_publisher>`.
2. Set the ``use_sim_time`` parameter to ``true`` on your external ROS 2 nodes:

    .. code-block:: bash

        ros2 param set /node_name use_sim_time true

    Or configure it in your ROS 2 launch files.

If you observe that timestamps in your ROS messages do not match what you expect, or that TF transforms appear to jump or lag, verify that:

- A ``/clock`` topic is being published.
- All relevant ROS 2 nodes have ``use_sim_time`` set to ``true``.
- You understand whether the timestamps in your messages reflect simulation time or system time (controlled by the ``useSystemTime`` field on Camera Helper and RTX Lidar Helper nodes).

For further details, see the :ref:`ROS 2 Clock <isaac_sim_app_tutorial_ros2_clock>` tutorial.


.. _isaac_sim_ros2_faq_wsl2:

ROS 2 Topics are Slow or Dropping Messages on WSL2
====================================================

**Q: ROS 2 topics appear laggy, delayed, or are dropping messages when running Isaac Sim on WSL2.**

When running Isaac Sim on **Windows via WSL2**, ROS 2 topic throughput may be noticeably lower than on native Linux. This is caused by:

1. **WSL2 port-forwarded networking**: On Windows, Isaac Sim communicates with ROS 2 nodes in WSL2 via DDS over port-forwarded UDP connections (see the :ref:`Windows ROS 2 installation <isaac_sim_app_install_ros_options_other_platforms>`). This cross-boundary networking adds latency compared to shared-memory transport on native Linux, and large UDP payloads are more prone to packet loss over this bridge.

2. **Bandwidth-heavy topics**: Topics publishing large payloads (e.g., raw images, point clouds, compressed images) are most affected. For compressed images specifically, the additional software decoding overhead on the subscriber side can further reduce the effective visualization rate.

These are WSL2 platform limitations and not specific to Isaac Sim. For the best experience with high-throughput ROS 2 workflows, consider running natively on Linux.


Additional Resources
======================

- :ref:`ROS 2 Installation <isaac_sim_app_install_ros>`
- :ref:`ROS 2 Clock <isaac_sim_app_tutorial_ros2_clock>`
- :ref:`ROS 2 Real Time Factor <isaac_sim_app_tutorial_ros2_rtf>`
- :ref:`Setting Publish Rates <isaac_sim_app_tutorial_ros2_publish_rate>`
- :ref:`ROS 2 Troubleshooting <isaac_sim_ros2_troubleshooting>`
