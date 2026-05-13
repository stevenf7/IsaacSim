

..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_tutorial_ros2_publish_rate:

======================================
ROS2 Setting Publish Rates
======================================

Learning Objectives
=======================

In this example, you learn to:

- Set the simulation frame rate in |isaac-sim_short|.
- Set different publish rates for different sensor types (IMU, RTX Lidar, Camera) publishing to ROS 2 simultaneously.


Getting Started
=============================



**Prerequisite**

- Completed the :ref:`isaac_sim_app_tutorial_ros2_turtlebot`, :ref:`isaac_sim_app_tutorial_ros2_camera`, :ref:`isaac_sim_app_tutorial_ros2_rtx_lidar`, and :ref:`isaac_sim_app_tutorial_ros2_tf` tutorials.
- Completed :ref:`isaac_sim_app_install_ros` so that the necessary environment variables are set and sourced before launching |isaac-sim|, and ROS2 extension is enabled.


Setting Publish Rates with |omnigraph_short|
===================================================
Action Graphs are ticked every simulation frame and therefore |omnigraph_short| nodes are bound to the factors of the simulation rate. This tutorial explains how to configure publishing ROS2 nodes at these factors of simulation.

Non-RTX Sensors
^^^^^^^^^^^^^^^

Sensors which do not rely on RTX rendering, such as IMU sensors, can be configured to publish at a different rate than the simulation rate using the Isaac Simulation Gate node.

1. Open the turtlebot simple room scene, which can be found by going to the Isaac Sim Content browser and clicking **Isaac Sim>Samples>ROS2>Scenario>turtlebot_tutorial.usd**.

2. Select the prim at ``/World/turtlebot3_burger/base_link/imu_link`` and then create an IMU sensor by going to **Create > Isaac > Sensors > Imu Sensor**. Verify that the Imu sensor is created under the *imu_link* prim.

3. Create a new Action Graph inside */World/turtlebot3_burger/base_link/imu_link* prim and name it *ROS_IMU* (the placement of the graph is important for :ref:`isaac_sim_app_tutorial_ros2_auto_namespace`). To do this, select the prim at ``/World/turtlebot3_burger/base_link/imu_link`` and then create an Action Graph by going to **Window > Graph Editors > Action Graph**.

4. Make the graph for IMU including the simulation gate node and attach the graph as shown below.

    .. figure:: /images/isaac_tutorial_ros2_publish_rate_imu_graph.png
        :align: center
        :width: 800
        :alt: Turtlebot IMU Graph

    Set the following attributes for each node as such:

    - In the Property tab for the **Isaac Simulation Gate** node:

        - Set the *step* attribute to ``2``. Having a step size of ``2`` means that downstream nodes will be ticked every other frame.

    - In the Property tab for the **Isaac Read IMU Node**:

        - Add the IMU sensor prim ``/World/turtlebot3_burger/base_link/imu_link/Imu_Sensor`` to its *imuPrim* input field.

    - In the Property tab for the **ROS2 Publish Imu** node:

        - Set the frameId attribute to ``imu_link``. This will match the ``imu_link`` frame used in the TF tree that is already being published by the TF publisher, which you created in :ref:`isaac_sim_app_tutorial_ros2_tf_odometry`.



RTX Sensors
^^^^^^^^^^^^

Cameras, RTX Lidars, and RTX Radars can be configured to publish at a different rate than the simulation rate using the ``omni:sensor:tickRate`` attribute on the sensor prim, described in :ref:`isaac_sim_sensors_multitick_configuring_per_sensor_tick_rates`.

.. warning::
    Previous versions of |isaac-sim_short| used the **frameSkipCount** parameter on ROS2 helper nodes to control sensor publish rates. This is now deprecated.
    If **frameSkipCount** is set to a non-zero value, and the corresponding sensor prim has ``omni:sensor:tickRate`` set to a non-zero value, message publishing frequency may be unexpected as the **frameSkipCount** may not
    align periodically with the sensor's tick rate. See :ref:`isaac_sim_sensors_multitick_configuring_per_sensor_tick_rates`, and
    :ref:`isaac_sim_sensors_multitick_rendering` for the full migration guide.

1. Select the 2D Lidar prim ``/World/turtlebot3_burger/base_scan/Example_Rotary_2D`` (the ``OmniLidar`` referenced as ``cameraPrim`` on the ``Isaac Create Render Product`` node feeding ``/World/turtlebot3_burger/base_scan/ROS_LidarRTX/LaserScanPublish``). In the **Property** tab:

    - Set ``omni:sensor:tickRate`` to ``5``. The laser scan publishes once per tick, so this yields a publish rate of 5 Hz (every 12 frames at the default 60 Hz simulation rate).
    - Set ``omni:sensor:Core:scanRateBaseHz`` to ``5`` to match. The two values must be equal so the lidar accumulates a full scan per tick instead of falling back to per-frame partial scans (see :ref:`isaac_sim_sensors_multitick_lidar_tickrate_must_match_scanrate`). The shipped ``Example_Rotary_2D`` asset defaults to ``10``, so you must lower it.

2. Because you don't need to publish a point cloud in this tutorial, select the Ros2RTXLidarHelper node for point cloud and disable it by unchecking **enabled** attribute in */World/turtlebot3_burger/base_scan/ROS_LidarRTX/PointCloudPublish*.

3. Open the camera Action Graph */World/ActionGraph_camera*. Disable the second camera render product by unchecking **enabled** attribute in */World/ActionGraph_camera/isaac_create_render_product_01*.

4. Select the camera prim ``/World/Camera_1`` (the ``Camera`` referenced as ``cameraPrim`` on the ``Isaac Create Render Product`` node feeding both ``/World/ActionGraph_camera/ros2_camera_helper`` and ``/World/ActionGraph_camera/ros2_camera_info_helper``). In the **Property** tab, set ``omni:sensor:tickRate`` to ``15``. Both ``/camera_1/rgb/image_raw`` and ``/camera_1/rgb/camera_info`` now publish at 15 Hz (every 4 frames at the default 60 Hz simulation rate).


5. You don't need to publish depth images from Camera1 for this tutorial. Disable the camera helper for depth images by unchecking **enabled** attribute in */World/ActionGraph_camera/ros2_camera_helper_02*.

.. _isaac_sim_app_tutorial_ros2_publish_rate_set_simulation_frame_rates:

Setting Simulation Frame Rates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You configured the ActionGraphs to tick certain nodes at various rates. Because all Action Graphs are capped to the maximum frame rate defined for simulation rate, you can modify this simulation frame rate using the Python interface.


1. Set the rate of simulation by running Python code in the script editor. Open the script editor by going to **Window > Script Editor**.

    There are two ways to set simulation rates:

    a. Changing the carb setting. Run the script below after playing the scene. This method aims to set the simulation timeline run rate. This affects time from the OnPlayBackTick node.

        .. code-block:: bash

            # Change the carb settings. This is not persistent between when stopping and replaying

            import carb
            physics_rate = 60 # fps
            carb_settings = carb.settings.get_settings()
            carb.settings.get_settings().set_bool("/app/runLoops/main/rateLimitEnabled", True)
            carb.settings.get_settings().set_int("/app/runLoops/main/rateLimitFrequency", int(physics_rate))
            carb.settings.get_settings().set_int("/persistent/simulation/minFrameRate", int(physics_rate))

    b. Changing *SetTimeCodesPerSecond* and *set_target_framerate*. This method aims to set physics run rate. This will affect time from the IsaacReadSimulationTime node.

        .. note:: The Time Codes Per Second can only be set once before a scene is played. If you would like to change this value, reload a scene first.

        .. code-block:: bash

            # This must be called after a stage is loaded. Timeline must be stopped when setting SetTimeCodesPerSecond and set_target_framerate. This is persistent between stopping and replaying:
            import omni
            physics_rate = 60 # fps

            timeline = omni.timeline.get_timeline_interface()
            stage = omni.usd.get_context().get_stage()
            timeline.stop()

            stage.SetTimeCodesPerSecond(physics_rate)
            timeline.set_target_framerate(physics_rate)

            timeline.play()

2. Run the snippets in the script editor and notice its effect on the simulation rate. You can enable the FPS display by going to the viewport show/hide menu **(eye) > Heads Up Display > FPS**.

    Try modifying the **physics_rate** to a different value and check the FPS reading.

.. important:: Keep in mind that both methods are setting the target frame rate of simulation. Actual frame rate is dependent on your machine's performance.

Checking ROS 2 Publish Rate
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Press **Play** to start the simulation.
2. Check the publish rate for each ROS topic using the command:

    .. code::

      ros2 topic hz /topic_name

    Where ``/topic_name`` is replaced by each sensor topic listed below.

    The publish rates are estimated. On a high-performance machine the maximum FPS would be closer to the ``physics_rate`` that was set in the previous section (default of 60Hz).

3.  For each sensor topic, the rate is a factor of the maximum simulation FPS (according to the execution steps that we defined earlier).

    - **/clock**:  publish at same rate as the simulation FPS (~60hz default).
    - **/imu**:  publish at rate of *sim_fps/2* (~30 hz)
    - **/scan**:  publish at rate *sim_fps/12* (~5 hz)
    - **/camera_1/rgb/image_raw**:  publish at *sim_fps/4* (~15 Hz)
    - **/camera_1/rgb/camera_info**:  publish at *sim_fps/4* (~15 Hz, matching the RGB rate because both helpers share the same Camera prim's tick rate)

    The file that contains all of the steps in this tutorial can be opened by going to the Isaac Sim Content browser and clicking **Isaac Sim>Samples>ROS2>Scenario>turtlebot_tutorial_multi_sensor_publish_rates.usd**. After opening the file, remember to run the steps in :ref:`isaac_sim_app_tutorial_ros2_publish_rate_set_simulation_frame_rates` to set the target simulation rate.

    .. note:: If you observe that the */camera_1/rgb/image_raw* topic is publishing at a slower rate than anticipated, it might be because the large size of each image message is causing bottlenecks in network traffic or DDS queue management. To improve the publish rate, you can try reducing the dimensions of the render product resolution. This can be done by going to the render product node that is attached to the image publisher */World/ActionGraph_camera/isaac_create_render_product* and modifying the dimensions before replaying the scene.


.. _isaac_sim_app_tutorial_ros2_publish_rate_troubleshoot:

Troubleshooting
^^^^^^^^^^^^^^^^^^^

If you observe much different publish rates from the target simulation frame rate, try the following:

1. Try running |isaac-sim_short| with factory settings to clear any persistent simulation frame rate settings:

    .. code-block:: bash

        ./isaac-sim.sh --reset-user

2. Check your computer's CPU usage to identify bottlenecks. If Isaac Sim is exhibiting incredibly high usage try running with *Fabric* enabled:

    .. code-block:: bash

        ./isaac-sim.fabric.sh --reset-user


    .. important:: The above command is experimental and not all functionality of Isaac Sim is supported there. However you might observe better overall performance. You only need to use the ``--reset-user`` flag the first time running with *Fabric*.



Summary
=======================

This tutorial covered:

- Two ways to set the simulation frame rate in |isaac-sim_short| using the Python interface.
- Setting different publish rates for different sensor types: an Isaac Simulation Gate for non-RTX sensors (IMU), and ``omni:sensor:tickRate`` on the sensor prim for RTX sensors (Lidar, Camera).

Next Steps
^^^^^^^^^^^^^^^^^^^^^^
Continue on to the next tutorial in our ROS2 Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_qos` to learn about setting QoS Profiles for ROS 2 |omnigraph_short| nodes in |isaac-sim|.


