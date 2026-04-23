..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.





.. _isaacsim_sensors_rtx_materials:

===================================
RTX Sensor Non-Visual Materials
===================================

The ``omni.sensors.nv.materials`` extension, documented `here <http://omniverse-docs.s3-website-us-east-1.amazonaws.com/omni.sensors.nv.materials/1.6.0-coreapi/materials_extension.html>`_, provides support for rendering materials, which are visible in non-visual spectra for RTX sensors. These materials
are referred to as "non-visual materials".

As described in the extension documentation, non-visual materials are rendered using USD attributes, and can be specified in the USD file. |isaac-sim_short| includes the ``isaacsim.core.experimental.materials.NonVisualMaterial`` class to simplify setting these attributes on ``Material`` prims. The renderer
will compute a material ID for each non-visual material, based on the combination of provided attributes. This material ID is provided by the ``GenericModelOutput`` AOV, and is exposed by multiple Annotators. Refer to :ref:`rtx_sensor_annotator_descriptions` for more details.

Specifying Non-Visual Material Attributes
-----------------------------------------

Valid non-visual material attribute names and values are specified `in Omniverse Kit documentation <https://docs.omniverse.nvidia.com/kit/docs/omni.sensors.nv.materials/latest/materials_extension.html#materials-coatings-and-attributes>`_.

User Interface
##############

Attributes may be added to materials from the UI by right-clicking the material in the **Stage** window, then selecting **Add** > **Attribute**.
This will open a new window like the one below, enabling you to specify custom non-visual attributes.

.. figure:: /images/isaacsim_sensors_rtx_materials_new_attribute.png
    :align: center
    :width: 800
    :alt: Adding a non-visual material attribute.

After adding the new attribute, it will appear in the material's properties, at which point it can be populated:

.. figure:: /images/isaacsim_sensors_rtx_materials_new_nva_property.png
    :align: center
    :width: 800
    :alt: Populating a new non-visual material attribute.

Python
######

The ``isaacsim.core.experimental.materials.NonVisualMaterial`` class provides a Python API to simplify setting non-visual material attributes on ``Material`` prims. The following standalone example
demonstrates how to use this API. Examine the source code to learn more.

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.sensors.experimental.rtx/apply_nonvisual_materials.py

After running this example, verify that you receive the following:

.. figure:: /images/isim_5.1_full_tut_viewport_apply_nonvisual_materials_base.png
    :align: center
    :width: 800
    :alt: Cubes with non-visual materials applied, visualized by the default RTX Renderer.

Observe each cube is colored differently in the visual spectrum. Select the ``Non-Visual Material ID`` Debug View in the viewport by selecting **RTX - Real-Time** > **Debug View** > **Non-Visual Material ID**. The following image
shows the menu selection:

.. figure:: /images/isim_5.1_full_tut_viewport_apply_nonvisual_materials_debug_view_menu.png
    :align: center
    :width: 800
    :alt: Selecting the Non-Visual Material ID Debug View.

After selecting the Debug View, verify that you receive the following:

.. figure:: /images/isim_5.1_full_tut_viewport_apply_nonvisual_materials_debug_view.png
    :align: center
    :width: 800
    :alt: Non-visual materials rendered by the RTX Sensor renderer.

The ``Non-Visual Material ID`` Debug View shows the material ID for each non-visual material as a color, which can be used to identify the material in the scene.
Observe each cube's color changes compared to the default view to reflect the material ID, which is computed from the combination of non-visual material attributes applied to the visual material
applied to the cube.

.. note:: If you modify non-visual material attributes on a material prim, you must save and reload the stage for the changes to take effect.

Mapping Visual Materials to RTX Sensor Non-Visual Materials (Deprecated)
-------------------------------------------------------------------------

.. warning:: Mapping Visual Materials to RTX Sensor non-visual materials via a CSV specification is deprecated as of |isaac-sim_short| 5.1. By default, RTX Sensor non-visual materials will
    now be specified and rendered via USD attributes (review above).

There are 21 sensor materials that are rendered in the visual spectrum, and more can not be added at this time.  Their properties are stored in JSON files by the same name, located in
the ``./data/material_files/`` folder.

======  ======================
Index   Sensor Material Type
======  ======================
0       Default
1       AsphaltStandard
2       AsphaltWeathered
3       VegetationGrass
4       WaterStandard
5       GlassStandard
6       FiberGlass
7       MetalAlloy
8       MetalAluminum
9       MetalAluminumOxidized
10      PlasticStandard
11      RetroMarkings
12      RetroSign
13      RubberStandard
14      SoilClay
15      ConcreteRough
16      ConcreteSmooth
17      OakTreeBark
18      FabricStandard
19      PlexiGlassStandard
20      MetalSilver
31      INVALID
======  ======================

Using Sensor Material Mapping
#############################

In the legacy system, |isaac-sim_short| must know how to map material IDs to the sensor material type
in the table above.  This is done by setting the following ``carb`` setting on the command line:

.. code-block:: bash

    --/rtx/materialDb/rtSensorNameToIdMap="DefaultMaterial:0;AsphaltStandardMaterial:1;AsphaltWeatheredMaterial:2;VegetationGrassMaterial:3;WaterStandardMaterial:4;GlassStandardMaterial:5;FiberGlassMaterial:6;MetalAlloyMaterial:7;MetalAluminumMaterial:8;MetalAluminumOxidizedMaterial:9;PlasticStandardMaterial:10;RetroMarkingsMaterial:11;RetroSignMaterial:12;RubberStandardMaterial:13;SoilClayMaterial:14;ConcreteRoughMaterial:15;ConcreteSmoothMaterial:16;OakTreeBarkMaterial:17;FabricStandardMaterial:18;PlexiGlassStandardMaterial:19;MetalSilverMaterial:20"

Having set ``rtx.materialDb.rtSensorNameToIdMap``, edit ``kit/rendering-data/runtime/RtxSensorMaterialMap.csv`` to map exact material name tokens to sensor material types.

The ``RtxSensorMaterialMap.csv`` file contains a material prim partial names to sensor material type pairs.  The ones that come with  |isaac-sim_short| by default can be deleted as they may clash with names you wish to set.
There is only one CSV file.  It controls the material mapping for all of the content.  It is read at  |isaac-sim_short| startup and any changes made during runtime will not appear until |isaac-sim_short| is restarted.

As an example, consider this scene:

.. figure:: /images/isaacsim_sensors_rtx_material_map.png
    :align: center
    :width: 400

The ``/Root/SM_floor29/SM_floor02/SM_floor02`` prim has a material prim assigned to it whose path is ``/Root/SM_floor29/Looks/MI_Floor_02b``.  If you want to add
an entry to the CSV file so that the ``SM_floor02`` prim looks like rough concrete to the RTX sensors, you would add the entry:


.. code-block:: bash

    mi_floor_02b,ConcreteRoughMaterial

In the CSV mapping file, the first token after the first appearance of ``/Looks/`` in the material prim name attached to the mesh is used, and it must
always be lowercase in the CSV file, no matter what the case is on the stage. Also note how the word Material is concatenated onto the sensor material type from
the table above.

Debugging
#########

The carb parameter:

.. code-block:: bash

    [settings]
    rtx.materialDb.rtSensorMaterialLogs=true

can help.  If set to true, it will output a list of all the materials in the scene that are NOT mapped to a sensor material.  This
list outputs to the terminal and the log at |isaac-sim_short| startup.
