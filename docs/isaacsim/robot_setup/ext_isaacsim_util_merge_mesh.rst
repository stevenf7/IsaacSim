
..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_merge_mesh:

===============================
Merge Mesh Utility
===============================

.. _isaac_merge_mesh_about:

About
=================

The :ref:`isaac_merge_mesh` Extension is used to merge multiple prims into a single mesh.
Geometry subsets are used when there are multiple materials on the set of meshes being merged.

To access this Extension, go to the `top menu bar` and click **Tools**> **Robotics** > **Asset Editors** > **Mesh Merge Tool**.
This extension is enabled by default. If it is ever disabled, it can be re-enabled from the :doc:`Extension Manager <extensions:ext_core/ext_extension-manager>`
by searching for ``isaacsim.util.merge_mesh``.


.. _isaac_merge_mesh_user_interface:

User Interface
=================

.. figure:: /images/isaac_merge_mesh_ui.png
    :align: center
    :alt: Merge Mesh UI

Configuration Options
^^^^^^^^^^^^^^^^^^^^^^

Under the input section you will observe:

* **Source Prim**: This text box shows the prims selected to be merged. TThis gets automatically populated by the selection in the scene. The first item selected will be used as base and origin for the merged asset.
* **Submeshes**: The number of meshes the selected prim contains.
* **Geometry Subsets**: The number of subsets the selected prim contains.
* **Materials**: The number of unique materials used by the selected prim.

.. note:: To change the mesh origin, you can first select an empty Xform at the desired origin pose, then select all meshes you want to merge afterwards.

Under the output section you will observe:

* **Destination Prim**: The auto-generated output path for the merged mesh.
* **Geometry Subsets**: The number of geometry subsets created after merge. Each unique material will generate a subset on the final merged mesh.

The options when merging are:

* **Clear Parent Transform**: When selected, the merged mesh transform will be at world origin, otherwise it will be the same as the source prim.
* **Deactivate source assets**: When selected, the prims that were selected for merging will be set to "inactive" (effectively deleted, but can be reactivated later).
* **Combine Materials**: When selected, provide the Prim for the Looks folder, it will combine all meshes that use the same material (checked by material name) into a single geomsubset, and move that material to the provided Looks Folder. This is useful for Onshape and Cad imported assets, that contain internal Looks Scopes that are sublayers to the a materials USD layer.

.. _isaac_merge_mesh_tutorials:

Tutorials and Examples
======================================

The following example showcases how to best use this extension:

.. raw:: html

    <div id="kaltura_player_915765221" style="width: 560px;height: 395px"></div>
                    <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/53712482"></script>
                    <script type="text/javascript">
                    try {
                      var kalturaPlayer = KalturaPlayer.setup({
                        targetId: "kaltura_player_915765221",
                        provider: {
                          partnerId: 2935771,
                          uiConfId: 53712482
                        }
                      });
                      kalturaPlayer.loadMedia({entryId: '1_2ddk0c6f'});
                    } catch (e) {
                      console.error(e.message)
                    }
                  </script>