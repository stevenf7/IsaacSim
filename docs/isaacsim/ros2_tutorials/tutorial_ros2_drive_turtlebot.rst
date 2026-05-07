..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaac_sim_app_tutorial_ros2_drive_turtlebot:


=============================================
Driving TurtleBot using ROS 2 Messages
=============================================

The ROS 2 bridge comes with a few popular rostopics that are packaged for ease of use. Here the focus is on the procedures for using them.

The steps to connect |isaac-sim| to ROS can be done:

* using the UI 
* scripting inside the extension workflow
* scripting inside the standalone Python workflow
 
Refer to :ref:`isaac_sim_app_tutorial_intro_workflows` for details of different workflows. The UI method using existing OmniGraph nodes is demonstrated. Introductions to other methods are listed in the :ref:`isaac_sim_app_tutorial_ros2_drive_turtlebot_further_reading` section.


Learning Objectives
=======================
In this example, you enable a `Turtlebot3 <https://emanual.robotis.com/docs/en/platform/turtlebot3/overview>`_ to drive around and subscribe to a twist message through the ROS network. You learn to:

- Add controllers to Turtlebot3
- Introduce the ROS 2 bridge and ROS |omnigraph_short| (OG) nodes
- Setup the robot to be driven by a ROS2 Twist message


Getting Started
=============================



**Prerequisite**

- Having a rigged Turtlebot, or completed :ref:`isaac_sim_app_tutorial_ros2_turtlebot`.
- Completed :ref:`isaac_sim_app_install_ros`, so that the necessary environment variables are set and sourced before launching |isaac-sim| and the ROS2 extension is enabled.


Main Concepts
===================



Driving the Robot
^^^^^^^^^^^^^^^^^^^^

At the end of :ref:`isaac_sim_app_tutorial_ros2_turtlebot`, the robot has drivable joints, and when given a target position or velocity, it can move the joints to match the targets. Typically, you want to control the vehicle speed and not the individual wheel speed. Therefore, add the appropriate controllers. For Turtlebot3, a wheeled robot with two wheels, the nodes needed are ``Differential Controller`` and ``Articulation Controller``. The ``Differential Controller`` node converts vehicle speed to wheel speed, and the ``Articulation Controller`` node sends the commands to the joint drives.

For more instructions on how to connect nodes, refer to :ref:`isaac_sim_app_tutorial_gui_omnigraph`.


Connecting to ROS2
^^^^^^^^^^^^^^^^^^^^^^^^

As part of our ROS2 bridge, there are nodes that are subscribers and publishers of specific messages, some utility nodes such as keeping track of simulation time and context ID. You will also find "Helper Nodes", which are gateways to more complex OmniGraphs that we abstract away from users.

To establish a ROS2 bridge for a specific topic, the steps can be generalized to the following:

- open an action graph
- add the OG nodes relevant to the desired ROS 2 topics
- modify any properties as needed
- connect the data pipeline

The ROS2 publisher nodes are where |isaac-sim| data gets packaged into ROS messages and sent out to the ROS network, and subscriber nodes are where ROS2 messages are received and allocated to the corresponding |isaac-sim| parameters. So to use them, you must pipe in and out the necessary data, as directed by the properties of each node. If you need to publish or subscribe to messages beyond the ones that are provided, review :ref:`isaac_sim_app_omnigraph_custom_python_nodes`, or :ref:`isaac_sim_app_tutorial_advanced_omnigraph_custom_cpp_nodes` for ways to integrate custom OmniGraph nodes.


Putting It Together
=============================

Building the Graph
^^^^^^^^^^^^^^^^^^^^^^^^

#. Open Visual Scripting: **Window > Graph Editors > Action Graph**. An **Action Graph** window will appear on the bottom, you can dock it wherever convenient.
#. Click on the **New Action Graph** icon in the middle of the **Action Graph** window.
#. Inside the **Action Graph** window, there is a panel on the left hand side with all the |omnigraph_short| Nodes (or OG nodes). All ROS2 related OG nodes are listed under *Isaac Ros2*. You can also search for nodes by name. To place a node into the graph, drag it from the node list into the graph window.
#. Build a graph that matches the one below.

.. figure:: /images/isim_4.5_ros_tut_gui_ros2_turtlebot_graph.png
    :align: center
    :width: 900
    :alt: Turtlebot Graph

.. figure:: /images/isim_4.5_ros_tut_gui_turtlebot_make_array.png
    :align: center
    :width: 300
    :alt: Make Array OG Node


Graph Explained
^^^^^^^^^^^^^^^^^^^^^^^^

- **On Playback Tick Node**: Producing a tick when simulation is "Playing". Nodes that receive ticks from this node will execute their compute functions every simulation step.
- **ROS2 Context Node**: ROS2 uses DDS for its middleware communication. DDS uses `Domain ID <https://docs.ros.org/en/humble/Concepts/Intermediate/About-Domain-ID.html>`_ to allow for different logical networks to operate independently even though they share a physical network. ROS 2 nodes on the same domain can freely discover and send messages to each other, while ROS 2 nodes on different domains cannot. ROS2 context node creates a context with a given Domain ID. It is set to 0 by default. If `Use Domain ID Env Var` is checked, it will import the ``ROS_DOMAIN_ID`` from the environment in which you launched the current instance of |isaac-sim_short|.
- **ROS2 Subscribe Twist Node**: Subscribing to a Twist message. Specify the ROS 2 topic's name ``/cmd_vel`` in the *topicName* field in its Property Tab.

    - The subscriber nodes often have a *Exec Out* field. This acts similar to a tick and will send a signal when a message is received by the subscriber. In this case, the differential controller must be ticked each frame regardless of when a new command arrives. Therefore, for this situation, the Differential Node's *Exec In* is ticked by the output of the *On Playback Tick* node rather than the subscriber node.

- **Scale To/From Stage Unit Node**: Convert assets or inputs to stage unit.
- **Break 3-Vector Node**: The output of the Twist subscriber node is linear and angular velocities, both 3-dimensional vectors. But the input of the differential controller node only takes a forward velocity and rotation velocity in z-axis, therefore you must decompose the array and extract the corresponding elements before feeding them into the differential controller node.
- **Differential Controller Node**: This node receives desired vehicle speed and calculates the wheel speed of the robot. It needs the wheel radius and distance between the wheels to make that calculation. It can also receive optional speed limit parameters to cap off wheel speed. Type in the property tab the wheel radius, the distance between the wheels, and the maximum linear speed for the vehicle as seen in table below to match the Turtlebot.

        =======================  =================
        Field                    Value
        =======================  =================
        Max Angular Speed        1.0
        Max Linear Speed         0.22
        Wheel Distance           0.16
        Wheel Radius             0.025
        =======================  =================



- **Articulation Controller Node**: This node is assigned to a target robot, then takes in the names or the indices of the joints that need to be moved, and moves them by the commands given in *Position Commands*, *Velocity Commands*, or *Effort Commands*.

    - The Articulation Controller node is ticked by *On Playback Tick*. So that if no new Twist message arrives, it will continue to execute whatever command it had received before.
    
    #. To assign the *Articulation Controller* node's target to be the Turtlebot. In the property tab, click on *Add Target* and search for the Turtlebot prim in the popup box. Make sure the robot prim you select is also where the Articulation Root API is applied. Sometimes it is the robot's parent prim. But often times for mobile robots, it is the chassis prim instead. If you imported the URDF following our previous tutorial, the Articulation Root API can be found on ``/World/turtlebot3_burger/base_footprint``. More about Articulation API can be found in :ref:`isaac_sim_app_tutorial_gui_simple_robot_articulation`. If the articulation root is set on the `base_footprint` prim, remove the articulation root property from ``/World/turtlebot3_burger/base_footprint`` and :ref:`add the articulation root property <isaac_sim_app_tutorial_gui_simple_robot_articulation>` on the main robot prim of ``/World/turtlebot3_burger``.
    
    #. To put the names of the wheel joints in an array format, type in the names of the wheel joints inside each of the **Constant Token** nodes, and feed the array of the names into the **Make Array** Node. The names of the joints for the Turtlebot are ``wheel_left_joint`` and ``wheel_right_joint``.
    
    - Do not put the names in *Constant String* node, because |omnigraph_short| does not have a string-array data type. If strings are needed in an array format, to be used by a node, it must be *token* type.




Verifying ROS Connections
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Press **Play** to start ticking the graph and the physics simulation.

#. In a separate ROS-sourced terminal, check that the associated ROS 2 topics exist with ``ros2 topic list``. Verify that ``/cmd_vel`` is listed along with ``/rosout`` and ``/parameter_events``.

#. Now a twist message can be published to the ``/cmd_vel`` topic to control the robot. Let's drive it forward with the command:

    .. code-block:: bash
        
        ros2 topic pub /cmd_vel geometry_msgs/Twist "{'linear': {'x': 0.2, 'y': 0.0, 'z': 0.0}, 'angular': {'x': 0.0, 'y': 0.0, 'z': 0.0}}"


#. To stop the robot from moving, publish a zero velocity command:
    
    .. code-block:: bash

        ros2 topic pub /cmd_vel geometry_msgs/Twist "{'linear': {'x': 0.0, 'y': 0.0, 'z': 0.0}, 'angular': {'x': 0.0, 'y': 0.0, 'z': 0.0}}"


#. To make it easier for us to move the Turtlebot around, install the ``teleop_twist_keyboard`` by running the following command:

    .. code-block:: bash

    	sudo apt-get install ros-$ROS_DISTRO-teleop-twist-keyboard


    Enable driving, using the keyboard, by running:

    .. code-block:: bash

    	ros2 run teleop_twist_keyboard teleop_twist_keyboard



Troubleshooting
^^^^^^^^^^^^^^^^^^^^^^^^


Make sure your robot is on the ground. The table has a different property therefore making it hard for the robot to move on it. To change properties of either the ground or the wheels, go to :ref:`isaac_sim_app_tutorial_gui_simple_robot`.


Summary
========

This tutorial covered the following topics:

#. Drive the robot using the Differential Controller and the Articulation Controller
#. Introduction to ROS 2 Bridge OmniGraph nodes
#. Subscribing to a ROS2 Twist message


Next Steps
^^^^^^^^^^^^^^^^^^^^^^

- Continue on to the next tutorial in our ROS2 Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_clock` to learn to setup ROS2 Clock publishers and subscribers with |isaac-sim|.

.. _isaac_sim_app_tutorial_ros2_drive_turtlebot_further_reading:

Further Learning
^^^^^^^^^^^^^^^^^^^^^^

- Scripting inside the extension workflow is introduced in :ref:`isaac_sim_app_tutorial_ros2_manipulation`.
- Scripting using the standalone Python workflow is introduced in :ref:`isaac_sim_app_tutorial_ros2_python`
- Scripting |omnigraph_short| nodes is introduced in :ref:`isaac_sim_app_tutorial_advanced_omnigraph_scripting`.
- Building custom OmniGraph Python nodes is introduced in :ref:`isaac_sim_app_omnigraph_custom_python_nodes`
- Building custom OmniGraph C++ nodes is introduced in :ref:`isaac_sim_app_tutorial_advanced_omnigraph_custom_cpp_nodes`

