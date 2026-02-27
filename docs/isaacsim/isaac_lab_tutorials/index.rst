..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_lab_tutorials_page:

=========
Isaac Lab
=========

Overview
--------

.. .. image:: /images/isaac_orbit_tasks.jpg
..     :width: 100%
..     :align: center

Isaac Lab is the official robot learning framework for |isaac-sim_short|, providing APIs and examples for reinforcement learning,
imitation learning, and more. The framework provides the ability to design tasks in different workflows, including
a modular design to easily and efficiently create robot learning environments, while leveraging the latest simulation capabilities.

Some of its core features include:

* Modular configuration-driven system to easily create and modify environments
* Flexible user-designed workflow for optimized performance
* Suite of robot learning environments for training and evaluation
* Support for different reinforcement learning and imitation learning libraries
* Connection to peripheral devices, such as game-pads and keyboards, for collecting demonstrations
* Ability to augment simulation with custom actuator models for sim-to-real transfer


Isaac Lab Resources
-------------------

For more information and documentation for Isaac Lab, see the following external references:

* `Isaac Lab Repository <https://github.com/isaac-sim/IsaacLab>`_

* `Isaac Lab Documentation <https://isaac-sim.github.io/IsaacLab>`_




Suggested Isaac Sim Tutorials
------------------------------
The following set of tutorials details usage of reinforcement learning related components in |isaac-sim_short|.



**Robot Setup**

- :ref:`Importing URDF <isaac_sim_app_tutorial_advanced_import_urdf>`
- :ref:`Importing MJCF <isaac_sim_app_tutorial_advanced_import_mjcf>`
- :ref:`Simulation Fundamentals <simulation_fundamentals>`

**Deploying Policies**

- :ref:`Rigging a Legged Robot for Policy Inference <isaac_sim_app_tutorial_rig_legged_robot>`
- :ref:`Policy Deployment <isaac_sim_app_tutorial_policy_deployment>`
- :ref:`Policy Deployment in ROS 2 <isaac_sim_app_tutorial_ros2_rl_controller>`

.. toctree::
    :hidden:
    :maxdepth: 1

    ./tutorial_policy_deployment
    ./../ros2_tutorials/tutorial_ros2_rl_controller


**Data Generation**

- :ref:`Getting Started with Cloner <isaac_sim_app_tutorial_cloner>`
- :ref:`Instanceable Assets <isaac_sim_app_tutorial_instanceable_assets>`


.. toctree::
    :hidden:
    :maxdepth: 1

    ./tutorial_cloner
    ./tutorial_instanceable_assets



**Python Scripting**

- :ref:`Python Scripting <isaac_sim_core_api_tutorials_page>`


Troubleshooting
---------------

.. toctree::
    :maxdepth: 1

    ./troubleshooting

Common Isaac Lab issues and their solutions are documented in the :ref:`isaac_sim_isaac_lab_troubleshooting` page. For general simulation troubleshooting, see :ref:`isaac_sim_troubleshooting`.


Deprecated Frameworks
---------------------

Isaac Lab will be replacing previously released frameworks for robot learning and reinforcement learning,
including `IsaacGymEnvs <https://github.com/isaac-sim/IsaacGymEnvs>`_ for the
`Isaac Gym Preview Release <https://developer.nvidia.com/isaac-gym>`_, `OmniIsaacGymEnvs <https://github.com/isaac-sim/OmniIsaacGymEnvs>`_ for
|isaac-sim_short|, and `Orbit <https://isaac-orbit.github.io>`_ for |isaac-sim_short|.

These frameworks are now deprecated in favor of continuing development in Isaac Lab.
We encourage users of these frameworks to migrate your work over to Isaac Lab.
Migration guides are available to support the migration process:

* Migrating from IsaacGymEnvs and Isaac Gym Preview Release: `link <https://isaac-sim.github.io/IsaacLab/main/source/migration/migrating_from_isaacgymenvs.html>`__
* Migrating from OmniIsaacGymEnvs: `link <https://isaac-sim.github.io/IsaacLab/main/source/migration/migrating_from_omniisaacgymenvs.html>`__
* Migrating from Orbit: `link <https://isaac-sim.github.io/IsaacLab/main/source/migration/migrating_from_orbit.html>`__



.. image:: /images/isaac_orbit_tasks.jpg
    :width: 100%
    :align: center