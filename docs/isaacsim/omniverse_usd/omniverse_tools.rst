
..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _Command History: https://docs.omniverse.nvidia.com/extensions/latest/ext_command-history.html

.. _isaac_sim_app_omniverse_tools:


==========
Commands
==========

You can run many of the UI commands through ``omni.kit.commands.execute("CommandName", args)``. To find a list of available commands, and what args to use, open **Window > Commands**, then click on ``Search Commands``. On the window that appears, you will find an extensive list of all the commands available, and their respective documentation. Each command comes from a source Extension, and enabling/disabling extensions will change the list of available commands.

More information can be found `Command History`_

=======================
Registered Actions
=======================

An action is a pre-defined sequence of API and/or UI commands. Open the **Utilities > Registered Actions** to see a list of all the registered actions.  The actions are registered by the extensions, and enabling/disabling extensions will change the list of available actions. Double clicking on the action name will execute the action. 

You can also call these functions from Python scripts when using the ``onclick_action`` variable.

You can create your own actions using `Kit Action API <https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/guide/extensions_api.html#actions-api>`_:

.. literalinclude:: ../snippets/omniverse_usd/omniverse_tools/registered_actions.py
    :language: python