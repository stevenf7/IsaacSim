..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


:orphan:

.. _isaac_sim_app_gui_layouts:

==========================================
Layout Templates
==========================================

As you explore and use |isaac-sim_short| tools, you may find yourself having preferences in how your windows and tools are arranged. We offers layout templates and the ability to save custom GUI layouts to be loaded later. The **Layouts** menu is located in the top navigation bar, and the predefined layouts are listed under **Templates**.

.. image:: /images/isim_5.0_base_ref_gui_layouts.png
    :width: 600
    :align: center

|

The predefined layouts in the **Layouts** menu both opens up the frequently used tools for a specific usecase and arranges them in a way that is most convenient.

#. **Default**: for general use
#. **Visual Scripting**: for usecases that frequently opens Omnigraph Editors (e.g. ROS)
#. **Replicator**: opens and arranges the frequently used Replicator tools, such as the Semantic Schema Editor, Synthetic Data Recorder, and Script Editor
#. **Occupancy Map Generation**: opens the Occupancy Map window, as well as an additional viewport with the top-down view of the scene
#. **Action and Event Data Generation** [#f1]_: opens and arranges the frequently used Action and Event Data Generation tools, such as Actor SDG, Object SDG, and Camera Placement.

.. [#f1] visible only when relevant extensions are enabled.

You can also save your own custom layouts by clicking on the **Save Layout** button in the top-right corner of the window. Layouts are saved as JSON files, and you load them by clicking on the **Load Layout** button in the menu and locate the desired layout file.



Additional information can be found in :doc:`Omniverse Layouts <extensions:ext_layouts>`.


