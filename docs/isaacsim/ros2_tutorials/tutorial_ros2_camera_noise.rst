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



Code Explained
============================

The first step is to set the camera on the render product we want to use for capturing data.
There are APIs to set the camera on the viewport, but there are also lower level APIs that use the render product prim directly.
Both achieve the same. Because we are already working with the render product path, we use ``set_camera_prim_path`` for illustrative purposes.

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_noise/code_explained.py
    :language: python

There are several methods for defining an augmentation within a sensor pipeline:

- C++ OmniGraph node
- Python OmniGraph node
- :doc:`omni.warp kernel <extensions:ext_warp>`
- numpy kernel

The numpy and omni.warp kernel options are demonstrated below to define a basic noise function.
For brevity there are no out of bounds checks for the color values.

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_noise/grab_our_render_product_and_directly_set_the_camer.py
    :language: python

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_noise/gpu_noise_kernel_for_illustrative_purposes_input_i.py
    :language: python

Either of the two functions can be used with ``rep.Augmentation.from_function()`` to define an augmentation.

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_noise/cpu_noise_kernel.py
    :language: python

.. note::
    ``seed`` is an optional predefined Replicator Augmentation argument that can be used with both Python and warp functions. If set to `None` or `< 0`, it will use Replicator's global seed together with the node identifier to produce a repeatable unique seed. When used with warp kernels, the seed is used to initialize a random number generator that produces a new integer seed value for each warp kernel call.

Next, a new writer is created with the new `rgb_gaussian_noise` annotator and registered.

.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_noise/the_image_gaussian_noise_warp_variable_can_be_repl.py
    :language: python

The ``CustomROS2PublishImage`` writer, which uses our new augmented ``rgb_gaussian_noise`` annotator, is registered. We can attach the render product to our replicator writer after initializing. This will begin capturing and publishing data to ROS.


.. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_camera_noise/register_writer_for_replicator_telemetry_tracking.py
    :language: python

Summary
=======================

This tutorial covered the basics of adding an augmentation to the ROS sensor pipeline and adding noise to the RGB sensor output.


Next Steps
*****************
Continue on to the next tutorial in our ROS Tutorials series, :ref:`isaac_sim_app_tutorial_ros2_camera_publishing`.