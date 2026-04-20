..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _behavior_tree_gen_required_inputs:

===============
Required inputs
===============

The behavior tree generation workflow in ``omni.ai.behavior_tree_gen`` can be used in two ways:

* **Manually**, by filling in the UI.
* **From bundled examples**, where most file inputs are pre-populated automatically.

Base inputs for every run
-------------------------

These inputs form the first layer of a run:

* **Scenario text**: Natural-language task or goal, such as
  ``Anna picks up the CardBox_A and places it on the Table.``.
* **Output folder**: Writable folder where generated behavior trees and reusable cache data are
  stored.
* **NVIDIA API key**: Required during runtime preparation for NVIDIA-hosted chat and embedding
  models. The key can come from the UI, carb settings, or ``NVIDIA_API_KEY``.
* **Context files**: One or more JSON files containing the actor and object instances for the scene,
  including their metadata values.
* **Node catalog files**: One or more JSON files describing the behavior tree nodes the pipeline is
  allowed to use.

.. note::

   Context files should be read together with the actor and object schema files. The context provides
   the concrete scene data, while the schema defines the metadata fields and structure that give that
   data planner-visible meaning.

Advanced direct inputs
----------------------

These inputs shape metadata interpretation and runtime model routing:

* **Actor schema file**: Defines the structure of actor metadata used by the pipeline.
* **Object schema file**: Defines the structure of object metadata used by the pipeline.
* **Model selection config**: Selects the default chat model and embedding model and can define
  per-node overrides that drive runtime behavior.
* **Embedding model configs**: Defines the named embedding profiles referenced by the model
  selection config during RAG and retriever preparation.
* **Named model configs**: Defines the named chat-model profiles referenced by model selection and
  per-node routing.
* **Node-to-model map**: Provides explicit routing from planner nodes to named chat models when
  runtime behavior must be controlled per node.

Conditional inputs
------------------

The following input is optional, but important when the workflow depends on it:

* **Blackboard file**: Preloads blackboard metadata and variables into the workspace when
  blackboard-driven planning data should be available.

Relationship between schema and context
---------------------------------------

The schema files and context files work together as a connected input set:

* **Context** provides the instance data for actors, objects, identifiers, and metadata values.
* **Schema** provides the structure and meaning of that metadata.
* During workspace setup, the pipeline loads the actor and object schemas first, builds typed
  models from them, and then loads the context JSON into those typed models.
* During runtime preparation, schema-derived terms are reused for grounding, parameter generation,
  and Action IR preparation.

Where these inputs usually come from
------------------------------------

* The examples window can load the bundled ``simple`` or ``warehouse`` scene and prefill the
  **Behavior Tree Gen** panels from a scene configuration JSON.
* The **Context Cache Files** panel is where context files, node catalogs, blackboard data, and
  metadata schemas are selected.
* The **Network Config** panel is where the API key and model-related JSON files are selected.
* The **Planner** panel is where the scenario text is entered.

Bundled example inputs
----------------------

For the built-in ``simple`` example, the extension automatically resolves inputs such as:

* actor and object context JSON files.
* actor and common node catalog JSON files.
* a blackboard JSON file.
* actor and object metadata schema JSON files.
* model selection, embedding-model, and named-model JSON files.


If you use the example flow, the main values you still need to confirm are the NVIDIA API key, the
output folder, the scenario text, and any additional runtime routing inputs required by your model
selection setup.
