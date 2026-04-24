..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _ext_isaacsim_asset_generator_occupancy_map:

.. _isaac_sim_mapping_tools:

=============================
Mapping
=============================

|isaac-sim| mapping extension supports 2D occupancy map generation for a specified height.



.. _ext_isaacsim_asset_generator_occupancy_map_about:

Occupancy Map Generator
===========================

The :ref:`ext_isaacsim_asset_generator_occupancy_map` Extension is used to generate a binary map of whether or not an area in the scene is occupied at a given height. It uses physics collision geometry in the :ref:`isaac_sim_glossary_stage` to determine if a location is occupied or not.

This extension is enabled by default. If it is ever disabled, it can be re-enabled from the :doc:`Extension Manager <extensions:ext_core/ext_extension-manager>` by searching for ``isaacsim.asset.gen.omap``.

To access this Extension, go to the `top menu bar` and click **Tools** > **Robotics** >> **Occupancy Map**.

.. _ext_isaacsim_asset_generator_occupancy_map_conventions:

Conventions
^^^^^^^^^^^^

- All geometry must have `Collisions Enabled` to be detected by the Occupancy Map Generator. Otherwise the geometry will not appear in the final map.
- The `Start` location of the map cannot be occupied.

.. note:: If mapping does not work correctly make sure the start location is not occupied. You can view the physics geometry by clicking the Show/Hide (eye icon) in the viewport window and selecting **Show By Type** > **Physics Mesh** > **All**.

.. _ext_isaacsim_asset_generator_occupancy_map_api_doc:

API Documentation
^^^^^^^^^^^^^^^^^^^

See the `API Documentation <../py/source/extensions/isaacsim.asset.gen.omap/docs/index.html>`_ for usage information.

.. _ext_isaacsim_asset_generator_occupancy_map_user_interface:

User Interface
^^^^^^^^^^^^^^^^^

The user interface is composed of two parts, the configuration window (named *Occupancy Map*) and the *Occupancy Map Visualization* window.

Occupancy Map window
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure:: /images/isaac_occupancy_map_ui_1.png
    :align: center
    :alt: Main Occupancy Map Generator UI Window

|

* **Origin**: An open location inside of the area you wish to map.
* **Lower/Upper Bound**: Areas outside of these bounds will not be mapped. These are maximal bounds, the mapped area may be smaller than these limits.
* **Positioning**:

    - **CENTER TO SELECTION**: The origin will be moved to the center of a selected prim or prims.
    - **BOUND SELECTION**: The bounds will updated to incorporate the selected prim or prims.

- **Cell Size**: The number of meters each pixel in the final image represents.
- **Occupancy Map**:

    - **CALCULATE**: Compute the occupancy map.
    - **VISUALIZE IMAGE**: Open a new window to preview and save the resulting map as an image.

- **Use PhysX Collision Geometry**: When set to True (default), the current collision approximations are used by the PhysX based Lidar to generate the occupancy map. If set to False, the collision approximations are temporarily removed and the RTX Lidar uses the original triangle meshes to generate the occupancy map.

**Example:**

The following steps show how to create and visualize an occupancy map of a certain scene:

    #. Create a new Cone shape (**Create > Shape > Cone** menu) and add the physics Collision property to it (right click and **Add > Physics > Collider Preset**, or in the *Property* panel).
    #. Translate the shape 0.3 meters in the X-axis and orient it 90º in the X-axis Euler angles by modifying its *Transform* in the *Property* panel.
    #. Click on the **Tools > Robotics > Occupancy Map** menu to open the *Occupancy Map* window docked to the *Property* panel.
    #. Set the Occupancy Map's Origin Z-axis value to 0.1 meters to map the area at that height
    #. Click on **CALCULATE** followed by **VISUALIZE IMAGE**. The *Occupancy Map Visualization* window will appear as shown in the image in the next subsection.
    #. Finally, click **Save Image** to save the map to an easily accessible location.  You will need it for later steps in this guide!

Occupancy Map Visualization window
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure:: /images/isaac_occupancy_map_visualize_image.png
    :align: center
    :alt: Visualize Image User Interface

|

- **Occupied Color**: The color chosen to represent space that is "occupied".
- **Freespace Color**: The color chosen to represent space that is "free".
- **Unknown Color**: The color chosen to represent space that is interstitial or "unknown".
- **Rotate Image**: Rotates the coordinates of the image space.  A rotation of :math:`\text{180}^{\circ}` will result in a Heightmap orientation that matches that of the original source stage of the occupancy map.
- **Coordinate Type**: Determines the format of the output in the information window.  Stage Space coordinates reports values in the space of the stage, while the "ROS Occupancy Map Parameters File" returns the needed parameters for the ROS Occupancy Map.
- **Filename**: Base name used when saving the PNG image or YAML file, and written into the YAML ``image`` field. Defaults to the stage name. 
- **RE-GENERATE IMAGE**: This will regenerate the image and information window if you changed the stage.
- **Save Image**: Opens a file dialog pre-filled with the Filename to save the occupancy map as a ``.png`` file.
- **Save YAML**: Opens a file dialog pre-filled with the Filename to save the ROS occupancy map parameters as a ``.yaml`` file.


Heightmap Importer
=========================

.. _ext_omni_isaac_heightmap_tool:

Heightmap Importer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Heightmap Importer Extension converts a 2D occupancy map into a 3D heightmap terrain.
In this extension black pixels in the occupancy map are considered occupied and white pixels are considered free space.
The generated 3D terrain automatically has a collision mesh applied for all the occupied pixels.


To access this Extension, go to the `top menu bar` and click **Tools** > **Robotics** > **Heightmap Importer**.

.. figure:: /images/isim_6.0_full_ext-isaacsim.asset.importer.heightmap-2.2.0_gui_ui.png
    :align: center
    :alt: Main Heightmap Importer UI Window

|

- **Cell Size**: Real-world units represented by a single pixel in the 2D occupancy image. The default unit in Isaac Sim is in meters.
- **Load** : Load the desired occupancy image.
- **Generate**: Button to generate the 3D heightmap terrain.


Heightmap Usage Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To run the Example:

1. Save the following image to disk:

.. figure:: /images/isim_6.0_full_ext-isaacsim.asset.importer.heightmap-2.2.0_external_example.png
    :align: center
    :alt: Heightmap Importer Example

|

2. Go to the top menu bar and click **Tools** > **Robotics** > **Heightmap Importer**.
3. Press the **Load Image** button and open the saved image. A window titled **Visualization** will appear.
4. Press the **Generate Heightmap** button to create geometry corresponding to the input occupancy map in the :ref:`isaac_sim_glossary_stage`.

.. figure:: /images/isim_6.0_full_ext-isaacsim.asset.importer.heightmap-2.2.0_viewport_example.png
    :align: center
    :alt: Heightmap Importer Example
