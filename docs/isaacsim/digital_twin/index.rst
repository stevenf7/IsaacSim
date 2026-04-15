..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_digital_twin_index:

==========================================
Digital Twin
==========================================


.. _isaac_sim_app_warehouse_logistics_index:

Warehouse Logistics
===============================

The warehouse logistics section contains extensions for building warehouses, generating conveyor belts, animating people, and using NVIDIA cuOpt for routing optimization.


.. toctree::
    :maxdepth: 1

    ./warehouse_logistics/ext_omni_warehouse_creator
    ./warehouse_logistics/ext_isaacsim_asset_gen_conveyor
    ./warehouse_logistics/tutorial_static_assets
    ./warehouse_logistics/logistics_tutorial_cuopt


.. _isaac_sim_app_cortex_index:

Cortex
=====================

.. warning::
    [DEPRECATED]: The Cortex framework has been deprecated as of Isaac Sim 6.0.0 and will be removed in a future release.
    For behavior programming, migrate to open-source libraries such as
    `py_trees <https://py-trees.readthedocs.io/en/devel/>`_ for behavior trees or
    `transitions <https://github.com/pytransitions/transitions>`_ for finite state machines.
    Isaac Sim 7.0 will include examples using these libraries.

Cortex ties the robotics tooling of Isaac Sim together into a cohesive collaborative robotic system. The Cortex tutorials start with an overview of the core concepts and then steps through a series of examples of increasing sophistication.

..


.. toctree::
    :maxdepth: 1

    ../cortex_tutorials/tutorial_cortex_1_overview
..    ../cortex_tutorials/tutorial_cortex_2_decider_networks
..    ../cortex_tutorials/tutorial_cortex_3_example_peck_games
..   ../cortex_tutorials/tutorial_cortex_4_franka_block_stacking
..    ../cortex_tutorials/tutorial_cortex_5_ur10_bin_stacking
..    ../cortex_tutorials/tutorial_cortex_7_cortex_extension


.. _isaac_sim_app_mapping_index:

Mapping
=====================

.. toctree::
   :maxdepth: 1

   ext_isaacsim_asset_generator_occupancy_map


Troubleshooting
---------------

.. toctree::
    :maxdepth: 1

    ./troubleshooting

Common Digital Twin issues and their solutions are documented in the :ref:`isaac_sim_digital_twin_troubleshooting` page. For general simulation troubleshooting, see :ref:`isaac_sim_troubleshooting`.
