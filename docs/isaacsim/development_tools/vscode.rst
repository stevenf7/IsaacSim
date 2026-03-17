
.. _Isaac Sim VS Code Edition: https://marketplace.visualstudio.com/items?itemName=NVIDIA.isaacsim-vscode-edition

.. _isaac_sim_app_vscode:


==========================================
Visual Studio Code (VS Code)
==========================================

Isaac Sim VS Code Edition
--------------------------

`Isaac Sim VS Code Edition`_ is an extension for Visual Studio Code that provides development support for NVIDIA Omniverse in general and Isaac Sim in particular.

Key Features:

* Execute Python code, in the Python environment of a running application, locally or remotely from VS Code and show the output in the *Isaac Sim VS Code Edition* panel.
* Browse and insert snippets of code related to Isaac Sim, Omniverse Kit and Universal Scene Description (USD).
* Create templates for Omniverse/Isaac Sim extensions and other development approaches.
* Quick access to the most relevant Omniverse/Isaac Sim documentation sources and resources without leaving the editor.

**Install it now to get started**: `Isaac Sim VS Code Edition`_

.. image:: /images/isaac_tutorial_advanced_code_editors_vscode.png
    :align: center

|br| |hr|

Interactive Scripting
-----------------------

The ``isaacsim.code_editor.vscode`` extension adds VS Code launcher and menu integration to Isaac Sim.
It depends on the ``isaacsim.code_editor.python_server`` extension which provides the TCP server for remote Python code execution (see :ref:`isaac_sim_app_python_server` for full protocol details and usage examples).

Both extensions can be enabled or disabled using the :doc:`Extension Manager <extensions:ext_core/ext_extension-manager>` by searching for ``isaacsim.code_editor.vscode``.
Enabling the VS Code extension automatically enables the Python server.

    .. note::

        This extension requires its Visual Studio Code pair extension: `Isaac Sim VS Code Edition`_ to be installed and enabled, in the VS Code editor, in order to execute Python scripts on a running Isaac Sim instance.

#. To begin, enable this extension using the :doc:`Extension Manager <extensions:ext_core/ext_extension-manager>` by searching for ``isaacsim.code_editor.vscode``.
#. Once the extension is enabled, go to the top menu bar and click on `Window > VS Code` to open the Isaac Sim folder in a VS Code application.
#. Open a stored file or write the code you want to run in a VS Code editor tab.
#. From the VS Code editor, click on the *Isaac Sim VS Code Edition* container in the Activity Bar (the one with the Isaac Sim logo) to open it.
   Then, click on *Run* (or *Run selected text* if you have selected code statements), in the *Commands* tree view, to execute it.
#. Inspect the execution output, if any, in the *Isaac Sim VS Code Edition* output panel.

.. tip::

   The Python server can also be used independently of VS Code, for example by LLM agents or custom scripts.
   See :ref:`isaac_sim_app_python_server` for details on the wire protocol and programmatic usage.

|br| |hr|

VS Code Configuration Files
-----------------------------

The |isaac-sim_short| installation provides a ``.vscode`` workspace with a pre-configured environment under the following three files:

.. code-block:: bash

    .vscode/launch.json
    .vscode/settings.json
    .vscode/tasks.json

launch.json
**********************

This file provides three different configurations that can be executed using the ``Run & Debug`` section in VSCode.

- **Python: Current File**: Debug the currently open standalone Python file, should not be used with extension examples/code.
- **Python: Attach**: Attach to a running |isaac-sim_short| application for debugging purposes, most useful when running an interactive GUI application. See :ref:`isaac_sim_app_tutorial_advanced_attach_debugger` for usage information.
- **(Linux) isaac-sim** Run the main |isaac-sim_short| application with an attached debugger.

settings.json
**********************

This file sets the default Python executable that comes with |isaac-sim_short|:

.. literalinclude:: ../snippets/development_tools/vscode/settingsjson.py
    :language: python

As well as a configuration for ``"python.analysis.extraPaths"`` which by default includes all of the extensions that are provided by default. You can add additional paths here if needed.

tasks.json
**********************

This is a helper file that contains a task used to automatically setup the Python environment when using the ``Python: Current File`` option in ``Run & Debug``.

.. literalinclude:: ../snippets/development_tools/vscode/tasksjson.py
    :language: python

Once executed, the task generates the ``.standalone_examples.env`` file used by VS Code to launch the Python debug process.
Refer to :ref:`isaac_sim_app_tutorial_advanced_debug_vscode` for more details.
