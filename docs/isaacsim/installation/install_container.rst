..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _Isaac Sim Container: https://catalog.ngc.nvidia.com/orgs/nvidia/containers/isaac-sim
.. _NGC API Key: https://docs.nvidia.com/ngc/ngc-overview/index.html#generating-api-key

.. _Key Pair Guide: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html#create-a-key-pair
.. _Connecting to Your Linux Instance from Windows Using PuTTY: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/putty.html
.. _Visual Studio Code: https://code.visualstudio.com/download
.. _Remote-SSH extension: https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh
.. _Create a Linux virtual machine in the Azure portal: https://docs.microsoft.com/en-us/azure/virtual-machines/linux/quick-create-portal

.. _Install Docker Engine on Ubuntu: https://docs.docker.com/engine/install/ubuntu
.. _Post-installation steps for Linux: https://docs.docker.com/engine/install/linux-postinstall
.. _NVIDIA Container Toolkit: https://github.com/NVIDIA/nvidia-container-toolkit

.. _Nucleus System Requirements: <nucleus:installation/workstation.html#system-requirements>`

.. _Unix Driver Archive: https://www.nvidia.com/en-us/drivers/unix/
.. _NVIDIA GPU Driver Archive: https://www.nvidia.com/en-us/drivers/unix/linux-amd64-display-archive/
.. _Isaac Sim Dockerfiles: https://github.com/isaac-sim/IsaacSim/tree/main/tools/docker


.. _isaac_sim_app_install_container:


Container Installation
========================================================

The container installation of Isaac Sim is recommended for deployment on remote headless servers or the Cloud using a Docker container running Linux.

.. seealso::

    * :ref:`isaac_sim_setup_differences`

.. _isaac_sim_requirements_isaac_sim_container:

Container Setup
--------------------------------------------------

1. Ensure your system meets the :ref:`isaac_sim_requirements_isaac_sim_system` for running |isaac-sim|.

2. Install Docker:

.. code-block:: console

    # Docker installation using the convenience script
    $ curl -fsSL https://get.docker.com -o get-docker.sh
    $ sudo sh get-docker.sh

    # Post-install steps for Docker
    $ sudo groupadd docker
    $ sudo usermod -aG docker $USER
    $ newgrp docker

    # Verify Docker
    $ docker run hello-world

.. seealso::

    * `Install Docker Engine on Ubuntu`_
    * `Post-installation steps for Linux`_

3. Install the |nv| Container Toolkit:

.. code-block:: console

    # Configure the repository
    $ curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
        && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
        sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
        sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list \
        && \
        sudo apt-get update

    # Install the NVIDIA Container Toolkit packages
    $ sudo apt-get install -y nvidia-container-toolkit
    $ sudo systemctl restart docker

    # Configure the container runtime
    $ sudo nvidia-ctk runtime configure --runtime=docker
    $ sudo systemctl restart docker

    # Verify NVIDIA Container Toolkit
    $ docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi

.. note::

    * Install the latest version of `NVIDIA Container Toolkit`_ to get security fixes.


.. _isaac_sim_setup_remote_headless_container:

Container Deployment
------------------------------------------------------------------------------------------------

This section describes how to run the |isaac-sim| container in headless mode with livestreaming.

**Steps:**

1. Setup and install the container prerequisites. See :ref:`isaac_sim_requirements_isaac_sim_container` above.

2. Run the following command to confirm your GPU driver version:

.. code-block:: console

    $ nvidia-smi

3. Pull the `Isaac Sim Container`_:

.. code-block:: console

    $ docker pull nvcr.io/nvidia/isaac-sim:5.1.0

4. Create the cached volume mounts on host:

.. code-block:: console

    $ mkdir -p ~/docker/isaac-sim/cache/main/ov
    $ mkdir -p ~/docker/isaac-sim/cache/main/warp
    $ mkdir -p ~/docker/isaac-sim/cache/computecache
    $ mkdir -p ~/docker/isaac-sim/config
    $ mkdir -p ~/docker/isaac-sim/data/documents
    $ mkdir -p ~/docker/isaac-sim/data/Kit
    $ mkdir -p ~/docker/isaac-sim/logs
    $ mkdir -p ~/docker/isaac-sim/pkg
    $ sudo chown -R 1234:1234 ~/docker/isaac-sim

5. Run the |isaac-sim_short| container with an interactive Bash session:

.. code-block:: console

    $ docker run --name isaac-sim --entrypoint bash -it --gpus all -e "ACCEPT_EULA=Y" --rm --network=host \
        -e "PRIVACY_CONSENT=Y" \
        -v ~/docker/isaac-sim/cache/main:/isaac-sim/.cache:rw \
        -v ~/docker/isaac-sim/cache/computecache:/isaac-sim/.nv/ComputeCache:rw \
        -v ~/docker/isaac-sim/logs:/isaac-sim/.nvidia-omniverse/logs:rw \
        -v ~/docker/isaac-sim/config:/isaac-sim/.nvidia-omniverse/config:rw \
        -v ~/docker/isaac-sim/data:/isaac-sim/.local/share/ov/data:rw \
        -v ~/docker/isaac-sim/pkg:/isaac-sim/.local/share/ov/pkg:rw \
        -u 1234:1234 \
        nvcr.io/nvidia/isaac-sim:5.1.0

.. note::

    * The Isaac Sim container now runs as a rootless user.
    * The Isaac Sim container now supports multi-arch. The same tag can be run on Linux x86_64 and aarch64 systems.
    * By using the ``-e "ACCEPT_EULA=Y"`` flag, you accept the license agreement of the image found at :doc:`NVIDIA Omniverse License Agreement</common/NVIDIA_Omniverse_License_Agreement>`.
    * By using the ``-e "PRIVACY_CONSENT=Y"`` flag, you opt-in to the data collection agreement found at :doc:`../common/data-collection`. You may opt-out by not setting this flag.
    * The ``-e "PRIVACY_USERID=<email>"`` flag can optionally be set for tagging the session logs.
    * Add the ``--runtime=nvidia`` flag if there are issues detecting the GPU in the container.
    * For enterprise users, see :doc:`Enterprise Nucleus Server <nucleus:enterprise/installation/install-ove-nucleus>`.
    * The |isaac-sim_short| container uses assets in the Cloud if no Nucleus server is available.

    When using a separate Nucleus server:

        * See :ref:`isaac_sim_setup_net_host` to expose all ports of the container and connect to an external Nucleus server.
        * See :ref:`isaac_sim_setup_set_omni_server` to set the default Nucleus server.
        * See :ref:`isaac_sim_setup_set_omni_user` to set the default credentials for any Nucleus server.

6. Check if your system is compatible with |isaac-sim_short|:

.. code-block:: console

    $ ./isaac-sim.compatibility_check.sh --/app/quitAfter=10 --no-window

.. note::

    * To run the Compatibility Checker separately:

    .. code-block:: console

        $ docker run --entrypoint bash -it --gpus all --rm --network=host \
            nvcr.io/nvidia/isaac-sim:5.1.0 ./isaac-sim.compatibility_check.sh --/app/quitAfter=10 --no-window

    * You should see the text "System checking result: PASSED" if your system is compaitble.


7. Start |isaac-sim_short| with native livestream mode:

.. code-block:: console

    $ ./runheadless.sh -v

.. warning::

    * :ref:`Livestreaming <isaac_sim_setup_livestream_webrtc>` is not supported on aarch64 systems like |spark_short| for Isaac Sim 5.1.0.
    * See :ref:`isaac_sim_setup_local_gui_container`.

.. note::

    * Before running a livestream client, you must have the |isaac-sim_short| app loaded and ready.
        It may take a few minutes for |isaac-sim_short| to completely load.

    * The -v flag is used to show additional logs while the shader cache is being warmed up.

    * To confirm this, look out for this line in the console or the logs:

    .. code-block:: console

        Isaac Sim Full Streaming App is loaded.

    * The first time loading |isaac-sim_short|, it takes a while for the shaders to be cached. Subsequent runs of |isaac-sim_short| are quicker because the shaders are cached and the cache is mounted when the container runs.

    * See :ref:`isaac_sim_setup_keep_configs` to make |isaac-sim_short| configs and cache persistent when using containers.

8. Connect a streaming client to view |isaac-sim_short|. There are two options:

    * **Desktop client**: Download and run the :ref:`isaac_sim_setup_livestream_webrtc` from the :ref:`isaac_sim_latest_release` section. Enter the IP address of the host and click **Connect**.
    * **Web-based client**: Use Docker Compose to deploy a browser-based viewer alongside |isaac-sim_short|. See :ref:`isaac_sim_web_streaming_client` or :ref:`isaac_sim_docker_compose_deployment` below.

9. Proceed to :ref:`isaac_sim_intro_quickstart_series` to begin your first tutorial.

.. note::

    * Some tutorials that use the Content Browser may not work when using the |isaac-sim_short| container with no Nucleus connected.
    * It is recommended to use the Workstation |isaac-sim_short| from the Omniverse Launcher to run all tutorials.
    * The |isaac-sim_short| container supports running our Python apps and standalone examples in headless mode only.
    * The latest NVIDIA drivers may not be fully supported for some features like livestreaming. See :doc:`Technical Requirements<dev-guide:common/technical-requirements>` for recommended drivers.
    * See also `Isaac Sim Dockerfiles`_ to build your own custom |isaac-sim_short| container.
    * You can debug :ref:`isaac_sim_app_tutorial_advanced_python_debugging_docker`.


.. _isaac_sim_docker_compose_deployment:

Docker Compose Deployment (Isaac Sim + Web Viewer)
------------------------------------------------------------------------------------------------

Docker Compose can deploy |isaac-sim_short| and a web-based WebRTC streaming client together. This is a simpler alternative to the manual ``docker run`` workflow above, and does not require downloading a native streaming client.

For full details on Docker Compose configuration, multi-instance deployment, and environment variables, see the `Docker README <https://github.com/isaac-sim/IsaacSim/blob/main/tools/docker/README.md>`_.

The ``docker-compose.yml`` in ``tools/docker/`` handles volume mounts, GPU assignment, networking, and health checks automatically. The web viewer is built from the `NVIDIA Omniverse Web SDK <https://docs.omniverse.nvidia.com/ov-web-sdk/latest/web-sample/overview.html>`_.

.. warning::

    |isaac-sim_short| and the web viewer are designed for use on private/trusted networks. They do not include authentication or encryption. If you need to expose them over the Internet, add a reverse proxy with HTTPS/TLS and authentication (e.g. nginx with SSL certificates and basic auth). Users are responsible for securing any public-facing deployments.

**Quick Start:**

.. code-block:: console

    # Create cache/log mounts (use uid 1234 to match container user)
    $ mkdir -p ~/docker/isaac-sim/{cache/main,cache/computecache,config,data,logs,pkg}
    $ sudo chown -R 1234:1234 ~/docker

    # Build the Isaac Sim image (one-time)
    $ ./tools/docker/prep_docker_build.sh --build --x86_64
    $ ./tools/docker/build_docker.sh --x86_64

    # Launch both services
    $ docker compose -p isim -f tools/docker/docker-compose.yml up --build -d

    # Check the web viewer URL
    $ docker compose -p isim logs web-viewer

.. note::

   On DGX Spark, use ``--aarch64`` instead of ``--x86_64`` in the build commands above.

Open the URL shown in the logs (e.g. ``http://<host-ip>:8210``) in a Chromium-based browser.

To use a prebuilt NGC image instead of building locally:

.. code-block:: console

    $ ISAAC_SIM_IMAGE=nvcr.io/nvidia/isaac-sim:6.0.0 docker compose -p isim -f tools/docker/docker-compose.yml up --build -d

To stop:

.. code-block:: console

    $ docker compose -p isim -f tools/docker/docker-compose.yml down

.. note::

    * The web viewer bakes the signaling host and ports at build time. Use ``--build`` when changing ``ISAACSIM_HOST`` or port variables.
    * Docker Compose supports multi-instance deployment with dedicated GPUs, custom signal/stream ports, and more. See the `Docker README <https://github.com/isaac-sim/IsaacSim/blob/main/tools/docker/README.md>`_ for full configuration details.


.. _isaac_sim_setup_local_gui_container:

Container Deployment with GUI
------------------------------------------------------------------------------------------------

This section describes how to run the |isaac-sim| container with GUI.

**Steps:**

1. Setup and install the container prerequisites. See :ref:`isaac_sim_requirements_isaac_sim_container` above.

2. Run the following command to confirm your GPU driver version:

.. code-block:: console

    $ nvidia-smi

3. Pull the `Isaac Sim Container`_:

.. code-block:: console

    $ docker pull nvcr.io/nvidia/isaac-sim:5.1.0

4. Create the cached volume mounts on host:

.. code-block:: console

    $ mkdir -p ~/docker/isaac-sim/cache/main/ov
    $ mkdir -p ~/docker/isaac-sim/cache/main/warp
    $ mkdir -p ~/docker/isaac-sim/cache/computecache
    $ mkdir -p ~/docker/isaac-sim/config
    $ mkdir -p ~/docker/isaac-sim/data/documents
    $ mkdir -p ~/docker/isaac-sim/data/Kit
    $ mkdir -p ~/docker/isaac-sim/logs
    $ mkdir -p ~/docker/isaac-sim/pkg
    $ sudo chown -R 1234:1234 ~/docker/isaac-sim

5. Run the |isaac-sim_short| container with an interactive Bash session:

.. code-block:: console

    $ xhost +local:
    $ docker run --name isaac-sim --entrypoint bash -it --gpus all -e "ACCEPT_EULA=Y" --rm --network=host \
        -e "PRIVACY_CONSENT=Y" \
        -v $HOME/.Xauthority:/isaac-sim/.Xauthority \
        -e DISPLAY \
        -v ~/docker/isaac-sim/cache/main:/isaac-sim/.cache:rw \
        -v ~/docker/isaac-sim/cache/computecache:/isaac-sim/.nv/ComputeCache:rw \
        -v ~/docker/isaac-sim/logs:/isaac-sim/.nvidia-omniverse/logs:rw \
        -v ~/docker/isaac-sim/config:/isaac-sim/.nvidia-omniverse/config:rw \
        -v ~/docker/isaac-sim/data:/isaac-sim/.local/share/ov/data:rw \
        -v ~/docker/isaac-sim/pkg:/isaac-sim/.local/share/ov/pkg:rw \
        -u 1234:1234 \
        nvcr.io/nvidia/isaac-sim:5.1.0

6. Check if your system is compatible with |isaac-sim_short|:

.. code-block:: console

    $ ./isaac-sim.compatibility_check.sh

7. Start |isaac-sim_short| with GUI:

.. code-block:: console

    $ ./runapp.sh

8. Proceed to :ref:`isaac_sim_intro_quickstart_series` to begin your first tutorial.

.. warning::

    * Running |isaac-sim_short| with GUI in the container is generally not recommended.
    * The application experience may not be as expected. For a full GUI app experience please run |isaac-sim_short| with the :ref:`isaac_sim_app_install_workstation`.
