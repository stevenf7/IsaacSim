..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _Key Pair Guide: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html#create-a-key-pair
.. _Connecting to Your Linux Instance from Windows Using PuTTY: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/putty.html
.. _Visual Studio Code: https://code.visualstudio.com/download
.. _Remote-SSH extension: https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh
.. _Create a Linux virtual machine in the Azure portal: https://docs.microsoft.com/en-us/azure/virtual-machines/linux/quick-create-portal

.. _isaac_sim_setup_container_requirements:

Remote Workstation Deployment
############################################

Requirements
---------------------------

The requirements for running |isaac-sim| on a headless remote workstation are:

  * See :ref:`isaac_sim_requirements_isaac_sim_system`.
  * See :doc:`Container Installation</installation/install_container>`.

Setup
---------------------------

Follow these steps to access a remote Ubuntu workstation:

#. If you have access to the remote workstation physically, install an SSH server to allow remote access:

    .. code-block:: console

        $ sudo apt update
        $ sudo apt install openssh-server

#. Run the following command to get the remote workstation IP address:

    .. code-block:: console

        $ ifconfig

#. Run the following command to access the remote workstation:

    .. code-block:: console

        $ ssh <remote_workstation_username>@<remote_workstation_ip_address>
        <remote_workstation_username>@<remote_workstation_ip_address>'s password:

#. Proceed to :ref:`isaac_sim_setup_remote_headless_container`.
