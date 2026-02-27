..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaacsim_ros2_reference_architecture:

================================================
ROS 2 Reference Architecture
================================================

This section presents an overview of the ROS 2 workflow with |isaac-sim_short| and the associated building blocks.
It is designed to provide robotics developers working with ROS 2 with the necessary information to integrate |isaac-sim_short|
into their existing workflows for simulating and validating their robot software stacks.


This workflow, which includes importing assets, setting up and interacting with the scene can be performed in the GUI
or in headless mode with Python scripting.
|isaac-sim_short| also comes with an internal set of minimal ROS 2 libraries, which can be used to enable the ROS 2 Bridge
when there is no system level ROS 2 installation, refer to :ref:`isaac_sim_app_no_system_installed_ros` .
This can be particularly useful in container based workflows where simulation and the robot software are run in 2 separate containers.
The |isaac-sim_short| container can interact with ROS 2 software running in another container after the bridge is enabled.



.. image:: /images/isim_4.5_ros_ref_external_ref_arch.png
    :align: center
    :alt: Isaac Sim ROS 2 Reference Architecture
    :width: 75%


The URDF importer can be used to import the robot. After adding sensors, developers can use Python scripting or ROS 2
OmniGraph Nodes provided with the ROS 2 Bridge Extension to enable their simulation scene and robot to interact with ROS 2.



Robot URDF
-------------

The Unified Robotics Description Format or `URDF <https://docs.ros.org/en/humble/Tutorials/Intermediate/URDF/URDF-Main.html>`_ is
an XML file format, which is commonly used in ROS 2 and the robotics community to describe the elements of a robot.
All the links, joints, visual and collision meshes and materials of the robot are represented with their hierarchical structure in the XML file.
Developers can use packages and `tools <https://hiro-group.ronc.one/vscode_urdf_previewer.html>`_
to verify and `visualize <https://foxglove.dev/urdf>`_ URDF files. Many robotics manufacturers provide URDF models for their robots.


URDF contains various `elements/tags <https://wiki.ros.org/urdf/XML>`_ like robot, sensors, joints and transmission to define
the robot and its components. Optionally, custom Isaac Sim tags for sensors can also be added to the URDF file.
This currently supports pre-configured lidars or user-defined configurations.


Popular CAD modeling softwares like SolidWorks, Fusion360 and OnShape support methods to export robot models to URDF.



URDF Importer
---------------

|isaac-sim_short| comes with an extension to :ref:`isaac_sim_app_tutorial_advanced_import_urdf`, which allows users to bring in their own robot URDF files.
Extensions enable developers to add functionality and integrate other tools for Isaac Sim. The URDF importer extension is open-source
and converts the robot URDF to USD so that it can be used with |isaac-sim_short|. The importer can directly ingest the URDF file or subscribe
to a ROS 2 topic on which the robot description is being published. Various parameters like importing inertia tensors,
fixing the base link, setting joint strength and damping, collision and physics properties can be set while importing the robot.
Tuning of the physics parameters of the robot is also supported through a variety of Schemas and APIs.


Developers can also access a variety of pre-packaged :ref:`isaac_assets_robots`, which can be directly added to any scene.



Environment Setup
-------------------


The `CAD converter <https://docs.omniverse.nvidia.com/extensions/latest/ext_cad-converter.html>`_ can be used to import assets from various CAD modeling tools.
|isaac-sim_short| also comes with more than a thousand of `‘SimReady’ <https://developer.nvidia.com/omniverse/simready-assets>`_ assets.
SimReady or simulation-ready assets are physically accurate 3D objects that encompass accurate physical properties, behavior and connected data streams
to represent the real world in simulated digital worlds. These can be used as building blocks to construct the environment for the robots.
The warehouse asset collection comprises over 800 3D assets of commonly available tools, equipment and items in a warehouse including forklifts, pallets,
racks and shelves.



.. image:: /images/isim_4.5_base_ref_external_arch_simready_warehouse.png
    :align: center
    :alt: SimReady Warehouse Assets
    :width: 75%


Isaac Sim also contains a few :ref:`isaac_assets_environments` like a simple room, warehouse, hospital and office.
Developers can leverage various tools like :ref:`isaac_sim_warehouse_creator` and  :ref:`isaac_conveyor` to build an environment for their use case.
People assets can also be added to the scene performing tasks like walking, sitting, standing and looking around through the :ref:`Replicator Agents <isaac_sim_app_tutorial_replicator_character>`.
extension. 3D scenes built in other digital content creation tools can also be imported using OpenUSD.



Add Sensors
-------------


After the robot is imported and the environment is set up, the next step is adding the relevant sensors. Developers can leverage a variety of sensors including:
RGB and RGBD cameras, 2D and 3D RTX Lidars, and physics-based sensors (for example, contact sensor, IMUs, radar, ultrasonic sensors, …).
Commonly used sensors including cameras like Intel Realsense, Hawk Stereo camera by Leopard Imaging, ZED X by Stereolabs and Lidars from Hesai, Velodyne,
SLAMTEC, SICK and Ouster are available and many more can be found at :ref:`isaac_assets_camera_depth_sensors` and :ref:`isaac_assets_nonvisual_sensors`. These can be added directly to the robot and the environment.



Configure ROS 2 Bridge Interface
----------------------------------

Isaac Sim connects to ROS 2 through the ROS 2 Bridge extension. There are two main ways in which developers can interface with ROS 2 using this extension:

    1. ROS 2 OmniGraph Nodes
    2. Python Scripting




ROS 2 OmniGraph Nodes
^^^^^^^^^^^^^^^^^^^^^^^

This ROS 2 Bridge extension consists of various :ref:`isaac_sim_app_tutorial_gui_omnigraph` (OG) Nodes designed for ROS 2 developers.
OG nodes are not the same as ROS 2 nodes, they have separate frameworks. OG nodes provide an encapsulated piece of functionality that can be used in a
connected graph structure to perform complex tasks in a simulation scene. As an example, an OG node can be created, which adds a cube to the current
stage and changes its position based on some constraints. A large collection of OG nodes are provided with extensions in |isaac-sim_short|.


The ROS 2 Bridge gives developers access to a variety of OG nodes useful for robotics tasks, which can interface with ROS 2. These OG nodes can be used to
publish data from a simulated camera or lidar, publish the transform tree of a robot and subscribe to velocity messages, refer to the :ref:`isaac_ros2_tutorials_page` page.
They can be connected to build an Action Graph, which enables complex tasks like navigation and manipulation with popular ROS 2 packages.
Many commonly used Action Graphs can now be directly added to the scene and can be found at :ref:`isaac_sim_app_tutorial_advanced_omnigraph_shortcuts`

.. figure:: /images/isim_4.5_ros_tut_gui_ros2_clock_publisher_system_time.png
    :align: center
    :width: 500
    :alt: ROS 2 Clock publisher with System Time


The image above denotes a simple action graph created using OG nodes. This enables publishing simulation time on a ROS 2 topic with the appropriate message type.
Some of the key OG nodes from the figure above perform the following tasks:

    1. On Playback TIck: This node executes an output execution pulse during playback
    2. Isaac Read Simulation Time: Provides the simulation time
    3. ROS 2 Publish Clock: This OG node is a part of the ROS 2 Bridge Extension. It is active after it is connected to the output of the ‘On Playback Tick’. It receives the simulation time from the ‘Isaac Read Simulation Time’ node and publishes this on a ROS 2 topic, which can be modified in the node.  This is important because simulation time is used for synchronizing the ROS 2 nodes, which is not the same as real world time.



The ROS 2 OG nodes also have various parameters like topic name, namespace, context, and QoS, which can be modified.


Developers can write their own OG nodes for task specific requirements as well in C++ or Python. For example if you want to publish contact sensor state on a custom message topic.



Python Scripting
^^^^^^^^^^^^^^^^^^^


Isaac Sim comes with a built-in Python 3 environment. This can be accessed from the `Script Editor <https://docs.isaacsim.omniverse.nvidia.com/latest/development_tools/omniverse_script_editor.html>`_
or through the standalone :ref:`isaac_sim_python_environment`. Enabling the ROS 2 Bridge gives access to `rclpy <https://github.com/ros2/rclpy>`_, the ROS 2 client library for Python.
This makes it possible to write your custom ROS 2 code containing nodes, services and actions, which can directly access and modify data from the
scene and the simulated robot when scripting in Python. ROS 2 custom message support is enabled by sourcing your workspace before running |isaac-sim_short|, refer to the
:ref:`isaac_sim_app_ros2_custom_message_python` tutorial.


ROS 2 OG nodes can also be created, modified and connected to form an Action Graph using their Python APIs.




Simulate Scene
------------------


After the environment and robots have been imported and the action graphs for ROS 2 have been set up we can start simulating the scene.
After you hit play in simulation, all ROS 2 OG nodes will enter the `active` state and will publish and subscribe to data depending on how the graph was set up.
An important note here is that all ROS 2 OmniGraph nodes depend on the simulation being in the running or active state, which happens after hitting play.



ROS 2 Packages
----------------


After starting the simulation, developers can use their ROS 2 packages to control the simulated robot and scene. The ROS 2 OG nodes or your Python code will perform the
role of interfacing with your ROS 2 software and controlling the simulated robot in the scene. For example, sensor and robot state data can be sent using the ROS 2
bridge, which the robotics software stack can then consume. These algorithms might output actions on the basis of the input received. Then, the simulated robot performs these actions.



Next Steps
------------

Refer to the ROS Tutorials for getting started.