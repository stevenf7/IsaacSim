
.. _isaac_sim_app_tutorial_intro_usd:

=============================
Working with USD
=============================

Learning Objectives
=======================

This tutorial covers how to:

- save USD stages
- load and reference existing USD stages
- Organize stage tree hierarchy

Saving Options
==================

- **Save**: To save the current USD stage, go to the Menu Bar and click *Files > Save* or *Files > Save As ..* to save as a new file.
- **Save Flattened As**: Saves the current USD file while merging all components to one mesh.
- **as .usda files**: You have the option to save as ``.usda`` file instead of ``.usd`` file. ``.usda`` file is a human-readable text file format for the given USD stage.
- **Collect Assets**: If your current stage used many reference USD stages, materials, and textures from other folders and servers, you must *Collect Assets* to make sure all the external references that are used in your stage get collected in one folder. To do so, save the current USD locally, then find it in the *Content* tab, right-click on it, and select *Collect Asset*.

.. raw:: html

    <div style="width: 100%;display: inline-block;position: relative;">
        <div id="dummy" style="margin-top: 56%;">
        </div>
        <div align="center">
        <div id="kaltura_player_1" style="position:absolute;top:0;left:0;left: 0;right: 0;bottom:0;border:solid thin black;"></div>
        <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/46302491"></script>
        <script type="text/javascript">
            try {
            var kalturaPlayer = KalturaPlayer.setup({
            targetId: "kaltura_player_1",
            provider:
            { partnerId: 2935771, uiConfId: 46302491 }
            });
            kalturaPlayer.loadMedia(
            {entryId: '1_rhc2d1dw'}
            );
            } catch (e)
            { console.error(e.message) }
        </script>
        </div>
    </div>

Loading Options
===========================

- **Open**: To load a USD stage, go to Menu Bar and click *Files > Open*. This opens the USD stage for direct editing.
- **Add Reference**: *Files > Add Reference* adds a USD file as a reference. Or find the file in the *Content* Tab and drag it into the viewport. You can not edit the referenced USD. 


Set the Stage for a Reference
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To demonstrate adding a file as reference, save the current stage with the cube and cylinders as a mock robot. 
First, you must rearrange the rigid bodies on the stage into a hierarchical structure with meaningful names. 
Put all the rigid body parts of the robot under a single :ref:`isaac_sim_glossary_prim`.

#. Right click inside the *Stage* tab, select *Create > Xform*. 
#. Rename the newly added :term:`Xform<XForm>` to *mock_robot*. The Prim appears under the *World* prim.
#. Drag and drop the Cube, both Cylinders, Physics Material, and Looks folder under *mock_robot*.
#. Rename the Cube and Cylinders to the body, wheel_left, and wheel_right.
#. Save the stage as an USD file.

			.. raw:: html

							<div style="width: 100%;display: inline-block;position: relative;">
											<div id="dummy" style="margin-top: 56%;">
											</div>
											<div align="center">
											<div id="kaltura_player_2" style="position:absolute;top:0;left:0;left: 0;right: 0;bottom:0;border:solid thin black;"></div>
											<script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/46302491"></script>
											<script type="text/javascript">
															try {
															var kalturaPlayer = KalturaPlayer.setup({
															targetId: "kaltura_player_2",
															provider:
															{ partnerId: 2935771, uiConfId: 46302491 }
															});
															kalturaPlayer.loadMedia(
															{entryId: '1_szx9q5qp'}
															);
															} catch (e)
															{ console.error(e.message) }
											</script>
											</div>
							</div>

#. Open a new stage. 
#. Load the USD file as a reference, either *Files > Add Reference* or drag the file from *Content* on to the stage. It loads the referenced USD under a Prim withe the same name as the USD filename. 
#. Validate that it loaded everything under the original :code:`World(defaultPrim)`, including :code:`PhysicsScene`, :code:`defaultLight`, and :code:`GroundPlane`. This may not be optimal if you are loading multiple USD references that all have their own version of PhysicsScenes and defaultLights. You cannot delete them on the new stage because they are loaded by reference, but deleting them in the original USD would make it difficult to work within those USD stages.

To have the necessary environment set up in the USD stages but not export them when they are being referenced, you need to move non-referenced items out of the default Prim:

- Select the robot's parent prim on stage, in this tutorial `/mock_robot`.
- Open the menu *Edit* while the prim is selected, and click on *unparent*. 
- Validate that instead of being under `World`, `mock_robot` is parallel to `World`.
- Right-click on the robot prim again on stage, and *Set as a Default Prim*. Save.
- Open a new stage and load the same file again as a reference, verify that only the robot is imported.

.. raw:: html

    <div align="center">
    <div id="OVK1624_Isaac-tutorial-gui-set-default-prim" style="width: 800px;height: 600px"></div>
                    <script type="text/javascript" src="https://cdnapisec.kaltura.com/p/2935771/embedPlaykitJs/uiconf_id/53712482"></script>
                    <script type="text/javascript">
                    try {
                      var kalturaPlayer = KalturaPlayer.setup({
                        targetId: "OVK1624_Isaac-tutorial-gui-set-default-prim",
                        provider: {
                          partnerId: 2935771,
                          uiConfId: 53712482
                        }
                      });
                      kalturaPlayer.loadMedia({entryId: '1_01lzd38n'});
                    } catch (e) {
                      console.error(e.message)
                    }
                  </script>
    </div>

Summary
========

In this tutorial, you learned how to save and open USD files.

Further Readings
^^^^^^^^^^^^^^^^^^^^^^

More on :doc:`File Menu <composer:menu_file>`, :doc:`Collect Assets <extensions:ext_collect>`, and others in :doc:`Composer <composer:index>`.

