..
   Copyright (c) 2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_joint_inspector:

Joint Inspector
===============

The ``isaacsim.gui.property`` extension provides a standalone **Joint Inspector** window for Adjusting per-joint values across the robots present on the stage.

.. image:: ../images/isim_6.0_base_ref_gui_joint_inspector_overview.png
   :width: 800px
   :align: center
   :alt: Joint Inspector window showing a robot drop-down, the New Inspector button, the joint name filter, the columns hamburger menu, and a per-joint table with editable cells.


Opening the Window
------------------

Open the inspector through **Tools > Robotics > Joint Inspector**. 

.. image:: ../images/isim_6.0_base_ref_gui_joint_inspector_menu.png
   :width: 360px
   :align: center
   :alt: Tools > Robotics submenu with the Joint Inspector entry and its checkmark indicator.

The window docks to the left of the viewport.

Selecting a Robot
-----------------

The header exposes a robot picker, a refresh button, and a **+ New Inspector** button.


- **Robot drop-down** -- lists every prim on the stage that has ``IsaacRobotAPI`` applied. Click the drop-down to open a searchable popup; type any substring of the prim path to narrow the list. Selecting a robot rebinds the table to that robot's joints.
- **Refresh** -- rescans the stage for prims with ``IsaacRobotAPI``. Use this after authoring a new robot in a script editor or after switching layers.
- **+ New Inspector** -- spawns an additional Joint Inspector window. Each window keeps an independent robot selection and column set, which is useful for side-by-side comparison of two robots or two views of the same robot.

.. image:: ../images/isim_6.0_base_ref_gui_joint_inspector_robot_picker.png
   :width: 480px
   :align: center
   :alt: Robot picker popup with a search field and a list of robot prim paths, the active selection highlighted.

The window listens to stage open/close and asset-load events so the robot list refreshes automatically when assets finish loading.

Filtering Joints
----------------

A search field above the table filters the joint rows by name. Two matching modes are supported:

- **Substring (default)** -- a case-insensitive substring match against the joint short name and the full prim path. ``arm`` matches ``shoulder_arm_joint`` as well as ``/World/UR10/shoulder/arm``.
- **Glob (``*`` or ``?`` in the query)** -- ``fnmatch``-style wildcards. The query is also matched in a substring-fenced form (``*pattern*``) so ``hand*`` finds anything that contains ``hand``, mirroring the typical search-bar mental model.

.. image:: ../images/isim_6.0_base_ref_gui_joint_inspector_filter.png
   :width: 700px
   :align: center
   :alt: Joint name filter showing the magnifier icon, the typed query, and the trailing clear button that appears when text is present.

A clear button on the right of the field removes the query and restores the full list.

Choosing Columns
----------------

The hamburger button on the right of the toolbar opens a categorized columns popup.

.. image:: ../images/isim_6.0_base_ref_gui_joint_inspector_columns_menu.png
   :width: 360px
   :align: center
   :alt: Columns popup with the BACKENDS pill toggles (PhysX, MuJoCo) at the top and grouped checkbox rows for Joint Limits, Drives, Performance Envelope, Joint State, and MuJoCo Joint columns.

The popup contains:

- **Backend pills** at the top -- ``PhysX`` and ``MuJoCo`` toggle the visibility of every column belonging to that simulation backend. The pill state does not flip the per-column checkboxes, so re-enabling a backend restores the previously checked columns.
- **Categorized checkbox rows** for the available column groups.

The available column groups are summarized below.

.. list-table::
   :header-rows: 1
   :widths: 22 18 60

   * - Group
     - Backend
     - Columns
   * - **Joint Limits**
     - USD / PhysX
     - ``Position Min``, ``Position Max``, ``Velocity Max``.
   * - **Drives**
     - USD
     - ``Max Force``, ``Target Position``, ``Target Velocity``, ``Stiffness``, ``Damping``.
   * - **Performance Envelope**
     - PhysX
     - ``Max Actuator Velocity``, ``Speed-Effort Gradient``, ``Velocity-Dependent Resistance``.
   * - **Joint State**
     - PhysX
     - ``State Position``, ``State Velocity``.
   * - **MuJoCo Joint**
     - MuJoCo
     - ``Armature``, ``Damping``, ``Stiffness``, ``Friction Loss``, ``Spring Ref``, ``SolRef Limit (timeconst)``, ``SolImp Limit (dmin)``.

Column behavior:

- Items whose backing API is not applied on any joint of the current robot stay clickable but render dimmed; their tooltip explains why the column is currently empty.
- The user's column selection persists across robot switches. A column reappears as soon as a robot whose joints back the column is selected.
- ``Joint Limits`` columns belong to USD core schemas and are not affected by the backend pills.

Per-axis fan-out
^^^^^^^^^^^^^^^^

When every joint authoring a multi-apply schema has at most one axis applied (the common case for revolute and prismatic chains), the per-axis dimension is collapsed and the column appears once. The cell automatically picks the joint's authored axis or its natural axis (``angular`` for revolute, ``linear`` for prismatic).

Multi-DOF (for example, ``D6Joint``) joints make the column fan out: one column per distinct axis (``transX``, ``transY``, ``transZ``, ``rotX``, ``rotY``, ``rotZ``) is rendered, with the axis token appended to the header label.

Editing Values
--------------

Each cell is a free-form ``ui.FloatDrag`` bound directly to the underlying USD attribute. Drag horizontally to scrub the value or click to type a number. double-click or Ctrl-click to type a number.


Behavior of empty cells, multi-row edits, and array-typed attributes:

- Cells whose backing API is not applied on the joint render empty rather than as a disabled ``0.0`` field. This avoids implying a meaningful zero where no value is authored.
- Click rows to select them. ``Ctrl`` / ``Cmd`` and ``Shift`` allow multi-row selection. Editing one cell of a selected row mirrors the new value to the same column on every other selected row whose attribute exists.
- The MuJoCo ``solreflimit`` and ``solimplimit`` columns surface only the dominant element of the underlying array (``timeconst`` and ``dmin``); the rest of the array is preserved on write.

The status line above the table shows the number of joints currently displayed.

Default Visible Columns
-----------------------

The first time the inspector is opened, the following columns are visible:

- ``Position Min`` and ``Position Max`` (Joint Limits)
- ``Target Position``, ``Stiffness``, ``Damping`` (Drives)
- ``State Position`` (Joint State)
- ``Armature``, ``Damping``, ``Stiffness``, ``Friction Loss`` (MuJoCo Joint)

Use the columns menu to add or remove columns from this set.
