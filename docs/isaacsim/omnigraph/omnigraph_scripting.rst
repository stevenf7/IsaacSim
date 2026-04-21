.. _isaac_sim_app_tutorial_advanced_omnigraph_scripting:

==========================================
OmniGraph via Python Scripting Tutorial
==========================================

While |omnigraph_short| is intended to be a visual scripting tool, it does have Python scripting interfaces. This tutorial will give some examples of how to script an action graph using Python.


Learning Objectives
=======================

This tutorial will

- walk you through examples of scripting an Omnigraph using purely Python APIs
- introduce the basic concepts and frequently used parameters in OmniGraphs and showcase them using scripted examples




Getting Started
=======================

**Prerequisites**

- Review the GUI Tutorial series, especially :ref:`isaac_sim_app_tutorial_gui_omnigraph` and :ref:`isaac_sim_app_omniverse_script_editor` prior to beginning this tutorial.
- Review the Core API Tutorial series, especially :ref:`isaac_sim_app_tutorial_core_hello_world` to become familiar with the extension workflow via Python, as well as the Python Standalone workflow.



Code Snippets
=======================

Creating a Graph
^^^^^^^^^^^^^^^^^^^^
First let's build a simple action graph that prints "Hello World" to the console on every simulation frame.

#. Open 'Window > Script Editor' and paste the following code:

    .. literalinclude:: ../snippets/omnigraph/omnigraph_scripting/open_window_script_editor_and_paste_the_following_.py
        :language: python

#. Press 'Run' to execute the script. You should see a new prim ``/action_graph`` created on the Stage tree.
#. Expand the prim on stage, the nodes "tick" and "print" should be listed under the graph. These nodes can be accessed just like any other prim on the stage.
#. Press "play" to start the simulation. You should see "Hello World" printed to the console on every frame.
#. Open graph editor by going to `Window > Graph Editors > Action Graph`. 
#. With the newly created graph highlighted on the Stage tree on the right, open the graph by clicking on the icon for 'Edit Action Graph' in the graph editor window. You should see two nodes connected with each other by a line.


Editing a Graph
^^^^^^^^^^^^^^^^^^^^
Once a graph has been created, there are specific APIs to manipulate the graph's terms. 

**Getting and Setting Attribute Values**

Open another tab in the Script Editor, paste the snippet below, and run. 

.. literalinclude:: ../snippets/omnigraph/omnigraph_scripting/editing_a_graph.py
    :language: python

This will change the value in the "Print Text" node from "Hello World" to "New Texts to print". But this affect won't take place until the first tick through the graph. So when you press 'Run' in the script editor, the graph has yet to be ticked, so it should fetch the current value from the node, and print out a single string of "Existing Text: Hello World" in the Script Editor's console (as well as the terminal if you are using that, or the main Omniverse's console if you include "Info" to be printed). 

Now press 'Play' and start the simulation. It should now print, at the rate of one string per tick, the updated text "New Texts to print", in the terminal or the main Omniverse console (though not the Script Editor's console).

**Adding Nodes and Connections**

Open a third tab in the Script Editor to add nodes and make more connections to an existing graph.

.. literalinclude:: ../snippets/omnigraph/omnigraph_scripting/set_new_value.py
    :language: python

A new node named "new_node_name" will be created and connected to the "Print Text" node. If you have the graph editor (`Window > Graph Editors > Action Graph`) open, you can see that there are now three nodes connected to each other instead of two.

Graph Execution
^^^^^^^^^^^^^^^^^^^^

By default, the graph is evaluated on every frame. You can change this behavior by setting the graph to evaluate only when you call it.

You can also trigger each graph explicitly by making execute only when you call it. To do this, there is a special parameter called "pipeline_stage" where you can set the graph to execute "On Demand". Most of the times we want to set this variable during the creation of the graph:

#. Delete the previous graph by selecting it on the stage tree and pressing 'Delete' key.
#. Open a new tab in the Script Editor and paste the following code


    .. literalinclude:: ../snippets/omnigraph/omnigraph_scripting/open_a_new_tab_in_the_script_editor_and_paste_the_.py
        :language: python

#. Press 'Run' in the Script Editor. A new graph ``/ondemand_graph`` will be created. 
#. Start simulation by press "play", nothing should be printed from this graph because we did not explicitly call to evaluate it.
#. To manually trigger a graph, open another tab, and paste in ``demand_graph_handle.evaluate()`` 
#. Make sure simulation is still running. Click 'Run' in the Script Editor. You should see "On Demand Graph" printed to the console once. 

Alternatively, you can also set it for an existing graph by ``demand_graph_handle.change_pipeline_stage(og.GraphPipelineStage.GRAPH_PIPELINE_STAGE_ONDEMAND)``

A more in-depth example of attaching graphs to physics callbacks and/or rendering callbacks can be found in `standalone_examples/api/isaacsim.core.experimental.api/omnigraph_triggers.py`


Summary
=======================

In this tutorial, we introduced scripting |omnigraph_short| via Python.

Further Reading
^^^^^^^^^^^^^^^^^^^^
For more Python Scripting API in `OmniGraph APIs <https://docs.omniverse.nvidia.com/kit/docs/omni.graph/latest/omni.graph.core.html>`_ 