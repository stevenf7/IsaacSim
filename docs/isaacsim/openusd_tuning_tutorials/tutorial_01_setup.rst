..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_tutorial_tuning_openusd_setup:

================================
Tutorial 1: Setup
================================

This tutorial runs in NVIDIA Isaac Sim with the Inspire Hand USD asset. Complete the following setup before starting the tutorials in this series.

Learning Objectives
===================

In this tutorial, you will:

- Understand the hardware and software requirements for the OpenUSD and Tuning Best Practices series.
- Obtain and extract the course USD files.
- Open the starting Inspire Hand scene in Isaac Sim.

Prerequisites
=============

- Basic familiarity with USD and Isaac Sim (stage, prims, layers).

- Understanding of rigid-body physics (mass, inertia, joints) is helpful but not required.

Get the Course USD Files
========================

#. The course files are located at ``IsaacSim/Samples/Rigging/Inspire/``.

Within that folder, the course files are organized into multiple checkpoint folders:

- ``module_1_start`` — Initial Inspire Hand USD ``inspire_hand.usda``.
- ``module_3_end-checkpoint_1`` — Checkpoint with collision filters configured.
- ``module_4_end-checkpoint_2`` — Checkpoint with mimic joints, joint drive maximums, and tuned gains for the finger joints configured.
- ``module_5_end-checkpoint_3`` — Checkpoint with all finger and thumb joint gains tuned and authored.

Open the Starting Scene
=======================

#. In ``IsaacSim/Samples/Rigging/Inspire/module_1_start/``, open ``inspire_hand.usda`` in Isaac Sim.
#. Select the ``inspire_hand`` prim.

Summary
=======

This tutorial covered:

- Where to obtain and how to organize the course USD checkpoint files.
- How to open the starting Inspire Hand scene in Isaac Sim.

Next Steps
^^^^^^^^^^

Continue to :ref:`isaac_sim_tutorial_tuning_openusd_module_1` (Tutorial 2: Asset Structure) to learn the USD Asset Structure 3.0 layout for the Inspire Hand.
