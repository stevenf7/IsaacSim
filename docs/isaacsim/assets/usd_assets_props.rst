
..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.







.. _isaac_assets_props:

================================
Prop Assets
================================

Characters
--------------------
Listed below are a few characters available in Isaac-Sim, located in the Content Browser inside the ``Isaac Sim`` folder.

Police Man
#############################

Male character in police uniform with retargeted skeleton.

.. figure:: /images/Adult_Male_Police_04.PNG
    :align: center
    :alt: Police Man
    :width: 25%

    ``People/Characters/original_male_adult_police_04/male_adult_police_04.usd`` in the Content Browser.

Male Doctor
#############################

Male character in doctor uniform with retargeted skeleton.

.. figure:: /images/Adult_Male_Medical_01.PNG
    :align: center
    :alt: Male Doctor
    :width: 25%

    ``People/Characters/origial_male_adult_medical_01/male_adult_medical_01.usd`` in the Content Browser.

Police Woman
#############################

Female character in police uniform with retargeted skeleton.

.. figure:: /images/Adult_Female_Police_02.PNG
    :align: center
    :alt: Police Woman
    :width: 25%

    ``People/Characters/female_adult_police_02/female_adult_police_02.usd`` in the Content Browser.

Construction Worker
#############################

Male character in construction uniform with retargeted skeleton.

.. figure:: /images/Adult_Male_Construction_03.PNG
    :align: center
    :alt: Construction Worker
    :width: 25%

    ``People/Characters/origial_male_adult_construction_03/male_adult_construction_03.usd`` in the Content Browser.

.. note::
    User can change a character's clothing color by modifying material's ``Property -> Material and Shader`` value

Here is an example of how to change male_adult_construction_03's safety hat's color

* First, expand the character on the stage menu and navigate to their ``Looks`` folder. Example - ``/World/male_adult_construction_03/Looks``.
* Next, select your target material (Example - ``opaque__plastic__hardhat``) and change material's ``Property -> Material and Shader -> Albedo -> Color Tint`` value to adjust character's color.

.. figure:: /images/Start_Color_Change_Male_Construction.PNG
    :align: center
    :alt: select male_adult_construction_03's hat's material
    :width: 66%

.. figure:: /images/Middle_Color_Change_Male_Construction.PNG
    :align: center
    :alt: change hat color
    :width: 66%

.. figure:: /images/Finish_Color_Change_Male_Construction.PNG
    :align: center
    :alt: change whole body color
    :width: 66%

.. _isaac_sim_asset_april_tag:

April Tags
###############

We provide a simple mdl material that can index into a April Tag mosaic image.

To use, add the material to your stage using ``Create->April Tag->``

Then create a mesh cube using ``Create->Mesh->Cube`` and assign the AprilTag material to that prim

The material has the following parameters which need to be configured:

- ``Mosaic texture`` The path to the texture that contains the grid of April tag images
- ``Tag Size`` The width/height of the tag in pixels
- ``Tags Per Row`` The number of tag images per row in the mosaic
- ``Spacing`` The number of padding pixels between each tag image
- ``Tag ID`` The index of the tag to use.


The figure below shows example usage using ``tag36h11.png``,
after manually creating the mesh cube and assigning the material as described above.

.. figure:: /images/isaac_april_tag.png
    :align: center
    :alt: April Tag Example Usage
