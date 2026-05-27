

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

2. In the **Stage** panel, right-click the prim ``/World/turtlebot3_burger_processed/Geometry/base_footprint/base_link/imu_link`` and choose **Create > Isaac > Sensors > Imu Sensor** from the context menu. Using the right-click menu on the link prim is what parents the sensor under *imu_link*; the top **Create > Sensors > Imu Sensor** menu-bar entry creates the sensor at the stage root instead. Verify that the Imu sensor is created under the *imu_link* prim.

3. Create a new Action Graph inside */World/turtlebot3_burger_processed/Geometry/base_footprint/base_link/imu_link* prim and name it *ROS_IMU* (the placement of the graph is important for :ref:`isaac_sim_app_tutorial_ros2_auto_namespace`). To do this, select the prim at ``/World/turtlebot3_burger_processed/Geometry/base_footprint/base_link/imu_link`` and then create an Action Graph by going to **Window > Graph Editors > Action Graph**.

4. Make the graph for IMU including the simulation gate node and attach the graph as shown below.

    .. figure:: /images/isaac_tutorial_ros2_publish_rate_imu_graph.png
        :align: center
        :width: 800
        :alt: Turtlebot IMU Graph

    Set the following attributes for each node as such:

    - In the Property tab for the **Isaac Simulation Gate** node:

        - Set the *step* attribute to ``2``. Having a step size of ``2`` means that downstream nodes will be ticked every other frame.

    - In the Property tab for the **Isaac Read IMU Node**:

        - Add the IMU sensor prim ``/World/turtlebot3_burger_processed/Geometry/base_footprint/base_link/imu_link/Imu_Sensor`` to its *imuPrim* input field.

    - In the Property tab for the **ROS2 Publish Imu** node:

        - Set the frameId attribute to ``imu_link``. This will match the ``imu_link`` frame used in the TF tree that is already being published by the TF publisher, which you created in :ref:`isaac_sim_app_tutorial_ros2_tf_odometry`.



RTX Sensors
^^^^^^^^^^^^

Cameras and RTX Lidars can be configured to publish at a different rate than the simulation rate using the ``omni:sensor:tickRate`` attribute on the sensor prim, described in :ref:`isaac_sim_sensors_multitick_configuring_per_sensor_tick_rates`.

.. warning::
    Previous versions of |isaac-sim_short| used the **frameSkipCount** parameter on ROS2 helper nodes to control sensor publish rates. This is now deprecated.
    If **frameSkipCount** is set to a non-zero value, and the corresponding sensor prim has ``omni:sensor:tickRate`` set to a non-zero value, message publishing frequency may be unexpected as the **frameSkipCount** may not
    align periodically with the sensor's tick rate. See :ref:`isaac_sim_sensors_multitick_configuring_per_sensor_tick_rates`, and
    :ref:`isaac_sim_sensors_multitick_rendering` for the full migration guide.

1. Select the 2D Lidar prim ``/World/turtlebot3_burger_processed/Geometry/base_footprint/base_link/base_scan/Example_Rotary_2D`` (the ``OmniLidar`` referenced as ``cameraPrim`` on the ``Isaac Create Render Product`` node feeding ``/World/turtlebot3_burger_processed/Geometry/base_footprint/base_link/base_scan/ROS_LidarRTX/LaserScanPublish``). In the **Property** tab:

    - Set ``omni:sensor:tickRate`` to ``5``. The laser scan publishes once per tick, so this yields a publish rate of ``R_lidar = 5`` Hz (independent of the simulation rate, as long as the simulation rate is at least 5 Hz).
    - Set ``omni:sensor:Core:scanRateBaseHz`` to ``5`` to match. The two values must be equal so the Lidar accumulates a full scan per tick instead of falling back to per-frame partial scans (see :ref:`isaac_sim_sensors_multitick_lidar_tickrate_must_match_scanrate`). The shipped ``Example_Rotary_2D`` asset defaults to ``10``, so you must lower it.

2. Because you don't need to publish a point cloud in this tutorial, select the Ros2RTXLidarHelper node for point cloud and disable it by unchecking **enabled** attribute in */World/turtlebot3_burger_processed/Geometry/base_footprint/base_link/base_scan/ROS_LidarRTX/PointCloudPublish*.

3. Open the camera Action Graph */World/ActionGraph_camera*. Disable the second camera render product by unchecking **enabled** attribute in */World/ActionGraph_camera/isaac_create_render_product_01*.

4. Select the camera prim ``/World/Camera_1`` (the ``Camera`` referenced as ``cameraPrim`` on the ``Isaac Create Render Product`` node feeding both ``/World/ActionGraph_camera/ros2_camera_helper`` and ``/World/ActionGraph_camera/ros2_camera_info_helper``). In the **Property** tab, set ``omni:sensor:tickRate`` to ``15``. Both ``/camera_1/rgb/image_raw`` and ``/camera_1/rgb/camera_info`` now publish at ``R_cam = 15`` Hz (independent of the simulation rate, as long as the simulation rate is at least 15 Hz).

    .. note::

        Cameras created from the top **Create > Camera** menu bar (as in the prerequisite :ref:`isaac_sim_app_tutorial_ros2_camera`) do **not** carry the ``omni:sensor:tickRate`` attribute by default. If you do not see it in the **Property** tab, scroll to the **Raw USD Properties** section, click **Add** > **omni:sensor:tickRate** to add the attribute, then set its value to ``15``. The shipped ``turtlebot_tutorial.usd`` already has the attribute applied to ``/World/Camera_1`` and ``/World/Camera_2``.


5. You don't need to publish depth images from Camera1 for this tutorial. Disable the camera helper for depth images by unchecking **enabled** attribute in */World/ActionGraph_camera/ros2_camera_helper_02*.

Checking ROS 2 Publish Rate
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Press **Play** to start the simulation.
2. Check the publish rate for each ROS topic using the command:

    .. code::

      ros2 topic hz /topic_name

    Where ``/topic_name`` is replaced by each sensor topic listed below.

    The publish rates are estimated. On a high-performance machine the maximum FPS would be closer to the ``target_hz`` that was set in the previous section (default of 60 Hz).

3. The topics fall into two categories that scale differently with ``target_hz``:

    - **OnPlaybackTick-driven publishers** (gated by app updates):

        - **/clock**: ``target_hz`` (~60 Hz default; one message per app update).
        - **/imu**: ``target_hz / k_imu`` (~30 Hz default; ``k_imu = 2`` is the Isaac Simulation Gate step you set earlier).

    - **Multi-tick-scheduled RTX sensors** (gated by ``/ExternalSimulationTime`` and the per-sensor ``omni:sensor:tickRate``, when the simulation runs in real time - i.e. the snippet from :ref:`isaac_sim_app_tutorial_ros2_publish_rate_set_simulation_frame_rates` was used):

        - **/scan**: ``min(R_lidar, target_hz) = 5`` Hz (constant in ``target_hz`` as long as ``target_hz >= 5``).
        - **/camera_1/rgb/image_raw**: ``min(R_cam, target_hz) = 15`` Hz (constant in ``target_hz`` as long as ``target_hz >= 15``).
        - **/camera_1/rgb/camera_info**: same as RGB, because both helpers share the same Camera prim's tick rate.

    The file that contains all of the steps in this tutorial can be opened by going to the Isaac Sim Content browser and clicking **Isaac Sim>Samples>ROS2>Scenario>turtlebot_tutorial_multi_sensor_publish_rates.usd**. After opening the file, remember to run the steps in :ref:`isaac_sim_app_tutorial_ros2_publish_rate_set_simulation_frame_rates` to set the target simulation rate.

    .. note:: If you observe that the */camera_1/rgb/image_raw* topic is publishing at a slower rate than anticipated, it might be because the large size of each image message is causing bottlenecks in network traffic or DDS queue management. To improve the publish rate, you can try reducing the dimensions of the render product resolution. This can be done by going to the render product node that is attached to the image publisher */World/ActionGraph_camera/isaac_create_render_product* and modifying the dimensions before replaying the scene.

.. _isaac_sim_app_tutorial_ros2_publish_rate_set_simulation_frame_rates:

Setting the Simulation Rate (Advanced)
======================================

Isaac Sim has three rate-related clocks: the physics scene's step rate (``UsdPhysicsScene.timeStepsPerSecond``), the timeline's per-tick dt (``stage.timeCodesPerSecond`` combined with the timeline's ``targetFramerate``), and the application's run-loop tick rate (``/app/runLoops/main/rateLimitFrequency``). For real-time playback you want all three set coherently to the same value. :py:meth:`isaacsim.core.simulation_manager.SimulationManager.setup_simulation` configures the physics scene's step rate; :py:meth:`isaacsim.core.rendering_manager.RenderingManager.set_dt` configures the timeline and run-loop together. Use them as a pair.

.. warning:: In |isaac-sim_short| 6.0, there is a known fatal crash in the full UI app when playing the simulation after modifying the simulation's physics scene's step rate and timeline's per-tick dt from their default values of ``60.0`` and then playing the simulation. This will be fixed in a future release.

Paste the following snippet into a standalone Python script in the Isaac Sim directory, eg. ``test_ros2_publish_rates.py``.

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_publish_rate/test_ros2_publish_rates.py
    :language: python

Then, run the script using the command:

.. code-block:: bash

    ./python.sh test_ros2_publish_rates.py \
    --/app/runLoops/main/rateLimitEnabled=true \
    --/app/runLoops/main/rateLimitFrequency=60 \
    --/app/runLoops/main/manualModeEnabled=true

This will force the simulation to run at 60 frames per wall-clock second (FPS).

In a separate terminal window with ROS2 installed and enabled, check the publish rate for each ROS topic using the command:

.. code-block:: bash

    ros2 topic hz /topic_name

If you change ``target_hz`` in the script, then rerun it with the command provided above, each topic scales differently because the topics are gated by two different mechanisms:

- **OnPlaybackTick-driven helpers** (``/clock`` publisher and the IMU graph through its **Isaac Simulation Gate**) fire once per app update, so their wall-clock rate scales linearly with ``target_hz`` (divided by the gate ``step`` for IMU).
- **Multi-tick-scheduled RTX sensors** (``/scan``, ``/camera_1/rgb/image_raw``, ``/camera_1/rgb/camera_info``) fire when the renderer's simulation time has advanced by ``1 / omni:sensor:tickRate``, so they hold at the configured Hz independently of ``target_hz`` - until ``target_hz`` drops below the configured tick rate, at which point the sensor is capped at one tick per app update. See :ref:`isaac_sim_sensors_multitick_clock_relationships` for the underlying machinery.

For the tutorial setup (``R_lidar = omni:sensor:tickRate = 5`` on the Lidar prim, ``R_cam = omni:sensor:tickRate = 15`` on the Camera prim, IMU gate ``step = 2``), the wall-clock publish rates are:

.. csv-table::
    :header: "``target_hz`` (Hz)", "``/clock``", "``/imu``", "``/scan``", "``/camera_1/rgb/image_raw``, ``/camera_1/rgb/camera_info``"
    :widths: 14, 12, 12, 12, 50

    "30",  "30",  "15",  "5", "15"
    "60",  "60",  "30",  "5", "15"
    "120", "120", "60",  "5", "15"
    "240", "240", "120", "5", "15"
    "10",  "10",  "5",   "5", "10 (capped at ``target_hz``)"

The publish rates are estimated. On a high-performance machine the maximum FPS would be closer to the ``target_hz`` that was set in the previous section (default of 60 Hz).

.. important:: Actual frame rate is dependent on your machine's performance. If the renderer cannot sustain ``target_hz``, sensor publish rates will fall proportionally. For the relationship between the three clocks and what happens when they fall out of sync (slow-motion, fast-forward), see :ref:`isaac_sim_sensors_multitick_clock_relationships`.

The general formulas are:

.. code-block:: text

    clock_hz   = target_hz
    imu_hz     = target_hz / k_imu                 # k_imu = Isaac Simulation Gate step (= 2 here)
    scan_hz    = min(R_lidar, target_hz)
    camera_hz  = min(R_cam, target_hz)

.. note::

    The ``/camera_1/rgb/image_raw`` (and ``/camera_1/rgb/camera_info``) publish rate may fall below the table's predicted value even when the multi-tick scheduler is firing at the configured ``R_cam`` Hz. The RGB image path is computationally heavier than the other topics: the render product cost scales with resolution, and the published image size also stresses the DDS / network layer. If the observed rate is below ``R_cam``, the two knobs to try first are (1) lowering the render product resolution on ``/World/ActionGraph_camera/isaac_create_render_product``, and (2) lowering ``omni:sensor:tickRate`` on the ``/World/Camera_1`` prim to reduce render frequency. This complements the network/DDS note above.

.. note::

    If you change ``omni:sensor:tickRate`` on the Lidar prim, you must change ``omni:sensor:Core:scanRateBaseHz`` to match. The two values must be equal or the Lidar emits partial scans every frame instead of accumulating a full scan per tick; see :ref:`isaac_sim_sensors_multitick_lidar_tickrate_must_match_scanrate`.

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

- Setting a coherent simulation rate using ``SimulationManager.setup_simulation`` and ``RenderingManager.set_dt`` from the Python interface.
- Setting different publish rates for different sensor types: an Isaac Simulation Gate for non-RTX sensors (IMU), and ``omni:sensor:tickRate`` on the sensor prim for RTX sensors (Lidar, Camera).

Next Steps
^^^^^^^^^^^^^^^^^^^^^^
Continue on to the next tutorial in our ROS2 Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_qos` to learn about setting QoS Profiles for ROS 2 |omnigraph_short| nodes in |isaac-sim|.
