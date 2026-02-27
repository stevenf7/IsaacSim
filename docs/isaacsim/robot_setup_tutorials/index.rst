..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaac_sim_robot_setup_tutorials:

==================================
Robot Setup Tutorials Series
==================================

The GUI tutorials walk you through setting up your virtual world and building robot digital twins with various |isaac-sim| features. In the process, you will learn where to find frequently used properties, settings, and tools, and familiarize yourself with the toolbars, icons, and OpenUSD standards.

**Important:** These tutorials are designed as a progressive learning path from beginner to advanced. We recommend starting with the *Setup a Wheeled Robot* section, as it covers essential beginner concepts like environment setup, basic robot assembly, and fundamental rigging techniques that are required for all robot types.

**Beginner Level** - Setup a Wheeled Robot
==========================================

Start here to learn fundamental concepts that apply to all robot types:

.. toctree::
    :maxdepth: 1

    ./tutorial_intro_environment_setup
    ./tutorial_intro_assemble_robot
    ./tutorial_gui_simple_robot
    ./tutorial_gui_camera_sensors
    ./rig_mobile_robot

**Intermediate Level** - Setup a Manipulator
============================================

Build upon the foundational knowledge to work with more complex robot structures:

.. toctree::
    :maxdepth: 1

    ./tutorial_import_assemble_manipulator
    ./tutorial_configure_manipulator
    ./tutorial_generate_robot_config
    ./tutorial_pickplace_example

**Advanced Level** - Asset Tuning and Optimization
==================================================

Master advanced techniques for complex robot configurations:

.. toctree::
    :maxdepth: 1

    ./rig_closed_loop_structures
    ./joint_tuning
    ./optimizing_asset
    ./tutorial_rig_legged_robot