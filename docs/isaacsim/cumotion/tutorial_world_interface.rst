.. _isaac_sim_cumotion_tutorial_world_interface:

==================================
cuMotion World Interface Tutorial
==================================

This tutorial demonstrates how to use the :class:`CumotionWorldInterface` class in the |cumotion| integration to manage world state, obstacles, and robot base transforms for motion planning and control.

By the end of this tutorial, you'll understand:

* How to set up a :class:`CumotionWorldInterface`
* How to discover obstacles using :class:`SceneQuery`
* How to configure obstacle representations and safety tolerances
* How to synchronize world state with different update styles

**Prerequisites**

- Review the :doc:`Scene Interaction <../motion_generation/scene_interaction>` tutorial to understand :class:`SceneQuery`, :class:`WorldBinding`, :class:`ObstacleStrategy`, and the :class:`WorldInterface` interface.
- Know how to add collider presets to objects in Isaac Sim. You can add a collider preset by selecting an object in the stage tree, going to the **Property** tab, clicking the ``+ Add`` button, and selecting **Physics > Colliders Preset** (or **Physics > Rigid Body with Colliders Preset** for dynamic objects).

To follow along with the tutorial, run your |isaac-sim_short| instance. Then open **Window > Extensions**, search for **cuMotion Examples** (``isaacsim.robot_motion.cumotion.examples``), and enable it. If you cannot find it, remove ``@feature`` from the Extensions search bar and search again.
Within the ``isaacsim.robot_motion.cumotion.examples`` extension, there is a fully functional example of the :class:`CumotionWorldInterface` being used to manage world state,
discover obstacles, and synchronize world updates.

Key Concepts
============

The :class:`CumotionWorldInterface` is the bridge between Isaac Sim's USD scene and |cumotion|'s collision world. It works together with the Motion Generation API classes to provide a complete world state management:

* **WorldInterface Implementation**: :class:`CumotionWorldInterface` implements the :class:`WorldInterface` interface from the :doc:`Motion Generation API <../motion_generation/index>`, enabling use with :class:`WorldBinding` and other Motion Generation API components
* **cuMotion World Management**: Manages obstacles in |cumotion|'s internal world representation, providing a :attr:`world_view` for collision queries
* **Debug Visualization**: Optional visualization of collision geometries for debugging

The :class:`CumotionWorldInterface` works with :doc:`Motion Generation API <../motion_generation/index>` classes:
* :class:`SceneQuery` discovers objects in the USD scene
* :class:`ObstacleStrategy` configures how obstacle geometries are approximated
* :class:`WorldBinding` automatically synchronizes world state from USD to |cumotion| using the world interface

Searching for Obstacles
========================

The first step is to create a :class:`SceneQuery` and use it to discover objects in the USD scene:

.. literalinclude:: ../snippets/cumotion/world_interface_example.py
   :start-after: <start-search-obstacles-snippet>
   :end-before: <end-search-obstacles-snippet>
   :language: python

The ``SceneQuery`` searches for prims in the specified axis-aligned bounding box that have the specified collision API applied.

Configuring Obstacle Representations
=====================================

Obstacle geometries need to be approximated for collision checking. The :class:`ObstacleStrategy` manages how different geometry types are represented:

* In the case of |cumotion|, there are not natively supported obstacle types for the shapes ``Cone`` or ``Cylinder``, so we use the ``OBB`` representation for both, which :class:`CumotionWorldInterface` maps to the native ``cumotion.CUBOID`` type.
* For ``Mesh`` objects, we use the ``OBB`` representation for faster collision checking, but you can also use the ``TRIANGULATED_MESH`` representation for more accurate collision checking.
* The safety tolerance adds extra padding around obstacles to ensure safe clearance during planning.

.. note::
   Since :class:`ObstacleRepresentation` is a :class:`StrEnum`, you can use either the enum value (e.g., ``ObstacleRepresentation.OBB``) or the string directly (e.g., ``"obb"``) when creating :class:`ObstacleConfiguration` objects.
   See :doc:`Scene Interaction <../motion_generation/scene_interaction>` for details on how to configure obstacle representations.


.. literalinclude:: ../snippets/cumotion/world_interface_example.py
   :start-after: <start-configure-obstacle-strategy-snippet>
   :end-before: <end-configure-obstacle-strategy-snippet>
   :language: python


Creating the World Interface and World Binding
==============================================

The :class:`WorldBinding` can be used to connect a :class:`CumotionWorldInterface` with the USD scene. For the case of this tutorial,
we use the setting ``visualize_debug_prims=True``, which will:

* Create debug visualizations of the obstacles existing in the :class:`cumotion.World`
* Those objects will be colored in red to indicate that they are enabled for collision checking (no-go region).
* Those objects will be colored in green to indicate that they are disabled for collision checking (go region).

.. literalinclude:: ../snippets/cumotion/world_interface_example.py
   :start-after: <start-create-world-binding-snippet>
   :end-before: <end-create-world-binding-snippet>
   :language: python

The ``WorldBinding`` automatically extracts collision geometry from the tracked prims, and passes the 
appropriate data based on the obstacle strategy to the :class:`CumotionWorldInterface` to be 
converted to |cumotion| obstacle representations. Note that the :class:`CumotionWorldInterface`
can also be used without (or partially without) a :class:`WorldBinding`. For example, you may:

* Use :class:`WorldBinding` to initially populate the scene, then manually call :meth:`CumotionWorldInterface.update_obstacle_transforms` when transforms come from perception algorithms rather than the USD scene.
* Directly populate :class:`CumotionWorldInterface` using Isaac Sim Core API objects (``Sphere``, ``Cube``) for simple scenes.

Synchronizing the World Binding
================================

The world binding must be synchronized each frame to track moving obstacles and property changes. There are three synchronization methods,
as covered in the :doc:`Scene Interaction <../motion_generation/scene_interaction>` tutorial.

**Synchronize Transforms Only**
Updates only the transforms (positions and orientations) of obstacles:

.. literalinclude:: ../snippets/cumotion/world_interface_example.py
   :start-after: <start-synchronize-transforms-snippet>
   :end-before: <end-synchronize-transforms-snippet>
   :language: python

**Synchronize Properties Only**
Updates only the properties (sizes, shapes) of obstacles:

.. note::
    |cumotion| does not support updating the properties of obstacles. Therefore, all functions of the :class:`WorldInterface` to update shape properties
    are left unimplemented, and will raise a :class:`NotImplementedError` if called. The only property which supports updating in |cumotion| is the collision enabled state.

.. literalinclude:: ../snippets/cumotion/world_interface_example.py
   :start-after: <start-synchronize-properties-snippet>
   :end-before: <end-synchronize-properties-snippet>
   :language: python

**Synchronize Both**
Updates both transforms and properties:

.. literalinclude:: ../snippets/cumotion/world_interface_example.py
   :start-after: <start-synchronize-both-snippet>
   :end-before: <end-synchronize-both-snippet>
   :language: python

In a typical update loop, you would call the :meth:`WorldBinding.synchronize_transforms` method every frame,
and the :meth:`WorldBinding.synchronize_properties` method less frequently (or only when you know properties have changed).

.. note::
   The synchronization methods described above are only used for collision objects that you are tracking. 
   The robot base position is not automatically synchronized, and robot base pose is not generally part of the 
   :class:`WorldInterface` interface. The :class:`CumotionWorldInterface` provides an additional function to 
   update the robot base pose, which is covered in the section that follows.

Updating Robot Base Transforms
================================

The world interface needs to know the robot base transform to convert between world coordinates and robot base frame coordinates:

.. literalinclude:: ../snippets/cumotion/world_interface_example.py
   :start-after: <start-update-robot-base-transforms-snippet>
   :end-before: <end-update-robot-base-transforms-snippet>
   :language: python

This should be called whenever the robot base moves, and will update the transforms of all obstacles in the :class:`cumotion.World` to be relative to the robot base frame.

Exploring the Tutorial
=======================

.. note::
   To experiment with this tutorial interactively, see the ``scenario.py`` file in the ``isaacsim.robot_motion.cumotion.examples`` extension at ``isaacsim/robot_motion/cumotion/examples/world_interface/scenario.py``.

This tutorial provides an interactive environment for experimenting with the :class:`CumotionWorldInterface`. Here are some ways to explore the tutorial
and learn about the :class:`CumotionWorldInterface`:

**Basic usage**: move a single obstacle around the scene and see how the world interface tracks it.

In the example video below, we simply:

* Run the example
* Move around the cube obstacle (Shift + drag)
* When the synchronization is set to ``synchronize_transforms``, the USD object moves, and the internal cuMotion obstacle transform is internally updated, represented as a red OBB.
* When the synchronization is set to ``synchronize_properties``, the USD object moves, but the internal cuMotion obstacle transform is not internally updated.
* When the synchronization is set to ``synchronize``, the USD object moves, and the internal cuMotion obstacle transform is internally updated.

.. figure:: images/world_interface/isim_6.0_full_tut_viewport_moving_single_obstacle.webp
   :align: center
   :width: 100%

   Moving a single obstacle around the scene.

**Adding obstacles**

In the example video below, we:

* Create a Sphere
* Add collider Rigid Body with Colliders preset to the Sphere (so it is a physics collision and a dynamic object)
* Reset the example (which re-generates the :class:`CumotionWorldInterface` and its managed :class:`cumotion.World`)
* The Sphere is automatically found by the :class:`SceneQuery` and added to the `cumotion.World` through the :class:`WorldBinding` and :class:`CumotionWorldInterface`.

.. figure:: images/world_interface/isim_6.0_full_tut_viewport_adding_ball_obstacle.webp
   :align: center
   :width: 100%

   Adding a ball obstacle to the scene.

**Enabling and disabling obstacles**

In the example video below, we:

* Create a Capsule
* Add the collider preset to the Capsule (so it is a static physics collision object)
* Reset the example (which re-generates the :class:`CumotionWorldInterface` and its managed :class:`cumotion.World`)
* The Capsule is automatically found by the :class:`SceneQuery` and added to the `cumotion.World` through the :class:`WorldBinding` and :class:`CumotionWorldInterface`.
* When we enable/disable collisions, we see the internal cuMotion obstacle transform is updated to reflect the enabled/disabled state (unless we are using the ``synchronize_transforms`` synchronization method).

.. figure:: images/world_interface/isim_6.0_full_tut_viewport_enable_disable_capsule.webp
   :align: center
   :width: 100%

   Enabling and disabling a capsule obstacle.

**Changing obstacle representations**

To learn further, try changing some settings in the :class:`ObstacleStrategy` and see how the :class:`CumotionWorldInterface` and :class:`cumotion.World` react.
For example, we can add a ``Mesh`` obstacle and represent it as ``TRIANGULATED_MESH`` instead of ``OBB`` to see the difference in collision accuracy. For example,
the following two videos show an examples of meshes being added when the default representations in the :class:`ObstacleStrategy` are set to ``OBB`` and ``TRIANGULATED_MESH`` respectively.

.. figure:: images/world_interface/isim_6.0_full_tut_viewport_mesh_representation_obb.webp
   :align: center
   :width: 100%

   Representing a mesh as ``OBB``

.. figure:: images/world_interface/isim_6.0_full_tut_viewport_mesh_representation_triangulated_mesh.webp
   :align: center
   :width: 100%

   Representing a mesh as ``TRIANGULATED_MESH``

Summary
=======

This tutorial demonstrated:

1. **World Interface Setup**: Creating a :class:`CumotionWorldInterface` (often using :class:`WorldBinding` for centralized world state management)
2. **Obstacle Discovery**: Using :class:`SceneQuery` to discover objects in the USD scene
3. **Obstacle Configuration**: Configuring obstacle representations and safety tolerances with :class:`ObstacleStrategy`
4. **World Synchronization**: Using different update styles (transforms, properties, or both) to keep world state current
5. **Debug Visualizations**: Enabling visualizations to understand obstacle representations

The |cumotion| world interface provides a centralized, efficient way to manage world state for all motion planning and control algorithms.

Next Steps
----------

* :ref:`RMPflow tutorial <isaac_sim_cumotion_tutorial_rmpflow>` - Using the world interface with reactive control
* :ref:`Graph Planner tutorial <isaac_sim_cumotion_tutorial_graph_planner>` - Collision-free path planning with obstacles
* :ref:`Trajectory Generator tutorial <isaac_sim_cumotion_tutorial_trajectory_generator>` - Smooth path execution (collision-unaware)
* :ref:`Trajectory Optimizer tutorial <isaac_sim_cumotion_tutorial_trajectory_optimizer>` - Optimization-based planning with world awareness
