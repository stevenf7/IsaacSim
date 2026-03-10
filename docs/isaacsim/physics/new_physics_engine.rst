..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. meta::
  :title: Physics Data Flow and Engine Integration
  :keywords: lang=en physics data flow USD Fabric tensors engine integration Isaac Sim


.. _physics_data_flow:

********************************************
Physics Data Flow and Engine Integration
********************************************

This page describes how physics data moves through |isaac-sim_short| and how to integrate a new physics engine. The first section summarizes the three data pathways (USD, Fabric, and Physics Tensors) and the unified API layer. The second section explains the steps to implement a new backend that plugs into these same pathways.


Physics Data Flow
=================

|isaac-sim_short| uses three data pathways to move physics data between user code, the active physics engine, and the rendering pipeline: USD, Fabric, and Physics Tensors. On top of these, ``isaacsim.core.experimental`` provides a unified API that abstracts backend differences and is the recommended way to interact with simulation data.

.. figure:: /images/isim_6.0_full_ref_external_data_flow.png
    :align: center
    :width: 800

    Physics data flow architecture in |isaac-sim_short|.


.. _data_flow_pathways:

Data Pathways Explained
-----------------------

**USD** is the authoring and persistence format. It stores scene structure, transforms, physics properties, and visual properties. Physics properties use USD Physics and engine-specific schemas. Use USD before and after play for scene authoring, initial configuration, and persisting state. It is not designed for per-frame bulk reads. For runtime performance use Fabric or Tensors.

**Fabric** is a GPU-accelerated runtime data store, populated from USD at load and updated by the active engine for each frame. It holds world transforms (for example, ``omni:fabric:worldMatrix``) and is the bridge between simulation and rendering. Use Fabric when you need high-performance read access to transforms during simulation.

**Physics Tensors** provide batch read/write access to engine state (articulations, rigid bodies, contacts) and are available only after play. Create a ``SimulationView`` and view objects (for example, ``ArticulationView``, ``RigidBodyView``) to exchange data in NumPy, PyTorch, or Warp. Use Tensors for control loops, RL policies, and high-throughput state exchange. Both |physx| and Newton expose a tensor API that conforms to the same view interface.

**Unified API (``isaacsim.core.experimental``):** The recommended approach is to use the prim wrappers (``XformPrim``, ``RigidPrim``, ``ArticulationPrim``), which abstract over USD, Fabric, and Tensors and auto-select the appropriate backend. When the simulation is running, operations route to the active engine's tensor API. Refer to the :doc:`Core API Overview <../python_scripting/core_api_overview>` for details on the Core Experimental API.


Per-Engine Data Pathways
------------------------

Both |physx| and Newton import USD at initialization, write transforms to Fabric each frame, and provide a Tensor API with the same view types. |physx| also supports a Fabric/USD change listener for runtime USD edits and extends the tensor API to deformable bodies. Newton's tensor API covers rigid bodies, articulations, and rigid contacts.


Choosing a Pathway
------------------

Choose:

* **USD** for authoring and persistence
* **Fabric** for runtime transforms (for example, for rendering)
* **Tensors** for batch state read/write (RL, control, contact forces) 

For engine-agnostic code the preference is to use **isaacsim.core.experimental**.


.. _implementing_physics_engine:

Implementing a Physics Engine
=============================

To integrate a new physics engine with |isaac-sim_short|, you must:

* plug into the same data flow
* parse USD at initialization 
* write body transforms to Fabric each frame 
* expose a Tensor API that matches the expected view interface

The runtime then drives your engine using the unified physics interface (``omni.physics.core``), making it available to ``SimulationManager``, ``isaacsim.core.experimental``, and the tensor API.

The ``isaacsim.physics.newton`` extension is the reference implementation.


Architecture Overview
----------------------

The integration connects your engine to the three data pathways described above. Five components are involved:

* **Simulation Function adapters** — How the runtime drives simulation steps that include, attach/detach a USD stage, run a step (``simulate``), fetch results, and expose step/contact callbacks and capability queries.
* **Stage Update Function adapters** — How the runtime handles stage and timeline events including, play, pause, reset, load physics from USD, and release resources.
* **Registration** — A ``Simulation`` object holds your Simulation Function and Stage Update Function adapters. You can register it with the physics interface under a name (for example ``"newton"``) so the ``SimulationManager`` can activate it.
* **Fabric synchronization** — For each frame, write your engine's body transforms into Fabric so that the renderer can display the scene.
* **Tensor API** — A ``SimulationView`` and view classes (for example, ``ArticulationView``, ``RigidBodyView``) that wrap your engine state and use the existing NumPy/PyTorch/Warp frontends so that your user code can read/write the state in bulk.

.. figure:: /images/isim_6.0_full_ref_external_engine_architecture.png
    :align: center
    :width: 800

    Engine integration architecture.


Integration Flow
----------------

**Startup:** The extension creates the engine stage and the Simulation Function and Stage Update Function adapters, builds a ``Simulation`` object from them, and registers it with ``get_physics_interface().register_simulation(simulation, "your_engine_name")``. Optionally it switches the active engine to the new one using ``SimulationManager``.

**When the user hits Play:** The runtime calls your Stage Update Function adapters (for example, ``on_attach``, ``force_load_physics_from_usd()``) to parse the USD stage and build simulation objects. 

  Each frame it calls ``simulate(elapsed_time, current_time)`` to advance the engine and then write updated transforms to Fabric so that rendering stays in sync. Any code that you have that uses ``SimulationView`` or ``ArticulationView`` talks to your tensor backend, which reads and writes your engine's buffers.

**Shutdown:** The extension unregisters the simulation and releases resources; if it had auto-switched, it switches back to the default engine.

For a complete example, refer to the ``isaacsim.physics.newton`` extension: 

* ``impl.simulation_functions`` and ``impl.stage_update_functions`` implement the two adapter interfaces
* ``impl.fabric`` handles Fabric writes 
* ``impl.tensors`` implements the view classes
* ``impl.register_simulation`` and ``impl.extension`` tie registration and lifecycle together


Engine Switching at Runtime
----------------------------

``SimulationManager.switch_physics_engine(name)`` activates the engine registered under that name:

* it deactivates the current engine (Stage Update Function adapters ``on_detach``)
* activates the new one (``on_attach``)
* invalidates existing simulation views
* triggers a fresh load from USD on the new engine. 

Only one engine is active at a time. To switch it you must change it before starting the simulation.
