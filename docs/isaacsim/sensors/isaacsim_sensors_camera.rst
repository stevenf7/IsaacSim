..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaacsim_sensors_camera:

==============
Camera Sensors
==============

Cameras are modeled using the Camera USD prim type. Camera data is acquired from camera prims using render products, which can be created by multiple different extensions in Omniverse,
including the :doc:`omni.replicator<extensions:ext_replicator>` extension.

.. note::
    |isaac-sim_short| camera functionality is based on `Omniverse cameras <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/cameras.html>`_.

GUI
===

Creating and Modifying a Camera
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Create a cube by selecting **Create > Shape > Cube** and change its location and scale through the property panel as indicated in the screenshot below.

    .. image:: /images/isim_4.5_full_ext-isaacsim.sensors.camera-0.2.5_gui_1.png
        :align: center

#. Create a camera prim by selecting **Create > Camera** and then select it from the stage window to view its field of view as indicated below.

    .. image:: /images/isim_4.5_full_ext-isaacsim.sensors.camera-0.2.5_gui_2.png
        :align: center

#. To render the frames from the camera, switch the default viewport (which is a render product itself) to the camera prim that you just created.
   Select the video icon at the top of the viewport window and then select the camera prim you just created under the ``Cameras`` menu.

    .. image:: /images/isim_4.5_full_ext-isaacsim.sensors.camera-0.2.5_gui_3.png
        :align: center

Standalone Python
=================

There are multiple ways to retrieve data from a render product attached to a camera prim in |isaac-sim_short|. One method is the ``Camera`` class
under the ``isaacsim.sensors.camera`` extension. You can run an example using the ``Camera`` class using ``./python.sh standalone_examples/api/isaacsim.sensors.camera/camera.py``.
The code in that example is provided below, for reference.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_camera/standalone_python.py
    :language: python
    :linenos:
    :emphasize-lines: 38-44, 48, 51, 63-65

.. image:: /images/isim_4.5_full_ext-isaacsim.sensors.camera-0.2.5_gui_4.png
    :align: center

.. _isaacsim_sensors_camera_calibration_and_camera_lens_distortion_models:

Calibration and Camera Lens Distortion Models
=============================================

Omniverse cameras support a variety of lens distortion models, described `here <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/cameras.html#omniverse-cameras>`_.
The ``isaacsim.sensors.camera.Camera`` class includes APIs to set lens distortion parameters for each Omniverse camera lens distortion model.


Calibration toolkits like OpenCV normally provide the calibration parameters as an intrinsic matrix and distortion coefficients. Omniverse includes native renderer support for the OpenCV pinhole and
OpenCV fisheye lens distortion models. |isaac-sim_short| provides two standalone examples demonstrating the use of the ``Camera`` class with OpenCV lens distortion models,
located at ``standalone_examples/api/isaacsim.sensors.camera/camera_opencv_pinhole.py`` and ``standalone_examples/api/isaacsim.sensors.camera/camera_opencv_fisheye.py``.

Portions of these examples are repeated below for reference, and can be run using using **Script Editor**, opened from **Window > Script Editor**.

.. Note::
    - Previously, the ``Camera`` class included APIs to approximate OpenCV pinhole and fisheye models distortion parameters by setting coefficients for the ``fisheyePolynomial`` distortion model. Now that OpenCV lens distortion models are natively supported, those APIs have been deprecated.
    - `Omniverse RTX Camera Projection Attributes <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/cameras.html#rtx-camera-projection-attributes-deprecated>`_ have been deprecated as of |isaac-sim_short| 5.0, in favor of the ``OmniLensDistortion`` `schemata <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/cameras.html#omnilensdistortion-schemata>`_. The deprecated attributes are still visible in the UI in the ``Fisheye Lens`` panel when selecting a Camera prim, but will be ignored if the you have set an ``OmniLensDistortion`` schema instead. Follow the instructions in `"How To Add Schemata to Cameras" <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/cameras.html#omnilensdistortion-schemata>`_ to see how to update Camera prim attributes for the new schemata in  the UI.

OpenCV Fisheye
^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_camera/opencv_fisheye.py
    :language: python

After running the snippet above and setting the viewport to the newly-created camera, validate that you see an image like the one below.

.. image:: /images/isim_5.0_full_ext-isaacsim.sensors.camera-1.1.0_viewport_camera-opencv-fisheye-test.png
    :align: center

OpenCV Pinhole
^^^^^^^^^^^^^^

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_camera/opencv_pinhole.py
    :language: python

After running the snippet above and setting the viewport to the newly-created camera, you should see an image like the one below.

.. image:: /images/isim_5.0_full_ext-isaacsim.sensors.camera-1.1.0_viewport_camera-opencv-pinhole-test.png
    :align: center

Extrinsic Calibration
^^^^^^^^^^^^^^^^^^^^^

Extrinsic calibration parameters are normally provided by the calibration toolkits in a form of a transformation matrix. The convention between the axis and rotation order is important and it varies between the toolkits.

To set the extrinsic parameters for the individual camera sensor, use the following example to convert the transformation matrix from the calibration toolkit to the Isaac Sim units:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_camera/extrinsic_calibration.py
    :language: python

As an alternative, the camera sensor can be attached to a prim. In that case, the camera sensor will inherit the position and orientation from the prim.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_camera/depends_if_translation_or_position_is_specified.py
    :language: python

.. _isaacsim_sensors_camera_creating_camera_sensors:

Creating Camera Sensor Rigs
===========================

The camera sensor rig is a collection of camera sensors that are attached to a single prim. It can be assembled from the individual sensors, that are either created manually or derived from the calibration parameters.

This will be a short discussion on how we created a digital twin of the Intel® RealSense™ Depth Camera D455.  The USD for the camera can be found in the content folder as: ```/Isaac/Sensors/Intel/RealSense/rsd455.usd``.

There are three visual sensors, and one IMU sensor on the RealSense.  Their placement relative to the camera origin was taken from the layout diagram in
the `TechSpec document <https://www.intelrealsense.com/wp-content/uploads/2023/07/Intel-RealSense-D400-Series-Datasheet-July-2023.pdf>`_ from `Intel's web site <https://www.intelrealsense.com/depth-camera-d455/>`_.

Most camera parameters were also found in the TechSpec, for example, the USD parameter ``fStop`` is the denominator of the F Number from the TechSpec; the ``focalLength`` is the Focal Length, and the ``ftheatMaxFov``
is the Diagonal Field of View.  However, some parameters, like the ``focusDistance`` were estimated by comparing real output and informed guesses.

The ``horizontalAperture`` and ``verticalAperture`` in that example are derived from the technical specification. From the TechSpec, the left, right, and color sensors are listed as a OmniVision Technologies OV9782, and
the `Tech Spec <https://www.ovt.com/products/ov09782-ga4a/>`_ for that sensor lists the image area as 3896 x 2453 µm.  We used that as the aperture sizes.

The resolution for the depth and color cameras are 1280 x 800, but it's up to you to attach a render product of that size to the outputs.

The ``Pseudo Depth`` camera is a stand in for the depth image created by the camera's firmware.  We don't attempt to copy the algorithms that create the image from stereo, but the ``Camera_Pseudo_Depth`` component
is a convenience camera that can return the scene depth as seen from that camera position between the left and right stereo cameras.  It would be more accurate to create a depth image from stereo, and if
the same algorithm that is used in the RealSense was used then the same results (including artifacts) would be produced.


Exposing the Pre-ISP Camera Pipeline
====================================

The ``omni.sensors.nv.camera`` extension `simulates the camera sensor and image signal processor (ISP) pipeline <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/cameras.html#omni-sensors-nv-camera-extension>`_.

|isaac-sim_short| 5.1 now includes a standalone example demonstrating how to render and save output from each step of the pre-ISP camera pipeline, including color correction, CFA encoding, and companding, for users who
would like to test their own ISP using images rendered in Omniverse, or compare the output of their ISP with the output of the Omniverse simulatedISP.

Refer to the `extension documentation <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/cameras.html#omni-sensors-nv-camera-extension>`_ for more details on the camera pipeline.

Run the example via:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_camera/exposing_the_pre_isp_camera_pipeline.py
    :language: python

The example will render and save output from three pre-ISP steps, by default in the ``pre_isp_camera_pipeline_outputs`` directory. The HDR buffer, raw sensor output, and ISP output from the example are shown below:

.. image:: /images/isim_5.1_base_tut_external_camera_pre_isp_pipeline_hdr_input.png
    :align: center

.. image:: /images/isim_5.1_base_tut_external_camera_pre_isp_pipeline_raw_sensor_output.png
    :align: center

.. image:: /images/isim_5.1_base_tut_external_camera_pre_isp_pipeline_isp_output.png
    :align: center

.. _isaac_sim_app_tutorial_camera_inspector_extension:

Camera Inspector Extension
==========================

The Camera Inspector Extension allows you to:

* Create multiple viewports for each camera
* Check camera coverage
* Get and set camera poses in the desired frames


Launching Extension
^^^^^^^^^^^^^^^^^^^^^^
To open the Camera Inspector extension:

#. Go to the Menu Bar.
#. Select **Tools > Sensors > Camera Inspector**.
#. After launching the extension, verify that you can see your camera in the dropdown.
#. When adding a new camera, you must click the Refresh button to ensure that the extension finds this new camera.
#. Select the camera you want to inspect.

Camera State Textbox
^^^^^^^^^^^^^^^^^^^^^^

.. image:: /images/isim_4.5_base_ref_gui_camera_status_textbox.png
    :align: center

The **Camera State** textbox near the top of the extension provides a convenient way to copy the position and orientation of your camera directly into code.
Click the copy icon on the right of the textbox to copy to your clipboard.


Creating a Viewport
^^^^^^^^^^^^^^^^^^^^^^

With the camera selected, you can create a new viewport for your camera.

#. Click on the **Create Viewport** button to the right of the camera dropdown menu.

    By default, this creates a new viewport and assigns the current selected Camera to it.

#. Assign different cameras to different viewports using the two dropdown menus and buttons in the extension:

    .. image:: /images/isim_4.5_base_ref_gui_camera_sensors_create_viewport.png
        :align: center

#. After launching your viewport, you can change the resolution using the menu in the top left and going to **Viewport**.

    .. note:: When changing the resolution, Omniverse Kit only supports square pixels. This means that the resolution aspect ratio must be the same as the aperture ratio.

    .. image:: /images/isim_4.5_base_ref_gui_camera_sensors_config.png
        :align: center
        :width: 50%

