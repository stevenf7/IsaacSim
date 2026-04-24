..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_sim_warehouse_creator:

.. |wc_select| image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui_toolbar_select.svg
   :width: 18pt
   :height: 18pt

.. |wc_move| image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui_toolbar_move.svg
   :width: 18pt
   :height: 18pt

.. |wc_rotate| image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui_toolbar_rotate.svg
   :width: 18pt
   :height: 18pt

.. |wc_flip_h| image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui_toolbar_flip_horizontal.svg
   :width: 18pt
   :height: 18pt

.. |wc_flip_v| image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui_toolbar_flip_vertical.svg
   :width: 18pt
   :height: 18pt

.. |wc_draw| image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui_toolbar_draw.svg
   :width: 18pt
   :height: 18pt

.. |wc_line| image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui_toolbar_line.svg
   :width: 18pt
   :height: 18pt

.. |wc_box| image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui_toolbar_box.svg
   :width: 18pt
   :height: 18pt

.. |wc_erase| image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui_toolbar_erase.svg
   :width: 18pt
   :height: 18pt

.. |wc_sym_h| image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui_toolbar_symmetry_horizontal.svg
   :width: 18pt
   :height: 18pt

.. |wc_sym_v| image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui_toolbar_symmetry_vertical.svg
   :width: 18pt
   :height: 18pt

.. |wc_subtract| image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui_toolbar_subtract.svg
   :width: 18pt
   :height: 18pt

.. |wc_merge| image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui_toolbar_merge.svg
   :width: 18pt
   :height: 18pt

.. |wc_group| image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui_toolbar_group.svg
   :width: 18pt
   :height: 18pt

.. |wc_ungroup| image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui_toolbar_ungroup.svg
   :width: 18pt
   :height: 18pt

.. |wc_zoom_in| image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui_toolbar_zoom_in.svg
   :width: 18pt
   :height: 18pt

.. |wc_zoom_out| image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui_toolbar_zoom_out.svg
   :width: 18pt
   :height: 18pt

===========================
Warehouse Creator Extension
===========================

The Warehouse Creator is an interactive plan builder that converts a 2D grid layout into a USD warehouse
built from the Modular Warehouse asset pack. Sketch the floor plan in a top-down editor, place tiles from a
block library, and generate the corresponding USD prims on the active stage.

The feature ships as two extensions:

- ``omni.warehouse.creator.api`` --- headless logic (grid engine, auto-tiling, plan-to-stage sync, and the
  column editing controller). Use it from scripts and tests with no UI dependency.
- ``omni.warehouse.creator.ui`` --- the **Warehouse Builder** window, toolbar, block library palette,
  variant property widget, and column placement workflow.

Installing and enabling the extension
-------------------------------------

1. Open **Window > Extensions** from the top menu.
2. Search for ``omni.warehouse.creator.ui`` in the **Extension Manager** window.
3. Click **Install** or **Update** if needed.
4. Toggle the extension on. Enable **Autoload** to start it on every launch.

The UI extension pulls in ``omni.warehouse.creator.api`` automatically. Enabling the API extension on its
own is supported for headless / scripted workflows.

Opening the editor
------------------

Open **Window > Warehouse Creator** to show the **Warehouse Builder** window. The window contains:

- An **overhead 2D viewport** centered on the grid origin.
- A **floating toolbar** along the bottom of the viewport with all editing tools.
- A **block library palette** docked to the side of the window.
- A **Warehouse Creator** panel with the **Generate Warehouse** button and the collapsible **Column
  Editor** section.

The window builds on first open and stays in memory after you close it, so reopening is instantaneous.

.. image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui-1.1.0_gui_main_window.png
   :alt: Warehouse Builder window with the overhead viewport, floating toolbar, block library palette, and Warehouse Creator side panel.
   :align: center
   :width: 720

Configuring the dataset source
------------------------------

Configure asset paths from **Edit > Preferences > Warehouse Creator**. The page exposes:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Setting
     - Purpose
   * - **Cell Size (world units)**
     - World-space size of a single grid cell. Controls both the editor grid and the generated tile
       spacing.
   * - **Wall Height (world units)**
     - Height applied to the wall asset preset.
   * - **Center (floor) Asset**
     - File name of the center/floor USD asset relative to the asset root.
   * - **Wall Asset**
     - File name of the wall USD asset relative to the asset root.
   * - **Asset Root Path**
     - Local or Nucleus root folder containing the warehouse assets. Point this at your downloaded
       Isaac Sim assets folder for the fastest editor and generation experience.
   * - **Cloud Assets URL**
     - HTTPS fallback used when **Asset Root Path** is unset or unreachable.

.. note::
   The **Cell Size**, **Wall Height**, and asset name settings depend on the asset pack you use. The
   default values match the Isaac Sim assets pack; for a custom pack, set the values manually. An asset
   pack is a collection of Center/Floor and Wall assets that share a variant system exposing every
   available option of each asset type as a reference. See the Modular Warehouse pack for an example of
   how to structure one.

For local performance, download the Isaac Sim assets pack (see :ref:`isaac_sim_latest_release`) and point
**Asset Root Path** at ``[Isaac Sim Assets Path]/Isaac/Environments/Modular_Warehouse_New/``. The block
library palette and the warehouse generator both read from this location.

Editor workflow
---------------

The editor operates on a logical grid. At generation time, each occupied cell becomes a center/floor
prim and each exposed cell edge becomes a wall prim. The generator omits walls between two adjacent
occupied cells.

The toolbar uses three categories of buttons:

- **Modal tools** --- mutually exclusive. Activating one deactivates the previously active modal tool.

  - |wc_select| **Select**
  - |wc_move| **Move**
  - |wc_rotate| **Rotate**
  - |wc_draw| **Draw**
  - |wc_line| **Line**
  - |wc_box| **Box**
  - |wc_erase| **Erase**

- **Toggles** --- coexist with any modal tool. Activating symmetry mirrors every drawing or erasing
  action across the chosen axis.

  - |wc_sym_h| **Symmetry Horizontal**
  - |wc_sym_v| **Symmetry Vertical**

- **Immediate actions** --- one-shot operations. They execute on click without becoming the active tool.

  - |wc_flip_h| **Flip Horizontal**
  - |wc_flip_v| **Flip Vertical**
  - |wc_group| **Group**
  - |wc_ungroup| **Ungroup**
  - |wc_merge| **Merge**
  - |wc_subtract| **Subtract**
  - |wc_zoom_in| **Zoom In**
  - |wc_zoom_out| **Zoom Out**

Selection-dependent actions (|wc_flip_h| **Flip**, |wc_group| **Group**, |wc_ungroup| **Ungroup**,
|wc_merge| **Merge**, and |wc_subtract| **Subtract**) are disabled in the toolbar when the current
selection does not meet their requirements.

.. image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui-1.1.0_gui_toolbar.png
   :alt: Floating viewport toolbar showing the Select, Move, Rotate, Flip, Draw, Line, Box, Erase, Symmetry, Boolean, Group, and Zoom buttons.
   :align: center
   :width: 720

Drawing tiles
^^^^^^^^^^^^^

#. Pick an asset in the **Block Library Palette**. The next drawing operation places this asset as the
   manual tile.
#. Activate |wc_draw| **Draw** for free-form painting, |wc_line| **Line** for a straight-line drag, or
   |wc_box| **Box** for filled rectangles.
#. Click and drag inside the viewport to add cells. |wc_erase| **Erase** removes cells with the same
   gestures.

To drop a single tile at the cursor without changing the active tool, drag a palette card directly onto
the viewport.

|wc_sym_h| **Symmetry Horizontal** and |wc_sym_v| **Symmetry Vertical** mirror every drawing or erasing
action across the world origin on the selected axis. Toggle them at any time without leaving the active
drawing tool.

.. image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui-1.1.0_gui_main_window_drawn.png
   :alt: Warehouse Builder window with two ungrouped layouts drawn on the grid: a larger plus-shaped block straddling the origin and a smaller cluster of cells to the lower right.
   :align: center
   :width: 720

Selecting and editing
^^^^^^^^^^^^^^^^^^^^^

- |wc_select| **Select** --- click a cell to select it. Click and drag to draw a selection box.
  Selecting a grouped cell selects the entire group.
- |wc_move| **Move** --- drag selected cells or groups to a new grid location.
- |wc_rotate| **Rotate** --- click to rotate the selection 90 degrees clockwise. Use the keyboard
  shortcuts below for finer control.
- |wc_flip_h| **Flip Horizontal** / |wc_flip_v| **Flip Vertical** --- mirror the selection across the
  corresponding axis in place.

Hotkeys
^^^^^^^

The window owns its hotkey scope, so the shortcuts only fire while the cursor is over the
**Warehouse Builder** window.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Shortcut
     - Action
   * - ``Delete`` / ``Backspace``
     - Delete the current selection (cells and groups).
   * - ``Esc``
     - Clear the current selection.
   * - ``Ctrl+Z`` / ``Ctrl+Y``
     - Undo / redo the last grid command.
   * - ``Left`` / ``Right``
     - Rotate the selected cells 90 degrees counter-clockwise / clockwise. Hold ``Shift`` to rotate
       in place.
   * - ``Space``
     - Cycle to the next tool (when ``enable_hotkeys`` is enabled in the extension settings).

Grouping cells
^^^^^^^^^^^^^^

A group treats a set of cells as a single floating object. You can move, rotate, and flip a group as a
unit, and the generator emits each group as a separate warehouse root prim.

- |wc_group| **Group** --- combine the selection into a new group. Requires at least two ungrouped cells
  or existing groups.
- |wc_ungroup| **Ungroup** --- stamp a selected group's cells back onto the grid as ungrouped cells.
- |wc_merge| **Merge** --- combine two or more selected groups into one.
- |wc_subtract| **Subtract** --- remove the cells of later-selected groups from the first-selected
  group.

At generation time, each group becomes its own ``/Warehouse_group_<id>`` root prim with walls derived
from its boundary. Adjacent groups can sit next to ungrouped cells without sharing walls.

Variant property widget
^^^^^^^^^^^^^^^^^^^^^^^

The generator emits two tile types --- **Wall** and **Center** --- and each tile ships with a set of
visual variants such as a loading dock, an access panel, or a window. After generation, select one or
more tile prims in the stage and use the **Warehouse Tiles** section of the **Property** panel to switch
the variant on every selected tile of that type.

.. tip::
   In the viewport, set **Select Mode** to **Component** (right-click the toolbar) so individual tiles
   are selectable instead of the whole warehouse hierarchy.

.. image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui-1.1.0_gui_tile_variants.png
   :alt: Warehouse Tiles section of the Property panel showing the available variants for the Wall and Center tile types.
   :align: center
   :width: 600

Generating the warehouse
------------------------

The **Generate Warehouse** button in the **Warehouse Creator** panel converts the current plan into USD
prims on the active stage:

- All ungrouped cells go under ``/Warehouse``.
- Each group goes under its own ``/Warehouse_group_<id>``.
- A center/floor prim is placed at every occupied cell, and a wall prim is added on every exposed edge,
  rotated to face outward.

A modal **Generating Warehouse** popup blocks input until the USD layers settle. This keeps the editor
responsive while large layouts stream in.

Re-running **Generate Warehouse** replaces the existing root prims with a fresh layout, so you can
iterate on the plan and regenerate without manual cleanup.

.. image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui-1.1.0_gui_warehouse_built.png
   :alt: Generated warehouse rendered in the 3D viewport showing two separate root prims with floor, walls, and corner columns produced from the drawn plan.
   :align: center
   :width: 720

Editing column placement
------------------------

Each warehouse block carries a quarter-column at every corner. Adjacent blocks combine their
quarter-columns into a single full column. The **Column Editor** toggles individual full columns on or
off after the warehouse is generated, without manually authoring per-block variants.

#. Generate the warehouse, then select any prim under one of the warehouse roots. The **Edit Column
   Placement** button becomes available when the selection sits under a generated warehouse.
#. Click **Edit Column Placement** to enter edit mode. The editor hides the ceiling and non-column
   geometry, highlights each column (green for kept, red for pending removal), and forces the viewport
   outline overlay on so the highlights remain visible.
#. Click columns in the viewport to toggle each between **Enabled** (green) and **Disabled** (red). Drag
   a marquee to toggle multiple at once. Use the **Enable All**, **Disable All**, and **Flip All**
   buttons for bulk operations.
#. Click **Confirm** to author the variant selections on the root layer, or **Cancel** to discard the
   pending changes. Both actions exit edit mode and clear the temporary visibility overrides.

.. image:: /images/isim_6.0_full_ext-omni.warehouse.creator.ui-1.1.0_viewport_column_editor.png
   :alt: Column editor session on a generated warehouse with kept columns highlighted green and pending-removal columns highlighted red.
   :align: center
   :width: 600

Headless API
------------

For scripts, batch jobs, and tests, ``omni.warehouse.creator.api`` exposes the same generation pipeline
without any UI:

.. literalinclude:: ../../snippets/digital_twin/warehouse_logistics/ext_omni_warehouse_creator/headless_generation.py
   :language: python

The :class:`ColumnEditorController` mirrors the **Column Editor** workflow for headless use. Call
:meth:`enter` to begin a session, mutate the pending-disabled set with :meth:`set_all`,
:meth:`flip_all`, or :meth:`toggle_keys`, then call :meth:`leave` with ``commit=True`` to author the
selections.
