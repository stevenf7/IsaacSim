..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. meta::
  :title: Newton Physics Backend
  :keywords: lang=en Newton physics engine GPU Warp MuJoCo Isaac Sim


.. _newton_physics:

********************************************
Newton Physics Backend
********************************************

|isaac-sim_short| supports multiple physics backends. In addition to the default |physx| backend, you can now use Newton as the simulation backend.

`Newton <https://newton-physics.github.io/newton/>`_ is a GPU-accelerated, extensible, and differentiable physics simulation engine designed for robotics and research. Built on `NVIDIA Warp <https://nvidia.github.io/warp/>`_ and integrating `MuJoCo Warp <https://github.com/google-deepmind/mujoco_warp>`_, Newton provides high-performance simulation with multiple solver implementations, including XPBD, MuJoCo, Featherstone, and SemiImplicit. Newton is an open-source project maintained by Disney Research, Google DeepMind, and NVIDIA.


Overview
========

|isaac-sim_short| integrates Newton through three key extensions:

* **isaacsim.physics.newton**: The Newton physics backend implementation that:

  * Parses the USD stage and builds Newton simulation objects
  * Synchronizes simulation state with Fabric for rendering and data access
  * Provides a tensor-based API (``isaacsim.physics.newton.tensors``) compatible with NumPy, PyTorch, and Warp
  * Registers Newton with the unified physics interface

* **isaacsim.core.simulation_manager**: ``SimulationManager`` provides functionality for switching between physics engines at runtime, along with scene configuration classes (``PhysicsScene``, ``NewtonMjcScene``) for Newton-specific settings.

* **isaacsim.core.experimental.prims**: Uses ``isaacsim.physics.newton.tensors`` as its tensor backend when Newton is active. This extension provides engine-agnostic prim wrappers that work consistently across all physics backends.

When Newton is active, it replaces PhysX as the simulation backend while maintaining compatibility with standard USD Physics schemas used by your robot and environment assets.

Using the Experimental Core API
-------------------------------

The ``isaacsim.core.experimental`` extension provides engine-agnostic building blocks that ensure compatibility across different physics backends. User extensions and applications are highly recommended to use ``isaacsim.core.experimental`` to write simulation code that works with all physics backends (PhysX, Newton). Refer to `Core Experimental API documentation <../py/docs/overview/experimental.html>`_ for more details.


Launching Isaac Sim with Newton
===============================

You can launch |isaac-sim_short| with Newton as the default physics backend using the dedicated application file.

.. tab-set::
    .. tab-item:: Linux

        .. code-block:: bash

            ./isaac-sim.newton.sh

    .. tab-item:: Windows

        .. code-block:: bat

            isaac-sim.newton.bat

When launched with this application, Newton is automatically enabled and PhysX is disabled.


Switching Physics Engines at Runtime
====================================

You can switch between physics engines programmatically using the ``SimulationManager`` class. Use ``get_available_physics_engines()`` to list registered engines and ``switch_physics_engine()`` to activate Newton:

.. literalinclude:: ../snippets/physics/newton_physics/switch_physics_engine.py
    :language: python
    :start-after: # [snippet-start]

.. note::
   Switching physics engines should be done before starting the simulation. The switch deactivates the previous engine and activates the new one.
   Currently, only one physics engine can be active at a time.


Basic Usage Example
===================

The following example demonstrates setting up a simple physics scene with Newton:

.. literalinclude:: ../snippets/physics/newton_physics/basic_usage_example.py
    :language: python
    :start-after: # [snippet-start]


Scene Configuration
===================

Newton USD Schemas
------------------

Newton uses custom USD schemas to configure physics scenes. The `Newton USD Schemas <https://github.com/newton-physics/newton-usd-schemas>`_ project provides extensions to OpenUSD's UsdPhysics specification, allowing USD layers to fully specify Newton runtime parameters. These schemas follow a minimalist approach, capturing parameters that generalize across simulators and have clear physical meaning.

The key schemas include:

* **NewtonSceneAPI**: Base Newton schema applied to all physics scenes, providing common attributes like timestep (``newton:timeStepsPerSecond``), gravity settings, and solver iterations.
* **MjcSceneAPI**: MuJoCo solver-specific schema with integrator type, constraint solver algorithm, tolerance, and contact settings.

PhysicsScene Base Class
-----------------------

The ``PhysicsScene`` class provides a Python interface to the ``NewtonSceneAPI`` schema attributes. When you create a ``PhysicsScene``, it automatically applies the ``NewtonSceneAPI`` to the underlying USD prim, allowing you to configure common Newton settings:

.. literalinclude:: ../snippets/physics/newton_physics/physics_scene_config.py
    :language: python
    :start-after: # [snippet-start]

MuJoCo Solver Configuration
---------------------------

MuJoCo-specific parameters can be stored in USD through the MJC USD schemas, which capture settings for scenes, bodies, joints, and other elements. The ``MjcSceneAPI`` is one of these schemas, providing scene-level simulation parameters. The ``NewtonMjcScene`` class provides a Python interface to the ``MjcSceneAPI`` attributes, allowing you to configure MuJoCo solver settings directly on USD Physics Scene prims.

When you create a ``NewtonMjcScene``, it applies both ``NewtonSceneAPI`` and ``MjcSceneAPI`` to the prim:

.. literalinclude:: ../snippets/physics/newton_physics/mjc_scene_config.py
    :language: python
    :start-after: # [snippet-start]

.. note::
   Additional engine-specific scene classes to incorporate other solver-specific schemas (XPBD, Featherstone) are under development and will be available in future releases.

Robot Simulation Example
------------------------

The following example loads a Franka robot and simulates it with Newton:

.. literalinclude:: ../snippets/physics/newton_physics/robot_simulation_example.py
    :language: python
    :start-after: # [snippet-start]

.. figure:: /images/isim_6.0_full_ref_viewport_newton_engine_menu.png
    :align: center
    :width: 800

    The physics engine selector in the viewport menu.

For more on the physics umbrella UI (engine selector, scene settings, and related controls), see the `Omni Physics UI documentation <http://omniverse-docs.s3-website-us-east-1.amazonaws.com/omni_physics/110.0/dev_guide/physics_umbrella/physics_umbrella_ui.html>`_.

To compare simulation results between Newton and PhysX:

* stop the simulation
* switch the physics engine from "newton" to "physx" using the menu shown above
* play the simulation again


Asset Compatibility
===================


Not all existing PhysX-based assets in |isaac-sim_short| are compatible with Newton. There are certain limitations on the Newton/MuJoCo side that may prevent you from using older assets out of the box.
For instance:

  * Meshes with negative scales or zero volume are not yet fully supported. If you use an asset with such meshes, even if the simulation runs, the results may be incorrect.
  * Legacy assets tuned for PhysX may not produce exactly the same results with Newton/MuJoCo out of the box. You might need to adjust physics parameters (contact settings, solver iterations, and timestep) to achieve desired simulation behavior with Newton/MuJoCo.

With the new asset structure and MJCF/URDF importers, we are working toward converting each asset to both PhysX schemas and MJC USD schemas. This will enable consistent simulation behavior between the original MJCF asset (using MuJoCo) and the converted MJC USD asset (using Newton).

.. note::
    Newton integration in |isaac-sim_short| is experimental. The API and features may change in future releases.
    Many |isaac-sim_short| features and workflows that do not use the experimental core API are not yet supported with the Newton backend; support is being actively developed for the next release.
    The Newton backend in |isaac-sim_short| has been tested only with a limited set of robots, including G1, H1, T1, UR5e, Wonik Allegro, and Shadow Hand.


Additional Resources
====================

* `Newton Physics Documentation <https://newton-physics.github.io/newton/>`_
* `Newton USD Schemas <https://github.com/newton-physics/newton-usd-schemas>`_
* `NVIDIA Warp Documentation <https://nvidia.github.io/warp/>`_
* `MuJoCo Warp <https://github.com/google-deepmind/mujoco_warp>`_
* `Omni Physics UI documentation <http://omniverse-docs.s3-website-us-east-1.amazonaws.com/omni_physics/110.0/dev_guide/physics_umbrella/physics_umbrella_ui.html>`_ (physics umbrella UI, engine selector, scene settings)
