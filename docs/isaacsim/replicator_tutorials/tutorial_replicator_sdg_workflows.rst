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

This tutorial walks through two complete synthetic data generation (SDG) scripts. Each script authors a USD scene, randomizes it, runs the simulation, and writes annotated images to disk through a ``BasicWriter``. The two scripts share the same setup code but solve different problems: the first reuses one persistent scene and settles physics between captures, the second rebuilds the scene on a cadence and places assets with collision checks.

This tutorial is for developers who are comfortable with rigid-body simulation and USD scene graphs and want to see the Replicator API used end to end. By the end you will recognize the settings every SDG script configures at startup, the capture loop pattern both workflows follow, and the gotchas that produce corrupt or low-quality datasets.

Prerequisites
-------------

Before starting, make sure you have:

- Read :ref:`Getting Started Scripts <isaac_sim_app_tutorial_replicator_getting_started>`. It introduces the orchestrator step, the capture-on-play flag, ``rt_subframes``, ``wait_for_render``, ``wait_until_complete``, and DLSS quality mode one concept at a time. This tutorial assumes you know what each one does.
- Familiarity with USD (Universal Scene Description) concepts: prims, scopes, references, and transforms.
- A working |isaac-sim_short| install you can run as a :ref:`Standalone Application <standalone-application>` or through the :ref:`Script Editor <script-editor>`.
- Enough disk space for the captured dataset (scales with resolution and frame count).

Setup and Configuration
-----------------------

Both scripts run the same startup sequence before the capture loop. Each setting below shows the API call, why the workflows use it, and the effect of omitting it. The excerpts come from the example scripts shown later.

Writers and Backends
--------------------

A *writer* formats annotator output (RGB, depth, segmentation, bounding boxes, and so on) and hands it to a *backend* that performs the I/O. Both workflows attach the built-in ``BasicWriter`` to a ``DiskBackend`` and request RGB and colorized semantic segmentation:

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

``attach`` connects the writer to one or more render products. After this call, every orchestrator step routes that render product's annotator data through the writer. Each annotator you enable (``rgb``, ``semantic_segmentation``, and so on) adds GPU and I/O cost, so enable only what your dataset needs.

Replicator ships other built-in writers, for example ``PoseWriter`` (6-DoF object pose data) and ``CosmosWriter`` (multi-modal training data for `NVIDIA Cosmos <https://www.nvidia.com/en-us/ai/cosmos/>`_). To emit any other format, register a :doc:`custom writer <extensions:ext_replicator/custom_writer>`. See :doc:`writer examples <extensions:ext_replicator/writer_examples>` for the full list and :doc:`annotators <extensions:ext_replicator/annotators_details>` for the data sources writers can consume.

Capture on Play Flag
--------------------

By default Replicator captures a frame every time the timeline ticks. Both workflows capture data at specific timepoints rather than continuously, so they disable this flag once at startup and trigger each capture explicitly:

.. code-block:: python

    rep.orchestrator.set_capture_on_play(False)

After this call the writer receives only frames produced by an explicit ``step()`` (or ``step_async``). This lets Workflow 1 advance several physics frames between captures without recording any of them.

Orchestrator Step
-----------------

``rep.orchestrator.step()`` (``step_async()`` in the Script Editor) captures and processes one frame for the attached writers and annotators. Each workflow calls it once per capture. Its parameters are:

.. code-block:: python

    rep.orchestrator.step(rt_subframes=-1, pause_timeline=True, delta_time=None, wait_for_render=True)

- ``rt_subframes`` - number of subframes rendered before the frame is captured, covered in :ref:`RT Subframes <isaac_sim_app_tutorial_replicator_sdg_workflows_rt_subframes>` below.
- ``pause_timeline`` - pause the timeline after the step. Defaults to ``True``
- ``delta_time`` - how far the timeline advances during the step. ``None`` (default) advances by the timeline's rate, ``0.0`` does not advance the timeline, and a positive value advances by that amount.
- ``wait_for_render`` - block until the frame finishes rendering. Defaults to ``True``. Set it to ``False`` to let the next randomization start while the previous frame is still rendering, when exact frame-to-state correspondence is not required.

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

Render Product Updates
----------------------

A render product ties a camera to the rendering and annotation graph (ray tracing, denoising, segmentation, bounding boxes, etc.). Once created, it keeps rendering on every application tick even when ``step()`` is not called. This wastes GPU time during physics, scene construction, and randomization.

The pattern both scripts use is to disable updates immediately after the render product is created and re-enable them only around the orchestrator step:

.. code-block:: python

    rp = rep.create.render_product(cam, RESOLUTION, name="rp_workflow_01")
    rp.hydra_texture.set_updates_enabled(False)

    # ... scene updates, physics, randomization (no rendering cost) ...

    rp.hydra_texture.set_updates_enabled(True)
    rep.orchestrator.step(delta_time=0.0, rt_subframes=RT_SUBFRAMES)
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

The following sections present two complete example scripts that apply the settings from the previous section. Each section describes its scene, its capture loop, and its output on its own. Every script is shown in both the Script Editor and Standalone Application forms described above.

.. _isaac_sim_app_tutorial_replicator_sdg_workflows_workflow_01:

Workflow 1: Physics-Based Object Settling
#########################################

This workflow builds one scene (dome light, pallet, distractors, cardboxes, and camera) and keeps it for the whole run. Before each capture it re-drops one box and lets PhysX settle it, so every frame shows a slightly different physical arrangement of the same objects. The render product and writer are created once and reused, which avoids per-capture setup cost when the scene structure does not change.

.. image:: /images/isim_6.0_replicator_tut_external_workflow_1.webp
    :align: center
    :alt: Persistent SDG scene where a re-dropped cardbox settles on a pallet between captures
    :width: 80%

The script defines helper functions that each randomize one part of the existing scene:

- ``randomize_dome_light`` - chooses an HDR texture and intensity for the dome light.
- ``randomize_distractors`` - samples positions, rotations, scales, and display colors for the distractor prims.
- ``randomize_pallet`` - picks one of the pre-created materials and binds it to the pallet.
- ``randomize_camera`` - samples an orbit position around the pallet and points the camera back at it.
- ``randomize_boxes`` - writes per-box poses just before the timeline plays so PhysX settles the boxes over ``NUM_SIMULATION_FRAMES`` ticks.

The capture loop runs ``NUM_CAPTURES`` times:

#. Randomize the lighting, distractors, and pallet material with the helpers above.
#. Pick one box at random, give it a fresh pose, and advance the timeline ``NUM_SIMULATION_FRAMES`` ticks so PhysX settles the new pose.
#. Move the camera, enable the render product, call the orchestrator step, then disable the render product again.

Physics runs *between* captures (step 2), and only the orchestrator step (step 3) produces a frame.

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

Workflow 2: Collision-Checked Asset Placement
#############################################

This workflow rebuilds its SDG content on a configurable cadence (``CAPTURES_PER_SCENE``). Each rebuild picks an environment, scatters pallets on the floor, builds vertical box stacks on each pallet, and orbits one camera around each pallet. It places assets with sample-time collision checks rather than rigid-body simulation, so there is no physics settling step.

.. image:: /images/isim_6.0_replicator_tut_external_workflow_2.webp
    :align: center
    :alt: SDG scenes rebuilt across environments with pallets and collision-checked box stacks captured from an orbiting camera
    :width: 80%

The persistent objects (a dome light, one camera, one render product, and one ``BasicWriter``) are created once. The per-rebuild content lives under a unique scope ``/World/SDG/Scene_<n>``. The script removes the previous scope before authoring the next one. If the old scope remains on the stage, Replicator's scatter-mesh cache reuses stale planes and asset placement fails.

Each scene rebuild does the following:

#. Pick an environment URL from ``DEFAULT_ENV_URLS``. If the entry is ``None``, build a large ground plane with a collider instead.
#. ``create_pallets_on_floor`` - sample a count from ``PALLET_COUNT_RANGE``, scatter that many pallets on a hidden floor plane with ``rep.functional.randomizer.scatter_2d`` and ``check_for_collisions=True``, then snap each pallet so its measured bottom rests at ``z=0``.
#. ``create_stacks_on_pallet`` for each pallet - sample a stack count, scatter base boxes on a hidden plane fitted to the pallet top with collision checks (retry with one fewer base if scattering cannot find a collision-free layout), then build each stack vertically by referencing the same box asset at increasing heights.
#. For each capture in this scene, ``randomize_camera`` orbits the camera around the next pallet and the orchestrator step writes one frame.

The outer loop continues until ``TOTAL_CAPTURES`` frames have been written. The hidden scatter planes and the bounding-box queries (``compute_aabb``) place assets on surfaces without running physics.

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
- **Scattered assets overlap or land in the wrong place after a rebuild (Workflow 2).** The previous scene scope was not removed before authoring the new one, so Replicator's scatter-mesh cache reused stale planes.
- **Slow runs even though few frames are written.** The render product was left enabled during physics, scene construction, or randomization. Disable it and re-enable only around the orchestrator step.

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
