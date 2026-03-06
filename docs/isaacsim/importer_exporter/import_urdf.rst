
.. _Visual Studio Code: https://code.visualstudio.com/download
.. _isaac_sim_app_tutorial_advanced_import_urdf:

==========================================
Tutorial: Import URDF
==========================================

Learning Objectives
=======================
This tutorial shows how to import a URDF and convert it to a USD in |isaac-sim|.
After this tutorial, you can use URDF files in your pipeline while using |isaac-sim|.

*10-15 Minutes Tutorial*

Getting Started
=======================

**Prerequisites**

- Review the :ref:`isaac_sim_intro_quickstart_series` prior to beginning this tutorial.
- Check the :ref:`URDF Importer Extension<isaac_sim_urdf_importer>` for more details on the extension.


.. tab-set::

    .. tab-item:: Direct Import UI

        To import a UR10 URDF from the *Built in URDF* files that come with the extension:

        #. Enable the `isaacsim.asset.importer.urdf` extension in |isaac-sim| if it is not automatically loaded by going to **Window > Extensions** and enable `isaacsim.asset.importer.urdf`.

            - In this example, import the `ur10.urdf` that is included in the URDF importer extension. To find it:
                - Click on the file icon beside *AUTOLOAD* to find the *isaacsim.asset.importer.urdf* extension.
                - Navigate to ``/data/urdf/robots/ur10/urdf`` and find ``ur10.urdf``, and copy this path.

        #. Accesses the URDF extension by going to the **File > Import**, and select an URDF file you want to import. In this case, paste the path above to the navigation bar and left-click on **ur10.urdf**.

            .. image:: /images/isim_6.0_full_ext-isaacsim.asset.importer.urdf-3.0.0_gui_0.png
                :align: center
                :alt: find UR10 URDF
        
        #. Specify the settings you want to use to import UR10 with:

            - Set USD Ouptut to your desired output location for the USD.
            - Select or enter an address to store the output USD file.
            - Select **Merge Mesh** to merge the meshes under a rigid body into a single mesh.
            - Select **Allow Self-Collision** for the Colliders section and leave everything else as default.

            .. image:: /images/isim_6.0_full_ext-isaacsim.asset.importer.urdf-3.0.0_gui_1.png
                :align: center
                :alt: import settings

            .. note:: You must have write access to the output directory used for import, it will default to the same directory as your URDF.

        #. Click the **Import** button to add the robot to the stage.

            .. image:: /images/isim_6.0_full_ext-isaacsim.asset.importer.urdf-3.0.0_gui_2.png
                :align: center
                :alt: Imported UR10

        #. Visualize the collision meshes, not all the rigid bodies need to have collision properties, and collision meshes are often a simplified mesh compared to the visual ones. Therefore you might want to visualize the collision mesh for inspection.
        To visualize collision in any viewport:

            * **Select**: the eye icon in the upper left corner of the viewport.
            * **Select**: Show by type.
            * **Select**: Physics.
            * **Select**: Colliders.
            * **Check**: All.

            .. image:: /images/isim_6.0_full_ext-isaacsim.asset.importer.urdf-3.0.0_gui_3.png
                :align: center
                :width: 660

        ..  Note:: See the :ref:`isaac_gain_tuner` tutorial to tune the gains for your robot.

            - Set the joint drive type to **Velocity** drive for the velocity controlled joints (that is, wheels), and **Position** for the position controlled joints (that is, steering joint).
            - Set the **Joint Drive Strength** to the desired level. This will be imported as the joint's damping parameter. Joint stiffness are always set to zero in velocity drive mode.

        .. Note:: If you are importing a torque controlled mobile robot such as a quadruped:

            - Set the joint drive type to **None** drive for the torque controlled joints (that is, legs), and **Position** or **Velocity** for the position or velocity controlled joints.
            - Set the **Joint Drive Strength** to the desired level. For the torque controlled drives, stiffness and damping have no effect and will be imported as zero.



    .. tab-item:: Python API

        #. Open the **Script Editor**. Go to the top Menu Bar and click **Window > Script Editor**.
        #. The window for the **Script Editor** is visible in the workspace.
        #. Copy the following code into the **Script Editor** window.

            .. literalinclude:: ../snippets/importer_exporter/import_urdf/import_urdf_python_api.py
                :language: python

    .. tab-item:: Python Standalone Script

        Do the exact same thing with Python standalone instead.

        #. Open a terminal and navigate to the root of the Isaac Sim installation.
        #. Run the following command:

            .. code-block:: bash

                ./python.sh standalone_examples/api/isaacsim.asset.importer.urdf/urdf_import.py 

            **Args:**
                - ``--urdf``: Path to the URDF file (.urdf) to import.
                - ``--usd-path``: Directory to write converted USD assets.
                - ``--merge-mesh``: Merge meshes after conversion.
                - ``--debug-mode``: Enable debug mode and keep intermediate outputs.
                - ``--collision-from-visuals``: Generate collision geometry from visuals.
                - ``--collision-type``: Collision geometry type (e.g. default, Convex Hull, Convex Decomposition).
                - ``--allow-self-collision``: Allow self-collision for the imported asset.
                - ``--test``: uses nv_ant.xml test asset into a temp directory
                - ``--ros-package``: ROS package mapping in format 'name:path'. Can be specified multiple times for multiple packages.

        Example:

        .. code-block:: bash

            ./python.sh standalone_examples/api/isaacsim.asset.importer.urdf/urdf_import.py -u /path/to/ur10.urdf --usd-path /path/to/output --merge-mesh
            
    .. tab-item:: Import from ROS 2 Node

        .. _isaac_sim_urdf_from_ros:

        Importing a URDF through a ROS 2 node is a powerful way to integrate |isaac-sim| with your existing ROS 2 workflow. This allows you to import a URDF from a ROS 2 node and use it in |isaac-sim|, also indirectly enabling importing XACRO definitions without explicit conversion to URDF.

        .. note:: This tutorial is only supported on Linux and for Isaac Sim (while it may be possible to run in other Omniverse Applications, it is not covered by this tutorial and the extension may not work as expected).

        **Prerequisites**

        - :ref:`ROS 2<isaac_sim_app_install_ros>`
        - A ROS 2 workspace with a robot description (for example `Universal Robots ROS 2 Description <https://github.com/UniversalRobots/Universal_Robots_ROS2_Description>`_ ).
        - Follow the tutorials on how to `set up a ROS 2 workspace (Humble) <https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Creating-A-Workspace/Creating-A-Workspace.html>`_  and include a robot description like the one in this example, along with all its dependencies.

        **Steps**

        - Terminal 1
            - Source ROS 2
            - Launch a transform publisher for the robot description node (for example :code:`ros2 launch ur_description view_ur.launch.py ur_type:=ur10e`).
        - Terminal 2
            - Source ROS 2
            - Pick the ROS 2 node name for the node just created with :code:`ros2 node list`. For example, :code:`robot_state_publisher`.
        - Terminal 3
            - Source ROS 2
            - Start |isaac-sim_short|
            - Enable the extension :code:`isaacsim.ros2.urdf`
            - Open the URDF Importer using the **File > Import from ROS 2 URDF Node** menu
            - Put the node name in the text box
            - Click Find Node to find the node
            - Define an output directory, if it's not defined, it will be stored in the extension(isaacsim.ros2.urdf)'s data folder
            - Import

        **Extra steps to try:**

        - Terminal 1
            - Stop the publisher, change it to another robot and start service again (for example, :code:`ros2 launch ur_description view_ur.launch.py ur_type:=ur3`)
        - Terminal 3
            - Click the **Find Node** button
            - Change the output directory
            - Import


The robot is now imported into the stage. You can now use it in your simulation. You can perform additional changes to the asset after it's imported, such as adding sensors, changing materials, and updating the joint drives and configuration to achieve a more stable simulation. Robots are mapped as Articulations in the simulation, and for a complete guide in tuning articulations, refer to `Articulation Stability Guide <https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/guides/articulation_stability_guide.html>`_.


Summary
=======================

This tutorial covered the following topics:

#. Importing URDF file using GUI
#. Importing URDF file using Python
#. Importing URDF file using a ROS Node
#. Using the imported URDF in a Task
#. Visualizing collision meshes
#. Setting up importing a robot with the UI through the built-in examples

Further Learning
^^^^^^^^^^^^^^^^^^^^^^

Checkout :ref:`isaac_sim_urdf_importer` to learn more about the different configuration settings to import a URDF in |isaac-sim|.
