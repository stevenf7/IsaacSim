..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _NGC API Key: https://docs.nvidia.com/ngc/ngc-overview/index.html#generating-api-key
.. _NVIDIA GPU Driver: https://www.nvidia.com/en-us/drivers/unix
.. _Managing access keys (console): https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html#Using_CreateAccessKey
.. _AWS Secrets Manager: https://aws.amazon.com/secrets-manager
.. _Post-installation steps for Linux: https://docs.docker.com/engine/install/linux-postinstall
.. _PuTTYgen: https://www.puttygen.com

.. _isaac_sim_setup_faq:


Setup Tips
=======================================

.. _isaac_sim_setup_native_modes:

.. dropdown:: |isaac-sim_short| Modes

    .. rubric:: |isaac-sim_short| Full App

    This is the main windowed |isaac-sim_short| application.

    This mode includes all Isaac Sim extensions and most of them are enabled by default.

    .. _isaac_sim_setup_native_webrtc:

    .. rubric:: |isaac-sim_short| Full Streaming App (using |isaac-sim_short| WebRTC Streaming Client)

    This is a headless version of |isaac-sim_short|. It can be run remotely on a workstation with an RTX GPU
    and accessed from the :ref:`isaac_sim_setup_livestream_webrtc` app available for Linux, Windows and macOS,
    or from a :ref:`web-based viewer <isaac_sim_web_streaming_client>` deployed via Docker Compose.

    This mode includes all Isaac Sim extensions and most of them are enabled by default.

    .. rubric:: |isaac-sim_short| Python

    This is a mini app to run the Python samples.

    * See :ref:`isaac_sim_python_environment`.

    .. _isaac_sim_launch_scripts:

    .. rubric:: |isaac-sim_short| Launch Scripts

    .. tab-set::
        .. tab-item:: Linux

            .. list-table:: :ref:`isaac_sim_launch_scripts` that can be run from the |isaac-sim_short| package on Linux
                :widths: auto
                :header-rows: 1

                * - Script
                  - Description
                * - ``isaac-sim.sh``
                  - |isaac-sim_short| full app
                * - ``isaac-sim.streaming.sh``
                  - |isaac-sim_short| headless full app with |isaac-sim_short| WebRTC Streaming Client service
                * - ``isaac-sim.fabric.sh``
                  - |isaac-sim_short| full app with *Fabric* enabled
                * - ``isaac-sim.xr.vr.sh``
                  - |isaac-sim_short| base app with XR and VR enabled
                * - ``jupyter_notebook.sh``
                  - |isaac-sim_short| Jupyter Notebook executable
                * - ``python.sh``
                  - |isaac-sim_short| Python executable
                * - ``setup_python_env.sh``
                  - |isaac-sim_short| Python environment setup
                * - ``clear_caches.sh``
                  - Script to clear local caches
                * - ``post_install.sh``
                  - Script to be run once after install
                * - ``warmup.sh``
                  - Script to warm up the shader cache

        .. tab-item:: Windows

            .. list-table:: :ref:`isaac_sim_launch_scripts` that can be run from the |isaac-sim_short| package on Windows
                :widths: auto
                :header-rows: 1

                * - Script
                  - Description
                * - ``isaac-sim.bat``
                  - |isaac-sim_short| full app
                * - ``isaac-sim.streaming.bat``
                  - |isaac-sim_short| headless full app with |isaac-sim_short| WebRTC Streaming Client service
                * - ``isaac-sim.fabric.bat``
                  - |isaac-sim_short| full app with *Fabric* enabled
                * - ``isaac-sim.xr.vr.bat``
                  - |isaac-sim_short| base app with XR and VR enabled
                * - ``python.bat``
                  - |isaac-sim_short| Python executable
                * - ``setup_python_env.bat``
                  - |isaac-sim_short| Python environment setup
                * - ``clear_caches.bat``
                  - Script to clear local caches
                * - ``post_install.bat``
                  - Script to be run once after install
                * - ``warmup.bat``
                  - Script to warm up the shader cache

        .. tab-item:: Docker (x86_64)

            .. list-table:: :ref:`isaac_sim_launch_scripts` that can be run from the |isaac-sim_short| container
                :widths: auto
                :header-rows: 1

                * - Script
                  - Description
                * - ``runapp.sh``
                  - Script to run |isaac-sim_short| as a windowed app
                * - ``runheadless.sh``
                  - Script to run |isaac-sim_short| headless with |isaac-sim_short| WebRTC Streaming Client service
                * - ``jupyter_notebook.sh --allow-root``
                  - |isaac-sim_short| Jupyter Notebook executable
                * - ``python.sh``
                  - |isaac-sim_short| Python executable
                * - ``setup_python_env.sh``
                  - |isaac-sim_short| Python environment setup
                * - ``clear_caches.sh``
                  - Script to clear local caches
                * - ``warmup.sh``
                  - Script to warm up the shader cache

        .. tab-item:: Docker (aarch64)

            .. list-table:: :ref:`isaac_sim_launch_scripts` that can be run from the |isaac-sim_short| container
                :widths: auto
                :header-rows: 1

                * - Script
                  - Description
                * - ``runapp.sh``
                  - Script to run |isaac-sim_short| as a windowed app
                * - ``python.sh``
                  - |isaac-sim_short| Python executable
                * - ``setup_python_env.sh``
                  - |isaac-sim_short| Python environment setup
                * - ``clear_caches.sh``
                  - Script to clear local caches
                * - ``warmup.sh``
                  - Script to warm up the shader cache

.. dropdown:: |isaac-sim_short| CLI Launch flags

    .. list-table:: Flags that can be used to launch |isaac-sim_short|
        :widths: auto
        :header-rows: 1

        * - Flag
          - Description
        * - ``--/path/to/key=value``
          - instruct to supersede configuration key with given value.
        * - ``--clear-cache``
          - Clear $cache folder before starting.
        * - ``--clear-data``
          - Clear $data folder before starting.
        * - ``--disable-ext-startup``
          - Do not startup any extensions, only load them.
        * - ``--enable EXT_ID``
          - Enable extension (short hand to add extension to enabled list).
        * - ``--exec SCRIPT ARGS..., -e SCRIPT ARGS...``
          - execute a console command on startup
        * - ``--ext-folder PATH``
          - Add extension folder to look extensions in.
        * - ``--ext-path PATH``
          - Add direct extension path (allows adding single extension).
        * - ``--ext-precache-mode``
          - Only resolve and download all extensions, exit right after.
        * - ``--help``, ``-h``
          - this help message
        * - ``--info``, ``-v``
          - show info log output in console
        * - ``--list-exts``
          - List all local extensions and quit.
        * - ``--list-registry-exts``
          - List all registry extensions and quit.
        * - ``--merge-config, -m=<file>``
          - merge configuration file.
        * - ``--portable``
          - Enable portable mode. Portable root defaults to ${kit} path.
        * - ``--portable-root PATH``
          - Enable portable mode and place data/cache/logs folders there.
        * - ``--publish EXT_ID``
          - Publish extension to the registry and quit.
        * - ``--publish-overwrite``
          - Allow overwriting extension in registry when publishing.
        * - ``--reset-user``
          - Do not load persistent settings from user.config file.
        * - ``--unpublish EXT_ID``
          - Unpublish extension from the registry and quit.
        * - ``--update-exts``
          - Look for latest versions in extension registry and update for all enabled extensions.
        * - ``--verbose``, ``-vv``
          - show verbose log output in console
        * - ``--wait-debugger``, ``-d``
          - Suspend execution and wait for debugger to attach.


.. dropdown:: Kit Extension Registry

    .. _isaac_sim_setup_kit_registry:

    .. rubric:: Kit Extension Registry

    .. note::

        As of Isaac Sim 6.0, Kit extension registries are now managed automatically by the Kit SDK. If you have custom ``.kit`` files or configuration overrides that specify Kit registry settings, you should remove them.

    **Migration for Isaac Sim 6.0 and later:** If you have custom ``.kit`` configuration files or user configuration overrides that include Kit registry settings under ``[settings.exts."omni.kit.registry.nucleus"]``, we recommend removing them for compatibility.

    Kit SDK now handles registry configuration automatically, and custom registry overrides are no longer needed. Removing these settings ensures compatibility with Isaac Sim 6.0 and later versions.

    To add custom registries, go to **Window** > **Extensions** and add the new custom registry in the **Extension Registries** section.


.. dropdown:: Differences Between Workstation And Docker

    .. _isaac_sim_setup_differences:

    .. rubric:: Differences Between Workstation And Docker

    There are two methods to install |isaac-sim_short|:

    #. :ref:`isaac_sim_app_install_workstation` is recommended for **Workstation** users.
    #. :ref:`isaac_sim_app_install_container` is recommended for remote headless servers or the Cloud using a **Docker** container.

    .. note::

        Here are the main differences between Workstation and Docker installations:

        * The |isaac-sim_short| Docker container does not include Nucleus and will access assets directly from the Cloud by default.
        * The recommnded root folder of the workstation package is at **~/isaacsim** or **C:\\isaacsim**, while the root folder in the Docker container is **/isaac-sim**.
        * See :ref:`isaac_sim_misc_paths` for differences in common paths.



.. dropdown:: Common Path Locations

    .. _isaac_sim_misc_paths:

    .. _isaac_sim_paths_app:

    .. rubric:: Location for |isaac-sim_short| app

    .. tab-set::
        .. tab-item:: Linux

            .. code-block:: bash

                ~/isaacsim

        .. tab-item:: Windows

            .. code-block:: bat

                C:\isaacsim

        .. tab-item:: Docker

            .. code-block:: bash

                /isaac-sim

    .. _isaac_sim_paths_logs:

    .. rubric:: Location for |isaac-sim_short| logs

    .. tab-set::
        .. tab-item:: Linux

            .. code-block:: bash

                ~/.nvidia-omniverse/logs/Kit/Isaac-Sim

        .. tab-item:: Windows

            .. code-block:: bat

                %userprofile%\.nvidia-omniverse\logs\Kit\Isaac-Sim

        .. tab-item:: Docker

            .. code-block:: bash

                /root/.nvidia-omniverse/logs/Kit/Isaac-Sim

    .. _isaac_sim_paths_shadercache:

    .. rubric:: Location for |isaac-sim_short| shader cache

    .. tab-set::
        .. tab-item:: Linux

            .. code-block:: bash

                ~/.cache/ov/Kit

        .. tab-item:: Windows

            .. code-block:: bat

                %userprofile%\AppData\Local\ov\cache\Kit

        .. tab-item:: Docker

            .. code-block:: bash

                /root/.cache/ov/Kit

    .. _isaac_sim_paths_configs:

    .. rubric:: Location for |isaac-sim_short| configs

    .. tab-set::
        .. tab-item:: Linux

            .. code-block:: bash

                ~/.local/share/ov/data/Kit/Isaac-Sim

        .. tab-item:: Windows

            .. code-block:: bat

                %userprofile%\AppData\Local\ov\data\Kit\Isaac-Sim

        .. tab-item:: Docker

            .. code-block:: bash

                /root/.local/share/ov/data/Kit/Isaac-Sim




.. dropdown:: Multi-GPU

    .. _multi_gpu_ref:

    .. rubric:: Multi-GPU

    Multi-GPU support and specific GPU settings can be activated using the usual configurations methods, either by command line ...

    .. code-block:: console

            ./isaac-sim.sh --/renderer/multiGpu/enabled=true

    ...or by kit configuration in Python...

    .. literalinclude:: ../snippets/installation/install_faq/refisaac_sim_app_install_container_is_recommended_.py
        :language: python

    Some useful settings include, but are not limited to....

    * ``/renderer/multiGpu/Enabled=true`` enables multiple GPUs for rendering
    * ``/renderer/multiGpu/autoEnable=true`` enables multi GPU rendering if available
    * ``/renderer/multiGpu/maxGpuCount=2`` sets the maximum number of GPUs to be allocated for rendering
    * ``/renderer/activeGpu=0`` sets the active GPU according to `nvidia-smi`

    .. for further details, review :ref:`RTX-renderer`.



.. dropdown:: Assets

    .. _isaac_sim_setup_assets_content_pack:

    .. rubric:: Local Assets Packs

    |isaac-sim_short| :ref:`isaac_sim_setup_assets_content_pack` are available to be used locally and in an air-gapped environment.

    1. Download the **Isaac Sim Assets Complete Pack** from the :ref:`isaac_sim_latest_release` section.
       The example below shows using Aria2 to resume interrupted downloads and verify each file with its MD5 checksum.

    .. tab-set::
        .. tab-item:: Linux

            .. code-block:: bash

                sudo apt install aria2
                cd ~/Downloads
                aria2c -c --checksum=md5=0d1d98f46780d13bf83779c79360f883 "https://downloads.isaacsim.nvidia.com/isaac-sim-assets-complete-6.0.0.001.zip"
                aria2c -c --checksum=md5=9a03f3a32a2962fce4f464fc784a9da9 "https://downloads.isaacsim.nvidia.com/isaac-sim-assets-complete-6.0.0.002.zip"
                aria2c -c --checksum=md5=37ee649b2b35c6bc72958f12e625f862 "https://downloads.isaacsim.nvidia.com/isaac-sim-assets-complete-6.0.0.003.zip"

        .. tab-item:: Windows

            .. code-block:: bat

                winget install --id=aria2.aria2 -e
                cd %USERPROFILE%/Downloads
                aria2c -c --checksum=md5=0d1d98f46780d13bf83779c79360f883 "https://downloads.isaacsim.nvidia.com/isaac-sim-assets-complete-6.0.0.001.zip"
                aria2c -c --checksum=md5=9a03f3a32a2962fce4f464fc784a9da9 "https://downloads.isaacsim.nvidia.com/isaac-sim-assets-complete-6.0.0.002.zip"
                aria2c -c --checksum=md5=37ee649b2b35c6bc72958f12e625f862 "https://downloads.isaacsim.nvidia.com/isaac-sim-assets-complete-6.0.0.003.zip"

    If Aria2 reports a checksum failure, remove the failed part and rerun the command for that file before combining the parts.

    2. Unzip packages to a folder.

    .. tab-set::
        .. tab-item:: Linux

            .. code-block:: bash

                mkdir ~/isaacsim_assets
                cd ~/Downloads
                cat isaac-sim-assets-complete-6.0.0.001.zip isaac-sim-assets-complete-6.0.0.002.zip isaac-sim-assets-complete-6.0.0.003.zip > isaac-sim-assets-complete-6.0.0.zip
                unzip "isaac-sim-assets-complete-6.0.0.zip" -d ~/isaacsim_assets

        .. tab-item:: Windows

            .. code-block:: bat

                mkdir C:\isaacsim_assets
                cd %USERPROFILE%/Downloads
                copy /b isaac-sim-assets-complete-6.0.0.001.zip + isaac-sim-assets-complete-6.0.0.002.zip + isaac-sim-assets-complete-6.0.0.003.zip isaac-sim-assets-complete-6.0.0.zip
                tar -xvzf "isaac-sim-assets-complete-6.0.0.zip" -C C:\isaacsim_assets

    .. note::

        All three assets packs are required and they need to be combined into a single root folder (for example, *~/isaacsim_assets/Assets/Isaac/6.0*).

        This root folder (*~/isaacsim_assets/Assets/Isaac/6.0*) must contain both the *NVIDIA* and *Isaac* folders.


    3. Follow the instructions to :ref:`setup Isaac Sim<isaac_sim_install_workstation>`, then edit the **isaacsim.exp.base.kit** file.

    .. tab-set::
        .. tab-item:: Linux

            Edit the **/home/<username>/isaacsim/apps/isaacsim.exp.base.kit** file and add the settings below:

            .. code-block:: console

                [settings]
                persistent.isaac.asset_root.default = "/home/<username>/isaacsim_assets/Assets/Isaac/6.0"

                exts."isaacsim.gui.content_browser".folders = [
                    "/home/<username>/isaacsim_assets/Assets/Isaac/6.0/Isaac/Robots",
                    "/home/<username>/isaacsim_assets/Assets/Isaac/6.0/Isaac/People",
                    "/home/<username>/isaacsim_assets/Assets/Isaac/6.0/Isaac/IsaacLab",
                    "/home/<username>/isaacsim_assets/Assets/Isaac/6.0/Isaac/Props",
                    "/home/<username>/isaacsim_assets/Assets/Isaac/6.0/Isaac/Environments",
                    "/home/<username>/isaacsim_assets/Assets/Isaac/6.0/Isaac/Materials",
                    "/home/<username>/isaacsim_assets/Assets/Isaac/6.0/Isaac/Samples",
                    "/home/<username>/isaacsim_assets/Assets/Isaac/6.0/Isaac/Sensors",
                ]

        .. tab-item:: Windows

            Edit the **C:/isaacsim/apps/isaacsim.exp.base.kit** file and add the settings below:

            .. code-block:: console

                [settings]
                persistent.isaac.asset_root.default = "C:/isaacsim_assets/Assets/Isaac/6.0"

                exts."isaacsim.gui.content_browser".folders = [
                    "C:/isaacsim_assets/Assets/Isaac/6.0/Isaac/Robots",
                    "C:/isaacsim_assets/Assets/Isaac/6.0/Isaac/People",
                    "C:/isaacsim_assets/Assets/Isaac/6.0/Isaac/IsaacLab",
                    "C:/isaacsim_assets/Assets/Isaac/6.0/Isaac/Props",
                    "C:/isaacsim_assets/Assets/Isaac/6.0/Isaac/Environments",
                    "C:/isaacsim_assets/Assets/Isaac/6.0/Isaac/Materials",
                    "C:/isaacsim_assets/Assets/Isaac/6.0/Isaac/Samples",
                    "C:/isaacsim_assets/Assets/Isaac/6.0/Isaac/Sensors",
                ]


    4. Run |isaac-sim_short| with the flag below to use the local assets.

    .. tab-set::
        .. tab-item:: Linux

            .. code-block:: console

                ./isaac-sim.sh --/persistent/isaac/asset_root/default="/home/<username>/isaacsim_assets/Assets/Isaac/6.0"

        .. tab-item:: Windows

            .. code-block:: console

                .\isaac-sim.bat --/persistent/isaac/asset_root/default="C:/isaacsim_assets/Assets/Isaac/6.0"

    .. note::

        * The `persistent.isaac.asset_root.default` setting can either be set in the .kit settings file (Step 3) or using the  commandline (Step 4). The default is set to `https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0`
        * The `persistent.isaac.asset_root.default` setting is used in the Python code that calls the `get_assets_root_path_async`` or `get_assets_root_path`` functions.
        * The `exts."isaacsim.gui.content_browser".folders` setting is used in the :ref:`Content Browser <isaac_sim_app_gui_content_browser>`.

    .. _isaac_sim_asset_root_resolution:

    .. rubric:: Asset Root Resolution Order

    The ``persistent.isaac.asset_root.default`` setting is resolved from multiple sources. The following table lists them from **highest to lowest priority**:

    .. list-table::
        :widths: 5 30 65
        :header-rows: 1

        * - Priority
          - Source
          - Example
        * - 1
          - ``ISAACSIM_ASSET_ROOT`` environment variable
          - ``export ISAACSIM_ASSET_ROOT=https://my-server``
        * - 2
          - Command-line argument
          - ``--/persistent/isaac/asset_root/default=https://my-server``
        * - 3
          - Experience (``.kit``) file
          - ``persistent.isaac.asset_root.default = "https://my-server"``
        * - 4
          - Extension default (``extension.toml``)
          - ``persistent.isaac.asset_root.default = "https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0"``

    At startup the ``isaacsim.storage.native`` extension reads the ``ISAACSIM_ASSET_ROOT`` environment variable and, if set, overwrites the setting regardless of any value provided by a ``.kit`` file or command-line argument. When the variable is unset, the normal Kit settings precedence applies (CLI > ``.kit`` > ``extension.toml``).

    .. _isaac_sim_setup_assets_check:

    .. rubric::  Assets Check

    In the |isaac-sim_short| app, to verify the access to the assets, go to the **Utilities** menu. Then click **Check Default Assets Root Path**.

    .. figure:: /images/isim_6.0_base_ref_gui_assets_check.png
        :align: center

    If manually downloading the assets pack from the previous section, the logs should show:

    .. tab-set::
        .. tab-item:: Linux

            .. code-block:: console

                [139.213s] Checking for Isaac Sim Assets...
                [139.218s] Isaac Sim assets found: /home/<username>/isaacsim_assets/Assets/Isaac/6.0

        .. tab-item:: Windows

            .. code-block:: console

                [139.213s] Checking for Isaac Sim Assets...
                [139.218s] Isaac Sim assets found: C:\isaacsim_assets\Assets\Isaac\5.0

    By default, the logs should show:

    .. code-block:: console

        [139.213s] Checking for Isaac Sim Assets...
        [139.218s] Isaac Sim assets found: https://omniverse-content-production.s3-us-west-2.amazonaws.com/Assets/Isaac/6.0


.. dropdown:: Docker

    .. _isaac_sim_setup_keep_configs:

    .. rubric:: Save |isaac-sim_short| Configs on Local Disk

    To keep |isaac-sim_short| configuration and data persistent when running in a container, use the flags below
    when running the Docker container.

    .. code-block:: console

        -v ~/docker/isaac-sim/cache/main:/isaac-sim/.cache:rw                    #For cache
        -v ~/docker/isaac-sim/cache/computecache:/isaac-sim/.nv/ComputeCache:rw  #For cache
        -v ~/docker/isaac-sim/logs:/isaac-sim/.nvidia-omniverse/logs:rw          #For log files
        -v ~/docker/isaac-sim/config:/isaac-sim/.nvidia-omniverse/config:rw      #For config files
        -v ~/docker/isaac-sim/data:/isaac-sim/.local/share/ov/data:rw            #For data
        -v ~/docker/isaac-sim/pkg:/isaac-sim/.local/share/ov/pkg:rw              #For apps
        -u 1234:1234                                                             #To set user permissions

    .. code-block:: console

        $ sudo docker run --name isaac-sim --entrypoint bash -it --gpus all -e "ACCEPT_EULA=Y" --rm --network=host \
        -v ~/docker/isaac-sim/cache/main:/isaac-sim/.cache:rw \
        -v ~/docker/isaac-sim/cache/computecache:/isaac-sim/.nv/ComputeCache:rw \
        -v ~/docker/isaac-sim/logs:/isaac-sim/.nvidia-omniverse/logs:rw \
        -v ~/docker/isaac-sim/config:/isaac-sim/.nvidia-omniverse/config:rw \
        -v ~/docker/isaac-sim/data:/isaac-sim/.local/share/ov/data:rw \
        -v ~/docker/isaac-sim/pkg:/isaac-sim/.local/share/ov/pkg:rw \
        -u 1234:1234 \
        nvcr.io/nvidia/isaac-sim:6.0.0

    .. note:: These flags will use the use Home folder to save the |isaac-sim_short| cache, logs, config, and data.


    .. _isaac_sim_setup_net_host:

    .. rubric:: Problem Connecting to Docker Container

    To resolve some problems connecting to a Docker container, try using the **--network=host** flag
    when running the Docker container.

    .. code-block:: console

        $ sudo docker run --gpus all -e "ACCEPT_EULA=Y" --rm --network=host nvcr.io/nvidia/isaac-sim:6.0.0

    .. note:: This flag is needed to connect to a Nucleus server.


    .. _isaac_sim_setup_read_logs:

    .. rubric:: Reading the Logs in a Container

    To ensure |isaac-sim| is running in a container, you can read the logs:

    1. If the |isaac-sim| container is on a remote machine, SSH into the Docker host using a terminal.
    Run this command from where your pem key folder is; replace the ``<public_ip_address>`` with your
    instance or remote host IP address:

    .. code-block:: console

        $ ssh -i "yourkey.pem" ubuntu@<public_ip_address>


    2. Access the running container as follows:

    .. code-block:: console

        $ docker exec -it <container_id_or_name> bash
        $ cd /root/.nvidia-omniverse/logs/Kit/Isaac-Sim/<version_number>


    .. _isaac_sim_setup_restart_container:

    .. rubric:: Restarting the Container

    The steps below are used to restart a headless container.

    1. SSH into the host machine or AWS instance running the |isaac-sim| Container.

    .. code-block:: console

        $ ssh -i "<ssh_key_name>.pem" ubuntu@<public_ip_address>

    2. List all running containers and find the container ID running |isaac-sim|.

    .. code-block:: console

        $ sudo docker ps
        CONTAINER ID        IMAGE
        823686a7036d      nvcr.io/nvidia/isaac-sim...2021.2.1

    3. Restart the container.

    .. code-block:: console

        $ sudo docker restart [CONTAINER ID]

    4. View the Docker logs.

    .. code-block:: console

        $ sudo docker logs [CONTAINER ID]


    .. _isaac_sim_restart_sim_inside_docker:

    .. rubric:: Restart |isaac-sim| inside Docker


    If you want to restart |isaac-sim| while keeping Docker running, you must start the Docker with
    Bash as the entrypoint so that you can manually start or stop |isaac-sim|.

    1. Start the Docker with Bash, and start |isaac-sim| manually.

    .. code-block:: console

        $ sudo docker run -it --entrypoint bash --gpus all -e "ACCEPT_EULA=Y" --rm --network=host nvcr.io/nvidia/isaac-sim:6.0.0
        $ ./runheadless.sh

    2. Proceed to :ref:`isaac_sim_setup_livestream_webrtc` to connect the native streaming client and
       view |isaac-sim| remotely. See :ref:`isaac_sim_manual_livestream_client` for all streaming options.

    3. When you need to exit, in a separate terminal start an interactive bash session inside the same
    container that's running the headless server and kill the |isaac-sim| related processes.

    .. code-block:: console

        $ docker exec -it <container_id> bash
        $ pkill omniverse-kit

    4. Restart |isaac-sim|.

    .. code-block:: console

        $ ./runheadless.sh


    .. _isaac_sim_save_docker_image:

    .. rubric:: Save Docker Image

    If you made significant changes inside the Docker, for example, installed ROS or other libraries, you may want to save the Docker image so that you can restart the Docker without having to reinstall everything.

    1. Find the container's ID and commit it.

    .. code-block:: console

        $ docker ps
        $ docker commit <CONTAINER ID> <new docker name>

    2. To reload a specific Docker:

    .. code-block:: console

        $ docker run -it --entrypoint bash --gpus all -e "ACCEPT_EULA=Y" --rm --network=host -d <new Docker name>


    .. _isaac_sim_cached_docker_image:

    .. rubric:: Create a Cached Docker Image


    Creating a local cached image of |isaac-sim_short| will help improve the load times of running |isaac-sim_short| in a container as well as having custom pre-installed dependencies.

    1. To create this cached image, first pull and run the latest |isaac-sim_short| container from NGC.

    .. code-block:: console

        $ docker pull nvcr.io/nvidia/isaac-sim:6.0.0
        $ docker run --name isaac-sim --entrypoint bash -it --rm --gpus all --network=host \
            -e "ACCEPT_EULA=Y" -e "PRIVACY_CONSENT=Y" \
            nvcr.io/nvidia/isaac-sim:6.0.0

    2. Install any dependencies (for example, ROS or other libraries) and warm up the shader cache.

    .. code-block:: console

        $ ./python.sh -m pip install stable-baselines3 tensorboard
        $ ./python.sh standalone_examples/api/isaacsim.simulation_app/hello_world.py -v
        $ ./runheadless.sh -v --/app/quitAfter=1000

    3. Create the cached Docker image.

    .. code-block:: console

        $ docker commit isaac-sim isaac-sim-cached

    4. Save the Docker image to a compressed archive to transfer it to another machine, if needed.

    .. code-block:: console

        $ docker save isaac-sim-cached | gzip > isaac-sim-cached.tar.gz

    5. Load the compressed archive as a Docker image.

    .. code-block:: console

        $ docker load -i isaac-sim-cached.tar.gz isaac-sim-cached

    6. Run this cached image.

    .. code-block:: console

        $ docker run --name isaac-sim-cached --entrypoint bash -it --gpus all --rm --network=host \
            -e "ACCEPT_EULA=Y" -e "PRIVACY_CONSENT=Y" \
            isaac-sim-cached

    .. _isaac_sim_setup_docker_post_install:

    .. rubric:: Setting up Docker


    After you have Docker on Linux installed, follow the instructions at `Post-installation steps for Linux`_ to set it up so that you would not need to use *sudo* to run a Docker container.


    .. _isaac_sim_setup_mount_folder:

    .. rubric:: Mount a Folder to the Container


    To add data from the host machine to a container, you must mount a folder.

    .. code-block:: console

        $ sudo docker run --gpus all --rm -e "ACCEPT_EULA=Y" -v ~/docker/isaac-sim/documents:/root/Documents:rw nvcr.io/nvidia/isaac-sim:6.0.0

    .. note:: Can now copy files to docker/isaac-sim/documents in your Home folder and it will show up in the |isaac-sim_short| container at /root/Documents.


.. dropdown:: Cloud

    .. _isaac_sim_setup_aws_ip_address:

    .. rubric:: Getting IP Addresses of AWS EC2 Instance


    To get the public and private IP addresses of an AWS EC2 instance, go to the **Instances** section of the **EC2 Dashboard** and select the instance. Refer to the image below for an example of the Private and Public IPs:

    .. figure:: /images/isaac_main_aws_ip_address.png
            :align: center

    .. _isaac_sim_setup_ssh_aws_instance:

    .. rubric:: SSH into the AWS EC2 Instance


    If you need to directly access an AWS EC2 instance that was created from the deployment above, run these steps to SSH into the instance:

    .. code-block:: console

        $ ssh -i "<ssh_key_name>.pem" ubuntu@<public_ip_address>

    .. _isaac_sim_setup_create_aws_key:

    .. rubric:: Creating AWS Access Key


    Create an AWS Access Key by following the instructions here:

        `Managing access keys (console)`_

    .. _isaac_sim_setup_create_ssh_key:

    .. rubric:: Creating SSH Key


    **On Linux**

    1. Run:

    .. code-block:: console

        $ mkdir ~/.ssh
        $ chmod 700 ~/.ssh
        $ ssh-keygen -t rsa

    2. Enter your passphrase twice.
    3. Your public key is at **.ssh/id_rsa.pub** in your home folder and private key at **.ssh/id_rsa**.

    **On Windows**

    #. Download `PuTTYgen`_.
    #. Launch PuTTYgen, and click on "Generate a public/private key pair".
    #. Click on **Save public key** and name the file "${ssh_key_name}.pub". This is your Public Key file.
    #. From the **Conversions** menu, select **Export OpenSSH key** and name the file "${ssh_key_name}.pem". This is your Private Key file.
    #. Edit the properties of the "${ssh_key_name}.pem" file.

        * Go to security settings, click **Advanced**
        * Remove inheritance
        * Set current user as owner of the file and full permissions to only that user
        * This is to prevent permission errors when trying to SSH into the instance



.. _assets_and_nucleus_ref:

.. dropdown:: Nucleus

    .. _isaac_sim_setup_nucleus_add_assets_mount:

    .. rubric:: Assets on Nucleus

    To access the |isaac-sim_short| assets, access to the Internet is required.

    .. note::

        - The |isaac-sim_short| assets are also available in the main **/NVIDIA/Assets/Isaac** folder in every |nuc_short| server.

    .. _isaac_sim_setup_set_omni_server:

    .. rubric:: Setting the Default |nuc_short| Server

    1. To set the default Nucleus server when running natively, open the ``user.config.json`` file for editing and locate the following line:

    .. code-block:: console

        "persistent": {
            "isaac": {
                "asset_root": {
                    "default": "omniverse://localhost/NVIDIA/Assets/Isaac/6.0",
                }
            },
        },

    2. Change ``localhost`` to the IP address of the |nuc_short| server.

    .. note::

        * Location of ``user.config.json`` file:

            * Linux: ``~/.local/share/ov/data/Kit/Isaac-Sim/5.0/user.config.json``
            * Windows: ``C:\Users\{username}\AppData\Local\ov\data\Kit\Isaac-Sim\5.0\user.config.json``

        * The folder in the **persistent/isaac/asset_root/default** setting should contain both the **Isaac** and the **NVIDIA** folder.

    3. You could also run |isaac-sim_short| with this flag:

    .. code-block:: console

        --/persistent/isaac/asset_root/default="omniverse://<ip_address>/NVIDIA/Assets/Isaac/6.0"

    4. To set the default |nuc_short| server when running in Docker, use the flag ``-e "OMNI_SERVER=omniverse://<ip_address>/NVIDIA/Assets/Isaac/6.0"``, where ``<ip_address>`` is the IP address of the |nuc_short| server.

    .. code-block:: console

        $ sudo docker run --gpus all -e "ACCEPT_EULA=Y" -e "OMNI_SERVER=omniverse://<ip_address>/NVIDIA/Assets/Isaac/6.0" --rm --network=host nvcr.io/nvidia/isaac-sim:6.0.0

    .. _isaac_sim_setup_set_omni_user:

    .. rubric:: Setting the Default Username and Password for Connecting to the |nuc_short| Server

    1. Use the following commands to set the default credentials when running natively:

    .. code-block:: console

        $ export OMNI_USER=<username>
        $ export OMNI_PASS=<password>

    2.  To set the default credentials when running in Docker, use the flag ``-e "OMNI_USER=<username>" -e "OMNI_PASS=<password>"`` (the default is "admin" for each).

    .. code-block:: console

        $ sudo docker run --gpus all -e "ACCEPT_EULA=Y" -e "OMNI_USER=<username>" -e "OMNI_PASS=<password>" --rm --network=host nvcr.io/nvidia/isaac-sim:6.0.0
