..
   Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_tutorial_replicator_getting_started:

=======================
Getting Started Scripts
=======================

This guide outlines a series of example scripts designed to facilitate typical |isaac-sim_short| Replicator workflows. The examples include both "asynchronous" usage through the :ref:`Script Editor <script-editor>` and "synchronous" usage through the :ref:`Standalone Application <standalone-application>`. These scripts cover simulation-based scenarios and configurations for synthetic data generation (SDG).

Prerequisites
-------------

Before starting with these examples, ensure you have:

- Basic understanding of Python programming
- Familiarity with USD (Universal Scene Description) concepts
- Access to NVIDIA Omniverse™ Isaac Sim
- Sufficient disk space for data capture (varies based on resolution and number of frames)
- GPU with sufficient memory for rendering (recommended: 8GB+)

Setup and Configuration
-----------------------

This section introduces configurations typically used in such workflows.


Orchestrator Step Function
--------------------------

In Replicator, the ``orchestrator.step()`` function is used to trigger the entire synthetic data generation (SDG) process, including executing randomizations and capturing data. For |isaac-sim_short| workflows, this function is used solely to trigger data capture only, with randomization triggers assigned to custom events and manually activated.

The ``step()`` function has the following signature:

.. code-block:: python

    rep.orchestrator.step(rt_subframes: int = -1, pause_timeline: bool = True, delta_time: float = None, wait_for_render: bool = True)

Where:

- ``rt_subframes``: Specifies the number of subframes to render. A value greater than 0 enables subframe generation, reducing rendering artifacts or allowing materials to load fully.
- ``pause_timeline``: Pauses the timeline (if currently playing) after the step if set to ``True``.
- ``delta_time``: Specifies the time to advance the timeline during a step. Defaults to the timeline's rate if ``None``.
- ``wait_for_render``: If ``True``, the function blocks until the renderer completes the current frame before returning. Defaults to ``True``.

More details on graph-based replicator randomizers can be found in the :doc:`Randomizer Details <extensions:ext_replicator/randomizer_details>`, and for custom |isaac-sim_short| or USD API-based randomizations, refer to the :ref:`Isaac Sim Randomizers Guide <isaac_sim_app_tutorial_replicator_isaac_randomizers>`.

Capture on Play Flag
--------------------

By default, Replicator captures data every frame during playback. For |isaac-sim_short| workflows, data capture is configured to occur at user-defined frames using the ``step()`` function. To achieve this, the capture-on-play flag is disabled:

.. code-block:: python

    import omni.replicator.core as rep

    rep.orchestrator.set_capture_on_play(False)
    # OR
    import carb.settings

    carb.settings.get_settings().set("/omni/replicator/captureOnPlay", False)

.. _isaac_sim_replicator_getting_started_subframes:

RT Subframes Parameter
----------------------

In scenarios where reducing temporal rendering artifacts is needed, such as ghosting caused by quickly moving or teleporting assets, or under weak lighting conditions, RTSubframes can be used to render the same frame multiple times. This pauses the simulation and renders additional subframes, improving rendering quality.

The ``rt_subframes`` parameter is typically set during the capture request in the ``step()`` function but can also be configured globally:

.. code-block:: python

    # Set the rt_subframes parameter for a specific capture step
    rep.orchestrator.step(rt_subframes=4)

    # Set the rt_subframes parameter globally
    import carb.settings

    carb.settings.get_settings().set("/omni/replicator/RTSubframes", 4)

Refer to the :ref:`documentation examples <subframes examples>` for additional details.

DLSS Quality Mode for SDG
-------------------------

When using Replicator for synthetic data generation (SDG) workflows, it is recommended to set the DLSS model to Quality mode to avoid rendering artifacts. At lower resolutions (especially below 600x600), the default Performance mode may cause issues such as transparent or incorrectly rendered edges in the generated images.

.. code-block:: python

    import carb.settings

    # Set DLSS to Quality mode (2) for best SDG results (Options: 0 (Performance), 1 (Balanced), 2 (Quality), 3 (Auto))
    carb.settings.get_settings().set("/rtx/post/dlss/execMode", 2)

.. _isaac_sim_replicator_getting_started_wait_for_render:

Wait for Render Parameter
-------------------------

By default, the ``step()`` function blocks until the renderer finishes producing the current frame before returning. Setting ``wait_for_render=False`` decouples the capture request from the rendering pipeline, allowing the next randomization to begin immediately while the previous frame is still being rendered. This can significantly improve throughput in workflows where the captured data does not need to exactly match the current simulation state at the time the ``step()`` call returns.

.. code-block:: python

    # Default behavior: blocks until the frame is rendered
    rep.orchestrator.step(wait_for_render=True)

    # Non-blocking: returns immediately, allowing the next randomization to start
    rep.orchestrator.step(wait_for_render=False)

.. note::

    When using ``wait_for_render=False``, the annotation and writer data may correspond to a previous frame rather than the frame triggered by the most recent ``step()`` call. Use this mode only when strict frame-to-data correspondence is not required.

.. _isaac_sim_replicator_getting_started_write_to_fabric:

Write to Fabric Mode
--------------------

Fabric is the runtime data layer that the renderer reads from directly. By default, Replicator writes attribute changes (such as positions, rotations, and colors) to the USD stage, which are then synchronized to Fabric before rendering. Enabling write-to-fabric mode bypasses the USD stage and writes changes directly to Fabric, reducing the overhead of USD-to-Fabric synchronization and improving randomization performance.

.. code-block:: python

    import carb.settings

    # Enable write-to-fabric mode
    carb.settings.get_settings().set("/exts/omni.replicator.core/enableWriteToFabric", True)

.. note::

    Because changes are written directly to Fabric and bypass the USD stage, they will not be reflected in the USD stage or persisted when saving the scene. This mode is intended for transient randomizations during data generation, not for permanent scene modifications.

Custom Event Randomizations
---------------------------

To provide flexibility, replicator randomizers can be triggered independently using custom events. This is achieved by registering the randomizer trigger through ``trigger.on_custom_event`` and activating it with ``utils.send_og_event``. For instance, the following example creates a randomization graph for a dome light and randomizes its color. The randomization graph is then triggered manually through its custom event name. The ``step()`` function does not trigger this randomization graph.

.. code-block:: python

    # Create a randomization graph for creating a dome light and randomizing its color
    with rep.trigger.on_custom_event(event_name="randomize_dome_light_color"):
        rep.create.light(light_type="Dome", color=rep.distribution.uniform((0, 0, 0), (1, 1, 1)))

    # Trigger the randomization graph using its custom event name
    rep.utils.send_og_event(event_name="randomize_dome_light_color")

An example snippet for custom events is also available :ref:`here <replicator_isaac_snippets_custom_event>`.

Wait Until Complete
-------------------

Ensuring that all data is fully written to disk before closing the application is essential to prevent data loss. High data throughput, such as from multiple cameras or large resolutions, may introduce I/O bottlenecks; refer to the :doc:`I/O Optimization Guide <extensions:ext_replicator/io_guidelines>` for strategies to mitigate such issues.

The ``wait_until_complete`` function ensures that all writing tasks are finalized by waiting for the writer backend to complete its operations. This process allows the application to continue updating until all writing tasks are complete, safeguarding against potential data loss.

.. code-block:: python

    from omni.replicator.core import BackendDispatch
    import omni.kit.app

    async def wait_until_complete():
        while not BackendDispatch.is_done_writing():
            await omni.kit.app.get_app().next_update_async()

Alternatively, use the documented helper functions: ``rep.orchestrator.wait_until_complete()`` for synchronous contexts or ``await rep.orchestrator.wait_until_complete_async()`` for asynchronous contexts.

Examples
---------

Data Capture: BasicWriter
#########################

This example demonstrates how to use the ``BasicWriter`` for data capture with RGB and bounding box annotators. It sets up a scene with a cube and a dome light, attaches semantic labels to the cube, and saves captured data to disk. The standalone example can also be run directly (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.replicator.examples/sdg_getting_started_01.py

.. tab-set::

    .. tab-item:: Script Editor

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_getting_started/sdg_getting_started_01_script_editor.py
            :language: python
            :lines: 16-

    .. tab-item:: Standalone Application

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_getting_started/sdg_getting_started_01.py
            :language: python
            :lines: 16-

The output directory will contain the captured data, including RGB images and bounding box annotations in ``.npy`` and ``.json`` formats:

.. figure:: /images/isim_4.5_replicator_tut_external_getting_started_01.jpg
    :align: center


Custom Writer and Annotators with Multiple Cameras
#####################################################

This example demonstrates data capture by creating a custom writer to access annotator data such as camera parameters and 3D bounding boxes. It configures two cameras (custom and viewport perspective), uses annotators to access data directly, writes data to disk using ``PoseWriter``. The standalone example can also be run directly (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.replicator.examples/sdg_getting_started_02.py

.. tab-set::

    .. tab-item:: Script Editor

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_getting_started/sdg_getting_started_02_script_editor.py
            :language: python
            :lines: 16-

    .. tab-item:: Standalone Application

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_getting_started/sdg_getting_started_02.py
            :language: python
            :lines: 16-

The output directory will contain the captured data, including RGB with the 3D bounding box annotations as overlays together with ``.json`` files with the frame data. The annotator and custom writer data is printed to the terminal.

.. figure:: /images/isim_4.5_replicator_tut_external_getting_started_02.jpg
    :align: center


Custom Randomizations: Replicator Graph and USD API
####################################################

This example demonstrates creating a custom randomization using Replicator's graph-based randomizers triggered by custom events and a custom USD API-based randomization. A dome light's color is randomized through custom events, while a cube's location is randomized through USD API. Data is captured using the ``BasicWriter`` with semantic segmentation. The standalone example can also be run directly (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.replicator.examples/sdg_getting_started_03.py

.. tab-set::

    .. tab-item:: Script Editor

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_getting_started/sdg_getting_started_03_script_editor.py
            :language: python
            :lines: 16-

    .. tab-item:: Standalone Application

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_getting_started/sdg_getting_started_03.py
            :language: python
            :lines: 16-

The output directory will contain the RGB and semantic segmentation images with the captured data. The cube is randomized each capture, while the dome light color is randomized every second capture.

.. figure:: /images/isim_4.5_replicator_tut_external_getting_started_03.jpg
    :align: center


Event-Triggered Data Capture: Timeline and Simulation
######################################################

This example shows how to capture simulation data when specific conditions are met. A cube and sphere are dropped in a physics simulation, and data is captured at specific intervals based on the cube's height. The timeline is paused during capture to ensure data consistency. The standalone example can also be run directly (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.replicator.examples/sdg_getting_started_04.py

.. tab-set::

    .. tab-item:: Script Editor

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_getting_started/sdg_getting_started_04_script_editor.py
            :language: python
            :lines: 16-

    .. tab-item:: Standalone Application

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_getting_started/sdg_getting_started_04.py
            :language: python
            :lines: 16-

The output directory will contain the RGB and semantic segmentation images with the captured data at specific simulation times (cube drop height intervals) and the cube hidden during capture. During every second capture with the cube hidden, the timeline will not advance (``delta_time=0.0``) ensuring the same simulation state can be captured multiple times.

.. figure:: /images/isim_4.5_replicator_tut_external_getting_started_04.jpg
    :align: center


Batch Randomization with Performance Optimization
##################################################

This example demonstrates batch creation and randomization of 100 cubes using the functional API and ``ReplicatorRNG``. It runs three configurations to compare performance: default (``wait_for_render=True``), non-blocking capture (``wait_for_render=False``), and non-blocking capture with :ref:`write-to-fabric <isaac_sim_replicator_getting_started_write_to_fabric>` enabled. Each run prints per-step randomization and capture timings as well as the total duration including ``wait_until_complete``, illustrating the impact of :ref:`wait_for_render <isaac_sim_replicator_getting_started_wait_for_render>` and :ref:`write-to-fabric <isaac_sim_replicator_getting_started_write_to_fabric>` on throughput. The standalone example can also be run directly (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.replicator.examples/sdg_getting_started_05.py

.. tab-set::

    .. tab-item:: Script Editor

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_getting_started/sdg_getting_started_05_script_editor.py
            :language: python
            :lines: 16-

    .. tab-item:: Standalone Application

        .. literalinclude:: ../../../source/standalone_examples/api/isaacsim.replicator.examples/sdg_getting_started_05.py
            :language: python
            :lines: 16-

Each configuration writes its output to a separate directory. The terminal output shows per-step randomization and capture durations (in milliseconds) and total time, allowing direct comparison of the three modes.

Troubleshooting
---------------

For troubleshooting information related to the Getting Started Scripts, refer to the :ref:`Getting Started Scripts Issues <isaac_sim_replicator_troubleshooting_getting_started>` section in the Replicator Troubleshooting page.

Next Steps
----------

After completing these examples, consider exploring:

1. Advanced randomizations using the :doc:`Randomizer Details <extensions:ext_replicator/randomizer_details>`
2. Custom annotators for specialized data capture
3. Distributed data generation using multiple GPUs
4. Integration with machine learning pipelines
5. Advanced physics-based simulations

For more information, refer to:
- :doc:`Replicator Documentation <extensions:ext_replicator/basic_functionalities>`
- :ref:`Isaac Sim Randomizers Guide <isaac_sim_app_tutorial_replicator_isaac_randomizers>`
- :doc:`I/O Optimization Guide <extensions:ext_replicator/io_guidelines>`