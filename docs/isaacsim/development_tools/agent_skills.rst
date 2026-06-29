..
   Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_agent_skills:


==========================================
Agent Skills
==========================================

Agent skills are version-controlled workflow guides that teach AI coding agents — such as Cursor, Claude Code, and Codex Command-Line Interface (CLI) — how to perform |isaac-sim_short| tasks: importing robots, configuring physics, generating synthetic data, rendering, driving a running instance, and more. Each skill is a Markdown file (``SKILL.md``) that an agent loads on demand when your request matches the skill's subject.

The skills ship with |isaac-sim_short| in the ``skills/`` directory, so you do not need to clone the source repository to use them. They are present in the source tree and are bundled into both the pip packages and the binary package. When a skill-aware agent can see the ``skills/`` directory, the agent follows the same procedures and avoids the same pitfalls that the |isaac-sim_short| team encoded.

|br| |hr|

.. _isaac_sim_agent_skills_how_they_work:

How Skills Work
---------------

A skill is a directory that contains a ``SKILL.md`` file plus optional ``scripts/`` and ``references/`` subdirectories:

- The ``SKILL.md`` frontmatter holds a ``name`` and a ``description``. The agent reads the description to decide *when* to load the skill.
- The Markdown body holds the procedure, code snippets, reference tables, and known gotchas. The agent reads the body only when your task matches the description.
- ``scripts/`` holds runnable helper scripts the skill invokes; ``references/`` holds longer reference material the skill links to.

Skill-aware agents discover skills through pointer files at the repository root:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Agent
     - Discovery mechanism
   * - Cursor
     - ``.cursor/rules/agent_skills.mdc`` points the agent at every ``SKILL.md`` under ``skills/``.
   * - Claude Code
     - ``CLAUDE.md`` and the symlinks under ``.claude/skills/`` expose the same skills to native skill discovery.
   * - Codex CLI and other ``AGENTS.md``-aware tools
     - ``AGENTS.md`` instructs the agent to read every ``SKILL.md`` under ``skills/`` at session start.

The library is organized in two layers:

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Layer
     - Purpose
   * - Repo-native
     - Build, test, debug, and profile this |isaac-sim_short| source repository. These skills call in-repo tooling (``build.sh``, ``tools/``, benchmark scripts, the ``python_server`` socket), so they are most useful in the source-build workflow.
   * - Robotics-sim
     - Build, render, and validate |isaac-sim_short| simulations as a downstream user. These skills drive a built |isaac-sim_short| from a Python script (``SimulationApp``, ``isaacsim.core.experimental.*``, USD authoring), so they apply to all three workflows below.

|br| |hr|

.. _isaac_sim_agent_skills_available:

Available Skills
----------------

The following tables list the skills shipped with |isaac-sim_short|. The full categorized index, with pipeline diagrams and a recommended read order, is in ``skills/SKILLS.md`` (`view on GitHub <skills_index_github_>`_).

Repo-native skills
^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Skill
     - What it does
   * - ``isaac-sim-remote``
     - Drive a running |isaac-sim_short| over the ``isaacsim.code_editor.python_server`` Transmission Control Protocol (TCP) socket: run code, open stages, inspect or modify prims, take screenshots, step physics, and read console logs. Works headless.
   * - ``profile-isaac-sim``
     - Profile and optimize |isaac-sim_short| with the in-repo benchmark scripts and Tracy. Compare runs, diff frame times, and isolate hot zones.
   * - ``validation-diff-gifs``
     - Build pixel-difference GIFs comparing a validation capture against its golden data — the fastest way to triage benchmark image failures.

Foundations and operating loop
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Skill
     - What it does
   * - ``isaac-sim-orchestrator``
     - Top-level dispatcher that turns a natural-language request into a runnable simulation and declares the environment-variable contract every other skill assumes.
   * - ``meta-skills``
     - Composition patterns and the Meta-Skilling Framework. Read first to learn how to navigate, compose, and author skills.
   * - ``skill-distillation``
     - The final step of every request: capture what you learned before delivering.
   * - ``isaac-sim-validator``
     - Final quality gate before delivery. Rejects black frames, hardcoded user paths, deprecated imports, and missing lights.
   * - ``isaac-sim-troubleshooting``
     - Hang, freeze, and performance reference for large Universal Scene Description (USD) stages.

Robot asset pipeline
^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Skill
     - What it does
   * - ``urdf-mjcf-to-usd-conversion``
     - Convert Unified Robot Description Format (URDF) and MuJoCo XML (MJCF) descriptions to USD for |isaac-sim_short| and Isaac Lab. Every new robot starts here.
   * - ``usd-articulation``
     - Validate and assemble multi-link and multi-arm articulations, and flatten them before deployment.

Physics simulation
^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Skill
     - What it does
   * - ``physics-simulation``
     - Single source of truth for physics scene configuration and per-prim setup: rigid bodies, collisions, joint drives, contact materials, and Newton-versus-PhysX solver selection.

Mobile robot navigation
^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Skill
     - What it does
   * - ``navigation-primitives``
     - Shared substrate for mobile-robot work: occupancy maps, A* planning, robot footprints, and chase-camera math. Read first.
   * - ``occupancy-map``
     - Generate Robot Operating System (ROS)-compatible occupancy maps from USD warehouses.
   * - ``isaac-sim-robot-navigation``
     - Runtime navigation in custom scripts, including reinforcement-learning policies and large-stage memory management.
   * - ``mobility-gen``
     - Two-phase synthetic-data generation for mobile robots: record trajectories, then replay and render sensors.

Manipulation
^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Skill
     - What it does
   * - ``manipulation-ik``
     - Differential inverse kinematics, grasp frames, and hybrid inverse-kinematics with joint-space control.

Sensors and perception
^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Skill
     - What it does
   * - ``isaac-sim-sensor``
     - Replicator sensor suite (RGB, depth, segmentation, LiDAR, Inertial Measurement Unit (IMU), contact) plus the vendor LiDAR and radar catalog.
   * - ``isaac-camera``
     - Camera setup, render products, intrinsics, annotators, and lens distortion.

Synthetic data generation
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Skill
     - What it does
   * - ``data-collection-sim``
     - Static-scene Replicator synthetic-data generation with the standard writers.

Rendering and lighting
^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Skill
     - What it does
   * - ``isaac-sim-rendering``
     - Headless production rendering: Replicator capture, ray-traced versus path-traced modes, tone mapping, and lighting recipes.
   * - ``isaac-sim-headless-deployment``
     - Headless ``--no-window`` usage: launch modes, CLI flags, and the ``SimulationApp`` batch pattern.

USD pipeline
^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Skill
     - What it does
   * - ``spatial-reasoning``
     - Transform math: meters-per-unit conversion, bounding boxes, placement ordering, look-at, and collision-free grids.
   * - ``usd-pipeline``
     - Asset discovery, measurement, placeholder-to-asset placement, and headless render compatibility.
   * - ``usd-composition-architecture``
     - NVIDIA's layered USD pattern (root plus physics plus appearance payloads) and load-time optimization.

ROS 2 integration
^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Skill
     - What it does
   * - ``isaac-sim-ros2-bridge``
     - OmniGraph ROS 2 nodes, Nav2 integration, and multi-robot namespacing.

|br| |hr|

.. _isaac_sim_agent_skills_configure:

Configure Your Environment
--------------------------

Setup has two parts: make the skills visible to your agent, and define the environment-variable contract the skills rely on.

Step 1: Locate the skills and expose them to your agent
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The skills ship with every install. Their location depends on your workflow:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Workflow
     - Skills location
   * - Source build
     - ``<repo>/skills/`` (and mirrored into the build output at ``$ISAAC_SIM_DIR/skills``).
   * - Pip package
     - ``<isaacsim package>/skills/``. Find the package directory with ``pip show isaacsim``.
   * - Binary package
     - ``$ISAAC_SIM_DIR/skills/`` under the install root.

Every install also bundles the ``AGENTS.md`` and ``CLAUDE.md`` pointer guides next to ``skills/`` (at the repository root, the install root, or the ``isaacsim`` package directory). These guides instruct an agent to read the ``SKILL.md`` files under ``skills/``.

Expose the skills to your agent in one of the following ways:

- **Source build** — Open the repository as your agent's workspace root. The pointer files (``AGENTS.md``, ``CLAUDE.md``, and ``.cursor/rules/agent_skills.mdc``) load the skills automatically.
- **Pip or binary install** — Open the directory that holds ``skills/``, ``AGENTS.md``, and ``CLAUDE.md`` as your agent's workspace root: Cursor and Codex CLI read ``AGENTS.md``, and Claude Code reads ``CLAUDE.md``. Alternatively, copy or symlink ``skills/`` into your own project, link it into your agent's skills directory (for example ``~/.claude/skills/``), or instruct the agent to read the ``SKILL.md`` files under that path.

.. note::

   Published packages include the public skill directories, the ``SKILLS.md`` index, and the public ``AGENTS.md`` and ``CLAUDE.md`` guides. The Cursor rules under ``.cursor/rules/`` are not bundled, but ``AGENTS.md`` is sufficient for Cursor. Dev-only skills under ``skills/_internal`` are not packaged.

Step 2: Set the environment-variable contract
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Skills reference these shell variables instead of hardcoding paths. Set them in your agent configuration or your shell profile so the skills resolve to your install:

.. list-table::
   :header-rows: 1
   :widths: 22 43 35

   * - Variable
     - Purpose
     - Example
   * - ``ISAAC_SIM_DIR``
     - |isaac-sim_short| install root or built repository path.
     - ``<repo>/_build/linux-x86_64/release`` (source) or the install root (pip or binary).
   * - ``ISAAC_LAB_DIR``
     - Isaac Lab checkout, when present.
     - ``$ISAAC_SIM_DIR/IsaacLab``
   * - ``WORKSPACE_DIR``
     - Per-agent outputs, scratch, and caches.
     - A project-local path or ``~/.cache/isaacsim``.
   * - ``CIP_ROOT`` (Windows)
     - Content-pipeline install, when used.
     - ``C:\_Data``

.. note::

   Several skills, including ``isaac-sim-remote``, drive a running |isaac-sim_short| over the ``isaacsim.code_editor.python_server`` socket on port ``8226``. Enable that extension before using those skills. See :ref:`isaac_sim_app_python_server`.

|br| |hr|

.. _isaac_sim_agent_skills_workflows:

Workflows
---------

The skills are the same across all three workflows. What differs is where the bundled ``skills/`` directory lives, where ``ISAAC_SIM_DIR`` points, and how you launch |isaac-sim_short|.

.. list-table::
   :header-rows: 1
   :widths: 22 26 26 26

   * - 
     - Source build
     - Pip package
     - Binary package
   * - Skills location
     - ``<repo>/skills``
     - ``<isaacsim package>/skills``
     - ``$ISAAC_SIM_DIR/skills``
   * - ``ISAAC_SIM_DIR``
     - ``<repo>/_build/linux-x86_64/release``
     - Pip install location
     - Install root
   * - Launch and Python
     - ``./python.sh`` or ``python_server``
     - ``isaacsim`` entry point or venv ``python``
     - ``./isaac-sim.sh`` or ``./python.sh``

Build from source
^^^^^^^^^^^^^^^^^^

Use this workflow when you develop |isaac-sim_short| itself or need the repo-native skills.

#. Clone and build the repository (``./build.sh`` on Linux, ``build.bat`` on Windows).
#. Set ``ISAAC_SIM_DIR`` to the build output: ``<repo>/_build/linux-x86_64/release``.
#. Open the repository in your agent. All skills load, including the repo-native ``profile-isaac-sim`` and ``validation-diff-gifs`` skills, which depend on the in-repo benchmark and validation tooling.
#. Run scripts with ``./python.sh path/to/script.py``, or drive a running instance over the :ref:`Python server <isaac_sim_app_python_server>`.

Pip package
^^^^^^^^^^^

Use this workflow when you install |isaac-sim_short| as Python packages into a virtual environment.

#. Install the packages as described in :ref:`isaac_sim_app_install_pip`, for example ``pip install "isaacsim[all,extscache]==6.0.1.0" --extra-index-url https://pypi.nvidia.com``. The ``isaacsim`` package bundles the ``skills/`` directory.
#. Set ``ISAAC_SIM_DIR`` to the pip install location. Query it with ``pip show isaacsim``. The skills are at ``$ISAAC_SIM_DIR/skills``.
#. Expose the bundled skills to your agent as described in :ref:`isaac_sim_agent_skills_configure`.
#. Run scripts with the virtual environment's ``python``, or launch experiences with the ``isaacsim`` entry point. The robotics-sim skills apply directly; the repo-native profiling and validation skills are limited because they expect the source tree.

Binary package
^^^^^^^^^^^^^^^

Use this workflow when you install the prepackaged binary build.

#. Download and install the binary as described in :ref:`isaac_sim_download` and :ref:`isaac_sim_app_install_workstation`. The binary bundles the ``skills/`` directory at the install root.
#. Set ``ISAAC_SIM_DIR`` to the install root (for example, ``~/isaacsim``). The skills are at ``$ISAAC_SIM_DIR/skills``.
#. Expose the bundled skills to your agent as described in :ref:`isaac_sim_agent_skills_configure`.
#. Launch the app with ``./isaac-sim.sh`` (Linux) or ``isaac-sim.bat`` (Windows), and run scripts with ``./python.sh`` (Linux) or ``python.bat`` (Windows). As with the pip workflow, the robotics-sim skills apply directly and the repo-native skills are limited.

|br| |hr|

.. _isaac_sim_agent_skills_security:

Security
--------

Skills such as ``isaac-sim-remote`` execute arbitrary Python inside the running Kit process, which has full filesystem and network access. The agent's tool allow-list shapes only the agent's own file tools; it does not contain the Python that runs in-process.

- Run a skill-driven agent only in an environment you would trust the agent to act in. An operating-system sandbox (restricted filesystem and network egress) around the |isaac-sim_short| process is the real security boundary.
- Keep the ``isaacsim.code_editor.python_server`` ``host`` setting bound to ``127.0.0.1``. Binding it to ``0.0.0.0`` lets any machine on the network execute arbitrary Python in your session. See :ref:`isaac_sim_app_python_server`.

|br| |hr|

See Also
--------

- :ref:`isaac_sim_app_python_server` — the socket many skills use to drive a running instance.
- :ref:`isaac_sim_app_mcp_server` — Model Context Protocol server that gives AI assistants semantic search over |isaac-sim_short| knowledge.
- :ref:`isaac_sim_app_install_pip` — install |isaac-sim_short| as Python packages.
- :ref:`isaac_sim_app_install_workstation` — install the binary build on a workstation.

.. _skills_index_github: https://github.com/isaac-sim/IsaacSim/blob/main/skills/SKILLS.md
