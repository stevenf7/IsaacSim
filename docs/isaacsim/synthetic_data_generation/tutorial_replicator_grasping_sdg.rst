..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_replicator_grasping_sdg:

==========================================
Grasping Synthetic Data Generation
==========================================

This tutorial introduces the ``isaacsim.replicator.grasping`` extension and its associated UI, ``isaacsim.replicator.grasping.ui``. These tools provide a comprehensive workflow for generating synthetic grasping datasets in |isaac-sim_short|.

Learning Objectives
-------------------

After completing this tutorial, you will be able to:

*   Understand the core components and data flow of the Grasping SDG extension.
*   Navigate and utilize the Grasping SDG UI to configure and run grasp generation workflows.
*   Define gripper properties, joint states, and multi-step grasp phases.
*   Configure object properties and grasp pose sampling parameters.
*   Execute and interpret the results of physics-based grasp evaluations.
*   Manage grasping configurations using YAML files for saving, loading, and sharing setups.

The extensions are automatically loaded in |isaac-sim_short|, and the UI window can be opened from the main menu using **Tools** > **Replicator** > **Grasping**.

.. image:: /images/isim_5.0_replicator_tut_viewport_grasping_workflow.webp
    :align: center
    :alt: Grasping workflow overview

Getting Started
---------------

Before proceeding, it is recommended that you familiarize yourself with:

*   :ref:`Simulation Fundamentals <simulation_fundamentals>`: For understanding physics simulation concepts and gripper rigging (for example, drive joints).
*   :ref:`Grasp Editor <isaac_sim_app_tutorial_grasp_editor_import>`: This tutorial covers related concepts and provides a foundation for grasp definition.

.. note::

    The grasp sampler requires the ``libspatialindex`` library. If you see related warnings, install it (for example, on Ubuntu: ``sudo apt-get install libspatialindex-dev``).

This tutorial utilizes an example stage that includes a pre-configured gripper and objects suitable for grasping exercises. You can find this stage at:

::

    https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0
    /Isaac/Samples/Replicator/Stage/sdg_grasping_xarm.usd

The stage asset can be found in the **Content Browser** under **Isaac Sim** > **Samples** > **Replicator** > **Stage** > **sdg_grasping_xarm.usd**, or can be loaded using by inserting the whole URL in the path field.

The example stage features a gripper with drive joints and three objects equipped with rigid body physics and colliders. Gravity is disabled for these objects to simplify initial interactions. The Grasping UI window typically docks in the **Property** panel upon opening.

.. image:: /images/isim_5.0_replicator_tut_gui_grasping_stage.jpg
    :align: center
    :alt: Example stage with a gripper and objects for grasping

Overview
---------

The extension is designed to automate the process of finding and evaluating potential grasp poses for a given gripper-object pair. At its core, the workflow revolves around several key components and stages:

1.  **Configuration**: Defining the specific gripper, the target object, and the parameters that govern how grasps are found and tested.
2.  **Grasp Pose Sampling**: Algorithms (for example, antipodal samplers) generate a set of candidate grasp poses around the target object. These poses represent potential ways the gripper might hold the object.
3.  **Grasp Execution Phases**: For each candidate grasp, a sequence of actions, termed "Grasp Phases" (for example, move to pre-grasp, close fingers, lift), is simulated. This allows for defining complex, multi-step grasping behaviors analogous to real-world robot actions.
4.  **Physics-Based Evaluation**: Each phase of the grasp is simulated in the physics engine. The success or failure of the grasp attempt, along with other metrics (like contact forces, object displacement), can be recorded. In its current state the extension saves the gripper state as result from which the grasps can be evaluated.
5.  **Data Logging and Management**: Successful grasps and their associated parameters are logged. The entire setup can be saved to and loaded from configuration files (YAML format), ensuring reproducibility and facilitating batch processing.

The ``GraspingManager`` class is the central Python API orchestrating these steps, while the UI provides an intuitive way to configure and run this pipeline.

UI Window Overview
------------------------------

The Grasping UI window provides the interface for setting up and running the grasping simulations workflows. It is organized into several sections, each addressing a specific part of the process. The general workflow involves configuring these sections, typically starting with the gripper and object, then defining the evaluation workflow and simulation parameters, and finally managing the overall configuration.

.. image:: /images/isim_5.0_replicator_tut_gui_grasping_ui_window.jpg
    :align: center
    :alt: Grasping UI window main interface

Gripper Section
###############

This section is dedicated to defining the properties and behavior of the gripper, which is fundamental for any grasp attempt.

.. image:: /images/isim_5.0_replicator_tut_gui_grasping_ui_gripper_joints.jpg
    :align: center
    :alt: Grasping UI: Gripper joints configuration

*   **Path**: Specify the USD path to the root prim of your gripper (for example, ``/World/Robot/gripper_base``).
*   **Joints**: After a gripper is selected, its articulated joints are listed. Here you can:

    *   **Include/Exclude**: Select the joints that are actively controlled during the grasp phases. These joints have to be drive joints.
    *   Set **pre-grasp positions**: Define the initial state for each joint, typically an open configuration, before the grasp sequence begins.
    *   Toggle visibility between all joints or of type drive (non-mimic) joints.

*   **Grasp Phases**: This powerful feature allows you to define a sequence of discrete actions that constitute a complete grasp attempt. This is analogous to defining a state machine or a sequence of motion primitives for the gripper.

    .. image:: /images/isim_5.0_replicator_tut_gui_grasping_ui_gripper_grasp_phases.jpg
        :align: center
        :alt: Grasping UI: Gripper grasp phases configuration

    For each phase (for example, "Open", "Close"), you specify:

    *   Target joint positions for the active gripper joints.
    *   Simulation step delta time (``dt``) for the physics steps within this phase.
    *   Number of simulation steps to execute for this phase.

    Phases can be reordered, deleted, or simulated individually for debugging. If pre-grasp joint positions adequately prepare the gripper (for example, fully open), an explicit "Open" phase might be unnecessary.

Object Section
##############

This section focuses on specifying the target object and configuring how potential grasp poses are generated for it.

.. image:: /images/isim_5.0_replicator_tut_gui_grasping_ui_object.jpg
    :align: center
    :alt: Grasping UI: Object and grasp pose sampler configuration

*   **Path**: The USD path to the target object prim (for example, ``/World/MyObject``).
*   **Grasp Pose Sampler**: This configures the algorithm used to find potential grasp poses. This tutorial primarily uses an **antipodal grasp sampler** (implemented in ``sampler_utils.py``). An antipodal grasp is typically stable for parallel-jaw grippers, involving two contact points on opposite sides of the object. Key parameters include:

    *   **Number of orientations per grasp axis**: How many rotational variations around the primary grasp axis to sample.
    *   **Gripper standoff distance**: The distance from the gripper's Tool Center Point (TCP) or fingertips to the object surface during the approach phase, crucial for avoiding premature collision.
    *   **Maximum gripper aperture**: The widest opening of the gripper jaws, filtering out grasps that are too wide for the object.
    *   **Alignment axes for the grasp**: Defines local gripper axes to align with object features or the grasp line.
    *   **Gripper approach direction**: The vector along which the gripper moves towards the object.
    *   **Lateral perturbation (sigma)**: Adds randomness to the grasp point location along the grasp axis, allowing for exploration around nominal contact points.
    *   **Random seed**: For ensuring reproducible sampling results.

*   **Grasp Poses**: Manages the set of candidate grasp poses generated by the sampler.

    *   Specify the desired number of candidate poses.
    *   Clear previously generated poses.
    *   Visualize the poses in the viewport (either in world or object-local frames) and cycle through them to inspect their placement.

    The following image shows example grasp poses generated by the antipodal sampler on various objects:

    .. image:: /images/isim_5.0_replicator_tut_viewport_grasping_poses.jpg
        :align: center
        :alt: Resulting grasp poses from the antipodal grasp sampler

*   **Trimesh**: Provides options for debug visualization of the object's triangle mesh, which is used internally by the sampler for geometric calculations and collision checks.

.. note::

    The `Measure Tool <https://docs.omniverse.nvidia.com/extensions/latest/ext_measure-tool.html>`_ can be useful for determining values like gripper aperture or standoff distance.

    .. image:: /images/isim_5.0_replicator_tut_viewport_grasping_measure_tool.jpg
        :align: center
        :alt: Using the Measure Tool for gripper and standoff distances

Workflow Section
################

The Workflow section is where you orchestrate the actual grasp evaluation process using the configurations defined in the Gripper and Object sections.

.. image:: /images/isim_5.0_replicator_tut_gui_grasping_ui_workflow.jpg
    :align: center
    :alt: Grasping UI: Workflow configuration (This image might be missing, using a placeholder name)

The system first saves the gripper's initial pose. Then, for each generated grasp pose selected for evaluation, it sequentially executes the defined grasp phases within the physics simulation. After all phases for a given pose are completed, the outcome (for example, success based on object stability, contact with target) and other relevant metrics are recorded.

*   **Number of Grasps Samples**: Specify how many of the generated grasp poses should be evaluated. Use -1 to evaluate all available poses.
*   **Output Path**: Define the directory and base file name for saving the evaluation results. The results are typically saved in a structured format like YAML, detailing each evaluated grasp and its outcome.
*   **Overwrite Results**: If enabled, existing result files at the output path will be overwritten. Otherwise, new files will be created (for example, with incremental numbering) to avoid data loss.
*   **Start Workflow**: Initiates the grasp evaluation process. The UI will often provide feedback on the progress.

Simulation Section
##################

This section allows you to fine-tune global parameters that affect how the physics simulation is run during the grasp evaluation.

.. image:: /images/isim_5.0_replicator_tut_gui_grasping_ui_simulation.jpg
    :align: center
    :alt: Grasping UI: Simulation settings

*   **Render each simulation step**: Control whether the viewport updates after each individual physics step within a grasp phase. Disabling this can speed up the evaluation process significantly for large datasets, with rendering potentially only occurring after each full grasp attempt or phase.
*   **Simulate using timeline**: Choose between advancing the simulation by stepping the main Isaac Sim timeline or by directly stepping the physics scene. Direct physics steps can offer more precise control for rapid evaluations, while timeline-based simulation might be closer to how a full robot application would run.
*   **Isolated physics scene**: Optionally specify a path to a **Physics Scene** prim. If provided, the grasping simulation can be run within this dedicated physics scene, preventing interference from other dynamic objects or physics settings in the main stage. This is useful for ensuring consistent and repeatable grasp evaluations.

Config Section
##############

The Config section provides the crucial functionality for saving your entire grasping setup to a YAML file and loading it back later. This is essential for reproducibility, sharing configurations, and running batch experiments.

.. image:: /images/isim_5.0_replicator_tut_gui_grasping_ui_config.jpg
    :align: center
    :alt: Grasping UI: Configuration management

*   **File Path**: Specify the path to the YAML configuration file for saving or loading.
*   **Config Includes**: Selectively choose which components of the setup are included in the save/load operation. This allows for modular configurations. Options typically include:

    *   Gripper Path
    *   Joint Pregrasp States
    *   Grasp Phases
    *   Object Path
    *   Sampler Parameters
    *   Generated Grasp Poses (if you wish to save a specific set of poses)

*   **Overwrite Existing File**: When saving, this option determines if an existing file at the specified path should be overwritten.
*   **Load/Save Buttons**: Execute the respective file operations.

This structured UI and configuration system offers detailed control and flexibility for generating diverse grasping datasets.

Configuration File Example
##########################

Below is a snippet illustrating the structure of a YAML configuration file. It can store settings for the gripper, object, sampler, and defined grasp phases. The specific content will depend on which components were selected for inclusion through the 'Config Includes' UI options.

.. raw:: html

    <details open>
    <summary>xarm_antipodal.yaml</summary>

.. literalinclude:: ../snippets/synthetic_data_generation/tutorial_replicator_grasping_sdg/xarm_antipodal.yaml
    :language: yaml
    :lines: 16-

.. raw:: html

    </details>

Code Example
------------

The following scripts demonstrates a complete workflow for generating a grasping dataset using the ``GraspingManager`` API. This script programmatically performs the steps configurable through the UI:

* opening a stage
* setting up the ``GraspingManager`` (potentially by loading a configuration file)
* generating grasp Poses
* evaluating these poses using physics simulation
* saving the results

This approach is highly suitable for batch processing or integration into larger robotics workflows. The script can be run directly from the :ref:`Script Editor <script-editor>` or as a :ref:`Standalone Application <standalone-application>`.

To run the standalone example from the terminal (on Windows, use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.replicator.grasping/grasping_workflow_sdg.py


.. tab-set::

    .. tab-item:: Script Editor

        .. raw:: html

            <details open>
            <summary>Grasping Synthetic Data Generation Workflow</summary>

        .. literalinclude:: ../snippets/synthetic_data_generation/tutorial_replicator_grasping_sdg/grasping_workflow_sdg_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Standalone Application

        .. raw:: html

            <details open>
            <summary>Grasping Synthetic Data Generation Workflow</summary>

        .. literalinclude:: ../../../source/standalone_examples/api/isaacsim.replicator.grasping/grasping_workflow_sdg.py
            :language: python
            :lines: 16-
            :end-before: # <start-grasping-workflow-sdg-test>

        .. raw:: html

            </details>








