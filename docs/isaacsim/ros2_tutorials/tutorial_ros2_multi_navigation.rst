

..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_ros2_multi_navigation:

==================================
Multiple Robot ROS2 Navigation
==================================

**Support Limitations**

* Multiple Robot ROS2 Navigation with |isaac-sim_short| is fully supported on Linux and Windows with Pixi-based installation. On Windows (WSL), Multiple Robot ROS2 Navigation with |isaac-sim_short| could potentially produce errors.



Learning Objectives
=======================

In this ROS2 sample, we are demonstrating |isaac-sim| integrated with the ROS2 Nav2 stack to perform simultaneous multiple robot navigation.


Getting Started
===========================




**Prerequisite**

- Completed :ref:`isaac_sim_app_tutorial_ros2_navigation` for ROS2 Nav2 with a single robot. So that

    - ROS2 and Nav2 are installed.
    - ROS2 bridge is enabled.
    - ``ros2_ws`` is built and sourced (see :ref:`isaac_sim_ros_workspace_setup`) so that ``carter_navigation`` and ``isaac_ros_navigation_goal`` are inside your workspace.

.. note:: In Windows 10 or 11, depending on your machine's configuration, RViz2 might not open properly. 
    
Occupancy Map
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We generate the map of both the Hospital and Office environments using the :ref:`Occupancy Map Generator extension<ext_isaacsim_asset_generator_occupancy_map>` within |isaac-sim|.

Follow the steps depending on what environment you would like to use.


.. tab-set::

    .. tab-item:: Hospital Environment
        :sync: hospital

        1. Go to the Isaac Sim Content browser and click **Isaac Sim>Environments>Hospital**. Search for hospital and drag and drop the **hospital.usd** asset into the scene. Ensure that it is placed at the origin by zero'ing out all the *Translate* components in the Transform Property.


        2. At the upper left corner of the viewport, click on **Perspective**. Select **Top** from the dropdown menu. Select the `/Hospital` prim and press **F** to zoom to selection. Adjust the camera view as needed.

        3. Go to **Tools > Robotics > Occupancy Map**.

        4. In the Occupancy Map extension, ensure the Origin is set to ``X: 0.0, Y: 0.0, Z: 0.0``. For the lower bound, set ``Z: 0.1``. For the Upper Bound, set ``Z: 0.62``. Keep in mind, the upper bound Z distance has been set to 0.62 meters to match the vertical distance of the Lidar onboard Carter with respect to the ground.


        5. Select the `Hospital` prim in the stage. In the Occupancy Map extension, click on **BOUND SELECTION**. The bounds of the occupancy map should be updated to incorporate the selected `Hospital` prim.

            The map parameters should now look similar to the following image:

            .. figure:: /images/isaac_sample_ros_multiple_robot_nav_1.png
                :align: center
                :width: 600
                :alt: Occupancy Map Properties UI Window for the Hospital Environment


            A perimeter will be generated and it should resemble this image (Top View):

            .. figure:: /images/isim_5.0_ros_tut_viewport_ros_multiple_robot_nav_occupancy_map.png
                :align: center
                :width: 600
                :alt: Top View of Hospital with Occupancy Map

    .. tab-item:: Office Environment
        :sync: office

        1. Go to the Isaac Sim Content browser **Isaac Sim>Environments>Office**. Search for office and drag and drop the **office.usd** asset into the scene. Ensure that it is placed at the origin by zero'ing out all the *Translate* components in the Transform Property.

        2. At the upper left corner of the viewport, click on **Perspective**. Select **Top** from the dropdown menu. Select the `/Office` prim and press **F** to zoom to selection. Adjust the camera view as needed.

        3. Go to **Tools > Robotics > Occupancy Map**. In the Occupancy Map extension, set the map parameters to be similar to the following image:

            .. figure:: /images/isaac_sample_ros_multiple_robot_nav_3.png
                :align: center
                :width: 600
                :alt: Occupancy Map Properties UI Window for Office Environment

            Keep in mind, the upper bound Z distance has been set to 0.62 meters to match the vertical distance of the Lidar onboard Nova Carter with respect to the ground.

            A perimeter will be generated, verify that it resembles this image (Top View):

            .. figure:: /images/isaac_sample_ros_multiple_robot_nav_4.jpg
                :align: center
                :width: 600
                :alt: Top View of Office with Occupancy Map


1. After the setup for either environment is complete, click on **CALCULATE** followed by **VISUALIZE IMAGE**. A Visualization popup will appear.

2. For `Rotate Image`, select 180 degrees and for Coordinate Type select **ROS Occupancy Map Parameters File (YAML)**. Click **RE-GENERATE IMAGE**. Occupancy map parameters formatted to YAML will appear in the field below. Change the image name to your preference. Copy the full text.

3. Click **Save YAML** and save the YAML file to the `maps` directory, which is located in the sample ``carter_navigation`` ROS2 package (``carter_navigation/maps/carter_hospital_navigation.yaml``).

4. Back in the visualization tab in |isaac-sim|, click **Save Image**. Set the same image name as in the map parameters and choose to save in the same directory as the map parameters file.

    - The final saved image of the Hospital environment will look like the following:

    .. figure:: /images/isaac_sample_ros_nav_hospital_map.png
        :align: center
        :width: 500
        :alt: Sample Occupancy Map generated from hospital stage

    - The final saved image of the Office environment will look like the following:

    .. figure:: /images/isaac_sample_ros_nav_office_map.png
        :align: center
        :width: 500
        :alt: Sample Occupancy Map generated from office stage


An occupancy map is now ready to be used with Multiple Robot ROS2 Navigation.

.. _isaac_sim_app_tutorial_ros2_multi_nav_instructions:

Multiple Robot ROS2 Navigation Setup
======================================

Open hospital scene by going to **Window > Examples > Robotics Examples**, and then click on the **Robotics Examples** tab and expand the sections on the left hand side and open the example: **ROS2 > Navigation > Multiple Robots > Hospital Scene**.

For details on the ROS2 Navigation setup refer to the :ref:`ROS2 Navigation Sample<isaac_sim_app_tutorial_ros2_navigation>`.

For operating multiple robots in the same environment, namespaces are utilized.
This modifies the rostopic and rosnode names for different ROS2 packages, allowing for multiple instances of the same ROS2 node to run simultaneously.

To publish and receive ROS2 messages under namespaces, the ``node_namespace`` |omnigraph_short| node found in each of the action graphs under ``Nova_Carter_ROS_X`` has been set to the corresponding robot names.
The ``multiple_robot_carter_navigation_hospital.launch.py`` and ``multiple_robot_carter_navigation_office.launch.py`` launch files found in the sample ``carter_navigation`` ROS2 package are also configured with the same robot namespaces.


Running Multiple Robot ROS2 Navigation
========================================

.. note:: On multi-GPU systems running Windows, loading and playing this scene may currently result in a fatal application crash. This is a known issue and will be addressed in a future release.

#. Load scenario:

	- For the hospital environment, go to **Window > Examples > Robotics Examples**, and then click on the **Robotics Examples** tab and expand the sections on the left hand side and open the example: **ROS2 > Navigation > Multiple Robots > Hospital Scene**.
	- For the Office scenario, go to **Window > Examples > Robotics Examples**, and then click on the **Robotics Examples** tab and expand the sections on the left hand side and open the example: **ROS2 > Navigation > Multiple Robots > Office Scene**.


#. Click on **Play** to begin simulation.

#. In a new terminal, run the specific ROS2 launch file to begin Multiple Robot Navigation with the desired environment.


    .. tab-set::

        .. tab-item:: Hospital Environment
            :sync: hospital

            .. code-block:: bash

                ros2 launch carter_navigation multiple_robot_carter_navigation_hospital.launch.py

        .. tab-item:: Office Environment
            :sync: office

            .. code-block:: bash

                ros2 launch carter_navigation multiple_robot_carter_navigation_office.launch.py


    Three RViz2 windows will be launched. This process can take a few moments to startup.

#. In each RViz2 window, click on the **Map** located in the **Displays** panel to observe the **Topic** name and take note of the robot namespace corresponding to the RViz2 window.

#. Since the positions of each robot are defined in parameter files in ``carter_navigation/params/hospital/`` or ``carter_navigation/params/office/``, the robots should already be properly localized.

#. In the ``/carter1`` namespaced RViz2 window, click on the **2D Nav Goal** button and then click and drag at the desired location point in the map. The ROS2 Navigation stack will now generate a trajectory and the ``/carter1`` robot will start moving towards its destination!

#. Repeat the previous step for the ``/carter2`` and ``/carter3`` robots.

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
            {entryId: '1_j2707m1f'}
            );
            } catch (e)
            { console.error(e.message) }
        </script>
        </div>
    </div>

.. note:: The ROS2 Image publisher pipelines are disabled by default to improve performance. To start publishing images, open the `_hawk` action graphs found under each of the `Nova_Carter_ROS` prims and enable the `_camera_render_product` nodes. The ROS Camera publisher nodes, which are downstream of the render product nodes, must be enabled by default and will only start publishing when the render product node is enabled. All sensors and images in Nova Carter are being published with `Sensor Data QoS <https://docs.ros.org/en/rolling/Concepts/Intermediate/About-Quality-of-Service-Settings.html#qos-profiles>`_. If you wish to visualize the images in RViz2, expand the image tab, navigate to **Topic > Reliability Policy** and change the policy to `Best Effort`.

.. _isaac_sim_app_tutorial_ros2_multi_nav_instructions_troubleshoot:

Troubleshooting
^^^^^^^^^^^^^^^^^^^

This tutorial exhibits high CPU usage. If you observe instances of robots colliding or experiencing localization issues, it's likely because the Nav2 stack is unable to properly synchronize with sensor data, resulting in missed controller commands.
To improve Nav2 performance:

1. Try enabling the **Publish Full Scan** checkbox accessible through the `publish_front_3d_lidar_scan` |omnigraph_short| node found in the `ros_lidars` action graph found under each ``Nova_Carter_ROS_X`` robot.

2. If the previous step still results in issues, also try running Isaac Sim from the terminal using the following command:

    .. code-block:: bash

        ./isaac-sim.fabric.sh --reset-user


    .. important:: The above command is experimental and not all functionality of Isaac Sim is supported there. However you might observe better overall performance.


Running in Python Directly
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Alternatively, to load this sample environment from Python directly, follow the steps outlined :ref:`here<isaac_sim_app_tutorial_ros2_python_multi_navigation>`.

.. _isaac_sim_app_tutorial_ros2_multi_nav_goals:

Sending Goals Programmatically for Multiple Robots
====================================================

.. note:: The ``isaac_ros_navigation_goal`` package is fully supported on Linux. On Windows, running this package could potentially produce errors.
    
The ``isaac_ros_navigation_goal`` ROS2 package can be used to set goal poses for multiple robots simultaneously. Refer to :ref:`isaac_sim_app_tutorial_ros2_nav_goals` to learn about the configurations and parameters of this package.

To send navigation goals to multiple robots simultaneously, setting up node namespaces are required. In a Python launch file, one way to setup namespaces is to provide a value for the ``namespace`` argument in each node object.

#. Set up the namespace "carter1" by defining the node using the ``namespace`` argument in ``isaac_ros_navigation_goal/launch/isaac_ros_navigation_goal.launch.py``. The node object should be defined as such:

    .. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_multi_navigation/set_up_the_namespace_carter1_by_defining_the_node_.py
        :language: python

    Remember to update the map YAML file path and the initial pose of `carter1` for either the hospital or office scenario.

    .. note:: If goal generator type is set to ``RandomGoalGenerator`` then a goal text file will not be used.

#. Copy and paste the `carter1` node declaration (shown in the previous step) twice and modify them for `carter2` and `carter3` namespaces (uniquely naming each node variable). The map YAML file path can be identical in all three nodes. Make sure to update the initial poses of `carter2` and `carter3`.

    .. note:: If goal generator type is set to ``GoalReader`` then a separate goal text file must be created for each namespaced node.

#. Finally at the end of the launch file, add the two newly created nodes in the launch description similar to following:

    .. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_multi_navigation/finally_at_the_end_of_the_launch_file_add_the_two_.py
        :language: python

#. To run the newly modified launch file, use the following command:

    .. important:: Before running the following command, ensure you have run steps 1 to 4 from :ref:`isaac_sim_app_tutorial_ros2_multi_nav_instructions`.

    .. code-block:: bash

        ros2 launch isaac_ros_navigation_goal isaac_ros_navigation_goal.launch.py


Summary
========

In this tutorial, we covered running multiple robots with ROS2 navigation stack.


Next Steps
^^^^^^^^^^^^^

Continue on to the next tutorial in our ROS2 Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_navigation_heightmap`.


Further Learning
^^^^^^^^^^^^^^^^^^^^^^

- To learn more about Nav2 refer to the website: `<https://nav2.org/>`_
- Standalone Python scripting version: :ref:`isaac_sim_app_tutorial_ros2_python_multi_navigation`. With this approach you have the ability to manually control the timestep and rate at which ROS components are published.
