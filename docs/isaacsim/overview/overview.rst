..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. meta::
    :title: Isaac Sim Introduction
    :keywords: lang=en isaac isaac-sim robotics simulation introduction

.. figure:: /images/hero_shot.png
    :align: center

==========================================
What Is |isaac-sim_short|?
==========================================

NVIDIA Isaac Sim™ is a reference application built on NVIDIA Omniverse that enables developers to develop, simulate, and test AI-driven robots in physically-based virtual environments.

Design
====================

|isaac-sim_short| comes with a collection of workflows for importing and tuning mechanical
systems designed in the most common formats including `Onshape <https://docs.omniverse.nvidia.com/extensions/latest/ext_onshape.html#isaac-onshape-importer>`_, the :ref:`Unified Robotics Description Format (URDF) <isaac_sim_app_tutorial_advanced_import_urdf>`, and the :ref:`MuJoCo XML Format (MJCF)<isaac_sim_app_tutorial_advanced_import_mjcf>`.
This is made possible through the use of the `Universal Scene Description (USD)`_, an easily extensible, open source 3D scene description API that
serves as the unifying data interchange format at the heart of |isaac-sim_short|.

Tune and Train
====================
The core functionality of |isaac-sim_short| is the simulation itself: a high-fidelity GPU-based `PhysX engine`_, capable of
supporting :ref:`multi-sensor RTX rendering <isaac_sim_sensor_simulation>` at an industrial scale. |isaac-sim_short|'s direct access to the GPU enables the platform to support the simulation of various
kinds of sensors including :ref:`cameras <isaacsim_sensors_camera>`, :ref:`Lidars <isaacsim_sensors_rtx_lidar>`, and :ref:`contact sensors <isaacsim_sensors_physics_contact>`. This
in turn facilitates the simulation of digital twins, allowing your end-to-end pipelines to run before ever needing to turn on a real robot. |isaac-sim_short| provides a suite of tools for collecting synthetic
data with `Replicator`_, orchestrating simulated environments through `Omnigraph`_, tuning `PhysX simulation`_ parameters to match reality, and finally training control agents
through various methods like Reinforcement Learning (RL) with :ref:`Isaac Lab<isaac_lab_tutorials_page>`.

Deploy
====================
|isaac-sim_short| comes pre-equipped with all of the components necessary to not only deploy agents to real robots, but also build applications that are fully integrable with
such systems. `Omniverse <https://docs.omniverse.nvidia.com/dev-guide/latest/index.html>`_ provides `APIs <https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/guide/kit_overview.html>`_ for app infrastructure including GUI creation and file management.
The |isaac-sim_short| platform also provides bridge APIs to :ref:`ROS 2 <isaac_ros2_tutorials_page>`, for direct communication between live robots
and the simulation, as well as `NVIDIA Isaac ROS <https://nvidia-isaac-ros.github.io/>`_, a collection of performant, hardware-accelerated ROS 2 packages for making autonomous robots.

Getting Started
==========================================
- :ref:`isaac_sim_quick_install`: The quick install to get you started in under an hour.
- :ref:`isaac_sim_app_intro_quickstart`: The tutorial to get your feet wet with |isaac-sim|.
- :ref:`isaac_sim_app_install_workstation`: Installation guide for a local workstation.
- :ref:`isaac_sim_app_install_container`: Installation guide for a remote headless server.
- :ref:`Development Tools<isaac_sim_development_tools_tutorials>`: The tools and environments for debugging and development.
- :ref:`Python Scripting<isaac_sim_app_python_scripting_overview>`: Tools and tutorials for building environments, robots, and tasks using |isaac-sim| Core Python APIs.
- :ref:`isaac_sim_gui_tutorials_page`: The fundamental concepts of robotics in |isaac-sim| via GUI.
- :ref:`Importer and Exporter<isaac_sim_importers_and_exporters>`: Tools for importing and exporting robots and assets from various file formats.
- :ref:`Robot setup<isaac_sim_robot_setup>`: Isaac Sim tools for modifying robots.
- :ref:`isaac_sim_robot_setup_tutorials`: Tutorial series for using the robot setup tools and workflows.
- :ref:`Robot simulation<isaac_sim_robot_simulation>`: Controllers, motion generation tools for simulating robots.
- :ref:`isaac_sim_ros_ros2_tutorials`: ROS 2 bridges and interfaces.
- :ref:`Isaac Lab<isaac_lab_tutorials_page>`: Reinforcement learning framework and Cloner APIs.
- :ref:`Synthetic Data Generation<isaac_synthetic_data_generation_page>`: Collection of tools and workflows for generating synthetic data.
- :ref:`Digital Twin<isaac_sim_app_digital_twin_index>`: Tools for building and operating digital twins, such as :ref:`Warehouse logistics <isaac_sim_app_warehouse_logistics_index>`, :ref:`Cortex<isaac_sim_app_tutorial_cortex_1_overview>`, and :ref:`Mapping<ext_isaacsim_asset_generator_occupancy_map>`.

System Architecture
==========================================

.. figure:: /images/Isaac_Sim_System_Diagram.png
    :align: center
    :alt: Isaac Sim System Architecture Diagram

The purpose of |isaac-sim_short| is to support the creation of new robotics tools and empower the ones that already exist. The platform provides a flexible API for both C++ and Python and can be integrated into a project to varying degrees depending on your needs. The goal of the platform is not to compete with current or existing software, but to collaborate with and enhance it. To this end, many components of |isaac-sim_short| are open source and freely available for independent use. You may want to design your robot in OnShape, simulate its sensors with |isaac-sim_short|, and control the stage through ROS or some other messaging system. Likewise, it is also possible to build a complete, standalone application entirely on the platform provided by Isaac Sim!

|kit|
=================

|isaac-sim_short| uses the Omniverse™ Kit, a toolkit for building native Omniverse applications and microservices. |kit| provides a wide variety of functionality through a set of lightweight plugins. Plugins are authored with C interfaces for persistent API compatibility; however, a Python interpreter is also provided for accessible scripting and customization.

The Python API can be used to write new extensions to |kit| or new experiences for Omniverse.

Development Workflows
==========================================

.. image:: /images/Isaac_Sim_Workflows_Diagram.png
    :align: center
    :class: largepadding

|isaac-sim_short| is built on C++ and Python, and operates most commonly through the use of compiled plugins and bindings respectively. This means the platform is capable of supporting a wide variety of workflows for building and interacting with projects that make use of |isaac-sim_short|. |isaac-sim_short| comes with a full, standalone Omniverse application for interacting with and simulating robots, and while this is the most common way users interact with the platform, it is by no means the only method. |isaac-sim_short| also provides direct Python development support in the form of extensions for VS Code and Jupyter Notebooks. |isaac-sim_short| is not limited to synchronous operation either, and can operate with hardware in the loop through ROS 2, facilitating sim-to-real transfer and digital twins.

.. _NVIDIA Omniverse™ |isaac-sim_short|: https://developer.nvidia.com/isaac-sim
.. _NVIDIA Omniverse™: https://docs.omniverse.nvidia.com
.. _Omniverse Kit Programming Manual: https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/guide/kit_overview.html
.. _What is USD?: https://developer.nvidia.com/usd
.. _USD API: https://graphics.pixar.com/usd/release/index.html
.. _GUI API: https://docs.omniverse.nvidia.com/kit/docs/omni.ui/latest/API.html
.. _USD Glossary of Terms & Concepts:  https://graphics.pixar.com/usd/release/glossary.html
.. _NVIDIA USD tutorials: https://developer.nvidia.com/usd/tutorials
.. _Universal Scene Description (USD): https://openusd.org/release/index.html
.. _NVIDIA USD API: https://docs.omniverse.nvidia.com/kit/docs/pxr-usd-api/latest/pxr.html
.. _Replicator: https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator.html
.. _Omnigraph: https://docs.omniverse.nvidia.com/extensions/latest/ext_omnigraph.html
.. _PhysX simulation: https://docs.omniverse.nvidia.com/extensions/latest/ext_simulation.html
.. _PhysX engine: https://developer.nvidia.com/physx-sdk
.. _contact sensors: https://docs.omniverse.nvidia.com/isaacsim/latest/features/sensor_simulation/isaacsim_sensors_physics_contact.html#contact-sensor

USD
========================
|isaac-sim| uses the USD interchange file format to represent scenes. Universal Scene Description
(USD) is an easily extensible, open-source 3D scene description file format developed by Pixar
for content creation and interchange among different tools. Because of its power and versatility,
USD is being adopted widely, not only in the visual effects community, but also in architecture,
design, robotics, manufacturing, and other disciplines.

- For a more in-depth look at USD in |omni|, see the |nv| USD primer `What is USD?`_.
- See the `USD API`_ docs for more details.
- See the `NVIDIA USD API`_ for our Python wrappers around USD.
- See the `USD Glossary of Terms & Concepts`_ for more details.
- See the `NVIDIA USD tutorials`_ for a step-by-step introduction to USD.
