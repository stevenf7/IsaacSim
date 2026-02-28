..
   Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _ira_configuration_editor_api:

===============================
Configuration Editor API
===============================

The **Configuration Editor API** is provided by the ``isaacsim.replicator.agent.ui`` extension. It lets you load, modify, and save IRA (Isaac Sim Replicator Agent) configurations, as well as set up simulations and start data generation from the UI or Python scripts. The in-memory config uses the same schema as the YAML configuration described in the :ref:`Configuration File Guide <ira_configuration_file>`.

Use this API when you want to:

- Load or switch configuration files at runtime.
- Update specific fields (such as environment path, character counts, or writer settings) without editing YAML by hand.
- Add or remove items in lists (such as ``prop_asset_paths``) or in dictionaries (such as character/robot groups).
- Perform simulation setup and data generation from code and react to completion using core carb events.

Overview
========

The UI extension keeps an in-memory copy of the IRA config. The API operates on that copy and can optionally persist it to a file. Successful config changes and loads dispatch a UI refresh so that any open Configuration Editor panels stay in sync.

.. image:: /images/isaacsim_replicator_agent_configuration_editor_window.png
   :width: 600
   :align: center
   :alt: IRA Configuration Editor UI window

Functions are grouped as follows in ``isaacsim.replicator.agent.ui``:

- **Config file and path:** ``get_config_file_path``, ``load_config_file``, ``save_config_file``
- **Read/write config:** ``get_config``, ``set_config``, ``update_config``, ``add_config_item``, ``delete_config_item``
- **Simulation:** ``setup_simulation``, ``start_data_generation``

For ``get_config``, ``update_config``, ``add_config_item``, and ``delete_config_item``, use dot-separated paths and numeric indices for lists (see :ref:`ira_config_path_syntax`).

Config File and Path
===================

- **get_config_file_path()** — Returns the path of the config file currently associated with the in-memory config, or ``None`` if none is set.
- **load_config_file(file_path, set_config=True)** — Loads a YAML config from disk. Returns ``True`` on success. If ``set_config`` is ``True``, the loaded config becomes the current in-memory config. You can subscribe to ``isaacsim.replicator.agent.core.events.IRAEvents.CONFIG_FILE_LOADED_EVENT`` to be notified when loading has finished.
- **save_config_file(file_path, exclude_unset=False, exclude_defaults=False)** — Writes the current in-memory config to a YAML file. Returns ``True`` on success. Use ``exclude_unset`` or ``exclude_defaults`` to trim output.

**Example:**

.. literalinclude:: ../../snippets/action_and_event_data_generation/ira_config_load_save.py
   :language: python
   :start-after: # Example: load, inspect

Read and Update Config
======================

- **get_config(path=None)** — Returns the value at a dot-separated path, or the full config object if ``path`` is ``None``. Returns ``None`` if the path is invalid or config is not loaded.
- **set_config(config, file_path=None)** — Replaces the in-memory config with the given object (for example, from ``get_config()`` or the core loader). Optionally set ``file_path`` as the current file for the UI.
- **update_config(path, new_value)** — Sets one field at the given path. Validates after the change; on failure the update is rolled back and returns ``False``.
- **add_config_item(path, value, key=None)** — Appends to a list at ``path``, or adds a key-value pair to a dict (``key`` required for dicts).
- **delete_config_item(path, key)** — Removes a list element by index (or last item if ``key`` is ``None``) or a dict entry by key.

**Example:**

.. literalinclude:: ../../snippets/action_and_event_data_generation/ira_config_read_update.py
   :language: python
   :start-after: # Example: read and update

Simulation Control
==================

- **setup_simulation()** — Validates the current config and passes it to the IRA core to set up the simulation (environment, agents, sensors). Returns ``True`` if setup was started. Subscribe to ``isaacsim.replicator.agent.core.events.IRAEvents.SET_UP_SIMULATION_DONE_EVENT`` when setup has finished.
- **start_data_generation()** — Starts the data generation pipeline with the current config. Returns ``True`` if started. Subscribe to ``isaacsim.replicator.agent.core.events.IRAEvents.DATA_GENERATION_DONE_EVENT`` when generation has completed.

**Example workflow:** load config, optionally update fields, run setup, then start data generation. Use the carb event dispatcher to observe ``SET_UP_SIMULATION_DONE_EVENT`` and call ``start_data_generation()`` when setup is ready.

.. literalinclude:: ../../snippets/action_and_event_data_generation/ira_setup_and_data_generation.py
   :language: python
   :caption: Setup and data generation with event observers
   :start-after: # Example: Setup and data generation

Path Syntax
===========

.. _ira_config_path_syntax:

Config paths use dot-separated segments that correspond to the YAML structure in the :ref:`Configuration File Guide <ira_configuration_file>`:

- **Top-level keys:** ``version``, ``environment``, ``seed``, ``simulation_duration``, ``character``, ``robot``, ``sensor``, ``replicator``.
- **Nested keys:** for example, ``environment.base_stage_asset_path``, ``environment.prop_asset_paths``, ``character.groups``, ``replicator.writers``.
- **List index:** Use a numeric segment for the element index (for example, ``environment.prop_asset_paths.0`` for the first prop).
- **Dictionary key:** Use the group or writer name as the segment (for example, ``character.groups.warehouse_workers``, ``replicator.writers.IRABasicWriter``).

Paths are case-sensitive and must match the schema. When a path targets a list, the last segment can be an integer index; when it targets a dict, the last segment is the key name.
