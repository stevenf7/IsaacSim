.. _isaac_sim_app_robot_wizard:

==========================================
Robot Wizard [Deprecated]
==========================================

.. warning::

   **Deprecated:** The Robot Wizard extension (``isaacsim.robot_setup.wizard``) is deprecated since Isaac Sim 6.0.0 and will be removed in a future release.

The Robot Wizard was designed to speed up the process of setting up a robot in |isaac-sim_short|. It allowed you to define the robot's hierarchy, organize the meshes, add colliders, joints and joint drives. It automatically applied relevant Schemas and APIs without needing to manually edit the USD files. It separated the robot into different configurations based on the desired structure described in :ref:`isaac_sim_app_reference_asset_structure`.


The following sections explain the UI and functions behind each step in the wizard. To observe the wizard in action, refer to :ref:`isaac_sim_app_robot_wizard_tutorials`.



.. _isaac_sim_app_robot_wizard_file_structure:

Overview
=====================

The Robot Wizard guides you through the following steps:

^ **File Preparation**: Load the robot model and allocate folders and files for the final robot files.

* **Organize Link Hierarchy**: Define the robot's hierarchy and link the parent-mesh child relationships.

* **Colliders**: Examine colliders to the robot's links.

* **Joints and Drives**: Add joints to the robot's links and drives and configure their properties.  

The resulting files of the Robot Wizard are all placed in a folder, which you will have a chance to indicate in the wizard. The folder contains the following files: 


- <robot_root_folder>/configurations:
    - The folder that contains the robot's configurations USD files. The configurations are the different variants of the robot, such as a robot with or without physics, with sensors, and different end-effectors.

- <robot_root_folder>/configurations/<robot-name>_base.usd
    - The configuration file that contains the robot's base mesh and hierarchy. 

- <robot_root_folder>/configurations/<robot-name>_physics.usd
    - The configuration file that contains the robot's physics setup in a sublayer. This includes the rigid body definition, colliders, joints, and drives.
    
- <robot_root_folder>/configurations/<robot-name>_robot.usd
    - The configuration file that contains the robot schema, labeling the robot and its components.

- <robot_root_folder>/<robot-name>.usd:
    - The file that contains all the variants of the robot. In this case, the option of a robot with or without physics.




Wizard Steps
=====================


Page Orientation
-------------------

.. figure:: /images/robot_wizard/isim_5.0_full_tut_gui_opening_page.png
    :align: center
    :width: 600

.. list-table::
   :widths: 8 20 72
   :header-rows: 1

   * - Ref #
     - Panel Name
     - Description

   * - 1
     - Wizard Steps
     - The Wizard Steps panel shows your progress. You can click on each step to navigate to it. It will also advance itself as you go through the wizard. The names of the steps will change to green when it's completed.

   * - 2
     - Additional Tools
     - You may open other tools for robot setup here.
    
   * - 3
     - Step Pages
     - Each step in the wizard has a page. You can navigate through the pages by clicking on the step name in the Wizard Steps panel.

   * - 4
     - Next Button
     - The Next button will advance you to the next step in the wizard.

   * - 5
     - Start Over
     - The Button will reset the wizard to the first step.

   * - 6
     - Launch On Startup
     - When checked, the wizard will launch automatically when |isaac-sim_short| is started. It's defaulted to not start.

   * - 7
     - Help
     - Open the documentation page for the wizard in your browser.


.. _isaac_sim_app_tutorial_wizard_add_robot:

Add Robot
-----------------

This page allows you the select the starting point of the robot configuration. For the current iteration, the robot wizard only supports configuring robots that are already loaded in the stage. If you are starting with a URDF or MJCF file, go to **File > Import** can use the importer instead. 


.. figure:: /images/robot_wizard/isim_5.0_full_tut_gui_add_robot_page.png
    :align: center
    :width: 600


**Steps:**

#. Select **Configure a Robot on Stage**. 
#. Indicate the type of the robot you are configuring from the dropdown menu. Pick **custom** if your robot does not fit into the other categories. This will automatically populate the links that are frequently used in the selected robot types in :ref:`isaac_sim_app_tutorial_wizard_hierarchy`.
#. Give your robot a name. You can change it later.
#. Select the parent link of the robot from stage.
#. Click **Prepare Files** to advance to the next step.



.. _isaac_sim_app_tutorial_wizard_file_prep:

Prepare Files
-----------------

This page allows you to indicate the folder where the robot files will be saved. The resulting files are described in :ref:`isaac_sim_app_robot_wizard_file_structure`. While no files are created at this step, they will be created in the subsequent steps.

.. figure:: /images/robot_wizard/isim_5.0_full_tut_gui_file_prep_page.png
    :align: center
    :width: 600

**Steps:**

#. The folder will be created in the format of ``<Root Folder>/configurations/<robot-name>_base.usd``. You can change the name and the root folder.
#. The stage that is currently open will not be the final robot file. You may choose to save a copy of it in the ``<Root Folder>/stage_copy.usd``. If it has unsaved changes, you will also have the choice to save it and overwrite the existing path.
#. The **Robot Files Allocated** displays the filepaths that will be created in the folder. If filepaths text turned purple in color, it means that the file already exists, proceeding without changing the filepath will overwrite the existing file. If it turns red, it means you do not have permission to write to the folder.
#. In the case where you are examining a robot that's loaded to the stage as a reference or payload, the **Additional Information** section contains the path to the original file that the robot is loaded from.
#. Click **Robot Hierarchy** to advance to the next step.



.. _isaac_sim_app_tutorial_wizard_hierarchy:

Robot Hierarchy
-----------------

Assets in |isaac-sim_short| are organized based on how the robot moves. All the components that move as a single link are grouped together under a single parent. This page allows you to organize your robot components accordingly.


.. figure:: /images/robot_wizard/isim_5.0_full_tut_gui_hierarchy_page.png
    :align: center
    :width: 600


.. list-table::
   :widths: 8 20 72
   :header-rows: 1

   * - Ref #
     - Panel Name
     - Description

   * - 1
     - New Link Structure
     - This section displays the new structure of the robot. This structure is based on the links. It might have existing links populated for you if you have chosen a robot type in :ref:`isaac_sim_app_tutorial_wizard_add_robot`. You can always add or remove links by using the buttons in the lower right hand corner.

   * - 2
     - Current Link Structure
     - This section displays the current structure of the robot that's on stage.

   * - 3
     - Parent 
     - The Parent button will be enabled after you've selected a target link from the window above and source links from the window below. Clicking on the button will parent the source link to the target link.

   * - 4
     - Unparent
     - The Unparent button will be enabled after you've selected a link from the window above. Clicking on the button will unparent the link from its parent.    

   * - 5
     - Add/Remove Links
     - The Add/Remove buttons will add/remove links from the new link structure.

   * - 6
     - Clear All/Copy All
     - The Clear All button will clear all the links in the new link structure. The Copy All button will copy all the links in the current link structure to the new link structure.

   * - 7
     - Instructions
     - Expand to observe the instructions for the current step.

   * - 8
     - Add Colliders
     - The Next button will advance you to the add collider step.


Notes
~~~~~~~~~~~~~~~~~~~~~~~~~

- The reorganization is focused on grouping different mesh components under a single parent when they belong to the same link. If you have robots where the mesh is nested under many layers of Xforms, choose only the mesh prim and move that to the top window, and delete (right click > delete) any leftover empty parent prims in the bottom window (old stage) where the mesh has been moved.

- It will also ignore any non-mesh prims, such as materials, joints, and textures. Those will be directly copied over to the new file under relevant parent prims.

- Any mesh that is not parented at the end will also get automatically copied over to the new file, unless explicitly deleted.

- The position of the links is set to align with a "reference child" prim. The reference child prim can be indicated by right clicking on the link in the top window, and selecting **Mark as Reference Child**. If no reference child is indicated through the stage, the link's origin will be positioned at the origin of the first child. Consequently, the transform of all the child meshes will be recalculated to be relative to the parent link's location.

- No actual prims are created or modified while on this page. All changes are implemented when clicking the **Add Colliders** button to move on to the next step.




Add Colliders
-----------------

This page allows you to examine and add the colliders of the robot. 

.. figure:: /images/robot_wizard/isim_5.0_full_tut_gui_collider_page.png
    :align: center
    :width: 600

At this point of the process, all the meshes are purely for visualization purposes. There are no colliders or rigid body physics applied to any of the meshes. 

The table displays the existing meshes of the robot in the first column. The second column displays the collision approximation method that will be applied to the mesh after you complete the page and move on by clicking the **Add Joints & Drives** button. You can modify the approximation method using the dropdown menu.

For this iteration of the wizard, no new colliders can be created on this page. However, you can always manually add additional meshes and apply the necessary :ref:`physics_schemas` directly in the USD file.



Add Joints and Drives
------------------------

This page allows you to add the joints and drives to the robot.

.. figure:: /images/robot_wizard/isim_5.0_full_tut_gui_joint_page.png
    :align: center
    :width: 600

To add a joint, click on the **Create New Joint** button. A popup will appear.

    
.. figure:: /images/robot_wizard/isim_5.0_full_tut_gui_joint_popup.png
    :align: center
    :width: 600

Give the joint a name and select the type of the joint from the dropdown menu. Select the parent and child links the joint will connect, the axis that the joint will move along, and the driver type from the dropdown menu. Then **Create** or **Create & Close** to add the joint to the table on the main page.


.. figure:: /images/robot_wizard/isim_5.0_full_tut_gui_joint_settings.png
    :align: center
    :width: 600

To modify the settings for a particular joint, click on the joint name in the table. Two additional sections will appear. The first section allows you to modify the joint properties. The second section allows you to configure the drive. Selecting a different joint or moving to the next page will automatically save the settings for the previously edit joint. 

No USD changes are made while on this page. All changes are implemented when clicking the **Save Robot** button to move on to the next step.


Save Robot
-----------------

This page finishes the process of creating the robot and creates the final robot files.

.. figure:: /images/robot_wizard/isim_5.0_full_tut_gui_save_robot_page.png
    :align: center
    :width: 600

You must indicate the link or joint to be the "Articulation Root". Think of this as the start of the joint chain. For fixed based robots, this is usually the fixed joint. For mobile robots, this is usually the chassis.

You can also choose to add a minimal environment to the main robot USD file. This can be a ground, a default light, and a PhysicsScene. These will be added outside of the Default Prim of the file, so that they will only show up when the original robot file is opened directly on stage, but not when the robot is added as a reference or payload into another scene. They are particularly useful for debugging purposes.

Click on the **Save Robot** button to finish the process.


Tutorials
=====================   

:ref:`isaac_sim_app_robot_wizard_tutorials`




