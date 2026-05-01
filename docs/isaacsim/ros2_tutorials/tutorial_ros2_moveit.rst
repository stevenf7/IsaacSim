
..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_ros2_moveit:

=================================
MoveIt 2
=================================

.. attention:: The MoveIt 2 tutorial may fail intermittently on **ROS 2 Humble** due to performance limitations. If you experience failures or timeouts during planning or execution, consider switching to **ROS 2 Jazzy**, which does not exhibit this issue.

Learning Objectives
=======================

Run a manipulation scene in Isaac Sim with MoveIt 2.


Getting Started
===========================



    
**Prerequisite**

- This tutorial requires ``isaac_moveit`` and ROS 2 packages, which are provided as part of your |isaac-sim| download. These ROS 2 packages are located inside the appropriate ``humble_ws`` or ``jazzy_ws``. They contain the required launch file and moveit configs. Complete :ref:`isaac_sim_app_install_ros` to ensure the ROS 2 workspace environment is set up correctly.

- If using multiple systems, set the ``FASTRTPS_DEFAULT_PROFILES_FILE`` environment variable as per instructions in :ref:`isaac_sim_app_install_ros` before launching |isaac-sim_short|, as well as any terminal where ROS messages will be sent or received, and ROS2 Extension is enabled.

- Completed :ref:`isaac_sim_app_tutorial_ros2_manipulation`.


Running MoveIt 2
======================================

#. Load the environment by going to **Window > Examples > Robotics Examples**, and then click on the **Robotics Examples** tab and expand the sections on the left hand side and open the example: **ROS2 > MoveIt > Franka MoveIt**. Then hit `Play` to start simulation.

#. Run the launch file to start MoveIt 2. 

    
    .. code-block:: bash

        ros2 launch isaac_moveit isaac_moveit.launch.py 

#. After Rviz is launched, you can start playing with the planner. Under ``Planning Group``, the ``hand`` option should be selected. Under ``Goal State``, select ``open``.

    .. Note:: 
        On certain machines, selecting **close** under **Goal State** for **hand** planning group will cause the execution to fail/abort, and execute the action later with a delay or on the next execution.

#. Under **Commands**, click **Plan**. The planned movement of the hand will now be visualized.

#. Click **Execute**. The hand will start moving as planned earlier.

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
                {entryId: '1_agsykzi5'}
                );
                } catch (e)
                { console.error(e.message) }
            </script>
            </div>
        </div>

#. To plan the movement for the arm, under ``Planning Group``, select ``panda_arm``.
   Use the displayed arrows and rotation disks to set a goal position for the robot.
   Alternatively you can choose to select ``<random_valid>`` under ``Goal State``.

#. Under **Commands**, click on **Plan** followed by **Execute** to visualize the planned motion of the arm and then move it.

    .. raw:: html

        <div style="width: 100%;display: inline-block;position: relative;">
            <div id="dummy" style="margin-top: 56%;">
            </div>
            <div align="center">
            <div id="kaltura_player_3" style="position:absolute;top:0;left:0;left: 0;right: 0;bottom:0;border:solid thin black;"></div>
            <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/46302491"></script>
            <script type="text/javascript">
                try {
                var kalturaPlayer = KalturaPlayer.setup({
                targetId: "kaltura_player_3",
                provider:
                { partnerId: 2935771, uiConfId: 46302491 }
                });
                kalturaPlayer.loadMedia(
                {entryId: '1_9peqniqz'}
                );
                } catch (e)
                { console.error(e.message) }
            </script>
            </div>
        </div>


Troubleshooting
====================

.. note:: On **ROS 2 Humble**, the tutorial may fail intermittently during planning or execution due to performance issues. This is a known limitation with no complete fix available at this time. Switching to **ROS 2 Jazzy** is recommended if you encounter repeated failures.

If your Rviz window is showing a black screen for where the robot should be, you can  update your mesa driver. Run the following commands in a new terminal.

.. code-block:: bash

    # update mesa driver
    sudo apt update
    sudo apt install -y software-properties-common 
    sudo add-apt-repository ppa:kisak/kisak-mesa
    sudo apt install -y mesa-utils
    sudo apt -y upgrade


Summary
========

Tips for running MoveIt2's |isaac-sim_short| tutorial.


Next Steps
^^^^^^^^^^^^^^^^^^^^^^

Continue on to the next tutorial in our ROS2 Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_generic_publisher_subscriber` to learn how to publish and subscribe to and from any ROS 2 topic.


Further Learning
^^^^^^^^^^^^^^^^^^^^^^

- Learn more about `MoveIt 2 <https://moveit.picknik.ai/humble/index.html>`_.
