
.. _Visual Studio Code: https://code.visualstudio.com/download
.. _isaac_sim_app_tutorial_advanced_import_mjcf:

==========================================
Tutorial: Import MJCF
==========================================

Learning Objectives
=======================
This tutorial shows how to import a MJCF model and convert it to a USD in |isaac-sim|.
After this tutorial, you can use MJCF files in your pipeline while using |isaac-sim|.

*5-10 Minute Tutorial*

Getting Started
=======================

**Prerequisites**

- Review the :ref:`isaac_sim_intro_quickstart_series` prior to beginning this tutorial.

Using the MJCF Importer
========================================

Begin by importing an Ant MJCF from the *Built in MJCF* files that come with the extension.

#. Load the MJCF Importer extension, which should be automatically loaded when |isaac-sim| opens and can be accessed from the **File** > **Import** menu. If not MJCF files are not listed in the import formats, go to **Window** > **Extensions** and enable ``isaacsim.asset.importer.mjcf``.

#. In the file selection dialog box, navigate to the desired folder, and select the desired MJCF file. For this example, use the Humanoid ``nv_humanoid.xml`` file  that comes with this extension, included in the extension assets. To find it:
    
    - Click on the folder icon beside *AUTOLOAD* to find the **isaacsim.asset.importer.mjcf** extension.
    - Navigate to ``/data/mjcf`` and find ``nv_humanoid.xml``.

#. Change the import options according to the your needs. Check :ref:`isaac_sim_mjcf_configuration_options` for more information on the import options.

    .. image:: /images/isim_4.5_base_ext-isaacsim.asset.importer.mjcf-2.3.0_gui_0.png
        :align: center
        :alt: Select MJCF to Import


#. Click the **Import** button to add the robot to the stage.

    .. image:: /images/isim_4.5_base_ext-isaacsim.asset.importer.mjcf-2.3.0_gui_humanoid.png
        :align: center
        :alt: Imported Humanoid

The robot is now imported into the stage. You can now use it in your simulation. You can perform additional changes to the asset after it's imported, such as adding sensors, changing materials, and updating the joint drives and configuration to achieve a more stable simulation. Robots are mapped as articulations in the simulation, and for a complete guide in tuning articulations, refer to `Articulation Stability Guide <https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/guides/articulation_stability_guide.html>`_.


Importing MJCF Using Python
========================================

Do the exact same thing with Python scripting instead.

#. Open the **Script Editor**. Go to the top Menu Bar and click **Window > Script Editor**.
#. The window for the **Script Editor** is visible in the workspace.
#. Copy the following code into the **Script Editor** window.

    .. literalinclude:: ../snippets/importer_exporter/import_mjcf/copy_the_following_code_into_the_script_editor_win.py
        :language: python

#. Click the **Run (Ctrl + Enter)** button to import the Ant robot.


Summary
=======================

This tutorial covered the following topics:

#. Importing MJCF file using GUI
#. Importing MJCF file using Python
#. Create a Ground Plane


Further Learning
^^^^^^^^^^^^^^^^^^^^^^

Review :ref:`isaac_sim_mjcf_importer` to learn more about the different configuration settings to import a MJCF in |isaac-sim|.
