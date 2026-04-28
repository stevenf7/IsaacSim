..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_sim_app_tutorial_ros2_camera_noise:

====================================
Add Noise to Camera
====================================



Learning Objectives
=======================

In this example, we will:

- Have a brief introduction regarding adding an augmentation to sensor images
- Publish image data with noise added


Getting Started
=============================

**Prerequisites**

- Completed the :ref:`isaac_sim_app_tutorial_ros2_camera` tutorial.
- ROS 2 bridge is enabled. 
- Familiarity with :doc:`omni.replicator <extensions:ext_replicator>` concepts.
- Set the environment variables needed to enable ROS2 messaging in standalone workflow by completing the steps in :ref:`isaac_sim_app_recommended_ros_distros_using_terminal`.


Running the Example
============================

#. In one terminal source your ROS 2 workspace.
#. In another terminal with your ROS 2 environment sourced, run the sample script:

    .. code-block:: bash

        ./python.sh standalone_examples/api/isaacsim.ros2.bridge/camera_noise.py

    After the scene finishes loading, verify that you observe the viewport scanning a warehouse scene counterclockwise.
#. In a new terminal with your ROS environment sourced, open an empty RViz window by running ``rviz2`` on the command line.
#. Add an Image window by clicking on "Add" on the bottom left. In the pop-up window, under the "By display type" tab, select "Image" and click "OK".
#. A new image window will appear somewhere on your RViz screen, along with a menu item labeled "Image" in the Display window. Dock the image window somewhere convenient.
#. Expand the Image in the Display menu and change the "Image Topic" to ``/rgb_augmented``. Verify that a slightly noisy version of the image in |isaac-sim_short| is now showing in the RViz image window.


    .. image:: /images/isim_5.0_ros_tut_gui_ros2_camera_noise.gif
        :align: center



Code explained
============================

First, set the camera on the render product used for capturing data. You can set the camera through the viewport API, but here we use ``set_camera_prim_path`` on the render product directly.

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_noise/camera_noise.py
    :language: python
    :start-after: # [set-camera]
    :end-before: # [/set-camera]

There are several methods for defining an augmentation within a sensor pipeline:

- C++ OmniGraph node
- Python OmniGraph node
- :doc:`omni.warp kernel <extensions:ext_warp>`
- numpy kernel

The numpy and warp kernel options are demonstrated below with a basic noise function. For brevity there are no out-of-bounds checks for color values.

The GPU warp kernel takes RGBA input and produces RGB output, applying per-pixel Gaussian noise:

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_noise/camera_noise.py
    :language: python
    :start-after: # [gpu-noise-kernel]
    :end-before: # [/gpu-noise-kernel]

The equivalent CPU kernel uses numpy:

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_noise/camera_noise.py
    :language: python
    :start-after: # [cpu-noise-kernel]
    :end-before: # [/cpu-noise-kernel]

Either function can be passed to ``rep.Augmentation.from_function()`` to define an augmentation. The following registers a new ``rgb_gaussian_noise`` annotator that composes the noise function on top of the ``rgb`` annotator:

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_noise/camera_noise.py
    :language: python
    :start-after: # [register-annotator]
    :end-before: # [/register-annotator]

.. note::
    ``seed`` is an optional predefined Replicator Augmentation argument that works with both Python and warp functions. If set to ``None`` or ``< 0``, Replicator uses its global seed together with the node identifier to produce a repeatable unique seed. For warp kernels, the seed initializes a random number generator that produces a new integer seed value for each kernel call.

Next, create a custom writer that uses the augmented ``rgb_gaussian_noise`` annotator and register it:

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_noise/camera_noise.py
    :language: python
    :start-after: # [register-writer]
    :end-before: # [/register-writer]

Finally, instantiate the writer, configure the ROS topic, and attach the render product. This begins capturing and publishing the augmented image data to ROS:

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_noise/camera_noise.py
    :language: python
    :start-after: # [attach-writer]
    :end-before: # [/attach-writer]

Summary
=======================

This tutorial covered the basics of adding an augmentation to the ROS sensor pipeline and adding noise to the RGB sensor output.


Next Steps
*****************
Continue on to the next tutorial in our ROS Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_camera_publishing`.