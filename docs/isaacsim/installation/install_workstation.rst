..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _Visual Studio Code: https://code.visualstudio.com/download


.. _isaac_sim_app_install_workstation:


Workstation Installation
========================================================

The workstation installation is recommended if you want to run Isaac Sim as a GUI application on Windows or Linux with a GPU.


.. seealso::

    * :ref:`isaac_sim_setup_differences`
    * :ref:`isaac_sim_setup_assets_content_pack`
    * :ref:`isaac_sim_launch_scripts` for additional scripts like the warmup script to pre-warm the shader cache before running |isaac-sim_short|.


.. _isaac_sim_ov_deprecation_warning:

.. note::

   * Omniverse Launcher, Nucleus Workstation, and Nucleus Cache will be deprecated and will no longer be available starting October 1, 2025.
   * For those who want to use Nucleus and Live Sync after October 1, 2025, please use :doc:`Enterprise Nucleus Server<nucleus:enterprise>`.
   * Nucleus Cache is replaced by :doc:`Hub Workstation Cache<utilities:cache/hub-workstation>`.
   * If you have issues installing :doc:`Hub Workstation Cache<utilities:cache/hub-workstation>` in Windows, run:

        .. code-block:: bat

            mklink /d %APPDATA%\ov %LOCALAPPDATA%\ov


.. _isaac_sim_compatibility_checker:

Isaac Sim Compatibility Checker
-----------------------------------

The **Isaac Sim Compatibility Checker** is a lightweight extension within |isaac-sim| that programmatically checks the above requirements and indicates which of them are valid, or not, for running |isaac-sim| on the machine.

The Compatibility Checker can be run either from a binary installation (Workstation, Container or Open-Source repository) or from Python packages (*pip* install), as follows:

* From binary installation (:ref:`Workstation <isaac_sim_install_workstation>` or `Open-Source repository <https://github.com/isaac-sim/IsaacSim>`_ setup):

    #. Install/build Isaac Sim according to the target setup workflow.
    #. Run the ``isaac-sim.compatibility_check.sh`` script on Linux, or the ``isaac-sim.compatibility_check.bat`` script on Windows.

* From Python packages (*pip* install):

    #. Follow the instructions to :ref:`install Isaac Sim from Python packages <isaac_sim_app_install_pip>`.

       .. hint::

            You can use ``pip install isaacsim[compatibility-check]`` to install a **minimal setup** for the Compatibility Checker extension instead of installing the full version.

    #. Run the ``isaacsim isaacsim.exp.compatibility_check`` command.

* From :ref:`Container <isaac_sim_app_install_container>`:

    * Run headless:

    .. code-block:: console

        $ docker run --entrypoint bash -it --gpus all --rm --network=host \
            nvcr.io/nvidia/isaac-sim:6.0.0 ./isaac-sim.compatibility_check.sh --/app/quitAfter=10 --no-window

    * Run as GUI:

    .. code-block:: console

        $ xhost +local:
        $ docker run --entrypoint bash -it --gpus all --rm --network=host \
            -e "PRIVACY_CONSENT=Y" \
            -v $HOME/.Xauthority:/isaac-sim/.Xauthority \
            -e DISPLAY \
            nvcr.io/nvidia/isaac-sim:6.0.0 ./isaac-sim.compatibility_check.sh

Verifying Compatibility
^^^^^^^^^^^^^^^^^^^^^^^^

The Compatibility Checker highlights, in color, the following states:

- **green** excellent
- **light-green** good
- **orange** enough, more is recommended
- **red** not enough/unsupported

The Compatibility Checker checks:

* **NVIDIA GPU:** Driver version, RTX-capable GPU, GPU VRAM
* **CPU, RAM and Storage:** CPU processor, Number of CPU cores, RAM, Available storage space
* **Others:** Operating system, Display

.. figure:: /images/isaac_sim_compatibility_checker.png
    :align: center
    :width: 900
    :alt: Isaac Sim Compatibility Checker examples

The **Test Kit** button, launches a minimal Kit application (in headless mode) and checks if its execution was successful or not, reporting the result on the panel next to it.


.. _isaac_sim_install_workstation:

Workstation Setup
------------------------------------------------------------------------------------------------

#. Review the requirements. See :ref:`isaac_sim_requirements`.
#. Optionally, for the full development install, make sure you have `Visual Studio Code`_ to view and debug source code.

|isaac-sim_short| Install and Launch
-------------------------------------

The |isaac-sim_short| app can be run directly from the command line with ``isaac-sim.bat`` or ``./isaac-sim.sh``.

The first run of the |isaac-sim_short| app takes some time to warm up the shader cache.

To run |isaac-sim_short| with a fresh config, use the ``--reset-user`` flag when running **Isaac Sim** in command line.

Nucleus, Cache, and Hub are not needed to run Isaac Sim.

1. Download the :ref:`isaac_sim_latest_release` of **Isaac Sim** for your platform to the ``Downloads`` folder.
2. Create a folder named ``isaacsim`` at ``c:/`` or at the root of your Linux environment.
3. Unzip the package to that folder.
4. Navigate to that folder.
5. To create a symlink to the **extension_examples** for the tutorials, run the ``post_install`` script. The script can be run at this stage or after installation.

    * On Linux, run ``./post_install.sh``.
    * On Windows, double click ``post_install.bat``.

.. _isaac_sim_setup_native_app_launcher:

6. Use one of the following methods to run **Isaac Sim**:

   * On Linux, run ``./isaac-sim.sh``.
   * On Windows, run ``isaac-sim.bat``.

7. The |isaac-sim_short| main app will start.

    A command window opens and runs scripts.

    You may need to login to Omniverse.

    The command window continues running scripts.

    Then the Isaac Sim GUI window opens with nothing displayed in it. It can take 5-10 minutes to complete.


8. Proceed to :ref:`isaac_sim_intro_quickstart_series` to begin the first Basic Tutorial.

.. note::

    There may be situations in which an internal conflict causes failures within the cache and configuration systems of Isaac Sim (for example, if there is a version mismatch between a source installation and a python package installation).
    If this occurs, the following may prove useful:

    - The ``--reset-user`` flag can be used to reset the user configuration to its default state.
    - The ``clear_caches.sh`` and ``.bat`` scripts can be used to clear the cache in Linux and Windows respectively.


Example Installation
--------------------------------

For example, from the command line, execute the following commands:

.. tab-set::
    .. tab-item:: Linux (x86_64)

        .. code-block:: bash

            mkdir ~/isaacsim
            cd ~/Downloads
            unzip "isaac-sim-standalone-6.0.0-linux-x86_64.zip" -d ~/isaacsim
            cd ~/isaacsim
            ./post_install.sh
            ./isaac-sim.sh

    .. tab-item:: Linux (aarch64)

        .. code-block:: bash

            mkdir ~/isaacsim
            cd ~/Downloads
            unzip "isaac-sim-standalone-6.0.0-linux-aarch64.zip" -d ~/isaacsim
            cd ~/isaacsim
            ./post_install.sh
            ./isaac-sim.sh

    .. tab-item:: Windows

        .. code-block:: bat

            mkdir C:\isaacsim
            cd %USERPROFILE%/Downloads
            tar -xvzf "isaac-sim-standalone-6.0.0-windows-x86_64.zip" -C C:\isaacsim
            cd C:\isaacsim
            post_install.bat
            isaac-sim.bat

Final load message example:

.. image:: /images/final_load.png
        :align: center
        :width: 550


Building from Source
--------------------------------

For developers who want to build Isaac Sim from source instead of using a pre-built binary, see the
`Isaac Sim GitHub README <https://github.com/isaac-sim/IsaacSim/blob/main/README.md>`_ for prerequisites,
build instructions, and advanced build options.

To build and deploy a Docker container from source, see the
`Docker Build Tools README <https://github.com/isaac-sim/IsaacSim/blob/main/tools/docker/README.md>`_.

