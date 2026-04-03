..
   Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_cli_extension_templates:

====================================
CLI Extension Templates
====================================

The CLI Extension Templates allow you to scaffold new Isaac Sim extensions from the terminal using ``./repo.sh template new``. Four templates are available covering the most common extension patterns:

- **Python Extension** — Minimal Python-only extension with ``extension.py``, docs, and test scaffolding.
- **UI Extension** — Python extension with Examples Browser integration, Load/Reset world controls, physics callbacks, and custom UI using the experimental ``BaseSample`` and ``BaseSampleUITemplate`` classes.
- **C++ Extension** — Extension with a Carbonite C++ plugin, pybind11 Python bindings, and a Python wrapper.
- **OmniGraph Extension** — Extension with C++ and Python OmniGraph node definitions, a Carbonite plugin, and OGN build integration.

All generated extensions are placed in ``source/extensions/`` and are automatically discovered by the build system — no manual registration required.


Getting Started
-------------------

To create a new extension:

.. code-block:: bash

   ./repo.sh template new

Follow the interactive prompts to select a template and configure your extension name, title, and other variables.


Available Templates
-------------------

Python Extension
^^^^^^^^^^^^^^^^

A minimal Python-only extension. Use this when you need a lightweight extension without UI, scene management, or C++ code.

Generated structure:

.. code-block:: text

   source/extensions/isaacsim.my.extension/
   ├── config/extension.toml
   ├── data/icon.png, preview.png
   ├── docs/Overview.md, CHANGELOG.md
   ├── isaacsim/my/extension/__init__.py
   ├── isaacsim/my/extension/extension.py
   ├── isaacsim/my/extension/tests/__init__.py
   └── premake5.lua


UI Extension
^^^^^^^^^^^^

A Python extension with full UI and scene management. This template provides:

- **Examples Browser integration** — Your extension appears in the Examples Browser (``Window > Examples Browser``) under your chosen category.
- **Load/Reset world controls** — Pre-built ``Load World`` and ``Reset`` buttons that manage the simulation lifecycle.
- **Physics callbacks** — A ``scenario.py`` with ``on_physics_step()`` called every simulation step via ``SimulationManager``.
- **Custom UI** — A ``ui.py`` with an ``Actions`` frame where you add your own buttons and controls using ``btn_builder`` and other ``UIElementWrapper`` utilities.

The template uses the experimental APIs:

- ``isaacsim.examples.base.base_sample_experimental.BaseSample`` for scene lifecycle
- ``isaacsim.examples.base.base_sample_extension_experimental.BaseSampleUITemplate`` for UI
- ``isaacsim.core.simulation_manager.SimulationManager`` for physics callbacks
- ``isaacsim.core.experimental.utils`` for stage and app utilities

Generated structure:

.. code-block:: text

   source/extensions/isaacsim.my.example/
   ├── config/extension.toml
   ├── data/icon.png, preview.png
   ├── docs/Overview.md, CHANGELOG.md
   ├── isaacsim/my/example/__init__.py
   ├── isaacsim/my/example/extension.py   ← Examples Browser registration
   ├── isaacsim/my/example/scenario.py    ← BaseSample with physics callbacks
   ├── isaacsim/my/example/ui.py          ← BaseSampleUITemplate with custom controls
   ├── isaacsim/my/example/tests/__init__.py
   └── premake5.lua

**Key files to modify:**

- ``scenario.py`` — Add your simulation assets in ``setup_scene()`` and logic in ``on_physics_step()``.
- ``ui.py`` — Add custom buttons and controls in ``build_extra_frames()``.


C++ Extension
^^^^^^^^^^^^^

An extension with a Carbonite C++ plugin and pybind11 Python bindings. The plugin and bindings are built as separate targets.

Generated structure:

.. code-block:: text

   source/extensions/isaacsim.my.extension/
   ├── config/extension.toml
   ├── include/isaacsim/my/extension/IExample.h
   ├── plugins/isaacsim.my.extension/ExamplePlugin.cpp
   ├── bindings/isaacsim.my.extension/Bindings.cpp
   ├── python/__init__.py, impl/__init__.py, impl/extension.py
   ├── python/tests/__init__.py
   └── premake5.lua

The ``binding_module`` variable controls the pybind11 module name (e.g., ``my_extension`` produces ``_my_extension.so``).


OmniGraph Extension
^^^^^^^^^^^^^^^^^^^

An extension with both C++ and Python OmniGraph node definitions, a Carbonite plugin, and full OGN build integration.

Generated structure:

.. code-block:: text

   source/extensions/isaacsim.my.nodes/
   ├── config/extension.toml
   ├── include/isaacsim/my/nodes/IExampleNodes.h
   ├── nodes/OgnExampleCpp.ogn, OgnExampleCpp.cpp
   ├── nodes/config/CategoryDefinition.json, icons/isaac-sim.svg
   ├── plugins/isaacsim.my.nodes/PluginInterface.cpp
   ├── python/nodes/OgnExamplePython.ogn, OgnExamplePython.py
   ├── python/nodes/config/CategoryDefinition.json, icons/isaac-sim.svg
   ├── python/__init__.py, impl/__init__.py, impl/extension.py
   ├── python/tests/__init__.py
   └── premake5.lua


Non-Interactive Usage (CI)
----------------------------

For CI automation, use the replay feature with a pre-defined playback file:

.. code-block:: bash

   # Generate a playback file interactively (one-time)
   ./repo.sh template new --generate-playback my_extension.toml

   # Replay without prompts
   ./repo.sh template replay my_extension.toml

Playback files are TOML files that specify the template and variable values:

.. code-block:: toml

   [isaacsim-python-extension]
   extension_name = "isaacsim.sensors.lidar"
   title = "Lidar Sensor"
   version = "0.1.0"
   description = "Provides lidar sensor simulation."
   category = "Sensors"

Pre-defined test playback files are provided in ``templates/tests/`` for CI build verification.


Template Variables
-------------------

All templates share a common set of variables:

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Variable
     - Source
     - Description
   * - ``extension_name``
     - User input
     - Dotted extension name (e.g., ``isaacsim.sensors.lidar``)
   * - ``title``
     - User input
     - Human-readable title
   * - ``version``
     - User input
     - Semantic version (e.g., ``0.1.0``)
   * - ``description``
     - User input
     - Short description of the extension
   * - ``category``
     - User input
     - Extension category (e.g., ``Simulation``, ``Sensors``)
   * - ``binding_module``
     - User input (C++ only)
     - pybind11 module name (e.g., ``my_extension``)
   * - ``python_module``
     - Auto-derived
     - Same as ``extension_name``
   * - ``python_module_path``
     - Auto-derived
     - Dots replaced with slashes (e.g., ``isaacsim/sensors/lidar``)
   * - ``python_module_toplevel``
     - Auto-derived
     - First segment of ``extension_name`` (e.g., ``isaacsim``)
   * - ``current_date``
     - Auto-generated
     - Today's date
