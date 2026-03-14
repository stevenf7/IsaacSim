..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_openusd_tuning_tutorials:

============================================================
OpenUSD and Tuning Best Practices Tutorial Series
============================================================

This tutorial series gives you the intuition and science of physics tuning for robotic assets in NVIDIA Isaac Sim so that your simulated robots behave realistically. Rigging and tuning complex assets—such as a dexterous hand—is foundational to successful robot learning and simulation. If the asset is not properly configured (collision meshes, mass properties, joint parameters), the simulation will be unstable, inaccurate, and unusable for training and validation.

Over this series, you work hands-on with the Inspire Hand asset in Isaac Sim to inspect the robot USD and asset structure, apply OpenUSD best practices for performance and stability, and tune joint parameters and control gains for stable, critically damped motion.

This series takes approximately 60–90 minutes to complete as a hands-on lab.

.. figure:: ../images/isim_6.0_full_tut_gui_inspire_hand_asset_structure_architecture.png
   :align: center
   :alt: Isaac Sim asset structure and Inspire Hand with joint and physics visualization.

Learning Objectives
===================

By the end of this series, you will be able to:

- **Explain** the end-to-end process for inspecting and preparing robot USD assets for simulation.
- **Apply** best practices to optimize the robot USD for performance and stability.
- **Tune** joint parameters and control gains to achieve stable, critically damped, and realistic robot motion in simulation.

We start by inspecting the robot USD, then configuring collision filters to manage self-collision, and finally tuning joint parameters: drive limits (max force, max velocity) in Tutorial 5 and stiffness and damping with the Gain Tuner in Tutorial 6. By the end, you will have a stable, functioning robotic hand ready to attach to an arm for a grasping controller.

Tutorials in This Series
=========================

.. toctree::
   :maxdepth: 1

   tutorial_01_setup
   tutorial_02_asset_structure
   tutorial_03_inspect_asset
   tutorial_04_collider_pairs
   tutorial_05_joint_drive_tuning
   tutorial_06_joint_gains_tuning
   tutorial_07_practice

To get started, see :ref:`isaac_sim_tutorial_tuning_openusd_setup` (Tutorial 1: Setup).
