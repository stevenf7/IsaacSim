..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_sim_app_omnigraph_custom_python_nodes:

================================
Custom Python Nodes
================================

There already exist a large number of default nodes that comes with |isaac-sim_short|. You can find the definitions and descriptions for them in either the :doc:`Omnigraph Node Library<extensions:ext_omnigraph/node-library/node-library>` or :ref:`isaac_sim_python_manual`. If those prove to be insufficient, you can write your own and integrate them into |isaac-sim_short|. 

A node is defined by two files, an .ogn file, which is a JSON file that defines the structure of the node, including its inputs, outputs, and parameters. Either a Python file or a C++ file can be used to define its function. Here we will focus on Python nodes.


Node Files
===========================

All OmniGraph Node files starts with "Ogn" as a prefix. This is expected by the parser. 

.. _isaac_sim_omnigraph_ogn_file:

Node Definition (.ogn)
---------------------------

The .ogn file is a JSON file that defines the structure of the node, including its inputs, outputs, and parameters. Here is an example of a simple node definition:

.. code-block:: JSON
   :linenos:   

   {
    "NodeName": {
        "version": 1,
        "categories": "examples",
        "description": ["Minimum Example"],
        "language": "python",
        "metadata": {
            "uiName": "minimum example"
        },
        "inputs": {
			   "execIn": {
                "description": "the trigger input that starts the node",
                "type": "execution",
            },
			   "value_input": {
                "type": "double",
                "description": "a number",
                "default": 0.0,
             },
        },
        "outputs": {
            "output_bool": {
                "type": "bool",
                "description": "let output be a boolean",
             }
         }
      }
   }


A note about the input "execIn". This is a special input that is used to trigger the node. This trigger is only relevant in an Action Graph, where you must explicitly trigger the node to run, such as on a physics tick, or a stage event, like opening and closing a stage. In a Push Graph, the node will run automatically at every frame and the 'execIn' input is not necessary.


Function Definition
---------------------------

Here's a minimum example of a Python node that takes an input number and outputs a boolean value based on whether the input is greater than 0:


.. literalinclude:: ../snippets/omnigraph/omnigraph_custom_python_nodes/function_definition.py
    :language: python

Notes:

- the class name must match the name of the node in the .ogn file, and the file name must match the class name.
- the "compute" function is what the 'execIn' input triggers. It takes a single argument, the database, which contains the inputs and outputs of the node. The function should return True if the node ran successfully, and False if it failed.
- this node has no internal state, which means all data that passes through it is gone the next tick. If you need to store data between ticks, you can use the "internal state" to store it.



Using the Custom Node
===========================

You can simply insert your custom node's ``.py`` and ``.ogn`` files into any of extensions that already have a directory that contains the ``.py`` and ``.ogn`` files for existing nodes and thereby avoid creating your own extension that way.

You can also create your own extension and insert the files there. (link to the new template generator)


Isaac Sim Nodes as Examples
=============================

You are welcome to dig into the code behind some of our existing OmniGraph nodes to find examples of how to structure a node, or even modify them to suite your own need. To find the backend ``.py`` and ``.ogn`` files for a particular node. Hover your mouse over the node in the editor window, a tooltip window will appear and the name of the extension will be written in the parentheses. You can then navigate to the extensions's folder that contains the backend scripts for the nodes by going to ``exts/isaacsim.<ext_name>/isaacsim/<ext_name>/ogn/python/nodes/``.

Not all of the nodes are written in Python, some have C++ backends, so if you won't necessarily see a corresponding ``.py`` and ``.ogn`` files for all the nodes on the list. Note that if you found a folder with a list of ``Ogn<node_name>Database.py``, this is NOT the directory that contains the Python description of the node.