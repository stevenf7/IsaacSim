.. _Visual Studio Code: https://code.visualstudio.com/download
.. _Remote-SSH extension: https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh

.. _isaac_sim_app_tutorial_advanced_debug_vscode:

==================================
Debugging With Visual Studio Code
==================================

Learning Objectives
=======================

In this tutorial, we will go over

- Debugging a standalone Python script
- Debugging :ref:`isaac_sim_app_tutorial_advanced_python_debugging_docker`.
- Attaching to the ``omni.kit.debug.vscode_debugger`` extension to debug a running instance of |isaac-sim_short|

Standalone Python Scripts
=========================

.. note::
    Debugging standalone Python scripts is only supported on Linux currently


#. Open a terminal in the Isaac Sim installation root folder, then execute the following command: :code:`code .` This launches a new VS Code window and opens the current folder. You can also launch VS Code and open the folder.
#. Let's try debugging a simple script, open ``standalone_examples/api/isaacsim.simulation_app/hello_world.py`` and place a breakpoint.
#. Select the "Run" icon from the toolbar on the left, and ensure "Current File" is selected from the configuration dropdown menu.
#. Click "Start Debugging" or press F5 to launch the debugger. Pressing F10 will step line by line. You can mouse over to examine variable values.

   .. image:: /images/isim_4.5_full_ref_external_vscode_standalone_debug.png
        :align: center

#. Stop the current debugging session and let's try passing a command-line argument to our code in the "args" field of the .vscode/launch.json file. For example, here we change the default nucleus server

    .. code-block:: json
        :emphasize-lines: 13, 14

            {
                "name": "Python: Current File",
                "type": "python",
                "request": "launch",
                "program": "${file}",
                "console": "integratedTerminal",
                "env": {
                    "EXP_PATH": "${workspaceFolder}/apps",
                    "RESOURCE_NAME": "IsaacSim"
                },
                "python": "${workspaceFolder}/kit/python/bin/python3",
                "envFile": "${workspaceFolder}/.vscode/.standalone_examples.env",
                "preLaunchTask": "setup_python_env",
                "args": ["--/persistent/isaac/asset_root/default=\"omniverse://my_server\""]
            }

#. Add the following lines to ``hello_world.py`` and place a breakpoint on the ``print(server_check)`` line.

        .. literalinclude:: ../../snippets/utilities/debugging/tutorial_advanced_python_debugging/add_the_following_lines_to_hello_worldpy_and_place.py
            :language: python

#. After modifying and saving the launch.json, press F5 to launch the debugger.

#. Verify that the variable contains the server set in the ``args`` in ``launch.json``

   .. image:: /images/isim_4.5_full_ref_external_vscode_standalone_inspect.png
        :align: center

.. _isaac_sim_app_tutorial_advanced_python_debugging_docker:

Python Scripts Running in Docker
=================================

You can debug a Python script running headless in a docker container.

#. :ref:`Deploy the container<isaac_sim_setup_remote_headless_container>` and run it with an interactive Bash session.

#. In the running container, install :code:`debugpy`:

    .. code-block:: console

        # ./python.sh -m pip install debugpy

#. Create a new debugging configuration in VS Code with ("Run" menu > "Add Configuration..." > "Python Debugger" > "Remote Attach", choose: host "localhost" and port "5678").

#. Make sure the pathMappings are correct with :code:`/isaac-sim` in the container mapping to the folder where you have |isaac-sim_short| installed locally. These paths should match the configuration in your vscode :code:`launch.json`:

        .. literalinclude:: ../../snippets/utilities/debugging/tutorial_advanced_python_debugging/make_sure_the_pathmappings_are_correct_with_codeis.py
            :language: python

#. You must still use :code:`./python.sh` to run Python scripts, but to debug them you have to add :code:`-m debugpy --wait-for-client --listen 0.0.0.0:5678` after :code:`./python.sh` and before the Python file.

#. As an example, open :code:`standalone_examples/deprecated/api/isaacsim.core.api/time_stepping.py` in VS Code and set a breakpoint by clicking on the margin to the left of a line of code.

#. Now start run :code:`time_stepping.py` in the docker container with the complete debugging command:

    .. code-block:: console

        # ./python.sh -m debugpy --wait-for-client --listen 0.0.0.0:5678 standalone_examples/deprecated/api/isaacsim.core.api/time_stepping.py

#. Because of the :code:`--wait-for-client` flag, the script will not start right away.  You must attach the debugger first by selecting it in VS Code's debug window and pressing the Play button.

#. The script should start in the docker window, and stop at the breakpoint inside VS Code.

.. note::
    If the path mappings are incorrect you will not be able to set breakpoints or step through code.

.. _isaac_sim_app_tutorial_advanced_attach_debugger:

Attaching the Debugger to a Running App
========================================

To debug a script you are already running, use the VS Code Debugger extension.

#. Launch Isaac Sim, and from the top toolbar, select Window > Extensions. Then search for "vscode" and click the Enable button for the ``omni.kit.debug.vscode`` extension.
   By default, the status will show "VS Code Debugger Unattached" in red text.

   .. image:: /images/isim_4.5_full_ref_external_vscode_debug_extension.png
        :align: center

#. Then launch VS Code, and select the "Run" icon from the toolbar on the left.
#. From the configuration menu, select "Python: Attach (windows-x86_64/linux-x86_64) and click the green arrow to start debugging.
#. Notice that the status in Isaac Sim changes to "VS Code Debugger Attached" in blue text.

   .. image:: /images/isim_4.5_full_ref_external_vscode_debug_attach.png
        :align: center

#. You can now return to your Python file in VS Code and add breakpoints to debug, as described above.

.. note::
    To configure the host and port used for debugging, the following command-line arguments can be provided

    .. code-block::

        --/exts/omni.kit.debug.python/host="127.0.0.1"
        --/exts/omni.kit.debug.python/port=3000

    These should match the configuration in your vscode ``launch.json``

        .. literalinclude:: ../../snippets/utilities/debugging/tutorial_advanced_python_debugging/you_can_now_return_to_your_python_file_in_vs_code_.py
            :language: python

Summary
========

In this tutorial, we covered
#. Debugging a standalone Python script
#.  Attaching the vscode debugger to a running instance of |isaac-sim_short|

Further Learning
^^^^^^^^^^^^^^^^^^^^^^

For more details about how the vscode integration works, refer to :ref:`isaac_sim_app_vscode`

