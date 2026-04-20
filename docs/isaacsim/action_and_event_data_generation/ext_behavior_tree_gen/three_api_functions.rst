.. _behavior_tree_gen_three_api_functions:

===============================
Using the API Functions
===============================

The **Behavior Tree Gen** UI in ``omni.ai.behavior_tree_gen.bridge`` is a thin wrapper around the
three-step public API in ``omni.ai.behavior_tree_gen.core.api``:

1. ``setup_workspace(...)``.
2. ``await prepare_runtime(...)``.
3. ``await generate_behavior_tree(...)``.

Use them in that exact order.

This page keeps the examples next to each API description because each call prepares state that the
next call consumes.

Shared Example Setup
--------------------

The snippets below use helper functions from ``omni.ai.behavior_tree_gen.bridge.utils`` only to
resolve the bundled ``simple`` example files. Replace those helper calls with your own file paths
when using custom planner data.

.. code-block:: python

    import os
    from pathlib import Path

    from omni.ai.behavior_tree_gen.core import api as core_api
    from omni.ai.behavior_tree_gen.bridge.utils import (
        get_example_scene_context_files,
        get_extension_path,
        load_example_scene_config,
        resolve_example_scene_file_path,
    )

    # Change these inputs to match your environment.
    ROOT_DIR = Path("Your/Output/Folder/Path") / "behavior_tree_gen_output"
    OUTPUT_DIR = ROOT_DIR / "output"
    API_KEY = "Your_NVIDIA_API_key"
    SCENARIO = "Anna picks up the CardBox_A and places it on the Table."

    ext_path = get_extension_path()
    scene_config = load_example_scene_config("simple")
    context_files = get_example_scene_context_files("simple")

    if ext_path is None or scene_config is None:
        raise RuntimeError("Could not load the bundled example scene configuration.")
    if not API_KEY:
        raise RuntimeError("Set NVIDIA_API_KEY before running this example.")

    node_catalog_paths = []
    for path in (scene_config.get("node_catalogs") or {}).values():
        resolved_path = resolve_example_scene_file_path(path, ext_path=ext_path)
        if resolved_path:
            node_catalog_paths.append(resolved_path)

    metadata_schemas = scene_config.get("metadata_schemas", {})
    actor_schema_path = resolve_example_scene_file_path(
        metadata_schemas.get("actor"),
        ext_path=ext_path,
    )
    object_schema_path = resolve_example_scene_file_path(
        metadata_schemas.get("object"),
        ext_path=ext_path,
    )

    model_info = scene_config.get("model_info", {})
    model_selection_config_path = resolve_example_scene_file_path(
        model_info.get("model_selection_config"),
        ext_path=ext_path,
    )
    embedding_model_configs_path = resolve_example_scene_file_path(
        model_info.get("embedding_model_configs"),
        ext_path=ext_path,
    )
    named_model_configs_path = resolve_example_scene_file_path(
        model_info.get("model_configs"),
        ext_path=ext_path,
    )
    node_to_model_map_path = resolve_example_scene_file_path(
        model_info.get("node_to_model_map"),
        ext_path=ext_path,
    )

Step 1: setup_workspace(...)
---------------------------

Use this function to create a reusable ``PlannerSession`` and load input data into the workspace.

The Python signature makes every argument optional, but real planner runs usually provide:

* ``cache_dir``: Folder for reusable planner cache artifacts.
* ``output_dir``: Folder where generated behavior tree files are written.
* ``context_data_paths``: Actor and object context JSON files.
* ``node_catalog_paths``: Behavior tree node catalog JSON files.

Common optional inputs:

* ``vectorstore_dir``: Folder for RAG and vectorstore data. If omitted, the runtime derives it from
  ``cache_dir`` when possible.
* ``actor_schema_path`` and ``object_schema_path``: Metadata schema files for typed planner-visible
  fields.
* ``blackboard_data_paths`` and ``apply_blackboard_cache``: Optional blackboard preload controls.
* ``refresh_cache``: Rebuild workspace caches before loading inputs.

What it returns:

* one ``PlannerSession`` object
* session fields such as ``actors_loaded``, ``objects_loaded``, ``nodes_loaded``, and
  ``workspace_ready``

Example:

.. code-block:: python

    session = core_api.setup_workspace(
        cache_dir=str(OUTPUT_DIR / "planner_cache"),
        output_dir=str(OUTPUT_DIR),
        context_data_paths=context_files["actors"] + context_files["objects"],
        node_catalog_paths=node_catalog_paths,
        actor_schema_path=actor_schema_path,
        object_schema_path=object_schema_path,
    )

    print(session.workspace_ready)
    print(session.actors_loaded, session.objects_loaded, session.nodes_loaded)

Step 2: prepare_runtime(...)
---------------------------

Use this function after workspace setup to configure model access, retrievers, and Action IR for
the session.

Required parameters:

* ``session``: The ``PlannerSession`` returned by ``setup_workspace(...)``.
* ``api_key``: NVIDIA API key.

Common optional inputs:

* ``model_selection_config_path``: Default LLM and embedding selection file.
* ``embedding_model_configs_path``: Named embedding profiles.
* ``named_model_configs_path``: Named chat-model profiles.
* ``node_to_model_map_path``: Explicit node-to-model routing.
* ``actor_types``: Warm only the listed actor types into Action IR.
* ``prefer_cached_action_ir``: Reuse compatible prepared Action IR when available.
* Direct overrides such as ``llm_model``, ``embedding_model``, ``rag_top_k``, and
  ``rag_similarity_threshold``.

What it does:

* configures NVIDIA model access
* prepares the context retriever and RAG state
* prepares or reuses Action IR for the current actor types

What it returns:

* a ``PlannerRuntimeResult``
* fields such as ``success``, ``message``, ``chat_model_name``, ``retriever_ready``,
  ``action_ir_ready``, and ``warmed_actor_types``

Example:

.. code-block:: python

    runtime_result = await core_api.prepare_runtime(
        session,
        api_key=API_KEY,
        model_selection_config_path=model_selection_config_path,
        embedding_model_configs_path=embedding_model_configs_path,
        named_model_configs_path=named_model_configs_path,
        node_to_model_map_path=node_to_model_map_path,
    )

    if not runtime_result.success:
        raise RuntimeError(runtime_result.message)

    print(runtime_result.chat_model_name)
    print(runtime_result.retriever_ready, runtime_result.action_ir_ready)

Step 3: generate_behavior_tree(...)
----------------------------------

Use this function only after the session has a ready workspace and a prepared runtime.

Required parameters:

* ``session``: The prepared ``PlannerSession``.
* ``scenario``: A natural-language instruction or goal.

Common optional inputs:

* ``skip_phase3``: Skip the phase-3 tree-construction stage when debugging the earlier pipeline
  stages.

What it returns:

* a ``PipelineResult``
* ``success``
* ``duration_seconds``
* ``behavior_tree_folder_path``
* ``error_message``

Example:

.. code-block:: python

    result = await core_api.generate_behavior_tree(
        session,
        SCENARIO,
    )

    if not result.success:
        raise RuntimeError(result.error_message)

    print(result.success)
    print(result.behavior_tree_folder_path)

Async Execution Note
--------------------

``setup_workspace(...)`` is synchronous, but ``prepare_runtime(...)`` and
``generate_behavior_tree(...)`` are coroutines. In Script Editor, put the shared setup and the three
step snippets inside one async function and schedule it:

.. code-block:: python

    import asyncio
    import os
    from pathlib import Path

    from omni.ai.behavior_tree_gen.core import api as core_api
    from omni.ai.behavior_tree_gen.bridge.utils import (
        get_example_scene_context_files,
        get_extension_path,
        load_example_scene_config,
        resolve_example_scene_file_path,
    )

    # Change these inputs to match your environment.
    ROOT_DIR = Path("Your/Output/Folder/Path") / "behavior_tree_gen_output"
    OUTPUT_DIR = ROOT_DIR / "output"
    API_KEY = "Your_NVIDIA_API_key"
    SCENARIO = "Anna picks up the CardBox_A and places it on the Table."


    async def run_planner_example():
        ext_path = get_extension_path()
        scene_config = load_example_scene_config("simple")
        context_files = get_example_scene_context_files("simple")

        if ext_path is None or scene_config is None:
            raise RuntimeError("Could not load the bundled example scene configuration.")
        if not API_KEY:
            raise RuntimeError("Set NVIDIA_API_KEY before running this example.")

        node_catalog_paths = []
        for path in (scene_config.get("node_catalogs") or {}).values():
            resolved_path = resolve_example_scene_file_path(path, ext_path=ext_path)
            if resolved_path:
                node_catalog_paths.append(resolved_path)

        metadata_schemas = scene_config.get("metadata_schemas", {})
        actor_schema_path = resolve_example_scene_file_path(
            metadata_schemas.get("actor"),
            ext_path=ext_path,
        )
        object_schema_path = resolve_example_scene_file_path(
            metadata_schemas.get("object"),
            ext_path=ext_path,
        )

        model_info = scene_config.get("model_info", {})
        model_selection_config_path = resolve_example_scene_file_path(
            model_info.get("model_selection_config"),
            ext_path=ext_path,
        )
        embedding_model_configs_path = resolve_example_scene_file_path(
            model_info.get("embedding_model_configs"),
            ext_path=ext_path,
        )
        named_model_configs_path = resolve_example_scene_file_path(
            model_info.get("model_configs"),
            ext_path=ext_path,
        )
        node_to_model_map_path = resolve_example_scene_file_path(
            model_info.get("node_to_model_map"),
            ext_path=ext_path,
        )

        session = core_api.setup_workspace(
            cache_dir=str(OUTPUT_DIR / "planner_cache"),
            output_dir=str(OUTPUT_DIR),
            context_data_paths=context_files["actors"] + context_files["objects"],
            node_catalog_paths=node_catalog_paths,
            actor_schema_path=actor_schema_path,
            object_schema_path=object_schema_path,
        )

        print(session.workspace_ready)
        print(session.actors_loaded, session.objects_loaded, session.nodes_loaded)

        runtime_result = await core_api.prepare_runtime(
            session,
            api_key=API_KEY,
            model_selection_config_path=model_selection_config_path,
            embedding_model_configs_path=embedding_model_configs_path,
            named_model_configs_path=named_model_configs_path,
            node_to_model_map_path=node_to_model_map_path,
        )

        if not runtime_result.success:
            raise RuntimeError(runtime_result.message)

        print(runtime_result.chat_model_name)
        print(runtime_result.retriever_ready, runtime_result.action_ir_ready)

        result = await core_api.generate_behavior_tree(
            session,
            SCENARIO,
        )

        if not result.success:
            raise RuntimeError(result.error_message)

        print(result.success)
        print(result.behavior_tree_folder_path)


    asyncio.ensure_future(run_planner_example())

Practical Notes
---------------

* ``omni.ai.behavior_tree_gen.bridge`` performs the same three calls automatically.
* ``prepare_runtime(...)`` must complete successfully before ``generate_behavior_tree(...)`` can
  work.
* ``prepare_runtime(...)`` can reuse compatible Action IR cached under ``cache_dir``.
* If you need a simpler one-call helper for testing, the bridge also provides
  ``omni.ai.behavior_tree_gen.bridge.test_pipeline.run(...)``.
