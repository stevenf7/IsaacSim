

..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_sim_app_tutorial_ros2_python:

====================================
ROS 2 Bridge in Standalone Workflow
====================================


Learning Objectives
================================

- Run standalone ROS2 Python examples
- Manually step ROS2 components

Getting Started
=============================



**Prerequisite**

- Completed :ref:`isaac_sim_app_tutorial_intro_workflows` and :ref:`isaac_sim_app_tutorial_core_hello_world` to understand the two workflows (Standalone and Extension).

- Set the environment variables needed to enable ROS2 messaging in standalone workflow by completing the steps in :ref:`isaac_sim_app_recommended_ros_distros_using_terminal`.

.. note:: In Windows 10 or 11, depending on your machine's configuration, RViz2 might not open properly.


    .. #. Create a file named ``fastdds.xml`` under ``~/.ros/`` if you haven't already, paste the following snippet into the file:

    ..     .. code-block:: bash

    ..         <?xml version="1.0" encoding="UTF-8" ?>

    ..         <license>Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
    ..         NVIDIA CORPORATION and its licensors retain all intellectual property
    ..         and proprietary rights in and to this software, related documentation
    ..         and any modifications thereto.  Any use, reproduction, disclosure or
    ..         distribution of this software and related documentation without an express
    ..         license agreement from NVIDIA CORPORATION is strictly prohibited.</license>


    ..         <profiles xmlns="http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles" >
    ..             <transport_descriptors>
    ..                 <transport_descriptor>
    ..                     <transport_id>UdpTransport</transport_id>
    ..                     <type>UDPv4</type>
    ..                 </transport_descriptor>
    ..             </transport_descriptors>

    ..             <participant profile_name="udp_transport_profile" is_default_profile="true">
    ..                 <rtps>
    ..                     <userTransports>
    ..                         <transport_id>UdpTransport</transport_id>
    ..                     </userTransports>
    ..                     <useBuiltinTransports>false</useBuiltinTransports>
    ..                 </rtps>
    ..             </participant>
    ..         </profiles>

    .. #. In every terminal where |isaac-sim_short| will be launched by the script, run ``unset LD_LIBRARY_PATH`` and ``export FASTRTPS_DEFAULT_PROFILES_FILE=~/.ros/fastdds.xml``.


Manually Stepping ROS2 Components
===================================

Standalone scripting is typically ideal for manual control of the simulation steps. An `OnImpulseEvent` |omnigraph_short| node can be connected to any ROS2 |omnigraph_short| node so that the frequency of the publishers and subscribers can be carefully controlled.

An example of how a new action graph with a `ROS2 Publish Clock` node can be setup to be precisely controlled with a ROS2 Domain ID of 1:

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_python/manually_stepping_ros2_components.py
    :language: python
    :start-after: # End test setup

On any frame, run the following to set an impulse event, which will tick the clock publisher once:

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_python/disable_usedomainidenvvar_to_ensure_we_use_the_abo.py
    :language: python

.. note::
    Due to the explicit control of rendering and physics simulation steps in standalone scripting, the time it takes to complete each step will depend on the computation load and will likely not match real time. This might cause a discrepancy in observed speed of action when running the same application using standalone scripting versus using the GUI. When that occurs, use the simulation clock as reference.


Examples
===================================

A few of the tutorial examples were transformed into standalone Python examples. Here are the instructions for running them.

.. _isaac_sim_app_tutorial_ros2_python_clock:

ROS 2 Clock
*************

This sample demonstrates how to create an action graph with ROS 2 component nodes and then tick them at different rates.

The sample can be executed by running the following:

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.ros2.bridge/clock.py

Echo the following topics to observe messages being published:

.. code-block:: bash

    ros2 topic echo /sim_time
    ros2 topic echo /manual_time

To create and set up a ROS 2 Clock publisher using the |isaac-sim_short| UI, refer to the :ref:`isaac_sim_app_tutorial_ros2_clock` tutorial.

.. _isaac_sim_app_tutorial_ros2_python_camera:

ROS 2 Camera
*************

The following two samples demonstrate how to create an action graph with ROS 2 Camera Helper and Camera Info Helper |omnigraph_short| nodes, which are used to setup ROS 2 RGB image, depth image, and camera info publishers.
Both samples accomplish the same outcome of publishing ROS 2 image data at different rates but use different solutions.

- On each frame:

    - Camera Info is published

- Every 5 frames:

    - RGB image is published

- Every 60 frames:

    - Depth image is published

Periodic Image Publishing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The execution rate (every N frames) for each of the ROS 2 image and camera info publishers are set by modifying their respective Isaac Simulation Gate |omnigraph_short| nodes in the SDGPipeline graph.
By setting the execution rate, an image publisher will automatically be ticked every N rendered frames.

The sample can be executed by running the following:

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.ros2.bridge/camera_periodic.py


To exit the sample, you can terminate the process using ``CTRL-C`` from the terminal.


Manual Image Publishing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ROS 2 image and camera info publishers are manually controlled by injecting Branch |omnigraph_short| nodes between each publisher node and their respective Isaac Simulation Gate |omnigraph_short| node.
The Branch nodes act like a custom gate and can be enabled or disabled at any time. Whenever a Branch node is enabled, the connected ROS 2 publisher node will be ticked.

The sample can be executed by running the following:

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.ros2.bridge/camera_manual.py

To exit the sample, you can terminate the process using ``CTRL-C`` from the terminal.

Visualizing Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To visualize the result of either sample in RViz2, in a new ROS2-sourced terminal navigate to the |isaac-sim_short| package directory and run the following command:

.. code-block:: bash

    rviz2 -d <ros2_ws>/src/isaac_tutorials/rviz2/camera_manual.rviz


.. note:: Due to an issue with RViz2, black frames might appear for depth image displays. To verify that |isaac-sim_short| is correctly publishing depth images, run ``ros2 run rqt_image_view rqt_image_view`` and set the topic to ``/depth``.


.. _isaac_sim_app_tutorial_ros2_python_stereo:

Carter Stereo
******************

This sample demonstrates how to take an existing USD stage with an action graph containing ROS 2 component nodes and modify the default settings. The stereo camera pair is automatically enabled and the second viewport window is docked in the UI.

- On each frame:

  - The ROS 2 clock is published
  - A ROS 2 PointCloud2 message originating from an RTX Lidar is published
  - Odometry is published
  - The Twist subscriber is spun
  - TF messages are published
  - Left and right cameras are published

- Every Two Frames:

   - The Twist command message is published


The sample can be executed by running the following:

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.ros2.bridge/carter_stereo.py

To exit the sample, you can terminate the process using ``CTRL-C`` from the terminal.


To visualize the result:

In a new terminal, run the following command to load RViz2:

.. code-block:: bash

    rviz2 -d <ros2_ws>/src/isaac_tutorials/rviz2/carter_stereo.rviz

Make sure ``Right Camera - RGB`` and ``Left Camera - RGB`` within the ``Displays`` are enabled to visualize RGB images.

.. note::
    If some of the images don't show up on RViz2, press ``Stop`` and ``Play`` in the simulator for the images to show up.


.. _isaac_sim_app_tutorial_ros2_python_multi_navigation:

Multiple Robot ROS 2 Navigation
*********************************

This sample shows how to run an existing USD stage.

To visualize the output refer to the :ref:`interactive version of the sample<isaac_sim_app_tutorial_ros2_multi_navigation>`:

- On each frame:

  - The ROS 2 clock component is published
  - ROS 2 PointCloud2 messages originating from RTX Lidars are published
  - Odometry is published
  - The Twist subscriber is spun
  - TF messages are published

The sample can be executed with both the hospital and office environments.
Run either of the following commands to run the sample with the specified environment:

.. tab-set::

    .. tab-item:: Hospital Environment

        .. code-block:: bash

            ./python.sh standalone_examples/api/isaacsim.ros2.bridge/carter_multiple_robot_navigation.py --environment hospital


    .. tab-item:: Office Environment

        .. code-block:: bash

            ./python.sh standalone_examples/api/isaacsim.ros2.bridge/carter_multiple_robot_navigation.py --environment office

To exit the sample, you can terminate the process using ``CTRL-C`` from the terminal.


.. note:: If you encounter any issues, refer to :ref:`isaac_sim_app_tutorial_ros2_multi_nav_instructions_troubleshoot`.


.. _isaac_sim_app_tutorial_ros2_python_moveit:

MoveIt2
******************

This sample shows how to add multiple USD stages. It also demonstrates how to manually create an action graph with ROS 2 component nodes and then manually tick them.

To visualize the output refer to the :ref:`interactive version of the sample<isaac_sim_app_tutorial_ros2_moveit>`:

- On each frame:

  - The ROS 2 clock is published
  - Joint State messages are published
  - Joint State subscriber is spun
  - TF messages are published

The sample can be executed by running the following:

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.ros2.bridge/moveit.py

To exit the sample you can terminate using the terminal with ``CTRL-C``


Receiving ROS 2 Messages
************************

This is a basic subscriber example where upon receiving an empty ROS2 message, a cube in the scene teleports to a random location. This one is running with rendering enabled, you can verify that you observe the scene and the cube moving. To run this example:


    .. code-block:: bash

		./python.sh standalone_examples/api/isaacsim.ros2.bridge/subscriber.py

To exit the sample, you can terminate the process using ``CTRL-C`` from the terminal.


After the scene with cube is loaded, you can publish the empty message manually from another terminal. Use the rate of 1Hz.


    .. code-block:: bash

		ros2 topic pub -r 1 /move_cube std_msgs/msg/Empty

.. raw:: html

    <div style="width: 100%;display: inline-block;position: relative;">
        <div id="dummy" style="margin-top: 56%;">
        </div>
        <div align="center">
        <div id="kaltura_player_1" style="position:absolute;top:0;left:0;left: 0;right: 0;bottom:0;border:solid thin black;"></div>
        <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/46302491"></script>
        <script type="text/javascript">
            try {
            var kalturaPlayer = KalturaPlayer.setup({
            targetId: "kaltura_player_1",
            provider:
            { partnerId: 2935771, uiConfId: 46302491 }
            });
            kalturaPlayer.loadMedia(
            {entryId: '1_3629t1cp'}
            );
            } catch (e)
            { console.error(e.message) }
        </script>
        </div>
    </div>

Summary
=======================

In this tutorial you learned how to manually step ROS 2 components and run standalone ROS 2 Python examples.

Next Steps
****************
Continue on to the next tutorial in our ROS 2 Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_navigation` to learn to use ROS 2 Nav2 with |isaac-sim|.


