..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_ros2_custom_omnigraph_node_python:

=============================================
ROS 2 Python Custom |omnigraph_short| Node
=============================================

Learning Objectives
=====================

This is an optional, advanced tutorial where you will learn how to

- Use ROS 2 *rclpy* Python interface with |isaac-sim_short|
- Create a basic custom |omnigraph_short| Python node (using the `Isaac Sim VS Code Edition <https://marketplace.visualstudio.com/items?itemName=NVIDIA.isaacsim-vscode-edition>`_) that can subscribe to a topic (with message type ``std_msgs/msg/Int32``) and output the Fibonacci computation of the published number.

Getting Started
====================



**Prerequisite**

- Completed :ref:`isaac_sim_app_install_ros`: installed ROS2, enabled the ROS2 extension, built the provided *Isaac Sim* ROS 2 workspace, and set up the necessary environment variables.

- Completed the tutorial for writing custom Python nodes: :ref:`isaac_sim_app_omnigraph_custom_python_nodes`

Creating the ROS 2 Custom |omnigraph_short| Python Node Template
=====================================================================

#. Go to *Template > Extension* in the **Isaac Sim VS Code Edition** (VS Code extension) to open a wizard to create a new Isaac Sim extension.

    Take action on the following fields:

    * **Ext. name:** Set to ``custom.python.ros2_node``
    * **Ext. path:** Define the target path where the extension will be created.
    * **Ext. title:** Set to ``ROS 2 Python Custom OmniGraph Node``

    * **Ready-to-use extension:** Check it to create a ready-to-use extension in Python.
    * **Omnigraph node:** Check it to generate OmniGraph-specific files/folders when creating the extension.

    .. figure:: /images/tutorial_ros2_custom_omnigraph_node_python_vscode_extension_template.png
        :align: center
        :width: 100%
        :alt: Extension template wizard

#. Edit the extension configuration file (``custom.python.ros2_node/config/extension.toml``) to add the Isaac Sim's ROS 2 Bridge extension as a dependency (under ``[dependencies]``)

    .. literalinclude:: ../snippets/ros2_tutorials/tutorial_ros2_custom_omnigraph_node_python/edit_the_extension_configuration_file_custompython.py
        :language: python

#. Edit the OmniGraph definition file (``OgnCustomPythonRos2NodePy.ogn`` located in the ``custom.python.ros2_node/custom/python/ros2_node/ogn/python/nodes`` folder) with the following specification.

    This specification defines an OmniGraph node with two inputs (the input execution trigger, and the topic name to subscribe to (a string)) and two outputs (the output execution trigger, and the computed Fibonacci number (an integer)).

    .. hint::

        Visit the `OGN Reference Guide <https://docs.omniverse.nvidia.com/kit/docs/omni.graph.docs/latest/dev/ogn/ogn_reference_guide.html>`_
        for a detailed guide to the syntax of ``.ogn`` files.
        Visit OmniGraph's `Attribute Data Types <https://docs.omniverse.nvidia.com/kit/docs/omni.graph.docs/latest/dev/ogn/attribute_types.html>`_
        for more details about the supported attribute data types for inputs and outputs.

    .. literalinclude:: ../static/source/tutorial_ros2_custom_omnigraph_node_python_OgnCustomPythonRos2NodePy.ogn
        :language: json

#. Edit the OmniGraph Python source code file (``OgnCustomPythonRos2NodePy.py`` located in the ``custom.python.ros2_node/custom/python/ros2_node/ogn/python/nodes`` folder) with the following content.

    The code is self-commented enough.
    Basically, the ``OgnCustomPythonRos2NodePyInternalState`` class handles the communication with ROS. It creates the ROS 2 node, the subscription and handles the received messages.
    On the other hand, the ``OgnCustomPythonRos2NodePy`` class implements the custom OmniGraph node. It computes and sets the outputs according to the input values and the internal state.

    .. literalinclude:: ../static/source/tutorial_ros2_custom_omnigraph_node_python_OgnCustomPythonRos2NodePy.py
        :language: python

Running the Custom |omnigraph_short| Node
============================================

.. warning::

    The custom extension must first be activated for the OmniGraph node to be available.

    Open the extension manager using the *Window > Extensions* menu and search for the ``custom.python.ros2_node`` extension to enable it.

#. In a new stage, go to *Window > Graph Editors > Action Graph* to create an Action Graph and add, connect and configure the following |omnigraph_short| nodes into the Action Graph:

    * **On Playback Tick** node to execute other graph nodes every simulation frame.
    * **Custom Python ROS 2 Node** custom node.
    * **To String** node to convert the output of our custom node to a string.
    * **Print Text** node to display the output of our custom node (as string) to the viewport or terminal.
      Edit this node's properties, in the *Property* panel, and check the *To Screen* attribute to display the text in the viewport.
  
    .. figure:: /images/tutorial_ros2_custom_omnigraph_node_python_node_graph.png
        :align: center
        :width: 100%
        :alt: OmniGraph nodes

#. Play the simulation

#. In a new ROS 2-sourced terminal, run the next command to publish a number to the ``/number`` topic.

    .. code-block:: bash

        ros2 topic pub -1 /number std_msgs/msg/Int32 "{data: 10}"

#. After messages are being received from the topic, the Fibonacci number will appear in the top-left corner of the viewport.
   If no new values are received, the display will fade over time.

    .. note::

        To view the values in the Isaac Sim console, you can edit the *Print Text* node properties and uncheck the *To Screen* attribute and set the *Log Level* attribute to *Warning*.

    .. figure:: /images/tutorial_ros2_custom_omnigraph_node_python_results_display.png
        :align: center
        :width: 200
        :alt: Results display

#. Publish a different number using the previous ROS 2 topic command and notice the change in Isaac Sim.

Summary
========

This tutorial covered the following topics:

#. Creating a custom |omnigraph_short| Python node in an extension.

#. Using *rclpy* interface to create a ROS 2 node within a custom |omnigraph_short| node to subscribe to a topic, perform the Fibonacci computation and trigger downstream nodes when the computed |omnigraph_short| output is ready.


Next Steps
^^^^^^^^^^^^^
Continue on to the next tutorial in our ROS2 Tutorials series, :ref:`isaac_sim_app_ros2_omnigraph_cpp_node`.
