..
   Copyright (c) 2024-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_tutorial_replicator_sdg_workflows:

=============
SDG workflows
=============

.. note::

   Work in progress. Two reference SDG scripts that walk through the patterns a developer needs to start using Replicator in |isaac-sim_short|.

This tutorial walks through two complete synthetic data generation (SDG) scripts. Each one authors a USD scene, randomizes it, runs the simulation, and writes annotated images to disk through a ``BasicWriter``. The audience is a developer who is comfortable with rigid-body simulation and USD scene graphs and wants to see the Replicator API used end to end.

If you have not used Replicator before, read :ref:`Getting Started Scripts <isaac_sim_app_tutorial_replicator_getting_started>` first - it introduces the orchestrator step, the capture-on-play flag, ``rt_subframes``, ``wait_for_render``, ``wait_until_complete``, and DLSS quality mode in isolation.

Execution modes
---------------

Each workflow has two entry-point scripts:

- **Script Editor** (``*_script_editor.py``) - executes inside the |isaac-sim_short| :ref:`Script Editor <script-editor>` window. The entry function is a coroutine that awaits the ``_async`` Replicator helpers (for example ``rep.orchestrator.step_async``) and yields back to the application loop with ``await omni.kit.app.get_app().next_update_async()``.
- **Standalone application** (``sdg_workflow_*.py``) - launches its own :ref:`Standalone Application <standalone-application>` (``python.sh`` on Linux, ``python.bat`` on Windows). It uses the synchronous Replicator helpers and drives the application loop directly with ``simulation_app.update()``.

How the two workflows differ
----------------------------

- **Workflow 1** builds one persistent scene (dome light, pallet, distractors, cardboxes, camera) and uses PhysX between captures so a re-dropped box settles before each frame is written.
- **Workflow 2** rebuilds the SDG content on a configurable cadence: it picks an environment, scatters pallets on the floor, builds vertical box stacks on each pallet using sample-time collision checks (no rigid-body simulation), and orbits one camera around each pallet.

API surface
-----------

The scripts touch the Replicator entry points listed below. See the :doc:`Replicator documentation <extensions:ext_replicator>` for full signatures.

- ``rep.functional.create.*`` - author USD content (xforms, scopes, references, planes, lights, cameras, materials).
- ``rep.functional.create_batch.*`` - bulk-create labeled primitive geometry.
- ``rep.functional.modify.*`` - update prim attributes (pose, material, generic attribute).
- ``rep.functional.physics.apply_rigid_body`` / ``apply_collider`` - add PhysX rigid bodies and colliders.
- ``rep.functional.randomizer.*`` - built-in randomizers such as ``scatter_2d`` and ``display_color``.
- ``rep.rng.ReplicatorRNG`` - seeded NumPy-style RNG passed as the ``rng=`` argument to every randomizer.
- ``rep.create.render_product`` - bind a camera to the rendering and annotation graph.
- ``rep.writers.get`` / ``rep.backends.get`` - pick a writer (for example ``BasicWriter``) and a backend (for example ``DiskBackend``).
- ``rep.orchestrator.step`` / ``step_async``, ``set_capture_on_play``, ``wait_until_complete[_async]`` - drive frame capture.

Background concepts used by both scripts
----------------------------------------

The settings below are introduced in isolation in :ref:`Getting Started Scripts <isaac_sim_app_tutorial_replicator_getting_started>`. This section shows how the workflows combine them.

Writers and backends
####################

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

Capture loop
############

Replicator captures one frame each time the orchestrator step runs. The standalone scripts use the synchronous version, the script-editor scripts await the async version:

.. code-block:: python

    rep.orchestrator.step(rt_subframes=8, wait_for_render=False)              # standalone
    await rep.orchestrator.step_async(rt_subframes=8, wait_for_render=False)  # script editor

By default Replicator also captures a frame every time the timeline ticks. Both workflows want the opposite - the script decides exactly when to capture. Disable the default once at startup:

.. code-block:: python

    rep.orchestrator.set_capture_on_play(False)

After this call the writer only sees frames produced by an explicit ``step()`` (or ``step_async``). This is what lets Workflow 1 advance several physics frames between captures without recording any of them.

DLSS quality mode
#################

|isaac-sim_short| ships with the DLSS denoiser in Performance mode (``execMode=0``). At common SDG resolutions the performance modes can produce visible ghosting around moving edges and incorrect transparency on thin geometry. Both workflows switch DLSS to Quality mode once at startup:

.. code-block:: python

    import carb.settings
    carb.settings.get_settings().set("rtx/post/dlss/execMode", 2)

Available values: ``0`` Performance, ``1`` Balanced, ``2`` Quality, ``3`` Auto.

.. _isaac_sim_app_tutorial_replicator_sdg_workflows_rt_subframes:

Subframes
#########

``rt_subframes`` is the number of times the renderer produces the *same* logical frame before the writer reads its annotators. The simulation is paused during subframe generation. The default is ``-1`` (use the global ``/omni/replicator/RTSubframes`` carb setting); per-step values must be greater than ``0``. Both workflows pass ``rt_subframes=8`` because they teleport the camera and randomize materials between captures.

Increase it when:

- The camera or props moved a lot between two captures (DLSS ghosting; faint trails or blurred silhouettes from the previous frame).
- Lights, textures, or MDL materials changed between captures (newly assigned materials need a few frames to fully load and resolve in the render graph).
- Path tracing is enabled or the scene is dimly lit.

Use ``rt_subframes=1`` only when nothing is changing between captures.

Wait for render
###############

Both workflows pass ``wait_for_render=False`` because they never read stage data (object poses, bounding boxes, etc.) after a step. The call returns as soon as the orchestrator has scheduled the frame, which lets the next randomization start while the previous frame is still being rendered. Set it to ``True`` whenever the annotation or writer data must match the current simulation state at the time the call returns.

Toggle render-product updates around captures
#############################################

A render product ties a camera to the rendering and annotation graph (ray tracing, denoising, segmentation, bounding boxes, etc.). Once created, it keeps rendering on every application tick even when you are not calling ``step()``. This wastes GPU time during physics, scene construction, and randomization.

The pattern both scripts use is to disable updates immediately after the render product is created and re-enable them only around the orchestrator step:

.. code-block:: python

    rp = rep.create.render_product(cam, RESOLUTION, name="rp_workflow_01")
    rp.hydra_texture.set_updates_enabled(False)

    # ... scene updates, physics, randomization (no rendering cost) ...

    rp.hydra_texture.set_updates_enabled(True)
    rep.orchestrator.step(rt_subframes=8, wait_for_render=False)
    rp.hydra_texture.set_updates_enabled(False)

The cost difference is most visible in Workflow 1, which advances PhysX many ticks between captures, and in any pipeline with multiple high-resolution cameras.

Seed every random source
########################

The scripts use a single ``ReplicatorRNG`` instance for all sampling. Helpers such as ``randomize_camera``, ``scatter_2d``, and ``rng.generator.uniform`` all take that instance as their ``rng=`` argument. Seed it once at startup so the script is fully reproducible:

.. code-block:: python

    rng = rep.rng.ReplicatorRNG(seed=42)

The same seed always produces the same dataset, which is useful when regenerating a specific outlier image.

Flush the writer before exit
############################

Replicator writers do their I/O on background threads. If the script closes the application immediately after the last orchestrator step, the writer can still have several frames queued and the dataset will be missing PNGs or have half-written JSON files. Always wait before tearing down:

.. code-block:: python

    rep.orchestrator.wait_until_complete()                  # standalone
    await rep.orchestrator.wait_until_complete_async()      # script editor

After ``wait_until_complete`` returns it is safe to detach the writer, destroy the render product, and close the application.

Async vs sync
#############

The script-editor scripts are coroutines that the Script Editor schedules with ``asyncio.ensure_future(...)``. Anything that needs the application to advance is awaited:

.. code-block:: python

    await omni.kit.app.get_app().next_update_async()
    await rep.orchestrator.step_async(rt_subframes=8)
    await rep.orchestrator.wait_until_complete_async()

The standalone scripts call the synchronous variants and pump the application directly:

.. code-block:: python

    simulation_app.update()
    rep.orchestrator.step(rt_subframes=8)
    rep.orchestrator.wait_until_complete()

Gotchas
-------

See :ref:`Replicator Troubleshooting <isaac_sim_replicator_troubleshooting>` for the full list.

- **Ghosting or artifacts in early captures.** Increase ``rt_subframes`` (see :ref:`above <isaac_sim_app_tutorial_replicator_sdg_workflows_rt_subframes>`).
- **Frames missing from the writer.** ``wait_until_complete`` was not called before exit.

.. _isaac_sim_app_tutorial_replicator_sdg_workflows_workflow_01:

Workflow 1: persistent scene with physics-based settling
--------------------------------------------------------

Per-prim randomizers, persistent scene, PhysX between captures.

Scene built once, before the capture loop:

- ``/SDG`` parent xform with sub-scopes for ``Lights``, ``Assets``, ``Materials``, and ``Cameras`` (each created right before the prims that go into it).
- One dome light under ``/SDG/Lights``.
- One pallet (kinematic rigid body, so PhysX collides against it but does not move it) and a pool of pre-created ``OmniPBR`` materials with randomly sampled diffuse color, roughness, and metallic values.
- Four sets of primitive distractors (cubes, spheres, cylinders, cones) created with ``rep.functional.create_batch.*``.
- ``NUM_DROP_BOXES`` cardboxes (rigid bodies with a bounding-cube collider on each child mesh) referenced from a single asset.
- One camera and one render product wired to a ``BasicWriter`` for RGB and colorized semantic segmentation.

Helper functions used by the capture loop:

- ``randomize_distractors`` - samples positions, rotations, scales, and display colors for the existing distractor prims.
- ``randomize_dome_light`` - chooses an HDR texture and an intensity and writes them to the dome light.
- ``randomize_pallet`` - picks one of the pre-created materials and binds it to the pallet.
- ``randomize_camera`` - samples an orbit position around the pallet and points the camera back at it.
- ``randomize_boxes`` - writes per-box poses just before the timeline plays so PhysX settles the boxes for ``NUM_SIMULATION_FRAMES`` ticks.

Capture loop, repeated ``NUM_CAPTURES`` times:

#. Run the randomizers above (light, distractors, pallet material).
#. Pick one box at random, give it a fresh pose, and advance the timeline for ``NUM_SIMULATION_FRAMES`` ticks so PhysX settles the new pose.
#. Move the camera, enable the render product, call the orchestrator step, disable the render product.

Run the standalone example (on Windows use ``python.bat`` instead of ``python.sh``):

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

Output directory ``_out_workflow_01``: per captured frame, an ``rgb_*.png``, a colorized ``semantic_segmentation_*.png``, and a matching ``*.json`` label map written by the ``BasicWriter``.

.. _isaac_sim_app_tutorial_replicator_sdg_workflows_workflow_02:

Workflow 2: scene rebuild with sample-time collision checks
-----------------------------------------------------------

Full SDG content rebuild every ``CAPTURES_PER_SCENE`` captures. No rigid-body simulation; collisions are checked at sample time only.

Persistent setup (created once):

- ``/World`` and ``/World/SDG`` xforms.
- One dome light under ``/World/SDG``.
- One camera, one render product, and one ``BasicWriter`` (RGB and colorized semantic segmentation).

Per-randomization sequence is built under a unique scope ``/World/SDG/Scene_<n>``; the previous scope is removed before authoring the new one so Replicator's scatter-mesh cache does not see stale planes.

#. Pick an environment URL from ``DEFAULT_ENV_URLS``. If the entry is ``None``, build a large ground plane with a collider instead.
#. ``create_pallets_on_floor`` - sample a count from ``PALLET_COUNT_RANGE``, scatter that many pallets on a hidden floor plane with collision checks (``rep.functional.randomizer.scatter_2d``), then snap each pallet so its measured bottom rests at ``z=0``. Returns the pallet prims.
#. Shuffle the pallet order with ``rng.generator.shuffle`` so the camera does not always start at the same pallet.
#. ``create_stacks_on_pallet`` for each pallet - sample a count from ``STACK_COUNT_RANGE`` and create that many base boxes (each referencing a random asset from ``BOX_URLS``), scatter them on a hidden plane fitted to the pallet top with collision checks, retry with one fewer base on collision timeout, then build each stack vertically by referencing the same asset ``BOXES_PER_STACK_RANGE`` times.
#. For each capture in this scene, ``randomize_camera`` orbits the camera around the next pallet and the orchestrator step writes one frame.

The outer loop continues until ``TOTAL_CAPTURES`` frames have been written.

Run the standalone example (on Windows use ``python.bat`` instead of ``python.sh``):

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

Output directory ``_out_workflow_02``: per captured frame, an ``rgb_*.png``, a colorized ``semantic_segmentation_*.png``, and a matching ``*.json`` label map.

See also
--------

- :ref:`Getting Started Scripts <isaac_sim_app_tutorial_replicator_getting_started>` - smaller, single-concept scripts that introduce the same settings in isolation.
- :ref:`Scene Based SDG <isaac_sim_app_tutorial_replicator_scene_based_sdg>` - large-scale configurable dataset generation.
- :ref:`Object Based SDG <isaac_sim_app_tutorial_replicator_object_based_sdg>` - physics-heavy object drops with multiple cameras.
- :doc:`Writer examples <extensions:ext_replicator/writer_examples>` and :doc:`custom writer guide <extensions:ext_replicator/custom_writer>` - write a different output format.
- :doc:`Annotators <extensions:ext_replicator/annotators_details>` - the full set of data sources available to writers.
- :doc:`I/O Optimization Guide <extensions:ext_replicator/io_guidelines>` - scaling to large datasets.
- :ref:`Performance Optimization Handbook <isaac_sim_performance_optimization_handbook>` - full set of ``rtx/post/dlss/execMode`` values and other render settings.
- :ref:`Replicator Troubleshooting <isaac_sim_replicator_troubleshooting>`.
