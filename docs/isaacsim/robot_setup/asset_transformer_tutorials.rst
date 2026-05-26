..
  Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_asset_transformer_tutorials:

Asset Transformer Tutorials
===========================

These tutorials walk through common Asset Transformer workflows step by step. Each tutorial builds on the previous one, so it is recommended to follow them in order.

For an in-depth explanation of the UI and concepts, refer to :ref:`isaac_sim_app_asset_transformer`.

Open the Asset Transformer from **Tools > Robotics > Asset Editors > Asset Transformer** before starting.


.. _asset_transformer_tutorial_existing_profile:

Tutorial 1: Transform an Asset Using the Isaac Sim Structure Profile
====================================================================

This tutorial demonstrates how to transform a robot USD asset into the recommended |isaac-sim_short| asset structure using the built-in **Isaac Sim Structure** profile.


Prerequisites
-------------

- A robot USD asset loaded in the stage, or available on disk. This tutorial uses a sample robot from ``Isaac/Robots/`` in the Nucleus assets. For this tutorial, we will use the ``Isaac/Robots/Fraunhofer/Evobot/evobot.usd`` asset.


Instructions
------------

Select the Input Asset
^^^^^^^^^^^^^^^^^^^^^^

#. In the **Input Section**, select **Active Stage** to transform the currently open stage, or select **Pick File** and browse to a robot USD file on disk.
#. Set the **Output Directory** to a writable folder where the transformed asset package will be saved (for example, ``/tmp/my_robot_transformed/``).
#. Check **Load Restructured File** if you want the output file to open automatically after execution.

.. image:: /images/isim_6.0_full_ext-isaacsim.asset.transformer-1.0.0_gui_select_input.png
   :align: center
   :width: 80%
   :alt: Selecting the input asset and output directory

Load the Built-in Profile
^^^^^^^^^^^^^^^^^^^^^^^^^

#. In the **Actions Section**, click the **Load Preset** button.
#. From the recent presets menu, select **Isaac Sim Structure**.
#. The action list populates with all the rules defined in the Isaac Sim Structure profile.

.. image:: /images/isim_6.0_full_ext-isaacsim.asset.transformer-1.0.0_gui_load_preset.png
   :align: center
   :width: 80%
   :alt: Loading the Isaac Sim Structure preset

#. Expand one or two rules in the action list to inspect their parameters. Each rule shows its **Rule Type**, **Destination**, and **Parameters**.

.. image:: /images/isim_6.0_full_ext-isaacsim.asset.transformer-1.0.0_gui_inspect_rules.png
   :align: center
   :width: 80%
   :alt: Inspecting rule parameters in the action list

Execute the Transformation
^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Click **Execute Actions** in the Execute Section. The button is enabled when at least one action is enabled and an output directory is set.
#. Wait for the pipeline to complete. The console log displays progress for each rule.

.. image:: /images/isim_6.0_full_ext-isaacsim.asset.transformer-1.0.0_gui_execute.png
   :align: center
   :width: 80%
   :alt: Executing the transformation pipeline

Verify the Output
^^^^^^^^^^^^^^^^^

#. Since **Load Restructured File** was checked, the transformed asset opens automatically. Notice the loaded asset does not contain the ground plane anymore, as it was not in the default prim of the original robot asset. This is expected and desired. 
#. Inspect the output folder structure. It should follow the :ref:`Isaac Sim Asset Structure <isaac_sim_app_reference_asset_structure>`:

.. code-block:: text

   output_directory/
   ├── payloads/
   │   ├── base.usd
   │   ├── robot.usda
   │   ├── geometries.usd
   │   ├── instances.usda
   │   ├── materials.usda
   │   ├── Textures/
   │   │   └── ...
   │   └── Physics/
   │       ├── physics.usda
   │       ├── physx.usda
   │       └── mujoco.usda
   ├── <asset_name>.usda          (interface layer)
   └── transform_report.json

#. Inspect the robot prim structure, and verify that all meshes are now added through a reference, and the former looks scope is now empty, since all materials are now added to the materials.usda layer, and added through the meshes. 
   
   .. image:: /images/isim_6.0_full_ext-isaacsim.asset.transformer-1.0.0_gui_robot_structure.png
      :align: center
      :width: 80%
      :alt: Robot prim structure after transformation
#. Inspect the default prim properties, and verify that there is a Variant set for the physics engine, with the physx variant selected.

#. Open ``transform_report.json`` to review per-rule execution logs and confirm all rules completed successfully.


.. _asset_transformer_tutorial_create_profile:

Tutorial 2: Creating a New Profile
===================================

This tutorial demonstrates how to build a custom transformation profile from scratch. The example profile routes physics schemas and materials into dedicated layers, a common workflow for assets that do not need the full Isaac Sim Structure treatment.


Instructions
------------

Clear the Action List
^^^^^^^^^^^^^^^^^^^^^

#. Click **Clear All Actions** to start with an empty pipeline.
#. Expand the **Profile Settings** frame and fill in the metadata:

   - **Profile Name**: ``My Custom Profile``
   - **Version**: ``1.0``
   - **Base Name**: ``base.usd``
   - **Flatten Source**: Leave unchecked unless your source asset has complex sublayer composition you want to flatten first.

.. image:: /images/isim_6.0_full_ext-isaacsim.asset.transformer-1.0.0_gui_profile_settings.png
   :align: center
   :width: 80%
   :alt: Configuring profile settings

Add a Schema Routing Rule
^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Click **Add Action** to add a new rule to the pipeline.
#. Expand the new action and set:

   - **Rule Type**: Search for ``SchemaRoutingRule`` and select ``isaacsim.asset.transformer.rules.core.schemas.SchemaRoutingRule``.
   - **Name**: ``Route Physics Schemas``
   - **Destination**: ``payloads/Physics``
   - **Parameters**:

     - ``stage_name``: ``physics.usda``
     - ``schemas``: ``["Physics*", "Newton*"]`` (Click on the [+] button to add a new schema line per item in the list)

.. image:: /images/isim_6.0_full_ext-isaacsim.asset.transformer-1.0.0_gui_add_schema_rule.png
   :align: center
   :width: 80%
   :alt: Configuring the Schema Routing Rule

Add a Materials Routing Rule
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Click **Add Action** again to add a second rule.
#. Expand it and set:

   - **Rule Type**: Search for ``MaterialsRoutingRule`` and select ``isaacsim.asset.transformer.rules.perf.materials.MaterialsRoutingRule``.
   - **Name**: ``Route Materials``
   - **Destination**: ``payloads``
   - **Parameters**:

     - ``materials_layer``: ``materials.usda``
     - ``textures_folder``: ``Textures``
     - ``deduplicate``: ``true``
     - ``download_textures``: ``true``

.. image:: /images/isim_6.0_full_ext-isaacsim.asset.transformer-1.0.0_gui_add_materials_rule.png
   :align: center
   :width: 80%
   :alt: Configuring the Materials Routing Rule

Add a Geometry Deduplication Rule
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Click **Add Action** one more time.
#. Expand and set:

   - **Rule Type**: Search for ``GeometriesRoutingRule`` and select ``isaacsim.asset.transformer.rules.perf.geometries.GeometriesRoutingRule``.
   - **Name**: ``Deduplicate Geometries``
   - **Destination**: ``payloads``
   - **Parameters**:

     - ``geometries_layer``: ``geometries.usd``
     - ``instance_layer``: ``instances.usda``
     - ``deduplicate``: ``true``
     - ``save_base_as_usda``: ``true``

.. image:: /images/isim_6.0_full_ext-isaacsim.asset.transformer-1.0.0_gui_add_geometry_rule.png
   :align: center
   :width: 80%
   :alt: Configuring the Geometries Routing Rule

Review the Pipeline
^^^^^^^^^^^^^^^^^^^

The action list now contains three rules in order:

1. Route Physics Schemas
2. Route Materials
3. Deduplicate Geometries

Verify execution order is correct. Drag actions to reorder if needed. Use the checkboxes to disable individual rules during testing.

.. image:: /images/isim_6.0_full_ext-isaacsim.asset.transformer-1.0.0_gui_review_pipeline.png
   :align: center
   :width: 80%
   :alt: Reviewing the three-rule custom pipeline

.. note::

   Rule execution order matters. Rules execute sequentially and each rule operates on the working stage as modified by the previous rule. Place schema routing rules before material and geometry rules so that schemas are separated before deduplication occurs.


.. _asset_transformer_tutorial_save_profile:

Tutorial 3: Saving a Profile
=============================

After building the custom profile in :ref:`Tutorial 2 <asset_transformer_tutorial_create_profile>`, save it for reuse.


Instructions
------------

#. Verify the profile metadata by expanding the **Profile Settings** frame. Confirm the **Profile Name**, **Version**, and other fields are correct.
#. Click the **Save Preset** button in the Actions Section.
#. In the file picker, navigate to the desired save location and enter a filename (for example, ``my_custom_profile.json``).
#. Click **Save**.


The profile is saved as a JSON file and added to the recent presets list for quick loading in the future.

Verify the saved file by opening it in a text editor. The structure matches the :ref:`Rule Profile format <isaac_sim_app_asset_transformer>`:

.. code-block:: json

   {
      "profile_name": "My Custom Profile",
      "version": "1.0",
      "rules": [
         {
            "name": "Route Physics Schemas",
            "type": "isaacsim.asset.transformer.rules.core.schemas.SchemaRoutingRule",
            "destination": "payloads/Physics",
            "params": {
            "schemas": [
               "Physics*",
               "Newton*"
            ],
            "ignore_schemas": [],
            "stage_name": "physics.usda",
            "prim_names": [
               ".*"
            ],
            "ignore_prim_names": []
            },
            "enabled": true
         },
         {
            "name": "Route Materials",
            "type": "isaacsim.asset.transformer.rules.perf.materials.MaterialsRoutingRule",
            "destination": "payloads",
            "params": {
            "scope": "/",
            "materials_layer": "materials.usda",
            "textures_folder": "Textures",
            "deduplicate": true,
            "download_textures": true
            },
            "enabled": true
         },
         {
            "name": "Deduplicate Geometries",
            "type": "isaacsim.asset.transformer.rules.perf.geometries.GeometriesRoutingRule",
            "destination": "payloads",
            "params": {
            "scope": "/",
            "geometries_layer": "geometries.usd",
            "instance_layer": "instances.usda",
            "deduplicate": true,
            "save_base_as_usda": true,
            "verbose": false
            },
            "enabled": true
         }
      ],
      "flatten_source": false,
      "base_name": "base.usd"
   }


.. _asset_transformer_tutorial_modify_profile:

Tutorial 4: Modifying a Rule Profile
=====================================

This tutorial demonstrates how to load an existing profile, modify its rules and parameters, and re-save it. The example modifies the profile saved in :ref:`Tutorial 3 <asset_transformer_tutorial_save_profile>` to add the Interface Connection Rule and change geometry deduplication settings.


Instructions
------------

Load the Existing Profile
^^^^^^^^^^^^^^^^^^^^^^^^^

#. Click **Load Preset** and select the ``my_custom_profile.json`` file saved previously. The action list populates with the three rules from Tutorial 3.



Add a New Rule
^^^^^^^^^^^^^^

#. Click **Add Action** to add a fourth rule.
#. Expand it and set:

   - **Rule Type**: ``Interface Connection Rule``
   - **Name**: ``Connect Interfaces``
   - **Destination**: ``payloads``
   - **Parameters**:

     - ``Base Layer``: ``payloads/base.usda``
     - ``Base Connection Type``: ``Reference``
     - ``Generate Folder Variants``: ``true``
     - ``Payloads Folder``: ``payloads``
     - ``Custom Connections``: ``[]``
     - ``Default Variant Selections``: ``{}``



Modify an Existing Rule
^^^^^^^^^^^^^^^^^^^^^^^^

#. Expand the **Deduplicate Geometries** rule.
#. Change the ``deduplicate`` parameter from ``true`` to ``false`` to disable deduplication while keeping the geometry routing active.



Reorder the Rules
^^^^^^^^^^^^^^^^^

#. Drag the **Deduplicate Geometries** rule to the second position, so that it is executed before the **Route Materials** rule.


Disable a Rule
^^^^^^^^^^^^^^

#. Uncheck the enable checkbox next to **Route Materials** to disable it without removing it from the pipeline. This is useful for iterating on specific transformations.


Update Profile Metadata
^^^^^^^^^^^^^^^^^^^^^^^^

#. Expand **Profile Settings**.
#. Change the **Version** to ``1.1`` to track the modification.

Save the Modified Profile
^^^^^^^^^^^^^^^^^^^^^^^^^

#. Click **Save Preset**.
#. Overwrite the existing file or choose a new filename.

The final action list now contains four rules:

.. list-table::
   :header-rows: 1
   :widths: 5 30 15 50

   * - #
     - Rule Name
     - Enabled
     - Change
   * - 1
     - Route Physics Schemas
     - Yes
     - (unchanged)
   * - 2
     - Deduplicate Geometries
     - Yes
     - (``deduplicate`` set to ``false``)
   * - 3
     - Route Materials
     - No
     - (disabled)
   * - 4
     - Connect Interfaces
     - Yes
     - (new rule added)

.. _asset_transformer_tutorial_programmatic:

Tutorial 5: Adding an Asset Transform Pipeline Through Code
============================================================

This tutorial demonstrates how to use the Asset Transformer API to run a transformation pipeline programmatically. This is useful for batch processing, CI/CD integration, or embedding asset transformation into custom extensions and workflows.

The code blocks below are taken from a single script, :file:`docs/isaacsim/snippets/robot_setup/asset_transformer_tutorials.py`, which you can run as a standalone app (for example, to list registered rule types) using Isaac Sim's ``python.sh``.


Load and Run a Saved Profile
-----------------------------

The simplest approach is to load an existing profile JSON file and execute it against an input asset.

.. literalinclude:: ../snippets/robot_setup/asset_transformer_tutorials.py
   :start-after: <start-load-and-run-saved-profile-snippet>
   :end-before: <end-load-and-run-saved-profile-snippet>
   :language: python
   :dedent:


Build a Profile Programmatically
----------------------------------

To define a profile entirely in code without a JSON file:

.. literalinclude:: ../snippets/robot_setup/asset_transformer_tutorials.py
   :start-after: <start-build-profile-programmatically-snippet>
   :end-before: <end-build-profile-programmatically-snippet>
   :language: python
   :dedent:


Use the Isaac Sim Structure Profile in Code
--------------------------------------------

To use the built-in Isaac Sim Structure profile programmatically, load it from the extension's data directory:

.. literalinclude:: ../snippets/robot_setup/asset_transformer_tutorials.py
   :start-after: <start-use-isaac-sim-structure-profile-snippet>
   :end-before: <end-use-isaac-sim-structure-profile-snippet>
   :language: python
   :dedent:


Batch-Process Multiple Assets
------------------------------

Combine the API with standard Python to transform multiple assets:

.. literalinclude:: ../snippets/robot_setup/asset_transformer_tutorials.py
   :start-after: <start-batch-process-multiple-assets-snippet>
   :end-before: <end-batch-process-multiple-assets-snippet>
   :language: python
   :dedent:


Save and Inspect the Execution Report
--------------------------------------

The ``ExecutionReport`` returned by ``manager.run()`` can be serialized to JSON for logging or CI validation:

.. literalinclude:: ../snippets/robot_setup/asset_transformer_tutorials.py
   :start-after: <start-save-and-inspect-report-snippet>
   :end-before: <end-save-and-inspect-report-snippet>
   :language: python
   :dedent:


Discover Available Rule Types
------------------------------

To list all registered transformation rules at runtime:

.. literalinclude:: ../snippets/robot_setup/asset_transformer_tutorials.py
   :start-after: <start-discover-available-rule-types-snippet>
   :end-before: <end-discover-available-rule-types-snippet>
   :language: python
   :dedent:

This prints all fully qualified rule class names that can be used in ``RuleSpec.type``. Refer to :ref:`Asset Transformer Rules Reference <isaac_sim_app_asset_transformer_rules>` for documentation on each rule.
