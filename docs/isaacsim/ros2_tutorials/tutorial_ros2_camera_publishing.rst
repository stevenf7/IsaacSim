..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_ros2_camera_publishing:

==========================
Publishing Camera's Data
==========================

Learning Objectives
=======================

In this tutorial, you learn how to programmatically set up publishers for Isaac Sim Cameras at an approximate frequency.


Getting Started
=============================

**Prerequisite**

- Completed the :ref:`isaac_sim_app_tutorial_ros2_camera` tutorial.
- Completed :ref:`isaac_sim_app_install_ros` so that the necessary environment variables are set and sourced before launching |isaac-sim|.
- Read through the :ref:`isaac_sim_cameras`.
- Read through how to programmatically create a :ref:`Camera<isaacsim_sensors_camera>` sensor object in the scene.
- ROS 2 Bridge is enabled.



.. note:: In Windows 10 or 11, depending on your machine's configuration, RViz2 might not open properly.


Setup a Camera in a Scene
==============================================

To begin this tutorial, set up an environment with a ``isaacsim.sensors.camera`` :ref:`Camera<isaacsim_sensors_camera>` object. Running the following code results in a basic warehouse environment loaded with a camera in the scene.

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_publishing/camera_publishing.py
    :language: python
    :end-before: ###### Camera helper functions

Publish Camera Intrinsics to CameraInfo Topic
==============================================

The following snippet will publish camera intrinsics associated with an ``isaacsim.sensors.camera`` Camera to a |link_sensor_msg| topic.

    .. |link_sensor_msg| raw:: html

        <a href="http://docs.ros2.org/latest/api/sensor_msgs/msg/CameraInfo.html" target="_blank">sensor_msgs/CameraInfo</a>

   .. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_publishing/camera_publishing.py
       :language: python
       :pyobject: publish_camera_info

Publish Pointcloud from Depth Images
==============================================

In the following snippet, a pointcloud is published to a `sensor_msgs/PointCloud2 <https://docs.ros2.org/latest/api/sensor_msgs/msg/PointCloud2.html>`_ message. This pointcloud is reconstructed from the depth image using the intrinsics of the camera.

   .. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_publishing/camera_publishing.py
       :language: python
       :pyobject: publish_pointcloud_from_depth

Publish RGB Images
==============================================

    .. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_publishing/camera_publishing.py
        :language: python
        :pyobject: publish_rgb

Publish Depth Images
==============================================

    .. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_publishing/camera_publishing.py
        :language: python
        :pyobject: publish_depth

Publish a TF Tree for the Camera Pose
==============================================

The pointcloud, published using the above function, will publish the pointcloud in the ROS camera axes convention (-Y up, +Z forward). To make visualizing this pointcloud easy in ROS using RViz, the following snippet will publish a TF Tree to the ``/tf``, containing two frames.


The two frames are:

1. ``{camera_frame_id}``: This is the camera's pose in the ROS camera convention (-Y up, +Z forward). Pointclouds are published in this frame.

    .. figure:: /images/camera_frames_v2.005.png
        :width: 600
        :align: center

2. ``{camera_frame_id}_world``: This is the camera's pose in the World axes convention (+Z up, +X forward). This will reflect the true pose of the camera.

    .. figure:: /images/camera_frames_v2.004.png
        :width: 600
        :align: center

The TF Tree looks like this:

    .. figure:: /images/transformation.png
            :width: 600
            :align: center

- world -> ``{camera_frame_id}`` is a dynamic transform from origin to the camera in the ROS camera convention, following any movement of the camera.
- ``{camera_frame_id}`` -> ``{camera_frame_id}_world`` is a static transform consisting of only a rotation and zero translation. This static transform can be represented by the quaternion [0.5, -0.5, 0.5, 0.5] in [w, x, y, z] convention.

Because the pointcloud is published in ``{camera_frame_id}``, it is encouraged to set the ``frame_id`` of the pointcloud topic to ``{camera_frame_id}``. The resulting visualization of the pointclouds can be viewed in the world frame in RViz.

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_publishing/camera_publishing.py
    :language: python
    :pyobject: publish_camera_tf

Running the Example
==============================================

The full standalone script combining all of the above sections is available here:

.. dropdown:: Full Script

    .. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_publishing/camera_publishing.py
        :language: python

Enable ``isaacsim.ros2.bridge`` extension and set up ROS 2 environment variables following :ref:`this workflow tutorial <isaac_sim_app_tutorial_ros2_python>`. Save the above script and run it using ``python.sh`` in the Isaac Sim folder. In our example, ``{camera_frame_id}`` is the prim name of the camera, which is ``floating_camera``.

Verify that you observe a floating camera with prim path ``/World/floating_camera`` in the scene, and verify that the camera sees a forklift:

Verify that you observe the following:

.. figure:: /images/isaac_tutorial_ros_camera_publishing_simview.png
    :align: center

If you open a terminal and type ``ros2 topic list``, verify that you observe the following:

.. code-block:: console

    ros2 topic list
    /camera_camera_info
    /camera_depth
    /camera_pointcloud
    /camera_rgb
    /clock
    /parameter_events
    /rosout
    /tf

The frames published by TF will look like the following:

.. figure:: /images/frames.png
            :width: 300
            :align: center


Now, you can visualize the pointcloud and depth images using RViz2. Open RViz2, and set the **Fixed Frame** field to ``world``.

.. figure:: /images/rviz.png
            :width: 300
            :align: center

Then, enable viewing ``/camera_depth``, ``/camera_rgb``, ``/camera_pointcloud``, and ``/tf`` topics.

Verify that the depth image ``/camera_depth`` and RGB image ``/camera_rgb`` look like this:

.. figure:: /images/isaac_tutorial_ros_camera_publishing_rgbd.png
            :width: 400
            :align: center

The pointcloud will look like so. Verify that the camera frames published by the TF publisher shows the two frames. The image on the left shows the ``{camera_frame_id}_world`` frame, and the image on the right shows the ``{camera_frame_id}`` frame.

.. figure:: /images/isaac_tutorial_ros_camera_publishing_pc_frontview.png
            :align: center

From the side view:

.. figure:: /images/isaac_tutorial_ros_camera_publishing_pc_sideview.png
            :align: center

Summary
=======================

This tutorial demonstrated how to programmatically set up ROS 2 publishers for Isaac Sim Cameras at an approximate frequency.

Next Steps
^^^^^^^^^^^^^^^^^^^^^^

Continue on to the next tutorial in our ROS 2 Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_compressed_image`, to learn how to publish H.264 compressed camera images from |isaac-sim_short|.