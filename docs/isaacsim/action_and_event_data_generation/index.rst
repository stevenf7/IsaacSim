..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _action_and_event_data_generation:

==================================
Action and Event Data Generation
==================================

**Action and Event Data Generation** is a reference application for |isaac-sim_short| that provides a suite of extensions for realistic indoor simulation and large-scale synthetic data generation. It is designed to address the challenges of collecting high-quality, diverse, and richly labeled datasets for training Vision AI models.

Real-world data collection often faces limitations in scalability, cost, and the ability to capture rare or dangerous scenarios (such as accidents or near-misses). This application enables the programmatic generation of synthetic data that is accurate and diverse, effectively bridging the gap between simulation and real-world deployment.

Key Features
------------

*   **Ground Truth Generation**: Provides accurate ground truth across multiple modalities by leveraging :ref:`Replicator <isaac_replicator_tutorials_page>` for precise data capture and rich annotation.
*   **Rare Event Generation**: Enables the programmatic creation of rare and long-tail events to improve model robustness.
*   **Scalable Workflow**: Supports both an interactive interface for rapid prototyping and a headless batch generation mode for producing massive, reproducible datasets.
*   **Configurable Control**: Utilizes YAML configuration files to define scenes, agents, and events, ensuring the data generation process is versionable and reproducible.

Architecture and Workflow
-------------------------

Built on the Omniverse platform, this toolset integrates technologies such as `Omniverse Animation <https://docs.omniverse.nvidia.com/extensions/latest/ext_anim.html>`_ for character behaviors, `Omniverse Flow <https://docs.omniverse.nvidia.com/extensions/latest/ext_fluid-dynamics/using.html>`_ for dynamic events, and :ref:`Replicator <isaac_replicator_tutorials_page>` for data capture.

The architecture employs a layered approach to scene construction and data capture. **Object Simulation** defines the static environment, which serves as the foundation for dynamic elements introduced by **Event Generation** and **Actor Simulation**. The pipeline culminates in the data acquisition phase, where **Sensor Placement** optimizes sensor coverage and **VLM Scene Captioning** synthesizes semantic descriptions.

Launching the Application
-------------------------

To launch the app, use:

*   **Linux**: ``./isaac-sim.action_and_event_data_generation.sh``
*   **Windows**: ``.\isaac-sim.action_and_event_data_generation.bat``

The application launches with the Action and Event Data Generation extensions pre-enabled and a custom workspace layout.

Action and Event Data Generation Stack
--------------------------------------

.. image:: /images/isim_6.0_full_ref_external_action_and_event_data_generation_stack.png
    :width: 900
    :align: center
    :alt: Action and Event Data Generation Extension Stack

Extensions
----------

The core functionality is provided by a set of application-level extensions and supporting tools:

.. list-table::
   :widths: 25 30 45
   :header-rows: 1

   * - Extension
     - API Name
     - Description
   * - Actor Simulation and SDG
     - ``isaacsim.replicator.agent.core``
     - The **Isaac Sim Replicator Agent (IRA)** extension simulates intelligent actors in 3D environments. It handles complex human and robot behaviors, from large-scale routines like warehouse operations (for example, workers patrolling, forklifts roaming) to specific reactions to dynamic events. It captures diverse data and action metadata.
   * - Object Simulation and SDG
     - ``isaacsim.replicator.object.core``
     - The **Isaac Sim Replicator Object (IRO)** extension allows you to programmatically create and place objects at scale. It can procedurally generate unique shapes, automatically stack racks, and pack boxes before applying physics to settle the scene realistically.
   * - Physical Space Event Generation
     - ``isaacsim.replicator.incident.core``
     - The **Isaac Sim Replicator Incident (IRI)** extension generates realistic, configurable physical events. It orchestrates simulations using Omniverse Flow and PhysX to create scenarios ranging from spills and toppling boxes to complex fires with smoke, all with rich annotation and event metadata.
   * - VLM Scene Captioning
     - ``isaacsim.replicator.caption.core``
     - The **Isaac Sim Replicator Caption (IRC)** extension bridges the gap between vision and language. It analyzes the scene to build a scene graph (objects and spatial relationships) and uses an LLM to generate rich, human-readable descriptions (global and brief captions) and visualized scene graphs.
   * - RTX Sensor Placement
     - ``isaacsim.sensors.rtx.placement``
     - The **RTX Sensor Placement (ISP)** extension automates camera positioning. It algorithmically places sensors to maximize visual coverage, focus on points of interest, control occlusion, or create Bird's-Eye-View groups, while extracting intrinsic and extrinsic calibration data.
   * - RTX Sensor Calibration
     - ``isaacsim.sensors.rtx.calibration``
     - The **RTX Sensor Calibration (ISC)** extension generates camera calibration data for deployed cameras in the scene.
   * - Behavior tree generation
     - ``omni.ai.behavior_tree_gen.core`` and ``omni.ai.behavior_tree_gen.bridge``
     - The **Behavior Tree Generation** workflow converts natural-language scenarios into behavior tree outputs. ``omni.ai.behavior_tree_gen.core`` provides the reusable pipeline and scripted API, while ``omni.ai.behavior_tree_gen.bridge`` provides the Kit UI, example loaders, and interactive workflow orchestration.
   * - Animated Robot Controller
     - ``isaacsim.anim.robot``
     - The **Animated Robot Controller (IAR)** extension enables realistic robot animation by playing back captured simulation motion data. It bridges physics-based simulation and animation, allowing for precise robot movements without the overhead of real-time physics.
   * - Action and Event Generation Utilities
     - ``omni.metropolis.utils``
     - The **Action and Event Generation Utilities (OMU)** extension provides shared utilities across the Action and Event Generation extension stack.
   * - Chat IRO
     - ``omni.ai.langchain.agent.chat_iro``
     - **Chat IRO** is an AI assistant that enables natural language scene authoring for the **Object Simulation (IRO)** extension. It allows users to describe scenes in plain English to automatically generate YAML configurations, providing immediate viewport previews and iterative editing capabilities.

Extension Tutorials
-------------------

.. toctree::
   :maxdepth: 1

   ./tutorial_replicator_agent
   ./tutorial_behavior_tree_gen
   ./tutorial_replicator_object
   ./tutorial_replicator_caption
   ./tutorial_replicator_incident
   ./tutorial_sensors_rtx_placement


Integration Examples
--------------------

End-to-end examples that wire multiple extensions together.

.. toctree::
   :maxdepth: 1

   ./example_event_reactive_actors


Other Tools and Utilities
-------------------------

.. toctree::
   :maxdepth: 1

   ./tutorial_omni_metropolis_pipeline
   ./tutorial_telemetry
