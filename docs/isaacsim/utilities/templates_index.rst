..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_sim_templates:

============================
Templates
============================

We have many templates and template generator tools to help you get started with your projects.

- To scaffold a new extension from the terminal, use the :ref:`CLI Extension Templates <isaac_sim_cli_extension_templates>`. These cover Python, UI (with scene management and Examples Browser), C++, and OmniGraph extensions.
- You can use the Extension Template Generator to create a new extension projects: :ref:`isaac_sim_app_extension_template_generator`. These templates are structured to utilize |isaac-sim_short| libraries and built with robotics applications in mind.
- For extension using any combinations of C++, Python, OmniGraph, GUI elements, and more, refer to the :ref:`isaac_sim_app_vscode_extension_template_generator`.

.. toctree::
   :hidden:
   :maxdepth: 1

   cli_extension_templates
   extension_template_generator
   vscode_extension_template_generator

These are all for Extension-based projects. For standalone projects, simply browse through our Standalone Examples folder (``PATH_TO_ISAAC_SIM/standalone_examples``), and use them as a starting point.
