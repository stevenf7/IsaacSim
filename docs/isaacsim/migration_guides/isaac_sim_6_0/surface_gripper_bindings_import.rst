..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaacsim_surface_gripper_bindings_migration:

========================
Surface Gripper Bindings
========================

The compiled Surface Gripper binding module (``_surface_gripper``) moved from the
``isaacsim.robot.surface_gripper`` package root into the ``bindings`` subpackage. This
matches the |isaac-sim_short| packaging convention, where compiled pybind11 modules live
under ``<package>/bindings/``.

Scripts that import the binding through its old submodule path fail at import time:

.. code-block:: python

   import isaacsim.robot.surface_gripper._surface_gripper
   # ModuleNotFoundError: No module named 'isaacsim.robot.surface_gripper._surface_gripper'

The interface is otherwise unchanged. ``acquire_surface_gripper_interface()``,
``release_surface_gripper_interface()``, ``GripperStatus``, and ``SurfaceGripperInterface``
behave exactly as before — only the import path changed. Update your imports as described
below.

.. _isaacsim_surface_gripper_bindings_import_mapping:

Import mapping
==============

The binding is available in two equivalent ways. Use the package-root re-export when you
want the module as a namespace, and the direct ``bindings`` submodule import when you only
need specific symbols.

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Old import (Isaac Sim 5.x and earlier)
     - New import (Isaac Sim 6.0 and later)
   * - ``import isaacsim.robot.surface_gripper._surface_gripper as sg``
     - ``from isaacsim.robot.surface_gripper import _surface_gripper as sg``
   * - ``from isaacsim.robot.surface_gripper._surface_gripper import acquire_surface_gripper_interface, GripperStatus``
     - ``from isaacsim.robot.surface_gripper.bindings._surface_gripper import acquire_surface_gripper_interface, GripperStatus``

.. _isaacsim_surface_gripper_bindings_code_examples:

Code examples
=============

**Acquire the interface and query gripper status**

.. code-block:: python

   # Old (Isaac Sim 5.x and earlier)
   import isaacsim.robot.surface_gripper._surface_gripper as surface_gripper

   gripper = surface_gripper.acquire_surface_gripper_interface()
   status = gripper.get_gripper_status("/World/SurfaceGripper")
   is_closed = status == surface_gripper.GripperStatus.Closed

.. code-block:: python

   # New (Isaac Sim 6.0 and later)
   from isaacsim.robot.surface_gripper import _surface_gripper as surface_gripper

   gripper = surface_gripper.acquire_surface_gripper_interface()
   status = gripper.get_gripper_status("/World/SurfaceGripper")
   is_closed = status == surface_gripper.GripperStatus.Closed

**Import specific symbols**

.. code-block:: python

   # Old (Isaac Sim 5.x and earlier)
   from isaacsim.robot.surface_gripper._surface_gripper import (
       acquire_surface_gripper_interface,
       GripperStatus,
   )

.. code-block:: python

   # New (Isaac Sim 6.0 and later)
   from isaacsim.robot.surface_gripper.bindings._surface_gripper import (
       acquire_surface_gripper_interface,
       GripperStatus,
   )
