..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_tutorial_ros2_clock:

=================================
ROS 2 Clock
=================================

Learning Objectives
=======================

In this example, we will:

- Have a brief discussion on the ROS 2 Clock publisher and subscriber
- Publish simulation time to ROS 2 as a Clock message
- Subscribe to a ROS 2 Clock message
- Add a Clock Action Graph using the menu shortcut

Getting Started
===========================



**Prerequisite**

- Complete :ref:`isaac_sim_app_install_ros`.

- If using multiple systems, set the ``FASTRTPS_DEFAULT_PROFILES_FILE`` environment variable as per instructions in :ref:`isaac_sim_app_install_ros` before launching |isaac-sim_short|, as well as any terminal where ROS messages will be sent or received, and ROS 2 Extension is enabled.

.. note:: In Windows 11, depending on your machine's configuration, RViz2 might not open properly. 
    
Simulation Time and Clock
===========================

For external ROS 2 nodes to synchronize with simulation time, a clock topic is usually used. Many ROS 2 nodes such as RViz2 use the parameter ``use_sim_time``, which if set to `True` will indicate to the node to begin subscribing to the ``/clock`` topic and synchronizing to the published simulation time.

You can either set this parameter in a ROS 2 launch file or set the parameter using the following command in a new ROS 2-sourced terminal:

.. code-block:: bash

    ros2 param set /node_name use_sim_time true

Make sure to replace ``/node_name`` with whatever node you are currently running. If setting using the terminal, the node must already be running first before setting the parameter.

.. _isaac_sim_app_tutorial_ros2_clock_publisher:

Running ROS 2 Clock Publisher
=========================================



    
1. Go to **Window > Graph Editors > Action Graph** to create an Action graph.

2. Add the following |omnigraph_short| nodes into the Action graph:

  - **On Playback Tick** node to execute other graph nodes every simulation frame.
  - **ROS 2 Context** node to create a context using either the given Domain ID or the ``ROS_DOMAIN_ID`` environment variable.
  - **Isaac Read Simulation Time** node to retrieve current simulation time. Note: By default the simulation time increases monotonically, meaning regardless of whether simulation is stopped and re-played, the time will continue incrementing. This is mainly to prevent issues that can arise with the time jumping back when simulation resets. You can set ``resetOnStop`` to True if you would like the clock to start from 0 every time simulation is reset.
  - **ROS 2 Publish Clock** node to publish simulation time to the ``/clock`` topic.

    .. figure:: /images/isim_4.5_ros_tut_gui_ros2_clock_publisher.png
        :align: center
        :width: 500
        :alt: ROS2 Clock publisher

3. Start RViz in a new ROS 2-sourced terminal.

    .. code-block:: bash

        ros2 run rviz2 rviz2

    .. tab-set::

        .. tab-item:: Humble    
    
            Take note of the `ROS Time` and `ROS Elapsed` times listed in the bottom of the RViz window. These are currently displaying the wall time and, typically, match the `Wall Time` and `Wall Elapsed` fields.




4. In a new ROS 2-sourced terminal set the ``use_sim_time`` parameter to true for the RViz node. Ensure that simulation is stopped in |isaac-sim_short|.

    .. code-block:: bash

        ros2 param set /rviz use_sim_time true

    .. tab-set::

        .. tab-item:: Humble    

            Notice in RViz that `ROS Time` and `ROS Elapsed` are now both 0.


5. In |isaac-sim_short| click **Play**. 

        .. tab-set::

            .. tab-item:: Humble    

                In RViz, the `ROS Time` is now identical to the simulation time published from |isaac-sim_short| over the ``/clock`` topic.
            

.. _isaac_sim_app_tutorial_ros2_clock_publisher_system_time:

Publishing System Time
========================================

While publishing the simulation time is the most common workflow, there can be certain workflows that require certain messages to contain system time. To publish system time over the clock topic follow these steps:

1. Go to **Window > Graph Editors > Action Graph** to create an Action graph.

2. Add the following |omnigraph_short| nodes into the Action graph:

  - **On Playback Tick** node to execute other graph nodes every simulation frame.
  - **ROS2 Context** node to create a context using either the given Domain ID or the ``ROS_DOMAIN_ID`` environment variable.
  - **Isaac Read System Time** node to retrieve current system time.
  - **ROS2 Publish Clock** node to publish system time to the ``/clock`` topic.

    .. figure:: /images/isim_4.5_ros_tut_gui_ros2_clock_publisher_system_time.png
        :align: center
        :width: 500
        :alt: ROS2 Clock publisher with System Time

3. In |isaac-sim_short| click **Play**. To observe the system timestamp published from |isaac-sim_short| over the ``/clock`` topic run the following command in a ROS-sourced terminal:

    .. code-block:: bash

        ros2 topic echo /clock

**Camera Helper and RTX Lidar nodes**

In upcoming tutorials you will observe the :ref:`ROS 2 Camera Helper node <isaac_sim_app_tutorial_ros2_camera>` and the :ref:`ROS2 RTX Lidar Helper node <isaac_sim_app_tutorial_ros2_rtx_lidar>`. As both of these nodes automatically generate a sensor publishing pipeline, to use system timestamps for their publishers, ensure that their ``useSystemTime`` input field is set to True.


Running ROS 2 Clock Subscriber
==================================

1. Open a new stage. Go to **Window > Graph Editors > Action Graph** to create an Action graph.
2. Add the following |omnigraph_short| nodes into the Action graph:

  - **On Playback Tick** node to execute other graph nodes every simulation frame.
  - **ROS2 Context** node to create a context using either the given Domain ID or the ``ROS_DOMAIN_ID`` environment variable.
  - **ROS2 Subscribe Clock** node to subscribe to external timestamp data.

    .. figure:: /images/isim_4.5_ros_tut_gui_ros2_clock_subscriber.png
        :align: center
        :width: 800
        :alt: ROS2 Clock subscriber

3. Start simulation by clicking **Play**. Select the `ROS2 Subscribe Clock` node inside the action graph to view its ``timeStamp`` output in the **Property** window. Verify that the timestamp is 0.
4. In a new ROS2-sourced terminal run the following command to manually publish a clock message once:

    .. code-block:: bash

        ros2 topic pub  -t 1 /clock rosgraph_msgs/Clock "clock: { sec: 1, nanosec: 200000000 }"

    Verify that the ``timeStamp`` value in the `ROS2 Subscribe Clock` |omnigraph_short| node changes to 1.2.

5. Change the previous command with different `sec` and `nanosec` values to observe those values being reflected in the ``timeStamp`` field of the `ROS2 Subscribe Clock` |omnigraph_short| node.



.. _isaac_sim_app_tutorial_ros2_clock_omnigraph_shortcut:

Graph Shortcut
===============================================

We provide a menu shortcut to build a clock graph within just a few clicks. Go to **Tools > Robotics > ROS 2 OmniGraphs > Clock**. If you don't observe any ROS2 graphs listed, you need to enable the ROS2 bridge. A popup box will appear asking for the parameters needed to populate the graphs. Provide the graph path and click **OK**, verify that a graph publishing the simulated clock appears on the stage.


Summary
========

This tutorial covered:

#. Explanation for using the ``/clock`` topic and the ``use_sim_time`` ROS parameter for time synchronization.
#. Creating and using ROS2 Clock Publisher and Subscriber nodes.

Next Steps
^^^^^^^^^^^^^^^^^^^^^^

Continue on to the next tutorial in our ROS2 Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_rtf`.
