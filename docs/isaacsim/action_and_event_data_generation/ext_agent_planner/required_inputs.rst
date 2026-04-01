.. _agent_planner_required_inputs:

===============
Required Inputs
===============

Isaac Agent Planner can be used in two ways:

* **Manually**, by filling in the planner UI.
* **From bundled examples**, where most file inputs are pre-populated automatically.

Base Inputs for Every Run
-------------------------

These inputs form the first layer of a planner run:

* **Scenario text**: Natural-language task or goal, such as
  ``Anna picks up the CardBox_A and places it on the Table.``
* **Output folder**: Writable folder where generated behavior trees, planner cache, and RAG cache
  data are stored.
* **NVIDIA API key**: Required during runtime preparation for NVIDIA-hosted chat and embedding
  models. The key can come from the UI, carb settings, or ``NVIDIA_API_KEY``.
* **Context files**: One or more JSON files containing the actor and object instances for the scene,
  including their metadata values.
* **Node catalog files**: One or more JSON files describing the behavior tree nodes the planner is
  allowed to use.

.. note::

   Context files should be read together with the actor and object schema files. The context provides
   the concrete scene data, while the schema defines the metadata fields and structure that give that
   data planner-visible meaning.

Advanced Direct Inputs
----------------------

These inputs shape metadata interpretation and runtime model routing:

* **Actor schema file**: Defines the structure of actor metadata used by the planner.
* **Object schema file**: Defines the structure of object metadata used by the planner.
* **Model selection config**: Selects the default chat model and embedding model and can define
  per-node overrides that drive runtime behavior.
* **Embedding model configs**: Defines the named embedding profiles referenced by the model selection
  config during RAG and retriever preparation.
* **LLM model configs**: Defines the named chat-model profiles referenced by model selection and
  per-node routing.
* **Node-to-model map**: Provides explicit routing from planner nodes to named chat models when
  runtime behavior must be controlled per node.

Conditional Inputs
------------------

The following input is optional, but important when the workflow depends on it:

* **Blackboard file**: Preloads blackboard metadata and variables into the workspace when
  blackboard-driven planning data should be available.

Relationship Between Schema and Context
---------------------------------------

The schema files and context files work together as a connected input set:

* **Context** provides the instance data for actors, objects, identifiers, and metadata values.
* **Schema** provides the structure and meaning of that metadata.
* During workspace setup, the planner loads the actor and object schemas first, builds typed models
  from them, and then loads the context JSON into those typed models.
* During runtime preparation, schema-derived terms are reused for grounding, parameter generation,
  and Action IR preparation.

Where These Inputs Usually Come From
------------------------------------

* The **Examples** window can load the bundled ``simple`` or ``warehouse`` scene and prefill the
  planner panels from a scene configuration JSON.
* The **Context Cache Files** panel is where context files, node catalogs, blackboard data, and
  metadata schemas are selected.
* The **Network Config** panel is where the API key and model-related JSON files are selected.
* The **Planner** panel is where the scenario text is entered.

Bundled Example Inputs
----------------------

For the built-in ``simple`` example, the extension automatically resolves inputs such as:

* actor and object context JSON files
* actor and common node catalog JSON files
* a blackboard JSON file
* actor and object metadata schema JSON files
* model selection, embedding-model, and LLM model JSON files

If you use the example flow, the main values you still need to confirm are the NVIDIA API key, the
output folder, the scenario text, and any additional runtime routing inputs required by your
model-selection setup.
