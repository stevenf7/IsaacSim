..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_tutorial_tuning_openusd_practice:

=================================================
Tutorial 7: Using the Dexterous Hand in Practice
=================================================

With asset structure verified, collision pairs filtered, and joint parameters tuned, the Inspire Hand in Isaac Sim is stable and ready for downstream use. This tutorial points you to applied demos and next steps.

Learning Objectives
===================

In this tutorial, you will:

- **Review** what you accomplished across the OpenUSD and Tuning Best Practices series.
- **Learn** next steps for using the tuned Inspire Hand (attach to an arm, watch demos, fine tune, extend to other hands).
- **Find** additional documentation and resources for PhysX and articulation.

Prerequisites
=============

- Complete :ref:`isaac_sim_tutorial_tuning_openusd_module_5` (Tutorial 6: Joint Gains Tuning). You should have a tuned, stable Inspire Hand USD.

What You Accomplished
=====================

- **Tutorial 2** — You inspected the multi-physics asset structure.
- **Tutorial 3** — You enabled joint and mass/inertia visualization, and verified collision meshes.
- **Tutorial 4** — You identified problematic self-collisions and added filtered pairs so the hand simulates without artifacts.
- **Tutorial 5** — You set mimic joints, max joint torque, and max velocity from specs.
- **Tutorial 6** — You tuned drive stiffness and damping with the Gain Tuner and analyzed results with the built-in charts.

You now have a tuned, stable robotic hand USD that can be attached to an arm and used with a grasping controller in Isaac Sim or Isaac Lab.

Next Steps
==========

- **Attach to an arm** — Use the hand as an end effector on a manipulator (e.g. Kuka) in Isaac Sim or Isaac Lab and run grasping or manipulation tasks.
- **Watch applied demos** — Look for Isaac Lab Kuka + Inspire Hand demos (e.g. from GTC) to see the same hand used in full workflows.
- **Fine Tune in Simple Scene Setups** — Bring the hand into simple scenes involving contact. Tune mimic joint compliance as needed for realistic and stable behavior in contact scenarios.
- **Extend tuning** — Apply the same process (collision filters, max force/velocity, stiffness/damping) to other digits or to custom dexterous hands.

Additional Resources
====================

- `NVIDIA Isaac Sim Documentation <https://docs.omniverse.nvidia.com/isaacsim/latest/>`_
- `Physics and Rigid Body Dynamics <https://docs.omniverse.nvidia.com/isaacsim/latest/core/physics_tutorials/tutorial_rigid_body_dynamics.html>`_ — For deeper coverage of PhysX and articulation.

Summary
=======

This tutorial reviewed what you accomplished in the series, outlined next steps for using the tuned Inspire Hand (attach to an arm, demos, fine tuning, extending to other hands), and pointed to additional resources for further learning.
