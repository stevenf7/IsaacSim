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

Mapping Visual Materials to RTX Sensor Non-Visual Materials (Removed)
----------------------------------------------------------------------

.. deprecated:: 5.1
   Mapping visual materials to RTX Sensor non-visual materials via a CSV specification (the
   ``RtxSensorMaterialMap.csv`` workflow paired with the ``rtx.materialDb.rtSensorNameToIdMap``
   and ``rtx.materialDb.rtSensorMaterialLogs`` carb settings) is no longer supported — those
   settings and the CSV file are now ignored. Specify non-visual materials via USD attributes
   instead — see `Specifying Non-Visual Material Attributes`_ above.
