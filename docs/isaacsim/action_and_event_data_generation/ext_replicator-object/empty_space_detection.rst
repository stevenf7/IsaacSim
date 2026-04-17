..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _empty_space_detection:

============================
Empty Space Detection
============================

The **empty space** detector is an optional scene analysis step in ``isaacsim.replicator.object``. You declare it as a top-level key in the description file (alongside other :ref:`mutables<mutable>`) with ``detector_type: empty_space``. At runtime the extension creates a temporary detector volume, voxelizes the region using ray casts, classifies free space, and writes **3D bounding boxes** and **2D polygon footprints** of detected empty regions into per-detector metadata. The implementation lives in ``EmptySpaceDetector`` (``mutables/detector.py``) and ``SpaceDetectManager`` (``mutables/detector_internal/space_detect_manager.py``).

Use it for workflows that need explicit **free-space regions** (for example bin packing, placement, or annotating voids) in addition to tracked object geometry.


When it Runs
------------------

Detectors are initialized and run during the normal simulation workflow after the USD scene for the frame has been updated. The detector prim is removed from the stage when detection finishes. Enable visualization flags (see below) if you want to see scope, voxels, or height-span debug drawing in the viewport for that frame.


Scope geometry (required)
---------------------------

Each detector entry **must** define a 3D axis-aligned scope. You can use either naming style:

.. list-table::
   :widths: 20 40 40
   :header-rows: 1

   * - Key
     - Meaning
     - Notes
   * - ``translate`` **or** ``center``
     - 3-vector position of the detector volume
     - Same units as the stage (typically meters when ``default_meters_per_unit`` is ``1``).
   * - ``scale`` **or** ``size``
     - 3-vector extent of the box
     - Values are interpreted in **centimeters**; internally they are converted to meters for the USD transform (refer to ``EmptySpaceDetector`` in the extension source).

Example (excerpt):

.. code:: yaml

   my_empty_space_detector:
     detector_type: empty_space
     translate: [0, 0, 0.25]
     scale: [500, 500, 200]   # centimeters: width, depth, height of the analysis region


Detection Parameters
--------------------

Detection Parameters are optional. These keys are read from the **same** detector block (the dictionary named after your detector, for example ``my_empty_space_detector``). All numeric thresholds below are in **meters** unless your scene uses a different meters-per-unit convention. Defaults match ``EmptySpaceDetector.detect`` in the extension.

============================================ ================ ======================= =====================================================================
Key                                          Type             Default                 Description
============================================ ================ ======================= =====================================================================
``cell_size``                                numeric          ``0.05``                Voxel / grid resolution along X and Y.
``cell_height_threshold``                    numeric          ``0.2``                 Minimum vertical clearance used when classifying empty height spans.
``x_length_threshold``                       numeric          ``0.2``                 Minimum extent along X for a region to count as empty space.
``y_length_threshold``                       numeric          ``0.2``                 Minimum extent along Y for a region to count as empty space.
``exclusive_ratio_threshold``                numeric          ``0.8``                 Ratio used when filtering candidate regions (higher tends to retain more regions; range ``0.0``–``1.0``).
``top_tolerance``                            numeric          ``0.2``                 Height tolerance at the top of a span.
``bottom_tolerance``                         numeric          ``0.1``                 Height tolerance at the bottom of a span.
``max_stack_height``                         numeric / null   ``None``                Optional cap on stack height in meters; ``None`` means no limit.
============================================ ================ ======================= =====================================================================

You can drive several of these from a single root-level macro (for example a shared ``cell_size`` in meters) using :ref:`Macro` expressions such as ``$[/cell_size] * 2.0``.


Visualization
--------------

Visualization is optional.

============================================ ========= =======================
Key                                          Type      Description
============================================ ========= =======================
``visualize``                                bool      Draw 3D boxes for detected free regions and 2D polygon outlines when ``True``.
``visualize_raycast``                        bool      Draw raycast or height-span debug (for example yellow height-span visualization in the sample config).
``visualize_color``                          list      RGBA for 3D bbox drawing; default ``[1, 0, 0, 0.5]``.
``visualize_2d_color``                       list      RGBA for 2D polygon outlines; default ``[0, 1, 0, 0.5]``.
``visualize_scope``                          bool      Show the detector scope as a wireframe when ``True``; default ``True`` when visualization runs.
============================================ ========= =======================


Visualization Color Legend
-----------------------------

When debug draw is available (``isaacsim.util.debug_draw``), the viewport uses the following default colors. You can change the 3D box and 2D outline colors with ``visualize_color`` and ``visualize_2d_color``.  The other colors listed below are fixed in ``space_detect_visualization.py``.

.. list-table::
   :widths: 18 22 60
   :header-rows: 1

   * - Color (default)
     - Meaning
     - Notes
   * - **Yellow** wireframe (RGBA ``1, 1, 0, 0.3``)
     - Detector **scope** (analysis volume)
     - The axis-aligned box you defined with ``translate``/``center`` and ``scale``/``size``. Shown when ``visualize`` is ``True`` and ``visualize_scope`` is ``True``.
   * - **Red** wireframe (default ``visualize_color``: ``1, 0, 0, 0.5``)
     - **3D empty-space** result
     - One box per detected free region: edges of the 3D bounding boxes written to ``detected_space_3d``.
   * - **Green** polylines (default ``visualize_2d_color``: ``0, 1, 0, 0.5``)
     - **2D empty-space** result (footprint)
     - Outlines of free regions projected to the ground plane (near ``min_height``), matching ``detected_space_2d`` outlines.
   * - **Magenta** (``1, 0, 1, 0.5``)
     - **Holes** inside 2D regions
     - Fixed color for hole boundaries; not controlled by YAML.

If ``visualize_raycast`` is ``True``, raycast and height-span debug lines are
drawn in addition to the colors above:

.. list-table::
   :widths: 18 22 60
   :header-rows: 1

   * - Color
     - Meaning
     - Notes
   * - **Yellow** vertical segments (``1, 1, 0, 0.5``)
     - Per-voxel **height span** along the cast direction
     - One vertical line per free height interval in the voxelization grid.
   * - **Red** points (``1, 0, 0, 0.5``)
     - **Base** of each span
     - Lower bound of a height interval.
   * - **Green** points (``0, 1, 0, 0.5``)
     - **Ceiling** of each span
     - Upper bound of a height interval.


The raycast green points are not the same as the green 2D polygon outlines. Turn
off ``visualize_raycast`` if you only want the final 2D and 3D empty-space
overlays.


Outputs
---------

After ``detect`` completes, the extension stores results on the metadata entry for that detector key:

* ``detected_space_3d``: list of dicts with ``translate`` and ``scale`` (each axis-aligned free region in world space).
* ``detected_space_2d``: serialized polygons (``id``, ``min_height``, ``max_height``, ``outline``, ``holes``) suitable for logging or downstream tools.

Exact consumption of these fields in written outputs depends on your :ref:`output switches<Output switches>` and description logging pipeline.


Example Configuration
-------------------------

The extension ships a full demo that uses a **Z-up** stage, basic primitives on a floor, and an ``empty_space`` detector with macros and visualization enabled:

``PATH_TO_CORE_EXTENSION/isaacsim/replicator/object/core/configs/demo_empty_space.yaml``

Select that YAML from the **Object SDG** panel, or pass it as
``--/config/file=...`` when running headless, to reproduce the workflow
end to end.

.. figure:: /images/ext_replicator-object/isim_6.0_replicator_ext-isaacsim.replicator.object-0.11.9_viewport_empty_space.png
   :align: center

Viewport with ``demo_empty_space.yaml``. The following colors appear in the
viewport:

- **Yellow wireframe**: The detector scope.
- **Red boxes**: 3D empty-space results.
- **Green outlines**: 2D footprints.

When ``visualize_raycast`` is enabled, additional elements appear as described
in the preceding legend:

- **Yellow vertical segments**: Raycast lines.
- **Red and green span points**: Height-span sample points.
