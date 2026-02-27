..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_isaac_lab_troubleshooting:


=============================
Isaac Lab Troubleshooting
=============================

This page consolidates troubleshooting information for Isaac Lab components in Isaac Sim.

Common Issues
=============

Installation Issues
^^^^^^^^^^^^^^^^^^^^^^^^^

* Make sure you have the correct Python version (3.9+) when setting up Isaac Lab
* If encountering `ModuleNotFoundError`, ensure all dependencies are installed via `pip install -e .` in the Isaac Lab repository
* For GPU compatibility issues, verify that your CUDA version matches the requirements for Isaac Lab

Performance Issues
^^^^^^^^^^^^^^^^^^^^^^^^^

* For slow training performance, try reducing the number of environments or the complexity of the scene
* Memory issues can be resolved by setting smaller batch sizes or reducing environment complexity
* To improve frame rates during training, consider using fewer sensors or reducing their resolution

Environment Setup Issues
^^^^^^^^^^^^^^^^^^^^^^^^^

* If robots fail to initialize, check that the URDF/USD files are correctly specified
* For task initialization failures, ensure your task configuration files are properly formatted
* Make sure reward terms and observations are correctly defined in your environment configurations

Policy Deployment Issues
^^^^^^^^^^^^^^^^^^^^^^^^^

* When deploying trained policies, verify the observation space matches the training environment
* For poor policy performance after deployment, check if the simulation parameters match the training settings
* If policy files fail to load, verify they are in the correct format supported by Isaac Lab 