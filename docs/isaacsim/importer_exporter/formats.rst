..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _formats:

===============
Formats
===============

The standard format used in Omniverse is USD for scenes and MDL for materials.  You need to convert your content to be usable in Omniverse, if coming from external applications. Omniverse offers several ways to manage such content.

Asset Converter
-----------------------
Apps in Omniverse are loaded with the Asset Converter extension. With it, you can convert models into USD using the :doc:`Asset Converter <extensions:ext_asset-converter>` service.  Below is a list of formats it can convert to USD.

========= ================================================ ==================================================================================
Format    Name                                             Description
========= ================================================ ==================================================================================
``.fbx``  Autodesk FBX Interchange File                    Common 3D model saved in the Autodesk Filmbox format
``.obj``  Object File Format                               Common 3D Model format
``.gltf`` GL Transmission Format File                      Common 3D Scene Description
========= ================================================ ==================================================================================

.. Connectors
.. ----------------
.. Specialized connectors offer a more finely tuned conversion process.  Through connectors, native files are directly translated to usd.

.. .. note:: Because connected applications often have numerous file conversion capabilities, a path to even the most obscure formats may be possible through various connectors.

Materials
------------
NVIDIA has developed a custom schema in USD to represent material assignments and specify material parameters. In |omni|, these specialized USD's get an extension change to ``.MDL`` signifying that it is represented in NVIDIA's open-source MDL (Material Definition Language).

