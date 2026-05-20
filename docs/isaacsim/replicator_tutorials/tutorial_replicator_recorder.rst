..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_replicator_recorder:

==========================================
Synthetic Data Recorder
==========================================

This tutorial introduces the Synthetic Data Recorder for |isaac-sim_short|, which is a GUI extension for recording synthetic data with the possibility of using :doc:`custom writers <extensions:ext_replicator/custom_writer>` to record the data in various formats.

The Synthetic Data Recorder requires assets to be :doc:`semantically labelled <extensions:ext_replicator/semantics_schema_editor>` for all of the annotators to work correctly. The recorder uses the ``BasicWriter`` by default with access to most common :doc:`annotators <extensions:ext_replicator/annotators_details>`.


Getting Started
-------------------

The UI window can be opened from the main menu using **Tools** > **Replicator** > **Synthetic Data Recorder**.

This tutorial uses the following stage as an example:

::

    https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0
    /Isaac/Samples/Replicator/Stage/full_warehouse_worker_and_anim_cameras.usd

The stage asset can be found in the **Content Browser** under **Isaac Sim** > **Samples** > **Replicator** > **Stage** > **full_warehouse_worker_and_anim_cameras.usd**, or can be loaded using by inserting the whole URL in the path field.

.. figure:: /images/isim_5.0_replicator_tut_gui_sd_recorder_stage.jpg
    :align: center
    :alt: Synthetic Data Recorder

The example stage comes preloaded with semantic annotations and multiple cameras. Some of the included cameras are animated to move around the scene when running the simulation. To create custom camera movement animations, review the :doc:`Camera Animation Tutorial <extensions:ext_animation-timeline>`.

Basic Usage
-------------------

The recorder is split into two main parts:

* the **Writer** frame - containing sensor, data, and output parameters
* the **Control** frame - containing the recording functionalities such as start, stop, pause, and parameters such as the number of frames to execute

.. figure:: /images/isim_4.5_replicator_tut_gui_sd_recorder_window.jpg
    :align: center
    :width: 50%
    :alt: Synthetic Data Recorder Window


Writer Frame
###############

The **Writer** frame provides access to **Render Products**, **Parameters**, **Output**, and **Config** options.

The **Render Products** frame allows the creation of a list of render product entries using the **Add New Render Product** button. By default, a new entry is added to the list using the active viewport camera as its camera path (see left figure). If cameras are selected in the stage viewer, these are added to the render products list (see right figure). The render products list can include the same camera path multiple times, with each instance having a different resolution. All entry values, such as camera path or resolution, can be manually edited in the input fields.

.. figure:: /images/isim_4.5_replicator_tut_gui_sd_recorder_rp.jpg
    :align: center
    :alt: Synthetic Data Recorder Render Products


The **Parameters** frame offers a choice between the default built-in Replicator writer (``BasicWriter``) and a custom writer. Default writer parameters, primarily annotators, can be selected from the checkbox list. Parameters for custom writers, which are unknown beforehand, must be provided in the form of a JSON file containing all required parameters. The path to the JSON file is entered in the **Parameters Path** input field.

.. figure:: /images/isim_4.5_replicator_tut_gui_sd_recorder_writer_params.jpg
    :align: center
    :alt: Synthetic Data Recorder Parameters

The **Output** frame (left figure) specifies the working directory path where the data is saved, along with the folder name for the current recording. The output folder name is incremented in case of conflicts. The recorder also supports writing to S3 buckets by enabling **Use S3**, entering the required fields, and ensuring AWS credentials are properly configured.

.. Note:: When writing to S3, the **Increment** folder naming feature is not supported and defaults to **Timestamp**.

The **Config** frame (right figure) allows loading and saving the GUI writer state as a JSON configuration file. By default, the extension loads the most recently used configuration state.

.. figure:: /images/isim_4.5_replicator_tut_gui_sd_recorder_out_conf.jpg
    :align: center
    :alt: Synthetic Data Recorder Output and Config


Control Frame
###############

The **Control** frame contains the recording functionalities such as Start/Stop and Pause/Resume, and parameters such as the number of frames to record or the number of subframes to render for each recorded frame.

* The **Start** button creates a writer, given the selected parameters, and starts the recording.
* The **Stop** button stops the recording and clears the writer.
* The **Pause** button pauses the recording without clearing the writer.
* The **Resume** button resumes the recording.
* The **Number of Frames** input field sets the number of frames to record, after which the recorder is stopped and the writer cleared. If the value is set to ``0``, the recording runs indefinitely or until the **Stop** button is pressed.
* The **RTSubframes** field sets the number of additional subframes to render for each per frame. This can be used if randomized materials are not loaded in time or if temporal rendering artifacts (such as ghosting) are present due to objects being teleported.
* The **Control Timeline** checkbox starts, stops, pauses, and resumes the timeline together with the recorder.
* The **Verbose** checkbox enables verbose logging for the recorder (events such as start, stop, pause, resume, and the number of frames recorded).

.. figure:: /images/isim_4.5_replicator_tut_gui_sd_recorder_control.jpg
    :align: center
    :alt: Synthetic Data Recorder Output and Config
    :width: 60%

.. Note:: To improve the rendering quality, or to avoid any rendering artifacts caused by low lighting conditions or fast-moving objects, increase the **RTSubframes** parameter. This renders multiple subframes for each frame, thereby improving the quality of recorded data at the expense of longer rendering times per frame. For more details, see the :ref:`subframes <subframes examples>` documentation.


Custom Writer Example
------------------------

To support custom data formats, the custom writer can be registered and loaded from the GUI. In this example, a custom writer called ``MyCustomWriter`` is registered using the :ref:`Script Editor <script-editor>` for use with the recorder.

The Synthetic Data Recorder initializes the selected disk or cloud backend, then calls ``writer.initialize(backend=..., **parameters)``. Starting in recent |isaac-sim_short| / Replicator releases, those keyword arguments are applied when the writer is constructed. Custom writers must therefore accept a ``backend`` argument (the configured ``DiskBackend`` or ``S3Backend`` instance) or accept arbitrary keyword arguments with ``**kwargs``. They should write using that backend rather than constructing a separate ``BackendDispatch`` from a raw output path when ``backend`` is supplied.

.. raw:: html

    <details open>
    <summary>MyCustomWriter</summary>

.. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_recorder/register_my_custom_writer.py
    :language: python
    :start-after: __doc_snippet_mycustomwriter_begin__
    :end-before: __doc_snippet_mycustomwriter_end__

.. raw:: html

    </details>

.. raw:: html

    <details open>
    <summary>my_params.json</summary>

.. code-block:: json
    :linenos:

    {
        "rgb": true,
        "normals": true
    }

.. raw:: html

    </details>

.. figure:: /images/isim_4.5_replicator_tut_gui_sd_recorder_custom_writer.jpg
    :align: center
    :alt: Synthetic Data Recorder Custom Writer


Data Visualization Writer
###########################

The **Data Visualization** writer is a custom writer that can be used to visualize the annotation data on top of rendered images. The writer and its implementation details can be found in ``/isaacsim.replicator.writers/python/scripts/writers/data_visualization_writer.py``, and can be imported using ``from isaacsim.replicator.writers import DataVisualizationWriter``. The custom writer can be selected from the **Parameters** frame and its parameters can be loaded from a JSON file using the **Parameters Path** input field. Here is an example JSON file that can be used to parameterize the writer:

.. raw:: html

    <details open>
    <summary>my_data_visualization_params.json</summary>

.. code-block:: json
    :linenos:

    {
        "bounding_box_2d_tight": true,
        "bounding_box_2d_tight_params": {
            "background": "rgb",
            "outline": "green",
            "fill": null
        },
        "bounding_box_2d_loose": true,
        "bounding_box_2d_loose_params": {
            "background": "normals",
            "outline": "red",
            "fill": null
        },
        "bounding_box_3d": true,
        "bounding_box_3d_params": {
            "background": "rgb",
            "fill": "blue",
            "width": 2
        }
    }

.. raw:: html

    </details>

And the resulting data:

.. figure:: /images/isim_4.5_replicator_tut_gui_sd_recorder_datavis_writer.jpg
    :align: center
    :alt: Synthetic Data Recorder Visualization Writer

For more information on the supported parameters, see the class docstring:

.. raw:: html

    <details open>
    <summary>DataVisualizationWriter class docstring</summary>

.. code-block:: python

    """Data Visualization Writer

    This writer can be used to visualize various annotator data.

    Supported annotators:
    - bounding_box_2d_tight
    - bounding_box_2d_loose
    - bounding_box_3d

    Supported backgrounds:
    - rgb
    - normals

    Args:
        output_dir (str):
            Output directory for the data visualization files forwarded to the backend writer.
        bounding_box_2d_tight (bool, optional):
            If True, 2D tight bounding boxes will be drawn on the selected background (transparent by default).
            Defaults to False.
        bounding_box_2d_tight_params (dict, optional):
            Parameters for the 2D tight bounding box annotator. Defaults to None.
        bounding_box_2d_loose (bool, optional):
            If True, 2D loose bounding boxes will be drawn on the selected background (transparent by default).
            Defaults to False.
        bounding_box_2d_loose_params (dict, optional):
            Parameters for the 2D loose bounding box annotator. Defaults to None.
        bounding_box_3d (bool, optional):
            If True, 3D bounding boxes will be drawn on the selected background (transparent by default). Defaults to False.
        bounding_box_3d_params (dict, optional):
            Parameters for the 3D bounding box annotator. Defaults to None.
        frame_padding (int, optional):
            Number of digits used for the frame number in the file name. Defaults to 4.

    """

.. raw:: html

    </details>

Replicator Randomized Cameras
--------------------------------

To take advantage of Replicator randomization techniques, randomized cameras can be loaded using the :ref:`Script Editor <script-editor>` before starting the recorder to run scene randomizations during recording. In this example a randomized camera is created using the Replicator API. This can be attached as a render product to the recorder and for each frame the camera is randomized with the given parameters.

.. code-block:: python

    import omni.replicator.core as rep

    camera = rep.create.camera()
    with rep.trigger.on_frame():
        with camera:
            rep.modify.pose(
                position=rep.distribution.uniform((-5, 5, 1), (-1, 15, 5)),
                look_at="/Root/Warehouse/SM_CardBoxA_3",
            )

.. figure:: /images/isim_4.5_replicator_tut_gui_sd_recorder_rep_cam.jpg
    :align: center
    :alt: Synthetic Data Recorder Custom Writer


Recording Loop Overview
------------------------

The **Synthetic Data Recorder** is a GUI extension for |isaac-sim_short| that uses the ``BasicWriter`` or custom Replicator writers for capturing data. Its implementation is located in ``/isaacsim.replicator.synthetic_recorder/isaacsim/replicator/synthetic_recorder/synthetic_recorder.py`` and utilizes the ``orchestrator.step(rt_subframes, pause_timeline, delta_time)`` function to manage the recording process. This function ensures that recorded frames remain synchronized with the stage by waiting for any "frames in flight" from the renderer. For integration with the UI, the recorder uses the asynchronous version of this function: ``step_async``.

.. code-block:: python

    while self._current_frame < num_frames:
        timeline = omni.timeline.get_timeline_interface()

        if self.control_timeline and not timeline.is_playing():
            timeline.play()
            timeline.commit()

        await rep.orchestrator.step_async(rt_subframes=self.rt_subframes, delta_time=None, pause_timeline=False)

        self._current_frame += 1

The recording loop offers flexibility for different use cases. It can advance the timeline for dynamic scenes, such as simulations or animations, or operate without advancing the timeline for static captures. This approach enables recording scenarios like randomizing views, adjusting lighting conditions, or repositioning objects.
