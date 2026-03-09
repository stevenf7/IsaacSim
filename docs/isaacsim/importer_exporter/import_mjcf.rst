
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

#. Load the MJCF Importer extension, which should be automatically loaded when |isaac-sim| opens and can be accessed from the **File** > **Import** menu. If not MJCF files are not listed in the import formats, go to **Window** > **Extensions** and enable ``isaacsim.asset.importer.mjcf`` and ``isaacsim.asset.importer.mjcf.ui`` extensions.

#. In the file selection dialog box, navigate to the desired folder, and select the desired MJCF file. For this example, use the Ant ``nv_ant.xml`` file  that comes with this extension, included in the extension assets. To find it:
    
    - Click on the folder icon beside *AUTOLOAD* to find the **isaacsim.asset.importer.mjcf** extension.
    - Navigate to ``/data/mjcf`` and find ``nv_ant.xml`` file.

#. Change the import options according to the your needs. Check :ref:`isaac_sim_mjcf_configuration_options` for more information on the import options.

    .. image:: /images/isim_6.0_full_ext-isaacsim.asset.importer.mjcf-3.0.0_user_interface.png
        :align: center
        :alt: Select MJCF to Import


#. Click the **Import** button to add the robot to the stage.

    .. image:: /images/isim_6.0_full_ext-isaacsim.asset.importer.mjcf-3.0.0_user_interface_ant.png
        :align: center
        :alt: Imported Ant

The robot is now imported into the stage. You can now use it in your simulation. You can perform additional changes to the asset after it's imported, such as adding sensors, changing materials, and updating the joint drives and configuration to achieve a more stable simulation. Robots are mapped as articulations in the simulation, and for a complete guide in tuning articulations, refer to `Articulation Stability Guide <https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/guides/articulation_stability_guide.html>`_.


Importing MJCF Using Python API
========================================

Do the exact same thing with Python scripting instead.

#. Open the **Script Editor**. Go to the top Menu Bar and click **Window > Script Editor**.
#. The window for the **Script Editor** is visible in the workspace.
#. Copy the following code into the **Script Editor** window.

    .. literalinclude:: ../snippets/importer_exporter/import_mjcf/copy_the_following_code_into_the_script_editor_win.py
        :language: python

#. Click the **Run (Ctrl + Enter)** button to import the Ant robot.

Importing MJCF Using Python Standalone
========================================

Do the exact same thing with Python standalone instead.

#. Open a terminal and navigate to the root of the Isaac Sim installation.
#. Run the following command:

    .. code-block:: bash

        ./python.sh standalone_examples/api/isaacsim.asset.importer.mjcf/mjcf_import.py 

    **Args:**
        - ``--mjcf``: Path to the MJCF file (.xml) to import.
        - ``--usd-path``: Directory to write converted USD assets.
        - ``--merge-mesh``: Merge meshes after conversion.
        - ``--debug-mode``: Enable debug mode and keep intermediate outputs.
        - ``--import-scene``: Import the MJCF simulation settings along with the model (default True).
        - ``--collision-from-visuals``: Generate collision geometry from visuals.
        - ``--collision-type``: Collision geometry type (e.g. "Convex Hull", "Convex Decomposition", "Bounding Sphere", "Bounding Cube").
        - ``--allow-self-collision``: Allow self-collision for the imported asset.
        - ``--test``: uses nv_ant.xml test asset into a temp directory

    Example:

    .. code-block:: bash

        ./python.sh standalone_examples/api/isaacsim.asset.importer.mjcf/mjcf_import.py --mjcf /path/to/nv_ant.xml --usd-path /path/to/output --merge-mesh

Known Issues
=======================

In USD, a joint is defined as a kinematics constraint between two rigid bodies. When a joint is created, the DOF is limited only to the axis of the joint.
For example, a revolute joint has only one DOF, and removes the other five DOFs. 

In MuJoCo, a joint is defined as a degree of freedom, enabling multiple joints to be combined together to create more degrees of freedoms. For example, 
an x-axis revolute joint and a y-axis revolute joint can be combined together to create a 2D x-y axis revolute joint.
This is not supported in USD, if two revolute joints between two bodies are defined, the system would form a kinematic loop, and become overconstrained.

The current solution is to place a dummy link between the two bodies, and create a joint between the dummy link and the other body in the MJCF file.
For example, if two revolute joints are defined between the body and the ground, a dummy link can be placed between the body and the ground, and a joint 
can be created between the dummy link and the ground and a joint between the dummy link and the body. This will create a 2D x-y axis revolute joint.

Summary
=======================

This tutorial covered the following topics:

#. Importing MJCF file using GUI
#. Importing MJCF file using Python API
#. Importing MJCF file using Python Standalone


Further Learning
^^^^^^^^^^^^^^^^^^^^^^

Review :ref:`isaac_sim_mjcf_importer` to learn more about the different configuration settings to import a MJCF in |isaac-sim|.
Learn how to use the :ref:`isaac_gain_tuner` to tune the gains for your robot.

