..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _behavior_tree_gen_context_files_and_schemas:

==================================
Context files and metadata schemas
==================================

This guide explains the context-file format used by the example data bundled with
``omni.ai.behavior_tree_gen.bridge`` under ``data/example/context_info`` and the base models defined
in ``omni.behavior.composer.models``.

* **Context** is the runtime knowledge base of actors and objects in a scene. Each context entry is
  a JSON object that follows one of two base models: ``ActorInfo`` or
  ``InteractableObjectInfo``.
* **Metadata schema** is a standard JSON Schema document that defines the structure of the
  ``metadata`` dictionary inside each context entry.

Base context entry format
-------------------------

Context entries are built on two base models:

* ``omni.behavior.composer.models.context_models.ActorInfo``.
* ``omni.behavior.composer.models.context_models.InteractableObjectInfo``.

Both models use the same top-level structure:

.. code-block:: json

    {
      "id": "UniqueName",
      "semantic_description": "Natural-language description of this entity.",
      "metadata": {
      },
      "supported_interactions": [],
      "entity_type": "object"
    }

Top-level fields:

* ``id``: Stable identifier used by the pipeline to refer to the entity.
* ``semantic_description``: Human-readable description used during retrieval and grounding.
* ``metadata``: Domain-specific fields defined by the actor or object schema.
* ``supported_interactions``: Optional list of passive interaction labels supported by the entity.
* ``entity_type``: Must be ``actor`` or ``object``.

.. note::

   ``supported_interactions`` is defined on the base context models, not in the metadata schema.
   When present, the model normalizes the values to lowercase unique tokens.

Actor example
-------------

The bundled ``simple`` example uses actor entries shaped like this:

.. code-block:: json

    {
      "id": "Anna",
      "semantic_description": "A female human actor with short hair and a purple vest, with jeans and white sneakers.",
      "metadata": {
        "actor_type": "human",
        "role": "test_actor",
        "location": {
          "x": 0.0,
          "y": 0.0,
          "z": 0.0
        },
        "prim_path": "/World/Actors/Anna",
        "move_to": "/World/Characters/Anna/female_adult_business_02/ManRoot/female_adult_business_02",
        "semantic_label": "human"
      },
      "entity_type": "actor"
    }

This follows ``ActorInfo`` at the top level and stores domain-specific details such as
``actor_type``, ``role``, ``location``, and ``prim_path`` under ``metadata``.

Object example
--------------

The bundled ``simple`` example uses object entries shaped like this:

.. code-block:: json

    {
      "id": "Table",
      "semantic_description": "An office table used for placing objects.",
      "metadata": {
        "interactable_type": "table",
        "prim_path": "/World/TestEnv/SM_TableB",
        "semantic_label": "office table",
        "move_to_targets": {
          "default": "/World/TestEnv/SM_TableB/MoveToTarget"
        },
        "placement_targets": {
          "left_end": "/World/TestEnv/SM_TableB/PlaceObject_LeftEnd",
          "right_end": "/World/TestEnv/SM_TableB/PlaceObject_RightEnd",
          "middle": "/World/TestEnv/SM_TableB/PlaceObject_Middle"
        }
      },
      "supported_interactions": [
        "move to",
        "place on"
      ],
      "entity_type": "object"
    }

This follows ``InteractableObjectInfo`` at the top level and stores object-specific metadata such as
``interactable_type``, ``prim_path``, ``move_to_targets``, and ``placement_targets`` inside
``metadata``.

How metadata schemas work
-------------------------

The schema files under ``data/example/context_info/schemas`` define the structure of ``metadata``.
For the bundled examples:

* ``actor_metadata_schema.json`` defines fields such as ``prim_path``, ``semantic_label``,
  ``actor_type``, ``role``, and nested ``location`` data.
* ``object_metadata_schema.json`` defines fields such as ``interactable_type``, ``prim_path``,
  ``semantic_label``, ``move_to_targets``, ``placement_targets``, and ``usage_guide``.

In the core implementation, ``ContextCacheManager.setup_actor_model_from_schema()`` and
``ContextCacheManager.setup_object_model_from_schema()`` use
``omni.behavior.composer.models.schema_builder.build_metadata_model_from_json_schema()`` to build a
typed metadata model and then attach it to ``ActorInfo`` or ``InteractableObjectInfo``.

This means:

* Base fields such as ``id``, ``semantic_description``, ``supported_interactions``, and
  ``entity_type`` stay at the top level.
* Schema-defined fields belong under ``metadata``.
* Schema types, descriptions, enums, and numeric constraints are preserved in the typed metadata
  model.
* Extra metadata fields are still allowed because the schema builder uses ``allow_extra=True``.

Bundled required metadata fields
--------------------------------

The shipped example schemas mark these metadata fields as required:

* Actors: ``metadata.prim_path`` and ``metadata.actor_type``.
* Objects: ``metadata.prim_path`` and ``metadata.interactable_type``.

If you extend those schemas with new required fields, matching context entries should provide those
fields under ``metadata``.

Planner-visible schema paths
----------------------------

The pipeline expands schema-defined metadata fields into planner-visible term paths.

Examples:

* ``actors.metadata.role``.
* ``actors.metadata.location.x``.
* ``objects.metadata.prim_path``.
* ``objects.metadata.move_to_targets.default``.
* ``objects.metadata.placement_targets.left_end``.

These paths are used for grounding, retrieval, and parameter generation, so field names and
descriptions in the schema directly affect how well the workflow can use your custom data.

Add a custom metadata field
---------------------------

To add a new item using your own schema:

1. Start from the existing actor or object schema and add the new metadata field there.
2. Add the same field under ``metadata`` in each matching context item.
3. Reload the workspace so the pipeline rebuilds the typed metadata models from the updated files.

Example schema extension for objects:

.. code-block:: json

    {
      "type": "object",
      "properties": {
        "interactable_type": {
          "type": "string",
          "description": "Category of the object."
        },
        "prim_path": {
          "type": "string",
          "description": "USD path for the object."
        },
        "zone": {
          "type": "string",
          "description": "Warehouse zone label for this item.",
          "example": "A1"
        }
      },
      "required": [
        "interactable_type",
        "prim_path"
      ]
    }

Matching context entry:

.. code-block:: json

    {
      "id": "CardBox_C",
      "semantic_description": "A cardboard box stored in zone A1.",
      "metadata": {
        "interactable_type": "box",
        "prim_path": "/World/TestEnv/SM_CardBoxA_04",
        "semantic_label": "cardboard box",
        "zone": "A1"
      },
      "supported_interactions": [
        "pickup",
        "place"
      ],
      "entity_type": "object"
    }

.. tip::

   Keep stable identity and planner-facing descriptions at the top level, and put schema-defined
   domain attributes under ``metadata``.

Using the files in behavior tree generation
-------------------------------------------

After updating the files:

* In the UI, select the context files and matching schema files in **Context Cache Files** inside
  **Behavior Tree Gen**.
* In Python, pass the context files through ``context_data_paths`` and the schema files through
  ``actor_schema_path`` or ``object_schema_path`` when calling ``setup_workspace(...)``.
* Reload the workspace so the updated typed models and schema paths are available to the pipeline.

The bundled example files are good references when authoring your own context data.
