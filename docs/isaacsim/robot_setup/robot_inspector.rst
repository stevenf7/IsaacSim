..
   Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_robot_inspector_window:

Robot Inspector Window
======================

The ``isaacsim.robot.schema.ui`` extension provides an interactive **Robot Inspector** window for inspecting the kinematic structure of robots on the stage and selectively masking components for simulation.

.. image:: ../images/isim_6.0_base_ref_gui_robot_inspector_overview.png
   :width: 800px
   :align: center
   :alt: Robot Inspector window showing a robot with the tree view, hierarchy mode selector, and masking columns (Deactivate, Bypass, Anchor).

Opening the Window
------------------

The Robot Inspector window is accessible via **Window > Robot Inspector**. It docks next to the Stage panel by default.

Hierarchy Display Modes
-----------------------

A mode selector at the top of the window controls how the robot hierarchy is displayed. Three modes are available:

.. list-table::
   :header-rows: 1
   :widths: 15 85

   * - Mode
     - Description
   * - **Flat**
     - Links and joints are listed as two flat scopes (``Links``, ``Joints``) under each robot, ordered as they appear in the schema relationships. Useful for quickly reviewing the complete lists.
   * - **Tree** (default)
     - Parent link → joint → child link chain. Matches the kinematic traversal order and is the most natural representation for articulated robots.
   * - **MuJoCo**
     - Tree rooted at the base link. Each link's children appear first, and the joint connecting the link to its own parent appears as the last child entry. Mirrors the body-centric layout used by MuJoCo MJCF files.

.. list-table::
   :widths: 33 33 33
   :align: center

   * - .. image:: ../images/isim_6.0_base_ref_gui_robot_inspector_hierarchy_mode_flat.png
         :width: 100%
         :align: center
         :alt: "Flat mode"
     - .. image:: ../images/isim_6.0_base_ref_gui_robot_inspector_hierarchy_mode_tree.png
         :width: 100%
         :align: center
         :alt: "Tree mode"
     - .. image:: ../images/isim_6.0_base_ref_gui_robot_inspector_hierarchy_mode_mujoco.png
         :width: 100%
         :align: center
         :alt: "MuJoCo mode"
   * - **Flat**
     - **Tree**
     - **MuJoCo**

.. raw:: html

   <style>
   .wy-table-responsive table td {
      vertical-align: top;
   }
   </style>



.. _isaac_sim_robot_inspector_masking:

Component Masking
-----------------

The Robot Inspector provides per-component masking controls that allow disabling individual joints and links for simulation without modifying the authored USD layers. All masking opinions are a debugging tool and are written to a dedicated anonymous sublayer inserted into the session layer stack, so they are transient and never saved to disk.

Three masking columns appear in the tree view:

.. |icon-deactivate| image:: ../images/isim_6.0_base_ref_gui_robot_inspector_icon_deactivate.png
   :width: 18px
   :align: middle
   :alt: Deactivate icon

.. |icon-bypass| image:: ../images/isim_6.0_base_ref_gui_robot_inspector_icon_bypass.png
   :width: 18px
   :align: middle
   :alt: Bypass icon

.. |icon-anchor| image:: ../images/isim_6.0_base_ref_gui_robot_inspector_icon_anchor.png
   :width: 18px
   :align: middle
   :alt: Anchor icon

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Column
     - Description
   * - **Deactivate** (|icon-deactivate|)
     - Disables the joint or link for simulation. Joint deactivation sets ``jointEnabled = False``. Link deactivation disables the rigid body, turns off collision meshes, and hides non-rigid child geometry.
   * - **Bypass** (|icon-bypass|)
     - Disables the element AND reconnects the kinematic chain around it. For joints, fixed joints are created bridging the nearest backward non-masked link to each forward non-masked link. For links, the backward joint is deactivated and forward joints are reparented to the nearest non-masked ancestor link with recalculated local-frame offsets.
   * - **Anchor** (|icon-anchor|)
     - Pins a link to the world at its current pose by creating a temporary fixed joint with no ``body0``. Only available on links that have ``RigidBodyAPI`` applied.


.. image:: ../images/isim_6.0_base_ref_gui_robot_inspector_masking_columns.png
   :width: 600px
   :align: center
   :alt: Close-up of the Robot Inspector masking columns showing the Deactivate, Bypass, and Anchor toggle icons next to robot links and joints.

Masking operations support multi-selection: clicking a column icon while multiple prims are selected applies the action to all selected prims in a single batch.

.. note:: The masking sublayer is automatically cleared when a new stage is opened or the current stage is closed. Masking state does not persist across sessions.

Viewport Joint Visualization
-----------------------------

When the Robot Inspector window is active, joint connections are drawn as overlay lines in the 3D viewport, connecting parent and child links at joint locations. This visualization provides a quick visual check of the kinematic chain.

- Connection lines include directional arrows indicating the parent-to-child relationship.
- When multiple joints overlap at the same screen position (common at dense joint clusters), an **overlay circle** is drawn. Clicking the circle opens a context menu listing all joints at that location, allowing selection of any individual joint.
- Joint visualization is hidden during simulation playback and restored when playback stops.
- Visibility is controlled by the **Visibility Menu (Eye Icon on viewport) > Show by Type > Physics > Joints** setting.


.. _isaac_sim_robot_schema_ui_utilities:

UI Utility Functions
====================

The ``isaacsim.robot.schema.ui`` extension exposes additional utilities for hierarchy generation and component inspection. These are accessible via:

.. code-block:: python

   from isaacsim.robot.schema.ui.utils import HierarchyMode, generate_robot_hierarchy_stage

Hierarchy Mode
--------------

``HierarchyMode`` is an enum controlling how the robot hierarchy is structured in the Robot Inspector and in the in-memory hierarchy stage:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Value
     - Description
   * - ``HierarchyMode.FLAT``
     - Links under a ``Links`` scope and joints under a ``Joints`` scope, in schema relationship order.
   * - ``HierarchyMode.LINKED``
     - Parent link → joint → child link chain (default).
   * - ``HierarchyMode.MUJOCO``
     - Tree rooted at the base link. Child links appear first under each link; the joint connecting the link to its parent appears as the last child entry.

Hierarchy Stage Generation
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - Function
     - Description
   * - ``generate_robot_hierarchy_stage(mode)``
     - Scans the current stage for prims with ``IsaacRobotAPI``, builds a link tree for each robot, and creates an in-memory USD hierarchy stage. Returns ``(hierarchy_stage, path_map, joint_connections)``. The ``mode`` parameter accepts a ``HierarchyMode`` value (default ``LINKED``).

The returned ``PathMap`` object provides bidirectional mapping between original stage paths and hierarchy stage paths:

.. code-block:: python

   hierarchy_stage, path_map, connections = generate_robot_hierarchy_stage(HierarchyMode.FLAT)
   # Map from original stage path to hierarchy path
   hier_path = path_map.get_hierarchy_path(original_prim_path)
   # Map back from hierarchy path to original stage path
   orig_path = path_map.get_original_path(hier_prim_path)

.. note:: During hierarchy generation, any active masking sublayer is temporarily muted so the tree always reflects the unmodified robot structure.

.. _isaac_sim_robot_schema_masking_api:

Masking Operations API
======================

The ``isaacsim.robot.schema.ui`` extension provides a programmatic API for masking, bypassing, and anchoring robot components. The state is managed by the ``MaskingState`` singleton and the USD operations are performed by ``MaskingOperations``.

.. code-block:: python

   from isaacsim.robot.schema.ui.masking_state import MaskingState
   from isaacsim.robot.schema.ui.masking_ops import MaskingOperations

MaskingState
------------

``MaskingState`` is a singleton that tracks which prims are deactivated (masked), bypassed, or anchored. It maintains three independent sets and notifies subscribers when any state changes.

.. list-table::
   :header-rows: 1
   :widths: 45 55

   * - Method
     - Description
   * - ``MaskingState.get_instance()``
     - Returns the singleton ``MaskingState`` instance.
   * - ``is_deactivated(original_path)``
     - Returns ``True`` if the prim is masked or bypassed.
   * - ``is_bypassed(original_path)``
     - Returns ``True`` only if the prim is in the bypassed state.
   * - ``is_anchored(original_path)``
     - Returns ``True`` if the link is anchored to the world.
   * - ``toggle_deactivated(original_path)``
     - Toggles plain mask. Unmasking a bypassed prim unbypasses it first.
   * - ``toggle_bypassed(original_path)``
     - Toggles bypass state (mask + reconnect chain).
   * - ``toggle_anchored(original_path)``
     - Toggles world-anchor on a link.
   * - ``set_deactivated_batch(paths, deactivated)``
     - Sets deactivation state for multiple prims with a single change notification.
   * - ``set_bypassed_batch(paths, bypassed)``
     - Sets bypass state for multiple prims with a single change notification.
   * - ``set_anchored_batch(paths, anchored)``
     - Sets anchor state for multiple links with a single change notification.
   * - ``clear()``
     - Clears all masking, bypass, and anchor state.
   * - ``subscribe_changed(callback)``
     - Registers a no-argument callback invoked when any state changes.
   * - ``unsubscribe_changed(callback)``
     - Unregisters a previously registered change callback.

MaskingOperations
-----------------

``MaskingOperations`` performs the actual USD edits on a dedicated anonymous sublayer. All opinions are transient and never written to the authored layers.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Method
     - Description
   * - ``mask_prim(original_path)``
     - Disables a joint (``jointEnabled = False``) or link (rigid body, collisions, visibility) for simulation.
   * - ``unmask_prim(original_path)``
     - Removes mask opinions, restoring base-layer values.
   * - ``bypass_prim(original_path)``
     - Masks the element and reconnects the kinematic chain around it. For joints, creates fixed joints bridging the gap. For links, deactivates the backward joint and reparents forward joints.
   * - ``unbypass_prim(original_path)``
     - Removes the bypass, restoring the chain to its original state.
   * - ``anchor_link(original_path)``
     - Pins a link to the world by creating a fixed joint at its current pose.
   * - ``unanchor_link(original_path)``
     - Removes the anchor fixed joint.
   * - ``clear_all()``
     - Drops the masking sublayer entirely, reverting everything at once.
