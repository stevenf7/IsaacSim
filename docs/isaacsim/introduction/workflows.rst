..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _Visual Studio Code: https://code.visualstudio.com/download

.. _isaac_sim_app_tutorial_intro_workflows:

=============
Workflows
=============

Isaac Sim is a component of larger solutions and can be used on its own. It consequently has multiple ways that you can use it to achieve the same thing. We refer to those different ways to do things as workflows. There are three main workflows when developing in |isaac-sim_short|: 

* GUI
* Extensions
* Standalone Python

We recommend that you go through the :doc:`Quick Start Tutorials <quickstart_index>` to have a basic understanding of all of them and how they are interconnected. 


Workflows
===============

Here is a summary of the key features and their recommended usages:

**GUI**

- **Key features**: Visual, intuitive, specialized tools for populating and simulating a virtual world.
- **Recommended usage**: World building, assemble robots, attach sensors, visual programming using OmniGraphs, and initializing ROS bridges.


**Extension**

- **Key features**: Runs asynchronously to allow interactions with the stage, *hot reloading* to reflect changes immediately, adaptive physics steps for real-time simulation.
- **Recommended usage**: Testing Python snippets, building interactive GUIs, custom application modules, and real-time sensitive applications.


.. _standalone-application:

**Standalone Python**

- **Key features**: Control over timing of physics and rendering steps, can be run in headless mode.
- **Recommended usage**: Large scale training for reinforcement learning, systematic world generation, and modification.


Combining Workflows
======================

Most of the actions that can be performed in the GUI, can be performed using Python. You can switch between performing actions in the GUI and in Python. Anything you make inside the GUI can be saved as part the USD file. 

For example, you can create the world, include the actions needed for your robots using the GUI. Then pull the entire USD file into a standalone Python script and systematically modify properties there as needed.



Extensions and the GUI 
--------------------------------------


:ref:`isaac_sim_glossary_extensions` are the core building blocks of Omniverse Kit based applications. They are individually built application modules and can be used across different Omniverse applications. Most of the tools in |isaac-sim_short| are built as extensions. You can enable and disable any set of extensions according to your project needs.

The **GUI workflow** uses a collection of extensions that are loaded by default at the start of |isaac-sim_short|. These are general tools that are frequently used when building virtual worlds, robots, examining physics, rendering, material properties, profiling performance, and include tools for visual programming, for managing USD stage and assets, and for Robotics applications. 

**Next steps**: Learn how to build your own extension with our :ref:`Templates <isaac_sim_templates>`, and explore our interactive examples in the :ref:`Examples Browser <isaac_sim_app_intro_examples>`, all of which are extension-based. 

Python Standalone and in an Extension 
-------------------------------------------

The Extension and Standalone Python workflows use the same APIs for all the functions. However, they diverge for printing or commanding the robot joint states continuously. 

**Python in an Extension** -- The :doc:`Script Editor <extensions:ext_script-editor>` allows you to interact with the Stage asynchronously using Python. This means that the Python APIs are interacting with the USD stage.

The Python in extension runs without blocking rendering and physics stepping. If you want to interact with the physics and rendering steps or perform an action that is likely to be blocking, you would have to explicitly insert relevant callbacks and async functions for those functions to work. In the extension applications, rendering is stepping the moment viewport opens and physics is stepping when you press the **Play** button. 

**Standalone Python** -- To use the standalone Python version of |isaac-sim_short|, you launch it using a Python script. Inside the script, you can control whether you open the GUI interface or run in headless mode. 

In standalone Python, you can do step rendering and physics manually, which gives you the ability to guarantee that stepping only happens after the completion of a set of commands. These functions make the standalone workflow ideal for use cases, such as training behaviors where there might be randomization actions that all need to complete before the next step, or if you need to control message publishing rates in ROS, as well as running headless to increase performance.

**Next steps**: Learn how to run your first standalone application with :ref:`isaac_sim_app_tutorial_core_hello_world`, and how to use development tools such as :ref:`isaac_sim_app_jupyter_notebook` or :ref:`isaac_sim_app_vscode` for Python development.

Hot Reloading for Extensions
===================================

Python-based Extensions also have the ability to "hot reload". This means that you can change the underlying code while |isaac-sim_short| is running, and then see the reflected changes in your application after saving the file, without shutting down or restarting |isaac-sim_short|. This is a powerful feature that allows you to iterate quickly on your application. 



Review Examples
===================

Review the: 

* **Extension Examples** available in the :ref:`Examples Browser <isaac_sim_app_intro_examples>`.
* **Standalone Examples** available in the ``<isaac-sim-root-dir>/standalone_examples`` folder. 






.. GUI
.. =============================
.. .. |isaac-sim_short|'s GUI interface are created for intuitive and interactive world-building. These tools make it easy to assemble, illuminate, simulate, and render scenes large and small, therefore making it the ideal place to build your virtual worlds, assemble robots, and examine physics.


.. Additionally, OmniGraph, a visual programming tool, is available in the GUI. It allows you to create complex behaviors and interactions between objects in the scene without writing any code.

.. To learn more about how to leverage the GUI for your robotics application, continue the GUI tutorial series with :ref:`isaac_sim_app_tutorial_gui_simple_robot`.




.. .. _isaac_sim_extension_workflow:

.. Extensions
.. ==================================

.. :ref:`isaac_sim_glossary_extensions` are the core building block of Omniverse Kit based applications. They are individually built application modules, and can be used across different Omniverse applications by installing it in the **Extensions Manager**. All the tools used in |isaac-sim_short| are built as extensions, that includes all of the GUI tools. 


.. One main feature of this workflow is that the application runs asynchronously. This enables the extension applications to interact with the USD stage without blocking rendering and physics stepping. It also allows for hot reloading, so you can change the application code while |isaac-sim_short| is running and then see the reflected changes in your application after saving the file, without shutting down or restarting |isaac-sim_short|.
.. Most of the action in an extension is done using callbacks that are triggered with certain events, such as a physics or rendering step, stage events, or ticks in time.

.. More Extension resources
.. ^^^^^^^^^^^^^^^^^^^^^^^^

.. - :ref:`isaac_sim_app_extension_template_generator` provides a template for creating a new extension.
.. - :ref:`isaac_sim_app_tutorial_extension_templates` provides examples of how to use the extension template.
.. - `Kit C++ Extension Template <https://docs.omniverse.nvidia.com/kit/docs/kit-extension-template-cpp/latest/index.html>`_ for writing custom C++ extension instructions.



.. .. _standalone-application:

.. Standalone Application
.. ========================

.. In this workflow, |isaac-sim_short| is launched using a Python script, inside which the rendering and physics are stepped manually, to guarantee that stepping only happens after ascertaining the completion of a set of commands.


.. TODO: what do you use it for. 
.. - headless mode
.. - training
.. - control over physics and rendering steps
.. - control message publishing rate in ROS



.. Standalone resources
.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. - check your setup  TODO
.. - to run your first standalone application. TODO
.. - :ref:`isaac_sim_app_tutorial_core_hello_world` provides a simple example of a standalone application.
.. - apis for standalone applications TODO
.. - python scripting section TODO
.. - debugging and dev tools


.. Running Your First Standalone Application
.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. #. Open the terminal.
.. #. Navigate to the package path and run the ``follow_target_with_rmpflow.py`` script:

..     .. code-block:: console

..         ./python.sh standalone_examples/api/isaacsim.robot.manipulators/franka/follow_target_with_rmpflow.py

.. #. Move the target prim by selecting it in the viewport so that Franka follows it.

.. .. figure:: /images/isaac_sim_follow_target.gif
..     :align: center



.. Using Jupyter to Develop a Standalone Application
.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. can be launched as headless in this workflow (that is, without a visible and updating GUI). It can also be launched via a Jupyter notebook (Linux only). In the clip below, the Jupyter notebook live syncs to the same USD so that changes are reflected in another |isaac-sim_short| process launched through the terminal or the launcher.

.. :ref:`isaac_sim_app_tutorial_core_hello_world` covers this workflow in detail.

.. .. figure:: /images/isaac_sim_jupyter_workflow.gif
..     :align: center


.. ROS Application
.. =================

.. For more information about using |isaac-sim_short| with ROS, see the ROS tutorial series starting with
.. :ref:`isaac_sim_app_tutorial_ros_turtlebot`.

.. Summary
.. ========

.. This tutorial covered the following topics:

.. - The different workflows to develop an application in |isaac-sim|
.. - Running an example using each workflow

.. Next Steps
.. ^^^^^^^^^^^^^^^^^^^^^^

.. Choose continue on to the next tutorial that suits your workflow:

.. - GUI: :ref:`isaac_sim_app_tutorial_gui_simple_robot`
.. - Standalone and Extension: :ref:`isaac_sim_app_tutorial_core_hello_world`



.. Further Learning
.. ^^^^^^^^^^^^^^^^^^^^^^
.. For a more in-depth look into the concepts covered in this tutorial, see the following reference materials:

.. - :doc:`Extensions <extensions:index>`

