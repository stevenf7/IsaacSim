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


.. _Tencent Cloud homepage: https://www.tencentcloud.com/
.. _GN7: https://www.tencentcloud.com/document/product/560/19701#GN7


.. _isaac_sim_setup_tencent_cloud_requirements:

Tencent Cloud Deployment
############################################

Requirements
---------------------------

Here are the requirements for running |isaac-sim| on Tencent Cloud:

* A Tencent Cloud account with Computing Instance access that is able to create a Virtual Machine with GPU support.

* An Cloud Virtual Machine with the following recommended specifications:

    * **GPU**: NVIDIA Tesla T4
    * **Machine type**: `GN7`_
    * **Image**: Ubuntu Server 18.04.1 LTS

Setup
---------------------------

To log in to Tencent Cloud, use the following steps:

#. Go to the `Tencent Cloud homepage`_.

    .. figure:: /images/isaac_cloud_tencent_1.jpg
        :align: center
        :alt: Tencent Cloud homepage

#. Click **Log in**.

    .. figure:: /images/isaac_cloud_tencent_2.jpg
        :align: center
        :alt: Tencent Cloud log in

#. Select enterprise user login, click **CAM user sign in**.

    .. figure:: /images/isaac_cloud_tencent_3.jpg
        :align: center
        :alt: CAM user sign in

#. Enter **Root account ID**, **Sub-user name**, and **Password**. Then click **Sign in**.

    .. figure:: /images/isaac_cloud_tencent_4.jpg
        :align: center
        :alt: Enterprise sign in

#. Enter the following page:

    .. figure:: /images/isaac_cloud_tencent_5.jpg
        :align: center
        :alt: Log in interface


To launch the Tencent Cloud Virtual Machine, use the following steps:

#. In the **Products** drop-down tab, click **04 Cloud Virtual Machine**.

    .. figure:: /images/isaac_cloud_tencent_6.jpg
        :align: center
        :alt: Select Cloud Virtual Machine

#. Click **Get Started**.

    .. figure:: /images/isaac_cloud_tencent_7.jpg
        :align: center
        :alt: Cloud Virtual Machine

#. Enter the **Cloud Virtual Machine** page, select **Instances** in the leftmost column, you can create a new instance through the **Create** button, or start an existing instance by using the **Start Up** button. Here, use the **Create** button to create a new instance.

    .. figure:: /images/isaac_cloud_tencent_8.jpg
        :align: center
        :alt: Create instance

#. Enter the **Cloud Virtual Machine (CVM)** interface as follows, and create a cloud service instance.

    .. figure:: /images/isaac_cloud_tencent_9.jpg
        :align: center
        :alt: CVM

#.  For Basic configurations, choose **Spot instances** for **T4** graphics card. **China**, **Guangzhou** are selected for the region, **Random** is selected for the Availability Zone. You can also choose according to your needs.

    .. figure:: /images/isaac_cloud_tencent_10.jpg
        :align: center
        :alt: Basic configuration

#. For Instance configurations, choose **GPU-based**, **GPU Compute GN7** (that is, **T4** graphics card). For the operating system of the instance, select **Ubuntu**, **18.04** version. Do not check **Install GPU driver automatically**. Select **500GB** or larger capacity for Storage.

    .. figure:: /images/isaac_cloud_tencent_11.jpg
        :align: center
        :alt: Instance configuration

#. After **Select basic configurations** is completed, click **Next: Configure network and host**, and click **Confirm**.

#. To create a network, click **create a VPC** and **a subnet** respectively to create a private network and a subnet. Then follow the prompts. For network **Bandwidth**, select **20Mbps**.

    .. note::

        * When creating a **subnet**, the region selection of **Availability zone** must be the same as **Availability zone** of **Instance configurations** in **Select basic configurations** section.

    .. figure:: /images/isaac_cloud_tencent_12.jpg
        :align: center
        :alt: CVM network

    .. figure:: /images/isaac_cloud_tencent_13.jpg
        :align: center
        :alt: CVM VPC

#. Mandatory. Select **Security Group** to ensure that all the ports required for |isaac-sim_short| remote connection are open. For simplicity, you can choose **Open all ports**. During actual operation, to ensure security, you must select a port that is open to the outside world.

    .. note::

        * Pay special attention here, you must ensure that all the ports required by |isaac-sim_short| are opened and secure.
        * For details, see :ref:`isaac_sim_setup_livestream_webrtc`.

    .. figure:: /images/isaac_cloud_tencent_14.jpg
        :align: center
        :alt: CVM network security

    .. figure:: /images/isaac_cloud_tencent_15.jpg
        :align: center
        :alt: CVM create security group

    .. figure:: /images/isaac_cloud_tencent_16.jpg
        :align: center
        :alt: CVM configure security group

    .. figure:: /images/isaac_cloud_tencent_17.jpg
        :align: center
        :alt: CVM select security group

#. For Other Settings, create a key for **ssh** connections. You can select an existing secret key or create a new secret key. The secret key is a file in ***.pem** format.

    .. figure:: /images/isaac_cloud_tencent_18.jpg
        :align: center
        :alt: CVM create key

#. After **Config network and host** is complete, click **Next: Confirm configuration**.

    .. figure:: /images/isaac_cloud_tencent_19.jpg
        :align: center
        :alt: CVM confirm configuration

#. After the instance has been created successfully, you can start the instance, and access the instance through the public network IP.

#. See :doc:`Container Installation </installation/install_container>` to install NVIDIA Drivers and other
   dependencies on the VM.

#. Proceed to :ref:`isaac_sim_setup_remote_headless_container`.

