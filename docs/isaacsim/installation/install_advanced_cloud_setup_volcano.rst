..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _Volcano Engine: https://www.volcengine.com/
.. _veOmniverse console: https://console.volcengine.com/omniverse


.. _isaac_sim_setup_volcano_engine_requirements:

Volcano Engine Deployment
############################################

Requirements
---------------------------

Volcano Engine provides veOmniverse services which are fully equipped with |isaac-sim_short|, Isaac Lab, and |isaac-sim_short| assets, all integrated with Nucleus. Additionally, Volcano Engine offers a wealth of ready-to-use USD assets, enabling to leverage high-quality resources for realistic simulations. The requirements for running Omniverse Isaac Sim on Volcano Engine simply are :

* A Volcano Engine account with access to the veOmniverse, which can create a launcher service with GPU support.

* A GPU-accelerated compute-optimized instance with the following recommended specifications:

    * **GPU**: NVIDIA L40
    * **Service specification**: 仿真计算ls1n2.1x
    * **Image**: Ubuntu Server 22.04 LTS

Setup
---------------------------

To launch veOmniverse Server, use the following steps:

#. Go to the `Volcano Engine`_ homepage. Follow the path in the image to select the veOmniverse product.

    .. figure:: /images/isim_4.5_full_ref_gui_cloud_ve_1.png
        :align: center
        :alt: Volcano Engine homepage

#. Click the login （登陆）button in the top right corner to log in to Volcano Engine.

#. If you haven't applied for veOmniverse access yet, you will see the interface below. Click the "Apply for Experience"（申请体验）button as shown in the image to request service access from the Volcano team.

    .. figure:: /images/isim_4.5_full_ref_gui_cloud_ve_2.png
        :align: center
        :alt: Apply for access

#. Once you have applied for the access and received approval, you can directly log in to the `veOmniverse console`_  and be directed to the launcher page.

#. On the launcher page, as shown in the image below, you can create and manage launcher services that can run |isaac-sim| and |nuc|.

    .. figure:: /images/isim_4.5_full_ref_gui_cloud_ve_3.png
        :align: center
        :alt: Launcher page

#. Creating a launcher is a simple process. Click the "Create" button in the top left corner to enter the creation page. Fill in the basic information, select the simulation computing service "仿真计算Is1n2.1x" and proceed to create it with payment.

    .. figure:: /images/isim_4.5_full_ref_gui_cloud_ve_4.png
        :align: center
        :alt: Creating a launcher

#. Once the creation is completed, you can manage the launcher services on the list page. Simply copy the IP address and login credentials to access remotely via VDI.

    .. figure:: /images/isim_4.5_full_ref_gui_cloud_ve_5.png
        :align: center
        :alt: Launcher services

#. After logging into the launcher, the system comes pre-installed with commonly used tools such as Isaac Sim and Isaac Lab. These tools are continuously updated and ready for direct use.
