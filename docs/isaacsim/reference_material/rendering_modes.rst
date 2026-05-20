..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_rendering_modes:

===============
Rendering modes
===============

|isaac-sim_short| uses the NVIDIA Omniverse RTX Renderer for viewport rendering, camera sensors, and synthetic data generation workflows. Select the render mode based on the balance you need between visual fidelity, physical accuracy, latency, and throughput.

For the complete renderer setting reference, see the `Omniverse RTX Renderer documentation <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/rtx-renderer.html>`_.

.. _isaac_sim_rendering_modes_overview:

Rendering mode overview
=======================

.. list-table::
    :header-rows: 1
    :widths: 20 24 34 22

    * - Mode
      - Best used for
      - Notes
      - Omniverse docs
    * - RTX - Real-Time 2.0
      - Interactive simulation, robotics workflows, and synthetic data generation where real-time performance is important.
      - This is the default rendering mode in |isaac-sim_short|. It uses path tracing with NVIDIA DLSS neural rendering technologies to provide a balance of fidelity and real-time performance.
      - `RTX - Real-Time 2.0 mode <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/rtx-renderer_rt.html>`_
    * - RTX - Interactive (Path Tracing)
      - High-quality still captures, validation images, and workflows that can trade performance for higher physical accuracy.
      - This mode accumulates samples for higher-fidelity lighting and material results. It is slower than RTX - Real-Time 2.0 and commonly requires more samples per pixel for low-noise output.
      - `RTX - Interactive (Path Tracing) mode <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/rtx-renderer_pt.html>`_
    * - RTX - Minimal
      - Training-in-the-loop and high-throughput workflows where low latency is more important than full light transport.
      - This mode provides simplified rendering. It disables indirect light transport and uses only the first distant light in the scene, with hard shadows. Ambient lighting can improve visibility.
      - `RTX - Minimal <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/rtx-renderer_minimal.html>`_

Common RTX renderer features, such as multi-GPU rendering, materials, light types, cameras, post-processing, volume rendering, texture streaming, and debug views, are documented in `RTX - Common <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/rtx-renderer_common.html>`_.

.. _isaac_sim_rendering_modes_select:

Select a rendering mode
=======================

For standalone Python workflows, configure the renderer when you create ``SimulationApp``:

.. code-block:: python

    from isaacsim import SimulationApp

    simulation_app = SimulationApp({"renderer": "RealTimePathTracing"})

Common ``renderer`` values include:

* ``RealTimePathTracing`` for RTX - Real-Time 2.0.
* ``PathTracing`` for RTX - Interactive (Path Tracing).
* ``RaytracedLighting`` for RTX Real-Time (Legacy).
* ``MinimalRendering`` for RTX - Minimal (``Minimal`` is also accepted).

For RTX - Minimal, set ``minimal_shading_mode`` in the ``SimulationApp`` launch configuration to select the shading behavior. This option maps to ``/rtx/minimal/mode``. The default is ``0``. Accepted values are:

* ``0`` — Real-Time 2.0 (reference).
* ``1`` — Diffuse/Glossy/Emission.
* ``2`` — Textured Diffuse.
* ``3`` — Constant Diffuse.
* ``4`` — No Rendering (black color output; use when only non-color AOVs such as depth or segmentation are needed).

In the |isaac-sim_short| GUI, you can also select RTX - Minimal from the viewport render mode menu and modify shading behavior and other settings in the Rendering Settings panel.

Call ``reset_render_settings()`` after opening a new stage to re-apply the launch configuration, including the renderer and minimal shading mode.

You can also change the active render mode while |isaac-sim_short| is running by setting ``/rtx/rendermode``:

.. code-block:: python

    import carb.settings

    carb.settings.get_settings().set("/rtx/rendermode", "PathTracing")

For RTX - Minimal at runtime, set ``/rtx/rendermode`` to ``MinimalRendering`` and adjust ``/rtx/minimal/mode`` as needed. Other RTX - Minimal carb settings, such as ``/rtx/minimal/constantColor`` and ambient light options under ``/rtx/sceneDb/``, are described in :ref:`RTX - Minimal limitations <isaac_sim_rendering_modes_minimal>` and in `RTX - Minimal <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/rtx-renderer_minimal.html>`_.

.. _isaac_sim_rendering_modes_minimal:

RTX - Minimal limitations
=========================

RTX - Minimal is optimized for throughput and latency, not full lighting fidelity. Use it when simplified visual output is acceptable for the workflow.

RTX - Minimal has the following limitations:

* It disables indirect light transport.
* It uses only the first distant light source found in the scene.
* It supports hard shadows only.
* It does not reproduce all material and lighting effects available in RTX - Real-Time 2.0 or RTX - Interactive (Path Tracing).
* The ``No Rendering`` minimal shading mode outputs black color images and is intended for workflows that only need non-color outputs such as depth, normals, or instance segmentation.

The primary RTX - Minimal settings are ``/rtx/minimal/mode``, ``/rtx/minimal/constantColor``, ``/rtx/sceneDb/ambientLightColor``, and ``/rtx/sceneDb/ambientLightIntensity``. In standalone Python workflows, ``SimulationApp`` applies ``/rtx/minimal/mode`` from ``minimal_shading_mode`` when ``renderer`` is set to ``MinimalRendering``. Use ``SimulationApp.set_setting()`` or carb settings directly for the other values. See `RTX - Minimal <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/rtx-renderer_minimal.html>`_ for the full setting descriptions.

.. _isaac_sim_rendering_modes_guidance:

Mode selection guidance
=======================

Use RTX - Real-Time 2.0 for most interactive robotics and simulation workflows. It provides the best default balance between quality and performance.

Use RTX - Interactive (Path Tracing) when image quality and physically accurate lighting matter more than frame time. This is commonly useful for final captures, quality comparisons, and validation images.

Use RTX - Minimal when throughput or latency is the primary requirement and the workflow does not depend on full light transport, multiple light sources, or high-fidelity material appearance.
