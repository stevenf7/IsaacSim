..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_quick_install:

Quick Install
=======================

The Quick Install can be used for demos and to get a quick working idea of what the full product can do. After completing the quick install, you can create a room with a robot in it, which provides an even fuller picture of the product capabilities. These instructions are aimed at installation by someone with basic computer knowledge.

For a quick install on Linux or Windows:

#. Download the current |isaac-sim_short| standalone package for your platform from the :ref:`isaac_sim_latest_release` section.

    .. note::

        * On Linux, install ``unzip`` before extracting the package.
        * Keep at least 50 GB of free disk space available. The downloaded package and extracted installation can temporarily require about 40 GB together.
        * Running on a remote or headless machine? Use ``isaac-sim.streaming.sh`` or ``isaac-sim.streaming.bat`` and connect with the :ref:`isaac_sim_setup_livestream_webrtc`.
        * The first launch can take several minutes while the shader cache warms up. Watch the terminal output until the final load message appears.
        * The **Simple Room** and **Franka Emika Panda Arm** steps download assets over HTTPS from the |isaac-sim_short| asset service. Hosts on restricted networks need outbound HTTPS access to the asset service, or can use :ref:`Local Assets Packs <isaac_sim_setup_assets_content_pack>` for air-gapped environments.

#. From the terminal or command line, execute the following commands:

    .. tab-set::
        .. tab-item:: Linux (x86_64)

            .. code-block:: bash

                mkdir ~/isaacsim
                cd ~/Downloads
                unzip "isaac-sim-standalone-<version>-linux-x86_64.zip" -d ~/isaacsim
                cd ~/isaacsim
                ./post_install.sh
                ./isaac-sim.sh

        .. tab-item:: Linux (aarch64)

            .. code-block:: bash

                mkdir ~/isaacsim
                cd ~/Downloads
                unzip "isaac-sim-standalone-<version>-linux-aarch64.zip" -d ~/isaacsim
                cd ~/isaacsim
                ./post_install.sh
                ./isaac-sim.sh

        .. tab-item:: Windows

            .. code-block:: bat

                mkdir C:\isaacsim
                cd %USERPROFILE%/Downloads
                tar -xvzf "isaac-sim-standalone-<version>-windows-x86_64.zip" -C C:\isaacsim
                cd C:\isaacsim
                post_install.bat
                isaac-sim.bat

    Final load message example:

    .. image:: /images/final_load.png
            :align: center
            :width: 550

#.  After the Isaac Sim development environment opens fully, verify that you can see:

    .. image:: /images/isaac-sim-dev-env.png
      :align: center
      :width: 900
      :alt: Isaac Sim Development Environment

#. Select **Create > Environment > Simple Room**.

#. Select **Create > Robots > Franka Emika Panda Arm**.

    .. image:: /images/isaac-sim-simple-room.png
      :align: center
      :width: 900
      :alt: Isaac Sim Simple Room

#. On the leftmost side of your screen, look for an arrow button, and press it to play a short simulation.

Further Reading
-----------------

Try out the following tutorials:

   * :ref:`isaac_sim_app_intro_quickstart`
   * :ref:`isaac_sim_app_intro_quickstart_robot`

Then you can try :ref:`isaac_sim_robot_setup_tutorials`.
