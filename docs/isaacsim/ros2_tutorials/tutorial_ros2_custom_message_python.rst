..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaac_sim_app_ros2_custom_message_python:

==============================
ROS 2 Python Custom Messages
==============================

.. note:: ROS 2 Python Custom Messages with |isaac-sim_short| is fully supported on Linux. On Windows (WSL), this workflow is not supported.

Learning Objectives
=====================

In this example, you learn how to use ROS 2 ``rclpy`` Python interface with |isaac-sim_short| for a custom message.


Getting Started
====================

**Prerequisite**

- Basic understanding of `building ROS 2 packages <https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Custom-ROS2-Interfaces.html>`_.



Using Custom Messages with Python
==================================

For using ``rclpy`` with |isaac-sim_short| the packages must be built with ``Python 3.12``. You can create your own package and build it in the ROS 2 workspace.

|isaac-sim_short| only supports Python 3.12. Packages built can be used directly with ``rclpy`` in |isaac-sim_short|, if they are built with Python 3.12. 

For demonstrating the workflow, the tutorial uses a ``custom_message`` package, which is a part of the `Isaac Sim ROS Workspace <https://github.com/isaac-sim/IsaacSim-ros_workspaces>`_  repository. 
This repository contains a custom message under ``custom_message/msg/SampleMsg.msg`` with the following definition:

.. code-block:: bash

    std_msgs/String my_string
    int64 my_num


To build your own ROS 2 custom message packages for use with |isaac-sim_short|, you can place the package under ``humble_ws/src`` or ``jazzy_ws/src`` in your ``Isaac Sim ROS Workspace`` folder. 

If you are on Ubuntu 24.04 and using ROS 2 Jazzy, you can follow the instructions :ref:`isaac_sim_ros_workspace_setup` to build the ROS 2 workspace with Python 3.12.

Otherwise, run ``./build_ros.sh`` and source your workspaces before running |isaac-sim_short|.
Ensure you have completed the steps in :ref:`isaac_sim_ros_workspace_setup_other_platforms`.
    

#. Run |isaac-sim_short| from the same terminal where the sourced workspace contains the minimal ROS 2 dependencies needed to enable the ROS 2 bridge and the ``custom_message`` package, which contains our sample message.

Using the ``custom_message`` package with Python in |isaac-sim_short|:

.. tab-set::

    .. tab-item:: Script Editor
        :sync: script_editor

        Launch |isaac-sim_short| from the sourced terminal containing the ``custom_message`` package.
        
        Open the **Script Editor** and type:

        .. code-block:: bash

            import rclpy
            from custom_message.msg import SampleMsg

            # Create message
            sample_msg = SampleMsg()

            # assign data in the string part and integer part of the message             
            sample_msg.my_string.data = "hello from Isaac Sim!"
            sample_msg.my_num = 23

            print("Message assignment completed!")

        Press **Run** and verify that the ``Message assignment completed`` is logged on your console. This indicates that the message import and interaction was successful. 


    .. tab-item:: Standalone Python Scripts
        :sync: standalone_python

        You can use a standalone Python script to enable the ROS 2 bridge and import your ``custom_message``. 
        Navigate to your |isaac-sim_short| installation directory and create a file named ``ros2_custom_message.py``, paste the following content into it:

        .. code-block:: bash

            import carb
            from isaacsim import SimulationApp

            simulation_app = SimulationApp({"renderer": "RayTracedLighting", "headless": True})

            import omni
            from isaacsim.core.utils.extensions import enable_extension

            # enable ROS2 bridge extension
            enable_extension("isaacsim.ros2.bridge")

            # Make the rclpy imports
            import rclpy
            from custom_message.msg import SampleMsg

            # Create message
            sample_msg = SampleMsg()

            # assign data in the string part and integer part of the message             
            sample_msg.my_string.data = "hello from Isaac Sim!"
            sample_msg.my_num = 23

            print("Message assignment completed!")

        
        Make sure that your ROS 2 workspace with the ``custom_message`` package is sourced in the same terminal and that you are in the right directory, which contains ``./python.sh``.

        Run this script:

        .. code-block:: bash

            ./python.sh ros2_custom_message.py

        Verify that ``Message assignment completed`` is logged on your console. This indicates that the message import and interaction was successful.



Summary
========

This tutorial covered the following topics:

#. Building a ROS 2 custom message package with ``Python 3.12``
#. Using the custom message with ``rclpy`` in |isaac-sim_short|
#. Overview of steps to build and use your own custom message package with ``rclpy`` and |isaac-sim_short|

Next Steps
*****************
Continue on to the next tutorial in our ROS2 Tutorials series, :ref:`isaac_sim_app_ros2_custom_omnigraph_node_python`.