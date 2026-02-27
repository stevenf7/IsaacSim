
..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.





.. _isaac_sim_command_tool:

==================================
Omniverse Commands Tool Extension
==================================


.. _isaac_sim_command_tool_about:

About
=================

The :ref:`isaac_sim_command_tool` provides an interface that connects the UI operations in |omni| and |isaac-sim_short|
to their corresponding Python commands.

To access this extension, go to the top menu bar and click `Window > Commands`.

.. _isaac_sim_command_tool_interface:

User Interface
=================

.. figure:: /images/isaac_commands_tool.png
    :align: center
    :width: 400

Configuration Options
^^^^^^^^^^^^^^^^^^^^^^

Below are the options that are supported:

* **Search commands**: Search for all the commands that can be executed.
* **Clear History**: Clears history for all the commands that have been executed and show up in history.
* **Top-level commands**: Generate Python scripts corresponding to all top-level commands in history and copy to clipboard.
* **Selected commands**: Generate Python scripts corresponding to selected commands in history and copy to clipboard.


.. _isaac_sim_commands_tutorials:

Tutorials & Examples
=====================

The following example demonstrates a simple scenario of creating and transforming a cube followed by changing via the UI.
It then shows how to use the :ref:`isaac_sim_command_tool` to generate the corresponding Python command to replicate the scenario.

.. image:: /images/isim_4.5_full_ref_external_command_tool.webp
    :align: center
    :width: 100%