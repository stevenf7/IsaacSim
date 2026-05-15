..
   Copyright (c) 2024-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_tutorial_replicator_sdg_workflows:

=============
SDG Workflows
=============

This tutorial walks through two complete synthetic data generation (SDG) scripts. Each one authors a USD scene, randomizes it, runs the simulation, and writes annotated images to disk through a ``BasicWriter``. The audience is a developer who is comfortable with rigid-body simulation and USD scene graphs and wants to see the Replicator API used end to end.

If you have not used Replicator before, read :ref:`Getting Started Scripts <isaac_sim_app_tutorial_replicator_getting_started>` first - it introduces the orchestrator step, the capture-on-play flag, ``rt_subframes``, ``wait_for_render``, ``wait_until_complete``, and DLSS quality mode in isolation.

Setup and Configuration
-----------------------

This section introduces the Replicator settings and helpers that both example scripts use end to end. Each subsection briefly explains the API and shows how the workflows apply it.

Writers and Backends
--------------------

A writer formats annotator output (RGB, depth, segmentation, bounding boxes, and so on) and hands it to a backend that performs the I/O. Both workflows attach the built-in ``BasicWriter`` to a ``DiskBackend`` for RGB and colorized semantic segmentation:

.. code-block:: python

    backend = rep.backends.get("DiskBackend")
    backend.initialize(output_dir=out_dir)
    writer = rep.writers.get("BasicWriter")
    writer.initialize(
        backend=backend,
        rgb=True,
        semantic_segmentation=True,
        colorize_semantic_segmentation=True,
    )
    writer.attach(rp)

Replicator ships several other built-in writers, for example ``PoseWriter`` (6-DoF object pose data) and ``CosmosWriter`` (multi-modal training data for `NVIDIA Cosmos <https://www.nvidia.com/en-us/ai/cosmos/>`_). To emit any other format, register a :doc:`custom writer <extensions:ext_replicator/custom_writer>`. See :doc:`writer examples <extensions:ext_replicator/writer_examples>` for the full list and :doc:`annotators <extensions:ext_replicator/annotators_details>` for the data sources writers can consume.

Capture on Play Flag
--------------------

By default Replicator captures a frame every time the timeline ticks. Both workflows want the opposite - the script decides exactly when to capture. Disable the default once at startup:

.. code-block:: python

    rep.orchestrator.set_capture_on_play(False)

After this call the writer only sees frames produced by an explicit ``step()`` (or ``step_async``). This is what lets Workflow 1 advance several physics frames between captures without recording any of them.

.. _isaac_sim_app_tutorial_replicator_sdg_workflows_rt_subframes:

RT Subframes
------------

``rt_subframes`` is the number of times the renderer produces the *same* logical frame before the writer reads its annotators. The simulation is paused during subframe generation. The default is ``-1`` (use the global ``/omni/replicator/RTSubframes`` carb setting); per-step values must be greater than ``0``. Both workflows pass ``rt_subframes=8`` because they teleport the camera and randomize materials between captures.

Increase it when:

- The camera or props moved a lot between two captures (DLSS ghosting; faint trails or blurred silhouettes from the previous frame).
- Lights, textures, or MDL materials changed between captures (newly assigned materials need a few frames to fully load and resolve in the render graph).
- Path tracing is enabled or the scene is dimly lit.

Use ``rt_subframes=1`` only when nothing is changing between captures.

DLSS Quality Mode
-----------------

|isaac-sim_short| ships with the DLSS denoiser in Performance mode (``execMode=0``). At common SDG resolutions the performance modes can produce visible ghosting around moving edges and incorrect transparency on thin geometry. Both workflows switch DLSS to Quality mode once at startup:

.. code-block:: python

    import carb.settings

    carb.settings.get_settings().set("rtx/post/dlss/execMode", 2)

Available values: ``0`` Performance, ``1`` Balanced, ``2`` Quality, ``3`` Auto.

Wait for Render
---------------

Both workflows pass ``wait_for_render=False`` because they never read stage data (object poses, bounding boxes, etc.) after a step. The call returns as soon as the orchestrator has scheduled the frame, which lets the next randomization start while the previous frame is still being rendered. Set it to ``True`` whenever the annotation or writer data must match the current simulation state at the time the call returns.

Render Product Updates
----------------------

A render product ties a camera to the rendering and annotation graph (ray tracing, denoising, segmentation, bounding boxes, etc.). Once created, it keeps rendering on every application tick even when ``step()`` is not called. This wastes GPU time during physics, scene construction, and randomization.

The pattern both scripts use is to disable updates immediately after the render product is created and re-enable them only around the orchestrator step:

.. code-block:: python

    rp = rep.create.render_product(cam, RESOLUTION, name="rp_workflow_01")
    rp.hydra_texture.set_updates_enabled(False)

    # ... scene updates, physics, randomization (no rendering cost) ...

    rp.hydra_texture.set_updates_enabled(True)
    rep.orchestrator.step(rt_subframes=8, wait_for_render=False)
    rp.hydra_texture.set_updates_enabled(False)

The cost difference is most visible in Workflow 1, which advances PhysX many ticks between captures, and in any pipeline with multiple high-resolution cameras.

Seeded Randomization
--------------------

The scripts use a single ``ReplicatorRNG`` instance for all sampling. Helpers such as ``randomize_camera``, ``scatter_2d``, and ``rng.generator.uniform`` all take that instance as their ``rng=`` argument. Seed it once at startup so the script is fully reproducible:

.. code-block:: python

    rng = rep.rng.ReplicatorRNG(seed=42)

The same seed always produces the same dataset, which is useful when regenerating a specific outlier image.

Wait Until Complete
-------------------

Replicator writers do their I/O on background threads. If the script closes the application immediately after the last orchestrator step, the writer can still have several frames queued and the dataset will be missing PNGs or have half-written JSON files. Always wait before tearing down:

.. code-block:: python

    rep.orchestrator.wait_until_complete()                  # standalone
    await rep.orchestrator.wait_until_complete_async()      # script editor

After ``wait_until_complete`` returns it is safe to detach the writer, destroy the render product, and close the application.

Async vs Sync
-------------

Each workflow ships with two entry-point scripts that share scene-authoring code but differ in how they drive the application loop:

- **Script Editor** (``*_script_editor.py``) - executes inside the |isaac-sim_short| :ref:`Script Editor <script-editor>` window. The entry function is a coroutine that awaits the ``_async`` Replicator helpers (for example ``rep.orchestrator.step_async``) and yields back to the application loop with ``await omni.kit.app.get_app().next_update_async()``.
- **Standalone Application** (``sdg_workflow_*.py``) - launches its own :ref:`Standalone Application <standalone-application>` (``python.sh`` on Linux, ``python.bat`` on Windows). It uses the synchronous Replicator helpers and drives the application loop directly with ``simulation_app.update()``.

Examples
--------

.. _isaac_sim_app_tutorial_replicator_sdg_workflows_workflow_01:

Workflow 1: Persistent Scene with Physics-Based Settling
########################################################

This example builds one persistent scene (dome light, pallet, distractors, cardboxes, camera) and uses PhysX between captures so a re-dropped box settles before each frame is written. The render product and writer are created once and reused for every capture.

Per-prim helper functions called on existing prims:

- ``randomize_dome_light`` - chooses an HDR texture and intensity for the dome light.
- ``randomize_distractors`` - samples positions, rotations, scales, and display colors for the distractor prims.
- ``randomize_pallet`` - picks one of the pre-created materials and binds it to the pallet.
- ``randomize_camera`` - samples an orbit position around the pallet and points the camera back at it.
- ``randomize_boxes`` - writes per-box poses just before the timeline plays so PhysX settles the boxes for ``NUM_SIMULATION_FRAMES`` ticks.

Capture loop, repeated ``NUM_CAPTURES`` times:

#. Run ``randomize_dome_light``, ``randomize_distractors``, and ``randomize_pallet``.
#. Pick one box at random, give it a fresh pose, advance the timeline ``NUM_SIMULATION_FRAMES`` ticks so PhysX settles the new pose.
#. Move the camera, enable the render product, call the orchestrator step, disable the render product.

The standalone example can also be run directly (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.replicator.examples/sdg_workflow_01.py

.. tab-set::

    .. tab-item:: Script Editor

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_sdg_workflows/sdg_workflow_01_script_editor.py
            :language: python
            :lines: 16-

    .. tab-item:: Standalone Application

        .. literalinclude:: ../../../source/standalone_examples/api/isaacsim.replicator.examples/sdg_workflow_01.py
            :language: python
            :lines: 16-
            :end-before: # <start-sdg-workflow-01-test>

Output directory ``_out_workflow_01``: per captured frame, an ``rgb_*.png``, a colorized ``semantic_segmentation_*.png``, and a matching ``*.json`` label map written by the ``BasicWriter``.

.. _isaac_sim_app_tutorial_replicator_sdg_workflows_workflow_02:

Workflow 2: Scene Rebuild with Sample Collision Checks
######################################################

This example rebuilds the SDG content on a configurable cadence (``CAPTURES_PER_SCENE``): it picks an environment, scatters pallets on the floor with collision checks, builds vertical box stacks on each pallet using sample-time collision checks (no rigid-body simulation), and orbits one camera around each pallet.

Persistent setup (created once): a dome light, one camera, one render product, and one ``BasicWriter``. Per-randomization content is built under a unique scope ``/World/SDG/Scene_<n>`` and the previous scope is removed before authoring the new one so Replicator's scatter-mesh cache does not see stale planes.

Per scene rebuild:

#. Pick an environment URL from ``DEFAULT_ENV_URLS``. If the entry is ``None``, build a large ground plane with a collider instead.
#. ``create_pallets_on_floor`` - sample a count from ``PALLET_COUNT_RANGE``, scatter that many pallets on a hidden floor plane with ``rep.functional.randomizer.scatter_2d`` and ``check_for_collisions=True``, then snap each pallet so its measured bottom rests at ``z=0``.
#. ``create_stacks_on_pallet`` for each pallet - sample a stack count, scatter base boxes on a hidden plane fitted to the pallet top with collision checks (retry with one fewer base on collision timeout), then build each stack vertically by referencing the same asset multiple times.
#. For each capture in this scene, ``randomize_camera`` orbits the camera around the next pallet and the orchestrator step writes one frame.

The outer loop continues until ``TOTAL_CAPTURES`` frames have been written.

The standalone example can also be run directly (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.replicator.examples/sdg_workflow_02.py

.. tab-set::

    .. tab-item:: Script Editor

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_sdg_workflows/sdg_workflow_02_script_editor.py
            :language: python
            :lines: 16-

    .. tab-item:: Standalone Application

        .. literalinclude:: ../../../source/standalone_examples/api/isaacsim.replicator.examples/sdg_workflow_02.py
            :language: python
            :lines: 16-
            :end-before: # <start-sdg-workflow-02-test>

Output directory ``_out_workflow_02``: per captured frame, an ``rgb_*.png``, a colorized ``semantic_segmentation_*.png``, and a matching ``*.json`` label map.

Troubleshooting
---------------

See :ref:`Replicator Troubleshooting <isaac_sim_replicator_troubleshooting>` for the full list.

- **Ghosting or artifacts in early captures.** Increase ``rt_subframes`` (see :ref:`above <isaac_sim_app_tutorial_replicator_sdg_workflows_rt_subframes>`).
- **Frames missing from the writer.** ``wait_until_complete`` was not called before exit.

See Also
--------

- :ref:`Getting Started Scripts <isaac_sim_app_tutorial_replicator_getting_started>` - smaller, single-concept scripts that introduce the same settings in isolation.
- :ref:`Scene Based SDG <isaac_sim_app_tutorial_replicator_scene_based_sdg>` - large-scale configurable dataset generation.
- :ref:`Object Based SDG <isaac_sim_app_tutorial_replicator_object_based_sdg>` - physics-heavy object drops with multiple cameras.
- :doc:`Writer examples <extensions:ext_replicator/writer_examples>` and :doc:`custom writer guide <extensions:ext_replicator/custom_writer>` - write a different output format.
- :doc:`Annotators <extensions:ext_replicator/annotators_details>` - the full set of data sources available to writers.
- :doc:`I/O Optimization Guide <extensions:ext_replicator/io_guidelines>` - scaling to large datasets.
- :ref:`Performance Optimization Handbook <isaac_sim_performance_optimization_handbook>` - full set of ``rtx/post/dlss/execMode`` values and other render settings.
- :ref:`Replicator Troubleshooting <isaac_sim_replicator_troubleshooting>`.
