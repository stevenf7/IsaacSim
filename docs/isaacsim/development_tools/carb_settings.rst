..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_carb_settings:

=========================
Modify Carb Settings
=========================



:ref:`isaac_sim_glossary_carb` settings are used to configure default behaviors of Omniverse and |isaac-sim_short|. They can control a wide ranges of features, such as window properties, ROS versions,  browser folders, and more. You may wish to change these settings to suit your needs. Here we show the four ways to change the Carb settings in |isaac-sim_short|. 


For this tutorial, we will set a parameter inside extension ``isaacsim.my.extension`` named ``data.foo`` to the value ``True``. Replace these with your actual extension name, setting parameter, and value when you are working with your project.


Script Editor Snippet
=========================

You can temporarily and quickly change the Carb settings in the :doc:`Script Editor <extensions:ext_script-editor>`. This is useful for testing and debugging, and can be done while |isaac-sim_short| is open. The changes made this way will not be saved after you close the application, and relaunching the simulator will reset the settings.


.. literalinclude:: ../snippets/development_tools/carb_settings/script_editor_snippet.py
    :language: python

Command-Line Argument
=========================

You can launch |isaac-sim_short| with a command-line argument to change the Carb settings. The changes made this way will not be saved after you close the application, and relaunching the simulator without the arguments will reset the settings.

At the root of your |isaac-sim_short| installation, run the following command:

        .. tab-set::
            .. tab-item:: Linux

                .. code-block:: bash

                    ./isaac-sim.sh --/exts/isaacsim.my.extension/data/foo=True

            .. tab-item:: Windows

                .. code-block:: bash

                    .\isaac-sim.bat --/exts/isaacsim.my.extension/data/foo=True




Edit .toml File
=========================

For more permanent changes, you can edit the extension's `.toml` file. The changes made this way will persist after you close the application.


#. Navigate to the extension's folder. For example, if you are changing the settings for the `isaacsim.my.extension`, navigate to `<isaac-sim-root_dir>/exts/isaacsim.my.extension/config`.
#. Open the `.toml` file with a text editor, and add the following line to the file:

    .. code-block:: 

        [settings]
        exts."isaacsim.my.extension".data.foo = true


#. Launch |isaac-sim_short| to see the changes.





Customize .kit File
=========================


If you have multiple settings in multiple extensions that you want to change, you can edit the `.kit` file for your application. The changes made this way will persist after you close the application.

#. From the root of your |isaac-sim_short| installation, navigate to `<isaac-sim-root_dir>/apps/`. Locate the Kit experience app file you are using in this folder. By default, it is the `isaacsim.exp.full.kit`.  
#. Open the app file and add the following line to the file:

    .. code-block:: 

        [settings]
        exts."isaacsim.my.extension".data.foo = true

#. Launch |isaac-sim_short| to see the changes.