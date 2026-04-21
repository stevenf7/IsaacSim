..
   Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_omnigraph_custom_ipc_nodes:

===================================
Building Custom IPC OmniGraph Nodes
===================================

This guide explains how to build OmniGraph nodes for inter-process communication (IPC) in |isaac-sim_short|—covering the node schema, transport lifecycle with ``BaseResetNode``, non-blocking I/O inside ``compute``, and how to add your transport library as a dependency. The OmniGraph patterns apply regardless of which IPC stack you use; the worked example is ``isaacsim.examples.ipc``, a clock-send and step-receive node pair over BSD sockets in C++ and Python. The tutorial starts by scaffolding a new extension with the CLI template so you have a working build skeleton before writing any IPC code.

.. note::

   All commands in this tutorial are run from the **Isaac Sim repository root** (the directory that contains ``build.sh`` and ``repo.sh``).

Before You Start
================

**Prerequisites**:

#. **Custom C++ extensions** — `Kit C++ Extension Template <https://docs.omniverse.nvidia.com/kit/docs/kit-extension-template-cpp/latest/index.html>`_.
#. **OmniGraph** — :doc:`OmniGraph Core Concepts <extensions:ext_omnigraph/getting-started/core_concepts>` and :doc:`Basic OmniGraph Tutorial <extensions:ext_omnigraph/tutorials/gentle_intro>`.
#. **Custom nodes** — :ref:`isaac_sim_app_omnigraph_custom_python_nodes` and :ref:`isaac_sim_app_tutorial_advanced_omnigraph_custom_cpp_nodes`.

Optional: :ref:`isaac_sim_app_tutorial_gui_omnigraph` if you are new to the Action Graph editor.

.. seealso::

   :ref:`isaac_sim_app_ros2_custom_omnigraph_node_python` — a complete Python node
   example (ROS 2 context, but the ``internal_state()`` factory,
   ``BaseResetNode``, ``db.per_instance_state``, and
   ``og.ExecutionAttributeState.ENABLED`` patterns are identical for any IPC
   node).

Scaffold Your Extension
=======================

Before writing IPC code, create the extension skeleton with the CLI template:

.. code-block:: bash

   ./repo.sh template new

When prompted, select **Isaac Sim OmniGraph Node Extension**. You will be asked for:

- ``extension_name`` — dotted identifier, for example ``isaacsim.my.ipc.nodes``
- ``title`` — human-readable name shown in the Extensions window
- ``description`` — short summary
- ``category`` — used to group your nodes in the Action Graph node library (for example ``Simulation``)

The template creates the full extension skeleton under ``source/extensions/<extension_name>/``:

.. code-block:: text

   source/extensions/<extension_name>/
   ├── config/extension.toml          ← metadata, dependencies, test entries
   ├── nodes/
   │   ├── OgnExampleCpp.ogn          ← rename/replace with your IPC node schema
   │   └── OgnExampleCpp.cpp          ← rename/replace with your IPC node implementation
   ├── plugins/<extension_name>/
   │   └── PluginInterface.cpp        ← Carbonite plugin + OGN registration (keep as-is)
   ├── bindings/<extension_name>/
   │   └── Bindings.cpp               ← pybind11 bindings; acquires the Carbonite interface (keep as-is)
   ├── include/<extension_name>/
   │   └── IExampleNodes.h            ← Carbonite interface (keep as-is)
   ├── python/nodes/
   │   ├── OgnExamplePython.ogn       ← rename/replace with your Python node schema
   │   └── OgnExamplePython.py        ← rename/replace with your Python Node Implementation
   ├── python/impl/extension.py       ← calls acquire_example_ipc_interface() on startup to load the plugin
   ├── python/tests/                  ← test modules go here
   └── premake5.lua                   ← build configuration

Build once to confirm the scaffold compiles before making any changes:

.. code-block:: bash

   ./build.sh

The generated ``OgnExampleCpp`` and ``OgnExamplePython`` nodes are placeholder stubs (they double an input value). Rename or replace them with your actual IPC node(s) as you work through the sections below.

.. admonition:: Try it: verify your scaffold

   After ``./build.sh`` completes above, confirm the scaffold registers its placeholder nodes:

   #. Launch Isaac Sim: ``./_build/linux-x86_64/release/isaac-sim.sh``
   #. Open **Window → Extensions**, search for your extension name, and enable it.
   #. Open **Window → Graph Editors → Action Graph** and search for ``OgnExampleCpp`` and ``OgnExamplePython`` in the node library.

   If both nodes appear, the scaffold is wired correctly. Proceed to `Design and Implement Your Nodes`_ to replace the placeholders.

Add Your Transport Library
==========================

Before writing node code, wire in the library that provides your IPC and serialization. The generated ``config/extension.toml`` and ``premake5.lua`` are already in place; the sections below show where to add entries.

Python
------

Isaac Sim ships a pip archive (``omni.isaac.core_archive`` and related extensions) that pre-bundles many common packages—NumPy, SciPy, and others. If your library is already in that archive you can import it directly with no extra configuration.

If the package is not yet bundled, declare it in ``config/extension.toml``, for example:

.. code-block:: toml

   [python.pipapi]
   requirements = ["pyzmq>=25", "grpcio"]  # replace with your actual packages
   use_online_index = true

Isaac Sim resolves these at extension startup. ``use_online_index = true`` must be set; if it is omitted or set to ``false``, ``omni.kit.pipapi`` logs a warning and skips the ``requirements`` list entirely.

C++
---

Prebuilt native libraries go through packman. These steps follow the same pattern described in the `Kit Extension C++ template documentation <https://docs.omniverse.nvidia.com/kit/docs/kit-extension-template-cpp/latest/index.html>`_:

1. **Declare the dependency.** Add your library to ``deps/ext-deps.packman.xml`` — this is the designated file for extension-specific dependencies (separate from the Kit SDK deps). The unpacked tree typically lands under ``_build/target-deps/<libname>/``:

   .. code-block:: xml

      <project toolsVersion="5.0">
        <dependency name="mylib" linkPath="../_build/target-deps/mylib">
          <package name="mylib" version="1.2.3" />
        </dependency>
      </project>

2. **Update premake5.lua.** Point to the include and library directories and add the link:

   .. code-block:: lua

      includedirs { "%{target_deps}/mylib/include" }
      libdirs     { "%{target_deps}/mylib/lib/%{platform}" }
      links       { "mylib" }

3. **Shared libraries at runtime.** If the library ships as a ``.so`` / ``.dll``, either bundle it beside the extension plugin or list it under ``[native.library]`` in ``extension.toml`` so Kit's loader finds it.

The sample extension uses only standard BSD socket APIs and has no additional native library entries beyond the plugin itself.

Design and Implement Your Nodes
================================

Design Principle
----------------

Keep IPC nodes thin: they should only handle **serialization and transport**. Simulation data reads (joint positions, sensor data, simulation time) belong in upstream built-in nodes wired into the graph before your IPC node; downstream processing or command writes belong in other nodes after it. This keeps ``compute`` fast and makes the graph layout self-documenting.

What Every IPC Node Requires
-----------------------------

Every custom IPC node requires the same six things, regardless of transport:

#. **Node schema** (``.ogn`` file) — declare inputs (URI, config), outputs (data, ``execOut``), and state. See the sample ``.ogn`` files under ``nodes/`` in ``isaacsim.examples.ipc`` as a reference.
#. ``BaseResetNode`` subclass — holds per-instance state (sockets, buffers, handles). Implement ``reset()`` (C++) or ``custom_reset()`` (Python) to tear down the transport when the timeline stops or inputs change.
#. ``compute(db)`` with a lifecycle split:

   - Detect input changes (URI, config) → call reset and teardown
   - Try to open the transport if not ready → return early on failure (retry next evaluation)
   - Do non-blocking I/O (send or try-receive)
   - Write ``db.outputs`` and fire ``execOut``

#. **Non-blocking I/O** — never block indefinitely in ``compute``. Use try-receive, timeouts, or offload slow paths to a worker thread (see `Performance Considerations`_).
#. **Fire** ``execOut`` at the end of ``compute`` to signal downstream nodes that the transport operation is complete and/or new data is ready. You control when to fire it — every evaluation, only on successful send, or only when a full message has been received.
#. **Your transport library** — add it as a dependency (see `Add Your Transport Library`_ above) and replace the TCP helpers with your stack's API.

OGN Schema Quick Reference
--------------------------

Each ``.ogn`` file is a single JSON object keyed by the node's registered type
name. The minimum schema for a Python IPC node looks like this:

.. code-block:: json

   {
       "MyNodeName": {
           "version": 1,
           "language": "Python",
           "description": "One-line description shown in the node library.",
           "metadata": { "uiName": "My Node Display Name" },
           "categoryDefinitions": "config/CategoryDefinition.json",
           "categories": "myCategory",
           "inputs": {
               "execIn":  { "type": "execution", "description": "Trigger." },
               "uri":     { "type": "string",    "description": "...", "default": "tcp://127.0.0.1:5550" },
               "myValue": { "type": "double",    "description": "...", "default": 0.0 }
           },
           "outputs": {
               "execOut":  { "type": "execution", "description": "Output execution port." },
               "myTokens": { "type": "token[]",   "description": "Array of token outputs." }
           }
       }
   }

Common scalar types: ``"string"``, ``"double"``, ``"float"``, ``"int"``,
``"uint"``, ``"bool"``, ``"execution"``. Array variants append ``[]``:
``"double[]"``, ``"float[]"``, ``"token[]"``, etc. The ``"default"`` key is
required for non-execution scalar inputs; use ``[]`` for array inputs.

``categoryDefinitions`` is a path relative to the ``nodes/`` directory that
points to a JSON file mapping category keys to human-readable display strings:

.. code-block:: json

   {
       "categoryDefinitions": {
           "myCategory": "My node group label in the Action Graph library"
       }
   }

C++ Node Implementation
-----------------------

``BaseResetNode`` is declared in ``isaacsim.core.includes``. This extension is a compile-time only dependency — do **not** add it to ``[dependencies]`` in ``extension.toml``. Instead, add the header path in ``premake5.lua``:

.. code-block:: lua

   includedirs { "%{root}/source/extensions/isaacsim.core.includes/include" }

Then include the header in your ``.cpp`` file:

.. code-block:: cpp

   #include <isaacsim/core/includes/BaseResetNode.h>

Derive your per-instance node class from ``isaacsim::core::includes::BaseResetNode``. That base subscribes to the timeline stop event and calls your ``reset()`` so transport handles are not left open after simulation stops.

Replace the generated ``OgnExampleCpp`` stub with a class like this (see ``OgnSimpleSendSimulationClockCpp.cpp`` in ``isaacsim.examples.ipc`` for a full TCP implementation):

.. literalinclude:: ../../../source/extensions/isaacsim.examples.ipc/docs/templates/OgnMyIpcNodeCpp.cpp
   :language: cpp
   :start-after: // TEMPLATE-START
   :end-before: // TEMPLATE-END

.. note::

   The generated ``python/impl/extension.py`` calls ``acquire_example_ipc_interface()`` in
   ``on_startup()``. This is what triggers the Carbonite plugin to load and run
   ``INITIALIZE_OGN_NODES()``, registering your C++ nodes. If your nodes do not appear in the
   Action Graph library, verify that ``extension.py`` is calling the acquire function and that
   ``PluginInterface.cpp`` does **not** contain a ``CARB_PLUGIN_IMPL_DEPS`` line — that macro
   can prevent the plugin from loading.

Python Node Implementation
--------------------------

``BaseResetNode`` is provided by the ``isaacsim.core.nodes`` extension. Add it as a dependency in ``config/extension.toml`` and import it in your node file:

.. code-block:: toml

   [dependencies]
   "isaacsim.core.nodes" = {}

.. code-block:: python

   import omni.graph.core as og
   from isaacsim.core.nodes import BaseResetNode

Put per-instance data in a small class that subclasses ``BaseResetNode``. Pass ``initialize=False`` to ``super().__init__`` if you lazy-open sockets in ``compute``, as the samples do. Without it, ``BaseResetNode.__init__`` calls ``custom_reset()`` immediately during construction, before your instance attributes (``self.sock = None``, etc.) are set, raising ``AttributeError``. Implement ``custom_reset()`` to close sockets and clear buffers; it runs on timeline stop and mirrors the C++ ``reset()``.

Replace the generated ``OgnExamplePython`` stub with a class like this (see ``OgnSimpleSendSimulationClockPy.py`` in ``isaacsim.examples.ipc`` for a full TCP implementation):

.. literalinclude:: ../../../source/extensions/isaacsim.examples.ipc/docs/templates/OgnMyIpcNodePy.py
   :language: python
   :start-after: # TEMPLATE-START
   :end-before: # TEMPLATE-END

.. admonition:: Try it: implement and build your node

   Adapt your scaffolded extension to a minimal IPC sender:

   #. **Update the OGN schema.** In ``nodes/OgnExampleCpp.ogn`` (or ``OgnExamplePython.ogn``), rename the node and add a ``uri`` string input (default ``"127.0.0.1:9000"``) and ``execIn``/``execOut`` execution ports.
   #. **Replace the implementation.** Copy the template above into ``OgnExampleCpp.cpp`` (or ``OgnExamplePython.py``), rename classes to match, and fill in a no-op ``transfer()`` that always returns ``true``.
   #. **Rebuild:** ``./build.sh``
   #. **Verify:** enable your extension in Isaac Sim and confirm the renamed node appears in the Action Graph library.

   For a complete TCP implementation of the same pattern, study ``OgnSimpleSendSimulationClockCpp.cpp`` (or the Python equivalent) in ``source/extensions/isaacsim.examples.ipc/``.

For Python-only extensions (no C++ plugin), omit ``project_ext_plugin``, ``project_ext_bindings``, and all ``includedirs`` / ``links`` entries from ``premake5.lua``. Keep ``add_ogn_dependencies`` (processes ``.ogn`` files and generates ``*Database.py`` modules) and the ``repo_build.prebuild_link`` block:

.. code-block:: lua

   if os.target() == "linux" then
       local ext = get_current_extension_info()
       local ogn = get_ogn_project_information(ext, "myorg/my/ipc/nodes")
       project_ext(ext)

       add_ogn_dependencies(ogn, { "python/nodes" })

       repo_build.prebuild_copy {
           { "python/__init__.py",  ogn.python_target_path },
           { "python/extension.py", ogn.python_target_path },
       }

       repo_build.prebuild_link {
           { "python/nodes",  ogn.python_target_path .. "/nodes" },
           { "python/tests",  ogn.python_target_path .. "/tests" },
       }
   end

Sample Extension Reference
--------------------------

Source: ``source/extensions/isaacsim.examples.ipc/``.

.. list-table::
   :header-rows: 1

   * - Registered type name
     - Implementation
     - Role
   * - ``SimpleSendSimulationClockCpp`` / ``SimpleSendSimulationClockPy``
     - C++ / Python
     - Forwards the simulation clock to an external process on each evaluation. Connects as a TCP client to ``uri`` (``host:port``). Input: ``simulationTime`` (``double``, seconds; connect from ``IsaacReadSimulationTime``). Encodes the value as nanoseconds in an 8-byte signed int64 (little-endian) and sends it. Fires ``execOut`` on every evaluation.
   * - ``SimpleReceiveExternalStepCpp`` / ``SimpleReceiveExternalStepPy``
     - C++ / Python
     - Receives a step counter from an external process and exposes it to downstream nodes. Binds as a TCP server on ``uri`` and accepts one client. Output: ``step`` (uint32). Fires ``execOut`` only when a complete 4-byte message arrives; partial reads are buffered across evaluations.

In graphs, the full path is typically ``isaacsim.examples.ipc.<TypeName>`` (see the extension's ``config/extension.toml``).

C++ and Python follow the same sequence in ``compute``; only naming and state wiring differ (for example ``reset()`` vs ``custom_reset()``, and C++ ``state`` from the OGN database vs Python ``internal_state()``).

.. code-block:: text

   compute(db)
        │
        ├─► uri (or relevant inputs) changed? ──yes──► teardown transport
        │                    C++: state.reset()    Python: custom_reset()
        ▼
   try open: connect or listen / accept
        │         (retry next eval if not ready)
        ▼
   transport ready? ──no──► return false
        │    (recv: often "no full message yet")
        yes
        ▼
   framed try-send / try-recv  (see Performance Considerations for time budget)
        │
        ▼
   write db.outputs and set execOut
        │
        ▼
   return true/false  (per node type / sample rules)

Use Your Nodes in Isaac Sim
============================

Enable Your Extension and Find Your Nodes
------------------------------------------

``./build.sh`` compiles your extension and places the output under ``_build/linux-x86_64/release/exts/<extension_name>/``. Isaac Sim launched from the same repo automatically searches that directory, so no additional path configuration is needed.

Launch Isaac Sim if it is not already running:

.. code-block:: bash

   ./_build/linux-x86_64/release/isaac-sim.sh

Then enable your extension:

#. Open **Window → Extensions**.
#. Search for your extension name (for example ``isaacsim.my.ipc.nodes``) and enable it.

Your nodes then appear in the Action Graph node library under the category you chose during scaffolding. Use the search box in the node library to find them by name.

.. tip::

   ``isaacsim.examples.ipc`` is a fully working example of this pattern that ships with Isaac Sim. Enable it now and follow the `Building an Example Graph`_ steps below to see the end-to-end IPC workflow before writing any of your own node code.

Building an Example Graph
--------------------------

The steps below build the sample graph for ``tcp_tutorial_playback_bridge.py`` using the reference nodes from ``isaacsim.examples.ipc``. Use it to verify the end-to-end IPC pattern before wiring in your own nodes.

#. **Enable the sample extension.** Open Window → Extensions, search for ``isaacsim.examples.ipc``, and enable IPC OmniGraph Node Examples.
#. **Open the Action Graph editor.** Window → Graph Editors → Action Graph.
#. **Place the tutorial nodes.** Under Isaac Examples in the node library, add Receive External Step and Send Simulation Clock. Use the search box to add On Playback Tick and Isaac Read Simulation Time from ``isaacsim.core.nodes``. Either C++ or Python node pair works with the bridge script.
#. **Wire the graph.**

   Execution chain:

   - On Playback Tick ``execOut`` → Receive External Step ``execIn``
   - Receive External Step ``execOut`` → Send Simulation Clock ``execIn``

   Data:

   - Isaac Read Simulation Time ``simulationTime`` → Send Simulation Clock ``simulationTime``

   The default ``uri`` values are ``127.0.0.1:9001`` on the receive node and ``127.0.0.1:9000`` on the send node.

#. **Start playback.** Click the **Play** button in the toolbar (or press **Space**) to begin the simulation.

General Action Graph UI is covered in :ref:`isaac_sim_app_tutorial_gui_omnigraph` and in the OmniGraph documentation linked in `Before You Start`_.

Once the graph is wired and playback is running, Receive External Step listens on its URI, the bridge script connects and sends the first step token, and Send Simulation Clock reports the current simulation time back to the script each tick. The script drives the timing loop; Isaac Sim advances one tick per received step.

.. admonition:: Try it: run the bridge with your own node

   Once the reference graph works end-to-end with ``isaacsim.examples.ipc`` nodes, substitute your custom node:

   #. In the graph, delete the ``SimpleSendSimulationClock`` node.
   #. Add your renamed node from the exercise above.
   #. Wire it the same way: Receive External Step ``execOut`` → your node ``execIn``, and Isaac Read Simulation Time ``simulationTime`` → your node ``simulationTime``.
   #. Run the bridge script. Because ``transfer()`` is still a stub that returns ``true`` without sending data, the script will connect but receive no clock output — that is expected. This confirms that your extension loads, enables, and participates in the graph.
   #. To complete the implementation, add the actual send logic to ``transfer()``. Use ``OgnSimpleSendSimulationClockCpp.cpp`` (or the Python equivalent) in ``source/extensions/isaacsim.examples.ipc/`` as a reference.

External Python Playback Bridge
--------------------------------

The ``tcp_tutorial_playback_bridge.py`` script demonstrates a complete roundtrip. It listens for the 8-byte clock the Send node emits, connects to the Receive node's listen port, primes one step, then for each frame reads the clock and sends back the next step so the next ``OnPlaybackTick`` can fire.

The script uses only the Python standard library (``socket``, ``struct``, ``argparse``) and has no Isaac Sim or third-party dependencies. Run it from the repo root with any system ``python3``:

.. code-block:: bash

   python3 source/extensions/isaacsim.examples.ipc/python/scripts/tcp_tutorial_playback_bridge.py

Pass ``--help`` to see ``--clock-host``, ``--clock-port``, ``--step-host``, ``--step-port``, and ``--max-frames`` options.

.. warning::

   The script binds a TCP listener on ``127.0.0.1``. For real deployments, bind only to loopback unless you intentionally expose a port; open interfaces increase attack surface. Treat any IPC bridge like a network service: authentication, TLS or equivalent, and firewall rules are your responsibility.

Performance Considerations
===========================

**Stay within your frame budget.** OmniGraph evaluates ``compute`` on paths that must stay responsive relative to simulation, UI, and other graphs. The usual failure mode is unpredictably long work—waiting on a slow peer, large copies, contended locks, or RPC that can stall for many milliseconds—not "synchronous" I/O by itself.

**Small, fast paths are often fine.** A tiny, fixed-size, fire-and-forget operation in ``compute`` (the tutorial's 8-byte clock send once the socket is connected) can stay on the graph thread if it consistently completes within your per-node budget at the target frame rate. The same applies to other stacks when you have measured the path and it does not wait on back-pressure from the remote side.

**When to use workers, queues, or async APIs.** If a call might block for an unknown duration—request/response, readiness waits, large payloads, or anything that can exceed your per-node budget—run that IPC on a worker thread, use callbacks that enqueue results, and keep ``compute`` to non-blocking dequeue and writing ``db.outputs``. For inbound data, try-receive (as in the tutorial's step node) avoids waiting indefinitely when the external process does not send on your schedule.

- **Async or callback-based I/O:** drive network or IPC on a worker thread, push decoded messages into a thread-safe queue, and let ``compute`` only dequeue (non-blocking) and write ``db.outputs``.
- **Deferred completion:** post work from ``compute`` without waiting for the reply; a background thread enqueues results for a later evaluation.

**Structured messages vs fixed bytes.** The tutorial's fixed-size framing is for clarity. A production bridge typically uses your library's message format (IDL-generated types, JSON, or other schema); you still decide when to send, how to parse inbound data, and how to keep each ``compute`` within budget.

**Large messages (camera frames, point clouds).** Single-shot calls that move multi-megabyte payloads can stress memory and scheduling. Use streaming APIs, explicit back-pressure (drop or skip frames on a slow consumer), or shared-memory / zero-copy paths outside OmniGraph, with the node passing only handles or small metadata.

Built-In Nodes for Data in and Out
===================================

Besides ``isaacsim.examples.ipc``, several extensions register OmniGraph nodes that read simulation state or drive simulation inside |isaac-sim_short|—without acting as a general-purpose bridge to another process. The table highlights types that often sit next to custom IPC nodes in a bridge graph. Before designing your custom node's inputs and outputs, check the ``.ogn`` of the built-in nodes you plan to connect to—their output attribute names and types determine what your node needs to consume or produce.

.. list-table:: Common built-in OmniGraph nodes for bridge-style graphs
   :header-rows: 1
   :widths: 18 28 22 32

   * - Goal
     - Node (registered type)
     - Extension
     - Key inputs / outputs (abbrev.)
   * - Read joint positions / velocities (and efforts) for publishing
     - ``IsaacArticulationState``
     - ``isaacsim.core.nodes``
     - In: ``robotPath`` or ``targetPrim``, optional ``jointNames`` / ``jointIndices``. Out: ``jointPositions``, ``jointVelocities`` (``double[]``), ``jointNames`` (``token[]``), plus measured effort arrays.
   * - Alternative joint state (physics sensor path)
     - ``isaacsim.sensors.physics.IsaacReadJointState``
     - ``isaacsim.sensors.physics.nodes``
     - In: ``prim`` (articulation root). Out: ``jointPositions``, ``jointVelocities``, ``jointEfforts``, ``jointNames``, ``execOut``, etc.
   * - Apply joint position / velocity / effort commands
     - ``IsaacArticulationController``
     - ``isaacsim.core.nodes``
     - In: same robot targeting as above; ``positionCommand``, ``velocityCommand``, ``effortCommand`` (``double[]``). Angular units are radians at the controller API.
   * - Simulation tick / gating
     - ``OnPhysicsStep``, ``IsaacSimulationGate``, ``IsaacReadSimulationTime``, …
     - ``isaacsim.core.nodes``
     - Use to pace state reads and command writes consistently (exact attributes vary by node).
   * - Camera / viewport render product path (setup only)
     - ``IsaacGetViewportRenderProduct``, ``IsaacCreateRenderProduct``, ``IsaacAttachHydraTexture``, ``IsaacSetCameraOnRenderProduct``
     - ``isaacsim.core.nodes``
     - Mostly paths and targets (``renderProductPath``, ``renderProductPrim``); pixels require a separate readback step—see `Camera / Render Products`_.

Other read extensions you may chain before a custom sender:

- ``isaacsim.sensors.physics.nodes`` — IMU, contact, effort, etc., backed by ``isaacsim.sensors.experimental.physics``.
- ``isaacsim.sensors.physx`` — for example Isaac Read Lidar Beams, Isaac Read Lidar Point Cloud, Isaac Read Light Beam Sensor.
- ``isaacsim.sensors.rtx`` — for example Isaac Create RTX Lidar Scan Buffer, Isaac Compute RTX Lidar Flat Scan.

For IPC with external applications (topics, services, or other runtimes), use dedicated bridge extensions—for example ``isaacsim.ros2.nodes`` (ROS 2) or ``isaacsim.ucx.nodes`` (UCX)—rather than treating the table above as a transport; those extensions play the same role as the TCP tutorial nodes, not the sensor-read nodes in the table.

**Reference implementations in this repository.** If you want to see how a full IPC bridge is laid out (``extension.toml`` dependencies, native plugins, C++/Python OmniGraph nodes, and transport backends), browse ``source/extensions/`` for the ROS 2 stack (``isaacsim.ros2.nodes``, ``isaacsim.ros2.bridge``, and related packages) and the UCX stack (``isaacsim.ucx.nodes``, ``isaacsim.ucx.core``, ``isaacsim.ucx.bridge``). Those are the reference implementations to study when you outgrow the TCP tutorial.

Use the OmniGraph node library in the Kit docs to search by name: :doc:`OmniGraph <extensions:ext_omnigraph>`.

Camera / Render Products
========================

Getting raw RGB pixels into a custom IPC node requires more than a plain ``uchar[]`` OGN input. Imagery typically flows through a Replicator pipeline or a render product chain before reaching any IPC encoder—not a single wire in the graph editor. The key steps are:

1. Set up a render product (``IsaacCreateRenderProduct`` or ``IsaacGetViewportRenderProduct``) and attach a camera.
2. Feed the render product into a readback mechanism: either a Replicator annotator (host-friendly NumPy arrays) or a Hydra texture chain (GPU handles via ``IsaacAttachHydraTexture``).
3. Pass the resulting CPU-addressable bytes or arrays into your IPC encoder node.

The ``isaacsim.ros2.bridge`` extension's camera helper node is a concrete reference for how this pipeline is assembled. The ROS 2 camera publisher wires a render product to host readback and then to IPC—browsing that source is the fastest way to understand the pattern before building your own.

See `Performance Considerations`_ before passing large buffers through ``compute``; camera frames are a common source of frame-budget overruns.


Testing Your OmniGraph Node Implementation
==========================================

Python integration tests for OmniGraph nodes can build Action Graphs at runtime using ``og.Controller.edit``, wire nodes together programmatically, drive the timeline, and assert on output attribute values. Useful things to cover:

- Correct outputs: given known inputs, the node produces the expected ``db.outputs`` values.
- ``execOut`` timing: the node fires ``execOut`` only under the intended conditions (every evaluation for send nodes; only on data receipt for receive nodes).
- Reset behavior: changing a URI input or stopping the timeline closes the transport and a subsequent evaluation reopens it cleanly.
- Edge cases: partial messages, peer disconnect, malformed data from the external process.

For C++ helpers (parsing, encoding, endianness), unit tests can run outside Isaac Sim via a native test library such as doctest, wired in ``premake5.lua`` and referenced from ``extension.toml``.

Point ``[[test]]`` entries in your ``extension.toml`` at your test modules. The generated test driver is typically ``_build/<platform>/<config>/tests/tests-<your.extension.id>.sh``. For a scaffolded extension, tests go in ``python/tests/`` (already created by the template).

For examples of the patterns above (async tests, ``OnImpulseEvent``, free-port helpers, timeline control), see ``source/extensions/isaacsim.examples.ipc/python/tests/``.
