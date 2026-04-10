..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_asset_transformer_rules:

Asset Transformer Rules Reference
=================================

This page provides a reference of all available transformation rules for the Asset Transformer.

For general usage, refer to :ref:`Asset Transformer <isaac_sim_app_asset_transformer>`. For API and custom rule development, refer to :ref:`Asset Transformer API <isaac_sim_app_asset_transformer_api>`.

Rules Overview
--------------

Rules are organized into four packages based on their function:

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Package
     - Rules
     - Purpose
   * - **Core Routing**
     - SchemaRoutingRule, PropertyRoutingRule, PrimRoutingRule, RemoveSchemaRule
     - Route USD opinions to dedicated layers
   * - **Performance**
     - MaterialsRoutingRule, GeometriesRoutingRule
     - Optimize assets through deduplication and instancing
   * - **Structure**
     - FlattenRule, VariantRoutingRule, InterfaceConnectionRule
     - Reorganize USD composition structure
   * - **Isaac Sim**
     - RobotSchemaRule, MakeListsNonExplicitRule, PhysicsJointPoseFixRule
     - Apply Isaac Sim-specific transformations

Available Rules
---------------

Select a category tab to view available rules. Expand each rule for detailed parameters and execution logic.

.. tab-set::

   .. tab-item:: Core Routing

      These rules route USD opinions (schemas, properties, prims) from source layers to dedicated destination layers. The routing process preserves composition semantics by creating override opinions in the destination layer while removing the original opinions from source layers.

      .. dropdown:: SchemaRoutingRule
         :color: primary

         Routes applied API schemas and their associated properties to a separate layer. This enables modular organization where physics schemas, robot schemas, or other API schemas can be selectively loaded.

         **Fully Qualified Type**: ``isaacsim.asset.transformer.rules.core.schemas.SchemaRoutingRule``

         **Parameters**:

         .. list-table::
            :header-rows: 1
            :widths: 20 15 65

            * - Parameter
              - Type
              - Description
            * - ``schemas``
              - list
              - List of API schema patterns to route. Supports wildcards (for example, ``Physics*`` matches ``PhysicsRigidBodyAPI``, ``PhysicsMassAPI``)
            * - ``ignore_schemas``
              - list
              - Schema patterns to exclude from routing. Overrides positive matches from ``schemas``.
            * - ``stage_name``
              - str
              - Output USD filename (default: ``schemas.usda``)
            * - ``prim_names``
              - list
              - Wildcard patterns to filter which prim names to process (default: ``["*"]`` matches all)
            * - ``ignore_prim_names``
              - list
              - Prim name patterns to exclude from processing

         **Execution Logic**:

         1. **Schema Discovery**: Traverses all prims in the stage and collects applied API schemas matching the specified patterns.
         2. **Property Namespace Resolution**: For each matched schema, determines the property namespace prefix (for example, ``PhysicsRigidBodyAPI`` uses ``physics:`` namespace, ``PhysicsDriveAPI:angular`` uses ``drive:angular:``).
         3. **Schema Transfer**: Uses USD's ``TokenListOp`` to remove the schema token from the source layer's ``apiSchemas`` metadata and prepend it to the destination layer.
         4. **Property Transfer**: Copies all properties belonging to the schema namespace from the source layer to the destination layer using ``Sdf.CopySpec``, then removes them from the source.
         5. **Layer Management**: Sets the destination layer's default prim to match the source and saves both layers.

      .. dropdown:: PropertyRoutingRule
         :color: primary

         Routes properties matching name patterns to a separate layer. This allows organizing specific property namespaces (for example, physics properties, custom attributes) into modular layers.

         **Fully Qualified Type**: ``isaacsim.asset.transformer.rules.core.properties.PropertyRoutingRule``

         **Parameters**:

         .. list-table::
            :header-rows: 1
            :widths: 20 15 65

            * - Parameter
              - Type
              - Description
            * - ``properties``
              - list
              - Regular expression patterns to match property names (for example, ``physics:.*`` matches all physics namespace properties)
            * - ``ignore_properties``
              - list
              - Regex patterns to exclude from routing
            * - ``stage_name``
              - str
              - Output USD filename (default: ``properties.usda``)
            * - ``scope``
              - str
              - Root prim path to limit the search scope (default: ``/`` searches entire stage)
            * - ``prim_names``
              - list
              - Wildcard patterns to filter which prim names to process
            * - ``ignore_prim_names``
              - list
              - Prim name patterns to exclude

         **Execution Logic**:

         1. **Pattern Compilation**: Compiles the provided regex patterns for efficient matching.
         2. **Property Discovery**: Iterates through all attributes and relationships on prims within the scope, checking names against the compiled patterns.
         3. **Property Copy**: For each matching property, copies the spec from the strongest opinion in the prim stack to the destination layer using ``Sdf.CopySpec``.
         4. **Source Removal**: Removes the property spec from all source layers in the prim stack (except the destination layer) to prevent duplicate opinions.
         5. **Layer Finalization**: Exports the destination layer and saves all modified source layers.

      .. dropdown:: PrimRoutingRule
         :color: primary

         Routes entire prims matching type patterns to a separate layer. This enables organizing physics prims, render prims, or other typed prims into modular layers.

         **Fully Qualified Type**: ``isaacsim.asset.transformer.rules.core.prims.PrimRoutingRule``

         **Parameters**:

         .. list-table::
            :header-rows: 1
            :widths: 20 15 65

            * - Parameter
              - Type
              - Description
            * - ``prim_types``
              - list
              - Prim type patterns to route. Supports wildcards (for example, ``Physics*`` matches ``PhysicsJoint``, ``PhysicsScene``)
            * - ``ignore_prim_types``
              - list
              - Prim type patterns to exclude from routing
            * - ``stage_name``
              - str
              - Output USD filename (default: ``prims.usda``)
            * - ``scope``
              - str
              - Root prim path to limit the search scope (default: ``/``)
            * - ``prim_names``
              - list
              - Wildcard patterns to filter which prim names to process
            * - ``ignore_prim_names``
              - list
              - Prim name patterns to exclude

         **Execution Logic**:

         1. **Type Matching**: Collects all prims within the scope whose type name matches the specified patterns using ``fnmatch``.
         2. **Composed Copy**: Copies the complete composed prim definition (including all properties, metadata, and applied schemas) to the destination layer.
         3. **Complete Removal**: Removes the prim spec from all source layers, including explicitly deleting all property specs (to handle override properties authored by other rules like ``SchemaRoutingRule``), clearing ``apiSchemas`` metadata, and deleting the prim spec from parent namespaces.
         4. **Layer Management**: Exports the destination layer and saves modified source layers.

      .. dropdown:: RemoveSchemaRule
         :color: primary

         Removes specific applied API schemas (and optionally their associated properties) from a target layer. Useful for stripping simulator-specific schemas when preparing an asset for a different physics backend.

         **Fully Qualified Type**: ``isaacsim.asset.transformer.rules.core.remove_schema.RemoveSchemaRule``

         **Parameters**:

         .. list-table::
            :header-rows: 1
            :widths: 20 15 65

            * - Parameter
              - Type
              - Description
            * - ``stage_name``
              - str
              - Target USD filename to edit (for example, ``mujoco.usda``)
            * - ``schema_patterns``
              - list
              - Wildcard patterns matching API schema names to remove (for example, ``PhysicsDriveAPI.*``)
            * - ``prim_path_patterns``
              - list
              - Regex patterns limiting which prim paths are affected (default: ``[".*"]``)
            * - ``clear_properties``
              - bool
              - Also remove properties belonging to the matched schema namespaces (default: ``False``)

         **Execution Logic**:

         1. **Pattern Matching**: Iterates over all prims in the target layer, matching applied API schemas against the specified wildcard patterns.
         2. **Schema Removal**: Removes matching schema tokens from each prim's ``apiSchemas`` metadata using ``TokenListOp`` manipulation.
         3. **Property Cleanup**: If ``clear_properties`` is enabled, removes all properties in the matched schema namespace from the prim spec.
         4. **Layer Save**: Saves the modified layer.

   .. tab-item:: Performance

      These rules optimize assets for better simulation and rendering performance through deduplication and instancing.

      .. dropdown:: MaterialsRoutingRule
         :color: primary

         Routes material prims to a shared layer with global deduplication, creates instanceable references at original locations, and transfers texture/MDL assets to a designated folder.

         **Fully Qualified Type**: ``isaacsim.asset.transformer.rules.perf.materials.MaterialsRoutingRule``

         **Parameters**:

         .. list-table::
            :header-rows: 1
            :widths: 20 15 65

            * - Parameter
              - Type
              - Description
            * - ``scope``
              - str
              - Root prim path to limit material search (default: ``/``)
            * - ``materials_layer``
              - str
              - Output USD filename for the materials layer (default: ``materials.usda``)
            * - ``textures_folder``
              - str
              - Folder name for texture assets relative to destination (default: ``Textures``)
            * - ``deduplicate``
              - bool
              - Enable material deduplication based on content hash (default: ``True``)
            * - ``download_textures``
              - bool
              - Download remote textures (for example, from Nucleus) to local folder (default: ``False``)

         **Execution Logic**:

         1. **Material Discovery**: Finds all material prims (``UsdShade.Material``) within the scope, tracking which layer defines each material. Materials with ``PhysicsMaterialAPI`` applied are skipped — these physics-specific materials remain in the base layer at their original paths so that ``material:binding:physics`` relationships continue to resolve.
         2. **Asset Collection**: Resolves all texture and MDL file paths referenced by materials, handling both local and remote (Nucleus) assets. Parses MDL files to discover embedded texture references.
         3. **Content Hashing**: Computes SHA-256 hashes of each material's content (type, attributes, connections, relationships) using resolved asset paths for consistent deduplication.
         4. **Asset Transfer**: Copies all unique assets to the textures folder with global deduplication. Handles filename collisions by appending numeric suffixes. Updates MDL files to point to transferred textures.
         5. **Material Layer Creation**: Creates a ``/Materials`` scope in the materials layer. For each unique material (by hash), copies the material definition with updated asset paths.
         6. **Instanceable References**: Updates each original material location with an instanceable reference to the deduplicated material in the materials layer.
         7. **Binding Update**: Ensures ``MaterialBindingAPI`` is applied to all prims with material bindings.
         8. **Cleanup**: Removes instanceable references for materials that are not bound to any surface.

      .. dropdown:: GeometriesRoutingRule
         :color: primary

         Routes geometry prims to a shared layer with deduplication and creates a separate instances layer for per-instance overrides. Operates on a fully flattened stage (references and instances already resolved).

         **Fully Qualified Type**: ``isaacsim.asset.transformer.rules.perf.geometries.GeometriesRoutingRule``

         **Parameters**:

         .. list-table::
            :header-rows: 1
            :widths: 20 15 65

            * - Parameter
              - Type
              - Description
            * - ``scope``
              - str
              - Root prim path to limit geometry search (default: ``/``)
            * - ``geometries_layer``
              - str
              - Output USD filename for base geometry definitions (default: ``geometries.usd``)
            * - ``instance_layer``
              - str
              - Output USD filename for instance-specific overrides (default: ``instances.usda``)
            * - ``deduplicate``
              - bool
              - Reuse identical geometry definitions (default: ``True``)
            * - ``save_base_as_usda``
              - bool
              - Save the base stage as USD ASCII format (default: ``True``)
            * - ``verbose``
              - bool
              - Log detailed transform decomposition information (default: ``False``)

         **Execution Logic**:

         1. **Geometry Discovery**: Identifies all geometry prims (Mesh, Gprim types) within the scope.
         2. **Content Hashing**: Computes geometry hashes based on mesh data (points, face counts, indices), transforms, and intrinsic properties (type-specific attributes like ``subdivisionScheme``, ``orientation``).
         3. **Intrinsic vs Instance Properties**: Separates intrinsic geometry properties (mesh data, UVs, normals, tangents) from instance-specific properties (visual material bindings, applied schemas like CollisionAPI, custom attributes). Physics-purpose material bindings (``material:binding:physics``) are preserved as-is in the instance delta, pointing to their original target paths in the base layer rather than being rerouted through ``VisualMaterials``.
         4. **Geometry Layer Creation**: Creates geometry definitions under ``/Geometries/{name}/{name}`` in the geometries layer. Identical geometries share the same definition.
         5. **Instance Layer Creation**: Creates instance entries capturing per-instance deltas: material bindings, applied API schemas, transform overrides, and custom properties.
         6. **Base Stage Update**: Updates the base stage to reference the geometry definitions, replacing original geometry prims with instanceable references.
         7. **Delta Coalescing**: Groups instances with identical deltas to reduce redundancy in the instances layer.

   .. tab-item:: Structure

      These rules reorganize USD composition structure for modular asset organization.

      .. dropdown:: FlattenRule
         :color: primary

         Flattens the original input stage into a single layer with optional variant selection. This creates a neutral base representation suitable for subsequent transformation rules.

         **Fully Qualified Type**: ``isaacsim.asset.transformer.rules.structure.flatten.FlattenRule``

         **Parameters**:

         .. list-table::
            :header-rows: 1
            :widths: 20 15 65

            * - Parameter
              - Type
              - Description
            * - ``output_path``
              - str
              - Relative output path within the destination (default: ``base.usda``)
            * - ``clear_variants``
              - bool
              - Clear all variant selections before flattening to produce a neutral base (default: ``True``)
            * - ``selected_variants``
              - dict
              - Dictionary mapping variant set names to variant selections. Only applies to variant sets on the default prim. Example: ``{"Physics": "PhysX", "Gripper": "None"}``
            * - ``case_insensitive``
              - bool
              - Match variant names case-insensitively when applying selections (default: ``True``)

         **Execution Logic**:

         1. **Original Stage Access**: Opens the original input stage (before any processing) to preserve relative asset paths that would be broken after initial manager processing.
         2. **Variant Selection Application**: If ``selected_variants`` is specified, applies the variant selections to the default prim's variant sets. Case-insensitive matching finds variants like ``physx`` when ``PhysX`` is requested.
         3. **Variant Clearing**: If ``clear_variants`` is enabled, iterates through all prims and clears their ``variantSelections`` metadata to ensure a neutral base.
         4. **Stage Flattening**: Uses ``Usd.Stage.Flatten()`` to compose all layers, references, and payloads into a single layer.
         5. **Export**: Exports the flattened layer to the destination path. Handles USD layer caching by transferring content to cached layers when necessary.
         6. **Stage Switch**: Returns the output path so the manager switches subsequent rules to operate on the flattened stage.

      .. dropdown:: VariantRoutingRule
         :color: primary

         Routes variant set contents to separate layer files. Each variant is extracted into an individual USDA file organized by variant set folder. Handles composition arcs within variants by copying source assets and remapping dependencies.

         **Fully Qualified Type**: ``isaacsim.asset.transformer.rules.structure.variants.VariantRoutingRule``

         **Parameters**:

         .. list-table::
            :header-rows: 1
            :widths: 20 15 65

            * - Parameter
              - Type
              - Description
            * - ``variant_sets``
              - list
              - Optional list of variant set names to process. If empty, all variant sets on the default prim are processed.
            * - ``case_insensitive``
              - bool
              - Convert variant option names to lowercase for output filenames and references (default: ``True``)
            * - ``collect_dependencies``
              - bool
              - Collect external dependencies (referenced assets, textures) into a ``dependencies`` folder (default: ``True``)
            * - ``excluded_variants``
              - list
              - Variant names to exclude from full processing. Excluded variants get empty USDA files created but contents are not processed. Useful for variants like ``none``, ``default``.

         **Execution Logic**:

         1. **Variant Set Analysis**: Examines the default prim's variant sets and builds a map of variant assets (payloads/references within each variant) to variant names.
         2. **Variant File Mapping**: Creates a mapping from original variant asset paths to new output file paths (``{VariantSetName}/{variant_name}.usda``).
         3. **Dependency Collection**: Uses ``UsdUtils.ComputeAllDependencies`` to discover all assets referenced by each variant's source (sublayers, references, payloads, textures). Copies dependencies to a ``dependencies`` folder.
         4. **Asset Copy with Remapping**: For variants with payloads/references, copies the source asset to the variant output file. Uses ``UsdUtils.ModifyAssetPaths`` to remap all internal paths to point to new variant files or collected dependencies.
         5. **Delta Application**: Applies any direct overrides from the variant spec (attributes, relationships, child prims, composition arcs) as the strongest opinion on top of the copied content.
         6. **Inter-Variant Remapping**: Updates references between variants to point to the new variant files. Remaps paths in collected dependencies to ensure consistency.
         7. **Excluded Variant Handling**: Creates empty USDA files with just the default prim for excluded variants.

      .. dropdown:: InterfaceConnectionRule
         :color: primary

         Generates the final interface layer with composition arcs to organize USD assets. Creates the top-level asset file that references/payloads the base asset and optionally generates variant sets from folder structure.

         **Fully Qualified Type**: ``isaacsim.asset.transformer.rules.structure.interface.InterfaceConnectionRule``

         **Parameters**:

         .. list-table::
            :header-rows: 1
            :widths: 20 15 65

            * - Parameter
              - Type
              - Description
            * - ``base_layer``
              - str
              - Relative path to the base USD layer to connect (default: ``payloads/base.usda``)
            * - ``base_connection_type``
              - str
              - How to connect the base layer: ``Reference`` (default), ``Payload``, or ``Sublayer``
            * - ``generate_folder_variants``
              - bool
              - Generate variant sets from payloads folder structure (default: ``False``). Each subfolder becomes a variant set, each USD file becomes a variant option.
            * - ``payloads_folder``
              - str
              - Folder to scan for variant set organization (default: ``payloads``)
            * - ``connections``
              - list
              - List of custom connection specifications. Each spec is a dictionary with ``asset_path`` (layer to modify, empty for interface layer), ``target_path`` (layer to connect), and ``connection_type`` (``Reference``, ``Payload``, ``Sublayer``, or ``Inherit``).
            * - ``default_variant_selections``
              - dict
              - Dictionary mapping variant set names to default variant selections. Unspecified variant sets default to ``none``.

         **Execution Logic**:

         1. **Interface Layer Creation**: Creates the interface layer at the package root, named after the original input asset.
         2. **Default Prim Setup**: Ensures the default prim exists as an Xform in the interface layer.
         3. **Base Connection**: Connects the base layer to the default prim using the specified connection type (prepends Reference or Payload to the prim's list, or inserts Sublayer).
         4. **Folder Variant Generation**: If enabled, scans the payloads folder for subfolders containing USD files. Each subfolder becomes a variant set, with a ``none`` variant (no payload) and variants for each USD file (payloaded).
         5. **Custom Connections**: Applies custom connection specifications. For Sublayer connections, adds to the layer's sublayer paths. For Reference/Payload connections, adds to the default prim. Can modify the interface layer or any specified asset layer.
         6. **Extraneous Prim Recovery**: Scans the base layer for root-level prims outside ``defaultPrim`` (e.g. ``/Render``, ``/PhysicsScene``). Copies each into the interface layer at the same root level using ``Sdf.CopySpec``, then removes them from the base layer and saves it. This keeps those prims reachable in the composed stage and makes the pipeline idempotent — prims that would not survive a reference-based round-trip are promoted to the interface layer where they persist across re-transforms.
         7. **Variant Selection Defaults**: Sets default variant selections on the interface layer's default prim.

   .. tab-item:: Isaac Sim

      These rules apply Isaac Sim-specific transformations for robot assets.

      .. dropdown:: RobotSchemaRule
         :color: primary

         Applies the Isaac Sim robot schema to a target prim. Uses the robot schema utilities to detect articulation structure and populate robot relationships (links, joints, sites).

         **Fully Qualified Type**: ``isaacsim.asset.transformer.rules.isaac_sim.robot_schema.RobotSchemaRule``

         **Parameters**:

         .. list-table::
            :header-rows: 1
            :widths: 20 15 65

            * - Parameter
              - Type
              - Description
            * - ``prim_path``
              - str
              - Target prim path to apply the Robot schema. Defaults to the stage default prim if not specified.
            * - ``stage_name``
              - str
              - Output USD filename for robot schema opinions (default: ``robot_schema.usda``)
            * - ``add_sites``
              - bool
              - Add sites to the robot by scanning child Xforms with no children under Link prims (default: ``True``)
            * - ``sites_last``
              - bool
              - If ``False``, sites are added after their parent link in the relationship order. If ``True``, all sites are added at the end. (default: ``False``)
            * - ``sublayer``
              - str
              - Optional sublayer path to include on the working stage prior to applying the robot schema. Useful for including physics layers that define joints.

         **Execution Logic**:

         1. **Destination Layer Setup**: Creates or opens the destination layer for robot schema opinions. Adds it as a sublayer to the source stage.
         2. **Sublayer Insertion**: If a sublayer is specified (e.g., physics layer), inserts it as the strongest sublayer on the source stage.
         3. **Schema Detection**: Checks if ``RobotAPI`` is already applied to the target prim.
         4. **Schema Application**:

            - **New Schema**: Applies ``RobotAPI`` to the target prim, then calls ``PopulateRobotSchemaFromArticulation`` to detect the articulation structure and populate ``isaac:links``, ``isaac:joints``, and optionally ``isaac:sites`` relationships.
            - **Existing Schema**: Calls ``RecalculateRobotSchema`` to update the schema while preserving existing relationship order. Removes invalid entries and appends newly discovered links/joints/sites.

         5. **Schema Update**: Updates deprecated schema versions if necessary.
         6. **Layer Isolation**: Saves the edit layer and discards any changes to the root layer (since edits are isolated to the robot schema layer).

      .. dropdown:: MakeListsNonExplicitRule
         :color: primary

         Converts explicit list ops on prim metadata and properties to non-explicit list ops (prepended or appended). This is important for USD composition because explicit lists override all weaker opinions, while prepended/appended lists combine with weaker opinions.

         **Fully Qualified Type**: ``isaacsim.asset.transformer.rules.isaac_sim.make_lists_non_explicit.MakeListsNonExplicitRule``

         **Parameters**:

         .. list-table::
            :header-rows: 1
            :widths: 20 15 65

            * - Parameter
              - Type
              - Description
            * - ``metadata_names``
              - list
              - Prim metadata names to convert. Supports wildcards (for example, ``api*`` matches ``apiSchemas``).
            * - ``property_names``
              - list
              - Prim property names to convert. Supports wildcards (for example, ``material:*``).
            * - ``list_op_type``
              - str
              - Target list operation type: ``prepend`` (items go before weaker opinions) or ``append`` (items go after). Default: ``prepend``.

         **Execution Logic**:

         1. **Pattern Matching**: Uses ``fnmatch`` to match metadata and property names against the specified patterns.
         2. **Metadata Conversion**: For matching prim metadata (like ``apiSchemas``):

            - Extracts explicit items from the ``TokenListOp``
            - Creates a new ``TokenListOp`` with items as prepended or appended (not explicit)
            - Sets the new list op on the prim spec

         3. **Relationship Conversion**: For matching relationships:

            - Extracts explicit target paths from the ``targetPathList``
            - Recreates the relationship spec (preserving other metadata like variability, custom flag)
            - Re-authors targets using ``Prepend()`` or ``Append()`` calls instead of explicit list

         4. **Attribute Connection Conversion**: For matching attribute connections:

            - Extracts explicit connection paths
            - Clears the connection list and re-authors using ``Prepend()`` or ``Append()``

         5. **Layer Management**: Saves all modified layers.

      .. dropdown:: PhysicsJointPoseFixRule
         :color: primary

         Corrects physics joint local poses after upstream rules (such as GeometriesRoutingRule) change body world transforms. Compares joint world poses computed from the original input asset against the current working stage and updates ``localPos0/1`` and ``localRot0/1`` attributes on any joint whose world pose has drifted.

         **Fully Qualified Type**: ``isaacsim.asset.transformer.rules.isaac_sim.physics_joint_pose_fix.PhysicsJointPoseFixRule``

         **Parameters**:

         .. list-table::
            :header-rows: 1
            :widths: 20 15 65

            * - Parameter
              - Type
              - Description
            * - ``original_composition_path``
              - str
              - Optional ``Usd.Stage`` object or explicit path to the original composition stage. Defaults to the ``input_stage`` passed by the transformer manager (the unmodified source asset).
            * - ``tolerance_position``
              - float
              - Maximum allowed position difference (Euclidean distance) when comparing joint world poses (default: ``1e-6``)
            * - ``tolerance_orientation``
              - float
              - Minimum quaternion dot-product deviation from 1.0 when comparing joint world poses (default: ``1e-6``)

         **Execution Logic**:

         1. **Original Stage**: Opens the original input asset (before any transformer rules ran) via ``input_stage``.
         2. **Joint Discovery**: Traverses the working stage for all ``UsdPhysics.Joint`` prims.
         3. **World Pose Comparison**: For each joint, computes the joint world pose from both ``body0`` and ``body1`` on the original stage and on the working stage using ``local_pose * body_world_transform``.
         4. **Drift Detection**: If the working stage's joint world pose differs from the original beyond the configured tolerance, the affected body side is flagged for correction.
         5. **Local Pose Fix**: Computes the corrective local pose as ``joint_world_orig * inverse(body_world_entry)`` and writes the resulting translation and rotation back to the joint's ``localPos`` and ``localRot`` attributes.
         6. **Layer Save**: Saves the modified edit layer if any corrections were applied.


Idempotency Requirement
-----------------------

All transformation rules **must** be idempotent: running the full profile twice on the same asset (once on the original, then on the first run's output) must produce identical USD layers, with the sole exception of the ``doc`` metadata field which embeds absolute paths. The extension includes an idempotency test (``test_profile_idempotency.py``) that enforces this requirement.

Common sources of non-idempotency to watch for when developing new rules:

- **Floating-point drift** -- Matrix composition/decomposition round-trips introduce noise. Quantize values to a fixed number of significant digits, or read canonical xformOp values directly when possible.
- **Stale composition arcs** -- Extracting content from variant specs can leave behind self-referencing payloads or references on the destination prim. Strip any arcs that were not present in the source.
- **Inconsistent defaultPrim** -- Use ``self.source_stage.GetDefaultPrim()`` (composed stage) rather than ``self.source_stage.GetRootLayer().defaultPrim`` (root layer only) to reliably resolve the default prim across re-transforms.
- **Non-deterministic merge decisions** -- When deciding whether to merge a child into its parent, account for scaffolding prims (e.g. ``VisualMaterials`` scopes, empty overs) left behind by previous runs.
- **Extraneous root-level prims** -- After flattening, root-level prims outside the ``defaultPrim`` hierarchy (e.g. viewport/render artifacts) do not survive a reference-based round-trip. The ``InterfaceConnectionRule`` handles this automatically by moving such prims from the base layer into the interface layer, but custom rules that introduce root-level prims should be aware of this composition constraint.


Rule Type Quick Reference
-------------------------

Use these fully qualified type names in rule profiles:

.. code-block:: text

   # Core Routing
   isaacsim.asset.transformer.rules.core.schemas.SchemaRoutingRule
   isaacsim.asset.transformer.rules.core.properties.PropertyRoutingRule
   isaacsim.asset.transformer.rules.core.prims.PrimRoutingRule
   isaacsim.asset.transformer.rules.core.remove_schema.RemoveSchemaRule

   # Performance
   isaacsim.asset.transformer.rules.perf.materials.MaterialsRoutingRule
   isaacsim.asset.transformer.rules.perf.geometries.GeometriesRoutingRule

   # Structure
   isaacsim.asset.transformer.rules.structure.flatten.FlattenRule
   isaacsim.asset.transformer.rules.structure.variants.VariantRoutingRule
   isaacsim.asset.transformer.rules.structure.interface.InterfaceConnectionRule

   # Isaac Sim
   isaacsim.asset.transformer.rules.isaac_sim.robot_schema.RobotSchemaRule
   isaacsim.asset.transformer.rules.isaac_sim.make_lists_non_explicit.MakeListsNonExplicitRule
   isaacsim.asset.transformer.rules.isaac_sim.physics_joint_pose_fix.PhysicsJointPoseFixRule

