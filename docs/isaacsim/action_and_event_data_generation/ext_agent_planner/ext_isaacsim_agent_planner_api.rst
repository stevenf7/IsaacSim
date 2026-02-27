..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_ext_agent_planner_api:

=========================================
IAP Configuration and API Reference
=========================================

This document provides detailed configuration instructions and API reference for the Isaac Agent Planner (IAP). For a quick start guide, see the :doc:`IAP Example Walkthrough <ext_isaacsim_agent_planner_walkthrough>`.


Manual Configuration
--------------------

For production use or custom scenes, configure IAP manually using the steps below.

Prepare Your Data Files
#######################

Create the required JSON data files for your scene.

Actor Data File
^^^^^^^^^^^^^^^

Define the actors in your scene:

.. code-block:: json
   :caption: actors.json

   [
       {
           "id": "Alice",
           "semantic_description": "A female character who can perform various actions",
           "metadata": {
               "actor_type": "human",
               "role": "protagonist",
               "prim_path": "/World/Characters/Alice",
               "semantic_label": "woman"
           },
           "entity_type": "actor"
       },
       {
           "id": "MainCamera",
           "semantic_description": "The primary filming camera",
           "metadata": {
               "actor_type": "camera",
               "role": "main_camera",
               "prim_path": "/World/Cameras/MainCamera",
               "semantic_label": "camera"
           },
           "entity_type": "actor"
       }
   ]


Object Data File
^^^^^^^^^^^^^^^^

Define interactable objects:

.. code-block:: json
   :caption: objects.json

   [
       {
           "id": "CoffeeMug",
           "semantic_description": "A ceramic coffee mug on the counter",
           "metadata": {
               "prim_path": "/World/Props/CoffeeMug",
               "object_type": "pickup_item",
               "location": {"x": 1.5, "y": 2.0, "z": 0.8}
           },
           "entity_type": "object"
       },
       {
           "id": "DiningTable",
           "semantic_description": "A wooden dining table in the center of the room",
           "metadata": {
               "prim_path": "/World/Props/DiningTable",
               "object_type": "surface",
               "location": {"x": 0.0, "y": 0.0, "z": 0.0}
           },
           "entity_type": "object"
       }
   ]


Configure Context Cache Files
#############################

In the *Context Cache Files* panel:

1. **Context Files (Actors & Objects)**:

   - Click **+ Add Context File**
   - Browse to your ``actors.json`` file
   - Click **+ Add Context File** again
   - Browse to your ``objects.json`` file

2. **Node Catalog** (optional):

   - Browse to a node catalog JSON file if you have custom nodes
   - Or leave empty to use default node types

3. **Blackboard File** (optional):

   - Browse to a blackboard definition JSON file
   - Or leave empty for default blackboard setup


Configure Network Settings
##########################

In the *Network Configuration* panel:

1. **Model Config File**:

   - Browse to your ``model_configs.json`` file (defines LLM endpoints)

2. **Node-to-Model Map**:

   - Browse to your ``node_to_model_map.json`` file (maps nodes to specific models)

3. **API Key**:

   - Enter your LLM service API key
   - Or leave empty if using environment variable / agent registry


Configure Output Settings
#########################

In the *Output Settings* panel:

1. **Output Folder**:

   - Set the root folder where generated files will be saved
   - Example: ``/home/user/iap_output``

2. **RAG Cache Folder** (optional):

   - Set a folder for RAG vector store caches
   - Useful for faster subsequent runs with same context


Run the Pipeline
################

1. In the *Scenario Execution* panel, enter your scenario
2. Click **Run Pipeline**
3. Monitor the progress through status messages


Understanding the Output
------------------------

Generated Files
###############

After a successful run, the output folder contains:

.. code-block:: text
   :caption: Output folder structure

   output_folder/
   ├── behavior_tree_folder/
   │   └── ...                           # Behavior tree JSON files for each actor
   ├── bb_cache/
   │   └── ...                           # Blackboard variable definitions
   ├── simulation_event_cache/
   │   └── ...                           # Event sequence information
   └── rag_storage/
       └── ...                           # RAG vector store files


Behavior Tree JSON Structure
############################

Generated trees follow the OBC format:

.. code-block:: json
   :caption: Example generated behavior tree

   {
       "name": "Alice_PickUpAndPlace",
       "root": {
           "type": "Sequence",
           "children": [
               {
                   "type": "MoveToObject",
                   "parameters": {
                       "target_path": "/World/Props/CoffeeMug"
                   }
               },
               {
                   "type": "PickUpObject",
                   "parameters": {
                       "object_path": "/World/Props/CoffeeMug"
                   }
               },
               {
                   "type": "MoveToObject",
                   "parameters": {
                       "target_path": "/World/Props/DiningTable"
                   }
               },
               {
                   "type": "PlaceObject",
                   "parameters": {
                       "target_path": "/World/Props/DiningTable"
                   }
               }
           ]
       }
   }


Python API Reference
--------------------

For automated workflows, use the Python API directly.

Basic Usage
###########

.. code-block:: python
   :caption: Basic behavior tree generation

   from isaacsim.agent.planner.core.api import (
       BehaviorTreeGenerationConfig,
       generate_behavior_trees,
   )

   # Configure the generation
   config = BehaviorTreeGenerationConfig(
       scenario="Alice picks up the mug and places it on the table.",
       actor_data_path="/path/to/actors.json",
       object_data_path="/path/to/objects.json",
       node_catalog_path="/path/to/node_catalog.json",
       output_folder_path="/path/to/output",
   )

   # Generate behavior trees
   result = await generate_behavior_trees(config)

   if result.success:
       print(f"Generated trees for: {result.actor_ids}")
       print(f"Output folder: {result.behavior_tree_folder_path}")
   else:
       print(f"Error: {result.error}")


With Progress Callback
######################

.. code-block:: python
   :caption: Generation with progress tracking

   from isaacsim.agent.planner.core.api import (
       BehaviorTreeGenerationConfig,
       generate_behavior_trees,
       GenerationPhase,
   )

   def on_progress(phase: GenerationPhase, message: str):
       print(f"[{phase.value}] {message}")

   config = BehaviorTreeGenerationConfig(
       scenario="The camera pans across the room.",
       actor_data_path="/path/to/actors.json",
       output_folder_path="/path/to/output",
   )

   result = await generate_behavior_trees(config, progress_callback=on_progress)


Using the Bridge Pipeline
#########################

For Kit-integrated workflows:

.. code-block:: python
   :caption: Using BridgePipeline for Kit integration

   from isaacsim.agent.planner.bridge.pipeline import (
       BridgePipeline,
       PipelineConfig,
       ContextFilesConfig,
       OutputConfig,
   )

   # Create configuration
   config = PipelineConfig(
       scenario="Bob walks to the chair and sits down.",
       context_files=ContextFilesConfig(
           context_file_paths=["/path/to/actors.json", "/path/to/objects.json"],
           node_catalog_path="/path/to/node_catalog.json",
       ),
       output=OutputConfig(
           output_folder_path="/path/to/output",
       ),
   )

   # Run the pipeline
   bridge = BridgePipeline()
   result = await bridge.run(config)


Example Scene Setup API
-----------------------

For setting up example scenes programmatically:

One-Call Setup
##############

.. code-block:: python
   :caption: Quick example scene setup

   from isaacsim.agent.planner.bridge.examples.setup_stage.setup_example_stage import (
       setup_example_stage,
   )

   # Setup with all defaults
   actors = await setup_example_stage()
   print(f"Configured actors: {list(actors.keys())}")


Step-by-Step Setup
##################

.. code-block:: python
   :caption: Detailed example scene setup

   from isaacsim.agent.planner.bridge.examples.setup_stage.setup_example_stage import (
       ExampleStageSetup,
   )

   setup = ExampleStageSetup()

   # Step 1: Load context information
   context = setup.load_context_info(
       actor_files=["/path/to/actors.json"],
       object_files=["/path/to/objects.json"],
   )

   # Step 2: Setup OBC environment
   await setup.setup_obc_environment()

   # Step 3: Configure actors with OBC
   actors = setup.configure_actors()

   # Step 4: Assign default behavior trees
   setup.assign_default_trees(switch_immediately=True)


Troubleshooting
---------------

Common Issues
#############

No context files configured
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause**: No actor or object JSON files provided.

**Solution**: Add at least one context file in the *Context Cache Files* panel.


Pipeline initialization failed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause**: Missing or invalid model configuration.

**Solution**:

- Ensure model config and node-to-model map files exist and are valid JSON
- Verify API key is configured correctly


Failed to load example scene
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause**: Test stage URL not accessible or OBC not initialized.

**Solution**:

- Ensure you have network access to the test stage location
- Wait for stage to fully load before retrying
- Check the console for specific error messages


Empty or partial behavior trees
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause**: Actors or objects mentioned in scenario not found in context files.

**Solution**:

- Ensure actor/object IDs in scenario match IDs in JSON files
- Check semantic descriptions for better matching
- Verify prim paths exist in the USD stage


Debug Tips
##########

1. **Check Console Output**: Detailed logs are written with ``[IAP]`` or ``[IAP Bridge]`` prefix
2. **Validate JSON Files**: Ensure all JSON files are valid and have required fields
3. **Verify Prim Paths**: Confirm that prim paths in context files exist in the stage
4. **Test with Simple Scenarios**: Start with single-actor, single-action scenarios


Best Practices
--------------

Writing Effective Scenarios
###########################

1. **Be Specific**: Use actor IDs and object names from your context files

   - Good: *"Alice picks up the CoffeeMug"*
   - Less effective: *"Someone picks up the cup"*

2. **Keep It Simple**: Break complex scenarios into clear steps

   - Good: *"Alice walks to the table. Alice picks up the mug. Alice places the mug on the shelf."*
   - Less effective: *"Alice does various things with objects around the room"*

3. **Use Natural Language**: Write scenarios as you would describe them to a person


Organizing Data Files
#####################

1. **Separate Actors and Objects**: Keep actor and object definitions in separate files
2. **Use Descriptive IDs**: Choose IDs that reflect the entity's role or appearance
3. **Include Semantic Descriptions**: Rich descriptions help RAG matching


Performance Optimization
########################

1. **Use RAG Caching**: Set a persistent RAG cache folder for repeated runs
2. **Limit Context Size**: Include only relevant actors and objects for each scenario
3. **Batch Similar Scenarios**: Process scenarios with similar context together


Additional Resources
--------------------

- :doc:`IAP Introduction <ext_isaacsim_agent_planner>` - Overview and architecture
- :doc:`IAP Example Walkthrough <ext_isaacsim_agent_planner_walkthrough>` - Quick start tutorial
- :doc:`Omni Behavior Composer <../ext_replicator-agent/ext_omni_behavior_composer>` - OBC reference documentation

