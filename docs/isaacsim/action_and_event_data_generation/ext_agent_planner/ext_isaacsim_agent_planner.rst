..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_ext_agent_planner:

==========================
Isaac Agent Planner (IAP)
==========================

The **Isaac Agent Planner (IAP)** is an advanced AI-powered system that automatically generates behavior trees for actors (characters and cameras) in simulation environments based on natural language scenario descriptions. By leveraging Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG), IAP transforms high-level scenario descriptions like *"Alice picks up the mug and places it on the table"* into executable behavior trees that drive actor behaviors in NVIDIA Omniverse Isaac Sim.

The IAP system consists of two complementary extensions:

+--------------------------------------+-------------------------------------------------------------------------+
| Extension                            | Purpose                                                                 |
+======================================+=========================================================================+
| ``isaacsim.agent.planner.core``      | Core API for behavior tree generation using LLMs and RAG                |
+--------------------------------------+-------------------------------------------------------------------------+
| ``isaacsim.agent.planner.bridge``    | Bridge layer connecting the core API with Kit/Omniverse environment     |
+--------------------------------------+-------------------------------------------------------------------------+


Key Features
------------

Natural Language Scenario Processing
####################################

IAP accepts plain English scenario descriptions and automatically:

- Parses the scenario to identify actors and their actions
- Segments complex scenarios into per-actor behavior sequences
- Maps actions to available behavior tree node types
- Generates parameters using context-aware RAG retrieval


Context-Aware Generation
########################

The system understands your simulation environment through:

- **Actor Context**: Information about characters, cameras, and their capabilities
- **Object Context**: Details about interactable objects in the scene
- **Node Catalog**: Available behavior tree actions and their parameter schemas
- **Blackboard Variables**: Shared state accessible to all behavior trees


RAG-Enhanced Parameter Generation
#################################

Using Retrieval-Augmented Generation, IAP enriches behavior tree parameters with:

- Semantic matching of scenario elements to scene objects
- Elaboration of actor metadata for richer context
- Intelligent parameter extraction based on node schemas


Event-Driven Architecture
#########################

IAP uses a sophisticated event system for:

- Dispatching tree construction completion events
- Triggering automatic behavior tree switching at runtime
- Responding to blackboard value changes and timeline events


Architecture
------------

The IAP system is organized into three main layers:

**User Interface Layer**

- *Context Cache Panel*: Configure data sources for generation
- *Network Config Panel*: Configure LLM settings
- *Scenario Execution Panel*: Enter scenarios and trigger generation

**IAP Bridge Layer** (``isaacsim.agent.planner.bridge``)

- ``BridgePipeline``: Orchestrates the generation workflow
- Path Mapping: Translates IDs to USD prim paths
- Event-Driven Tree Switcher: Manages runtime behavior switching

**IAP Core Layer** (``isaacsim.agent.planner.core``)

- Context Cache Manager: Loads and manages actor/object data
- RAG Systems: Context and event retrieval for parameter generation
- LLM Network: Tree construction using language models

**Output**

- Behavior Tree JSON Files compatible with OBC
- Blackboard Metadata for shared state
- Simulation Event Cache for event sequencing


Generation Pipeline
-------------------

The IAP pipeline processes scenarios through these phases:

1. **Configuration Validation**: Verify all required inputs and paths
2. **Context Loading**: Load actor, object, and blackboard data
3. **Node Catalog Loading**: Load available behavior tree node definitions
4. **RAG Construction**: Build vector stores for context retrieval
5. **Elaboration Building**: Create enriched parameter lookups
6. **Network Construction**: Build the LLM processing network
7. **Generation**: Invoke the network to generate behavior trees
8. **Output Saving**: Save trees and dispatch completion events


Core Concepts
-------------

Actors
######

Actors are entities in your scene that can execute behavior trees. IAP supports:

- **Human Actors**: Characters that can perform physical actions (walk, pick up, sit, etc.)
- **Camera Actors**: Cameras that can perform cinematic behaviors (pan, zoom, follow, etc.)

Actor data is provided as JSON with required fields:

.. code-block:: json
   :caption: Actor definition example

   {
       "id": "Alice",
       "semantic_description": "A character who can interact with objects",
       "metadata": {
           "actor_type": "human",
           "prim_path": "/World/Characters/Alice",
           "role": "protagonist"
       },
       "entity_type": "actor"
   }


Objects
#######

Objects are scene elements that actors can interact with:

.. code-block:: json
   :caption: Object definition example

   {
       "id": "Mug_01",
       "semantic_description": "A ceramic coffee mug on the counter",
       "metadata": {
           "prim_path": "/World/Props/Mug_01",
           "object_type": "pickup_item",
           "location": {"x": 1.5, "y": 2.0, "z": 0.8}
       },
       "entity_type": "object"
   }


Node Catalog
############

The node catalog defines available behavior tree actions. Each node includes:

- Node type identifier
- Human-readable description
- Parameter schema (JSON Schema format)
- Semantic keywords for RAG matching


Behavior Trees
##############

Generated behavior trees are saved as JSON files compatible with the Omni Behavior Composer (OBC). Each tree contains:

- Root node structure
- Composite nodes (Sequence, Selector, Parallel)
- Action/Condition leaf nodes with parameters
- Blackboard references


UI Components
-------------

The IAP Bridge Window provides a unified interface with four main panels:

Context Cache Panel
###################

Configure the data sources for generation:

- **Context Files**: JSON files containing actor and object definitions
- **Node Catalog**: Available behavior tree node types
- **Blackboard File**: Shared variable definitions
- **Metadata Schemas**: Optional JSON schemas for elaboration RAG


Network Config Panel
####################

Configure the LLM generation settings:

- **Model Configuration**: LLM model settings and endpoints
- **Node-to-Model Map**: Map specific nodes to specialized models
- **API Key**: Authentication for LLM services


Output Settings Panel
#####################

Configure where generated outputs are saved:

- **Output Folder**: Root directory for all generated files
- **RAG Cache Folder**: Location for RAG vector store caches


Scenario Execution Panel
########################

Trigger behavior tree generation:

- **Scenario Description**: Natural language input describing the scene
- **Run Pipeline**: Execute the generation pipeline
- **Load Example Scene**: Set up a demo environment for testing


Integration with Omni Behavior Composer
---------------------------------------

IAP integrates seamlessly with the :doc:`Omni Behavior Composer (OBC) <../ext_replicator-agent/ext_omni_behavior_composer>` system:

1. **Node Libraries**: Action nodes are registered in OBC node libraries
2. **Blackboard**: Shared state between all actors in the scene
3. **Tree Execution**: Generated trees execute through OBC runtime
4. **Event System**: IAP events can trigger tree switching during simulation


Use Cases
---------

Synthetic Data Generation (SDG)
###############################

Generate diverse actor behaviors for training data collection:

- Vary scenarios programmatically
- Create realistic motion sequences
- Capture multi-actor interactions


Digital Twin Simulation
#######################

Model real-world scenarios with accurate agent behaviors:

- Warehouse worker activities
- Retail store customer flows
- Manufacturing line operations


Rapid Prototyping
#################

Quickly iterate on character behaviors without manual tree authoring:

- Test scenario variations
- Explore behavior possibilities
- Validate scene setups


Requirements
------------

System Requirements
###################

- NVIDIA Omniverse Isaac Sim 4.5+
- RTX GPU (4080+ or datacenter GPU recommended)
- Python 3.10+


Dependencies
############

- ``omni.behavior.composer`` - Behavior tree runtime
- ``omni.behavior.composer.models`` - Pydantic models for BT nodes
- ``omni.behavior.composer.schema`` - USD schema types
- ``omni.metropolis.core`` - Metropolis utilities
- ``omni.metropolis.agent_registry`` - LLM agent management


API Key Requirements
####################

IAP requires an API key for LLM services. Configure via:

- UI: *Network Config Panel* > **API Key** field
- Environment variable: Set in your shell configuration
- Agent Registry: Configure in ``omni.metropolis.agent_registry``


Getting Started
---------------

- For a quick start guide using the example scene, see the :doc:`IAP Example Walkthrough <ext_isaacsim_agent_planner_walkthrough>`.
- For manual configuration and Python API usage, see the :doc:`IAP Configuration and API Reference <ext_isaacsim_agent_planner_api>`.


API Reference
-------------

For programmatic usage, see the core API documentation:

.. code-block:: python
   :caption: Basic IAP API usage

   from isaacsim.agent.planner.core.api import (
       BehaviorTreeGenerationConfig,
       generate_behavior_trees,
       GenerationPhase,
   )

   # Configure and run generation
   config = BehaviorTreeGenerationConfig(
       scenario="Alice picks up the mug.",
       actor_data_path="/path/to/actors.json",
       output_folder_path="/path/to/output",
   )

   result = await generate_behavior_trees(config)


Additional Resources
--------------------

- :doc:`IAP Example Walkthrough <ext_isaacsim_agent_planner_walkthrough>` - Quick start tutorial
- :doc:`IAP Configuration and API Reference <ext_isaacsim_agent_planner_api>` - Manual configuration and Python API
- :doc:`Omni Behavior Composer <../ext_replicator-agent/ext_omni_behavior_composer>` - OBC reference documentation

.. toctree::
    :hidden:
    :maxdepth: 1

    ext_isaacsim_agent_planner_walkthrough
    ext_isaacsim_agent_planner_api

