.. _agent_planner_example_walkthrough:

===================
Example Walkthrough
===================

This walkthrough uses the bundled **Test Stage Simple** example and the planner UI.

Goal
----

Generate a behavior tree for the following scenario:

.. code-block:: text

    Anna picks up the CardBox_A and places it on the Table.

Steps
-----

1. Open **Agent Planner Examples** from **Window > Examples > Agent Planner Examples**.
2. In **Agent Planner Examples**, select **Test Stage Simple** and click the button to load the
   example scene.

   * This loads the bundled demo stage.
   * It also pre-fills the planner panels using the **Test Stage Simple** scene configuration.
   * The **Agent Planner** window is shown automatically, so you do not need to open it separately.

3. In **Agent Planner**, verify the loaded inputs.

   * The **Context Cache Files** panel should contain the example actor and object context files and
     node catalogs.
   * The **Network Config** panel should contain the example model JSON paths.
   * The **Output Settings** panel should point to a writable output directory.

4. Enter a valid NVIDIA API key, if one is not already available from settings or the environment.
5. Paste or type the scenario text:

   .. code-block:: text

       Anna picks up the CardBox_A and places it on the Table.

6. Click **Run Pipeline**.

What Happens Internally
-----------------------

When you click **Run Pipeline**, the bridge performs the same three API steps it uses in scripted
mode:

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

Useful Behavior to Know
-----------------------

* If you run the same scenario again without changing the tracked input files, the extension can
  reuse the loaded workspace and prepared runtime.
* If you change a tracked file such as a context file, node catalog, or model config, the extension
  reloads the workspace and prepares the runtime again.
* You can repeat the same flow with **Test Stage Warehouse** to test a multi-actor scenario.
