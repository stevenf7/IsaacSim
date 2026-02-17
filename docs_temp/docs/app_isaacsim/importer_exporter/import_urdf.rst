
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

    .. tab-item:: Direct Import

        To import a Franka Panda URDF from the *Built in URDF* files that come with the extension:

        #. Enable the `isaacsim.asset.importer.urdf` extension in |isaac-sim| if it is not automatically loaded by going to **Window > Extensions** and enable `isaacsim.asset.importer.urdf`.

            - In this example, import the `panda_arm_hand.urdf` that is included in the URDF importer extension. To find it:
                - Click on the file icon beside *AUTOLOAD* to find the *isaacsim.asset.importer.urdf* extension.
                - Navigate to ``/data/urdf/robots/franka_description/robots`` and find ``panda_arm_hand.urdf``, and copy this path.


            .. image:: /images/isim_4.5_full_tut_gui_import_urdf_enable_extension.png
                :align: center
                :alt: Enable extension and find Franka URDF


        #. Accesses the URDF extension by going to the **File > Import**, and select an URDF file you want to import. In this case, paste the path above to the navigation bar and left-click on **panda_arm_hand.urdf**.

            .. image:: /images/isim_4.5_full_tut_gui_import_urdf_select_robot.png
                :align: center
                :alt: Select Franka URDF

        #. Specify the settings you want to use to import Franka with:

            - Set USD Ouptut to your desired output location for the USD.
            - Select **Static Base** and leave **Default Density** empty.
            - Refer to :ref:`urdf importer Robot Properties<isaac_sim_urdf_robot_properties>` for joints and drive instructions. In this tutorial, increase the natural frequencies of the joints to reduce oscillations during movement.
            - Select **Allow Self-Collision** for the Colliders section and leave everything else as default.

            .. note:: You must have write access to the output directory used for import, it will default to the same directory as your URDF.

        #. Click the **Import** button to add the robot to the stage.

            .. image:: /images/isim_4.5_full_tut_viewport_import_urdf_franka.png
                :align: center
                :alt: Imported Franka

        #. Visualize the collision meshes, not all the rigid bodies need to have collision properties, and collision meshes are often a simplified mesh compared to the visual ones. Therefore you might want to visualize the collision mesh for inspection.
        To visualize collision in any viewport:

            * **Select**: the eye icon in the upper left corner of the viewport.
            * **Select**: Show by type.
            * **Select**: Physics.
            * **Select**: Colliders.
            * **Check**: All.

            .. image:: /images/isim_4.5_full_tut_viewport_import_urdf_visualize_franka_colliders.png
                :align: center
                :width: 660

        .. Note:: If you are importing a mobile robot, you might need to change the following settings:

            - Select :ref:`Moveable Base<isaac_sim_urdf_configuration_options>`.
            - Set the joint drive type to **Velocity** drive for the velocity controlled joints (that is, wheels), and **Position** for the position controlled joints (that is, steering joint).
            - Set the **Joint Drive Strength** to the desired level. This will be imported as the joint's damping parameter. Joint stiffness are always set to zero in velocity drive mode.

        .. Note:: If you are importing a torque controlled mobile robot such as a quadruped:

            - Select :ref:`Moveable Base<isaac_sim_urdf_configuration_options>`.
            - Set the joint drive type to **None** drive for the torque controlled joints (that is, legs), and **Position** or **Velocity** for the position or velocity controlled joints.
            - Set the **Joint Drive Strength** to the desired level. For the torque controlled drives, stiffness and damping have no effect and will be imported as zero.


    .. tab-item:: UI Integration Examples

        Activate **Windows** > **Examples** > **Robotics Examples**, which will open the **Robotics Examples** tab at the bottom dock.

        .. note::
            For these examples, wait for materials to get loaded.
            You can track progress on the bottom right corner of the UI.

        There are Four examples available in the **Import Robots** section:

        - **Nova Carter URDF**
        - **Franka URDF**
        - **Kaya URDF**
        - **UR10 URDF**

        Each one of them contains an individual import configuration and post import setup in code, but overall the usage is similar:


        #. Go to the **Robotics Examples** tab and navigate to **Import Robots > <Robot> URDF**.
        #. Press the **Load Robot** button to import the URDF into the stage, add a ground plane, add a light, and a physics scene.
        #. Press the **Configure Drives** button to configure the joint drives. This sets each drive stiffness and damping value.
        #. Press the **Open Source Code** button to view the source code. The source code illustrates how to import and integrate the robot using the Python API.
        #. Press the **PLAY** button to begin simulating.
        #. Press the **Move to Pose** button to make the robot move to a home or rest position.

        .. image:: /images/isim_4.5_full_ext-isaacsim.asset.importer.urdf-2.3.0_gui_example_import_franka.png
            :align: center
            :alt: Franka URDF Sample




    .. tab-item:: Python Script


        Use Python scripting to do what can be done through the Import window. Then use the imported robot with one of
        the tasks defined under **isaacsim.robot.manipulators.examples.franka** extension to follow a target in the stage.

        #. Open the **Hello World** example.
            - Go to the top Menu Bar and click **Window > Examples > Robotics Examples**.
            - In the **Robotics Examples** tab at the bottom, select **General > Hello World**.
        #. Validate that the window for the *Hello World* example extension is in the workspace.
        #. Click the **Open Source Code** button to launch the source code for editing in `Visual Studio Code`_.
        #. Edit the ``hello_world.py`` file as shown below:

        .. literalinclude:: ../snippets/importer_exporter/import_urdf/edit_the_hello_worldpy_file_as_shown_below.py
            :language: python

        #. Press :code:`Ctrl+S` to save the code and hot-reload |isaac-sim|.
        #. Click the **File > New From Stage Template > Empty** to create a new stage. Click **Don't Save** if the simulator is prompting you to save the stage.
        #. Open the menu again and load the example.
        #. Click the **LOAD** button and move the target prim around to observe the robot follow it.



            .. figure:: /images/isaac_sim_import_urdf.gif
                :align: center



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
            - Define an output directory
            - Import

        **Extra steps to try:**

        - Terminal 1
            - Stop the publisher, change it to another robot and start service again (for example, :code:`ros2 launch ur_description view_ur.launch.py ur_type:=ur3`)
        - Terminal 3
            - Click the **Refresh** button
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
