..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_cli_extension_templates:

========================
CLI extension templates
========================

The command-line interface (CLI) extension templates allow you to scaffold new |isaac-sim_short| extensions from the terminal using ``./repo.sh template new``. Four templates cover the most common extension patterns:

- **Python extension** --- Minimal Python-only extension with ``extension.py``, docs, and test scaffolding.
- **UI extension** --- Python extension with **Examples Browser** integration, **Load World**/**Reset** controls, physics callbacks, and custom UI using the experimental ``BaseSample`` and ``BaseSampleUITemplate`` classes.
- **C++ extension** --- Extension with a Carbonite C++ plugin, pybind11 Python bindings, and a Python wrapper.
- **OmniGraph extension** --- Extension with C++ and Python OmniGraph Node (OGN) definitions, a Carbonite plugin, pybind11 bindings, and OGN build integration.

The generator places all extensions in ``source/extensions/``, and the build system discovers them automatically --- no manual registration required.


.. _cli_ext_templates_prerequisites:

Prerequisites
==============

The template generator runs from the |isaac-sim_short| source tree. If you have not already cloned the
open-source repository, do so first:

.. code-block:: bash

   git clone -b develop https://github.com/isaac-sim/IsaacSim.git isaacsim
   cd isaacsim

All commands shown in this guide are run from the repository root (the directory that contains
``repo.sh``, ``build.sh``, and ``templates/``). On Windows, substitute ``./repo.sh`` with ``.\repo.bat``
and ``./build.sh`` with ``.\build.bat``.

The first invocation of ``./build.sh`` prompts you to accept the **NVIDIA Software License Agreement**.
After acceptance, a marker file ``.eula_accepted`` is written to the repository root and the prompt does
not appear again. Similarly, ``./repo.sh template new`` has its own EULA prompt that writes
``.omniverse_eula_accepted.txt``. Both files must exist for a fully non-interactive workflow.
See :ref:`cli_ext_templates_ci` below for how to pre-accept the EULA in non-interactive
(CI) environments.

For the full list of platform requirements (OS, GPU, driver, build tools), see the project
`README <https://github.com/isaac-sim/IsaacSim#prerequisites-and-environment-setup>`_.


.. _cli_ext_templates_getting_started:

Getting started
================

To create a new extension:

.. code-block:: bash

   ./repo.sh template new

Follow the interactive prompts to select a template and configure your extension name, title, and other variables.


.. _cli_ext_templates_available:

Available templates
====================

Python extension
-----------------

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

- ``extension.py`` --- Add your startup/shutdown logic in ``on_startup()`` and ``on_shutdown()``.


UI extension
-------------

A Python extension with full UI and scene management. This template provides:

- **Examples Browser integration** --- Your extension appears under your chosen category in **Window > Examples Browser**.
- **Load/Reset world controls** --- Pre-built **Load World** and **Reset** buttons that manage the simulation lifecycle.
- **Physics callbacks** --- A ``scenario.py`` with ``on_physics_step()`` called every simulation step via ``SimulationManager``.
- **Custom UI** --- A ``ui.py`` with an **Actions** frame where you add your own buttons and controls using ``btn_builder`` and other ``UIElementWrapper`` utilities.

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

- ``scenario.py`` --- Add your simulation assets in ``setup_scene()`` and logic in ``on_physics_step()``.
- ``ui.py`` --- Add custom buttons and controls in ``build_extra_frames()``.


C++ extension
--------------

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

- ``IExample.h`` --- Define your Carbonite interface methods.
- ``ExamplePlugin.cpp`` --- Implement the interface.
- ``Bindings.cpp`` --- Expose additional methods to Python via pybind11.
- ``extension.py`` --- The interface is already acquired on startup; add your Python-side logic.


OmniGraph extension
--------------------

An extension with both C++ and Python |omnigraph_short| node definitions, a Carbonite plugin for C++ node registration,
pybind11 bindings, and full OGN build integration.

The C++ nodes are defined by ``.ogn`` + ``.cpp`` pairs in ``nodes/``. The Python nodes are defined by ``.ogn`` + ``.py``
pairs in ``python/nodes/``. The OGN build system auto-generates database classes and test scaffolding for both.

The Carbonite plugin implements ``INITIALIZE_OGN_NODES()`` / ``RELEASE_OGN_NODES()`` in ``carbOnPluginStartup()`` /
``carbOnPluginShutdown()``. The pybind11 bindings expose ``acquire_example_nodes_interface()`` which ``extension.py``
calls on startup --- this triggers the plugin to load and register the C++ OGN nodes.

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

Unlike the C++ template, the OGN template does not use a separate ``binding_module`` variable. The OGN build system
automatically derives the bindings module name from the extension name (e.g., ``isaacsim.my.nodes`` →
``_isaacsim_my_nodes``).

**Key files to modify:**

- ``.ogn`` files --- Define node inputs, outputs, and metadata (JSON format).
- ``OgnExampleCpp.cpp`` --- Implement the ``compute()`` method for the C++ node.
- ``OgnExamplePython.py`` --- Implement the ``compute()`` method for the Python node.
- To add more nodes, create new ``.ogn`` + ``.cpp``/``.py`` pairs in the appropriate ``nodes/`` directory.


.. _cli_ext_templates_tutorial:

Tutorial: Creating and testing an extension
=============================================

This tutorial walks through creating a Python extension, building it, and verifying it works.

Step 1: Generate the extension
-------------------------------

Run the template generator:

.. code-block:: bash

   ./repo.sh template new

Select the **Python extension** template and enter values when prompted:

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
--------------

Rebuild the project so the new extension is included:

.. code-block:: bash

   ./build.sh

The build system discovers the extension automatically --- no manual registration required.
A successful build ends with a summary similar to:

.. code-block:: text

   BUILD (release) SUCCEEDED (Took NN.NN seconds)

After the build, the extension is staged at:

.. code-block:: text

   _build/linux-x86_64/release/exts/isaacsim.my.hello/

If the build fails, re-run with ``./build.sh -v`` for verbose output and inspect the first error
message --- subsequent errors are usually cascading consequences of the first.

Step 3: Run the startup test
------------------------------

Every generated extension includes a startup test. Run it from the build directory:

.. code-block:: bash

   cd _build/linux-x86_64/release
   ./tests/tests-isaacsim.my.hello.sh

This runs two test suites:

- A **startup test** that loads Kit with the extension enabled and verifies it starts and shuts down cleanly.
- The **unit tests** in ``isaacsim/my/hello/tests/test_extension.py``.

A successful run ends with the standard ``unittest`` summary lines:

.. code-block:: text

   Ran N tests in N.NNs

   OK

If a test fails, the failing test name and traceback are printed above the summary. Kit log files
written during the run can be found under ``~/.nvidia-omniverse/logs/`` for deeper inspection.

Step 4: Verify in Isaac Sim
-----------------------------

Launch |isaac-sim_short| with your extension enabled:

.. code-block:: bash

   ./_build/linux-x86_64/release/isaac-sim.sh --enable isaacsim.my.hello

**Extension Manager check**

Open the **Extensions Manager** (**Window > Extensions**) and search for ``isaacsim.my.hello``.
The extension should appear in the list with its status toggle set to **enabled** (green) and the
title and description from your ``extension.toml``.

**Script Editor check**

From **Window > Script Editor**, run:

.. code-block:: python

   import omni.kit.app
   ext_mgr = omni.kit.app.get_app().get_extension_manager()
   print(ext_mgr.is_extension_enabled("isaacsim.my.hello"))
   # Expected: True

Step 5: Customize
------------------

Open ``source/extensions/isaacsim.my.hello/isaacsim/my/hello/extension.py`` and modify the
``on_startup`` and ``on_shutdown`` methods to add your custom logic. Rebuild and re-test.


Verifying UI, C++, and OmniGraph extensions
---------------------------------------------

The verification flow is the same for every template (build → run startup test → launch and check
in the **Extensions Manager**); the additional checks below confirm the template-specific surfaces.

**UI extension**

After enabling the extension, open **Window > Examples Browser**. Your extension should appear under
the category you selected at generation time (e.g., ``Examples``). Selecting it opens a panel with
**Load World** and **Reset** buttons:

- Click **Load World** --- the simulation should load the default scene defined in
  ``scenario.py::setup_scene()`` (a grid ground plane referenced from
  ``Isaac/Environments/Grid/default_environment.usd``) and physics callbacks become active.
- Click **Reset** --- the world should return to its initial state and physics callbacks stop.

Replace the body of ``setup_scene()`` and ``on_physics_step()`` to drive your own simulation.

**C++ extension**

Verify the bindings work after building:

.. code-block:: bash

   cd _build/linux-x86_64/release
   ./tests/tests-isaacsim.my.extension.sh

The unit tests import the bindings module and call the ``greet()`` method on the Carbonite interface.
You can repeat the check interactively from the **Script Editor** (substituting your own
``extension_name`` and ``binding_module``):

.. code-block:: python

   from isaacsim.my.extension.bindings._my_extension import acquire_example_interface
   iface = acquire_example_interface()
   print(iface.greet())
   # Expected: a non-empty greeting string

**OmniGraph extension**

Verify both C++ and Python nodes are registered:

.. code-block:: bash

   cd _build/linux-x86_64/release
   ./tests/tests-isaacsim.my.nodes.sh

The unit tests check that both node types appear in ``og.get_registered_nodes()`` and that their
``compute()`` methods produce correct results.

You can also verify OGN nodes interactively via the **Script Editor**:

.. code-block:: python

   import omni.graph.core as og
   nodes = og.get_registered_nodes()
   print([n for n in nodes if "my.nodes" in n])
   # Expected: ['isaacsim.my.nodes.ExampleCpp', 'isaacsim.my.nodes.ExamplePython']

To exercise the nodes graphically, open **Window > Graph Editors > Action Graph**, create a new
graph, and search the node palette for ``ExampleCpp`` / ``ExamplePython``. Both should appear under
the category named after the first segment of your extension name (e.g., ``isaacsim``), as defined
in the generated ``CategoryDefinition.json`` files.


.. _cli_ext_templates_ci:

Non-interactive usage (CI)
============================

For Continuous Integration (CI) automation, the full pipeline is:

#. **Pre-accept the EULA.** Both ``./build.sh`` and ``./repo.sh template`` prompt on first use;
   in a non-interactive job the prompt blocks execution. Create **both** marker files in your CI
   setup step:

   .. code-block:: bash

      touch .eula_accepted
      touch .omniverse_eula_accepted.txt

   - ``.eula_accepted`` is checked by ``tools/eula_check.sh`` (used by ``./build.sh``).
   - ``.omniverse_eula_accepted.txt`` is checked by the template generator (used by
     ``./repo.sh template new`` and ``./repo.sh template replay``).

   Both are empty files that persist across builds, so creating them once at the start of the job
   is sufficient.

   .. note::

      If only ``.eula_accepted`` is present, ``./build.sh`` will work but
      ``./repo.sh template replay`` will fail with an unhandled exception in the EULA prompt
      because the playback frontend cannot answer interactive prompts.

#. **Generate a playback file once, interactively.** This step records the template selection and
   variable values into a TOML file:

   .. code-block:: bash

      ./repo.sh template new --generate-playback my_extension.toml

#. **Replay non-interactively in CI.** The replay command consumes the playback file and produces the
   extension without prompting:

   .. code-block:: bash

      ./repo.sh template replay my_extension.toml

#. **Build and run the startup tests** as in the tutorial above:

   .. code-block:: bash

      ./build.sh
      cd _build/linux-x86_64/release
      ./tests/tests-<extension_name>.sh

Playback files use TOML (Tom's Obvious, Minimal Language) format to specify the template and variable
values. The section header names the template (one of ``isaacsim-python-extension``,
``isaacsim-ui-extension``, ``isaacsim-cpp-extension``, ``isaacsim-omnigraph-extension``):

.. code-block:: toml

   [isaacsim-python-extension]
   extension_name = "isaacsim.sensors.lidar"
   title = "Lidar Sensor"
   version = "0.1.0"
   description = "Provides lidar sensor simulation."
   category = "Sensors"

The ``templates/tests/`` directory contains pre-defined playback files
(``test_python_extension.toml``, ``test_ui_extension.toml``, ``test_cpp_extension.toml``,
``test_omnigraph_extension.toml``) used for CI build verification --- copy one as a starting point
when wiring up your own pipeline.


.. _cli_ext_templates_variables:

Template variables
===================

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

   The |omnigraph_short| template does not use ``binding_module``. The OGN build system automatically
   derives the pybind11 module name from ``extension_name``.


.. _cli_ext_templates_checklist:

Build and verification checklist
==================================

After generating an extension, always:

1. **Build** --- ``./build.sh``
2. **Test** --- ``cd _build/linux-x86_64/release && ./tests/tests-<extension_name>.sh``

For C++ and |omnigraph_short| templates, the build compiles the Carbonite plugin and pybind11 bindings.
If the build fails, check that the ``premake5.lua`` include paths match your extension's directory layout.


.. _cli_ext_templates_troubleshooting:

Troubleshooting
================

**Extension not loading at runtime**
   Check that the extension name in ``config/extension.toml`` matches the directory name under ``source/extensions/``.
   Verify the extension is enabled with ``--enable <extension_name>`` on the command line or through the **Extensions Manager**.

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
   The build itself succeeds --- only the ``.pyi`` stub generation fails, which does not affect runtime.

**Template replay fails with "This should not be encountered"**
   This means ``.omniverse_eula_accepted.txt`` is missing from the repository root. The template
   generator's playback frontend cannot answer the EULA prompt interactively, so it raises an
   exception in its ``select()`` method. Fix by creating the file:

   .. code-block:: bash

      touch .omniverse_eula_accepted.txt

   This is a separate file from ``.eula_accepted`` (which is used by ``./build.sh``). Both must
   exist for fully non-interactive CI pipelines.
