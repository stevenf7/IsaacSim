..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_replicator_character:

===============================================
Actor Simulation and Synthetic Data Generation
===============================================

Detecting and tracking animated actors or agents like human characters and robots in diverse environments offers significant value across industries like retail, manufacturing, and logistics. It helps optimize layouts, improve safety, and enhance efficiency. However, collecting real-world data to train detection models is often costly and unscalable.

Synthetic data generation offers a flexible, scalable solution. The ``Omni.Metropolis.Pipeline`` (OMP), ``Isaacsim.Replicator.Agent`` (IRA), ``Isaacsim.Anim.Robot.Core`` (IAR) extensions together provide a way to set up human characters and robots in 3D environments and generate synthetic data.
This framework also provides control over actor behaviors, environments, and sensors, through a configuration file. It aims to provide a GPU-accelerated solution for training computer vision models and testing software-in-the-loop systems.

This framework simplifies simulation customization with features like:

* **Codeless Interaction**: Configurations are expressed in YAML file. No code is needed to get synthetic data.
* **Simplified Setup**: Included in Isaac Sim, it offers both GUI and scripting interfaces for interactive and headless workflows.
* **High-Fidelity Data**: Leverages Omniverse's SimReady assets, physics, and rendering to produce realistic imagery and accurate annotations essential for AI training.
* **Seamless Integration**: As part of Kit extensions, it works natively with ``omni.anim.behavior``, ``omni.anim.navigation``, and ``omni.replicator.core``.

Before enabling this extension, read :doc:`What Is Isaac Sim? </overview/overview>` to learn about |isaac-sim_short| and follow :doc:`Installation </installation/index>` to install |isaac-sim_short|.

.. image:: /images/isim_4.5_full_ext-isaacsim.replicator.agent-5.0.0_viewport_IRA_overview.png
    :width: 900
    :align: center
    :alt: characters and robots move around a warehouse 3D environment.

|

.. _actor_sim_enable_extensions:

Enable Extensions
----------------------------------
1. Follow the `Omniverse Extension Manager guide <https://docs.omniverse.nvidia.com/extensions/latest/ext_core/ext_extension-manager.html>`_ to enable the ``Omni.Metropolis.Pipeline``, ``Isaacsim.Anim.Robot.Core``, and ``Isaacsim.Replicator.Agent.Core & UI``.

    * The extensions fetch sample assets from Isaac Sim Assets during start. Refer to :doc:`Isaac Sim Assets </assets/usd_assets_overview>` if you encounter issues for loading assets.
    * If loading the UI appears to be hanging, try starting Isaac Sim with the flag ``--/persistent/isaac/asset_root/timeout=1.0``.

2. The UI panel is accessible by **Tools > Action and Event Data Generation > Actor SDG** and it opens on the right side of the screen.

.. note::
    * To have the extension auto-loaded on startup, check the **autoload** checkbox in the extension manager.
    * Because of extension dependencies, a restart of the |isaac-sim_short| app might be required.

.. tip::
    If you encounter unexpected errors, try launching |isaac-sim_short| with the ``--reset-user`` flag to clear previous user settings.

    .. code-block:: bash

        ./isaac-sim.sh --reset-user

.. _actor_sim_getting_started:

Getting Started in the UI
-------------------------
For first-time users, it is recommended that you use the UI. Refer to :ref:`Running from script <actor_sim_running_from_script>` section for running with Python script in IsaacSim headless mode.

1. Follow the :ref:`Enable Extensions <actor_sim_getting_started>` and open the UI panel.

2. The default minimal config is loaded by default. You can also load a separate config file using the folder browser icon.

    * All the sample config files are in ``[Isaac Sim App Path]/extscache/isaacsim.replicator.agent.core-[current-version]/data/sample_configs/``.
    * The minimal config file does not have actors and cameras. For a more comprehensive example, use ``warehouse.yaml`` in the above folder. This example can take up more loading time.

.. image:: /images/isim_6.0_full_tut_external_actor_sim_getting_started_config_panel.png
    :width: 600
    :align: center
    :alt: Load a config file.

|

3. [Optional] Modify the configuration file to your needs.

    * Use Save or Save As icon to save the changes in UI to config file.
    * Use Reload icon to reset changes in UI and load the original config file again.

4. Click the **Set Up Simulation** button from the top of the UI and it will start loading simulation assets (scene, cameras, actors) according to the UI.

    * The scene requires a NavMesh to spawn assets and control them correctly. The scenes in the example config has NavMesh set up in advance. If you are using a external scene, refer to :doc:`Navigation Mesh<extensions:ext_navigation-mesh>` for NavMesh set up.
    * You can also go to **Window > Navigation > NavMesh** and turn off **Auto-Bake** in the NavMesh settings. Turning it off can increase the performance.

    .. note::
        Clicking **Set Up Simulation** always fully reloads the scene from the current configuration. This includes reopening the base environment USD and re-creating all actors (characters and robots), sensors, and prop layers from scratch. Any manual edits made to the stage after a previous setup will be lost. If you want to iterate on the configuration, make your changes in the UI or config file first, then click **Set Up Simulation** to apply them.

5. Click the **Start Data Generation** button from the top of the UI and the simulation and data generation will start. It will run for the duration (in seconds) specified in the **Simulation Duration** in **Actor SDG Setup** panel.

6. When data generation finishes, the output data can be found from the **Output Directory** according to the output directory in  **Replicator** panel.

    * By default, it is in the User folder for Windows and the home folder for Linux.


.. _actor_sim_running_from_script:

Running from Script
--------------------

For large-scale data generation, it can be more efficient to launch it from script. IRA provides an automatic script (``actor_sdg.py``) to run offline data generation.

To run from script, open a terminal from where Isaac Sim is installed and run the following commands:

* For Linux:
   ``./python.sh tools/actor_sdg/actor_sdg.py -c [config file path]``

* For Windows:
   ``.\python.bat tools\actor_sdg\actor_sdg.py -c [config file path]``

.. note::
    * ``[config file path]`` is the path to the IRA configuration file.

    * You must use the ``python.sh`` or ``python.bat`` bundled with Isaac Sim to run the script.

    * An example config file is also provided in the ``/tools/actor_sdg`` folder. For a sample Linux run, execute: ``./python.sh tools/actor_sdg/actor_sdg.py -c tools/actor_sdg/sample_config.yaml``

API Usage
--------------------------
This extension also exposes a Python API which you can use to set up simulations and generate data from your own script.
Ensure that ``isaacsim.replicator.agent.core`` is enabled, and use the API as in the following example.

.. note:: The snippet below uses the minimal config bundled with the extension (``data/sample_configs/minimal.yaml``).

.. literalinclude:: ../snippets/action_and_event_data_generation/tutorial_replicator_agent.py
    :language: python
    :lines: 20-


.. _configuration_file:

Configuration File
------------------

The configuration file is the central place to define your simulation. It controls everything from the environment and characters to the sensors and data output. The file uses the YAML format.

The configuration file is organized into these top-level sections:

-   ``environment``: Defines the simulation environment and assets.
-   ``character``: Configures human characters.
-   ``robot``: Configures robots.
-   ``sensor``: Configures RTX sensors.
-   ``replicator``: Configures data generation and output.

For detailed configuration instructions, parameter lists, and examples, refer to the following document:

.. toctree::
    :maxdepth: 1

    ./ext_replicator-agent/ext_isaacsim_replicator_agent_configuration.rst

Migrating from IRA 0.x.x
--------------------------

If you are upgrading from IRA 0.x.x (shipped with Isaac Sim 5.1 and earlier),
be aware that IRA 1.x.x (Isaac Sim 6.0+) is a complete architectural redesign.
All core capabilities, such as the following, are carried forward:

- environment loading
- character and robot spawning
- sensor placement
- synthetic data generation

However, the configuration schema, behavior system, and Python API have all changed.
Existing 0.x config files and scripts will not work without modification.

Key reasons for the redesign:

-   **Simpler workflow** -- The multi-step process of generating, saving, and
    loading external command files is gone. Behaviors are now defined inline in
    the YAML config, reducing setup to two clicks in the UI.
-   **Greater flexibility** -- Named groups let you define multiple character,
    robot, and sensor populations with independent settings in a single config.
    Multiple data writers can run concurrently with per-writer timing and sensor
    selection.
-   **Stronger validation** -- Pydantic v2 models validate configs on load and
    surface clear error messages, catching mistakes before the simulation starts.
-   **USD-native architecture** -- Actor configurations are persisted as USD
    schemas and prims, making them inspectable and editable directly in the
    stage.

The migration guide below walks through every breaking change with before and after
examples, and a step-by-step checklist:

.. toctree::
    :maxdepth: 1

    ./ext_replicator-agent/ext_isaacsim_replicator_agent_migration_guide.rst

For editing the configuration files through UI or code, refer to the :ref:`Configuration Editor API <ira_configuration_editor_api>`:

.. toctree::
    :maxdepth: 1

    ./ext_replicator-agent/ext_isaacsim_replicator_agent_configuration_editor.rst

For a practical walkthrough of using the CustomWriter to stream RTSP video from IRA cameras, review the following example:

.. toctree::
    :maxdepth: 1

    ./ext_replicator-agent/ext_isaacsim_replicator_agent_custom_writer_example.rst

Actor Behaviors
-------------------

Actor behaviors are achieved by OMP, IRA, and IAR together.

.. image:: /images/isim_6.0_full_tut_external_actor_sim_actor_behavior_ext_overview.png
    :width: 900
    :align: center
    :alt: Extension relationship.



Actors perform a "routine-trigger" behavior loop at play. This pattern is configurable by the behaviors and triggers assigned to the actor.

.. image:: /images/isim_6.0_full_tut_external_actor_sim_actor_behavior_overview.png
    :width: 900
    :align: center
    :alt: actor, behavior, trigger

|

The Routine Trigger Loop
^^^^^^^^^^^^^^^^^^^^^^^^^^

When no actor triggers are activated, actors perform routine loop by repeatedly pick behaviors under routines to perform by their probability weights, using the ``actor global seed``.

When any trigger is activated, the actor will pause routine and start performing the behaviors under each active trigger. Running triggers will be paused and pushed to queue if a trigger with higher priority happens (triggers with lower priority will be skipped).
The trigger will be marked complete when its behaviors are all finished. Then the first trigger in queue will resume running.
After all active triggers complete, the actors will fallback to their routine.

.. image:: /images/isim_6.0_full_tut_external_actor_sim_actor_behavior_flowchart.png
    :width: 900
    :align: center
    :alt: routine-trigger flowchart.

|

Configure Behaviors
^^^^^^^^^^^^^^^^^^^^^^^^^^

After the actors are loaded into scene by config file, the configurations are embedded in the USD API schemas and USD Prims. Each actor is represented by MetroAgentAPI schema and its derived type.
For a human character, it is the ``IRACharacterAPI`` attached on the SkelRoot prim. For an animated robot, it is the ``AnimRobotAPI`` attached on the root prim of the robot payload.
Each behavior and trigger becomes an individual USD Prim that the actor USD API can have reference to, each actor trigger prim can also have reference to a list of behaviors.

The actor USD API schema defines basic information of the actor:

- name
- group
- seed
- a routine reference slot and a trigger reference slot

At play, the name, group, and seed will be combined and hashed into a single seed as ``actor global seed``. This seed will be used for all the "randomness" of the actor, including random routine picking for the actor itself and the picking within each behavior such as picking a speed from speed range.
This also means the same ``actor global seed`` will display same result if other settings and the environment don't change.

Each type of actor behavior is represented by a USD Prim type. It defines the configuration of the behavior:

- weight
- repeat
- behavior 

For human characters, the behavior prim types follows the ``CharacterXXXBehavior`` naming pattern. For animated robots, they are ``RobotXXXBehavior``.

Each actor trigger is also a USD Prim. It defines the trigger priority and has a reference of behavior list to be executed sequentially when this trigger activates.
Human characters and anim robots share the same trigger types that's defined in OMP with naming ``MetroXXXTrigger``.

In addition, the actors leverage ``omni.behavior.behavior`` (Human characters) and ``isaacsim.anim.robot.core`` (Animated robots) as their animation implementation.
For more information about them, refer to the following documents:

.. toctree::
    :maxdepth: 1

    ./ext_replicator-agent/ext_isaacsim_anim_robot.rst

Behavior Tree (Experimental)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. warning::
    Behavior tree character support is **experimental** and may change in future releases.

In addition to the routine-trigger behavior system described above, IRA 1.3.0 introduces support for driving character behavior through **behavior trees**. Behavior trees are authored with the ``omni.behavior.tree.core`` and ``omni.anim.behavior.tree`` extensions.

.. TODO: Add links to omni.behavior.tree.core and omni.anim.behavior.tree extension docs when available.

**What is a Behavior Tree?**

A behavior tree is a hierarchical model for decision-making. It is composed of different node types that work together:

-   **Action nodes** are the leaf-level nodes where characters perform concrete actions (for example, ``MoveTo``, ``Wait``).
-   **Composite nodes** control logic and execution flow. For example, a ``Sequence`` node runs its children in order, while a ``Selector`` node tries children until one succeeds.
-   **Modifiers and Decorators** wrap other nodes to alter their behavior, such as ``Repeat`` (loop a subtree) or ``RandomNavMeshPoint`` (supply a random destination).

By combining these node types, you can compose arbitrarily complex behaviors. Behaviors from simple wander loops to multi-step conditional sequences, that are all within a single tree definition, without writing code. Compared to the IRA routine system, which picks behaviors randomly by weight, a behavior tree gives full deterministic control over ordering, branching, and looping.

**Relationship to Routines and Triggers**

.. note::
    **Triggers are not currently supported** for behavior-tree character groups. Any reactive or conditional logic must be authored as nodes inside the behavior tree itself.

Behavior tree mode is an alternative to the routine-trigger system. Each character group in the configuration uses **one or the other**: a group either defines ``routines`` and ``triggers`` (IRA-style) or references a ``behavior_tree``. However, a single configuration file can contain multiple groups, so IRA-style and behavior-tree groups can coexist side by side.

**Workflow**

1.  Author a behavior tree using ``omni.behavior.tree.ui`` and save it as a JSON file. The tree references node libraries ``omni.behavior.tree.core`` and ``omni.anim.behavior.tree`` for its action, composite, and modifier nodes. Refer to the `Behavior Tree's User Guide <https://docs.omniverse.nvidia.com/kit/docs/behavior-tree/latest/user-guide.html>`_ on how to author a behavior tree.
2.  In the IRA configuration YAML, create a character group with a ``behavior_tree`` field pointing to the JSON file. Optionally provide an ``overrides`` field to assign node parameters for different character groups without modifying the tree file.
3.  Run the simulation as usual. The behavior-tree characters share the same spawning, NavMesh, and data-generation pipeline as IRA characters.

Some sample config files with behavior tree character groups are provided in the ``[Isaac Sim Assets Path]/Samples/BehaviorTree`` folder as well as bundled in the ``data/sample_configs`` folder in the ``isaacsim.replicator.agent.core`` extension. For configuration details, parameter reference, and YAML examples, refer to :ref:`Behavior Tree Character Group (Experimental) <ira_bt_character_group>` in the Configuration File Guide.

.. warning::
    Behavior tree characters set up by IRA still have the ``IRACharacterAPI`` schema applied, but this is only used for data-generation identification (name, group, semantic labels, etc.). The character's behavior is entirely controlled by the behavior tree through ``omni.behavior.tree.core`` (OBT). IRA-level settings such as ``seed`` have no effect on behavior-tree characters.

Terminology
-------------
.. dropdown:: Isaacsim.Replicator.Agent.Core

    The core extension that manages the simulation state. It contains the essential API and modules for setting up the simulation and capturing the synthetic data. Its modules can be called independently.

.. dropdown:: Isaacsim.Replicator.Agent.UI

    The UI extension for IRA. When this extension loads, the core extension is loaded automatically. This extension contains the UI components for easy interaction with the extension.

.. dropdown:: Configuration File

    A ``.yaml`` file that contains configuration data that defines the key components of a simulation, including the randomization seed, duration of the simulation, number of the actors, and output format. To use the extension, you must load a configuration file or use the UI to generate a YAML file first.

.. dropdown:: Actor

    Actors are controlled by the respective controllers (``omni.behavior.tree`` and ``isaacsim.anim.robot``) and perform actions in the simulation. The extension supports human characters and robots (Nova Carter, iw.hub) as actors. The terms "actor" and "agent" are used interchangeably in this documentation.

.. dropdown:: Seed

    Randomization seed. Given the same seed, the extension can generate the same randomized result for camera and agent location and agent behaviors. With the same seed and the same sequence of operations, the same data is guaranteed to be generated.

.. dropdown:: Replicator (Omni.Replicator.Core)

    The data capturing extension that our extension is based on. More information about the Replicator extension can be found in :doc:`Replicator Official Documentation</replicator_tutorials/index>`.

.. dropdown:: Behavior Tree

    A hierarchical data model for organizing decision-making and actions. A behavior tree is defined as a JSON file and referenced from the IRA configuration. It provides an alternative to the routine-trigger system for controlling character behavior. Refer to the `Behavior Tree documentation <https://docs.omniverse.nvidia.com/kit/docs/behavior-tree/latest/index.html>`_ for more information.
