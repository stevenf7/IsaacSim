..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_sim_warehouse_creator:

===========================
Warehouse Creator Extension
===========================

The warehouse Creator Extension uses the new Modular Warehouse Assets to build a custom shape warehouse.

Installing and Enabling the Extension
-------------------------------------

The extension can be installed/enabled by:

1.	Navigating to **Window > Extensions** from the top-level menu
2.	Searching for Warehouse Creator in the text field of the **Extension Manager** window, to reveal the ``omni.warehouse_creator`` result.
3.  Clicking on the **Install** or **Update** button if not previously installed.
4.  Toggling to enable the extension and checking the autoload checkbox if you like.


How to Use
----------

Start by navigating to **Tools > Modular Warehouse Creator**. Verify that you see:

    .. image:: /images/isaac_warehouse_creator_main_window.png
        :align: center
        

In the **Instructions** tab, there is a brief description on how to use it. 

For faster warehouse creation, Download Isaac sim assets locally, and update your assets path. Refer to :ref:`isaac_sim_latest_release` for the download pack. On the Warehosue Creator tab, in the dataset source, click on the Folder icon and select the ``[Isaac Sim Assets Path]/Isaac/Environments/Modular_Warehouse/Props`` folder in the downloaded location.

Drawing
^^^^^^^

To begin the Warehouse Generation, click on **Build Warehouse**. It places the viewport on build mode. A curve draw dialog will display while in this mode. **Do not interact with that dialog as it may disrupt the warehouse creation**. 

Every click on the viewport gets translated into a segment for your warehouse wall in the draw mode. The warehouse is built in a counter-clockwise order. Start by placing a starting point, and moving your way along the shape you want to make. All points are automatically aligned by the warehouse tile size. 

There are two methods to finish drawing:

#. Place a final point at the start. It closes the loop and places the center tiles to complete the warehouse. 
#. If last point added is aligned with the first, **Finish** automatically closes the drawing and the warehouse interior is built. 

.. Note:: 
    - The points must form a perimeter of the warehouse shape. The builder does not handle crossing lines during warehouse generation.
    - The UI prevents you from placing two points too close to each other. To place the closing point, you can zoom in to the start point and click nearby it. The most effective way of achieving it is by placing it along the start edge opposite to the edge direction, as shown in the demonstration video.

.. image:: /images/isaac_warehouse_draw.webp
    :align: center
    :width: 600


Styling
^^^^^^^

Most warehouse blocks have a selection of styles to choose from. By selecting the blocks, on the **Property** panel you can pick the style you want to use for that **Tile**. Each style may serve a different purpose in a warehouse. For example, like a loading dock, or an access panel. 

.. Note:: To facilitate selecting the blocks by clicking at them on the viewport, change the **Select Mode** by right-clicking the toolbar and set it to  **Component**.

    .. image:: /images/isaac_warehouse_select_mode.png
        :align: center


To select the style scroll down in the **Property** panel, and choose the desired option for each block type. It will affect all selected blocks of that type. 

    .. image:: /images/isaac_warehouse_style.webp
        :align: center
        :width: 600

Block Styles
__________________

The block styles are split by the type of blocks, which can vary from straight walls, corners in and out, or a center piece. 
    .. image:: /images/isaac_warehouse_styles.png
        :align: center


Editing Column Placement
^^^^^^^^^^^^^^^^^^^^^^^^

Every block's internal corner contains a quarter of a column to it. By combining all adjacent blocks, a column is formed through all the sub-components. Figuring out which components to enable or disable when adding or removing a column can become easily cumbersome. To facilitate this effort, there is the column Placement editor. To use it, select the floor plan prim, and then click on **Edit Column Placement** on the warehouse creator window.
This puts the editor in a column placement mode. The ceiling and details of the warehouse are hidden, and the floor plan with the columns shows. 

By clicking on a column, it switches from "Enabled" to "Disabled" and vice-versa. "Enabled" columns are displayed in their default materials and appearance, while disabled columns are displayed in a translucent green. You can select multiple at once by click-dragging on the viewport. To enable or disable all columns, you can push the corresponding button in the UI. The **Flip All** button will reverse the enabled status in all columns.
When you are done with column edit, Click **Confirm** to save your current selection. To revert to how it was before entering editing mode, click **Cancel**. 

    .. image:: /images/isaac_warehouse_column.webp
        :align: center
        :width: 600


