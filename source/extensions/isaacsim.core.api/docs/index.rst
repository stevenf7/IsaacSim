.. _API isaacsim.core.api:


Core [isaacsim.core.api]
######################################################

|

Articulations
--------------

Articulation
=============

.. autoclass:: isaacsim.core.api.articulations.Articulation
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

ArticulationView
=================

.. autoclass:: isaacsim.core.api.articulations.ArticulationView
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

ArticulationController
========================

.. autoclass:: isaacsim.core.api.controllers.ArticulationController
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

Loggers
--------------

DataLogger
========================

.. autoclass:: isaacsim.core.api.loggers.DataLogger
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

Materials
--------------

Visual Material
========================

.. autoclass:: isaacsim.core.api.materials.VisualMaterial
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:


Preview Surface
========================

.. autoclass:: isaacsim.core.api.materials.PreviewSurface
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

OmniPBR Material
========================

.. autoclass:: isaacsim.core.api.materials.OmniPBR
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

Omni Glass Material
========================

.. autoclass:: isaacsim.core.api.materials.OmniGlass
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

Physics Material
========================

.. autoclass:: isaacsim.core.api.materials.PhysicsMaterial
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:


Particle Material
========================

.. autoclass:: isaacsim.core.api.materials.ParticleMaterial
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

Particle Material View
========================

.. autoclass:: isaacsim.core.api.materials.ParticleMaterialView
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

Deformable Material
=========================

.. autoclass:: isaacsim.core.api.materials.DeformableMaterial
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

Deformable Material View
=========================

.. autoclass:: isaacsim.core.api.materials.DeformableMaterialView
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Objects
--------------

Modules to create/encapsulate visual, fixed, and dynamic shapes (Capsule, Cone, Cuboid, Cylinder, Sphere) as well as ground planes

.. list-table::
    :header-rows: 1

    * - Type
      - Classes
      - Collider API
      - Rigid Body API
    * - Visual
      - :py:class:`isaacsim.core.api.objects.VisualCapsule`
        |br| :py:class:`isaacsim.core.api.objects.VisualCone`
        |br| :py:class:`isaacsim.core.api.objects.VisualCuboid`
        |br| :py:class:`isaacsim.core.api.objects.VisualCylinder`
        |br| :py:class:`isaacsim.core.api.objects.VisualSphere`
      - No
      - No
    * - Fixed
      - :py:class:`isaacsim.core.api.objects.FixedCapsule`
        |br| :py:class:`isaacsim.core.api.objects.FixedCone`
        |br| :py:class:`isaacsim.core.api.objects.FixedCuboid`
        |br| :py:class:`isaacsim.core.api.objects.FixedCylinder`
        |br| :py:class:`isaacsim.core.api.objects.FixedSphere`
        |br|
        |br| :py:class:`isaacsim.core.api.objects.GroundPlane`
      - Yes
      - No
    * - Dynamic
      - :py:class:`isaacsim.core.api.objects.DynamicCapsule`
        |br| :py:class:`isaacsim.core.api.objects.DynamicCone`
        |br| :py:class:`isaacsim.core.api.objects.DynamicCuboid`
        |br| :py:class:`isaacsim.core.api.objects.DynamicCylinder`
        |br| :py:class:`isaacsim.core.api.objects.DynamicSphere`
      - Yes
      - Yes

|

Ground Plane
=============

.. autoclass:: isaacsim.core.api.objects.GroundPlane
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Visual Capsule
==============

.. autoclass:: isaacsim.core.api.objects.VisualCapsule
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Visual Cone
============

.. autoclass:: isaacsim.core.api.objects.VisualCone
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Visual Cuboid
==============

.. autoclass:: isaacsim.core.api.objects.VisualCuboid
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Visual Cylinder
==================

.. autoclass:: isaacsim.core.api.objects.VisualCylinder
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Visual Sphere
===============

.. autoclass:: isaacsim.core.api.objects.VisualSphere
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Fixed Capsule
==============

.. autoclass:: isaacsim.core.api.objects.FixedCapsule
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Fixed Cone
==========

.. autoclass:: isaacsim.core.api.objects.FixedCone
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Fixed Cuboid
=============

.. autoclass:: isaacsim.core.api.objects.FixedCuboid
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Fixed Cylinder
==================

.. autoclass:: isaacsim.core.api.objects.FixedCylinder
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Fixed Sphere
===============

.. autoclass:: isaacsim.core.api.objects.FixedSphere
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Dynamic Capsule
================

.. autoclass:: isaacsim.core.api.objects.DynamicCapsule
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Dynamic Cone
============

.. autoclass:: isaacsim.core.api.objects.DynamicCone
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Dynamic Cuboid
===============

.. autoclass:: isaacsim.core.api.objects.DynamicCuboid
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Dynamic Cylinder
==================

.. autoclass:: isaacsim.core.api.objects.DynamicCylinder
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Dynamic Sphere
================

.. autoclass:: isaacsim.core.api.objects.DynamicSphere
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Physics Context
----------------

.. automodule:: isaacsim.core.api.physics_context
    :inherited-members:
    :imported-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Prims
--------------

Base Sensor
================

.. autoclass:: isaacsim.core.api.prims.BaseSensor
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

XForm Prim
================

.. autoclass:: isaacsim.core.api.prims.XFormPrim
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

XForm Prim View
===================

.. autoclass:: isaacsim.core.api.prims.XFormPrimView
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Geometry Prim
================

.. autoclass:: isaacsim.core.api.prims.GeometryPrim
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Geometry Prim View
===================

.. autoclass:: isaacsim.core.api.prims.GeometryPrimView
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Rigid Prim
===================

.. autoclass:: isaacsim.core.api.prims.RigidPrim
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Rigid Prim View
===================

.. autoclass:: isaacsim.core.api.prims.RigidPrimView
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Rigid Contact View
===================

.. autoclass:: isaacsim.core.api.prims.RigidContactView
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

Cloth Prim
===================

.. autoclass:: isaacsim.core.api.prims.ClothPrim
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

Cloth Prim View
===================
.. autoclass:: isaacsim.core.api.prims.ClothPrimView
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

Particle System
===================
.. autoclass:: isaacsim.core.api.prims.ParticleSystem
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

Particle System View
=====================
.. autoclass:: isaacsim.core.api.prims.ParticleSystemView
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:


Robots
--------------

Robot
===================
.. autoclass:: isaacsim.core.api.robots.Robot
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Robot View
=====================
.. autoclass:: isaacsim.core.api.robots.RobotView
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Scenes
--------------

Scene
=====================
.. autoclass:: isaacsim.core.api.scenes.Scene
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

SceneRegistry
=====================
.. autoclass:: isaacsim.core.api.scenes.SceneRegistry
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

|

Simulation Context
-------------------

.. automodule:: isaacsim.core.api.simulation_context
    :inherited-members:
    :imported-members:
    :members:
    :undoc-members:
    :exclude-members:

|

World
--------------

.. automodule:: isaacsim.core.api.world
    :inherited-members:
    :imported-members:
    :members:
    :undoc-members:
    :exclude-members:

Tasks
--------------

Base Task
=====================
.. autoclass:: isaacsim.core.api.tasks.BaseTask
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

Follow Target
=====================
.. autoclass:: isaacsim.core.api.tasks.FollowTarget
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:

Pick and Place
=====================
.. autoclass:: isaacsim.core.api.tasks.PickPlace
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:


Stacking
=====================
.. autoclass:: isaacsim.core.api.tasks.Stacking
    :inherited-members:
    :members:
    :undoc-members:
    :exclude-members:
