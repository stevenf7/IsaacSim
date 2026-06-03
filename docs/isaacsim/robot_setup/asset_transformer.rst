..
  Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_asset_transformer:

Asset Transformer
=================

The Asset Transformer is a framework for transforming USD assets in |isaac-sim_short|. It provides utilities for batch transforms, schema routing, mesh deduplication, material optimization, and structural reorganization. The transformer operates through a rule-based pipeline where each rule performs a specific transformation on the USD stage, enabling complex multi-step asset optimization workflows.

.. image:: /images/isim_6.0_full_ext-isaacsim.asset.transformer-1.0.0_gui_workflow.png
   :align: center
   :width: 90%
   :alt: Asset Transformer Workflow

The following sections explain the UI and functions behind each part of the Asset Transformer. To see the tool in action with step-by-step walkthroughs, refer to :ref:`isaac_sim_app_asset_transformer_tutorials`.


Purpose
-------

The Asset Transformer addresses key challenges when preparing assets for simulation:

- **Schema Separation**: Extracting physics, robot, and other API schemas into dedicated layers for modularity.
- **Performance Optimization**: Deduplicating geometries and materials to reduce memory usage and improve rendering performance.
- **Structural Reorganization**: Flattening complex hierarchies, routing variants, and creating standardized asset structures.
- **Composition Setup**: Generating interface layers with proper USD composition arcs (references, payloads, sublayers).

The result is a modular, simulation-ready asset structure that follows the :ref:`Isaac Sim Asset Structure <isaac_sim_app_reference_asset_structure>` guidelines.

**Related Documentation**:

- :ref:`Asset Transformer Tutorials <isaac_sim_app_asset_transformer_tutorials>` - Step-by-step practical walkthroughs
- :ref:`Asset Transformer Rules Reference <isaac_sim_app_asset_transformer_rules>` - Complete reference of available transformation rules
- :ref:`Asset Transformer API <isaac_sim_app_asset_transformer_api>` - Programmatic usage and custom rule development


Opening the Asset Transformer
-----------------------------

The Asset Transformer UI is accessible from the menu bar: **Tools > Robotics > Asset Editors > Asset Transformer**.


.. _isaac_sim_app_asset_transformer_ui:

User Interface
--------------

.. image:: /images/isim_6.0_full_ext-isaacsim.asset.transformer-1.0.0_gui_ui.png
   :align: center
   :width: 80%
   :alt: Asset Transformer UI

The window contains three main sections described below. Each section controls a stage of the transformation workflow: selecting input, configuring actions, and executing the pipeline.


Input Section
^^^^^^^^^^^^^

Configure the source asset and output location:

- **Active Stage / Pick File**: Choose between transforming the currently open stage or selecting a file from disk.
- **Output Directory**: Destination folder for the transformed asset package.
- **Load Restructured File**: Automatically open the output file after execution.


Actions Section
^^^^^^^^^^^^^^^

Configure the transformation pipeline:

- **Load Preset**: Load a saved rule profile from a JSON file. Recent presets appear in a quick-access menu.
- **Save Preset**: Save the current configuration as a JSON preset file.
- **Clear All Actions**: Remove all rules from the action list.
- **Profile Settings** (collapsible): Configure profile metadata:

  - **Profile Name**: Display name for the profile
  - **Version**: Version string
  - **Interface Asset**: Output interface asset name
  - **Base Name**: Base stage filename
  - **Flatten Source**: Whether to flatten the source stage before processing

- **Action List**: Ordered list of rules to execute. Each action row shows:

  - Drag handle for reordering
  - Enable/disable checkbox
  - Expansion triangle to reveal configuration
  - Rule name
  - Remove button

- **Add Action**: Add a new rule to the pipeline. Review :ref:`Asset Transformer Rules Reference <isaac_sim_app_asset_transformer_rules>` for available rules.

When an action is expanded, the following configuration options appear:

- **Rule Type**: Searchable dropdown to select the rule implementation. The dropdown lists each rule by its short class name in the **Rule Name** column and bundles rules by scope in the **Package** column.
- **Destination**: Output path for the rule (relative to package root).
- **Parameters**: Dynamic parameter editors generated from the rule's configuration parameters.

.. note::

   The **Rule Type** dropdown shows the short class name (for example, ``SchemaRoutingRule``), while the documentation and saved profiles identify a rule by its *fully qualified type*. The fully qualified type combines the scope shown in the **Package** column with the class name: ``isaacsim.asset.transformer.rules.<package>.<module>.<ClassName>``. For example, the **Rule Name** ``SchemaRoutingRule`` in the **Package** ``core`` corresponds to ``isaacsim.asset.transformer.rules.core.schemas.SchemaRoutingRule``.

   Use the filter icon next to the search field to show only rules from selected packages (``core``, ``perf``, ``structure``, ``isaac_sim``). Refer to the :ref:`Asset Transformer Rules Reference <isaac_sim_app_asset_transformer_rules>` for the fully qualified type of each rule.


Execute Section
^^^^^^^^^^^^^^^

- **Execute Actions**: Run the transformation pipeline. The button is enabled when at least one action is enabled and an output directory is set.


Transformer Manager Process
---------------------------

The ``AssetTransformerManager`` coordinates execution of a rule profile over USD stages.

.. image:: /images/isim_6.0_full_ext-isaacsim.asset.transformer-1.0.0_gui_manager_flow.png
   :align: center
   :width: 85%
   :alt: Asset Transformer Manager Flow

**Process Flow**:

1. **Initialize**: Create an execution report to track results.
2. **Open Source Stage**: Load the input USD stage from the specified path.
3. **Create Base Copy**: Export the source stage to ``{package_root}/payloads/{base_name}``. If ``flatten_source`` is enabled, the stage is flattened first.
4. **Collect External Assets**: Copy external assets (textures, materials) to ``{package_root}/source_assets/`` and update paths to local references.
5. **Execute Rules**: For each enabled rule in the profile:

   - Instantiate the rule with the working stage
   - Execute ``process_rule()``
   - If the rule returns a new stage path, switch to that stage for subsequent rules
   - Collect operation logs and affected stages

6. **Save Working Stage**: Save any unsaved changes to the root layer.
7. **Return Report**: Generate an execution report with per-rule logs and status.

.. note::

   The Asset Transformer is meant to be used with atomic assets (assets that are not composed of other assets, or with external references). If the asset is composed of other assets, or has external references, the Asset Transformer will collect the external assets and include them in the output package.

   Example:

   - Asset is composed of a base asset and a secondary asset (A robot and a Gripper or Sensor).
   - The base asset is the atomic asset.
   - The Asset Transformer will collect the referenced asset (Gripper or Sensor) and include it in the output package.
   - The output package will contain the base asset, and the referenced asset on a single new atomic asset.
   - If the secondary asset is loaded from a variant, it will be included in the variant structure of the new atomic asset.


Rule Profiles
-------------

A rule profile defines a complete transformation pipeline. Profiles are stored as JSON files with the following structure:

.. code-block:: json

   {
     "profile_name": "My Profile",
     "version": "1.0",
     "rules": [
       {
         "name": "Rule Display Name",
         "type": "fully.qualified.rule.ClassName",
         "destination": "output/path",
         "params": {
           "param_name": "value"
         },
         "enabled": true
       }
     ],
     "interface_asset_name": "asset",
     "output_package_root": "/path/to/output",
     "flatten_source": false,
     "base_name": "base.usd"
   }

**Profile Fields**:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Field
     - Description
   * - ``profile_name``
     - Display name for the profile (required)
   * - ``version``
     - Version string
   * - ``rules``
     - Ordered list of rule specifications
   * - ``interface_asset_name``
     - Output interface asset identifier
   * - ``output_package_root``
     - Default output directory
   * - ``flatten_source``
     - Flatten source stage before processing
   * - ``base_name``
     - Base stage filename

**Rule Specification Fields**:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Field
     - Description
   * - ``name``
     - Display name for the rule (required)
   * - ``type``
     - Fully qualified rule class name (required). Review :ref:`Asset Transformer Rules Reference <isaac_sim_app_asset_transformer_rules>`.
   * - ``destination``
     - Output path relative to package root
   * - ``params``
     - Dictionary of parameter overrides
   * - ``enabled``
     - Whether the rule is active


Managing Profiles
^^^^^^^^^^^^^^^^^

**Loading a Profile**:

1. Click the **Load Preset** button in the Actions section.
2. Select a preset from the recent presets menu, or choose **Browse...** to open a file picker.
3. The profile loads and populates the action list.

**Saving a Profile**:

1. Configure the desired rules and parameters.
2. Click the **Save Preset** button.
3. Choose a filename and location in the file picker.
4. The profile is saved as JSON and added to recent presets.

**Editing a Profile**:

1. Expand the **Profile Settings** frame to edit metadata.
2. Expand individual rules to modify their parameters.
3. Drag rules to reorder execution.
4. Use checkboxes to enable or disable rules.
5. Save the modified profile using **Save Preset**.


Transform Report
----------------

The Asset Transformer generates a comprehensive execution report that documents every operation performed during the transformation process. This report is saved as ``transform_report.json`` in the output package root directory.

Report Structure
^^^^^^^^^^^^^^^^

The execution report contains the following information:

**Top-Level Fields**:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Field
     - Description
   * - ``profile``
     - The complete profile configuration used for the transformation
   * - ``input_stage``
     - Path to the original input USD stage
   * - ``package_root``
     - Output directory where transformed assets are written
   * - ``started_at``
     - ISO 8601 timestamp when execution started
   * - ``finished_at``
     - ISO 8601 timestamp when execution completed
   * - ``results``
     - Array of per-rule execution results
   * - ``output_stage_path``
     - Path to the final transformed asset

**Per-Rule Results**:

Each rule's execution result includes:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Field
     - Description
   * - ``rule``
     - The rule specification (name, type, parameters, enabled status)
   * - ``success``
     - Boolean indicating whether the rule completed successfully
   * - ``log``
     - Array of log entries recorded during rule execution
   * - ``affected_stages``
     - List of USD layer identifiers created or modified by the rule
   * - ``error``
     - Error message if the rule failed (null on success)
   * - ``started_at``
     - Timestamp when the rule started
   * - ``finished_at``
     - Timestamp when the rule completed

.. dropdown:: Example Report
   :color: secondary

   .. code-block:: json

      {
        "profile": {
          "profile_name": "Isaac Sim Structure",
          "version": "1.0",
          "rules": ["...truncated..."]
        },
        "input_stage": "/path/to/robot.usd",
        "package_root": "/output/robot_package",
        "started_at": "2024-01-15T10:30:00.000Z",
        "finished_at": "2024-01-15T10:30:45.123Z",
        "output_stage_path": "/output/robot_package/robot.usda",
        "results": [
          {
            "rule": {
              "name": "Route Physics Schemas",
              "type": "isaacsim.asset.transformer.rules.core.schemas.SchemaRoutingRule",
              "destination": "payloads/Physics",
              "params": {"schemas": ["Physics*"], "stage_name": "physics.usda"},
              "enabled": true
            },
            "success": true,
            "log": [
              {"message": "SchemaRoutingRule start destination=payloads/Physics/physics.usda"},
              {"message": "Schema patterns: Physics*"},
              {"message": "Using schemas layer: /output/robot_package/payloads/Physics/physics.usda"},
              {"message": "Moved 3 schema(s) from /World/Robot: PhysicsArticulationRootAPI, PhysicsRigidBodyAPI, PhysicsMassAPI"},
              {"message": "Processed 15 prim(s), moved 42 schema instance(s)"},
              {"message": "SchemaRoutingRule completed"}
            ],
            "affected_stages": ["payloads/Physics/physics.usda"],
            "error": null,
            "started_at": "2024-01-15T10:30:05.000Z",
            "finished_at": "2024-01-15T10:30:08.500Z"
          }
        ]
      }

Using the Report
^^^^^^^^^^^^^^^^

The transform report serves multiple purposes:

- **Debugging**: Identify the rule that failed and why it failed by examining log entries and error messages
- **Auditing**: Review exactly what transformations were applied to an asset
- **Verification**: Confirm that expected schemas, properties, or prims were routed to the correct layers
- **Automation**: Parse the report programmatically to validate the transformation results in CI/CD pipelines

For programmatic access to reports, refer to the :ref:`Asset Transformer API <isaac_sim_app_asset_transformer_api>`.


Isaac Sim Asset Structure Profile
---------------------------------

|isaac-sim_short| includes a default profile called **Isaac Sim Structure** that transforms assets into the recommended :ref:`Isaac Sim Asset Structure <isaac_sim_app_reference_asset_structure>`. This profile is automatically available in the recent presets menu.

.. image:: /images/isim_6.0_full_ext-isaacsim.asset.transformer-1.0.0_gui_output_structure.png
   :align: center
   :width: 70%
   :alt: Asset Transformer Output Structure

The profile executes the following transformation pipeline:

1. **Route Variants**: Extract variant sets to separate files, excluding ``none``, ``default``, and ``physx`` variants.

2. **Flatten Base**: Create a flattened base stage with specific variant selections (for example, Physics: PhysX).

3. **Route Isaac Robot Schemas**: Move Isaac robot schemas (``IsaacRobotAPI``, ``IsaacLinkAPI``, ``IsaacJointAPI``) to ``robot.usda``.

4. **Route Isaac Robot Properties**: Move Isaac robot properties to ``robot.usda``.

5. **Route Geometries**: Deduplicate geometries and create instanceable references in ``geometries.usd`` and ``instances.usda``.

6. **Fix Physics Joint Poses**: Correct physics joint local poses (``localPos0/1``, ``localRot0/1``) that may have been invalidated by the geometry routing step combining parent/child transforms.

7. **Route Materials**: Deduplicate visual materials, download textures, and create ``materials.usda``. Physics materials (those with ``PhysicsMaterialAPI``) are left in the base layer.

8. **Route PhysX Schemas**: Move PhysX schemas to ``Physics/physx.usda``.

9. **Route MuJoCo Schemas/Prims/Properties**: Move MuJoCo-related opinions to ``Physics/mujoco.usda``.

10. **Route Physics Schemas/Prims**: Move general physics schemas and prims to ``Physics/physics.usda``.

11. **Make Robot Schema**: Apply Isaac Sim robot schema and populate robot relationships.

12. **Make API Schemas Non-Explicit**: Convert explicit apiSchemas lists to prepended list ops.

13. **Generate Interface**: Create the final interface layer with:

    - Reference to the base layer
    - Variant sets generated from folder structure
    - Sublayer connections for physics engines (PhysX, MuJoCo)
    - Default variant selections
    - Recovery of extraneous root-level prims (e.g. ``Render``, camera definitions) from the base layer into the interface layer so they remain reachable in the composed stage

**Output Structure**:

The resulting output follows the modular asset structure documented in :ref:`isaac_sim_app_reference_asset_structure`, with:

- Base geometry and hierarchy in ``payloads/base.usd``
- Robot schema in ``payloads/robot.usda``
- Deduplicated geometries in ``payloads/geometries.usd``
- Materials and textures in ``payloads/materials.usda`` and ``payloads/Textures/``
- Physics layers in ``payloads/Physics/``
- Variant options in individual files
- Final composed asset in the interface layer


Tutorials
---------

:ref:`isaac_sim_app_asset_transformer_tutorials`
