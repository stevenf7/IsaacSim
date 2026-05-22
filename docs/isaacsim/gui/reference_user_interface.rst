..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.

.. _isaac_sim_user_interface:

========================
User Interface Reference
========================

:ref:`NVIDIA Omniverse™ Isaac Sim <isaac_sim_app_overview>` is built on `NVIDIA Omniverse <https://docs.omniverse.nvidia.com/>`_ platform, so it shares the same UI elements as many Omniverse apps.


.. _isaac_sim_opening_page:

Opening Page
===============

Here's a summary of the |isaac-sim_short| frequently mentioned elements on the opening page. For more detailed view of all the elements on the page, go to :doc:`Omniverse User Interface <composer:interface>`.

.. image:: /images/isim_4.5_base_ref_gui_opening_screen.png
    :align: center
    :alt: Overview of the Isaac Sim opening page showing main UI elements


========== ================================== ====================================================================
Ref #      Option                             Result
========== ================================== ====================================================================
1          Menu Bar                           | |isaac-sim_short| :ref:`isaac_sim_menu_bar`
2          Viewport                           | The primary way of viewing assets. See :doc:`Viewport <extensions:ext_core/ext_viewport>` for more details.
3          Main Toolbar                       | :ref:`Toolbar` for manipulating the assets and start/stop simulation buttons are located.
4          Browsers                           | The default location for asset and example browsers. 
5          Stage                              | The Stage window allows you to see all the assets in your current USD Scene. See the :doc:`Stage <extensions:ext_core/ext_stage>` docs for more details.
6          Property Panel                     | The window that displays the details of selected prim. See :doc:`Property Window <extensions:ext_core/ext_property-panel>` for more details.
========== ================================== ====================================================================


.. _isaac_sim_menu_bar:

Menu Bar
============

The |isaac-sim_short| menu layout may be different from the layout of other |omni| applications. Here are the ones unique to |isaac-sim_short|.


.. image:: /images/isim_4.5_base_ref_gui_overview.png
    :align: center

========== ================================== ====================================================================
Ref #      Option                             Result
========== ================================== ====================================================================
1          Create                             | The menu for creating various primitives and other simulation objects
2          Window                             | Opens various windows of loaded extensions, in this case, the ones composing the GUI and other extensions
3          Tools                              | The menu of available simulation tools for animation, physics, replicator, robotics, and USD  
4          Utilities                          | Access various diagnostic and developer utilities such as debugging and extension templates
5          Layout                             | Opens menu for selecting preferred gui layouts
========== ================================== ====================================================================



.. _Toolbar:

Tool Bar
==================

.. image:: /images/isim_4.5_base_ref_gui_kit_reference-guide_toolbar_vertical.png
	:align: center


.. |tb_sel_mod| image:: /images/isim_4.5_base_ref_gui_kit_reference-guide_toolbar_select_models.svg
    :width: 20pt
    :height: 20pt

.. |tb_mv_glob| image:: /images/isim_4.5_base_ref_gui_kit_reference-guide_toolbar_move_global.svg
    :width: 20pt
    :height: 20pt

.. |tb_rot_glob| image:: /images/isim_4.5_base_ref_gui_kit_reference-guide_toolbar_rotate_global.svg
    :width: 20pt
    :height: 20pt

.. |tb_scl| image:: /images/isim_4.5_base_ref_gui_kit_reference-guide_toolbar_scale.svg
    :width: 20pt
    :height: 20pt

.. |tb_snap| image:: /images/isim_4.5_base_ref_gui_kit_reference-guide_toolbar_snap.svg
    :width: 20pt
    :height: 20pt

.. |tb_mv_local| image:: /images/isim_4.5_base_ref_gui_kit_reference-guide_toolbar_move_local.svg
    :width: 20pt
    :height: 20pt

.. |tb_sel_prim| image:: /images/isim_4.5_base_ref_gui_kit_reference-guide_toolbar_select_prims.svg
    :width: 20pt
    :height: 20pt

.. |tb_anim_trans| image:: /images/isim_4.5_base_ref_gui_kit_reference-guide_animation-bar-1.png
    :width: 20pt
    :height: 20pt

=================================  ==============================================  ==================================================================
Icon                               Menu Item                                       Action
=================================  ==============================================  ==================================================================
|tb_sel_mod| / |tb_sel_prim|       :doc:`../gui/selection-modes`                   | Allows user to pick select and object in the viewport.
                                                                                   | This is also the default viewport mouse behavior.
|tb_mv_glob| / |tb_mv_local|       Move (Global / Local)                           | Instantiates a user widget that allows user to move a
                                                                                   | selected object or group of objects
|tb_rot_glob|                      Rotate (Global / Local)                         | Instantiates a user widget that allows user to rotate
                                                                                   | a selected object or group of objects
|tb_scl|                           Scale                                           | Instantiates a user widget that allows user to scale a
                                                                                   | selected object or group of objects
|tb_snap|                          Snap (enable/disable)                           | Sets snapping to specified increments or surface snap.
|tb_anim_trans|                    Select Mode                                     | Toggles transform widgets between local and global
                                                                                   | translation modes
|tb_anim_trans|                    - Play                                          | Start an animation
|tb_anim_trans|                    - Stop                                          | Stop an animation
=================================  ==============================================  ==================================================================

.. Note:: Tools with a small triangle below their icon denotes additional options are available by right clicking the icon.





.. _Tabs:


Tabs
=================

The Layout of the windows can be rearranged by moving the tabbed windows around, and docking them to different locations. 


.. image:: /images/isim_4.5_base_ref_gui_kit_reference-guide_elements_v1a.png
	:width: 800px
	:align: center


1. Panel Being Dragged (See Note below).
2. Panels Original location.
3. Acceptable Docking Locations.

.. Note:: A tab can be "torn-off" and moved to another panel or window by click-hold-drag on the tabs title-bar and dragging it to another location or UI pane.

OS Tabs
--------

Certain tabs in the interface can be detached from the main window, which can be useful on multiple monitors and wide aspect ratio monitors.

To Detach a Tabbed panel use the following procedure.

#. ``Right Click`` on a ``Tab`` to invoke the ``Move to New OS Window`` option.

    .. image:: /images/isim_4.5_base_ref_gui_create_tabs_right-click.png
        :alt: Right-click menu showing Move to New OS Window option

#. ``Left Click`` Select ``Move to OS Window`` action.

    .. image:: /images/isim_4.5_base_ref_gui_create_tabs_open-os-window.png
        :alt: Window showing Move to OS Window action

#. Position the window wherever you wish by using ``Left-Click`` + Dragging.

    .. image:: /images/isim_4.5_base_ref_gui_create_tabs_open-os-window.png
        :alt: Window showing position adjustment



.. _Grab Handles:


Grab Handles
===================

Grab handles are found in all Omniverse Apps and allow you to resize panels.

.. image:: /images/isim_4.5_base_ref_gui_kit_reference-guide_grab-handle.png
	:align: center

1. Grab Handle.

They are "invisible" UI element dividers that, when rolled over, will illuminate and can be click-dragged.  This allows for UI customization, which is especially helpful in managing window content.

.. Note:: Sliding is restricted to horizontal or vertical only.

See Also
--------

- :doc:`Omniverse User Interface <composer:interface>` - Detailed overview of Omniverse UI elements
- :doc:`Viewport <extensions:ext_core/ext_viewport>` - In-depth guide to the viewport functionality
- :doc:`Stage <extensions:ext_core/ext_stage>` - Comprehensive documentation of the Stage window
- :doc:`Property Window <extensions:ext_core/ext_property-panel>` - Detailed guide to the Property Panel