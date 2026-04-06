..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_agent_planner:

====================
Isaac Agent Planner
====================

**Isaac Agent Planner** helps turn natural-language scene instructions into behavior tree outputs for
simulation workflows. The planner is organized around the ``isaacsim.agent.planner.bridge`` extension for
the Kit user experience and the ``isaacsim.agent.planner.core`` extension for the core pipeline.

The workflow supports both interactive usage in the Isaac Sim UI and scripted usage through the
``isaacsim.agent.planner.core.api`` module. The bridge extension provides the user-facing tools,
while the core extension owns the reusable planning pipeline that produces behavior tree outputs.

Before enabling this extension, read :doc:`What Is Isaac Sim? </overview/overview>` to learn about
|isaac-sim_short| and follow :doc:`Installation </installation/index>` to install |isaac-sim_short|.

Enable Extensions
-----------------

1. Follow the `Omniverse Extension Manager guide <https://docs.omniverse.nvidia.com/extensions/latest/ext_core/ext_extension-manager.html>`_
   to enable ``isaacsim.agent.planner.bridge``. When the bridge extension loads, it can drive the planner
   workflow exposed by ``isaacsim.agent.planner.core``.
2. **Agent Planner** window is accessed from **Tools > Agent Planner**.
3. Optional: open **Window  > Examples > Agent** Planner to load bundled example stages such as
   ``simple`` or ``warehouse`` and setup **Agent Planner** window.

.. note::

   The planner workflow expects scene context files, node catalogs, model configuration files, a writable
   output directory, and a valid NVIDIA API key before a generation run can succeed.

What the Bridge Does
--------------------

``isaacsim.agent.planner.bridge`` is the integration layer between the Isaac Agent Planner core
pipeline and the Kit user experience.

* **Agent Planner** window allows users to enter a natural-language scenario and run the
  planner workflow.

.. image:: /images/isim_6.0_full_ext-isaacsim.agent.planner_configuration_window.png
    :width: 500
    :align: center
    :alt: Extension relationship.

|

* **Agent Planner Examples** window helps users load bundled demo stages such as
  ``simple`` and ``warehouse``.

.. image:: /images/isim_6.0_full_ext-isaacsim.agent.planner_example_window.png
    :width: 500
    :align: center
    :alt: Extension relationship.

|

* Connects scene and cache data to the planner runtime so actor and object context, node catalogs,
  blackboard data, and model configuration files are available to the planner.
* Coordinates the end-to-end planner workflow inside Isaac Sim.

Supported Workflows
-------------------

Agent Planner supports both of the following workflows:

* **Interactive testing and demos** inside Kit, where a user wants a UI-driven workflow.
* **Scripted usage**, where the same planner flow is called from Python APIs.

If the tracked input files do not change between runs, the bridge can reuse the loaded workspace and
prepared runtime instead of rebuilding everything from scratch.

Workflow Overview
-----------------

A typical UI session starts from **Agent Planner Examples** or from manually selected planner input
files. The examples flow is the fastest way to begin because it loads a sample stage and pre-fills
the planner panels, while manual usage lets you point the planner at your own context, catalog,
schema, and model configuration files.

After the inputs are available, use the **Agent Planner** window to review the loaded files, choose
the output location, provide a valid NVIDIA API key, and enter the natural-language scenario that
should be converted into behavior tree output.

For the full step-by-step UI flow, expected outputs, and example scenario, see :doc:`Example Walkthrough <./ext_agent_planner/example_walkthrough>`.

Core API
--------

``isaacsim.agent.planner.core`` provides the reusable planning pipeline used by both the UI and
Python callers. Its public API exposes ``setup_workspace(...)``, ``prepare_runtime(...)``, and
``generate_behavior_tree(...)`` for the same workflow used by the bridge UI.

For a tutorial on authoring planner context files and metadata schemas, refer to :doc:`Context Files and Metadata Schemas <./ext_agent_planner/context_files_and_schemas>`.
For the full API sequence and script example, refer to :doc:`Using the Three API Functions <./ext_agent_planner/three_api_functions>`.

Detailed Guides
---------------

For more detailed guidance on the planner workflow, schema-based context authoring, inputs, example
usage, and API sequence, refer to the following pages:

.. toctree::
    :maxdepth: 1

    ./ext_agent_planner/context_files_and_schemas
    ./ext_agent_planner/required_inputs
    ./ext_agent_planner/example_walkthrough
    ./ext_agent_planner/three_api_functions

Terminology
-----------

.. dropdown:: isaacsim.agent.planner.bridge

    The bridge extension provides the Kit and Omniverse user experience for Agent Planner. It exposes
    the UI windows, example loaders, and pipeline execution entry points used by interactive workflows.

.. dropdown:: isaacsim.agent.planner.core

    The core extension provides the reusable planner pipeline and public API used to prepare runtime
    state and generate behavior tree output from natural-language scenarios.

.. dropdown:: PlannerSession

    ``PlannerSession`` is the reusable workspace state returned by ``setup_workspace(...)``. The same
    session can be reused across runs when the tracked planner inputs do not change.
