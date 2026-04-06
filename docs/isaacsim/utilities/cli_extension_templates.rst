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
- **OmniGraph Extension** — Extension with C++ and Python OmniGraph node definitions, a Carbonite plugin, pybind11 bindings, and OGN build integration.

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
   ├── isaacsim/my/extension/
   │   ├── __init__.py
   │   ├── extension.py
   │   └── tests/__init__.py, test_extension.py
   └── premake5.lua

**Key files to modify:**

- ``extension.py`` — Add your startup/shutdown logic in ``on_startup()`` and ``on_shutdown()``.


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
   ├── isaacsim/my/example/
   │   ├── __init__.py
   │   ├── extension.py   ← Examples Browser registration
   │   ├── scenario.py    ← BaseSample with physics callbacks
   │   ├── ui.py          ← BaseSampleUITemplate with custom controls
   │   └── tests/__init__.py, test_extension.py
   └── premake5.lua

**Key files to modify:**

- ``scenario.py`` — Add your simulation assets in ``setup_scene()`` and logic in ``on_physics_step()``.
- ``ui.py`` — Add custom buttons and controls in ``build_extra_frames()``.


C++ Extension
^^^^^^^^^^^^^

An extension with a Carbonite C++ plugin and pybind11 Python bindings. The plugin implements a Carbonite interface
(``IExample``) and the bindings expose ``acquire_example_interface()`` / ``release_example_interface()`` to Python.
The Python ``extension.py`` acquires the interface on startup, which triggers the Carbonite plugin to load.

Generated structure:

.. code-block:: text

   source/extensions/isaacsim.my.extension/
   ├── config/extension.toml
   ├── data/icon.png, preview.png
   ├── docs/api.rst, Overview.md, CHANGELOG.md
   ├── include/isaacsim/my/extension/IExample.h       ← Carbonite interface
   ├── plugins/isaacsim.my.extension/ExamplePlugin.cpp ← Plugin implementation
   ├── bindings/isaacsim.my.extension/Bindings.cpp     ← pybind11 bindings
   ├── python/
   │   ├── __init__.py
   │   ├── impl/__init__.py, extension.py
   │   └── tests/__init__.py, test_extension.py
   └── premake5.lua

The ``binding_module`` variable controls the pybind11 module name (e.g., ``my_extension`` produces ``_my_extension.so``).

**Key files to modify:**

- ``IExample.h`` — Define your Carbonite interface methods.
- ``ExamplePlugin.cpp`` — Implement the interface.
- ``Bindings.cpp`` — Expose additional methods to Python via pybind11.
- ``extension.py`` — The interface is already acquired on startup; add your Python-side logic.


OmniGraph Extension
^^^^^^^^^^^^^^^^^^^

An extension with both C++ and Python OmniGraph node definitions, a Carbonite plugin for C++ node registration,
pybind11 bindings, and full OGN build integration.

The C++ nodes are defined by ``.ogn`` + ``.cpp`` pairs in ``nodes/``. The Python nodes are defined by ``.ogn`` + ``.py``
pairs in ``python/nodes/``. The OGN build system auto-generates database classes and test scaffolding for both.

The Carbonite plugin implements ``INITIALIZE_OGN_NODES()`` / ``RELEASE_OGN_NODES()`` in ``carbOnPluginStartup()`` /
``carbOnPluginShutdown()``. The pybind11 bindings expose ``acquire_example_nodes_interface()`` which is called in
``extension.py`` on startup — this triggers the plugin to load and register the C++ OGN nodes.

Generated structure:

.. code-block:: text

   source/extensions/isaacsim.my.nodes/
   ├── config/extension.toml
   ├── data/icon.png, preview.png
   ├── docs/api.rst, Overview.md, CHANGELOG.md
   ├── include/isaacsim/my/nodes/IExampleNodes.h          ← Carbonite interface
   ├── nodes/
   │   ├── OgnExampleCpp.ogn, OgnExampleCpp.cpp           ← C++ OGN node
   │   ├── config/CategoryDefinition.json
   │   └── icons/isaac-sim.svg
   ├── plugins/isaacsim.my.nodes/PluginInterface.cpp       ← Plugin with OGN macros
   ├── bindings/isaacsim.my.nodes/Bindings.cpp             ← pybind11 bindings
   ├── python/
   │   ├── __init__.py
   │   ├── impl/__init__.py, extension.py
   │   ├── nodes/
   │   │   ├── OgnExamplePython.ogn, OgnExamplePython.py   ← Python OGN node
   │   │   ├── config/CategoryDefinition.json
   │   │   └── icons/isaac-sim.svg
   │   └── tests/__init__.py, test_extension.py
   └── premake5.lua

Unlike the C++ template, the OGN template does not have a separate ``binding_module`` variable. The bindings module
name is automatically derived from the extension name by the OGN build system (e.g., ``isaacsim.my.nodes`` →
``_isaacsim_my_nodes``).

**Key files to modify:**

- ``.ogn`` files — Define node inputs, outputs, and metadata (JSON format).
- ``OgnExampleCpp.cpp`` — Implement the ``compute()`` method for the C++ node.
- ``OgnExamplePython.py`` — Implement the ``compute()`` method for the Python node.
- To add more nodes, create new ``.ogn`` + ``.cpp``/``.py`` pairs in the appropriate ``nodes/`` directory.


Tutorial: Creating and Testing an Extension
--------------------------------------------

This tutorial walks through creating a Python extension, building it, and verifying it works.

Step 1: Generate the Extension
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run the template generator:

.. code-block:: bash

   ./repo.sh template new

Select the **Python Extension** template and enter values when prompted:

- Extension name: ``isaacsim.my.hello``
- Title: ``Hello World``
- Version: ``0.1.0``
- Description: ``A hello world extension.``
- Category: ``Examples``

You should see:

.. code-block:: text

   Extension 'isaacsim.my.hello' created successfully in
   source/extensions/isaacsim.my.hello

Step 2: Build
^^^^^^^^^^^^^

Rebuild the project so the new extension is included:

.. code-block:: bash

   ./build.sh

The extension is automatically discovered — no manual registration is needed.

Step 3: Run the Startup Test
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Every generated extension includes a startup test. Run it from the build directory:

.. code-block:: bash

   cd _build/linux-x86_64/release
   ./tests/tests-isaacsim.my.hello.sh

This runs two test suites: a startup test (extension loads without errors) and unit tests
(``test_extension.py``).

Step 4: Verify in Isaac Sim
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Launch Isaac Sim with your extension enabled:

.. code-block:: bash

   ./_build/linux-x86_64/release/isaac-sim.sh --enable isaacsim.my.hello

To verify it loaded, open the Extensions Manager (``Window > Extensions``) and search for
``isaacsim.my.hello``. It should appear as enabled.

You can also verify from the Script Editor (``Window > Script Editor``):

.. code-block:: python

   import omni.kit.app
   ext_mgr = omni.kit.app.get_app().get_extension_manager()
   print(ext_mgr.is_extension_enabled("isaacsim.my.hello"))
   # Expected: True

Step 5: Customize
^^^^^^^^^^^^^^^^^^^

Open ``source/extensions/isaacsim.my.hello/isaacsim/my/hello/extension.py`` and modify the
``on_startup`` and ``on_shutdown`` methods to add your custom logic. Rebuild and re-test.


Verifying C++ and OmniGraph Extensions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For **C++ extensions**, verify the bindings work after building:

.. code-block:: bash

   cd _build/linux-x86_64/release
   ./tests/tests-isaacsim.my.extension.sh

The unit tests import the bindings module and call the ``greet()`` method on the Carbonite interface.

For **OmniGraph extensions**, verify both C++ and Python nodes are registered:

.. code-block:: bash

   cd _build/linux-x86_64/release
   ./tests/tests-isaacsim.my.nodes.sh

The unit tests check that both node types appear in ``og.get_registered_nodes()`` and that their
``compute()`` methods produce correct results.

You can also verify OGN nodes interactively via the Script Editor:

.. code-block:: python

   import omni.graph.core as og
   nodes = og.get_registered_nodes()
   print([n for n in nodes if "my.nodes" in n])
   # Expected: ['isaacsim.my.nodes.ExampleCpp', 'isaacsim.my.nodes.ExamplePython']


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
     - pybind11 module name (e.g., ``my_extension`` → ``_my_extension.so``)
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

.. note::

   The OmniGraph template does not use ``binding_module``. Its pybind11 module name is derived
   automatically from ``extension_name`` by the OGN build system.


Build and Verification Checklist
---------------------------------

After generating an extension, always:

1. **Build** — ``./build.sh``
2. **Test** — ``cd _build/linux-x86_64/release && ./tests/tests-<extension_name>.sh``

For C++ and OmniGraph templates, the build compiles the Carbonite plugin and pybind11 bindings.
If the build fails, check that the ``premake5.lua`` include paths match your extension's directory layout.


Troubleshooting
----------------

**Extension not loading at runtime**
   Check that the extension name in ``config/extension.toml`` matches the directory name under ``source/extensions/``.
   Verify the extension is enabled with ``--enable <extension_name>`` on the command line or through the Extensions Manager.

**C++ plugin not loading**
   Ensure the ``[[native.plugin]]`` section in ``extension.toml`` includes ``path = "bin/*.plugin"``.
   Without this, Kit cannot find the ``.so`` plugin file in the extension's ``bin/`` directory.

**C++ OGN nodes not registering**
   The Carbonite plugin must be started for ``INITIALIZE_OGN_NODES()`` to run. This happens when
   ``acquire_example_nodes_interface()`` is called from the pybind11 bindings in ``extension.py``.
   If the C++ nodes don't appear in ``og.get_registered_nodes()``, verify that:

   - ``Bindings.cpp`` has a ``defineInterfaceClass<IExampleNodes>`` call
   - ``extension.py`` imports and calls ``acquire_example_nodes_interface()`` in ``on_startup()``
   - ``PluginInterface.cpp`` does **not** have ``CARB_PLUGIN_IMPL_DEPS`` (this can prevent the plugin from loading)

**Build errors with OmniGraph nodes**
   Verify that ``.ogn`` files are valid JSON and that each C++ ``.ogn`` has a matching ``.cpp`` file
   with the ``REGISTER_OGN_NODE()`` macro. Python ``.ogn`` files need ``"language": "Python"`` and a
   matching ``.py`` file with a ``compute()`` method.

**Stubgen failure during build**
   The stubgen step may fail with ``generic_type: type "X" is already registered`` errors.
   This is a known issue with the pybind11 stub generator when multiple extensions share type names.
   The build itself succeeds — only the ``.pyi`` stub generation fails, which does not affect runtime.
