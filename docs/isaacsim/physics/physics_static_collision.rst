..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_static_collision_utils:

********************************************
Physics Static Collision Extension
********************************************

.. _isaac_static_collision_utils_about:


The :ref:`isaac_static_collision_utils` Extension is used to visualize collision meshes. Use this Utility extension to add static collision APIs to an entire :ref:`isaac_sim_glossary_stage`. The extension can also be used to remove all physics related APIs for testing purposes.

This extension is enabled by default. If it is ever disabled, it can be re-enabled from the :doc:`Extension Manager <extensions:ext_core/ext_extension-manager>` by searching for ``isaacsim.utils.physics``.

To access this Extension, go to the top menu bar and click **Tools** > **Physics API Editor**.

.. note:: Dynamic objects are currently not supported.

.. _isaac_static_collision_utils_user_interface:

User Interface
=================

The User Interface provides options to add or clear static collision on selected static objects.

.. image:: /images/isaac_physics_utilities_ui.png
    :align: center
    :width: 800

Configuration Options
----------------------

* **Apply to children**: Recursively create collision on all selected children; otherwise, create collision for just the selected object.
* **Visible only**: Ensure the prim is visible before creating collision. (Ignores hidden prims)
* **Collision Type**: Type of collision approximation to use
* **Apply Static**: Applies collision to the current selection.
* **Remove Collision API**: Clears the collision from the current selection.
* **Remove All Physics APIs**: Remove all Physics-related APIs (including collision) from the current selection.


Enable Visualization
-----------------------

.. image:: /images/isaac_physics_visualize_collision.png
    :align: center
    :width: 660

To visualize collision in any viewport:

#. **Select**: the |eyecon| eye icon.
#. **Select**: Show by type.
#. **Select**: Physics Mesh.
#. **Check**: All.

.. note:: Enable visualization **after** collision APIs have been applied or removed. Otherwise there will be a loss in performance while the extension traverses the desired subtree.

.. |eyecon| image:: /images/isaac_physics_visualize_eyecon.png
    :width: 30

