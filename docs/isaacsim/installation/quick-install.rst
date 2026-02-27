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

#. Download one of the following:

    * `Linux (x86_64) <https://download.isaacsim.omniverse.nvidia.com/isaac-sim-standalone-5.1.0-linux-x86_64.zip>`__.
    * `Linux (aarch64) <https://download.isaacsim.omniverse.nvidia.com/isaac-sim-standalone-5.1.0-linux-aarch64.zip>`__.
    * `Windows <https://download.isaacsim.omniverse.nvidia.com/isaac-sim-standalone-5.1.0-windows-x86_64.zip>`__.

#. From the terminal or command line, execute the following commands:

    .. tab-set::
        .. tab-item:: Linux (x86_64)

            .. code-block:: bash

                mkdir ~/isaacsim
                cd ~/Downloads
                unzip "isaac-sim-standalone-5.1.0-linux-x86_64.zip" -d ~/isaacsim
                cd ~/isaacsim
                ./post_install.sh
                ./isaac-sim.sh

        .. tab-item:: Linux (aarch64)

            .. code-block:: bash

                mkdir ~/isaacsim
                cd ~/Downloads
                unzip "isaac-sim-standalone-5.1.0-linux-aarch64.zip" -d ~/isaacsim
                cd ~/isaacsim
                ./post_install.sh
                ./isaac-sim.sh

        .. tab-item:: Windows

            .. code-block:: bat

                mkdir C:\isaacsim
                cd %USERPROFILE%/Downloads
                tar -xvzf "isaac-sim-standalone-5.1.0-windows-x86_64.zip" -C C:\isaacsim
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


