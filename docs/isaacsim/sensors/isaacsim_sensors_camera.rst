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

.. deprecated:: 6.0
   The ``isaacsim.sensors.camera`` extension is deprecated. Use ``isaacsim.sensors.experimental.rtx`` instead.
   The new extension provides ``RtxCamera``, ``CameraSensor``, ``TiledCameraSensor``,
   ``SingleViewDepthCameraSensor``, and ``StructuredLightCamera`` with a uniform authoring/runtime
   split. See :ref:`isaacsim_sensors_camera_migration` below.

Overview
--------

|isaac-sim_short| cameras are USD ``Camera`` prims rendered by the RTX renderer. The
``isaacsim.sensors.experimental.rtx`` extension wraps these prims with two paired classes:

* **Authoring** — ``RtxCamera`` creates or wraps a USD ``Camera`` prim, applies the
  ``OmniSensorAPI`` schema, and exposes the optical parameters (focal length, aperture,
  clipping range) through its ``.camera`` property.
* **Runtime** — ``CameraSensor`` wraps an ``RtxCamera`` object, creates a Replicator render
  product at a specified resolution, attaches annotators (``rgb``, ``distance_to_camera``,
  ``semantic_segmentation``, etc.), and provides ``get_data()`` for retrieving rendered frames
  as numpy/warp arrays.

Two specialized camera variants extend this base — ``SingleViewDepthCameraSensor`` for
stereoscopic depth simulation and ``StructuredLightCamera`` for projected-pattern depth
recovery. See :ref:`Specialized Camera Types <isaacsim_sensors_camera_specialized_types>` below.

How to Create a Camera
----------------------

|isaac-sim_short| supports creating camera prims through the GUI **Create** menu or
programmatically via the :class:`~isaacsim.sensors.experimental.rtx.RtxCamera` class.

Create from the Create Menu
^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

Create with the ``RtxCamera`` Class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``RtxCamera`` authoring class creates (or wraps) a ``Camera`` prim with the ``OmniSensorAPI`` schema applied,
sets transforms via plural-array constructor parameters (``positions``, ``translations``, ``orientations``, ``scales``),
and exposes optical parameters through its ``.camera`` property. The standalone example
``standalone_examples/api/isaacsim.sensors.experimental.rtx/create_camera_basic.py`` demonstrates
the full create-and-read workflow:

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/create_camera_basic.py

The example loads a warehouse environment, creates an ``RtxCamera`` at ``/World/camera``, attaches
``rgb`` and ``distance_to_image_plane`` annotators via ``CameraSensor``, and saves a rendered
RGB frame to disk every 100 ticks under
``_example_output_isaacsim.sensors.experimental.rtx/create_camera_basic/``. The frame at tick 100
looks like:

.. figure:: /images/isim_6.0_base_tut_external_create_camera_basic_rgb.png
    :align: center
    :width: 80%
    :alt: Rendered RGB frame from create_camera_basic.py — the Simple Warehouse environment viewed from an RtxCamera at (0, 0, 1.5) looking down the +Y axis.

    RGB frame saved by ``create_camera_basic.py`` (tick 100, 480x640).

Tick Rate
^^^^^^^^^

The ``tick_rate`` parameter (Hz) on ``RtxCamera`` controls how frequently the camera renders. A value
of ``0`` (the default) enables autotrigger mode, where the camera renders every simulation frame.
Setting a nonzero value causes the camera to render at the specified frequency independently of the
simulation step rate. This maps to the ``omni:sensor:tickRate`` prim attribute and requires the
``OmniSensorAPI`` schema to be applied to the Camera prim — ``RtxCamera`` does this automatically.

.. code-block:: python

    from isaacsim.sensors.experimental.rtx import RtxCamera

    camera = RtxCamera(path="/World/Camera", tick_rate=30.0)

``tick_rate`` is the recommended replacement for the deprecated ``frameSkipCount`` input on
``ROS2 Camera Helper``, ``ROS2 Camera Info Helper``, ``UCX Camera Helper``, and
``HSB Camera Helper`` nodes. See :ref:`isaac_sim_sensors_multitick_rendering` for the full
migration guide and the list of related known issues.

How to Collect Data from a Camera
---------------------------------

The recommended method for collecting data from a camera is to use the ``CameraSensor`` runtime class,
which wraps an ``RtxCamera`` authoring object and manages Replicator annotators on its render product.
For batched multi-camera workflows, use ``TiledCameraSensor``. For stereoscopic depth simulation, use
``SingleViewDepthCameraSensor`` (see
:ref:`Specialized Camera Types <isaacsim_sensors_camera_specialized_types>` for the full sub-page).

Annotators
^^^^^^^^^^

``CameraSensor`` accepts a list of annotator names (``rgb``, ``distance_to_camera``,
``distance_to_image_plane``, ``semantic_segmentation``, ``motion_vectors``, etc.) at construction
time and exposes the latest data through ``get_data("annotator-name")``, which returns a
``(warp.array, info_dict)`` tuple. Run the basic example to see ``rgb`` and
``distance_to_image_plane`` collection end-to-end:

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/create_camera_basic.py

To select between CPU- and CUDA-resident annotator buffers, see the standalone example
``standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_annotator_devices.py``.

Tiled / Batched Cameras
^^^^^^^^^^^^^^^^^^^^^^^

``TiledCameraSensor`` packs many cameras into a single tiled render product, which is significantly
more efficient than one render product per camera for reinforcement-learning and multi-environment
workflows. Pass an explicit list of camera prim paths (or an ``isaacsim.core.experimental.objects.Camera``
instance) plus a per-tile ``resolution``:

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_tiled.py

Single-View Depth Cameras
^^^^^^^^^^^^^^^^^^^^^^^^^

``SingleViewDepthCameraSensor`` extends ``CameraSensor`` with stereoscopic-depth simulation
post-processing (disparity, baseline, noise, outlier removal). See the
:ref:`isaacsim_sensors_camera_depth_stereoscopic_pipeline` sub-page for the full pipeline
description. End-to-end example:

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_stereoscopic_depth.py

.. _isaacsim_sensors_camera_specialized_types:

Specialized Camera Types
------------------------

Two specialized camera sensors build on ``RtxCamera`` and ``CameraSensor`` for depth and structured-light workflows:

.. toctree::
   :maxdepth: 1

   ./isaacsim_sensors_camera_depth
   ./isaacsim_sensors_camera_structured_light

Advanced Topics
---------------

.. _isaacsim_sensors_camera_calibration_and_camera_lens_distortion_models:

Calibration and Camera Lens Distortion Models
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Omniverse cameras support a variety of lens distortion models, described `here <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/cameras.html#omniverse-cameras>`_.
The ``RtxCamera`` class from ``isaacsim.sensors.experimental.rtx`` supports applying lens distortion schemas (e.g. ``OmniLensDistortionOpenCvFisheyeAPI``, ``OmniLensDistortionOpenCvPinholeAPI``) via the ``schemas`` parameter and setting distortion coefficients via the ``attributes`` parameter.

Calibration toolkits like OpenCV normally provide the calibration parameters as an intrinsic matrix and distortion coefficients. Omniverse includes native renderer support for the OpenCV pinhole and
OpenCV fisheye lens distortion models. |isaac-sim_short| provides two standalone examples demonstrating the use of ``RtxCamera`` with OpenCV lens distortion models,
located at ``standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_opencv_pinhole.py`` and ``standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_opencv_fisheye.py``.

.. note::
    - Previously, the ``Camera`` class included APIs to approximate OpenCV pinhole and fisheye models distortion parameters by setting coefficients for the ``fisheyePolynomial`` distortion model. Now that OpenCV lens distortion models are natively supported, those APIs have been deprecated.
    - `Omniverse RTX Camera Projection Attributes <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/cameras.html#rtx-camera-projection-attributes-deprecated>`_ have been deprecated as of |isaac-sim_short| 5.0, in favor of the ``OmniLensDistortion`` `schemata <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/cameras.html#omnilensdistortion-schemata>`_. The deprecated attributes are still visible in the UI in the ``Fisheye Lens`` panel when selecting a Camera prim, but will be ignored if you have set an ``OmniLensDistortion`` schema instead. Follow the instructions in `"How To Add Schemata to Cameras" <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/cameras.html#omnilensdistortion-schemata>`_ to see how to update Camera prim attributes for the new schemata in the UI.

.. warning::
    In |isaac-sim_short| 6.0, enabling arbitrary distortion models using a generalized projection model by
    applying the ``OmniLensDistortionLutAPI`` schema to Camera prims does not correctly function, and if set,
    the renderer will fallback to the default pinhole model. Instead, use the deprecated Omniverse RTX Camera
    Projection Attributes referenced above to specify an arbitrary distortion model. This will be fixed in a future release.

OpenCV Fisheye
~~~~~~~~~~~~~~

Run the standalone example to create an ``RtxCamera`` with the ``OmniLensDistortionOpenCvFisheyeAPI`` schema applied:

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_opencv_fisheye.py

After running the example and setting the viewport to the newly-created camera, validate that you see an image like the one below.

.. image:: /images/isim_5.0_full_ext-isaacsim.sensors.camera-1.1.0_viewport_camera-opencv-fisheye-test.png
    :align: center

OpenCV Pinhole
~~~~~~~~~~~~~~

Run the standalone example to create an ``RtxCamera`` with the ``OmniLensDistortionOpenCvPinholeAPI`` schema applied:

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_opencv_pinhole.py

After running the example and setting the viewport to the newly-created camera, you should see an image like the one below.

.. image:: /images/isim_5.0_full_ext-isaacsim.sensors.camera-1.1.0_viewport_camera-opencv-pinhole-test.png
    :align: center

Extrinsic Calibration
~~~~~~~~~~~~~~~~~~~~~

Extrinsic calibration parameters are normally provided by the calibration toolkits in a form of a transformation matrix. The convention between the axis and rotation order is important and it varies between the toolkits.

To set the extrinsic parameters for the individual camera sensor, use the following example to convert the transformation matrix from the calibration toolkit to the Isaac Sim units:

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_camera/extrinsic_calibration.py
    :language: python
    :start-after: # -- End test setup --

As an alternative, the camera sensor can be attached to a prim. In that case, the camera sensor will inherit the position and orientation from the prim.

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_camera/depends_if_translation_or_position_is_specified.py
    :language: python

Exposing the ISP Camera Pipeline
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``omni.sensors.nv.camera`` extension `simulates the camera sensor and Image Signal Processor (ISP) pipeline <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/cameras.html#omni-sensors-nv-camera-extension>`_.
|isaac-sim_short| includes a standalone example that configures the ISP pipeline via the ``OmniSensorGenericCameraCoreAPI`` USD schema and saves the introspection output from every pipeline stage as viewable images.
You can use these outputs to test your own ISP against images rendered in RTX, or compare them with the Omniverse-simulated ISP output.

Refer to the `extension documentation <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/cameras.html#omni-sensors-nv-camera-extension>`_ for details on individual pipeline stages and schema attributes.

.. note::
    The sample ISP program bundled with ``omni.sensors.nv.camera`` is only available on Linux x86_64.
    Running the example on any other platform will print an informative message and exit early.
    If you have your own ISP program for a different platform, update the ``_isp_program_path``
    variable in the script to point to it, and comment-out the platform check.

Run the example:

.. code-block:: bash

   ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_isp_pipeline.py

The example renders 20 frames and saves output from each ISP stage to the ``camera_isp_pipeline_outputs`` directory.
The pipeline stages, in order, are described below.

**HDR texture read** --- the raw HDR radiance buffer read from the renderer before any sensor processing.

.. image:: /images/isim_6.0_base_tut_external_camera_isp_pipeline_texread.png
    :alt: HDR texture read output from the ISP pipeline example
    :align: center
    :width: 80%

**Color correction** --- applies black-level subtraction, white-balance gains, a 3x3 color-correction matrix, and sensor-response scaling.

.. image:: /images/isim_6.0_base_tut_external_camera_isp_pipeline_color.png
    :alt: Color-corrected output from the ISP pipeline example
    :align: center
    :width: 80%

**CFA encoding** --- encodes the RGB image into a single-channel Bayer mosaic using the configured Color Filter Array pattern (GRBG in this example).

.. image:: /images/isim_6.0_base_tut_external_camera_isp_pipeline_cfa.png
    :alt: CFA-encoded Bayer output from the ISP pipeline example
    :align: center
    :width: 80%

**Noise simulation** --- adds Gaussian and shot noise to the Bayer image to approximate real sensor behavior.

.. image:: /images/isim_6.0_base_tut_external_camera_isp_pipeline_noise.png
    :alt: Noise-simulated Bayer output from the ISP pipeline example
    :align: center
    :width: 80%

**Companding** --- applies a piecewise-linear tone curve that compresses the high-dynamic-range Bayer data into a lower bit depth.

.. image:: /images/isim_6.0_base_tut_external_camera_isp_pipeline_comp.png
    :alt: Companded output from the ISP pipeline example
    :align: center
    :width: 80%

**ISP output** --- the fully processed image after the on-chip ISP program runs (demosaic, denoise, tone-map, and color grading).

.. image:: /images/isim_6.0_base_tut_external_camera_isp_pipeline_isp_output.png
    :alt: ISP-processed output from the ISP pipeline example
    :align: center
    :width: 80%

**YUV conversion** --- the final ISP output converted from RGB to YUV color space.

.. image:: /images/isim_6.0_base_tut_external_camera_isp_pipeline_yuv.png
    :alt: YUV-converted output from the ISP pipeline example
    :align: center
    :width: 80%

.. _isaacsim_sensors_camera_creating_camera_sensors:

Camera Sensor Rigs
^^^^^^^^^^^^^^^^^^

The camera sensor rig is a collection of camera sensors that are attached to a single prim. It can be assembled from the individual sensors, that are either created manually or derived from the calibration parameters.

This will be a short discussion on how we created a digital twin of the RealSense™ Depth Camera D455.  The USD for the camera can be found in the content folder as: ``/Isaac/Sensors/RealSense/D455/rsd455.usd``.

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

.. _isaac_sim_app_tutorial_camera_inspector_extension:

Camera Inspector Extension
^^^^^^^^^^^^^^^^^^^^^^^^^^

The Camera Inspector Extension allows you to:

* Create multiple viewports for each camera
* Check camera coverage
* Get and set camera poses in the desired frames

Launching Extension
~~~~~~~~~~~~~~~~~~~

To open the Camera Inspector extension:

#. Go to the Menu Bar.
#. Select **Tools > Sensors > Camera Inspector**.
#. After launching the extension, verify that you can see your camera in the dropdown.
#. When adding a new camera, you must click the Refresh button to ensure that the extension finds this new camera.
#. Select the camera you want to inspect.

Camera State Textbox
~~~~~~~~~~~~~~~~~~~~

.. image:: /images/isim_4.5_base_ref_gui_camera_status_textbox.png
    :align: center

The **Camera State** textbox near the top of the extension provides a convenient way to copy the position and orientation of your camera directly into code.
Click the copy icon on the right of the textbox to copy to your clipboard.

Creating a Viewport
~~~~~~~~~~~~~~~~~~~

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

Standalone Examples
-------------------

For end-to-end examples of creating and collecting data from camera sensors, refer to the following.

**Basic Creation and Visualization**

.. code-block:: bash

    # Basic camera creation with rgb + distance_to_image_plane annotators in a warehouse scene
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/create_camera_basic.py

**Specialized Cameras**

.. code-block:: bash

    # Single-view stereoscopic depth sensor
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/create_camera_depth_sensor.py
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_stereoscopic_depth.py

    # Structured light camera
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_structured_light.py

**Batched / Tiled**

.. code-block:: bash

    # TiledCameraSensor for multi-camera batched rendering
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_tiled.py

**Calibration**

.. code-block:: bash

    # OpenCV pinhole and fisheye lens distortion models on RtxCamera
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_opencv_pinhole.py
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_opencv_fisheye.py

**Annotator Device Selection**

.. code-block:: bash

    # CPU vs CUDA-resident annotator buffers
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_annotator_devices.py

**ISP Pipeline**

.. code-block:: bash

    # Per-stage ISP pipeline introspection (Linux x86_64 only)
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_isp_pipeline.py

**ROS 2 Integration**

.. code-block:: bash

    # Publish camera frames over ROS 2
    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/camera_ros.py

.. _isaacsim_sensors_camera_migration:

Migrating from ``isaacsim.sensors.camera`` to ``isaacsim.sensors.experimental.rtx``
-----------------------------------------------------------------------------------

The deprecated ``isaacsim.sensors.camera`` extension is replaced by ``isaacsim.sensors.experimental.rtx``. The replacement keeps the same camera concepts (single camera, batched camera views, single-view depth sensor) but reshapes the Python API to mirror ``isaacsim.sensors.experimental.physics`` — array-form transforms, no command-based creation, and a split between authoring (``RtxCamera``) and runtime (``CameraSensor``, ``TiledCameraSensor``, ``SingleViewDepthCameraSensor``) classes.

.. _isaacsim_sensors_camera_concept_mapping:

Concept mapping
^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - ``isaacsim.sensors.camera`` (deprecated)
     - ``isaacsim.sensors.experimental.rtx``
   * - ``Camera(prim_path, name, frequency, dt, resolution, position, orientation, translation, render_product_path, annotator_device)``
     - ``CameraSensor(RtxCamera(path, ...), resolution=(W, H), annotators=[...])``. The ``frequency`` / ``dt`` knobs map to ``RtxCamera(tick_rate=...)`` (Hz). ``annotator_device`` maps to the CPU vs CUDA selection ``CameraSensor`` performs in ``attach_annotators``.
   * - Singular ``position=`` / ``orientation=`` / ``translation=`` constructor args
     - Plural ``positions=[[...]]`` / ``orientations=[[...]]`` / ``translations=[[...]]`` arrays on ``RtxCamera``. Shape ``(N, 3)`` / ``(N, 4)``; only ``N=1`` is supported per camera.
   * - ``name=`` constructor parameter
     - Removed (was unused).
   * - ``Camera.add_*_to_frame()`` / ``Camera.get_current_frame()`` (legacy frame-dict APIs)
     - ``CameraSensor(annotators=[...])`` plus ``CameraSensor.get_data("annotator-name")``. Each annotator is requested explicitly; data is returned per annotator instead of as a frame dict.
   * - ``Camera`` ``fisheyePolynomial`` distortion APIs
     - ``RtxCamera(schemas=["OmniLensDistortionOpenCvFisheyeAPI"], attributes={...})`` (or the OpenCV pinhole equivalent). See :ref:`isaacsim_sensors_camera_calibration_and_camera_lens_distortion_models` above for the supported schemas and the deprecation note on the legacy distortion attributes.
   * - ``CameraView(prim_paths_expr, name, camera_resolution, output_annotators, positions, translations, orientations, scales, visibilities, reset_xform_properties)``
     - ``TiledCameraSensor(paths=[...], resolution=(W, H), annotators=[...])``. The ``prim_paths_expr`` regex selection becomes an explicit list of camera prim paths (or an ``isaacsim.core.experimental.objects.Camera`` instance). ``output_annotators`` maps directly to ``annotators=``.
   * - ``SingleViewDepthSensor(prim_path, asset_path, position, translation, orientation)``
     - ``SingleViewDepthCameraSensor(RtxCamera.create(path, usd_path=asset_path, translations=[[...]], orientations=[[...]]), resolution=(W, H), annotators=["depth_sensor_distance", "depth_sensor_imager", "depth_sensor_point_cloud_color", "depth_sensor_point_cloud_position"])``. Post-processing setters (``set_sensor_baseline``, ``set_sensor_disparity_confidence``, etc.) keep the same names.

.. _isaacsim_sensors_camera_code_examples:

Code examples
^^^^^^^^^^^^^

**Camera — create and read RGB**

Old (``isaacsim.sensors.camera``):

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_camera/migration_camera_old.py
   :language: python

New (``isaacsim.sensors.experimental.rtx``):

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_camera/migration_camera_new.py
   :language: python

**CameraView → TiledCameraSensor — batched read**

Old (``isaacsim.sensors.camera``):

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_camera/migration_cameraview_old.py
   :language: python

New (``isaacsim.sensors.experimental.rtx`` — explicit path list, or pass a ``Camera`` object):

.. literalinclude:: ../snippets/sensors/isaacsim_sensors_camera/migration_tiledcamera_new.py
   :language: python

For the per-class API surface, see the **Overview** and **How to Collect Data from a Camera** sections above. For the broader RTX-sensor migration (``isaacsim.sensors.rtx`` → ``isaacsim.sensors.experimental.rtx`` for Lidar / Radar / Acoustic), see :ref:`isaacsim_sensors_rtx_migration`.
