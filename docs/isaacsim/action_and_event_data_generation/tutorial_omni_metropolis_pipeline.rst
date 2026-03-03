..
   Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


====================================================================================
Omni Metropolis Pipeline
====================================================================================

The ``omni.metropolis.pipeline`` extension provides a shared configuration, trigger, and agent layer used by Action and Event Data Generation extensions.

It supplies the **ConfigurationManager**, a singleton that loads YAML configuration files, parses sections per extension, and runs async setup so extensions can configure the application from a single config file.
It also supplies the **TriggersManager** and built-in trigger types so that events (such as those from :ref:`Physical Space Event Generation <isaac_sim_app_tutorial_replicator_incident>`) can be started at a specific time, on a carb event, or on a physics collision.
It also supplies the **AgentManager** and base agent interface so that agents (such as those from :ref:`Actor Simulation and Synthetic Data Generation <isaac_sim_app_tutorial_replicator_character>`) can be created and managed.

Overview
--------

* **Configuration** – YAML-driven application setup

  * **ConfigurationManager** – Singleton that loads a config file and dispatches sections to registered extensions. Extensions register a section parser and async setup function that are used when the config file is loaded and the simulation is set up.

* **Triggers** – event objects that run callbacks when they fire

  * **TriggersManager** – Singleton that creates and manages trigger instances from a dictionary description. Use it to create triggers in script and pass them into incident (fire, topple, spill) and other event APIs.
  * **Trigger types** – Time-based, carb-event-based, and collision-based triggers are registered by the extension at startup. Each trigger can have callbacks added using ``add_callback``; when the trigger fires, all callbacks are invoked.

* **Agents** – runtime representations of entities that can perform routines and respond to triggers

  * **AgentManager** – Singleton that creates and manages agent instances from a dictionary description. Use it to create agents in script and pass them into agent APIs.
  * **Base agent interface** – The base agent interface is a USD Prim that defines the agent's behavior and trigger. It is used to create and manage agents.


Configuration
-------------

The **ConfigurationManager** loads a YAML config file and routes sections to extensions that have registered a parser and setup function. The config file currently supports the ``isaacsim.replicator.agent`` extension. Refer to the :ref:`Configuration File Guide <ira_configuration_file>` for more formatting information.

Using ConfigurationManager in Script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Access the singleton using ``ConfigurationManager.get_instance()`` or use the module-level functions from ``omni.metropolis.pipeline.configuration``. Register your extension's section before loading a config file; then call ``load_config_file(path)`` and ``await setup_simulation()``.

**Registration**

* **register_config_section(extension_name, section_header, section_name, section_parser, section_setup)** – Register a config section. ``section_header`` is the YAML top-level key (for example, ``"omni.metropolis.pipeline"`` or ``"isaacsim.replicator.agent.core"``). ``section_name`` is the key under the orchestrator header (for example, ``"agent"``). ``section_parser`` is a callable that accepts the raw dict for that section and returns parsed data. ``section_setup`` is an async callable that receives the parsed payload and runs when ``setup_simulation()`` is called.
* **is_section_registered(extension_name)** – Return whether that extension has registered a section.
* **unregister_config_section(extension_name)** – Remove the registration.

**Loading and access**

* **load_config_file(file_path)** – Load and parse the YAML file. Returns ``True`` on success. Use ``get_load_error_message()`` if it returns ``False``.
* **get_config(extension_name)** – Return the parsed configuration for that extension, or ``None`` if not present or not loaded.
* **get_config_file_path()** – Return the path of the currently loaded config file, or ``None``.

**Setup**

* **setup_simulation()** – Async. Run each registered extension's setup function with its parsed config. Returns ``True`` if all succeeded. Use ``get_setup_error_message()`` on failure.

Example Usage
~~~~~~~~~~~~~

.. code-block:: python

    import asyncio
    from pathlib import Path
    from omni.metropolis.pipeline.configuration import (
        get_config,
        get_load_error_message,
        get_setup_error_message,
        load_config_file,
        register_config_section,
        setup_simulation,
    )

    def parse_my_section(raw: dict):
        # Parser receives {section_header: section_data}. Return any structure your setup needs.
        return next(iter(raw.values()), {})

    async def setup_my_section(parsed):
        # Run async setup using parsed config (for example, create prims, load assets).
        pass

    # Register before loading. Use section_header and section_name that match your YAML.
    register_config_section(
        extension_name="my.extension.name",
        section_header="my.extension.name.core",
        section_name="my_section",
        section_parser=parse_my_section,
        section_setup=setup_my_section,
    )

    if load_config_file(Path("/path/to/config.yaml")):
        if asyncio.run(setup_simulation()):
            config = get_config("my.extension.name")
            # Use config as needed.
        else:
            print(get_setup_error_message())
    else:
        print(get_load_error_message())


Triggers
--------

Using TriggersManager in Script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Get the manager singleton and create triggers from a dictionary. For a complete script example that creates a time trigger, adds a callback, and passes the trigger into IRI event managers (fire, topple, spill), refer to :ref:`Physical Space Event Generation <isaac_sim_app_tutorial_replicator_incident>` and the :ref:`Event Configuration in IRI Script <iri_conifg_script>` and :ref:`Triggers <iri_trigger_section>` sections there.

**Prerequisites**

* Enable ``isaacsim.replicator.incident.core`` when using triggers with IRI events.
* The ``omni.metropolis.pipeline`` extension is loaded automatically when using the Action and Event Data Generation application.

Trigger Types
~~~~~~~~~~~~~

The extension registers these trigger types. Use the ``type`` field in the trigger dictionary and the corresponding parameters. For YAML and script examples of each trigger type with IRI events, refer to :ref:`Triggers <iri_trigger_section>` in the Physical Space Event Generation tutorial.

**time**

Fires when the simulation timeline reaches the given time (in seconds). Dictionary shape: ``{"trigger": {"type": "time", "time": <seconds>}}``.

**carb_event**

Fires when the named carb event is dispatched. Optional payload is available on the trigger after firing. Dictionary shape: ``{"trigger": {"type": "carb_event", "event_name": "<event_name>"}}``.

**collision**

Fires on physics trigger enter/exit for a collider prim. The collider must have CollisionAPI, TriggerAPI, and RigidbodyAPI. Optionally filter by other collider names using the ``metro:collider:name`` attribute. Parameters: ``collider_prim_path``, ``trigger_enter``, ``trigger_exit``, ``other_collider_names``.


Trigger API Summary
~~~~~~~~~~~~~~~~~~~

* **TriggersManager.get_instance()** – Return the singleton TriggersManager.
* **create_trigger_by_dict(dict_data)** – Build a trigger from ``{"trigger": {"type": "...", ...}}``. Returns a trigger instance or ``None`` if no registered type matches.
* **TriggerBase.add_callback(callback_fn)** – Add a callable that takes the trigger instance as an argument; it is invoked when the trigger fires.
* **TriggerBase.destroy()** – Unsubscribe from timeline/events and clear callbacks. Call when the trigger is no longer needed.


Example Usage
~~~~~~~~~~~~~

.. code-block:: python

    import carb
    from omni.metropolis.pipeline.triggers import TriggersManager

    def callback(trigger):
        carb.log_info("Trigger fired!")

    # Register a callback on a time trigger that fires at 1 second
    trigger_manager = TriggersManager.get_instance()
    trigger = trigger_manager.create_trigger_by_dict({"trigger": {"type": "time", "time": 1.0}})
    trigger.add_callback(callback)


Agents
------

Using AgentManager in Script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For creating and configuring agents in the Action and Event Data Generation application (YAML, UI), refer to :ref:`Actor Simulation and Synthetic Data Generation <isaac_sim_app_tutorial_replicator_character>`.

Example Usage
~~~~~~~~~~~~~

The following pattern registers a custom agent class and creates a prim with the agent's API. When the timeline plays, AgentsManager discovers the prim and instantiates the agent; when the timeline stops, runtime instances are cleared.

.. code-block:: python

    from typing import ClassVar
    from pxr import Usd, UsdPhysics
    import carb
    import omni.usd
    import omni.timeline
    from omni.metropolis.pipeline.agent import Agent, AgentsManager

    class MyAgent(Agent):
        AGENT_API: ClassVar[Usd.APISchemaBase] = UsdPhysics.RigidBodyAPI

        def get_world_position(self):
            return carb.Float3(0, 0, 0)

        def get_world_rotation(self):
            return carb.Float4(0, 0, 0, 1)

        def get_speed(self):
            return 0.0

        def get_facing_direction(self):
            return carb.Float3(1, 0, 0)

        def get_current_task_name(self):
            return None

        def on_update(self, delta_time: float):
            pass  # Custom behavior each frame

    # Create a prim with the agent API so the manager can discover it
    stage = omni.usd.get_context().get_stage()
    stage.DefinePrim("/World", "Xform")
    prim = stage.DefinePrim("/World/MyAgent", "Xform")
    UsdPhysics.RigidBodyAPI.Apply(prim)

    # Register the agent class and play to collect runtime instances
    manager = AgentsManager.get_instance()
    manager.register_agent_class(MyAgent)

    timeline = omni.timeline.get_timeline_interface()
    timeline.play()
    # After play, manager.get_runtime_agent_instances() will contain MyAgent instances
    # for each prim that has RigidBodyAPI. Call timeline.stop() to clear them.
