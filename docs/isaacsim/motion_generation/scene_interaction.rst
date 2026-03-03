Scene Interaction
=================

The Motion Generation API provides tools for interacting with the USD scene to support motion planning. 
These tools separate motion generation collision modeling from simulation collision modeling, giving you flexibility in how you represent the world.

All code examples in this section are drawn from a single, complete, runnable example file:

.. code-block:: bash

    # Scene interaction with SceneQuery, WorldInterface, ObstacleStrategy, and WorldBinding
    ./python.sh standalone_examples/api/isaacsim.robot_motion.experimental.motion_generation/scene_interaction_example.py


SceneQuery: Finding Objects
----------------------------

:class:`SceneQuery` lets you search the USD scene for objects matching specific criteria. 
It's useful for finding obstacles, robots, or other objects in your scene.

The most common use is finding collision objects in a region:

.. literalinclude:: ../snippets/motion_generation/scene_interaction/scene_interaction_example.py
   :start-after: <start-scene-query-snippet>
   :end-before: <end-scene-query-snippet>
   :language: python


:class:`SceneQuery` uses :class:`TrackableApi` to filter which USD APIs to search for. Currently supported APIs include:

* ``PHYSICS_COLLISION`` - Objects with collision geometry
* ``PHYSICS_RIGID_BODY`` - Rigid body objects

You can also include or exclude specific prim paths and their children, making it easy to filter out the robot itself or focus on specific regions.

ObstacleStrategy: Representation Management
--------------------------------------------

:class:`ObstacleStrategy` manages how USD scene objects are represented when passed to your planning library. 
It configures :class:`ObstacleConfiguration` objects, which define both the representation type and safety tolerance for each obstacle.

ObstacleConfiguration Structure
###############################
An :class:`ObstacleConfiguration` is a structure containing two components:

* **Representation** - How the obstacle is represented in your planning library (e.g., sphere, mesh, oriented bounding box)
* **Safety tolerance** - A padding distance applied around the obstacle for collision avoidance

Valid Representations per USD Type
##################################

Each USD shape type (Sphere, Cube, Mesh, etc.) has its own set of valid representations it can use:

* **Sphere** - Can be represented as ``SPHERE`` or ``OBB``
* **Cube** - Can be represented as ``CUBE`` or ``OBB``
* **Mesh** - Can be represented as ``MESH``, ``TRIANGULATED_MESH``, or ``OBB``
* **Cone, Capsule, Cylinder** - Can be represented as their native shape or ``OBB``
* **Plane** - Can only be represented as ``PLANE``

.. note::
   Since :class:`ObstacleRepresentation` is a :class:`StrEnum`, you can use either the enum value (e.g., ``ObstacleRepresentation.OBB``) or the string directly (e.g., ``"obb"``) when creating :class:`ObstacleConfiguration` objects.

.. note::
   Additional representation types will be added in future versions of the API.

ObstacleStrategy Management
###########################

:class:`ObstacleStrategy` uses a three-tier priority system to determine the configuration for each obstacle. By default, each shape type is represented by its native representation with zero safety tolerance (e.g., a Mesh object maps to ``MESH`` representation with 0.0 safety tolerance).

**Default Configurations and Global Safety Tolerance**

The built-in defaults map each shape type to its native representation. You can adjust the safety tolerance for all these default mappings using :meth:`ObstacleStrategy.set_default_safety_tolerance`. This convenience method affects only the default configurations and does not modify shape-level overrides or prim-level overrides.

**Shape-Level Overrides**

:meth:`ObstacleStrategy.set_default_configuration` allows you to set a configuration override for an entire shape type (e.g., all Mesh objects). These shape-level overrides take precedence over the default configurations and any global safety tolerance setting. For example, you can configure all Mesh objects to use ``OBB`` representation with a specific safety tolerance, regardless of the default settings.

**Prim-Level Overrides**

:meth:`ObstacleStrategy.set_configuration_overrides` sets configuration overrides for specific prim paths. These prim-level overrides have the highest priority and take precedence over both default configurations and shape-level overrides. This allows you to customize individual obstacles (e.g., a specific Mesh prim uses ``TRIANGULATED_MESH`` representation) while maintaining shape-level defaults for other objects of the same type.

When querying the configuration for a specific obstacle, :class:`ObstacleStrategy` checks these tiers in priority order: prim-level overrides first, then shape-level overrides, and finally default configurations.

Here's how to configure an :class:`ObstacleStrategy`:

.. literalinclude:: ../snippets/motion_generation/scene_interaction/scene_interaction_example.py
   :start-after: <start-obstacle-strategy-snippet>
   :end-before: <end-obstacle-strategy-snippet>
   :language: python

WorldInterface: Connecting to Motion Planning Libraries
--------------------------------------------------------

:class:`WorldInterface` is an abstract interface that acts as a bridge between obstacle data and your 
motion planning library. 

Different motion planning libraries have their own world representations.
The :class:`WorldInterface` lets you translate obstacle data (positions, orientations, shapes, etc.) into whatever format your 
planning library expects.

You implement :class:`WorldInterface` by creating a class that:

* Takes obstacle data as warp arrays and data structures (not USD objects directly)
* Implements methods for adding obstacles (spheres, boxes, meshes, etc.) to your planning library
* Implements methods for updating obstacle transforms and properties

Think of :class:`WorldInterface` as an adapter: it receives obstacle data as warp arrays and converts it into the format your specific motion planning library needs. 
The simplest way to get obstacle data is via :class:`WorldBinding`, which handles USD scene extraction and outputs warp arrays. 
Because both :class:`WorldBinding` outputs and :class:`WorldInterface` inputs are warp arrays, the system is modular; you can insert intermediate processing steps between them, 
such as perception algorithms, noise injection, filtering, or any other data transformation you need.

Here are examples of the three main types of methods you'll implement:

**Adding obstacles** - Initialize objects in your planning world:

.. literalinclude:: ../snippets/motion_generation/scene_interaction/scene_interaction_example.py
   :start-after: <start-add-spheres-snippet>
   :end-before: <end-add-spheres-snippet>
   :language: python

**Updating transforms** - Used frequently for real-time updates, or just before creating a trajectory plan:

.. literalinclude:: ../snippets/motion_generation/scene_interaction/scene_interaction_example.py
   :start-after: <start-update-transforms-snippet>
   :end-before: <end-update-transforms-snippet>
   :language: python

**Updating properties** - Called when shape properties change:

.. literalinclude:: ../snippets/motion_generation/scene_interaction/scene_interaction_example.py
   :start-after: <start-update-sphere-properties-snippet>
   :end-before: <end-update-sphere-properties-snippet>
   :language: python

WorldBinding: Synchronizing the Planning Library
-------------------------------------------------

:class:`WorldBinding` is a convenience class that automatically:

1. Tracks specified prims in the USD scene
2. Uses :class:`ObstacleStrategy` to determine how they should be represented
3. Extracts obstacle data (positions, orientations, shapes, etc.) from USD
4. Calls your :class:`WorldInterface` implementation with this data to add/update obstacles in your planning library world representation

This keeps your planning library's world representation in sync with the simulation scene. The :class:`WorldBinding` handles all the USD interaction - your :class:`WorldInterface` only needs to work with the extracted data.

Here's how to use :class:`WorldBinding` with your :class:`WorldInterface` implementation:

.. literalinclude:: ../snippets/motion_generation/scene_interaction/scene_interaction_example.py
   :start-after: <start-world-binding-snippet>
   :end-before: <end-world-binding-snippet>
   :language: python


The :class:`WorldBinding` uses USDRT change tracking for efficient updates - it only updates objects properties that have actually changed.

.. note::
   **Scene Validation During Initialization**
   
   When you call :meth:`WorldBinding.initialize()`, the binding automatically performs scene validation 
   on all tracked prims. For each tracked prim, it searches all parent prims in the hierarchy to ensure:
   
   * No parent prims have local scaling other than [1,1,1] (identity scaling)
   * No parent prims have point scaling (``xformOp:scale:unitsResolve``) other than [1,1,1] (unity scaling)
   
   This validation prevents unexpected shearing of reference frames that can occur when non-identity 
   scaling is applied to ancestor prims. If any invalid ancestors are found, initialization will raise 
   an :class:`AssertionError` with details about which prims have invalid scaling.
   
   In general, you should avoid putting non-uniform scaling (or any scaling other than [1,1,1]) on any 
   prim that has child prims. This restriction may be loosened in the future, but for now it ensures 
   that local scales match world scales, which is required for correct world-space operations.

Synchronization Methods
########################

:class:`WorldBinding` provides three methods for synchronizing the planning library with the USD scene:

* :meth:`WorldBinding.synchronize_transforms` - Very fast, updates all tracked obstacle poses (positions and orientations). 
  Use this when only transforms change, such as when rigid body obstacles are moving. This is the most efficient 
  synchronization method.

* :meth:`WorldBinding.synchronize_properties` - Can be slow, updates shape properties (collision enables, shape-specific 
  attributes) using USDRT change tracking. Only objects with property changes are updated. Use this when 
  obstacle properties (like collision enable state or shape attributes) may have changed. This method will return
  very quickly if no properties have changed.

* :meth:`WorldBinding.synchronize` - Convenience method that calls both :meth:`WorldBinding.synchronize_transforms` and :meth:`WorldBinding.synchronize_properties`. 
  Use this when you need full synchronization and don't need to optimize for performance.

In your simulation loop, you typically want to call :meth:`synchronize_transforms` every frame (or frequently) for moving 
obstacles, and :meth:`synchronize_properties` less frequently (or only when you know properties have changed).

How It All Fits Together
-------------------------

The scene interaction components work in two separate workflows:

**Configuration Workflow** - Finding and configuring obstacle representations:

.. figure:: images/isim_6.0_full_tut_external_scene_interaction_configuration_workflow.svg
   :alt: Configuration workflow for scene interaction
   :align: center
   :width: 100%

   SceneQuery discovers objects in the USD scene, ObstacleStrategy configures how they should 
   be represented, and WorldBinding initializes the planning library's world model.

**Data Flow** - Extracting and translating obstacle data:

.. figure:: images/isim_6.0_full_tut_external_scene_interaction_data_flow.svg
   :alt: Data flow from USD to planning library
   :align: center
   :width: 90%

   WorldBinding extracts updated transforms and properties from USD, updating the WorldInterface.

Complete Workflow
-----------------

Here's the complete example showing how all the pieces fit together. Note that the scene setup function creates a simple example scene, but emphasizes that the scene could come from anywhere:

.. literalinclude:: ../snippets/motion_generation/scene_interaction/scene_interaction_example.py
   :start-after: <start-setup-scene-snippet>
   :end-before: <end-setup-scene-snippet>
   :language: python


The main function demonstrates the complete workflow, including the use of different synchronize methods:

.. literalinclude:: ../snippets/motion_generation/scene_interaction/scene_interaction_example.py
   :start-after: <start-main-snippet>
   :end-before: <end-main-snippet>
   :language: python

Running the Example
-------------------

When you run the standalone example, you should see a group of objects falling in the simulation. The example demonstrates how :class:`WorldBinding` synchronizes obstacle data from the USD scene to your planning library as the objects move.

.. figure:: images/isim_6.0_full_tut_viewport_falling_objects_capture.webp
   :align: center
   :width: 100%

   Objects falling under gravity.

You should see output in the terminal showing the synchronization updates. As expected, the synchronizations show ``/World/Mesh1`` (the thin box) free falling, and then rotating as it hits the ground.

.. code-block:: text

  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.500, 0.484]
    Orientation (quat wxyz): [0.924, 0.383, 0.000, 0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.500, 0.473]
    Orientation (quat wxyz): [0.924, 0.383, 0.000, 0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.500, 0.459]
    Orientation (quat wxyz): [0.924, 0.383, 0.000, 0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.500, 0.443]
    Orientation (quat wxyz): [0.924, 0.383, 0.000, 0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.500, 0.424]
    Orientation (quat wxyz): [0.924, 0.383, 0.000, 0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.500, 0.402]
    Orientation (quat wxyz): [0.924, 0.383, 0.000, 0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.500, 0.377]
    Orientation (quat wxyz): [0.924, 0.383, 0.000, 0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.500, 0.350]
    Orientation (quat wxyz): [0.924, 0.383, 0.000, 0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.500, 0.320]
    Orientation (quat wxyz): [0.924, 0.383, 0.000, 0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.500, 0.287]
    Orientation (quat wxyz): [0.924, 0.383, 0.000, 0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.500, 0.252]
    Orientation (quat wxyz): [0.924, 0.383, 0.000, 0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.500, 0.214]
    Orientation (quat wxyz): [0.924, 0.383, 0.000, 0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.486, 0.203]
    Orientation (quat wxyz): [0.936, 0.353, 0.000, -0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.472, 0.192]
    Orientation (quat wxyz): [0.948, 0.320, -0.000, -0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.458, 0.178]
    Orientation (quat wxyz): [0.959, 0.284, -0.000, -0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.443, 0.163]
    Orientation (quat wxyz): [0.970, 0.245, -0.000, -0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.429, 0.146]
    Orientation (quat wxyz): [0.979, 0.203, -0.000, -0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.415, 0.126]
    Orientation (quat wxyz): [0.988, 0.158, -0.000, -0.000]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.401, 0.104]
    Orientation (quat wxyz): [0.994, 0.109, -0.000, -0.001]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.387, 0.079]
    Orientation (quat wxyz): [0.998, 0.058, -0.000, -0.001]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.374, 0.053]
    Orientation (quat wxyz): [1.000, 0.004, -0.000, -0.001]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.373, 0.050]
    Orientation (quat wxyz): [1.000, -0.000, -0.000, -0.001]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.373, 0.050]
    Orientation (quat wxyz): [1.000, 0.000, -0.000, -0.001]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.373, 0.050]
    Orientation (quat wxyz): [1.000, -0.000, 0.000, -0.001]
  WorldBinding update - /World/Mesh1:
    Position: [-1.500, -1.373, 0.050]
    Orientation (quat wxyz): [1.000, 0.000, 0.000, -0.001]


Summary
-------

The scene interaction components work together in this order:

1. :class:`SceneQuery` - Searches the USD scene for objects matching specific criteria (e.g., collision objects, robots)
2. :class:`ObstacleStrategy` - Configures how USD objects are represented when passed to your planning library (representation type and safety tolerance)
3. :class:`WorldInterface` - Defines the interface you implement to translate obstacle data (as warp arrays) into your planning library's format
4. :class:`WorldBinding` - Extracts obstacle data from USD, applies :class:`ObstacleStrategy` configurations, and calls your :class:`WorldInterface` implementation to keep your planning library synchronized

This separation of concerns means you can:
* Use different collision representations for planning vs simulation
* Update your planning library's world efficiently
* Customize obstacle representations per object
* Integrate with any motion planning library by implementing :class:`WorldInterface`
* Work with pure data structures - :class:`WorldInterface` doesn't require direct USD interaction

Next Steps
----------

* Building custom controllers for specific needs
* Composing controllers for complex behaviors

For detailed API reference, see the individual class documentation.
