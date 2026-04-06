

..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaac_sim_app_tutorial_ros2_navigation:

===============================
ROS 2 Navigation
===============================

**Support Limitations**

* ROS 2 Navigation with |isaac-sim_short| is fully supported on Linux and Windows with Pixi-based installation. On Windows (WSL), ROS 2 Navigation with |isaac-sim_short| is partially supported and could potentially produce errors.



Learning Objectives
=======================

This ROS2 sample demonstrates |isaac-sim| integrated with ROS2 Nav2.


Getting Started
===========================


**Prerequisite**

- You must source your ROS 2 installation from the terminal before running |isaac-sim_short|.

- The Nav2 project is required to run this sample. To install Nav2 refer to the `Nav2 installation page <https://docs.nav2.org/getting_started/index.html#installation>`_.

- Enable the ``isaacsim.ros2.bridge`` Extension in the **Extension Manager** window by navigating to **Window** > **Extensions**.

- This tutorial requires ``carter_navigation``, ``iw_hub_navigation``, and ``isaac_ros_navigation_goal`` ROS2 packages, which are provided as part of your |isaac-sim| download. These ROS2 packages are located inside the appropriate ``ros2_ws``. They contain the required launch file, navigation parameters, and robot model. Complete :ref:`isaac_sim_app_install_ros`, specifically the :ref:`isaac_sim_ros_workspace_setup` steps, to make sure the ROS 2 workspace is built and sourced correctly.

.. note:: In Windows 10 or 11, depending on your machine's configuration, RViz2 might not open properly.

Nav2 Setup
======================

This block diagram shows the ROS2 messages required for Nav2:

.. figure:: /images/isaac_sample_ros2_nav_1.png
    :align: center
    :width: 800
    :alt: ROS2 Nav2 Overview Block Diagram

The following topics and message types being published to Nav2 in this scenario are:

    ============= ======================
    ROS2 Topic    ROS2 Message Type
    ============= ======================
    /tf           tf2_msgs/TFMessage
    /odom         nav_msgs/Odometry
    /map          nav_msgs/OccupancyGrid
    /point_cloud  sensor_msgs/PointCloud
    /scan         sensor_msgs/LaserScan (published by an external `pointcloud_to_laserscan <https://index.ros.org/p/pointcloud_to_laserscan/>`_ node)
    ============= ======================

.. .. _isaac_sim_app_carter_ros2_omnigraph:

.. Carter_ROS OmniGraph Nodes
.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..
.. 1. Go to `Robotics Examples > ROS2 > Navigation > Carter Navigation` to load the warehouse scenario.

.. 1. Open the main `ActionGraph` by expanding ``Carter_ROS``. Right click on ``ActionGraph`` and press `Open Graph`. The following ROS |omnigraph_short| nodes are setup to do the following:

..     =============================== ================
..     Omnigraph Node                 Function
..     =============================== ================
..     ros2_subscribe_twist            Subscribes to the `/cmd_vel` topic and triggers the differential and articulation controllers to move the robot
..     ros2_publish_odometry           Publishes odometry received from the ``isaac_compute_odometry_node``
..     ros2_publish_raw_transform_tree Publishes the transform between the `odom` frame and `base_link` frame
..     ros2_publish_transform_tree     Publishes the static transform between the `base_link` frame and `chassis_link` frame. Keep in mind that since the target prim is set as ``Carter_ROS``, the entire transform tree of the Carter robot (with chassis_link as root) will be published as children of the `base_link` frame
..     ros2_publish_transform_tree_01  Publishes the static transform between the `chassis_link` frame and `carter_lidar` frame
..     ros2_publish_laser_scan         Publishes the 2D LaserScan received from the ``isaac_read_lidar_beams_node``
..     ros2_context                    Sets the ROS2 context with the default domain ID of 0
..     =============================== ================

.. 2. Open the `ROS_Cameras` graph by expanding ``Carter_ROS``. Right click on ``ROS_Cameras`` and press `Open Graph`. The following ROS Camera |omnigraph_short| nodes are setup to do the following:

..     =============================== ================
..     Omnigraph Node                 Function
..     =============================== ================
..     ros2_create_camera_left_info    Auto-generates the CameraInfo publisher for the `/camera_info_left` topic. It automatically publishes since the ``enable_camera_left`` branch node is enabled by default
..     ros2_create_camera_left_rgb     Auto-generates the RGB Image publisher for the `/rgb_left` topic. It automatically publishes since the ``enable_camera_left`` and ``enable_camera_left_rgb`` branch nodes are enabled by default
..     ros2_create_camera_left_depth   Auto-generates the Depth (32FC1) Image publisher for the `/depth_left` topic. To start publishing, ensure ``enable_camera_left`` and ``enable_camera_left_depth`` branch nodes are enabled
..     ros2_create_camera_right_info   Auto-generates the CameraInfo publisher for the `/camera_info_right` topic. To start publishing, ensure the ``enable_camera_right`` branch node is enabled
..     ros2_create_camera_right_rgb    Auto-generates the RGB Image publisher for the `/rgb_right` topic. To start publishing, ensure ``enable_camera_right`` is enabled. The ``enable_camera_right_rgb`` branch node is already enabled by default
..     ros2_create_camera_right_depth  Auto-generates the Depth (32FC1) Image publisher for the `/depth_right` topic. To start publishing, ensure ``enable_camera_right`` and ``enable_camera_right_depth`` branch nodes are enabled
..     ros2_context                    Sets the ROS2 context with the default domain ID of 0
..     =============================== ================


.. 3. Finally, to ensure all external ROS nodes reference simulation time, a ``ROS_Clock`` graph is added, which contains a ``ros2_publish_clock`` node responsible for publishing the simulation time to the `/clock` topic.


Occupancy Map
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In this scenario, an occupancy map is required. For this sample, you are generating an occupancy map of the warehouse environment using the :ref:`Occupancy Map Generator extension<ext_isaacsim_asset_generator_occupancy_map>` within |isaac-sim|.

#. Go to **Window > Examples > Robotics Examples**. Click on the **Robotics Examples** tab. Expand the sections on the left hand side. Open the example: **ROS2 > Navigation > Nova Carter** to load the warehouse scenario with the :ref:`Nova Carter robot<isaac_nova_carter>`.

#. At the upper left corner of the viewport, click on **Camera**. Select **Top** from the dropdown menu.

#. Go to **Tools > Robotics > Occupancy Map**.

#. In the Occupancy Map extension, ensure the Origin is set to ``X: 0.0, Y: 0.0, Z: 0.0``. For the lower bound, set ``Z: 0.1``. For the Upper Bound, set ``Z: 0.62``. Keep in mind, the upper bound Z distance has been set to 0.62 meters to match the vertical distance of the Lidar onboard Nova Carter with respect to the ground.

#. Select the ``warehouse_with_forklifts`` prim in the stage. In the Occupancy Map extension, click on **BOUND SELECTION**. Verify that the bounds of the occupancy map are updated to incorporate the selected `warehouse_with_forklifts` prim. Verify that the map parameters now look similar to the following:

    .. figure:: /images/isaac_sample_ros_nav_2.png
        :align: center
        :width: 600
        :alt: Occupancy Map Properties UI Window


    Verify that a perimeter is generated and that it resembles this Top View:

    .. figure:: /images/isim_5.0_ros_tut_viewport_ros_nav_occupancy_map.png
        :align: center
        :width: 600
        :alt: Top View of Warehouse with Occupancy Map

#. Delete the ``Nova_Carter_ROS`` prim from the stage.

#. After the setup is complete, click on **CALCULATE** followed by **VISUALIZE IMAGE**. A Visualization popup will appear.

#. For `Rotate Image`, select 180 degrees and for `Coordinate Type` select **ROS Occupancy Map Parameters File (YAML)**. Click **RE-GENERATE IMAGE**. The ROS camera and Isaac Sim camera have different coordinates.

#. Click **Save YAML** and save the YAML file to ``~/<ros2_ws>/src/navigation/carter_navigation/maps/carter_warehouse_navigation.yaml``.

#. Back in the visualization tab in |isaac-sim|, click **Save Image**. Name the image as ``carter_warehouse_navigation.png`` and choose to save it in the same directory as the map parameters file.

    Verify that the final saved image looks like the following:

    .. figure:: /images/isaac_sample_ros_nav_warehouse_map.png
        :align: center
        :width: 500
        :alt: Sample Occupancy Map generated from warehouse stage


An occupancy map is now ready to be used with Nav2.


.. _Running Nav2:

Running Nav2
===========================

Nav2 with Nova Carter in a Small Warehouse
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Go to **Window > Examples > Robotics Examples**, and then click on the **Robotics Examples** tab and expand the sections on the left hand side and open the example: **ROS2 > Navigation > Nova Carter** to load the warehouse scenario with the :ref:`Nova Carter robot<isaac_nova_carter>`.

#. Click on **Play** to begin simulation.

#. In a new terminal, run the ROS2 launch file to begin Nav2.

    .. code-block:: bash

        ros2 launch carter_navigation carter_navigation.launch.py

    RViz2 opens and begins loading the occupancy map. If a map does not appear, repeat the previous step.


#. Because the position of the robot is defined in the parameter file ``carter_navigation_params.yaml``, verify that the robot is already properly localized. If required, the **2D Pose Estimate** button can be used to re-set the position of the robot.


#. Click on the **Navigation2 Goal** button and then click and drag at the desired location point in the map. Nav2 now generates a trajectory and the robot starts moving towards its destination.

.. raw:: html

    <div style="width: 100%;display: inline-block;position: relative;">
        <div id="dummy" style="margin-top: 56%;">
        </div>
        <div align="center">
        <div id="kaltura_player_2" style="position:absolute;top:0;left:0;left: 0;right: 0;bottom:0;border:solid thin black;"></div>
        <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/46302491"></script>
        <script type="text/javascript">
            try {
            var kalturaPlayer = KalturaPlayer.setup({
            targetId: "kaltura_player_2",
            provider:
            { partnerId: 2935771, uiConfId: 46302491 }
            });
            kalturaPlayer.loadMedia(
            {entryId: '1_3hz44ehw'}
            );
            } catch (e)
            { console.error(e.message) }
        </script>
        </div>
    </div>

.. note::

    * The Carter robot uses the RTX Lidar by default. You can add people assets into the scene and they will be detected by the Lidar when being passed to Nav2.

    * Some of the ROS2 Image publisher pipelines in the Hawk cameras are disabled by default to improve performance. To start publishing images, open the ``_hawk`` action graphs found under the robot prim and enable the ``_camera_render_product`` nodes. Verify that the ROS Camera publisher nodes, which are downstream of the render product nodes, are enabled by default and that they start publishing when the render product node is enabled. All sensors and images in Nova Carter are being published with `Sensor Data QoS <https://docs.ros.org/en/rolling/Concepts/Intermediate/About-Quality-of-Service-Settings.html#qos-profiles>`_. If you want to visualize the images in RViz, expand the image tab, navigate to **Topic > Reliability Policy** and change the policy to **Best Effort**.

    * If you notice issues with localizing the robot in open spaces, this is a known issue likely attributed to lower performance. To improve localization, try adding more objects into the scene to introduce more features.

    * If you notice warnings as shown below, you can disregard them because they are harmless.

        .. code-block::

            [Warning] [omni.graph.core.plugin] /World/Nova_Carter_ROS/differential_drive/differential_controller_01: [/World/Nova_Carter_ROS/differential_drive] invalid dt 0.000000, cannot check for acceleration limits, skipping current step


Nav2 with Nova Carter with Robot Description in a Small Warehouse
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In addition to the previous steps, you can visualize the robot description in the simulation.

#. Install the **nova_carter_description** package. Follow the steps :ref:`isaac_sim_app_tutorial_ros2_nav_nova_carter_description` section.

#. Launch the Nova Carter description using the launch file that is already provided as part of Isaac Sim Workspaces. This launch file depends on **nova_carter_description** package being in the system.

    .. code-block:: bash

        ros2 launch carter_navigation nova_carter_description_isaac_sim.launch.py

#. Open the navigation scene in Isaac Sim. Go to **Window > Examples > Robotics Examples**, and then click on the **Robotics Examples** tab and expand the sections on the left hand side and open the example: 
   
    **ROS2 > Navigation > Nova Carter** to load the warehouse scenario with the :ref:`Nova Carter robot<isaac_nova_carter>`.

#. Click on **Play** to begin simulation.

#. In a new terminal, run the ROS2 launch file to begin Nav2.

    .. code-block:: bash

        ros2 launch carter_navigation carter_navigation.launch.py

    RViz2 opens and begins loading the occupancy map. If a map does not appear, repeat the previous step.

#. Verify that the robot model is automatically loaded in the scene in Rviz.

.. raw:: html

    <div style="width: 100%;display: inline-block;position: relative;">
    <div align="center">
    <div id="kaltura_player_414856343" style="width: 560px;height: 395px"></div>
    <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/53712482"></script>
    <script type="text/javascript">
    try {
        var kalturaPlayer = KalturaPlayer.setup({
        targetId: "kaltura_player_414856343",
        provider: {
            partnerId: 2935771,
            uiConfId: 53712482
        }
        });
        kalturaPlayer.loadMedia({entryId: '1_lpendbcw'});
    } catch (e) {
        console.error(e.message)
    }
    </script>
    </div>
    </div>

.. _isaac_sim_app_tutorial_ros2_nav_robot_state_publisher:

Nav2 with Nova Carter with robot_state_publisher in a Small Warehouse
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The previous Nova Carter warehouse scene had the robot publish transforms (TFs) directly from Isaac Sim. As your robot and scene assets become more complex, it will be more scalable and performant to publish static TFs of the robot using the default ROS 2 `robot_state_publisher <https://github.com/ros/robot_state_publisher>`_ package instead. This way, the robot state publisher will parse the robot URDF and publish the static TFs. Meanwhile, Isaac Sim will be responsible for publishing joint states for moving joints. The robot state publisher will then receive these joint states and convert them to corresponding transforms, adding them to the overall TF tree.

A new Nova Carter robot asset called ``Nova_Carter_Joint_States_ROS.usd`` has been created. This asset differs from the original ``Nova_Carter_ROS.usd`` in the following ways:

- The ``transform_tree_odometry`` action graph has been removed and an `odometry` action graph has been added in its place. This effectively removed most TF publishers, only keeping one Raw TF publisher required for the ground truth localization transform (odom frame > base_link frame).

- New `joint_states` action graph is added, which publishes the movable joint states for Nova Carter. This will be read in by the `robot_state_publisher` and it will publish the relevant TFs accordingly.

- All hawk camera action graphs have been modified to include a new static TF publisher to add a sub TF tree for the left and right camera frames from each camera mount frame. 

    .. note:: Each camera has its own static TF publisher for the following reason: Due to the camera calibration process, the spacing between left and right cameras can differ from device to device. Therefore, the (mount > left camera) and (mount > right camera) transforms are left out of the main URDF and are up to the device driver to provide instead. In this case Isaac Sim acts as the hardware device driver and publishes these static transforms accordingly.       


#. Install the **nova_carter_description** package. Follow the steps :ref:`isaac_sim_app_tutorial_ros2_nav_nova_carter_description` section.

#. In |isaac-sim_short|, open the navigation scene. Go to **Window > Examples > Robotics Examples**, and then click on the **Robotics Examples** tab and expand the sections on the left hand side and open the example: **ROS2 > Navigation > Nova Carter Joint States** to load the warehouse scenario with the :ref:`Nova Carter robot<isaac_nova_carter>` asset with joint state publishers.

#. Click on **Play** to begin simulation.

#. In a new terminal, run the ROS2 launch file to start publishing the robot description using the `robot_state_publisher` and the official Nova Carter URDF.

    .. code-block:: bash

        ros2 launch carter_navigation nova_carter_description_isaac_sim.launch.py

#. In a new terminal, run the ROS2 launch file to begin Nav2.

    .. code-block:: bash

        ros2 launch carter_navigation carter_navigation.launch.py

#. Notice the robot model is automatically loaded in the scene in Rviz and performing the same as non-joint state example.

.. raw:: html

    <div style="width: 100%;display: inline-block;position: relative;">
        <div id="dummy" style="margin-top: 56%;"></div>
        <div align="center">
        <div id="kaltura_player_996204565" style="position:absolute;top:0;left:0;left: 0;right: 0;bottom:0;border:solid thin black;"></div>
        <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/46302491"></script>
        <script type="text/javascript">
            try {
            var kalturaPlayer = KalturaPlayer.setup({
            targetId: "kaltura_player_996204565",
            provider:
            { partnerId: 2935771, uiConfId: 46302491 }
            });
            kalturaPlayer.loadMedia(
            {entryId: '1_9hweqg9j'}
            );
            } catch (e)
            { console.error(e.message) }
        </script>
        </div>
    </div>


.. _isaac_sim_app_tutorial_ros2_nav_nova_carter_description:

Installing the Nova Carter Description Package
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. note:: This section is only supported in Linux for ROS 2 **Humble**.

The Nova Carter description package contains the robot geometry including meshes that can be used to visualize the robot in RViz2. Follow the steps below to configure this description package for |isaac-sim_short| workflows:

#. Open a new ROS-sourced terminal. Set up the locale: 

    .. code-block:: bash

        locale  # check for UTF-8

        sudo apt update && sudo apt install locales
        sudo locale-gen en_US en_US.UTF-8
        sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
        export LANG=en_US.UTF-8

        locale  # verify settings

#. Install the required dependencies.

    .. code-block:: bash

        sudo apt update && sudo apt install gnupg wget
        sudo apt install software-properties-common
        sudo add-apt-repository universe

#. Register NVIDIA's GPG Key and Repository.

    .. tab-set::

        .. tab-item:: US CDN 
        
            .. code-block:: bash

                wget -qO - https://isaac.download.nvidia.com/isaac-ros/repos.key | sudo apt-key add -
                grep -qxF "deb https://isaac.download.nvidia.com/isaac-ros/release-3 $(lsb_release -cs) release-3.0" /etc/apt/sources.list || \
                echo "deb https://isaac.download.nvidia.com/isaac-ros/release-3 $(lsb_release -cs) release-3.0" | sudo tee -a /etc/apt/sources.list
                sudo apt-get update
    
        .. tab-item:: China CDN 

            .. code-block:: bash

                wget -qO - https://isaac.download.nvidia.cn/isaac-ros/repos.key | sudo apt-key add -
                grep -qxF "deb https://isaac.download.nvidia.cn/isaac-ros/release-3 $(lsb_release -cs) release-3.0" /etc/apt/sources.list || \
                echo "deb https://isaac.download.nvidia.cn/isaac-ros/release-3 $(lsb_release -cs) release-3.0" | sudo tee -a /etc/apt/sources.list
                sudo apt-get update

#. Install the **nova_carter_description** package.

    .. code-block:: bash
        
        sudo apt install ros-humble-nova-carter-description


.. _isaac_sim_app_tutorial_ros2_nav_iw_hub:

Nav2 with iw.hub in Warehouse
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. TODO: Add iw.hub robot assets page

#. Go to **Window > Examples > Robotics Examples**, and then click on the **Robotics Examples** tab and expand the sections on the left hand side and open the example: **ROS2 > Navigation > iw_hub** to load the warehouse scenario with the :ref:`iw.hub robot<isaac_assets_robots>`.

#. Click on **Play** to begin simulation.

#. In a new terminal, run the ROS2 launch file to begin Nav2. The map for the different warehouse environment has already been generated.

    .. code-block:: bash

        ros2 launch iw_hub_navigation iw_hub_navigation.launch.py

    RViz2 opens and begins loading the occupancy map. If a map does not appear, repeat the previous step.


#. Because the position of the robot is defined in the parameter file ``iw_hub_navigation_params.yaml``, verify that the robot is already properly localized. If required, the **2D Pose Estimate** button can be used to re-set the position of the robot.

#. Click on the **Navigation2 Goal** button and then click and drag at the desired location point in the map. Nav2 now generates a trajectory and the robot starts moving towards its destination. Verify that the robot avoids dynamic obstacles, such as the pallets that are in scene but are not included in the initial map.

.. raw:: html

    <div style="width: 100%;display: inline-block;position: relative;">
        <div id="dummy" style="margin-top: 56%;">
        </div>
        <div align="center">
        <div id="kaltura_player_867327211" style="position:absolute;top:0;left:0;left: 0;right: 0;bottom:0;border:solid thin black;"></div>
        <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/53712482"></script>
        <script type="text/javascript">
            try {
            var kalturaPlayer = KalturaPlayer.setup({
            targetId: "kaltura_player_867327211",
            provider:
            { partnerId: 2935771, uiConfId: 53712482 }
            });
            kalturaPlayer.loadMedia(
            {entryId: '1_9x45hpz0'}
            );
            } catch (e)
            { console.error(e.message) }
        </script>
        </div>
    </div>


.. _isaac_sim_app_tutorial_ros2_nav_goals:

Sending Goals Programmatically
===============================

.. note:: The ``isaac_ros_navigation_goal`` package is fully supported on Linux. On Windows, running this package might produce errors.

The ``isaac_ros_navigation_goal`` ROS2 package can be used to set goal poses for the robot using a Python node. It is able to randomly generate and send goal poses to Nav2. It is also able to send user-defined goal poses if needed.


#. Make any changes to the parameters defined in the launch file found under ``isaac_ros_navigation_goal/launch`` as required. Make sure to re-build and source the package and workspace after modifying its contents.

    The parameters are described below:

    - **goal_generator_type**: Type of the goal generator. Use ``RandomGoalGenerator`` to randomly generate goals or use ``GoalReader`` for sending user-defined goals in a specific order.
    - **map_yaml_path**: The path to the occupancy map parameters YAML file. An example file is present at ``isaac_ros_navigation_goal/assets/carter_warehouse_navigation.yaml``. The map image is being used to identify the obstacles in the vicinity of a generated pose. **Required** if the goal generator type is set as ``RandomGoalGenerator``.
    - **iteration_count**: Number of times goal is to be set.
    - **action_server_name**: Name of the action server.
    - **obstacle_search_distance_in_meters**: Distance in meters in which a generated pose is free from obstacles of any kind.
    - **goal_text_file_path**: The path to the text file which contains user-defined static goals. Each line in the file has a single goal pose in the following format: ``pose.x pose.y orientation.x orientation.y orientation.z orientation.w``. A sample file is present at: ``isaac_ros_navigation_goal/assets/goals.txt``. **Required** if goal generator type is set as ``GoalReader``.
    - **initial_pose**: If initial_pose is set, it will be published to the `/initialpose` topic and goal poses will be sent to action server after that. Format is ``[pose.x, pose.y, pose.z, orientation.x, orientation.y, orientation.z, orientation.w]``.

#. Go to **Window > Examples > Robotics Examples**, and then click on the **Robotics Examples** tab and expand the sections on the left hand side and open the example: **ROS2 > Navigation > Nova Carter** to load the warehouse scenario.

#. Click on **Play** to begin simulation.

#. In a new terminal, run the ROS2 launch file to begin Nav2.

    .. code-block:: bash

        ros2 launch carter_navigation carter_navigation.launch.py

    RViz2 opens and begins loading the occupancy map. If a map does not appear, repeat the previous step.


#. Run the ``isaac_ros_navigation_goal`` launch file, to start sending goals automatically:

    .. code-block:: bash

        ros2 launch isaac_ros_navigation_goal isaac_ros_navigation_goal.launch.py


.. note:: After any of the following conditions are met, the package stops processing (setting goals):

    1. Number of goals published till now >= iteration_count.
    2. If the ``GoalReader`` parameter is used and if all the goals from the config file are published.
    3. A goal is rejected by the action server.
    4. In rare cases, a very dense map can cause ``RandomGoalGenerator`` to generate invalid poses. The package will stop processing if the number of invalid poses generated by ``RandomGoalGenerator`` exceeds the maximum number of iteration.


To automatically launch Isaac Sim and Nav2, while programmatically sending navigation goals from a single launch process, refer to :ref:`isaac_sim_app_tutorial_ros2_nav_goals_launch`.

To learn more about programmatically sending navigation goals to multiple robots simultaneously, refer to :ref:`isaac_sim_app_tutorial_ros2_multi_nav_goals`.

Sending Goals Using ActionGraph
================================

.. important:: Make sure `Nav2 <https://docs.nav2.org/getting_started/index.html#installation>`_ is installed and source your ROS2 installation from the terminal before running |isaac-sim_short|. Currently, the following section will not work with internal libraries.

#. Go to **Window > Examples > Robotics Examples** to open **Robotics Examples** tab.

#. Go to **Robotics Examples > ROS2 > Navigation > Nova Carter** and click on **Load Sample Scene** button to load the warehouse scenario with the :ref:`Nova Carter robot<isaac_nova_carter>`.

#. Go to **Robotics Examples > ROS2 > Navigation > Add Waypoint Follower** to open the waypoint follower parameter window.

#. Make changes to the waypoint follower parameters as required.

    .. figure:: /images/isim_4.5_ros_tut_gui_waypoint_follower_parameters.png
            :align: center
            :width: 600
            :alt: Occupancy Map Properties UI Window

    The parameters are described below:

    - **Graph Path**: Specify the path within the stage.
    - **Frame ID**: Specify the reference frame for navigation tasks.
    - **Navigation Modes**:
        #.	Waypoint Mode: Creates a single waypoint to send as a navigation goal. The robot will navigate towards this waypoint.
        #.	Patrolling Mode: Creates multiple waypoints (between 2 to 50 inclusive) for continuous patrolling. The robot will navigate between these predefined waypoints continuously.
    - **Waypoint Count**: Number of waypoints to generate for **Patrolling**.

#. Click on **Load Waypoint Follower ActionGraph** to create waypoints and add the action graph at **Graph Path** in stage pane.

#. Click on **Play** to begin simulation.

#. In a new terminal, run the ROS2 launch file to begin Nav2.

    .. code-block:: bash

        ros2 launch carter_navigation carter_navigation.launch.py

    RViz2 opens and begins loading the occupancy map. If a map does not appear, repeat the previous step.


#. Because the position of the robot is defined in the parameter file ``carter_navigation_params.yaml``, verify that the robot is properly localized. If required, the **2D Pose Estimate** button can be used to re-set the position of the robot.

#. Running navigation modes:

        #. **Waypoint**:
            #. Adjust the waypoint (/World/Waypoints/waypoint_1) in xy plane of the scene to set the desired goal location.
            #. Open the ROS_Nav2_Waypoint_Follower graph from the stage and click on **Send Impulse** in the OnImpulseEvent node.
            #. Verify that the robot starts navigating towards the specified goal.
            #. Repeat these steps after each goal is completed to set new waypoint.

        #. **Patrolling**:
            #. Adjust the waypoints (/World/Waypoints/waypoint_n) in xy plane of the scene to define the patrol path.
            #. Open the ROS_Nav2_Waypoint_Follower graph from the stage and click on **Send Impulse** in the OnImpulseEvent node.
            #. Verify that the robot starts patrolling along the set waypoints.

.. raw:: html

    <div style="width: 100%;display: inline-block;position: relative;">
        <div id="dummy" style="margin-top: 56%;">
        </div>
        <div align="center">
        <div id="kaltura_player_568651818" style="position:absolute;top:0;left:0;left: 0;right: 0;bottom:0;border:solid thin black;"></div>
        <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/53712482"></script>
        <script type="text/javascript">
            try {
                var kalturaPlayer = KalturaPlayer.setup({
                targetId: "kaltura_player_568651818",
                provider: {
                    partnerId: 2935771,
                    uiConfId: 53712482
                }
                });
                kalturaPlayer.loadMedia({entryId: '1_68lcjbar'});
            } catch (e) {
                console.error(e.message)
            }
        </script>
        </div>
    </div>


.. _isaac_sim_app_tutorial_ros2_waypoint_follower:

.. note::

    * This tutorial uses the AMCL localizer and the action graph is fully supported for this localizer.

    * If you notice errors as shown below after deleting the graph, you can disregard them because they are harmless. To prevent these logs you can click the "reload node" button to clean up the script nodes before deleting the graph.

        .. code-block::

            2024-12-03 13:55:27 [4,715,030ms] [Error] [omni.graph] Error executing python callback omni.graph.scriptnode.ScriptNode.release_instance
            2024-12-03 13:55:27 [4,715,030ms] [Error] [omni.graph] Error executing python callback omni.graph.scriptnode.ScriptNode.release


Summary
========

In this tutorial, you covered:

#. Occupancy map.
#. Running Isaac Sim with Nav2.
#. Running the Isaac ROS2 Navigation Goal package to send nav goals programmatically.
#. Running Waypoint Follower ActionGraph to send navigation goals.

Next Steps
^^^^^^^^^^^^^^^^^^^^^^

Continue on to the next tutorial in our ROS2 Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_multi_navigation` to move multiple navigating robots with ROS2.


Further Learning
^^^^^^^^^^^^^^^^^^^^^^

- To learn more about Nav2, refer to the `project website <https://nav2.org/>`_.
- More about :ref:`ext_isaacsim_asset_generator_occupancy_map`.
- Explore the inner workings of RTX Lidar sensors by learning :ref:`isaacsim_sensors_rtx_lidar_how_they_work`, and how to get :ref:`rtx_sensor_annotator_descriptions`.
