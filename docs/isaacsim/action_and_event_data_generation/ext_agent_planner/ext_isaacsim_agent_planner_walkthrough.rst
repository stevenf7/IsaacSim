..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_ext_agent_planner_walkthrough:

=========================
IAP Example Walkthrough
=========================

This guide provides a step-by-step walkthrough for using the Isaac Agent Planner (IAP) to generate behavior trees from natural language scenario descriptions using the built-in example scene.

For manual configuration and Python API usage, see the :doc:`IAP Configuration and API Reference <ext_isaacsim_agent_planner_api>`.


Prerequisites
-------------

Before starting, ensure you have:

1. **Isaac Sim Installed**: NVIDIA Omniverse Isaac Sim 4.5 or later
2. **Extensions Enabled**: Both ``isaacsim.agent.planner.core`` and ``isaacsim.agent.planner.bridge`` extensions
3. **API Key Configured**: An API key for LLM services (NVIDIA NIM or compatible endpoint)
4. **GPU**: RTX 4080+ or datacenter GPU (A40, L40S) for optimal performance


Quick Start with Example Scene
------------------------------

The fastest way to try IAP is using the built-in example scene.

Step 1: Enable the Extensions
#############################

1. Open Isaac Sim
2. Navigate to **Window** > **Extensions**
3. Search for ``isaacsim.agent.planner``
4. Enable both:

   - ``isaacsim.agent.planner.core``
   - ``isaacsim.agent.planner.bridge``


Step 2: Open the IAP Bridge Window
##################################

After enabling the extensions, the *IAP Bridge* window opens automatically. If not visible:

1. Navigate to **Tools** > **IAP Bridge**
2. The *IAP Bridge* window will appear on the right side of the screen


Step 3: Load the Example Scene
##############################

1. In the *Scenario Execution* panel at the bottom of the *IAP Bridge* window
2. Click the **Load Example Scene** button
3. Wait for the status message: *"Example scene loaded: X actors configured"*

This action will:

- Open a pre-configured test stage with actors and objects
- Load example context files (actors, objects, node catalog)
- Set up the OBC environment (motion library, node libraries, blackboard)
- Configure all actors with default idle behavior trees


Step 4: Configure NVIDIA API Key
################################

Before running the pipeline, configure your NVIDIA API key for LLM access:

1. In the *IAP Bridge* window, locate the *Network Configuration* panel
2. Find the **API Key** field
3. Enter your NVIDIA API key (format: ``nvapi-XXXX...``)

.. note::

   If you do not have an NVIDIA API key, visit the `NVIDIA API portal <https://build.nvidia.com>`_ to obtain one. See the `NVIDIA API reference page <https://docs.api.nvidia.com/nim/reference/llm-apis>`_ for more details on API usage and credits.

Alternatively, you can set the API key as an environment variable before launching Isaac Sim:

.. code-block:: bash
   :caption: Setting NVIDIA API key via environment variable

   export NVIDIA_API_KEY="nvapi-YOUR-KEY-HERE"


Step 5: Enter a Scenario Description
####################################

In the *Scenario Execution* panel:

1. Find the **Scenario Description** text area
2. Enter a natural language description of what you want actors to do

Example scenarios:

.. code-block:: text
   :caption: Simple pick and place scenario

   Anna picks up the box and places it on the table.


.. code-block:: text
   :caption: scenario with semantic description

   Anna walks to the black chair. 


Step 6: Run the Pipeline
########################

1. Click the **Run Pipeline** button
2. Watch the status messages as the pipeline progresses:

   - *"Validating configuration..."*
   - *"Loading context data..."*
   - *"Generating behavior trees..."*
   - *"Pipeline completed!"*


Step 7: View the Results
########################

When the pipeline completes successfully:

1. **Status Message**: Shows how many actors have generated behavior trees
2. **Console Log**: Detailed information about generated files
3. **Output Folder**: Generated behavior tree JSON files saved to the configured output path


Step 8: Run the Simulation
##########################

1. Click **Play** in the timeline toolbar
2. Actors will execute their generated behavior trees
3. Click **Stop** to end the simulation


Step 9: Generate Synthetic Data (Optional)
##########################################

Once your actors are executing their generated behavior trees, you can capture synthetic data for training computer vision models or other AI applications.

The :doc:`Synthetic Data Recorder </replicator_tutorials/tutorial_replicator_recorder>` provides a GUI extension for recording synthetic data from your simulation. It supports:

- Multiple camera render products with configurable resolutions
- Various annotators including RGB, depth, semantic segmentation, and bounding boxes
- Custom writers for specialized data formats
- Timeline-synchronized recording

To record synthetic data from your IAP-generated scene:

1. Open the Synthetic Data Recorder from **Tools** > **Replicator** > **Synthetic Data Recorder**
2. Add render products for the cameras in your scene
3. Select the annotators you need (RGB, bounding boxes, segmentation, etc.)
4. Configure the output directory
5. Click **Start** to begin recording while the simulation runs

For detailed instructions on using the recorder, see the :doc:`Synthetic Data Recorder Tutorial </replicator_tutorials/tutorial_replicator_recorder>`.


Next Steps
----------

- Read the :doc:`IAP Introduction <ext_isaacsim_agent_planner>` for architecture details
- See the :doc:`IAP Configuration and API Reference <ext_isaacsim_agent_planner_api>` for manual configuration, Python API usage, troubleshooting, and best practices
- Explore the :doc:`Omni Behavior Composer <../ext_replicator-agent/ext_omni_behavior_composer>` for behavior tree fundamentals

