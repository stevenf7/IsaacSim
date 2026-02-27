..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. meta::
    :title: Isaac Sim Installation
    :keywords: lang=en isaac isaac-sim requirements installation

.. _Unix Driver Archive: https://www.nvidia.com/en-us/drivers/unix/


.. _isaac_sim_requirements:

=====================================
|isaac-sim_short| Requirements
=====================================

.. hint::

    By installing Isaac Sim, you can run the :ref:`isaac_sim_compatibility_checker` lightweight app to check if your machine meets the system requirements and compatibility.

.. _isaac_sim_requirements_isaac_sim_system:

System Requirements
--------------------------------------------------

.. dropdown:: Requirements for x86_64
   :open:

    .. _isaac_sim_requirements_x86_64:

    =================================== ====================================== ========================================== =============================================
    Element                             Minimum Spec                           Good                                       Ideal
    =================================== ====================================== ========================================== =============================================
    OS                                  | Ubuntu 22.04/24.04                   | Ubuntu 22.04/24.04                       | Ubuntu 22.04/24.04
                                        | Windows 10/11                        | Windows 10/11                            | Windows 10/11
    CPU                                 | Intel Core i7 (7th Generation)       | Intel Core i7 (9th Generation)           | Intel Core i9, X-series or higher
                                        | AMD Ryzen 5                          | AMD Ryzen 7                              | AMD Ryzen 9, Threadripper or higher
    Cores                               | 4                                    | 8                                        | 16
    RAM [1]_                            | 32GB                                 | 64GB                                     | 64GB
    Storage                             | 50GB SSD                             | 500GB SSD                                | 1TB NVMe SSD
    GPU                                 | GeForce RTX 4080                     | GeForce RTX 5080                         | RTX PRO 6000 Blackwell
    VRAM [1]_                           | 16GB [2]_                            | 16GB                                     | 48GB
    Driver [3]_                         | Linux: 580.65.06                     | Linux: 580.65.06                         | Linux: 580.65.06
                                        | Windows: 580.88                      | Windows: 580.88                          | Windows: 580.88
    =================================== ====================================== ========================================== =============================================

    .. [1] More RAM and VRAM is recommended for advanced usage of |isaac-sim_short|. Isaac Lab usage will require additional RAM and VRAM for training.
    .. [2] GPUs with less than 16GB VRAM may be insufficient to run a complex scene rendering more than 16MP per frame. Consider upgrading to a higher spec if that is your use case.
    .. [3] Isaac Sim was tested on these driver versions. See :doc:`Technical Requirements<dev-guide:common/technical-requirements>` for recommended driver versions.

    .. note::
        - The |isaac-sim_short| container is only supported on Linux.
        - An Internet connection is required to access the |isaac-sim_short| assets online and to run some extensions.
        - GPUs without RT Cores (A100, H100) are not supported.
        - Due to VRAM constraints, some tutorials and benchmarks may not run on GPU below the minimum specifications. Workflows leveraging a large number of sensors are particularly affected.
        - See :doc:`Linux Troubleshooting<dev-guide:linux-troubleshooting>` to resolve driver installation issues on Linux.
        - We recommend installing the **Latest Production Branch Version drivers** from the `Unix Driver Archive`_ using the :code:`.run` installer on Linux if you are on a new GPU or experiencing issues with the current drivers.
        - Windows 10 support ends on October 14, 2025. After this date, Microsoft will no longer provide free security, feature, or technical updates for Windows 10. As a result, we will be dropping support for Windows 10 in future releases of Isaac Sim to ensure the security and functionality of our software.

.. dropdown:: Requirements for aarch64

    .. _isaac_sim_requirements_aarch64:

    =================================== ======================================
    Element                             Specifications
    =================================== ======================================
    Device                              | |spark_long|
    OS                                  | NVIDIA DGX OS 7.2.3
    Driver [4]_                         | 580.95.05
    =================================== ======================================

    .. [4] Isaac Sim was tested on these driver versions. See :doc:`Technical Requirements<dev-guide:common/technical-requirements>` for recommended driver versions.

    .. note::
        - Isaac Sim aarch64 builds are currently only supported on |spark_short| system.
        - The |isaac-sim_short| container is only supported on Linux.
        - An Internet connection is required to access the |isaac-sim_short| assets online and to run some extensions.

    .. _isaac_sim_requirements_aarch64_limitations:

    .. rubric:: Limitations

    .. warning::
        Here are the limitations of running |isaac-sim_short| 5.1 on |spark_short|:
            - :doc:`Hub Workstation Cache<utilities:cache/hub-workstation>` is not supported.
            - :ref:`Livestreaming <isaac_sim_setup_livestream_webrtc>` is not supported.
            - Importing OBJ files is not supported. This impacts the ability to use the :ref:`urdf importer <isaac_sim_urdf_importer>` for assets that contain OBJ meshes.
            - :ref:`isaac_sim_app_template` is not supported.
            - :ref:`isaac_sim_app_tutorial_cuRobo` is not supported.
