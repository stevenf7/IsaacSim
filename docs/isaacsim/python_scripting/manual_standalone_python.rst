..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaac_sim_python_environment:

===================================
Python Environment
===================================

This document will cover:

- Details about how running standalone Python scripts works.
- A short list of interesting/useful standalone Python scripts to try.
- Resources to develop Python scripts for |isaac-sim|, such as VSCode and Jupyter Notebook support.

Details: How ``python.sh`` works
#################################

.. note::
    - On Windows use python.bat instead of python.sh
    - The details of how python.sh works below are similar to how python.bat works

This script first defines the location of the apps folder so the contained .kit files can be located at runtime.

.. code-block:: bash

    # Get path to the script
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    # The apps directory is relative to where the script lives
    export EXP_PATH=$SCRIPT_DIR/apps

Then we source the |isaac-sim| Python environment so all extension interfaces can be loaded correctly.

.. code-block:: bash

    source ${SCRIPT_DIR}/setup_python_env.sh

The setup_python_env.sh script update/defined the following environment variables:

- ISAAC_PATH: Path to the main isaac folder
- PYTHONPATH: Paths to each extensions Python interfaces
- LD_LIBRARY_PATH: Paths to binary interfaces required to find symbols at runtime
- CARB_APP_PATH: path to the core |omni| kit executable

Finally, we execute the Python interpreter that is packaged with |omni|:

.. code-block:: bash

    python_exe=${PYTHONEXE:-"${SCRIPT_DIR}/kit/python/bin/python3"}
    ...
    $python_exe $@

.. _isaac_sim_python_simulationapp:

SimulationApp
#################################

The |simulation_app| provides convenience functions to manage the lifetime of a |isaac-sim| application.

.. |simulation_app| raw:: html

    <a href="../py/source/extensions/isaacsim.simulation_app/docs/index.html">SimulationApp Class</a>


Usage Example:
--------------

The following code provides a usage example for how SimulationApp can be used to create an app, step forward in time and then exit.

.. note::
    Any |omni| level imports **must** occur after the class is instantiated.
    Because APIs are provided by the extension/runtime plugin system, it must be loaded before they will be available to import.

.. important::
    When running headless:

    - Set ``"headless": True`` in the config when initializing ``SimulationApp``
    - Any calls that create/open a matplotlib window need to be commented out

.. literalinclude:: ../snippets/python_scripting/manual_standalone_python/usage_example.py
    :language: python

Details: How ``SimulationApp`` works
-------------------------------------

Although ``SimulationApp`` further configures the application and exposes APIs, there are some fundamental steps in any |omni| Kit-based implementation that must be executed.

The first is to get the carbonite framework.
Here the environment variables (e.g.: ``CARB_APP_PATH``, ``ISAAC_PATH`` and ``EXP_PATH``) were defined when running the `python.sh` script.

.. literalinclude:: ../snippets/python_scripting/manual_standalone_python/details_how_simulationapp_works.py
    :language: python

After loading the framework, it is possible to configure the start arguments before loading the application. For example:

.. literalinclude:: ../snippets/python_scripting/manual_standalone_python/details_how_simulationapp_works.py
    :language: python

And then start the application.

.. literalinclude:: ../snippets/python_scripting/manual_standalone_python/run_headless.py
    :language: python

Shutting down a running application is done by calling ``shutdown`` and then unloading the framework:

.. literalinclude:: ../snippets/python_scripting/manual_standalone_python/run_headless.py
    :language: python

.. _isaac_sim_python_additional_extensions:

Enabling additional extensions
------------------------------

There are two methods for adding additional extensions:

#. Under ``[dependencies]`` section in an experience file (e.g.: ``apps/isaacsim.exp.base.python.kit``):

    .. literalinclude:: ../snippets/python_scripting/manual_standalone_python/under_dependencies_section_in_an_experience_file_e.py
        :language: python

#.  From Python code:

    .. literalinclude:: ../snippets/python_scripting/manual_standalone_python/from_python_code.py
        :language: python

Standalone Example Scripts
#############################

Time Stepping
-------------

This sample shows how to start an |kit| Python app and then create callbacks which get called each rendering frame and each physics timestep. It also shows the different ways to step physics and  rendering.

The sample can be executed by running the following:

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.core.api/time_stepping.py

Load USD Stage
------------------

This sample demonstrates how to load a USD stage and start simulating it.

The sample can be executed by running the following, specify ``usd_path`` to a location on your nucleus server:

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.simulation_app/load_stage.py --usd_path /Isaac/Environments/Simple_Room/simple_room.usd


URDF Import
-----------

This sample demonstrates how to use the URDF Python API, configure its physics and then simulate it for a fixed number of frames.

.. |urdf_api| raw:: html

    <a href="../py/source/extensions/isaacsim.asset.importer.urdf/docs/index.html">URDF Python API</a>


The sample can be executed by running the following:

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.asset.importer.urdf/urdf_import.py


Change Resolution
------------------

This sample demonstrates how to change the resolution of the viewport at runtime.

The sample can be executed by running the following:

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.simulation_app/change_resolution.py

.. _isaac_sim_python_convert_assets:

Convert Assets to USD
---------------------

This sample demonstrates how to batch convert OBJ/STL/FBX assets to USD.

To execute it with sample data, run the following:

.. code-block:: bash

    ./python.sh standalone_examples/api/omni.kit.asset_converter/asset_usd_converter.py --folders standalone_examples/data/cube standalone_examples/data/torus

The input folders containing OBJ/STL/FBX assets are specified as argument
and it will output in terminal the path to converted USD files.

.. code-block:: bash

    Converting folder standalone_examples/data/cube...
    ---Added standalone_examples/data/cube_converted/cube_fbx.usd

    Converting folder standalone_examples/data/torus...
    ---Added standalone_examples/data/torus_converted/torus_stl.usd

This sample leverages Python APIs from the :doc:`Asset Importer <extensions:ext_asset-converter>` extension.

The details about the import options can be found :doc:`here <extensions:ext_asset-importer>`.


Livestream
------------------

This sample demonstrates how to enable livestreaming when running in native Python.

See :ref:`isaac_sim_setup_livestream_webrtc` for more information on running the client.

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.simulation_app/livestream.py

.. note::
    - Running livestream.py will not have all of the default |isaac-sim_short| extensions enabled. See :ref:`enabling additional extensions<isaac_sim_python_additional_extensions>` for more information.


