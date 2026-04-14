.. _isaac_sim_app_tutorial_cuRobo:

===================
cuRobo and cuMotion
===================

.. note::
   The cuRobo and cuMotion tutorials here are no longer maintained. The :ref:`cuMotion integration <isaac_sim_cumotion>`
   contains much of the same functionality.

.. note::
   This cuRobo tutorial is not supported on aarch64 platforms.

Learning Objectives
===================

`cuRobo <https://curobo.org>`_ (also on `GitHub <https://github.com/NVlabs/curobo>`_) is a high-performance,
GPU-accelerated robotics motion generation library for robot manipulators, developed by NVIDIA Research.
It is a standalone Python library that interfaces directly with |isaac-sim|, simplifying both testing in simulation
and deploying on physical robots.

`NVIDIA cuMotion <https://nvidia-isaac-ros.github.io/concepts/manipulation/index.html#nvidia-cumotion>`_,
available as a Developer Preview in Isaac 3.0, is a production motion generation package for
manipulators.  The current version leverages cuRobo as its backend, providing collision-free motion planning using a
plugin for `MoveIt 2 <https://moveit.picknik.ai>`_ and a set of supporting ROS 2 packages.  For an example of using
cuMotion with |isaac-sim| using the ROS 2 bridge, see the relevant
`section <https://nvidia-isaac-ros.github.io/concepts/manipulation/cumotion_moveit/tutorial_isaac_sim.html>`_
of the Isaac ROS documentation.  This example is somewhat limited in Isaac 3.0 but will be expanded in a future
release.

In the remainder of this tutorial, we focus on direct integration of cuRobo into |isaac-sim|, covering cuRobo
installation and use, with examples for collision-free inverse kinematics, motion planning, and reactive
control (MPPI).

.. image:: /images/isaac_tutorial_advanced_cuRobo.gif
    :align: center


Getting Started
===============

**Prerequisites**

- Complete the :ref:`isaac_sim_app_tutorial_core_adding_manipulator` tutorial prior to beginning this tutorial.


Installation
============

Follow the `cuRobo installation instructions <https://curobo.org/get_started/1_install_instructions.html>`_ for
installing cuRobo and required libraries.  cuRobo supports |isaac-sim| 2022.2.1 and later.  Follow the
:ref:`workstation installation instructions <isaac_sim_app_install_workstation>` to install |isaac-sim|.


Examples
========

Using Isaac Sim with cuRobo
---------------------------

In the cuRobo documentation, refer to the
`"Using Isaac Sim" section <https://curobo.org/get_started/2b_isaacsim_examples.html>`_ for an overview of how cuRobo
is interfaced to Isaac Sim, along with a series of standalone examples demonstrating collision checking, motion
generation, inverse kinematics, model-predictive control, and multi-arm reaching.


Using Isaac Sim with cuRobo and nvblox
--------------------------------------

In the cuRobo documentation, refer to the
`"Using with Depth Camera" section <https://curobo.org/get_started/2d_nvblox_demo.html>`_ for examples of
obstacle-aware motion generation in |isaac-sim|, both with pre-generated signed distance fields (SDFs)
from `nvblox <https://github.com/nvidia-isaac/nvblox>`_ and with online mapping leveraging nvblox with a
physical RealSense depth camera.
