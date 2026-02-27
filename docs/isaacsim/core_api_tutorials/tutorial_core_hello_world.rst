..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. meta::
    :title: Isaac Sim Core Tutorials
    :keywords: lang=en isaac isaac-sim core

.. _Visual Studio Code: https://code.visualstudio.com/download

.. _isaac_sim_app_tutorial_core_hello_world:

==========================================
Hello World
==========================================

:doc:`NVIDIA Omniverse™ Kit <dev-guide:kit-architecture>`, the toolkit that |isaac-sim| uses to build its applications, provides a Python interpreter for scripting. This means every single GUI command, as well as many additional functions are available as Python APIs. However, the learning curve for interfacing with |kit| using Pixar's USD Python API is steep and steps are frequently tedious. Therefore we've provided a set of APIs that are designed to be used in robotics applications, APIs that abstract away the complexity of USD APIs and merge multiple steps into one for frequently performed tasks.

In this tutorial, we will present the concepts of Core APIs and how to use them. We will start with adding a cube to an empty stage, and we'll build upon it to create a scene with multiple robots executing multiple tasks simultaneously, as seen below.


.. image:: /images/core_api_tutorials_6_2.webp
    :align: center
    :width: 600



Learning Objectives
===================

This tutorial series introduces the Core API. After this tutorial, you learn:

- How to use the Core APIs to manipulate the USD stage.
- How to add a rigid body to the :ref:`isaac_sim_glossary_stage` and simulate it using Python in |isaac-sim|.
- The difference between running Python in an **Extension Workflow** vs a **Standalone Workflow**.

*10-15 Minute Tutorial*



Getting Started
================

**Prerequisites**

- Intermediate knowledge in Python and asynchronous programming is required for this tutorial.
- Please download and install `Visual Studio Code`_ prior to beginning this tutorial.
- Please review :ref:`isaac_sim_intro_quickstart_series` and :ref:`isaac_sim_app_tutorial_intro_workflows` prior to beginning this tutorial.

Begin by opening the *Hello World* example. First activate **Windows** > **Examples** > **Robotics Examples** which will open the ``Robotics Examples`` tab.

1. Click **Robotics Examples > General > Hello World**.
2. Verify that the window for the *Hello World* example extension is visible in the workspace.
3. Click the **Open Source Code** button to launch the source code for editing in `Visual Studio Code`_.
4. Click the **Open Containing Folder** button to open the directory containing the example files.

This folder contains three files: :code:`hello_world.py`, :code:`hello_world_extension.py`, and :code:`__init__.py`.

The :code:`hello_world.py` script is where the logic of the application will be added, while the UI
elements of the application will be added in :code:`hello_world_extension.py` script and thus
linked to the logic.

#. Click the **LOAD** button to load the World.
#. click **File > New From Stage Template > Empty** to create a new stage, click **Don't Save** when prompted to save the current stage.
#. Click the **LOAD** button to load the World again.
#. Open :code:`hello_world.py` and press "Ctrl+S" to use the hot-reload feature. You will
   notice that the menu disappears from the workspace (because it was restarted).
#. Open the example menu again and click the **LOAD** button.

Now you can begin adding to this example.

Code Overview
=====================

This example inherits from BaseSample, which is a boilerplate extension application that
sets up the basics for every robotics extension application. The following are a few examples of the
actions BaseSample performs:

#. Loading assets into the stage using a button.
#. Clearing the stage when a new stage is created.
#. Resetting objects to their default states.
#. Handling hot reloading.


.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_hello_world/handling_hot_reloading.py
    :language: python
    :linenos:
    :emphasize-lines: 1-3, 10-15

Key Concepts
^^^^^^^^^^^^^^^

**Stage Utilities**: The :code:`stage_utils` module provides functions for directly manipulating the USD stage,
such as adding references, creating prims, and managing stage hierarchy.

**Prim Classes**: The API provides prim wrapper classes like :code:`RigidPrim`, :code:`GeomPrim`,
and :code:`Articulation` that give you direct control over USD prims with physics capabilities.

**SimulationManager**: For callbacks and simulation events, the :code:`SimulationManager` class provides
methods to register and deregister callbacks for various simulation events.


Adding to the Scene
=====================

Use the Python API to add a cube as a rigid body to the scene. With the Core APIs,
create the geometry first, then apply collision and rigid body properties.

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_hello_world/adding_to_the_scene.py
    :language: python
    :linenos:
    :emphasize-lines: 1-7, 21-40

#. Press **Ctrl+S** to save the code and hot-reload |isaac-sim|.
#. Open the menu again.
#. click **File > New From Stage Template > Empty**, then the **LOAD** button. You need to perform this action
   if you change anything in the **setup_scene**. Otherwise, you only need to press the
   **LOAD** button.
#. See the dynamic cube falling as the simulation starts automatically.

.. image:: /images/core_api_tutorials_1_1.webp
    :align: center
    :width: 600

.. note:: Every time the code is edited or changed, press **Ctrl+S** to save the code and hot-reload
          |isaac-sim|.


Understanding the Prim Classes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The experimental API uses a layered approach to create physics-enabled objects:

1. **Cube** (or other shape classes): Creates the visual geometry on the USD stage.
2. **GeomPrim**: Wraps the geometry and can apply collision APIs for physics interactions.
3. **RigidPrim**: Adds rigid body dynamics, making the object respond to gravity and forces.

This modular approach gives you fine-grained control - you can create static colliders
(GeomPrim without RigidPrim) or fully dynamic objects (with both).


Inspecting Object Properties
=============================

Print the world pose and velocity of the cube. The highlighted lines show how you can query object properties.

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_hello_world/inspecting_object_properties.py
    :language: python
    :linenos:
    :emphasize-lines: 38-51

.. note:: The experimental APIs return batched results as warp arrays. Use ``.numpy()`` to convert
          them to numpy arrays, and index with ``[0]`` to get the first (and only) element when
          working with a single object.


Continuously Inspecting the Object Properties during Simulation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Print the world pose and velocity of the cube during simulation at every physics step
executed. As mentioned in :ref:`isaac_sim_app_tutorial_intro_workflows`, in this workflow the
application is running asynchronously and can't control when to step physics. However, you can add
callbacks to ensure certain things happen before certain events.

Add a physics callback using the SimulationManager:

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_hello_world/continuously_inspecting_the_object_properties_duri.py
    :language: python
    :linenos:
    :emphasize-lines: 7, 44-46, 51-56

Converting the Example to a Standalone Application
=====================================================

.. note::
    - On windows use python.bat instead of python.sh
    - The details of how python.sh works below are similar to how python.bat works

As mentioned in :ref:`isaac_sim_app_tutorial_intro_workflows`, in this workflow, the robotics
application is started when launched from Python right away.

#. Open a new ``my_application.py`` file and add the following:

.. literalinclude:: ../snippets/core_api_tutorials/tutorial_core_hello_world/open_a_new_my_applicationpy_file_and_add_the_follo.py
    :language: python
    :linenos:

#. Run it using ``./python.sh ./exts/isaacsim.examples.interactive/isaacsim/examples/interactive/user_examples/my_application.py``.



Summary
========

This tutorial covered the following topics:

#. Overview of the Core APIs for direct stage manipulation.
#. Using :code:`stage_utils` to add assets to the stage.
#. Creating dynamic objects with :code:`Cube`, :code:`GeomPrim`, and :code:`RigidPrim`.
#. Registering physics callbacks with :code:`SimulationManager`.
#. Accessing dynamic properties for objects using prim wrapper methods.
#. The main differences in a standalone application.



Next Steps
^^^^^^^^^^^^^^^^^^^^^^

Continue to :ref:`isaac_sim_app_tutorial_core_hello_robot` to learn how to add a robot to the simulation.

.. Note:: The next tutorials will be developed mainly using the extensions application workflow.
          However, conversion to other workflows is similar given what was covered
          in this tutorial.

