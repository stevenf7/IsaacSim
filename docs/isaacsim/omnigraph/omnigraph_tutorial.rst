.. _isaac_sim_app_tutorial_gui_omnigraph:

=============================
Isaac Sim OmniGraph Tutorial
=============================

This tutorial introduces you to the world of visual programming via |omnigraph_short|.
We highly recommend that you also read :doc:`OmniGraph <extensions:ext_omnigraph>`, because it is a key component in |kit|.


Learning Objectives
===================

This tutorial aims to

- walk you through building an action graph to control a robot in |isaac-sim_short|, specifically, the Jetbot.
- show you how to use the OmniGraph shortcuts to generate a differential controller graph for the Jetbot.



Build the Graph
=====================

Let's build an action graph to control a robot in |isaac-sim_short| the Jetbot.


Setting Up the Stage
---------------------

#. On a new stage, start by right clicking and selecting **create > Physics > Ground Plane**.
#. In the Content Browser, navigate to ``Isaac Sim/Robots/NVIDIA/Jetbot/jetbot.usd``.
#. Click and drag ``jetbot.usd`` onto the stage.
#. Position the JetBot just above the ground plane.
#. When completed, verify that the JetBot is under ``/World/jetbot`` in the context tree and that the stage looks similar to:

.. figure:: /images/isim_4.5_base_tut_viewport_omnigraph_jetbot.png
    :align: center

    Jetbot on the stage

.. note:: Click play!  Validate that the JetBot falls and lands on the stage. Click stop before continuing.

Depending on your default render settings, the camera of the JetBot may have a placeholder mesh (it looks like a gray television camera).
To hide these meshes, click on the |eyecon| icon in the viewport and select **Show By Type --> Cameras**.

Building the Graph
-------------------

#. Select **Window > Graph Editors > Action Graph** from the dropdown menu at the top of the editor.
   The Graph Editor appears in the same pane as the Content browser.
#. Click **New Action Graph** to open an empty graph.
#. Type ``controller`` in the search bar of the graph editor.
#. Drag an ``Articulation Controller`` and a ``Differential Controller`` onto the graph.

The ``Articulation Controller`` applies driver commands (in the form of force, position, or velocity) to the specified joints
of any prim with an articulation root.

To tell the controller which robot it's going to control:

#. Select the ``Articulation Controller`` node in the graph and open up the property pane.
#. You can either:

   - Click **usePath** and Type in the path to the robot */World/jetbot* in **robotPath** 

     **OR**

   - Click **Add Targets** near the top of the pane for ``input:targetPrim`` and select **JetBot** in the pop up window.

The ``Differential Controller`` computes drive commands for a two wheeled robot given some target linear and angular velocity.  Like the
``Articulation Controller``, it also needs to be configured.

#. Select the ``Differential Controller`` node in the graph.
#. In the properties pane, set the ``wheelDistance`` to 0.1125, the ``wheelRadius`` to 0.03, and ``maxAngularSpeed`` to 0.2.

The ``Articulation Controller`` also needs to know which joints to articulate.  It expects this information in the form of a list of tokens or index values. Each joint in a robot has a name and the JetBot has exactly two.  Verify this by examining the JetBot in the stage context tree.  Within ``/World/jetbot/chassis``
are two revolute physics joints named ``left_wheel_joint`` and ``right_wheel_joint``.

.. figure:: /images/isim_4.5_base_tut_gui_omnigraph_jetbot_joints.png
    :align: center

    Stage Tree

#. Type ``token`` into the search bar of the graph editor.
#. Add two ``Constant Token`` nodes to the graph.
#. Select one and set it's value to ``left_wheel_joint`` in the properties pane.
#. Repeat this for the other constant token node, but set the value to ``right_wheel_joint``.
#. Type ``make array`` into the search bar of the graph editor.
#. Add a ``Make Array`` node to the graph.
#. Select the ``Make Array`` node and click on the ``+`` icon in the ``inputs`` section of the property pane menu to add a second input.
#. Set the ``arraySize`` to 2 and set the input type to ``token[]`` from the dropdown menu in the same pane.
#. Connect the constant token nodes to ``input0`` and ``input1`` of the ``Make Array`` node, and then the output of that node to the ``Joint Names`` input of the ``Articulation Controller`` node.

The last node is the event node.

#. Search for ``playback`` in the search bar of the graph editor.
#. Add an ``On Playback Tick`` node to the graph.  This node emits an execution event for every frame, but only while the simulation is playing.
#. Connect the ``Tick`` output of the ``On Playback Tick`` node to the ``Exec In`` input of both controller nodes.
#. Connect the ``Velocity Command`` output of the differential controller to the ``Velocity Command`` input of the articulation controller.
#. Validate that the graph looks similar to:

.. figure:: /images/isaac_tutorial_omnigraph_jetbot_minimal.png
    :align: center
    :width: 800

    Simple differential control for the JetBot

#. Press the play button.
#. Select the ``Differential Controller`` node in the graph.
#. Click and drag on either the angular or linear velocity values in the properties pane to change it's value (or just click and type in the desired value).


.. Note::

    Explore the available |omnigraph_short| nodes and try to setup a graph to control the JetBot with the keyboard. The graph
    below is an example graph for controlling the JetBot with a keyboard.

    .. figure:: /images/isaac_tutorial_omnigraph_full.png
        :align: center
        :width: 800

        Keyboard control Action graph for the JetBot


OmniGraph Shortcuts
===================

Putting the graph from scratch can be tedious, especially when you have to iterate. We made some shortcuts for frequently used graphs, so that within a couple clicks, you can generate a complex graph with multiple nodes and connections. They can be found under ``Tools -> Robotics -> OmniGraph Controllers``, and the instructions for them are in :ref:`isaac_sim_app_tutorial_advanced_omnigraph_shortcuts`.

To use the Differential Controller graph from the menu shortcut:

#. Delete (or Disable if that is an option) any previous OmniGraphs that controls the Jetbot.
#. Go to the Menu bar and click on **Tools -> Robotics -> OmniGraph Controllers -> Differential Controller**.
#. You are prompted for the necessary parameters.
#. Add "/World/jetbot" to ``Articulation Root``, set the **distance between wheels** to 0.1125, and the **wheel radius** to 0.03.
#. Given JetBot only has two controllable joints, you can leave the rest of the fields empty.
#. Turn **Use Keyboard Control (WASD)** on.
#. Click **OK** to generate the graph. You can open the generated graph under ``/Graph/differential_controller``.
#. Press **Play** to start simulation.
#. Verify that you can move the JetBot using the WASD keys on the keyboard.

.. figure:: /images/isim_4.5_base_tut_gui_jetbot_controller_graph.webp
    :align: center

Summary
========

This tutorial covered:

* Basic concepts of |omnigraph_short|
* Setting up a stage with a robot
* Using |omnigraph_short| to construct interfaces to a robot
* Using the OmniGraph shortcuts to generate differential controller graph

Further Learning
-------------------

* More in-depth concepts in :doc:`OmniGraph <extensions:ext_omnigraph>`
* More details about all the OmniGraph shortcuts :ref:`isaac_sim_app_tutorial_advanced_omnigraph_shortcuts`
* Examples for composing |omnigraph_short| via Python scripting: :ref:`isaac_sim_app_tutorial_advanced_omnigraph_scripting`
* Examples for writing custom Python nodes: :ref:`isaac_sim_app_omnigraph_custom_python_nodes`

.. |eyecon| image:: /images/isim_4.5_base_ref_gui_eyecon.png
    :width: 30