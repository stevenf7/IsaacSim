..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _Baidu AIHC Platform: https://cloud.baidu.com/product/aihc.html?track=d14999a11fc652a0f2b2c64cad2eae4400c75f47500d0870


.. _isaac_sim_setup_baidu_cloud_requirements:

Baidu Cloud Deployment
############################################

Requirements
---------------------------

Baidu AIHC Platform provides rapid deployment of |isaac-sim_short| and pre-installs some USD assets for |isaac-sim_short|.
The requirements for running |isaac-sim_long| on Baidu AIHC are as follows:

* Possess an account with access to Baidu AIHC Platform, and be able to purchase AIHC resource pools and GPU nodes.
* GPU-accelerated nodes, with recommended types including L20.

Setup
---------------------------

To start the deployment of |isaac-sim_short| on Baidu AIHC Platform, follow the steps below:

#. Navigate to the `Baidu AIHC Platform`_ homepage. As shown in the figure below, select "**Buy Now**" to access the **Baidu · AI Heterogeneous Computing Platform**.

    .. figure:: /images/isim_5.1_full_ref_gui_cloud_baiducloud_1.png
        :align: center
        :alt: Baidu AIHC Platform homepage

#. As shown in the figure, first select "**Quick Start**" in the left navigation bar, then search for "|isaac-sim_short|" — you will find the quick start guide for |isaac-sim_short| immediately.

    .. figure:: /images/isim_5.1_full_ref_gui_cloud_baiducloud_2.png
        :align: center
        :alt: Quickstart

#.  After accessing it, select "**Open in Development Machine**" and fill in the following information:

    a. Resource Configuration

        i. Enter the instance name
        ii. Version Content Selection Isaac Sim
        iii. Select the already created resource pool and queue
        iv. Resource Specifications: Choose GPU type (L20), number of GPUs (1), CPU cores (8 or more), and memory (64GiB or more)

    b. Environment Configuration:

        i. Enter the cloud disk capacity (500GiB recommended)
        ii. Storage Mounting: Mount the USD assets of Isaac Sim to the container by default

    c. Access Configuration: Select as needed
    d. Then confirm the payment and create the instance

    .. figure:: /images/isim_5.1_full_ref_gui_cloud_baiducloud_3.png
        :align: center
        :alt: Launcher page

#. After successful creation, you can log in to the development machine using WebIDE.
