..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _Omniverse Visual Debugger: https://nvidia-omniverse.github.io/PhysX/physx/5.4.2/docs/OmniVisualDebugger.html

.. _isaac_sim_physics:


===============================
Physics
===============================

On a high-level, simulations with |omni_physics| work as follows:

* The USD Physics schema of robot and environment assets are parsed and corresponding simulation objects are created in the selected physics backend.
* Then, for each discrete-time step of the simulation, |physics_short| advances the simulation objects given their current state and additional inputs such as, for example, control-policy torques.
* The updated state is written back to USD by default, where the state can be further processed by the user, a reinforcement-learning policy, or other extensions such as the |rtx|.
* |omni_physics| propagates runtime changes to physics parameters in USD to the physics objects.

|isaac-sim_short| supports multiple physics backends: the default |physx| backend and the experimental Newton backend.


.. toctree::
    :maxdepth: 3

    simulation_fundamentals
    new_physics_engine
    newton_physics
    physics_resources

Tools
==========

.. toctree::
    :maxdepth: 1

    :doc:`Physics Simulation Management <kit-physics:extensions/ux/source/omni.physx.ui/docs/dev_guide/sim_management>`
    joint_inspector
    physics_static_collision
    ext_isaacsim_inspect_physics
    :doc:`Physics Debug Window <kit-physics:extensions/ux/source/omni.physx.ui/docs/dev_guide/physics_debug_wnd>`


.. _isaac_sim_physics_links:

Additional Resources
====================================================


* |omni_physics| :doc:`core documentation <kit-physics:index>` and `programming guide <https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/index.html>`_
* `USD Physics Schemas <https://openusd.org/release/api/usd_physics_page_front.html>`_ and |physx|-engine-specific `Physx Schemas <https://docs.omniverse.nvidia.com/kit/docs/omni_usd_schema_physics/latest/annotated.html>`_
* Explore further |omni| :ref:`simulation extensions <SimOverview>`.
* `PhysX SDK <https://nvidia-omniverse.github.io/PhysX/physx/5.4.2/index.html>`_
* `Omniverse Visual Debugger <https://nvidia-omniverse.github.io/PhysX/physx/5.4.2/docs/OmniVisualDebugger.html>`_
* :doc:`Flow: Fluid Dynamics <extensions:ext_fluid-dynamics>`
* `NVIDIA Warp <https://nvidia.github.io/warp/index.html>`_


