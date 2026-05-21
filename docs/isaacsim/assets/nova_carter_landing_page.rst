
..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_nova_carter:

==================
Nova Carter
==================

Powered by the `Nova Orin™ <https://developer.nvidia.com/isaac/nova-orin>`_  sensor and compute architecture, Nova Carter is a complete robotics development platform that accelerates the development and deployment of next-generation Autonomous Mobile Robots (AMRs).

Nova Carter is being used as a reference platform for both Isaac AMR and Isaac ROS software, enabling real-world and simulation-based development. Nova Carter robots may be purchased from `Segway Robotics <https://robotics.segway.com/nova-carter>`_.

The robot features the full Nova Orin sensor set, including four Leopard Imaging Hawk stereo cameras, four Leopard Imaging Owl fisheye cameras, IMUs, two 2D RPLidars, and one XT-32 3D Lidar. The robot digital twins with the cameras, Lidars, and IMU sensors are simulated in |isaac-sim| and connected to the ROS 2 bridge for different robotics applications.

Assets
#########

Nova Carter
------------

The Nova Carter assets can be found on nucleus after |isaac-sim| is installed, the Nova Carter assets are in the  ``/Isaac/Robots/NVIDIA/NovaCarter`` folder, the ROS 2 assets are in the ``/Isaac/Samples`` folder, and the sample environments are in the ``/Isaac/Sampls/ROS2/Scenarios/`` folder.

.. figure:: /images/usd_assets_robots/isim_4.5_full_ref_viewport_Isaac_Robots_Carter_nova_carter.usd.png
    :align: center
    :alt: Nova Carter
    :width: 100%

    Nova Carter

- ``/Isaac/Robots/NVIDIA/NovaCarter/nova_carter.usd``, the Nova Carter robot with no sensors attached.
- ``/Isaac/Samples/ROS2/Robots/Nova_Carter_ROS.usd``, the Nova Carter robot with sensors attached and ROS 2 action graph enabled. This asset has been tested and verified before release.

Furthermore the nova_carter.usd asset in |isaac-sim| also contains prebuilt variants for different simulation and animation applications.

- Configuration:
    - Base: The Nova Carter robot all individual parts assembled
    - Fully Merged: The Nova Carter robot with all fixed parts merged into a single mesh for faster simulation
    - No_Internals: The Nova Carter robot with no internal components like circuit board, battery.
    - Skirt_only: The Nova Carter robot with only the skirt and wheels, useful for simulating the robot base without the upper structure or to mount custom parts on top.
- Physics:
    - No_Physics: The Nova Carter robot with no physics, useful for visual only applications like animation
    - Physics_Base: The Nova Carter robot with physics enabled
- Sensors
    - None: The Nova Carter robot with no sensors attached.
    - All_Sensors: The Nova Carter robot with all sensors attached.


.. dropdown:: Frames and Topic names
    :animate: fade-in
    :icon: info

    .. csv-table:: Nova Carter Frame Names and Topic Names
        :file: /csv/nova_carter_frame_topics.csv
        :header-rows: 1


Nova Dev Kit
--------------------

The Nova Dev Kit is a development platform consist of 3 hawk stereo cameras and 3 owl fisheye cameras.

.. figure:: /images/usd_assets_robots/isim_4.5_full_ref_viewport_Isaac_Robots_Carter_nova_dev_kit_sensors.usd.png
    :align: center
    :alt: Nova Dev Kit
    :width: 100%

    Nova Dev Kit

- ``/Isaac/Robots/NVIDIA/NovaCarterDevKit/nova_dev_kit_sensors.usd``, the Nova Dev Kit with sensors attached.
- ``/Isaac/Samples/ROS2/Robots/Nova_Dev_Kit_ROS.usd``, the Nova Dev Kit with sensors attached and ROS 2 action graph enabled.
- ``/Isaac/Samples/ROS2/Robots/Nova_Dev_Kit_On_Robot_ROS.usd``, the Nova Dev Kit ROS model attached to a Nova Carter base. This asset has been tested and verified before release.

.. dropdown:: Frames and Topic names
    :animate: fade-in
    :icon: info

    .. csv-table:: Nova Dev Kit Frame Names and Topic Names
        :file: /csv/nova_dev_kit_frame_topics.csv
        :header-rows: 1


Sensors
#############


Hawk Stereo Camera
-----------------------

The Hawk stereo camera features two RGB camera sensors and a 6 axis IMU, and it is located at ``Isaac/Sensors/LeopardImaging/Hawk/hawk_v1.1_nominal.usd``
The detailed specs can be found :ref:`here<hawk_stereo_camera>`.


.. dropdown:: Note: The front hawk is enabled by default for `Nova_Carter_ROS.usd`, additional hawk cameras can be enabled as needed, with increase load on computation.
    :animate: fade-in
    :icon: info

    - To enable to other hawk sensors, go to *Window > Graph Editors > ActionGraph*
    - Click *Edit Action Graph* and select the action graph for the sensor to enable. (For example, */nova_carter_ros2_sensors/back_hawk*)
    - Select the *Isaac Create Render Product Node* for the camera (there is one for the left camera, and one for the right camera), click *enabled*

    .. image:: /images/landing_page_carter_enable_sensor.gif
        :align: center

RPLidar
-----------

RP Lidar is a RTX based 2D lidar, that can be enabled by default and can be created by clicking *Create > Isaac > Sensors > RTX Lidar > SLAMTEC > RPLIDAR S2E*

.. Note:: The RP Lidars are disabled by default, to enable them, follow the dropdown above and check ``enabled``


XT-32
------------------

XT-32 is a RTX based 3D lidar, that can be enabled by default and can be created by clicking *Create > Isaac > Sensors > RTX Lidar > HESAI > PandarXT-32 10hz*

.. Note:: The XT-32 are enabled by default, to disable it, follow the dropdown above and uncheck ``enabled``


Getting Started
########################

|isaac-sim| has provided several ROS 2 samples with the Nova Carter robot for control and navigation.

ROS 2 Sample Scene
--------------------
First activate **Windows** > **Examples** > **Robotics Examples** which will open the ``Robotics Examples`` tab.
The sample scene can be loaded after :ref:`enabling the ROS 2 Bridge Extension<isaac_sim_app_enable_ros>` by clicking *Robotics Examples > ROS2 > Isaac ROS > Sample Scene*.

This scene showcases a Nova Carter inside a small warehouse, with all Lidars and front hawk camera running from the robot frame. Please follow  :ref:`Multiple Sensors in RViz2 section <isaac_sim_app_tutorial_ros2_tf_multiple_sensors>`
for visualizing the sensors and install ``teleop-twist-keyboard`` by following the :ref:`Driving Turtlebot Tutorial<isaac_sim_app_tutorial_ros2_drive_turtlebot>`.

.. raw:: html

    <div style="width: 100%;display: inline-block;position: relative;">
        <div id="dummy" style="margin-top: 56%;">
        </div>
        <div align="center">
        <div id="kaltura_player_784470725" style="position:absolute;top:0;left:0;left: 0;right: 0;bottom:0;border:solid thin black;"></div>
        <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/53479362"></script>
        <script type="text/javascript">
            try {
            var kalturaPlayer = KalturaPlayer.setup({
            targetId: "kaltura_player_784470725",
            playback:
            { autoplay: false, muted: true, volume: 0, loop: false, allowMutedAutoPlay: true },
            provider:
            { partnerId: 2935771, uiConfId: 53479362 }
            });
            kalturaPlayer.loadMedia(
            {entryId: '1_itr63yle'}
            );
            } catch (e)
            { console.error(e.message) }
        </script>
        </div>
    </div>

ROS 2 Navigation Scene
------------------------

The navigation scene can be loaded after :ref:`enabling the ROS 2 Bridge Extension<isaac_sim_app_enable_ros>` by clicking *Robotics Examples > ROS2 > Navigation > Nova Carter*.

Please follow :ref:`ROS 2 Navigation<isaac_sim_app_tutorial_ros2_navigation>` tutorial for usage.

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


Other Resources
################

- `Nova Orin <https://developer.nvidia.com/isaac/nova-orin>`_
- `Isaac AMR <https://docs.nvidia.com/isaac/doc/index.html>`_
- `Segway Nova Carter <https://robotics.segway.com/nova-carter>`_
- :ref:`Isaac Sim Overview<isaac_sim_app_overview>`
- :ref:`ROS 2 Tutorials<isaac_sim_app_tutorial_ros2_turtlebot>`
- :ref:`Hawk Stereo Camera<hawk_stereo_camera>`