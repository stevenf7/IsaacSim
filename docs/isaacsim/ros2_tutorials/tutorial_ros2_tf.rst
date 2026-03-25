

..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaac_sim_app_tutorial_ros2_tf:

======================================
ROS2 Transform Trees and Odometry
======================================

Learning Objectives
=======================

In this example, you:

- Add a transform publisher to publish the camera positions as part of the transform tree.
- Publish relative poses of objects.
- Publish the odometry of a robot.
- Use the menu shortcut to create transform and Odometry publishers.
- View the transform tree in Isaac Sim.

Getting Started
=============================



**Prerequisite**

- Completed the :ref:`isaac_sim_app_tutorial_ros2_turtlebot`, :ref:`isaac_sim_app_tutorial_ros2_camera`, and :ref:`isaac_sim_app_tutorial_ros2_rtx_lidar` tutorials.
- Completed :ref:`isaac_sim_app_install_ros` so that the necessary environment variables are set and sourced before launching |isaac-sim|, and ROS2 extension is enabled.

Transform Tree Publisher
===========================

Assuming you've already gone through the ROS 2 camera tutorial and have two cameras on stage already, let's add those cameras to a transform tree, so that you can track the cameras' positions in the global frame.

Transform Publisher
^^^^^^^^^^^^^^^^^^^^

#. In a new or existing **Action Graph** window, add a *ROS 2 Publish Transform Tree* node, and connect it up with *On Playback Tick*, and *Isaac Read Simulation Time*, like the image below.
#. In the **Property** tab for the *ROS 2 Publish Transform Tree* node, add both *Camera_1* and *Camera_2* to the *targetPrims* field.
#. Examine the transform tree in a ROS 2-enabled terminal: ``ros2 topic echo /tf``. Verify that both cameras are on the transform tree. Move the camera around inside the viewport and observe how the camera's pose changes.


.. figure:: /images/isim_4.5_ros_tut_gui_ros2_tf_graph.png
    :align: center
    :width: 800
    :alt: Turtlebot transform Graph


.. _isaac_sim_app_tutorial_ros2_tf_articulation_transforms:

Articulation Transforms
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To get the transforms of each linkage on an articulated robot, you can add the robot's articulation root to the **targetPrims** field in a **ROS2 Publish Transform Tree** node. All the linkages subsequent to the articulation root will be published automatically. 

.. important::

    If you find that the generated transform tree for an articulated robot chose the wrong link as the root link, use the following step to manually select the articulation root link.

    - Select the robot's root prim on the Stage Tree, in its **Raw USD Properties** tab, find the **Articulation Root** Section. Delete it by clicking on the **X** on the right upper corner inside the section.
    - Select the desired link on the Stage Tree, inside its **Raw USD Properties** Tab, click on the **+ADD** button, and add **Physics > Articulation Root**.
    - After you change the articulation root, save the file and reload.



Publish Relative Transforms
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
By default, the transforms are in reference to the world frame. You can check that the ``/base_link`` transform of the Turtlebot is published relative to the ``/World``. If you want to get the transforms relative to something else, such as a camera, make sure to indicate that in the *parentPrim* field. Add *Camera_1* in the *parentPrim* field, **Stop** and **Play** the simulation between property changes, and you can observe that the ``/base_link`` transform is now relative to *Camera_1*.


.. _isaac_sim_app_tutorial_ros2_tf_odometry:

Setting Up Odometry
=======================

To setup odometry for a robot, publish the odometry ROS message and its corresponding transforms.

#. Ensure the articulation root for your imported Turtlebot3 robot is ``/World/turtlebot3_burger``. Otherwise, remove the articulation root from ``/World/turtlebot3_burger/base_footprint`` and add it for ``/World/turtlebot3_burger``. Follow the steps in :ref:`isaac_sim_app_tutorial_ros2_tf_articulation_transforms` section to change the articulation root of the Turtlebot3 robot. 

    - (Optional Exercise) Add */World/turtlebot3_burger* (the default) to the **targetPrims** field in any **ROS2 Publish Transform Tree** node, and observe that the transforms of all the links of the robot, fixed or articulated, will be published on the ``/tf`` topic.  

#. To set up the odometry publisher, compose an Action Graph that matches the following image.

    .. figure:: /images/isim_5.0_ros_tut_gui_ros2_odometry_graph.png
        :align: center
        :width: 800



    - In the Property tab for the **Isaac Compute Odometry Node**: 

        - Add the Turtlebot prim (that is, ``/World/turtlebot3_burger``) to its **Chassis Prim** input field. This node calculates the position of the robot relative to its start location. Its output will be fed into both a publisher for the ``/odom`` ROS 2 topic, and a TF publisher that publishes the singular transform from ``/odom`` frame to ``/base_link`` frame.
    
    - In the Property tab for the **ROS2 Publish Raw Transform Tree** node:

        - Set the *childFrameId* input field to ``base_link``. 
        - Set the *parentFrameId* input field to ``odom``. This will now enable publishing `odom -> base_link` frames in the transform tree.

    - In the Property tab for the **ROS2 Publish Odometry** node:

        - Set the **chassisFrameId** input field to ``base_link``. 
        - Set the **odomFrameId** input field to ``odom``. This will now enable publishing `odom -> base_link` frames in the transform tree.

.. note::
    The **ROS2 Publish Odometry** node publishes full 3D velocity information. Both linear velocity and angular velocity are published with all three dimensions (x, y, and z), allowing for a more complete representation of the robot's motion state.

#. At this point we are publishing odometry data and our transform tree only consists of `odom -> base_link`. We would also like to add the relevant robot prims under `base_link` to the transform tree. To do this, add a **ROS2 Publish Transform Tree** node to the graph and attach the `Exec In`, `Context`, and `Timestamp` fields similarly to previous nodes above. 

    - In the Property tab for the **ROS2 Publish Transform Tree** node:

        - Set the *parentPrim* input field to the path to your base_link inside your Turtlebot Prim: ``/World/turtlebot3_burger/base_link``. 


        - Set the *targetPrims* input field to the following prims: 
            
            - ``/World/turtlebot3_burger/base_footprint``
            - ``/World/turtlebot3_burger/base_scan``
            - ``/World/turtlebot3_burger/caster_back_link``
            - ``/World/turtlebot3_burger/base_link/imu_link``
            - ``/World/turtlebot3_burger/wheel_left_link``
            - ``/World/turtlebot3_burger/wheel_right_link``
        

#. Publish a transform tree that consists of `odom -> base_link -> <other robot links>`. This next step is only required when you want to have ground truth localization of the robot. Usually, a ROS package for localization, such as `Nav2 AMCL <https://index.ros.org/p/nav2_amcl/>`_,  would be responsible for setting the transform between a global frame and the odom frame. To setup ground truth localization, add in another *ROS2 Publish Raw Transform Tree* node to the graph and attach the `Exec In`, `Context`, and `Timestamp` fields similarly to previous nodes above.

    - In the **Property** tab for the recently added **ROS2 Publish Raw Transform Tree** node:
  
        - Set the *childFrameId* input field to ``odom``. 
        - Set the *parentFrameId* input field to ``world``. This will now enable publishing `world -> odom` frames in the transform tree.
        - Leave *Translation* and *Rotation* fields detached as this will use the defaults of (0.0, 0.0, 0.0) translation vector (XYZ) and (1.0, 0.0, 0.0, 0.0) rotation quaternion (IJKR). This rotation and translation correspond to the robot's Start pose. If the robot starts in a different position, these fields would have to be updated accordingly to match that pose.

Verify that your final graph is similar to the following:

    .. figure:: /images/isim_5.0_ros_tut_gui_ros2_odometry_graph_final.png
        :align: center
        :width: 800


|
|


Press **Play** and in a new ROS-sourced terminal run the following command:
 
.. code-block::

    ros2 run tf2_tools view_frames



Open the generated PDF file to observe the transform tree that you are publishing from Isaac Sim. Verify that it is similar to the one below.
    
    .. figure:: /images/isim_4.5_ros_tut_gui_ros2_odometry_graph_tf_tree_view.png
        :align: center
        :width: 800


|
|

For an example of all the publishers and subscribers setup in the Turtlebot ROS2 tutorials, open the scene which can be found by going to the Isaac Sim Content browser and clicking **Isaac Sim>Samples>ROS2>Scenario>turtlebot_tutorial.usd**.


Graph Shortcuts
=======================

The following menu shortcuts build transform and odometry graphs:

**TF Publisher**

For transform Publisher, go to **Tools > Robotics > ROS 2 OmniGraphs > TF Publisher** . If you don't observe any ROS2 graphs listed, you need to first enable the ROS2 bridge. A popup box will appear asking for the parameters needed to populate the graphs. You must provide:

- the Graph Path and Node Namespaces if you have one.
- the Target Prim that contains the articulation root API if you want to get the full articulation chain in the transform, or the individual prims if you want to publish a single transform of the prim. 
- the parent prim that is used as the reference frame for the transforms. It is defaulted to \"/World\", but it could be any frame on stage.

If you already have a transform publisher and want to add more prims to publish, as long as they have the same reference prim, then you can check both the "Add to an existing graph" and "Add to an existing node" boxes, give the graph and node paths, and the new target prim to add to the existing graph. If you want to add to the same graph but have different reference prim, it will create a new transform node and use the existing tick, content, and timestamp nodes if they exist.


**Odometry Publisher**

For Odometry Publisher, go to **Tools > Robotics > ROS 2 OmniGraphs > Odometry Publisher**. A popup box will appear asking for the parameters needed to populate the graphs. You must provide:

- the Graph Path and Node Namespaces if you have one.
- the prim that contains the Articulation Root API, and the chassis prim, whose origin is used to calculate odometry.



Viewing the Transform Tree in Isaac Sim
=========================================

The Isaac Sim's ransform viewer allows you to draw on the simulated scene itself in the viewport window and on the transform tree published (under ``/tf`` and ``/tf_static`` topics) by Isaac Sim and/or external ROS 2 nodes.

#. To begin, enable the Isaac Sim's transform viewer extension using the :doc:`Extension Manager <extensions:ext_core/ext_extension-manager>` by searching for ``isaacsim.ros2.tf_viewer``.
#. After the extension is enabled, go to the top menu bar and click on **Window > TF Viewer** to open the transform viewer control window.

    .. figure:: /images/isim_4.5_ros_tut_gui_ros2_tf_viewer_window_legend.png
        :align: center
        :width: 450

    Window components:

    #. Frame on which to compute the transformations.
    #. Whether the frames (markers) are displayed. Marker color. Marker size (relative).
    #. Whether the frames' names are displayed. Text color. Text size (relative).
    #. Whether the frames' axes are displayed (RGB -> XYZ axes). Axis length (in meters). Axis thickness (relative).
    #. Whether to show the connection between the child frames and the parent frames. Line color. Line thickness (relative).
    #. Frame transformation update frequency (Hz). Higher frequency might reduce simulation performance.
    #. Reset transformation tree (clear transformation buffers). Useful to clean ``TF_OLD_DATA`` warning, for example.

    .. note::

        Closing the transform viewer window stops the display and clears the viewport drawings.

#. To start the visualization, choose the appropriate root frame on which to compute the transformations (for example, `World` or `world`, according to the published transform tree specification).

    .. note::

        If the visualization (or a specific root frame) does not show even though there are publications under ``/tf`` and/or ``/tf_static`` topics:

            #. Make sure the simulation is running before opening the **TF Viewer** window
            #. Close and reopen the **TF Viewer** window to update the transform subscriptions
            #. Press the Reset button on the **TF Viewer** window to reset the transformation tree

    .. figure:: /images/isim_4.5_ros_tut_gui_ros2_tf_viewer_example.png
        :align: center
        :width: 90%

Summary
=======================

This tutorial covered:

- Transform publisher to publish sensors and full articulation trees
- Raw transform publisher to publish individual transforms
- Odometry publisher and transform publishers setup for Turtlebot
- Show the transform Viewer in the Isaac Sim's viewport
- Full 3D velocity (x, y, z) publishing for both linear and angular velocity in the odometry message

Next Steps
^^^^^^^^^^^^^^^^^^^^^^
Continue on to the next tutorial in our ROS2 Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_publish_rate` to learn how to set publish rates for ROS2 |omnigraph_short| nodes.


