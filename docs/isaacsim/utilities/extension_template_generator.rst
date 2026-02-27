..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_extension_template_generator:

===========================================
Extension Template Generator
===========================================

The Extension Template Generator populate a UI-based extensions on your local machine. The available extension templates give a useful starting point for many |isaac-sim_short|
applications and are structured to help you learn how to build a custom UI tool that meets your needs.  


Getting Started
-------------------

To create and enable a new extension using the Extension Template Generator, follow these steps:

#. Open the extension generator by going to **Utilities > Generate Extension Templates** in the menu bar.

#. Select the :ref:`types of templates <isaac_sim_template_generator_options>` to expand the corresponding window. Fill in the fields as follow:

    - Extension Path: ``<Extension_Host_Dir>/my.extension.name``

    - Extension Name: ``my.extension.name``

    - Extension Description: ``My Extension Description``

#. Click Generate Extension. 

#. Navigate to **Window > Extensions** in the toolbar to open the Extensions Manager. Click the hamburger icon to the right of search bar, and then *Settings* in the sub-menu to open up the path table. If your selected ``<Extension_Host_Dir>`` is not already on the list, then scroll all the way down to the end in the "Extension Search Path". Click on the "+" button in the last row in the "edit" column, and type in the full path to the ``<Extension_Host_Dir>``. 

#. Search for your new extension. 

    - If your chosen ``<Extension_Host_Dir>`` was one of the default Extension Search Paths, you should find your extension under **NVIDIA** tab.
    
    - If you added a new Extension Search Path, you should find your extension under the **Third Party** tab.

#. Enable the extension. Verify that it appears in the menu bar on the top in |isaac-sim_short|.

#. Alternatively, you can enable extensions by command-line arguments when running |isaac-sim_short| from the terminal: ``./isaac-sim.sh --ext-folder {path_to_user_ext_folder} --enable {ext_directory_name}``. On Windows use ``python.bat`` instead of ``python.sh``.

#. Get familiar with the template code by reading the ``README.md`` file in the provided Python module.



.. image:: /images/isim_4.5_full_tut_gui_extension_template.webp
    :align: center



.. _isaac_sim_template_generator_options:

Template Options
-------------------

- **Load Scenario Template**: The :ref:`isaac_sim_app_tutorial_extension_templates_loaded_scenario` starts the user off with a simple UI that contains three buttons: *Load*, *Reset*, and *Run*.  This is meant to provide as clear a pathway as possible for the user to start writing code to directly affect the USD stage without having to understand much about the internal workings of the underlying simulator. 

- **Scripting Template**: The :ref:`isaac_sim_app_tutorial_extension_templates_scripting` demonstrates the implementation of a more advanced framework for programming script-like behavior from a UI-based extension in |isaac-sim|.  This template uses the same mechanics for loading and resetting the robot position as the "Load Scenario Template", but it implements the *Run* button as a script.

- **Configuration Tooling Template**: The :ref:`isaac_sim_app_tutorial_extension_templates_configuration_tooling` templates provides fundamental tools for asset configuration, such as finding ``Articulation`` on the stage and dynamically creates a UI frame through which the user may control each joint in the selected ``Articulation``.

- **UI Component Library Template**: The :ref:`isaac_sim_app_tutorial_extension_templates_ui_component_library` template demonstrate the usage of each ``UIElementWrapper``, such as the type of arguments and return values required for each callback function that can be attached to each ``UIElementWrapper``. 



More Resources
-------------------

For more detailed explanation regarding the template generator and each template can be found in :ref:`isaac_sim_app_tutorial_extension_templates`.

.. toctree::
    :hidden:
    :maxdepth: 1
   
    extension_templates_tutorial