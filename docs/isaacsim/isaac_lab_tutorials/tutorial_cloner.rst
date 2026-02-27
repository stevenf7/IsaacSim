..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaac_sim_app_tutorial_cloner:

===============================
Getting Started with Cloner
===============================

Training reinforcement learning policies can often benefit from collecting trajectories from vectorized copies of environments performing the same task. The Cloner interface is designed to simplify the environment design process for such a scene by providing APIs that allow users to clone a given environment as many times as desired.

In addition to providing cloning functionality, the Cloner interface also provides utilities to generate target paths, automatically compute target transforms, as well as filtering out collisions between clones.


Learning Objectives
===================

In this tutorial, we will walk through the Cloner interface:

1. Set up an example using the Cloner class
2. Set up an example using the GridCloner class
3. Use APIs from `isaacsim.core.api` to access cloned objects
4. Understand advanced cloning with physics replication and additional parameters

*10-15 Minute Tutorial*

Getting Started
===============

We will first launch Isaac Sim and enable the Cloner extension. Open the Extensions window from the UI by navigating to Window > Extensions from the top menu bar. Find the `Isaac Sim Cloner` extension, or `isaacsim.core.cloner` and enable the extension via the toggle switch on the right side of the extension name.

Next, open the Script Editor window from the UI by navigating to Window > Script Editor from the top menu bar. All example code in this tutorial can be pasted into the Script Editor window and executed by clicking on Run.

Introduction to Cloner
======================

Please make sure `isaacsim.core.cloner` is enabled from the Extensions window before running the snippets.

Let's first start with a simple use case of the Cloner interface. In this example, we will create a scene with 4 cubes.

.. literalinclude:: ../snippets/isaac_lab_tutorials/tutorial_cloner/introduction_to_cloner.py
    :language: python

We should now have 4 cubes in our stage: "/World/Cube_0", "/World/Cube_1", "/World/Cube_2", "/World/Cube_3". But you may have noticed that the cubes have all been created at the same position.

We can add a transform to each cube, simply replace the last line of the previous code with the following:

.. literalinclude:: ../snippets/isaac_lab_tutorials/tutorial_cloner/clone_the_cube_at_target_paths.py
    :language: python

It is also possible to specify the orientations of each clone by passing in an orientations argument, which should also be a `np.ndarray`.

Grid Cloner
===========

Grid Cloner is a specialized Cloner class that automatically places clones in a grid, without requiring pre-computed translations and orientations from the user.

To use the Grid Cloner, we will need to specify the spacing we would like between each clone at initialization.

.. literalinclude:: ../snippets/isaac_lab_tutorials/tutorial_cloner/grid_cloner.py
    :language: python

Now we have a scene with 4 cubes placed in a grid!

Accessing Cloned Objects
========================

Now that we have created our scene with the Cloner interface, we can access states for the cloned objects using APIs from `isaacsim.core.api`. These APIs allow us to collect and apply data as vectorized tensors to all or a subset of objects at once, avoiding iterating through objects in loops.

We will show a simple example of retrieving the global transforms of all of the boxes in the scene, as well as setting a new translation on the boxes.

.. literalinclude:: ../snippets/isaac_lab_tutorials/tutorial_cloner/accessing_cloned_objects.py
    :language: python

Physics Replication
===================

The cloning process can take advantage of faster physics parsing by replicating physics directly in PhysX, avoiding copying of USD physics properties. This feature can be enabled by passing in a new parameter `replicate_physics=True` when cloning objects in the scene. Note that to use this feature, the user must also specify some additional parameters: `base_env_paths` and `root_path`. `base_env_paths` points to the ancestry prim of all clones and `root_path` specifies the prefix of each target clone path before the index. This also imposes the limitation that all target clone paths must be appended by an incremental index. If both `define_base_env()` and `generate_paths()` APIs have already been called before cloning, the user can avoid specifying `base_env_paths` and `root_path` parameters as the information has already been provided to the Cloner class.

.. literalinclude:: ../snippets/isaac_lab_tutorials/tutorial_cloner/physics_replication.py
    :language: python

A full example using physics replication can be found at standalone_examples/api/isaacsim.core.cloner/cloner_ants.py.

There are currently some features that are not supported by physics replication. For example, runtime modification of shape properties are not allowed on prims that have been created using physics replication. For scenes that require randomization or modification of shape properties (such as materials, friction, restitution, etc.) at run time, please do not enable physics replication when cloning objects.

Additional Parameters
=====================

In addition to physics replication, the Cloner also provides an option to copy from the source prim. This flag can be set with the `copy_from_source` argument.

.. literalinclude:: ../snippets/isaac_lab_tutorials/tutorial_cloner/additional_parameters.py
    :language: python

By default, `copy_from_source` is set to `False`, in which case the cloned prims will be defined as `USD Inherits <https://openusd.org/release/api/class_usd_inherits.html>`_ of the source prim. The cloning process will be faster when USD Inherits are used for cloning. However, any changes that are made to the source prim *after* cloning will also reflect in the cloned prims. 

If this behavior is undesired, please set `copy_from_source` to `True`. When `copy_from_source` is set to `True`, the cloned prims will be defined as **copies** of the source prim. After cloning, each cloned prim will be an individual entity and any changes in the source prim **will not** be reflected on the cloned prims. This setting can be useful in cases where cloned environments are not designed to be identical.

Summary
=======

This tutorial covered the following topics:

1. How to use the Cloner interface
2. How to use the GridCloner interface
3. How to access states of cloned objects with isaacsim.core.api APIs
4. Advanced cloning with physics replication and additional parameters

Next Steps
^^^^^^^^^^

Continue on to the next tutorial in our Reinforcement Learning Tutorials series, :ref:`isaac_sim_app_tutorial_instanceable_assets`, to learn about instanceable assets for improving memory efficiency.

