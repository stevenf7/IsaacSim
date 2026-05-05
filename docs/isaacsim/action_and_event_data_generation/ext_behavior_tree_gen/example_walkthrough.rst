..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _behavior_tree_gen_example_walkthrough:

===================
Example Walkthrough
===================

This walkthrough uses the bundled **Basic Scene** scene and the **Behavior Tree Gen**
workflow shipped in ``omni.ai.behavior_tree_gen.bridge``.

Goal
----

Generate a behavior tree for the following scenario:

.. code-block:: text

    Anna picks up the CardBox_A and places it on the Table.

Steps
-----

1. Open the examples window from **Window > Examples > Behavior Tree Gen Examples**.
2. In the examples window, select **Basic Scene** and click the button to load the example
   scene.

   * This loads the bundled demo stage.
   * It also pre-fills the workflow panels from the ``Basic Scene`` scene configuration.
   * The **Behavior Tree Gen** window is shown automatically, so you do not need to open it
     separately.

3. In **Behavior Tree Gen**, verify the loaded inputs.

   * The **Context Cache Files** panel should contain the example actor and object context files,
     node catalogs, and metadata schemas.
   * The **Network Config** panel should contain the example model JSON paths.
   * The **Output Settings** panel should point to a writable output directory.

4. Enter a valid NVIDIA API key, if one is not already available from settings or the environment.
5. Paste or type the scenario text:

   .. code-block:: text

       Anna picks up the CardBox_A and places it on the Table.

6. Click **Run Pipeline**.

What Happens Internally
-----------------------

When you click **Run Pipeline**, the **Behavior Tree Gen** UI performs the same three public API steps that scripted
callers use:

1. It creates or reloads the planner workspace from the selected context, catalog, schema, and
   blackboard files.
2. It prepares the runtime by configuring the LLM, embedding setup, RAG retrievers, and Action IR.
3. It generates the behavior tree from the natural-language scenario.

Expected Result
---------------

If the run succeeds:

* the status line reports that generation completed successfully
* behavior tree output files are written under the selected output folder
* planner cache data is stored under a workspace cache directory
* RAG and vectorstore data is stored under the derived cache directory

Known limitations of Example Actions
-------------------------------------

.. note::

   The custom actions bundled with the examples (such as ``MoveTo``) are provided to demonstrate that
   the system supports action node imports and is fully extensible. At this stage, some actions may
   exhibit imperfect behavior. For example, ``MoveTo`` can produce paths that overlap with the target
   object. These examples serve as a transitional reference, a more comprehensive and refined set of
   actions is planned.

Useful Behavior to Know
-----------------------

* If you run the same scenario again without changing the tracked input files, the extension can
  reuse the loaded workspace and prepared runtime.
* If you change a tracked file such as a context file, node catalog, schema, or model config, the
  extension reloads the workspace and prepares the runtime again.
* You can repeat the same flow with **Warehouse Scene** to test a multi-actor scenario.
