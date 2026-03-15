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
.. _Launch Cloud Shell: https://cloud.google.com/shell/docs/launching-cloud-shell
.. _GPU Zones: https://cloud.google.com/compute/docs/gpus/gpu-regions-zones
.. _Connect to Linux VMs using Google tools: https://cloud.google.com/compute/docs/instances/connecting-to-instance
.. _Default VPC network: https://cloud.google.com/vpc/docs/create-modify-vpc-networks
.. _SSH connection to VM instances: https://cloud.google.com/community/tutorials/ssh-via-iap


.. _Alibaba Cloud homepage: https://us.alibabacloud.com/


.. _isaac_sim_setup_alibaba_cloud_requirements:

Alibaba Cloud Deployment
############################################

Requirements
---------------------------

The requirements for running |isaac-sim| on Alibaba Cloud are:

* An Alibaba Cloud account with ECS Instance access that is able to create a Virtual Machine with GPU support.

* A GPU-accelerated compute-optimized instance with the following recommended specifications:

    * **GPU**: NVIDIA Tesla T4
    * **Instance type**: ecs.gn6i-c40g1.10xlarge
    * **Image**: Ubuntu Server 18.04 LTS

Setup
---------------------------

To launch the Alibaba ECS Instance, use the following steps:

#. Go to the `Alibaba Cloud homepage`_. Click **Log In**.

#. Select **RAM User** to log in.

    .. figure:: /images/isaac_cloud_alibaba_1.jpg
        :align: center
        :alt: Alibaba Cloud log in

#. As shown in the figure below, click the upper left corner, select **Cloud Server ECS**, click **Instance**, and click **Create Instance** to enter the instance creation interface.

    .. figure:: /images/isaac_cloud_alibaba_2.gif
        :align: center
        :alt: Create instance entry

    .. figure:: /images/isaac_cloud_alibaba_3.jpg
        :align: center
        :alt: Create instance UI

#. Create instance - basic configuration.

    As shown in the figure below, the basic configuration (configure as needed):

    * Choose payment mode.
    * Select the region and available area.
    * Select the instance, here select **T4** GPU.
    * The usage time of preemptible instances.
    * Number of purchased instances: **1**.
    * Select image: **Ubuntu**, **18.04 64 bit**.
    * Select storage, and set the cloud disk size to **500G**.
    * Click **Next: Network and Security Groups**.

    .. figure:: /images/isaac_cloud_alibaba_4.gif
        :align: center
        :alt: Basic config

#. Create instance - Network and Security Group as shown below, network and security group (configure as needed).

    .. figure:: /images/isaac_cloud_alibaba_5.gif
        :align: center
        :alt: Network and security group

#. Select the network, you can select an existing network, such as **isaac-sim-vpc-sh / vpc-uf6uov4wgyl1ru928mlbk** in this example. Or create a new **VPC**, click **Go to the console to create>**. A new **private network** can be created.

#. Select a security group, you can select an existing security group, such as **isaac-sim-open-all-ports/sg-uf6ix68ocmepok99yn2v** in this example. Or create a new security group, click **New Security Group>**. You can create a new **Security Group**.

    .. note::

        * Pay special attention here to ensure that all the ports required by |isaac-sim_short| are opened and secure.
          Open TCP port **49100** (WebRTC signaling), UDP port **47998** (WebRTC media stream), and TCP port **8210** (web viewer, Docker Compose only).
          Restrict access to your client IP for security.
        * For streaming client options (native desktop app or web-based viewer via Docker Compose), see :ref:`isaac_sim_manual_livestream_client`.

    .. figure:: /images/isaac_cloud_alibaba_6.jpg
        :align: center
        :alt: Streaming ports

#. Open ports as needed.

    .. figure:: /images/isaac_cloud_alibaba_7.jpg
        :align: center
        :alt: Open network ports

#. Click **Next: System Configuration**.

#. Create instance - system configuration as shown below, the system configuration (configure as needed).

    * Login credentials, select **key pair**.
    * Login name, select **root**.
    * Key pair, you can choose an existing key, or create a new key, the key is a file in **.pem** format.
    * Instance name.
    * Click **Next: Group Settings**.

    .. figure:: /images/isaac_cloud_alibaba_8.gif
        :align: center
        :alt: System configuration

#. Create instance - group configuration.

    * The default setting is good.
    * Click **Confirm Order**.

#. Confirm the order.

    * Click **Create instance**.

    .. figure:: /images/isaac_cloud_alibaba_9.jpg
        :align: center
        :alt: Create instance

#. After the instance has been created successfully, you can start the instance, and access the instance through the public network IP.

    .. figure:: /images/isaac_cloud_alibaba_10.jpg
        :align: center
        :alt: Run instance

#. See :doc:`Container Installation </installation/install_container>` to install NVIDIA drivers and other
   dependencies on the VM.

#. Proceed to :ref:`isaac_sim_setup_remote_headless_container`.

