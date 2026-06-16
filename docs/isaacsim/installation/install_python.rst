..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_app_install_python:


Python Environment Installation
========================================================

This section presents the following contents:

* :ref:`isaac_sim_app_install_pip` in a (virtual) Python environment
* Using the Isaac Sim :ref:`isaac_sim_install_python_default`

.. _isaac_sim_app_install_pip:

Install Isaac Sim using PIP
============================================

.. note::

    * |isaac-sim_short| requires **Python 3.12**. Visit the `Python download page <https://www.python.org/downloads/>`_ to get a suitable version.
    * On Linux, GLIBC 2.35+ (``manylinux_2_35_x86_64``) version compatibility is required for pip to discover and install the Python packages. Check the GLIBC version using the command ``ldd --version``.
    * On Windows, it may be necessary to `enable long path <https://pip.pypa.io/warnings/enable-long-paths>`_ support to avoid installation errors due to OS limitations.

.. note::

    **Building Isaac Sim pip wheels from source.** To produce your own ``.whl`` files (for example, to test a local modification or a specific branch) instead of installing the pre-built wheels below, see the `PIP Packages <https://github.com/isaac-sim/IsaacSim/blob/main/README.md#pip-packages>`_ section of the Isaac Sim GitHub README.

|isaac-sim_short| provides several Python `namespace packages <https://packaging.python.org/en/latest/guides/packaging-namespace-packages/>`_
that allow you to compose an |isaac-sim_short| app by parts using a Python package manager (for example: `pip <https://pip.pypa.io/>`_).
The following tables list the available *Isaac Sim - Python packages*.

.. Use the following command to update the table:
..    cat python_packages.toml | grep -e "\[isaacsim" -e pyproject.description

.. list-table:: Main Python packages
    :widths: auto
    :header-rows: 1

    * - Package
      - Description
    * - ``isaacsim``
      - A metapackage that defines optional dependencies for installing some or all of the other Python packages
    * -
      -
    * - ``isaacsim-kernel``
      - Isaac Sim kernel
    * - ``isaacsim-app``
      - Isaac Sim components for application setup
    * - ``isaacsim-asset``
      - Isaac Sim components for asset import, creation and management
    * - ``isaacsim-benchmark``
      - Isaac Sim components for benchmarking
    * - ``isaacsim-code-editor``
      - Isaac Sim components for scripting and code edition
    * - ``isaacsim-core``
      - Isaac Sim core extensions and APIs
    * - ``isaacsim-cortex``
      - Isaac Sim components to enable the Cortex decision framework for intelligent robot behavior
    * - ``isaacsim-example``
      - Isaac Sim examples
    * - ``isaacsim-gui``
      - Isaac Sim components for the graphical user interface (GUI)
    * - ``isaacsim-replicator``
      - Isaac Sim components to enable the Replicator framework for synthetic data generation pipelines and services
    * - ``isaacsim-rl``
      - Isaac Sim components for reinforcement learning
    * - ``isaacsim-robot``
      - Isaac Sim's robot models and APIs
    * - ``isaacsim-robot-motion``
      - Isaac Sim components for motion generation pipelines and algorithms
    * - ``isaacsim-robot-setup``
      - Isaac Sim components for robot setup
    * - ``isaacsim-ros2``
      - Isaac Sim components for ROS 2 system integration
    * - ``isaacsim-sensor``
      - Isaac Sim components to simulate sensors
    * - ``isaacsim-storage``
      - Isaac Sim components for storage system
    * - ``isaacsim-template``
      - Isaac Sim templates
    * - ``isaacsim-test``
      - Isaac Sim components for testing
    * - ``isaacsim-utils``
      - Isaac Sim utilities

.. list-table:: Python packages that cache all the Omniverse extension dependencies for |isaac-sim_short|
    :widths: auto
    :header-rows: 1

    * - Package
      - Description
    * - ``isaacsim-extscache-kit``
      - Kit extensions cache for Isaac Sim
    * - ``isaacsim-extscache-kit-sdk``
      - Kit-SDK extensions cache for Isaac Sim
    * - ``isaacsim-extscache-physics``
      - Physics extensions cache for Isaac Sim

Installation Using PIP
---------------------------

#. Create and activate the virtual environment (optional, but highly recommended):

    .. tab-set::
        .. tab-item:: venv module
            :sync: python_venv

            .. tab-set::
                .. tab-item:: Ubuntu
                    :sync: python_ubuntu

                    .. code-block:: text

                        python3.12 -m venv env_isaacsim
                        source env_isaacsim/bin/activate

                .. tab-item:: Windows
                    :sync: python_windows

                    .. code-block:: batch

                        python3.12 -m venv env_isaacsim
                        env_isaacsim\Scripts\activate

        .. tab-item:: Conda
            :sync: python_conda

            .. code-block:: text

                conda create -n env_isaacsim python=3.12
                conda activate env_isaacsim

    Make sure pip is updated (``pip install --upgrade pip``) after activating the environment and before proceeding with installation.

#. Install PyTorch compiled with CUDA enabled:

    .. tab-set::
        .. tab-item:: CUDA 12

            .. code-block:: text

                pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128

        .. tab-item:: CUDA 13

            .. code-block:: text

                pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu130

#. Install *Isaac Sim - Python packages*:

    .. tab-set::
        .. tab-item:: (Virtual) Python environment
            :sync: env_native

            .. tab-set::
                .. tab-item:: Full Isaac Sim
                    :sync: package_full

                    .. code-block:: text

                        pip install isaacsim[all,extscache]==6.0.1.0 --extra-index-url https://pypi.nvidia.com

                .. tab-item:: Isaac Sim Bundle
                    :sync: package_bundle

                    .. code-block:: text

                        pip install isaacsim[BUNDLE]==6.0.1.0 --extra-index-url https://pypi.nvidia.com

                    .. list-table:: Available Bundles
                        :widths: auto
                        :header-rows: 1

                        * - Bundle
                          - Description
                        * - ``all``
                          - Install all the main Python packages
                        * - ``extscache``
                          - Install the packages that cache the Omniverse extension dependencies
                        * - ``compatibility-check``
                          - Install the packages to run the Isaac Sim Compatibility Checker extension
                        * - ``ros2``
                          - Install all the packages that enable ROS 2 system integration

                .. tab-item:: Specific Isaac Sim Package
                    :sync: package_specific

                    .. code-block:: text

                        pip install isaacsim-PACKAGE_SUBNAME==6.0.1.0 --extra-index-url https://pypi.nvidia.com

        .. tab-item:: Notebook (for example: Jupyter, Colab)
            :sync: env_notebook

            .. tab-set::
                .. tab-item:: Full Isaac Sim
                    :sync: package_full

                    .. code-block:: text

                        !pip install isaacsim[all,extscache]==6.0.1.0 --extra-index-url https://pypi.nvidia.com

                .. tab-item:: Isaac Sim Bundle
                    :sync: package_bundle

                    .. code-block:: text

                        !pip install isaacsim[BUNDLE]==6.0.1.0 --extra-index-url https://pypi.nvidia.com

                    .. list-table:: Available Bundles
                        :widths: auto
                        :header-rows: 1

                        * - Bundle
                          - Description
                        * - ``all``
                          - Install all the main Python packages
                        * - ``extscache``
                          - Install the packages that cache the Omniverse extension dependencies
                        * - ``compatibility-check``
                          - Install the packages to run the Isaac Sim Compatibility Checker extension
                        * - ``ros2``
                          - Install all the packages that enable ROS 2 system integration

                .. tab-item:: Specific Isaac Sim Package
                    :sync: package_specific

                    .. code-block:: text

                        !pip install isaacsim-PACKAGE_SUBNAME==6.0.1.0 --extra-index-url https://pypi.nvidia.com

    The installation path can be queried with the command ``pip show isaacsim``.

Running Isaac Sim
---------------------------

.. note::

    You must agree and accept the :doc:`Omniverse License Agreement </common/licenses>` (EULA) to use Isaac Sim.
    The EULA can be accepted in two ways, through system environment variables or by responding to a prompt:

    .. tab-set::
        .. tab-item:: Prompting at Runtime

            The first time ``isaacsim`` is imported, a prompt asks you to accept the EULA at runtime.
            After the EULA is accepted, you will not see it again.
            If the EULA is not accepted, the execution will be terminated.

            .. code-block:: ini

                By installing or using Omniverse Kit, I agree to the terms of NVIDIA OMNIVERSE LICENSE AGREEMENT (EULA)
                in https://docs.omniverse.nvidia.com/platform/latest/common/NVIDIA_Omniverse_License_Agreement.html

                Do you accept the EULA? (Yes/No):

        .. tab-item:: Environment Variable

            By setting the ``OMNI_KIT_ACCEPT_EULA`` environment variable to ``YES``, ``Y`` or ``1`` (case insensitive), the interpreter will not prompt for EULA acceptance at runtime.

            .. tab-set::
                .. tab-item:: Command line Interface

                    .. tab-set::
                        .. tab-item:: Ubuntu
                            :sync: python_ubuntu

                            .. code-block:: bash

                                export OMNI_KIT_ACCEPT_EULA=YES

                        .. tab-item:: Windows
                            :sync: python_windows

                            .. code-block:: batch

                                set OMNI_KIT_ACCEPT_EULA=YES

                .. tab-item:: Python Script

                    Add the following statements at the beginning of the script or notebook cell before importing ``isaacsim``:

                    .. literalinclude:: ../snippets/installation/install_python/running_isaac_sim.py
                        :language: python

.. warning::

   * Some Python packages required by some |isaac-sim_short| extensions or examples may not be included as dependencies.
     However, it is possible to install them using the command ``pip install DEPENDENCY_NAME``.
   * On |spark_short| / :ref:`aarch64 architecture<isaac_sim_requirements_aarch64_limitations>`, it may be necessary to preload (``LD_PRELOAD``) the ``libgomp`` shared library for some modules to be loaded.
     When the ``isaacsim`` package is imported, a check will be performed, after which a message providing preload instructions may be displayed.

Launching Isaac Sim Experiences
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. hint::

    To launch the (standard) Isaac Sim app, run the ``isaacsim`` command in the terminal.

The installation registers a Python entry point (``isaacsim``) that allows launching experience (``.kit``) files.
The experience file can be defined by its:

* absolute or relative file path
* file name, with/without ``.kit`` file extension (search paths: ``isaacsim/apps``, ``omni/apps``)

    .. code-block:: bash

        isaacsim path/to/experience_file.kit [arguments]

The following table lists the most common *Isaac Sim - Python packages* commands to launch experiences:

.. list-table::
    :widths: 40 60
    :header-rows: 1

    * - Command
      - Description
    * - ``isaacsim isaacsim.exp.compatibility_check``
      - Compatibility check: a lightweight extension that programmatically checks for Isaac Sim requirements.
    * - ``isaacsim isaacsim.exp.full``
      - Standard |isaac-sim_short| app, as it is executed from binary. It is the default experience if no experience file is specified (for example: ``isaacsim``).
    * - ``isaacsim isaacsim.exp.full.streaming --no-window``
      - Headless livestreaming |isaac-sim_short| (WebRTC protocol). Connect using the native :ref:`WebRTC Streaming Client <isaac_sim_setup_livestream_webrtc>`. See :ref:`isaac_sim_manual_livestream_client` for all streaming options.


Running Python Scripts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run the following command to execute a Python script in the (virtual) environment:

    .. code-block:: bash

        python path/to/script.py

Running in Interactive Interpreter or Notebooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When running in interactive interpreter or Notebooks (for example: Jupyter, Colab), you must import the ``isaacsim`` package  to access the :ref:`isaac_sim_python_simulationapp` class.
For convenience, the ``isaacsim`` package exposes that class (implemented in the ``isaacsim.simulation_app`` extension).

    .. tab-set::
        .. tab-item:: Using *isaacsim*

            .. literalinclude:: ../snippets/installation/install_python/perform_any_isaac_sim_omniverse_imports_after_inst.py
                :language: python

        .. tab-item:: Using *isaacsim.simulation_app*

            .. literalinclude:: ../snippets/installation/install_python/perform_any_isaac_sim_omniverse_imports_after_inst.py
                :language: python

    .. note::

        Calling the ``SimulationApp.close`` method on Notebooks causes a kernel interruption and termination.

Generating VS Code Settings
-------------------------------

Because of the structure resulting from the installation, VS Code IntelliSense (code completion, parameter info, and member lists) will not work by default.
To set it up (define the search paths for import resolution, the path to the default Python interpreter, and other settings), for a given workspace folder, run the following command:

    .. code-block:: bash

        python -m isaacsim --generate-vscode-settings

    .. note::

        The command will generate a ``.vscode/settings.json`` file in the workspace folder.
        If the file already exists, it will be overwritten (a confirmation prompt will be shown first).

|

.. _isaac_sim_install_python_default:

Default Python Environment
===================================================

It is possible to run |isaac-sim_short| natively from Python rather than as a standalone executable.
This provides more low-level control over how to initialize, setup, and manage an |omni| application.
|isaac-sim_short| provides a built-in Python 3.12 environment that packages can use, similar to a
system-level Python install. We recommend using this Python environment when running the Python
scripts.

Run the following from the |isaac-sim_short| root folder to start a Python script in this
environment:

    .. code-block:: bash

        ./python.sh path/to/script.py

.. note::
    - On Windows use ``python.bat`` instead of ``python.sh``.
    - If you need to install additional packages using *pip*, run the following:

        .. code-block:: bash

            ./python.sh -m pip install name_of_package_here


See the :ref:`isaac_sim_python_environment` manual for more details about ``python.sh``.

.. _isaac_sim_install_python_jupyter_notebook:

Jupyter Notebook Setup
---------------------------

Jupyter Notebook is supported on Linux only.

Jupyter Notebooks that use |isaac-sim_short| can be executed as follows:

    .. code-block:: bash

        ./jupyter_notebook.sh path/to/notebook.ipynb

The first time you run ``jupyter_notebook.sh``, it installs the Jupyter Notebook package
into the |isaac-sim_short| Python environment, this can take several minutes.

See the :ref:`isaac_sim_app_jupyter_notebook` documentation for more details.

.. _isaac_sim_install_python_vscode:

Visual Studio Code Support
---------------------------

Using Visual Studio Code for tutorials and examples is recommended.

The |isaac-sim_short| package provides a ``.vscode`` workspace with a pre-configured environment
that provides the following:

- Launch configurations for running in standalone Python mode or the interactive GUI
- An environment for Python auto-complete

You can open this workspace by opening the main |isaac-sim_short| package folder in Visual Studio
Code (VS Code).


See the :ref:`isaac_sim_app_vscode` documentation for details about the VS Code workspace.

.. _isaac_sim_install_python_docker:

Advanced: Running in Docker
------------------------------

Start the Docker container following the instructions in :ref:`isaac_sim_setup_remote_headless_container`
up to step 7.

After the |isaac-sim_short| container is running, you can run a Python script or Jupyter Notebook
from the sections above.

.. note::
    - You can install additional packages using *pip*:

      .. code-block:: bash

         ./python.sh -m pip install name_of_package_here

    - See :ref:`isaac_sim_save_docker_image` for committing the image and making the Python setup
      installation persistent.
