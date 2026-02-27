..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaac_sim_main_reference_architecture:


============================================================
Reference Architecture and Task Groupings
============================================================

Isaac Sim is typically installed and used as one part of a larger solution. Depending on your use case and  requirements, this document provides a reference architecture. Almost all use-cases involve some commonalities, which are highlighted as task groupings in the diagrams below. Within each task grouping your product architecture could include one or more of the products or components that are listed.


Regardless of your product components, most |isaac-sim_short| use cases involve the following high level task groupings that occur in roughly the same order:

.. dropdown:: 1. Geometry Authoring
    :animate: fade-in

    - `SimReady Assets <https://developer.nvidia.com/omniverse/simready-assets>`_
    - :ref:`Isaac Sim Assets <isaac_assets_overview>`

.. dropdown:: 2. Importing Assets
    :animate: fade-in

    - :ref:`Importers and Exporters <isaac_sim_importers_and_exporters>`
    - :ref:`USD Tools <isaac_sim_app_omniverse_usd_tools>`

.. dropdown:: 3. Scene Setup
    :animate: fade-in

    - :ref:`Robot Setup Tools and Standards<isaac_sim_robot_setup>`
    - :ref:`Robot Setup Tutorials <isaac_sim_robot_setup_tutorials>`
    - :ref:`Synthetic Sensors <isaac_sim_sensor_simulation>`

.. dropdown:: 4. Interaction with the Digital Twin
    :animate: fade-in

    - :ref:`Robot Simulation and Controllers <isaac_sim_robot_simulation>`
    - :ref:`Robot Articulation and Physics Tools <isaac_sim_physics>`
    - :ref:`Motion Generation <isaac_sim_motion_generation>`
    - :ref:`Omnigraph <isaac_sim_omnigraph_overview_page>`

.. dropdown:: 5. Use Cases
    :animate: fade-in

    - :ref:`Isaac Lab <isaac_lab_tutorials_page>`
    - :ref:`Synthetic Data Generation <isaac_synthetic_data_generation_page>`
    - :ref:`ROS 2 Bridge <isaac_ros2_tutorials_page>`
    - :ref:`Isaac ROS <isaac_sim_app_isaac_ros_tutorials>`

Typical use-cases are summarized in :ref:`isaac_sim_ra_consumption`.

.. image:: /images/isim_4.5_base_ref_external_arch_res_full.png
    :align: center
    :width: 100%
    :alt: Isaac Sim Reference Architecture





.. _isaac_sim_ra_geometry_authoring:

Geometry Authoring
=====================

The simulation environment (scene) is composed of various components including robots,
static, and dynamic objects. The mechanical and geometrical design for these components
is usually done with CAD software like Solidworks, Pro-E, Catia, AutoCad, or Creo. Parts and
components of varying complexity can be designed and assembled.


Developers can also leverage existing 3D asset libraries, which provide a vast collection of
existing 3D assets. Omniverse and Isaac Sim leverage a file format called `Universal Scene
Description (OpenUSD) <https://www.nvidia.com/en-us/omniverse/usd/>`_.

All assets need to be converted to OpenUSD before they can be used with Isaac Sim, and the default unit for |isaac-sim_short| is meters.


.. image:: /images/isim_4.5_base_ref_external_arch_geom_authoring.png
    :width: 50%
    :alt: Geometry Authoring
    :align: center


NVIDIA provides a vast collection of OpenUSD ‘SimReady’ assets. `SimReady <https://developer.nvidia.com/omniverse/simready-assets>`_, or
simulation-ready, assets are physically accurate 3D objects that have accurate
physical properties, behavior, and connected data streams that are used to represent the real world in
simulated digital worlds. Developers can use these building blocks to construct scenes and
generate data per their requirements. The Warehouse asset collection includes over
800 3D assets of commonly available tools, equipment, and items in a warehouse including
forklifts, pallets, racks, and shelves.


.. image:: /images/isim_4.5_base_ref_external_arch_simready_warehouse.png
    :width: 75%
    :alt: SimReady Warehouse Assets
    :align: center


.. image:: /images/isim_4.5_base_ref_external_arch_simready_pallets.png
    :width: 75%
    :alt: Pallet Collection
    :align: center


.. image:: /images/isim_4.5_base_ref_external_arch_simready_palletjacks.png
    :width: 75%
    :alt: PalletJack Collection
    :align: center


.. _isaac_sim_ra_importing_assets:

Importing Assets
==================


There are extensions that enable importing CAD (Computer Aided Design) files into |isaac-sim_short|
that handle conversion to OpenUSD. Extensions are core building blocks that
interact with and add or extend the functionality of Isaac Sim.


Importing and Creating Environments
-------------------------------------

The `asset importer <https://docs.omniverse.nvidia.com/extensions/latest/ext_asset-importer.html#asset-importer>`_
can be leveraged for importing OBJ, FBX, and glTF formats. The `CAD converter <https://docs.omniverse.nvidia.com/extensions/latest/ext_cad-converter.html#cad-converter>`_
extension supports a variety of popular CAD files from applications including
Catia, Solidworks, AutoCad, and Creo. This enables you to quickly convert and
import your environment into |isaac-sim_short|.


OpenUSD Connections and Data Exchange, formerly Omniverse Connect, is a collection of
`importers <https://docs.omniverse.nvidia.com/connect/latest/catalog.html#importers-exporters>`_,
`exporters <https://docs.omniverse.nvidia.com/connect/latest/catalog.html#exporters>`_,
`converters <https://docs.omniverse.nvidia.com/connect/latest/catalog.html#converters>`_, and
`USD file format <https://docs.omniverse.nvidia.com/connect/latest/catalog.html#file-format-plugins>`_ plug-ins. They enable various 3D applications, products, and file formats to exchange data using OpenUSD.

Some CAD applications have connectors with Omniverse, which allows them to bring over more relevant
and contextual information when converting to USD. For example, PTC Creo, Autodesk Revit, or Autodesk Alias have corresponding connectors. The files generated
from their CAD converters will have all the visual meshes represented in OpenUSD.



.. figure:: /images/isaac_assets_simple_warehouse_multiple_shelves.png
    :align: center
    :alt: Small warehouse multiple shelves
    :width: 75%


.. figure:: /images/isaac_assets_hospital.png
    :align: center
    :alt: Hospital
    :width: 75%


.. figure:: /images/isaac_assets_office.png
    :align: center
    :alt: Office
    :width: 75%


Importing Robots
------------------

|isaac-sim_short| comes with a variety of robots already imported. The pre-imported robots can be found on the :ref:`isaac_assets_robots` page. |isaac-sim_short| also provides advanced options for importing other robots.

If your robot is in `URDF <https://wiki.ros.org/urdf>`_, you can use the :ref:`isaac_sim_urdf_importer` extension from the GUI or from Python. This extension will import the visual meshes and the prim hierarchies (child-parent relationships), along with extra information about how the collision meshes, joints, and sensors are encoded.


You could also use the `Onshape Importer <https://docs.omniverse.nvidia.com/extensions/latest/ext_onshape.html>`_ and :ref:`isaac_sim_mjcf_importer`. With these importers, you will have to add the joint drives in
and may have to tune them. The :ref:`isaac_gain_tuner` allows you to visualize and tune the joints.



.. _isaac_sim_ra_scene_setup:

Scene Setup
==============

You can set up the scene after all the necessary assets are converted to OpenUSD and
imported into |isaac-sim_short|.

To properly simulate real world situations, you must have physics characteristics defined. For example, physics characteristics define if an object is subject to gravity or how solid it is.


.. image:: /images/isim_4.5_base_ref_external_arch_scene_setup.png
    :width: 50%
    :alt: Scene Setup
    :align: center


Adding Physics
----------------


After importing the required assets into Isaac Sim, make sure they have appropriate
Physics for accurate simulations. Some asset importers like the URDF and Onshape Importer carry over
most Physics parameters and configurations, for the rest of the imported assets adding
physics before proceeding would be necessary. The `NVIDIA Omniverse™ Physics simulation
extension <https://docs.omniverse.nvidia.com/extensions/latest/ext_physics.html#physics-core>`_
is powered by the NVIDIA PhysX SDK. It supports Rigid Body Simulation,
Character Control, Deformable Body Simulation, Particle Simulation, and Articulations. The
important steps for adding Physics to your scene are:

    1. Creating the physics scene
    2. Assigning collision settings
    3. Adding joints and drives.


Creating the Physics Scene
^^^^^^^^^^^^^^^^^^^^^^^^^^^^


The first step is to create a Physics Scene and ensure that the default parameters
for it are acceptable. For example, verify the direction and magnitude of gravity in
the scene. If the imported scene does not contain a ground plane, make sure to add
one before proceeding. It will prevent any physics-enabled objects from falling
below it. Unless you are simulating hundreds of rigid bodies and robots, it is more
efficient to use the CPU solver instead of the GPU solver.
Refer to the :ref:`isaac_sim_app_tutorial_intro_environment_setup` tutorial


Assigning Collision Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


`Collision <https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/rigid_bodies_articulations/rigid_bodies.html#create-a-rigid-body-with-a-collider>`_
enables rigid bodies to interact with each other in an environment. The
geometry of the object can be approximated by convex hull, convex decomposition,
bounding sphere, bounding box, and SDF collision meshes. Each of them
approximates the geometry using different methods and may be better suited for
specific use cases. PhysX supports exact representations for Cube, Capsule, and
Sphere shapes. Cones and Cylinders are supported through the custom geometry
flag and are particularly useful when setting collision approximations for wheels of
robots. `Rigid-body physics materials <https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/rigid_bodies_articulations/rigid_bodies.html#configure-rigid-body-s-material-properties>`_
provide friction, restitution (a.k.a. ‘bounciness’), and material density properties


Adding Joints and Drives
^^^^^^^^^^^^^^^^^^^^^^^^^^


After adding the appropriate collision meshes to prims in the scene, we need to
ensure that they interact correctly with one another. We can do this by defining
appropriate joints between prims connected to each other. Joints give you the
ability to connect physics objects by defining how the objects may move relative to
each other. There are various `joints types <https://docs.omniverse.nvidia.com/kit/docs/omni_physics/latest/dev_guide/rigid_bodies_articulations/joints.html>`_
to select from including revolute, prismatic, spherical, fixed, etc.



Adding Sensors
------------------


|isaac-sim_short| sensor simulation extensions can simulate ground truth perception and
physics-based sensors, and has a library of realistic sensor models. You can simulate
camera, lidar, radar, and physics-based sensors. It is possible to use camera calibration
parameters obtained from OpenCV or ROS by converting them to |isaac-sim_short| units, refer to the :ref:`isaacsim_sensors_camera` page.
RTX Lidar and Radar sensors are simulated at render time on the GPU with RTX hardware. A variety of physics-based sensors
like contact sensors, IMUs sensor, force sensor, effort sensor, and proximity sensor are also included. These sensors can be added
at the appropriate locations in the stage hierarchy (for example, a camera or lidar might be
added near the front/top of the robot). The :ref:`isaac_assets_camera_depth_sensors` and :ref:`isaac_assets_nonvisual_sensors` pages
highlight all the available physical sensor assets available with |isaac-sim_short|


Import and Create Materials
-----------------------------


`Materials <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/materials.html#omniverse-materials>`_ in |isaac-sim_short|
are supported using `NVIDIA Material Definition Language (MDL) <https://www.nvidia.com/en-us/design-visualization/technologies/material-definition-language/>`_ ,
a shading language designed for defining and describing the appearance
of materials in computer graphics. It allows artists and developers to create highly realistic
materials by specifying their physical properties, surface characteristics, and how they
interact with light. Omniverse comes with several template materials, including a physically
based glass; several general purpose multi-lobed materials useful for dielectric and
non-dielectric materials, skin, hair, liquids and other materials requiring subsurface
scattering or transmissive effects; and USD’s UsdPreviewSurface.


.. _isaac_sim_ra_interaction:

Interaction with Digital Twin
===============================

Once the assets have been imported and the scene has been set up, there are various ways
to interact with the simulated environment, which are summarized below.


.. image:: /images/isim_4.5_base_ref_external_arch_interact.png
    :width: 50%
    :alt: Interact with Scene
    :align: center


GUI
-----

The GUI provides intuitive controls for scene management, object manipulation, and
real-time monitoring, providing a streamlined interface for developing and testing robotic
systems. Pre-packaged examples, robots and environments can easily be accessed and
added to the scene via the GUI. Create tools make it easy to assemble, illuminate, simulate,
and render scenes large and small, therefore making it the ideal place to build your virtual
worlds, assemble robots, and examine physics. Refer to the :ref:`isaac_sim_gui_tutorials_page` for
getting started with the GUI tutorials.


Standalone Python
-------------------

|isaac-sim_short| provides a built-in :ref:`isaac_sim_python_environment` that packages can use, like a
system-level Python install. This is the recommended environment for running Python
Scripts with |isaac-sim_short|. All |isaac-sim_short| libraries and dependencies can be imported and
accessed through this Python environment. It also allows users to script and run their
entire worflkow headlessly. For using libraries and tools which are not a part of |isaac-sim_short|,
ensure that they work with Python 3.11 first. A collection of standalone python examples is
provided with Isaac Sim and serves as a good starting point to understand the overall
steps involved. Jupyter notebook and Visual Studio Code support is also available. Workflows from the GUI
can be completely scripted in Python and can be run in headless mode too.


Extensions
------------

Extensions enable developers to add functionality and integrate other tools for |isaac-sim_short|.
They are individually built application modules. All the tools used in |isaac-sim_short| are built as
extensions. Various extensions enable easier interaction with sensors, robots and prims in
the scene. The ROS 2 Bridge extension can be used to connect your ROS packages and
code to |isaac-sim_short|. Developers can write their own extensions in C++, Python or a
combination of both.


OmniGraph
-----------

`OmniGraph <https://docs.omniverse.nvidia.com/extensions/latest/ext_omnigraph.html>`_ is the visual scripting language
for Omniverse. It is not a single type of graph, but a composition of many different graph systems
under a single framework. Many Isaac Sim extensions provide nodes for building graphs for common
use cases. Core, sensor, and ROS extensions are a few examples that contain such OmniGraph Nodes.



.. _isaac_sim_ra_consumption:

Use Cases
=========================================


Synthetic Data Generation (SDG)
---------------------------------

Developers can generate physically accurate synthetic data that can enhance the training
and performance of AI perception networks used for robotics using
`Omniverse Replicator <https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator.html>`_.
Replicator is a collection of extensions, Python APIs, workflows, and tools that enable
synthetic data generation tasks.


Once the scene has been set up, Replicator can be used to modify and randomize various
features like position, rotation, lighting, size, and textures of assets in the scene. A wide
range of annotations are supported including 2D bounding boxes, 3D bounding boxes,
semantic and instance segmentation masks, normals, depth, pointclouds, and more, with
data being written in common formats like COCO and KITTI formats. Custom annotators
and writers can also be implemented for advanced use cases like pose estimation. This
enables developers to seamlessly integrate the generated data with their training pipelines


.. image:: /images/isim_4.5_base_ref_external_arch_sdg.png
    :width: 75%
    :alt: Replicator annotations
    :align: center


To get started, developers can leverage the Python API provided by Omniverse Replicator
for generating synthetic data. The same scripts can be used to generate data headlessly in
the cloud through the Isaac Sim docker container (instructions :ref:`isaac_sim_app_install_container`)
on a developer’s preferred CSP (AWS, Alibaba, Azure, GCP) with the :ref:`isaac_sim_app_install_cloud` guide.
`Replicator YAML <https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator/yaml_workflow.html#replicator-yaml>`_
can be used for low-code situations where scripts can easily be edited by non-technical experts.
They offer a high level of portability and care suitable for cloud use cases.


Software in the Loop (SIL)
-----------------------------


Once the simulation scenario has been set up, developers can tune and test various
aspects of their robotics software stack. The insights gained after varying parameters and
configurations of the software stack and the simulated robot enable an easier and
accurate transition to the physical real-world robot. A few common use cases are
highlighted below:


Single and Multi-Robot Navigation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The navigation stack for a robot can be easily tested in various scenarios. The assets in the
environment can be randomized to come up with these scenarios. For running navigation
with multiple robots, a multi-GPU setup can be leveraged. |isaac-sim_short| supports the ROS 2
Nav2 stack via the ROS 2 Bridge.


AI Model Evaluation
^^^^^^^^^^^^^^^^^^^^

Evaluating models is easy in simulation because of direct access to ground truth which
could be through Physics, the state of a robot, or reading of a sensor. These can then be
compared with the model predictions to obtain the evaluation metrics.


For example, in computer vision tasks, the rendered image from the simulated camera can
be passed through the model for obtaining predictions. This can then be compared with
the ground truth (available directly from simulation or via Replicator) to obtain evaluation
metrics. This can also be done for other sensors like Lidars and can be easily extended to
multimodal applications


Perception
^^^^^^^^^^^^

`Isaac Perceptor <https://developer.nvidia.com/isaac/perceptor>`_ is a reference workflow of
NVIDIA-accelerated libraries and AI models that helps you quickly build robust autonomous
mobile robots (AMRs) to perceive, localize, and operate in unstructured environments like
warehouses or factories. It works with inputs from simulated environments in |isaac-sim_short|


Manipulation
^^^^^^^^^^^^^^

`Isaac Manipulator <https://nvidia-isaac-ros.github.io/reference_workflows/isaac_manipulator/index.html>`_
can be leveraged for manipulation tasks and verified in simulation. It is a
collection of GPU-accelerated packages for perception driven manipulation, providing
capabilities such as object detection and pose estimation. Time optimal collision-free
motion can be generated with cuMotion. Nvblox can be used for local 3D reconstruction
and obstacle detection. MoveIt is also supported via the ROS Bridge in Isaac Sim.


Reinforcement Learning
^^^^^^^^^^^^^^^^^^^^^^^^

:ref:`isaac_lab_tutorials_page` is a united and modular framework for robot learning that aims to simplify
common workflows in robotics research (such as RL, learning from demonstrations, and
motion planning). It is built upon |isaac-sim|.


Hardware in the Loop (HIL)
----------------------------

Hardware in the loop testing and evaluation can be done with Isaac Sim. The target
deployment device will receive all the data from the simulated robot and sensors which can
be fed to the needed software stacks/algorithms. ROS 2 can be leveraged as the
middleware which handles sending and receiving all the data from the simulation computer
to the target device. For example, a simulated camera from |isaac-sim_short| will stream over all
the image data via the ROS 2 bridge from Isaac Sim to an
`NVIDIA Jetson Orin <https://www.nvidia.com/en-us/autonomous-machines/embedded-systems/jetson-orin/>`_, the
embedded device on the robot which will run the computer vision application. This is
particularly useful when selecting the target deployment device to verify it can run the
software stack needed before physically setting up the robot.


CI/CD
--------


OSMO
^^^^^^^

`OSMO <https://developer.nvidia.com/osmo>`_
is a cloud-native workow orchestration platform that lets you easily scale your
workloads across distributed environments — from on-premises to private and public
cloud. You can now apply for early access.


Sizing Calculator
^^^^^^^^^^^^^^^^^^

Please refer to the :ref:`isaac_sim_benchmarks` page for Isaac Sim performance benchmarks
across multiple consumer and enterprise hardware configurations.


Further Reading
=================

Follow the relevant tutorials for a deeper dive into a corresponding section.