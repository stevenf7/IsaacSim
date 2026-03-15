..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaac_sim_faq:

=======================
FAQ
=======================

.. dropdown:: General

   .. rubric:: Is there a way to use |isaac-sim_short| without an internet connection?

   Yes. Download the :ref:`isaac_sim_latest_release` of |isaac-sim_short| Assets Packs. See :ref:`isaac_sim_setup_assets_content_pack` to run local assets.

   .. rubric:: Is there a way to use |isaac-sim_short| without downloading it locally?

   Yes. See :ref:`isaac_sim_app_install_cloud`


.. dropdown:: Performance

   .. rubric:: |isaac-sim_short| is loading very slowly.

   The first time you open |isaac-sim|, it may take a while for the materials to compile.

   If a large asset is loading very slowly, it is likely that the materials are compiling. This should happen only on first load of the asset.

   See :ref:`isaac_sim_paths_shadercache` for location of the local shader cache.

   For more information, see :ref:`isaac_sim_app_install_workstation` for how to install.

   .. rubric:: |isaac-sim_short| is running very slowly.

   To speed up the simulation, you can reduce the complexity of the scene and robot, such as reducing the number of joints and links, simplify collision geometry and texture. You can also modify simulation step settings. For more information, see :ref:`isaac_sim_performance_optimization_handbook`.


.. dropdown:: Additional FAQ Pages
   :open:

   Many sections have dedicated FAQ and troubleshooting pages, check them for more targeted information.

   - :ref:`Installation FAQ<isaac_sim_setup_faq>`
   - :ref:`License FAQ<isaac_sim_license_faq>`
   - :ref:`isaac_sim_troubleshooting`
   - :ref:`isaac_sim_robot_simulation_tips`

.. - :ref:`isaac_sim_physics_tips`
