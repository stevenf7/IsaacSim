

..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_tutorial_ros2_qos:

======================================
ROS 2 Quality of Service (QoS)
======================================

Learning Objectives
=======================

In this tutorial, you:

- Set Quality of Service (QoS) for all ROS2 |omnigraph_short| nodes.
- Create a preset generic ROS2 publisher Action Graph.
- Set a static ROS2 publisher by setting a QoS Profile.


Getting Started
=============================



**Prerequisite**

- Completed :ref:`isaac_sim_app_install_ros` so that the necessary environment variables are set and sourced before launching |isaac-sim|, and ROS2 extension is enabled.

- Read about `Quality of Service settings <https://docs.ros.org/en/humble/Concepts/Intermediate/About-Quality-of-Service-Settings.html>`_.

.. note:: The ROS2 QoS Profile OmniGraph node has a known issue: it is unable to save custom profiles in USD unless you first set the `createProfile` input to "Custom" before modifying any other fields.

Setting QoS Profile for ROS 2 |omnigraph_short| Nodes
==========================================================

1. Open a new stage.

2. Go to **Tools > Robotics > ROS 2 OmniGraphs > Generic Publisher**. For **Generic Publisher Graph**, select **Publish String**. Click **OK**.

3. Expand the newly created *Graph* prim. Select **ROS_GenericPub**, right click and choose **Open Graph**. 

    All ROS 2 |omnigraph_short| nodes such as the ROS2 Publisher include a *qosProfile* string input. This input is formatted as a JSON string. An example of the JSON string for the default QoS settings for publishers and subscriptions is shown below. 

     .. code-block:: json
        
        {
            "history": "keepLast",
            "depth": 10,
            "reliability": "reliable",
            "durability": "volatile",
            "deadline": 0.0,
            "lifespan": 0.0,
            "liveliness": "systemDefault",
            "leaseDuration": 0.0
        }


    *depth* must be set as a positive integer while *deadline*, *lifespan*, and *leaseDuration* must be set as floats in order for the JSON string to be valid.

    While you can directly set the *qosProfile* input of any ROS 2 OmniGraph node with a valid JSON string, you can also use the *ROS2 QoS Profile* node to automatically generate this string and connect its output to multiple ROS 2 publisher or subscriber nodes.

4. In the Action Graph window, add the *ROS2 QoS Profile* node and connect as shown below. The *createProfile* input contains multiple `preset QoS profiles <https://docs.ros.org/en/humble/Concepts/Intermediate/About-Quality-of-Service-Settings.html#qos-profiles>`_. The other inputs are QoS policies, which can be individually set to create a custom QoS profile. 

    .. figure:: /images/isaac_tutorial_ros2_qos_connect.png
        :align: center
        :width: 800
        :alt: ROS2 QoS Graph

5. Set *createProfile* to *Sensor Data* and then click **Play** to start simulation. 

    .. note:: If the UI doesn't update with new values, you might have to click outside of the node and then click on it again.

6. In a ROS2-sourced terminal, run the following command to retrieve the QoS settings for the topic.

    .. code-block:: bash
        
        ros2 topic info /topic -v


    The output for QoS Profile should match the ones defined from |isaac-sim_short|.
	
	.. note:: By default Fast DDS (formerly Fast RTPS) does not store depth so depth policy might appear as UNKNOWN. Try running |isaac-sim_short| and ROS2 nodes using :ref:`Cyclone DDS <isaac_sim_app_install_cyclonedds>` to retrieve depth info. If depth policy still appears as UNKNOWN after switching to Cyclone DDS, this might be related to your hardware configuration. 

Creating Static Publishers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This section assumes you have already completed the above section. 

Static publishers can be useful when you publish a message exactly once but need the same message to be available regardless of how many subscribers connect to the topic.

1. Modify the Action Graph from earlier by adding in the *On Stage Event* and *Countdown* |omnigraph_short| nodes as shown below:

    .. figure:: /images/isaac_tutorial_ros2_qos_static_connect.png
        :align: center
        :width: 800
        :alt: ROS2 QoS Static node Graph


    - For the *On Stage Event* set the *eventName* to *Simulation Start Play*.

    - For the *Countdown* node, set the *duration* to 3 and *period* to 1. This will tick the *ROS2 Publisher* node 3 times after simulation is played. For the *ROS2 Publisher* node, the first 2 frames are used for setup and the 3rd frame publishes a message.
    
2. Select the *ROS2 QoS Profile* node and set *createProfile* to *Default for publisher/subscribers*. 

3. Then, set *depth* policy to 1 and *durability* policy to *transientLocal*.

4. Hit **Play** to start simulation. 

5. In a new ROS2-sourced terminal run the command once to view the static message:

    .. code-block:: bash
        
        ros2 topic echo /topic

6. In another ROS2-sourced terminal repeat step 5 and notice the static message appear again for this second subscriber.


Summary
=======================

This tutorial covered:

- QoS Profile Node.
- Setting Quality of Service (QoS) for all ROS2 |omnigraph_short| nodes.
- Setting a static ROS2 publisher using a custom QoS Profile.

Next Steps
^^^^^^^^^^^^^^^^^^^^^^
Continue on to the next tutorial in our ROS2 Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_manipulation` to learn how to move a manipulator using direct joint control and retrieve joint states.

