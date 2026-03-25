

..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_ros2_manipulation:

================================================
ROS2 Joint Control: Extension Python Scripting
================================================



Learning Objectives
=======================

In this tutorial, you interact with a manipulator, the Franka Emika Panda Robot. You:

- Add a ROS2 Joint State publisher and subscriber in Omnigraph
- Add a ROS2 Joint State publisher and subscriber using menu shortcut
- Add a ROS2 Joint State publisher and subscriber using the |omnigraph_short| Python API using the script editor
- Learn about the ``isaac:nameOverride`` prim attribute

Getting Started
=============================



**Prerequisite**

- Completed :ref:`isaac_sim_app_tutorial_intro_workflows` to understand the Extension Workflow.
- Appropriate ``ros2_ws`` is sourced in the terminal that will be running Python scripts.
- ``FASTRTPS_DEFAULT_PROFILES_FILE`` environment variable is set prior to launching Isaac Sim and the ROS2 bridge is enabled.

Add Joint States in UI
=====================================


1. Open the asset, which can be found by going to the Isaac Sim Content browser **Isaac Sim>Robots>FrankaRobotics>FrankaPanda>franka.usd**.
2. Go to **Window > Graph Editors > Action Graph** to create an Action graph.
3. Add the following |omnigraph_short| nodes into the Action graph:

  - **On Playback Tick** node to execute other graph nodes every simulation frame.
  - **Isaac Read Simulation Time** node to retrieve current simulation time.
  - **ROS2 Publish Joint State** node to publish ROS2 Joint States to the ``/joint_states`` topic.
  - **ROS2 Subscribe Joint State** node to subscribe to ROS2 Joint States from the ``/joint_command`` topic.
  - **Articulation Controller** node to move the robot articulation according to commands received from the subscriber node.

4. Select `ROS2 Publish Joint State` node and add the */panda* robot articulation to the `targetPrim`.
5. Select `Articulation Controller` node, indicate the robot articulation you want to move by adding */panda* to the `targetPrim`, or typing */panda* in the `robotPath` field.
6. Connect the Tick output of the `On Playback Tick` node to the Execution input of the `ROS2 Publish Joint State`, `ROS2 Subscribe JointState`, and `Articulation Controller` nodes.
7. Connect the Simulation Time output of the `Isaac Read Simulation Time` node to the Timestamp input of the `ROS2 Publish Joint State` node. Setup other connections between nodes as shown in the image below:

    .. figure:: /images/isim_4.5_ros_tut_gui_ros2_manipulation_1.png
        :align: center
        :width: 600
        :alt: ROS2 Joint State Action Graph

8. Press **Play** to start publishing joint states to the ``/joint_states`` topic and subscribing commands on the ``/joint_command`` topic.
9. To test out the ROS2 bridge, use the provided Python script to publish joint commands to the robot. In a ROS2-sourced terminal:

    .. code-block:: bash

    	ros2 run isaac_tutorials ros2_publisher.py

10. While the robot is moving, open a ROS2-sourced terminal and check the joint state ROS 2 topic by running:

    .. code-block:: bash

        ros2 topic echo /joint_states

.. Note::
    
    Articulation Root describes the beginning of an articulation tree, a collection of links and joints that makes up the robot in simulation.
    For fixed base robots like the franka, articulation root is specified at its root joint to world, and for move-able objects, the articulation root is specified at the rigid body with the deepest tree, typically the torso or chassis_link.

Graph Shortcut
===============================================

We provide a menu shortcut to build Joint State Publisher and Subscriber graphs with just a few clicks. Go to **Tools > Robotics > ROS 2 OmniGraphs > JointStates**. If you don't observe any ROS2 graphs listed, you need to enable the ROS2 bridge. A popup box will appear asking for the parameters needed to populate the graphs. You must provide the Graph Path, Node Namespace if there is one needed, and the prim that contains the Articulation Root API. If you are using the subscriber, you also have the option to add the Articulation Controller node needed to move the robot.


.. _isaac_sim_app_ros2_joint_states_extension:

Add Joint States in Extension
====================================

The same action done using the UI can also be done using a Python script. More details regarding the different workflows of using |isaac-sim| can be found :ref:`isaac_sim_app_tutorial_intro_workflows`.

1. Open the asset, which can be found by going to the Isaac Sim Content browser and clicking **Isaac Sim>Robots>FrankaRobotics>FrankaPanda>franka.usd**.
2. Open Script Editor in **Window > Script Editor** and copy paste the following code into it. This is the equivalent to Steps 2-7 of the previous section. If the robot appears other than `/panda` on the stage tree, make sure to match the Articulation Controller and Publish Joint State nodes' targets to the robot's prim path (line 29 and 30).

    .. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_manipulation/add_joint_states_in_extension.py
        :language: python

3. Press **Run** in the **Script Editor** and the Action Graph with all required nodes is added. You can find the corresponding ActionGraph in the Stage Tree.

.. note:: This script must only be run once. It is assuming there is no ActionGraph that already exists on stage. You can start a new stage to run it again.

4. Test out the ROS 2 bridge using the provided ROS 2 Python node to publish joint commands to the robot. In a ROS 2 sourced terminal, run the following command:

    .. code-block:: bash

        ros2 run isaac_tutorials ros2_publisher.py



5. Verify the joint state with a ROS 2 topic echo command while it's moving:

    .. code-block:: bash

        ros2 topic echo /joint_states



Position and Velocity Control Modes
====================================

The joint state subscriber supports position and velocity control. Each joint can only be controlled by a single mode at a time, but different joints on the same articulation tree can be controlled by different modes. Make sure each joint's stiffness and damping parameters are setup appropriately for the desired control mode (position control: stiffness >> damping, velocity control: stiffness = 0).

The snippet is an example of how to command a robot using both position and velocity controls by grouping joints that use the same mode into one message, and create two different messages for position control joints and velocity controlled joints. Separating them is for organization and potentially sending them at different rates.

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_manipulation/position_and_velocity_control_modes.py
    :language: python

They can be combined into a single message if desired. Use `'nan'` for joints that are not being controlled by that control mode.

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_manipulation/spin_in_a_separate_thread.py
    :language: python

Summary
=======================

This tutorial covered adding a ROS2 Joint State publisher and subscriber using both the UI and Extension scripting.

Next Steps
^^^^^^^^^^^^^^^^^^^^^^
Continue on to the next tutorial in our ROS2 Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_name_override` to learn how to apply custom names to prims using the ``isaac:nameOverride`` attribute.

