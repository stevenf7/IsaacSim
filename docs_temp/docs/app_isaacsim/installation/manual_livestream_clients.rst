..
   Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _Install FUSE 2: https://docs.appimage.org/user-guide/troubleshooting/fuse.html#setting-up-fuse-2-x-alongside-of-fuse-3-x-on-recent-ubuntu-22-04-debian-and-their-derivatives
.. _Video Encode and Decode Support Matrix: https://developer.nvidia.com/video-encode-decode-support-matrix


.. _isaac_sim_manual_livestream_client:

===================================
Livestream Clients
===================================

This section shows you the methods of livestreaming a headless instance of |isaac-sim_short|.

.. note::

    * Only one method of streaming can be used at a time for each |isaac-sim_short| instance.
    * Only one client can access an |isaac-sim_short| instance at a time.
    * To exit the Isaac Sim app remotely: Click the **File** menu, then click **Exit** in the streamed Isaac Sim app. Next, close the |isaac-sim_short| WebRTC Streaming Client app.
    * Livestreaming is not supported when |isaac-sim_short| is run on the A100 GPU. NVENC (NVIDIA Encoder) is required for livestreaming and is not included in the A100 GPU.
    * See `Video Encode and Decode Support Matrix`_ for supported GPU with NVENC.
    * By downloading or using the NVIDIA Isaac Sim WebRTC Streaming Client, you agree to the :doc:`NVIDIA Isaac Sim WebRTC Streaming Client License Agreement </common/license-isaac-sim-webrtc-streaming-client>`.
    * |isaac-sim_short| WebRTC Streaming Client is not yet supported on aarch64. See: :ref:`aarch64 Limitations<isaac_sim_requirements_aarch64_limitations>`.


.. _isaac_sim_setup_livestream_webrtc:

|isaac-sim_short| WebRTC Streaming Client
------------------------------------------------------------------------------------------------

|isaac-sim_short| WebRTC Streaming Client is the recommended streaming client to view |isaac-sim_short| remotely on your desktop or workstation without a powerful GPU.

1. To use the |isaac-sim_short| WebRTC Streaming Client, run |isaac-sim_short| using one of the following methods:

.. tab-set::
    .. tab-item:: Linux

        See :ref:`isaac_sim_app_install_workstation` for full installation instructions.

        .. code-block:: bash

            cd ~/isaacsim
            ./isaac-sim.streaming.sh

    .. tab-item:: Windows

        See :ref:`isaac_sim_app_install_workstation` for full installation instructions.

        .. code-block:: bat

            cd C:\isaacsim
            isaac-sim.streaming.bat

    .. tab-item:: Docker (x86_64)

        See :ref:`isaac_sim_app_install_container` for full installation instructions.

        .. code-block:: bash

            cd /isaac-sim
            ./runheadless.sh

    .. tab-item:: PIP

        See :ref:`isaac_sim_app_install_python` for full installation instructions.

        .. code-block:: bash

            isaacsim isaacsim.exp.full.streaming --no-window

    .. tab-item:: Python Sample

        See :ref:`isaac_sim_python_environment` for full installation instructions.

        .. code-block:: bash

            ./python.sh standalone_examples/api/isaacsim.simulation_app/livestream.py

.. note::

    * To run Isaac Sim on remote instance to be connected via the Internet, add these flags: ``--/exts/omni.kit.livestream.app/primaryStream/publicIp=<PUBLIC_IP> --/exts/omni.kit.livestream.app/primaryStream/signalPort=49100 --/exts/omni.kit.livestream.app/primaryStream/streamPort=47998``

    * For an example in a Docker container:

    .. code-block:: bash

        PUBLIC_IP=$(curl -s ifconfig.me) && ./runheadless.sh --/exts/omni.kit.livestream.app/primaryStream/publicIp=$PUBLIC_IP --/exts/omni.kit.livestream.app/primaryStream/signalPort=49100 --/exts/omni.kit.livestream.app/primaryStream/streamPort=47998

    * Use the same Public IP in the **Isaac Sim WebRTC Streaming Client** app.

    * The following ports must be opened on the host running Isaac Sim:

        * ``UDP port 47998``
        * ``TCP port 49100``


2. Make sure that the |isaac-sim_short| app is loaded and ready. It can take a few minutes for |isaac-sim_short| to be completely loaded the first time.

3. To confirm this, look for the following message in the terminal/console output or the application logs. This line may not appear when running using PIP or Python Sample.

.. code-block:: console

    Isaac Sim Full Streaming App is loaded.

4. Download **Isaac Sim WebRTC Streaming Client** from the :ref:`isaac_sim_latest_release` section for your platform.

5. Run the **Isaac Sim WebRTC Streaming Client** app.

.. figure:: /images/isim_4.5_full_ref_gui_iswsc_1.0.6.png
    :align: center

6. Use the default **127.0.0.1** IP address as the server to connect to a local instance of Isaac Sim.

7. Click **Connect**. The connection process may take a few moments. You should see the Isaac Sim interface appear in the client window once connected.

.. note::

    * |isaac-sim_short| WebRTC Streaming Client is recommended to be used within the same network as an |isaac-sim_short| headless instance.
    * To connect to a headless instance of |isaac-sim_short| in the same network, replace **127.0.0.1** with the IP address of the machine running |isaac-sim_short|.
    * On Linux:

        * In Terminal, run ``chmod +x *.AppImage`` to allow the app to be executable.
        * Double-click the AppImage file to run |isaac-sim_short| WebRTC Streaming Client.
        * **Important**: `libfuse2` is required to run on Ubuntu 22.04 or later. See `Install FUSE 2`_ for installation instructions.

    * On Windows:

        * If you have issues connecting to a local or remote Isaac Sim instance, make sure the `/kit/kit.exe` and **Isaac Sim WebRTC Streaming Client** app is on the allow list in the Windows Firewall.

    * On Mac:

        * Open the DMG file then click and drag the **Isaac Sim WebRTC Streaming Client** app to the **Applications** folder icon to install.
        * When streaming |isaac-sim_short| app, use ``Ctrl+C`` and ``Ctrl+V`` to copy and paste respectively within the streamed app.
        * To copy from host to client, use ``⌘C`` and ``Ctrl+V``.

    * To reload the connection, click **Reload** in the **View** menu. This may be useful if you see a blank screen after some time.

    .. figure:: /images/isim_4.5_full_ref_gui_iswsc_1.0.6_reload.png
        :align: center
