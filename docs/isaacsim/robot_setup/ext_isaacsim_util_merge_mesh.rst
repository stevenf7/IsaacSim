
..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_merge_mesh:

==================
Mesh merge tool
==================

.. deprecated:: 6.0

   The standalone ``isaacsim.util.merge_mesh`` extension is deprecated and will be removed in a future release. Use the **Scene Optimizer** ``merge`` operation instead, through the URDF/MJCF importer's **Merge Mesh** option, the **Scene Optimizer** panel (**Window > Utilities > Scene Optimizer**), the :ref:`isaac_sim_app_asset_transformer` ``MergeMeshRule``, or by calling the operation directly from Python.

.. _isaac_merge_mesh_about:

About
=================

Mesh merging combines multiple visual geometry prims that share a common rigid-body parent into a single mesh. Reducing the number of geometry prims lowers draw-call overhead and improves both rendering and physics performance.

|isaac-sim| performs mesh merging through the **Scene Optimizer** Kit extension (``omni.scene.optimizer.core``). The Scene Optimizer ``merge`` operation preserves materials as ``GeomSubset`` entries on the resulting mesh, supports vertex deduplication, and can group meshes spatially.

Four integration paths expose the Scene Optimizer merge operation in |isaac-sim|:

.. list-table::
   :header-rows: 1
   :widths: 25 35 40

   * - Integration
     - Where to use it
     - Best for
   * - URDF / MJCF importer
     - **File > Import** > **Merge Mesh** checkbox
     - One-shot import-time merging of robot assets
   * - Scene Optimizer panel
     - **Window > Utilities > Scene Optimizer**
     - Interactive merging on existing assets, ad-hoc presets
   * - Asset Transformer profile
     - :ref:`isaac_sim_app_asset_transformer` > ``MergeMeshRule``
     - Repeatable, version-controlled asset pipelines
   * - Python API
     - ``isaacsim.asset.importer.utils.merge_mesh_utils``
     - Custom scripts and headless asset preparation

.. _isaac_merge_mesh_importer_option:

Using the URDF / MJCF importer
==============================

Both the URDF and MJCF importers expose a **Merge Mesh** checkbox under the **Options** section of the importer UI. Enabling this option runs three Scene Optimizer operations in sequence on the converted USD stage:

1. ``meshCleanup`` — merges duplicate vertices, removes degenerate faces, fixes non-manifold geometry.
2. ``generateNormals`` and ``generateProjectionUVs`` — regenerates vertex normals and projected UVs.
3. ``merge`` — for each rigid body in the stage, merges all child visual mesh prims (those with ``default`` or ``render`` purpose) into a single mesh under that body.

The importer determines merge groups automatically by traversing each ``UsdPhysics.RigidBodyAPI`` prim and collecting its child geometry, stopping at nested rigid-body boundaries. No additional configuration is required.

Refer to :ref:`isaac_sim_urdf_importer` and :ref:`isaac_sim_mjcf_importer` for the full importer workflows.

.. _isaac_merge_mesh_scene_optimizer_ui:

Using the Scene Optimizer UI
============================

The Scene Optimizer extension ships its own UI panel that exposes the ``merge`` operation directly, with no intermediate Asset Transformer rule. Use this path for one-off interactive merges on an existing stage, or to combine ``merge`` with other Scene Optimizer operations such as deduplication and material consolidation.

.. tab-set::

   .. tab-item:: GUI (Scene Optimizer panel)

      Use the Scene Optimizer panel to merge meshes interactively.

      1. **Enable the Scene Optimizer extension.** Scene Optimizer is not enabled by default in the standard |isaac-sim| experiences. Open the :doc:`Extension Manager <extensions:ext_core/ext_extension-manager>` (**Window > Extensions**), search for ``omni.scene.optimizer.bundle``, and toggle it on. The bundle pulls in the ``core``, ``ui``, ``analysis``, and ``validators`` extensions.

      2. **Load the asset to merge.** Use **File > Open** to load the USD into the active stage.

      3. **Open the Scene Optimizer panel.** Select **Window > Utilities > Scene Optimizer**.

      4. **Choose a workflow:**

         - To use a bundled preset, click **Load Preset** and pick one of the merge-related presets:

           - **Modify Stage - Merge Meshes** — flatten the hierarchy and merge meshes by material into ``/World/Geometry/merged``.
           - **Modify Stage - Spatial Merge Meshes** — merge all meshes regardless of material based on a spatial bounding volume; useful for very dense scenes.
           - **Modify Instances - Merge Meshes** — merge meshes inside each prototype while preserving the instance hierarchy. Best when the asset uses scenegraph instancing.

         - To merge a hand-picked set of meshes, click **Add Scene Optimizer Process** and select **Merge Meshes** (the operation registered as ``merge``). Configure:

           - **Mesh Prim Paths**: enter prim paths or path expressions (for example, ``/World/Robot/left_wheel//Mesh*`` — the leading ``//`` matches descendants at any depth under ``left_wheel``). Click the **pencil** icon to pick paths from the stage, or click **Add** with prims selected in the viewport.
           - **Consider Materials**: enable to preserve per-material ``GeomSubset`` partitions on the merged mesh (Scene Optimizer equivalent of the legacy **Combine Materials** option).
           - **Original Geom Option**: ``0`` to keep the source meshes, ``1`` to deactivate them, ``2`` to delete them.
           - **Merge Point**: ``0`` to place the merged mesh at world origin, ``1`` to use the root prim's transform.
           - **Root Path**: optional explicit path for the merged result; defaults to the first entry in **Mesh Prim Paths**.
           - **Spatial Mode** / **Spatial Threshold** / **Spatial Vertex Count**: leave at defaults unless you need spatial grouping.

      5. **Add prerequisite cleanup steps (optional but recommended).** Click **Add Scene Optimizer Process** twice more and add **Mesh Cleanup** (``meshCleanup``) followed by **Generate Normals** (``generateNormals``). Drag the handles in the top-left of each process card so they execute before **Merge Meshes**. This matches the pipeline the URDF/MJCF importer runs internally.

      6. **Execute and verify.**

         - Click **Execute All**. The console log reports the operations as they run.
         - Inspect the stage. Each merge group is replaced by a single mesh prim under the configured **Root Path**. If **Original Geom Option** was set to ``1``, the source meshes remain in the stage as deactivated prims.
         - Save the result with **File > Save As**.

      7. **Save the configuration for reuse (optional).** Click **Save Preset** to write the current process stack to a JSON file. The same JSON can be loaded later from this UI, or fed to the Scene Optimizer CLI for batch processing.

      .. note::

         The Scene Optimizer UI executes operations directly on the **active stage** in memory. Save the stage explicitly after merging — the panel does not write to disk on its own.

   .. tab-item:: JSON preset (Scene Optimizer)

      The Scene Optimizer panel reads and writes its own JSON preset format. A minimal preset that mirrors the importer's pipeline (cleanup, normals + UVs, merge) looks like this:

      .. code-block:: json

         [
           {
             "operation": "meshCleanup",
             "paths": [],
             "mergeVertices": true,
             "tolerance": 0.0,
             "mergeBoundaries": true,
             "mergeNeighbors": true,
             "contractDegenerateEdges": true,
             "removeDegenerateFaces": true,
             "removeIsolatedVertices": true,
             "removeDuplicateFaces": true,
             "makeManifold": true
           },
           {
             "operation": "generateNormals",
             "paths": [],
             "binding": 0,
             "replaceExisting": true,
             "weightMode": 0,
             "sharpnessAngle": 60.0,
             "gpuThreshold": 500000
           },
           {
             "operation": "generateProjectionUVs",
             "paths": [],
             "projectionType": 4,
             "useWorldSpaceScales": true,
             "scaleFactor": 0.01,
             "overwriteExisting": true
           },
           {
             "operation": "merge",
             "meshPrimPaths": ["/World/Robot/left_wheel//Mesh*"],
             "considerMaterials": true,
             "materialAlbedoAsVertexColors": false,
             "originalGeomOption": 1,
             "mergePoint": 0,
             "rootPath": "",
             "considerAllAttributes": true,
             "allowSingleMeshes": false,
             "spatialMode": 0,
             "spatialThreshold": 10.0,
             "spatialMaxSize": 0.0,
             "spatialVertexCount": 10000,
             "spatialDebug": false
           }
         ]

      Edit ``meshPrimPaths`` to target the meshes to merge. Use `USD path expressions <https://openusd.org/release/api/class_sdf_path_expression.html>`_ — the ``//`` operator matches descendants at any depth, so ``/World/Robot//Mesh*`` finds every prim named ``Mesh*`` anywhere under ``/World/Robot``.

      Load this file via the Scene Optimizer panel's **Load Preset > Browse...** button.

Refer to the `Scene Optimizer extension documentation <https://docs.omniverse.nvidia.com/extensions/latest/ext_scene-optimizer.html>`_ for the full operation catalog, the bundled preset descriptions, and the Scene Optimizer CLI usage.

.. _isaac_merge_mesh_transformer_profile:

Using the asset transformer
===========================

If you need to chain mesh merging with other USD restructuring rules — schema routing, geometry deduplication, material routing, interface generation — wrap the merge step in an Asset Transformer profile. The :ref:`isaac_sim_app_asset_transformer` ships a **Merge Mesh** profile (``source/extensions/isaacsim.asset.transformer.rules/data/merge_mesh.json``) that runs the same rigid-body-aware merge as the importer:

.. code-block:: json

   {
     "profile_name": "Merge Mesh",
     "version": "1.0",
     "rules": [
       {
         "name": "Merge Meshes",
         "type": "isaacsim.asset.transformer.rules.isaac_sim.merge_mesh.MergeMeshRule",
         "destination": "",
         "params": {},
         "enabled": true
       }
     ],
     "interface_asset_name": null,
     "output_package_root": null,
     "flatten_source": false,
     "base_name": null
   }

The ``MergeMeshRule`` walks all rigid bodies in the stage and applies the Scene Optimizer ``merge`` operation to each body's child visual meshes — no parameters required.

Chain it with ``GeometriesRoutingRule`` and ``MaterialsRoutingRule`` for a full cleanup + merge + dedupe pipeline:

.. code-block:: json

   {
     "profile_name": "Cleanup + Merge + Dedupe",
     "version": "1.0",
     "rules": [
       {
         "name": "Merge Meshes",
         "type": "isaacsim.asset.transformer.rules.isaac_sim.merge_mesh.MergeMeshRule",
         "destination": "",
         "params": {},
         "enabled": true
       },
       {
         "name": "Route Geometries",
         "type": "isaacsim.asset.transformer.rules.perf.geometries.GeometriesRoutingRule",
         "destination": "payloads",
         "params": {
           "geometries_layer": "geometries.usd",
           "instance_layer": "instances.usda",
           "deduplicate": true
         },
         "enabled": true
       },
       {
         "name": "Route Materials",
         "type": "isaacsim.asset.transformer.rules.perf.materials.MaterialsRoutingRule",
         "destination": "payloads",
         "params": {
           "materials_layer": "materials.usda",
           "download_textures": true
         },
         "enabled": true
       }
     ],
     "interface_asset_name": null,
     "output_package_root": null,
     "flatten_source": false,
     "base_name": null
   }

Load the profile via **Tools > Robotics > Asset Editors > Asset Transformer > Load Preset**, set the **Output Directory**, and click **Execute Actions**. Refer to :ref:`isaac_sim_app_asset_transformer_rules` for the complete rule catalog and to :ref:`isaac_sim_app_asset_transformer_tutorials` for Asset Transformer GUI walkthroughs.

.. _isaac_merge_mesh_python_api:

Using the Python API
====================

The ``isaacsim.asset.importer.utils.merge_mesh_utils`` module wraps the Scene Optimizer operations used by the importer. Use it for headless asset preparation, batch processing, or custom asset "massaging" that does not fit the importer or transformer flows.

The code blocks below are taken from a single runnable script, :file:`docs/isaacsim/snippets/robot_setup/merge_mesh.py`, which you can execute with Isaac Sim's ``python.sh``. Pass ``--test`` to import the bundled ``carter.urdf`` test asset and exercise every snippet end-to-end.

.. note::

   The ``omni.scene.optimizer.core`` extension must be enabled before calling these helpers. Standalone scripts must enable it explicitly:

   .. literalinclude:: ../snippets/robot_setup/merge_mesh.py
      :language: python
      :start-after: # <start-enable-scene-optimizer-snippet>
      :end-before: # <end-enable-scene-optimizer-snippet>
      :dedent:

Available helpers:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Function
     - Purpose
   * - ``clean_mesh_operation(stage)``
     - Run ``meshCleanup``: merge duplicate vertices, remove degenerate faces, make manifold.
   * - ``generate_mesh_uv_normals_operation(stage)``
     - Run ``generateNormals`` and ``generateProjectionUVs`` to regenerate per-vertex normals and projected UVs.
   * - ``merge_meshes_operation(stage)``
     - Walk all rigid bodies and merge each body's child visual meshes (returns the number of merged groups).
   * - ``merge_mesh(stage, mesh_paths)``
     - Merge an explicit list of mesh prim paths into a single mesh.

Example: full importer-equivalent pipeline applied to an existing stage

.. literalinclude:: ../snippets/robot_setup/merge_mesh.py
   :language: python
   :start-after: # <start-full-pipeline-snippet>
   :end-before: # <end-full-pipeline-snippet>
   :dedent:

Example: merge a hand-picked set of meshes (replaces the legacy "select prims, click Merge" workflow)

.. literalinclude:: ../snippets/robot_setup/merge_mesh.py
   :language: python
   :start-after: # <start-explicit-merge-snippet>
   :end-before: # <end-explicit-merge-snippet>
   :dedent:

The first prim in the list is used as the merge root and origin, matching the legacy tool's "first selection wins" behavior.

.. _isaac_merge_mesh_operation_reference:

Scene Optimizer operation reference
===================================

For finer control, call ``omni.scene.optimizer.core`` operations directly. Build a ``SceneOptimizerCore`` instance and an ``ExecutionContext`` bound to your stage, then dispatch operations by name with a configuration dict:

.. literalinclude:: ../snippets/robot_setup/merge_mesh.py
   :language: python
   :start-after: # <start-direct-executeoperation-snippet>
   :end-before: # <end-direct-executeoperation-snippet>
   :dedent:

The default configurations the |isaac-sim| importer uses are listed below for reference.

.. literalinclude:: ../snippets/robot_setup/merge_mesh.py
   :language: python
   :start-after: # <start-default-configs-snippet>
   :end-before: # <end-default-configs-snippet>
   :dedent:

The importer sets ``considerMaterials`` to ``False`` because material routing is handled separately by the asset transformer's ``MaterialsRoutingRule``. Set it to ``True`` when running ``merge`` standalone to preserve per-material ``GeomSubset`` partitioning on the merged mesh — this is the Scene Optimizer equivalent of the legacy tool's **Combine Materials** option.

.. _isaac_merge_mesh_migration:

Migrating from the legacy mesh merge tool
=========================================

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Legacy option
     - Scene Optimizer equivalent
   * - **Source Prim** (first selection = origin)
     - Pass mesh paths to ``merge_mesh(stage, paths)``; first path is used as ``rootPath``.
   * - **Clear Parent Transform**
     - Set ``mergePoint`` to ``0`` (world origin) or ``1`` (root prim's transform) in the ``merge`` config.
   * - **Deactivate source assets**
     - Controlled by ``originalGeomOption``: ``0`` keeps originals, ``1`` deactivates them, ``2`` deletes them.
   * - **Combine Materials**
     - Set ``considerMaterials = True`` in the ``merge`` config. Material assignments are preserved as ``GeomSubset`` entries on the merged mesh.
   * - Selecting an empty Xform first to set origin
     - Use ``rootPath`` to specify any prim path as the merge target/origin.

.. _isaac_merge_mesh_see_also:

See also
========

- :ref:`isaac_sim_urdf_importer` — URDF importer with built-in **Merge Mesh** option.
- :ref:`isaac_sim_mjcf_importer` — MJCF importer with built-in **Merge Mesh** option.
- :ref:`isaac_sim_app_asset_transformer` — Rule-based asset transformation framework.
- :ref:`isaac_sim_app_asset_transformer_rules` — ``MergeMeshRule`` reference and other available rules.
- `Scene Optimizer extension documentation <https://docs.omniverse.nvidia.com/extensions/latest/ext_scene-optimizer.html>`_ — Full operation reference for ``omni.scene.optimizer.core``.
