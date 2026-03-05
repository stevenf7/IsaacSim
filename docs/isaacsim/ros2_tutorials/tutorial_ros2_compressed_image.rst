..
   Copyright (c) 2024-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_ros2_compressed_image:

========================================
ROS 2 Compressed Images
========================================

Learning Objectives
=======================

In this tutorial, you learn how to:

- Publish H.264 compressed camera images from |isaac-sim_short| using the ROS 2 bridge.
- Decode and visualize the compressed images on the subscriber side using a lightweight ROS 2 decoder node.


Getting Started
=============================

**Prerequisite**

- Completed :ref:`isaac_sim_app_tutorial_ros2_camera` so that you are familiar with how to set up camera publishers in |omnigraph_short|.
- Completed :ref:`isaac_sim_app_install_ros`: installed ROS 2, enabled the ROS 2 extension, built the provided *Isaac Sim* ROS 2 workspace, and set up the necessary environment variables.
- ROS 2 Bridge is enabled.
- Install the ``python3-av`` package, which provides the `PyAV <https://pyav.org/>`_ (Python FFmpeg bindings) dependency required by the ``isaac_compressed_image_decoder`` decoder node:

  .. code-block:: bash

      sudo apt install python3-av


Building the Graph for a Compressed Image Publisher
======================================================

#. Open the turtlebot scene by going to the Isaac Sim Content browser and clicking **Isaac Sim > Samples > ROS2 > Scenario > turtlebot_tutorial.usd**.

#. Open the Graph Editors: **Window** > **Graph Editors** > **Action Graph**.

#. Click on the **New Action Graph** icon in the middle of the *Action Graph* window.

#. Build an Action Graph with the nodes and connections shown below, using the parameters from the table:

    +----------------------------+---------------------+-----------------------------+
    | Node                       | Input Field         | Value                       |
    +----------------------------+---------------------+-----------------------------+
    | Isaac Create Render Product| cameraPrim          | /World/Camera_1             |
    |                            +---------------------+-----------------------------+
    |                            | enabled             | True                        |
    +----------------------------+---------------------+-----------------------------+
    | ROS 2 Camera Helper        | type                | rgb_h264                    |
    |                            +---------------------+-----------------------------+
    |                            | topicName           | image_raw/compressed        |
    |                            +---------------------+-----------------------------+
    |                            | frameId             | sim_camera                  |
    +----------------------------+---------------------+-----------------------------+

    Connect the nodes as follows:

    - **On Playback Tick** ``Tick`` output to **Isaac Create Render Product** ``Exec In``.
    - **Isaac Create Render Product** ``Exec Out`` to **ROS 2 Camera Helper** ``Exec In``.
    - **Isaac Create Render Product** ``Render Product`` output to **ROS 2 Camera Helper** ``renderProductPath`` input.

    Optionally, add a **ROS 2 Context** node and connect its ``Context`` output to the **ROS 2 Camera Helper** ``context`` input if you need a specific ROS 2 Domain ID.


Graph Explained
^^^^^^^^^^^^^^^^^^^^

- **On Playback Tick**: Produces a tick when simulation is playing.
- **Isaac Create Render Product**: Creates a render product for the specified camera prim, which captures rendered data each frame.
- **ROS 2 Camera Helper**: When the ``type`` is set to ``rgb_h264``, this node automatically activates the H.264 hardware encoder pipeline. The encoder compresses the RGB camera output into an H.264 bitstream and publishes it as a ``sensor_msgs/CompressedImage`` message. Each published message contains a complete IDR (Instantaneous Decoder Refresh) frame, meaning every frame can be independently decoded without reference to previous frames.


Verifying ROS Connection
============================

#. Press **Play** to start the simulation.

#. Optionally, drive the Turtlebot around using the keyboard to see the camera view change. In a ROS 2-sourced terminal, run:

    .. code-block:: bash

        ros2 run teleop_twist_keyboard teleop_twist_keyboard

    .. note::

        If ``teleop_twist_keyboard`` is not installed, install it with: ``sudo apt-get install ros-$ROS_DISTRO-teleop-twist-keyboard``

#. In a ROS 2-sourced terminal, verify that the compressed topic is available:

    .. code-block:: bash

        ros2 topic list

    You should observe ``/image_raw/compressed`` in the topic list.

#. Verify that data is being published on the topic:

    .. code-block:: bash

        ros2 topic hz /image_raw/compressed

    You should observe a non-zero publish rate.

#. Inspect the message format:

    .. code-block:: bash

        ros2 topic echo /image_raw/compressed --no-arr

    The ``format`` field should show ``h264``, and the ``data`` field will contain the compressed H.264 bitstream.


Decoding Compressed Images
=============================

The compressed H.264 images cannot be directly viewed in tools like RViz2. A decoder node is needed to convert them back to raw ``sensor_msgs/Image`` messages. The ``isaac_compressed_image_decoder`` package provides this functionality using `PyAV <https://pyav.org/>`_ (Python FFmpeg bindings) for software-based H.264 decoding.

Running the Decoder Node
^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. In a ROS 2-sourced terminal with the workspace sourced, run the decoder node:

    .. code-block:: bash

        ros2 run isaac_compressed_image_decoder decoder_node

    By default, the decoder subscribes to ``/image_raw/compressed`` and publishes decoded raw images on ``/image_decoded``.

#. To customize the input and output topic names, use ROS 2 parameters:

    .. note::

        The following customization of input and output topics is provided for your information and is optional for this tutorial—the default topics should work for most users.

    .. code-block:: bash

        ros2 run isaac_compressed_image_decoder decoder_node --ros-args -p input_topic:=/camera2/image_raw/compressed -p output_topic:=/camera2/image_decoded

#. Verify the decoded images are being published:

    .. code-block:: bash

        ros2 topic hz /image_decoded


Visualizing in RViz2
========================

#. In a ROS 2-sourced terminal, open RViz2:

    .. code-block:: bash

        rviz2

#. Click **Add** in the *Displays* panel, then select **By topic** and choose ``/image_decoded`` under the ``Image`` display type.

#. Verify that the decoded camera view is displayed in the *Image* panel.


Summary
===========

This tutorial covered the following topics:

- Publishing H.264 compressed camera images from |isaac-sim_short| using the ``rgb_h264`` type in the **ROS 2 Camera Helper** node.
- Decoding compressed images using the ``isaac_compressed_image_decoder`` ROS 2 package.
- Visualizing the decoded images in RViz2.

.. note::

    H.264 compression significantly reduces bandwidth compared to raw image publishing, making it suitable for scenarios where network bandwidth is constrained.


Next Steps
^^^^^^^^^^^^^^^^^^^^^^

Continue on to the next tutorial in our ROS 2 Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_rtx_lidar`, to learn how to add an RTX Lidar sensor to the Turtlebot3.
