..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _USD Glossary of Terms & Concepts:  https://graphics.pixar.com/usd/release/glossary.html
.. _USD Stage: https://graphics.pixar.com/usd/release/glossary.html#usdglossary-stage



.. _isaac_sim_glossary:

========================
Glossary
========================

This section provides an explanation of the terms used throughout |isaac-sim| and replicates several of the terms defined in the Omniverse Glossary.

.. contents:: :local:

Omniverse
========================


Application
^^^^^^^^^^^^^^^^^^^^^^^

|dev_app_description|

Apps
^^^^^^^^^^^^^^^^^

|dev_app_description|


Connectors
^^^^^^^^^^^^^^^^^
|dev_connector_description|


.. _isaac_sim_glossary_nucleus:

Omniverse Nucleus
^^^^^^^^^^^^^^^^^^^^^^^

Omniverse Nucleus offers a set of fundamental services that allow a variety of client applications, renderers, and microservices to share and modify representations of virtual worlds.

Nucleus operates under a publish/subscribe model. Subject to access controls, Omniverse clients can publish modifications to digital assets and virtual worlds to the Nucleus Database (DB) or subscribe to their changes. Changes are transmitted in real-time between connected applications. Digital assets can include geometry, lights, materials, textures and other data that describe virtual worlds and their evolution through time.

This allows a variety of Omniverse-enabled client applications ( Apps, Connectors, and others) to share and modify authoritative representations of virtual worlds.

- See :doc:`Nucleus overview <nucleus:overview/overview>` for a more in-depth look at Nucleus's data model, architecture, and distribution platforms.

.. _isaac_sim_glossary_nucleus_cache:

Hub Workstation Cache
^^^^^^^^^^^^^^^^^^^^^^^


Hub Workstation Cache is a service that helps speed up USD workflows on your local workstation. This is a stand-alone service that runs on your local workstation and benefits Kit-based applications or Client Library tools.

Hub Workstation Cache has been performance optimized and supports storage-derived data from newer versions of Kit-based applications.

- See :doc:`Hub Workstation Cache overview <utilities:cache/hub-workstation>` for more details.
- See the :ref:`isaac_sim_app_install_workstation` for how to install


.. _isaac_sim_glossary_live_sync:

Live Sync
^^^^^^^^^^^^^^^^^^^^^^^

Live Sync mode enables real-time “live” editing of shared files on a Nucleus Server. The Live Sync button is on the top-right corner of the Workspace.

.. _isaac_sim_glossary_kit:

Omniverse Kit
^^^^^^^^^^^^^^^^^^^^^^^

NVIDIA Omniverse™ Kit is a toolkit for building native Omniverse applications and microservices. It is built on a base framework known as Carbonite that provides a wide variety of functionality through a set of light-weight plugins. Carbonite plugins are all authored with C interfaces for persistent ABI compatibility. A Python interpreter is provided for scripting and customization.

NVIDIA Omniverse™ Kit exposes much of its functionality through Python bindings. This provides an API that can be used to write new extensions to Omniverse Kit or new experiences for Omniverse.

- For a more in-depth look at developing in Kit, see the :doc:`Kit Programming Manual <kit:guide/kit_overview>`.

.. _isaac_sim_glossary_launcher:

Omniverse Launcher
^^^^^^^^^^^^^^^^^^^^^^^

The NVIDIA Omniverse Launcher is your first step into the Omniverse. It provides immediate access to all the apps, connectors and other downloads within the Omniverse.

- See the :doc:`Launcher overview <launcher:index>` for more details.

.. _isaac_sim_glossary_create:

Omniverse USD Composer
^^^^^^^^^^^^^^^^^^^^^^^

NVIDIA Omniverse™ USD Composer was an Omniverse app for world-building that allows users to assemble, light, simulate and render large scale scenes. It is built using NVIDIA Omniverse™ Kit. The Scene Description and in-memory model is based on Pixar’s USD. |usd_composer| takes advantage of the advanced workflows of USD like Layers, Variants, Instancing and much more.

.. _isaac_sim_glossary_carb:

Carbonite (carb)
^^^^^^^^^^^^^^^^^^^^^^^

The Carbonite SDK provides the core functionality of all Omniverse apps. This is a C++ based SDK with Python bindings that provides features such as plugin management, input handling, file access, asset loading and management, thread and task management, and much more.

.. - See the :doc:`Carbonite Overview <carbonite:index>` docs for additional usage information.


.. _isaac_sim_glossary_raytracing:

|real_time_render| mode
^^^^^^^^^^^^^^^^^^^^^^^^^

High quality real-time rendering mode.

.. - See :doc:`RTX Real-Time mode<materials-and-rendering:rtx-renderer_rt>` for more details.

.. _isaac_sim_glossary_pathtracing:

|interactive_render| mode
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The highest quality, physically accurate rendering mode.

.. - See :doc:`RTX Interactive (Path Tracing) mode<materials-and-rendering:rtx-renderer_pt>` for more details.

.. _isaac_sim_glossary_extensions:

Extensions
^^^^^^^^^^^^^^^^^^^^^^^

Extensions are plug-ins to Omniverse Kit that extend its capabilities. They are offered with complete source code to help developers easily create, add, and modify the tools and workflows they need to be productive. Extensions are the core building blocks of Omniverse Kit based applications.

- See :doc:`Extension Manager <extensions:ext_core/ext_extension-manager>` for more details.

.. _isaac_sim_glossary_connectors:

Omniverse Connect
^^^^^^^^^^^^^^^^^^^^^^^
Connectors are extensions and additional software layers on top of the open-source USD distribution that allow DCC tools and compute services to communicate easily with each other through the Omniverse Nucleus DB. Those extensions and additions are collectively known as NVIDIA Omniverse™ Connect.

.. - See :doc:`Omniverse Connect <connect:overview>` for more details.

.. _isaac_sim_glossary_usd:

USD
=======================


USD
^^^^^^^^^^^^^^^^^^^^^^^

Universal Scene Description (USD) is an easily extensible, open-source 3D scene description file format developed by Pixar for content creation and interchange among different tools. As a result of its power and versatility, it’s being widely adopted, not only in the visual effects community, but also in architecture, design, robotics, manufacturing, and other disciplines.

- For a more in-depth look at USD in Omniverse, see NVIDIA's USD primer `What is USD? <https://developer.nvidia.com/usd/>`_.
- See the `USD API <https://graphics.pixar.com/usd/release/index.html>`_ docs for more details.
- See the `USD Glossary of Terms & Concepts`_ for more details.
- See `NVIDIA's USD tutorials <https://developer.nvidia.com/usd/tutorials>`_

.. _isaac_sim_glossary_mdl:

MDL
^^^^^^^^^^^^^^^^^^^^^^^

Material Definition Language (MDL) is a NVIDIA-developed USD schema that represents material assignments and specifies material parameters.

.. - See :doc:`MDL Overview<materials-and-rendering:materials>` for more details.

.. _isaac_sim_glossary_stage:

Stage
^^^^^^^^^^^^^^^^^^^^^^^

The Omniverse Stage window allows you to see all the assets in your current USD Scene. The `USD Stage`_ is the USD abstraction for a scenegraph derived from a root USD file, and all of the referenced/layered files it composes. Listed in a hierarchical (parent/child) order the Stage offers convenient access and is typically used to navigate large scenes.

- See the :doc:`Stage <extensions:ext_core/ext_stage>` docs for more details.
- See the `USD Glossary of Terms & Concepts`_ for more details.

.. _isaac_sim_glossary_prim:



Prim
^^^^^^^^^^^^^^^^^^^^^^^

A `Prim <https://graphics.pixar.com/usd/release/glossary.html#usdglossary-prim>`_ is the primary container object in USD: prims can contain (and order) other prims, creating a “namespace hierarchy” on a Stage,
and prims can also contain (and order) properties that hold meaningful data. Prims, along with their associated, computed indices, are
the only persistent scenegraph objects that a Stage retains in memory, and the API for interacting with prims is provided by the UsdPrim class.

- See the `USD Glossary of Terms & Concepts`_ for more details.



Mesh
^^^^^^^^^^^^^^^^^^^^^^^

A mesh is a subdividable primitive that consists of points, edges, and faces that define its shape. In USD, a mesh is encoded in a `UseGeomMesh <https://graphics.pixar.com/usd/release/api/class_usd_geom_mesh.html>`__ class.

Shape
^^^^^^^^^^^^^^^^^^^^^^^

A Shape is a geometric primitive that maps to one of USD's five "intrinsic" ``UsdGeomGprim`` classes:

    - `UsdGeomCapsule <https://graphics.pixar.com/usd/release/api/class_usd_geom_capsule.html>`__
    - `UsdGeomCone <https://graphics.pixar.com/usd/release/api/class_usd_geom_cone.html>`__
    - `UsdGeomCube <https://graphics.pixar.com/usd/release/api/class_usd_geom_cube.html>`__
    - `UsdGeomCylinder <https://graphics.pixar.com/usd/release/api/class_usd_geom_cylinder.html>`__
    - `UsdGeomSphere <https://graphics.pixar.com/usd/release/api/class_usd_geom_sphere.html>`__

Shapes are not :term:`meshes<Mesh>`, in that they are not defined by a collection of points, edges, and faces. Instead, they are defined by their shape and volume.

Pixar describes their use cases for these prims in their `UsdGeomGprim schema documentation <https://graphics.pixar.com/usd/release/api/usd_geom_page_front.html>`__.



Reference vs Payload vs Instance
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. figure:: /images/ReferencePayloadInstance.png
    :align: center

Everything in USD is a primitive (prim) with attributes.  Some of these primitives are defined in your current layer (the active stage), while others are defined in other layers (other USD files).


A primitive that is included from some other layer is a **Reference** to that prim, and are indicated by the **orange arrow** on the associated Xform icon in the context tree of Isaac Sim. References are designed to be lightweight, and carry with them an implicit assumption that the child prims of a reference will not be modified.


If the contents of a reference need to be modified during simulation, then it must be converted into a **Payload**. A payload is indicated by the **blue arrow** on the associated Xform in the context tree of Isaac Sim. Payloads are references that have all of their data actively loaded by the sim so that it can be modified at runtime.


**Instances** are indicated by a **blue "I"**, and can be either references or payloads. They carry additional assumptions about the structure of the asset for more efficient vectorization (scaled up).


For example, suppose you want to collect synthetic data with a robot.  If you aren't going to modify the structure of the robot, it can exist as a reference on the stage (the asset is defined in some other file). If, during data collection, you want to be able to swap the robot out for a different one, those meshes need to be held in active memory. This means that the asset first needs to be converted from a reference to a payload.  If you wanted to collect data with a 1000 robots at once, and they are all the same, you might use instantiable references. Whereas, if you wanted to collect data with a 1000 randomly sampled robots (different arms with the same number of joints for example), you would use instance payloads.

Y-Up / Z-Up
^^^^^^^^^^^^^^^^^^^^^^^

The axis of orientation of a given scene/prim. Y-Up refers to the Positive Y Axis is pointing up. Z-Up refers to the Positive Z Axis is pointing up. This orientation setting is generally set by the application of the scene/prims origination.



Layer
^^^^^^^^^^^^^^^^^^^^^^^

A component of the collaborative nature of USD. Each layer in USD signifies a user's "opinion" on assets inside a stage. Layers can override other layers.


Instance
^^^^^^^^^^^^^^^^^^^^^^^

A light-weight and less manipulable copy of a prim.


Checkpoint
^^^^^^^^^^^^^^^^^^^^^^^

Immutable historical file versions. Checkpoints are used for version control and allow you to look at and restore the stage to a previous state.



.. _isaac_sim_glossary_physx:

PhysX
========================

NVIDIA PhysX is a scalable multi-platform physics simulation solution.
The NVIDIA Omniverse™ Physics simulation extension is powered by the NVIDIA PhysX SDK, and includes
Rigid Body Simulation, Articulations, Deformable-Body Simulation, and Character Controller.

- See :doc:`Physics Core <kit-physics:index>` for more details.

Isaac Sim
========================

.. _isaac_sim_glossary_ros:

ROS / ROS 2
^^^^^^^^^^^^^^^^^^^^^^^

The `Robot Operating System (ROS) <https://www.ros.org/>`_ is a set of software libraries and tools that help you build robot applications.
|isaac-sim| provides many extensions, examples, and APIs for connecting to ROS and ROS 2 workflows.


.. _isaac_sim_glossary_dynamic_control:

Dynamic Control
^^^^^^^^^^^^^^^^^^^^^^^

The Dynamic Control extension a set of utilities to control physics objects. It provides opaque handles for different physics objects that remain valid between PhysX scene resets, which occur whenever play or stop is pressed.

- See the |link_ext_dc_docs| documentation for full usage examples and API details.

.. |link_ext_dc_docs| raw:: html

    <a href="../py/source/deprecated/omni.isaac.dynamic_control/docs/index.html" target="_blank">API Documentation</a>

.. note:: omni.isaac.dynamic_control is deprecated.

.. _isaac_core_about:

Core API
^^^^^^^^^^^^^^^^^^^^^^^

.. important::

    Isaac Sim 5.0.0 has introduced the `Core Experimental API <../py/docs/overview/experimental.html>`_: a rewritten implementation of the current Core API
    designed to be more robust, flexible, and powerful, yet still maintain the core utilities and wrapper concepts.

    Going forward, it will become the base API used in all Isaac Sim source code.
    The current Core API will be deprecated and removed in future releases.

    Therefore, **we strongly encourage early adoption and use of the Core Experimental API**.

The Isaac Core Extension in |isaac-sim_short| provides high-level interfaces to PhysX and raw USD APIs. It abstracts away default parameters to simplify creation and manipulation of a simulated world
and scenarios encountered in robotics simulators. Specifically, the extension allows for

    #. easy creation, manipulation, and management of the world, all its time-related events, and related physical and numerical parameters
    #. creation of various robotic tasks and controllers
    #. vectorized manipulation of reinforcement learning environments through various `view` classes such as ``ArticulationView``, ``RigidPrimView``, ``XFormPrimView``, which provide high-level functionalities to manipulate in parallel sets of articulations, rigid prims, and xforms, respectively.

- See the |link_ext| documentation for full usage examples and API details.

.. |link_ext| raw:: html

    <a href="../py/source/extensions/isaacsim.core.api/docs/index.html" target="_blank">API Documentation</a>

.. _isaac_sim_glossary_rmp:

Riemannian Motion Policy (RMP)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Riemannian Motion Policy (RMP) is a set of motion generation tools that underlies most of our manipulator controls inside Omniverse Isaac Sim. It creates smooth trajectories for the robots with intelligent collision avoidance.

- See the :ref:`isaac_sim_motion_generation` documentation for more details and examples.

.. _isaac_sim_glossary_world:

World
^^^^^^^^^^^^^^^^^^^^^^^
World is the core class that enables you to interact with the simulator in an easy and modular way. It takes care of many time-related events such as adding callbacks, stepping physics, resetting the scene, adding tasks, etc. The World class is a Singleton which means only one World can exist while running Omniverse Isaac Sim. Query the World for information about the simulation from different extensions.

.. _isaac_sim_glossary_scene:

Scene
^^^^^^^^^^^^^^^^^^^^^^^

A world contains an instance of a Scene, think about it as a scene management class that manages the assets of interest in the USD stage. It provides an easy API to add, manipulate and inspect different USD assets in the stage as well as setting its default reset states. Many of the object classes available which could be added to a Scene usually takes an already existing USD prim in stage or creates a new USD prim, thus providing an easy way to set/ get its common properties.

.. _isaac_sim_glossary_task:

Task
^^^^^^^^^^^^^^^^^^^^^^^
The Task class in :code:`isaacsim.core.api` provides a way to modularize the scene creation, information retrieval, calculating metrics and creating more complex scenes with more involved logic.

.. _isaac_sim_glossary_articulation:

Articulation
^^^^^^^^^^^^^^^^^^^^^^^

An articulated robot is a robot with rotary joints (e.g: a legged robot, a manipulator or a wheeled robot). In :code:`isaacsim.core.api` extension in |isaac-sim| there exists an Articulation class which enables the interaction with articulations that exists in a USD stage in an easy way.

.. _isaac_sim_glossary_replicator:

Replicator
^^^^^^^^^^^^^^^^^^^^^^^
Replicator is a Synthetic Data Generation tool for creating parameterizable offline datasets in |isaac-sim|.

- See the :doc:`omni.replicator extension documentation <extensions:ext_replicator>` for additional usage information.


.. _isaac_sim_glossary_synthetic_data:

Synthetic Data Generation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

|isaac-sim| supports Synthetic Data Generations workflows. See :ref:`isaac_sim_glossary_replicator` for more details.

.. _isaac_sim_glossary_ground_truth:

Ground Truth
^^^^^^^^^^^^^^^^^^^^^^^
|isaac-sim| can be used to generate ground truth data that is very similar to real-life analogs. See :ref:`isaac_sim_glossary_replicator` for more details.
