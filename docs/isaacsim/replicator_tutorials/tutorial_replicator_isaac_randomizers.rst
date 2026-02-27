..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_sim_app_tutorial_replicator_isaac_randomizers:

==========================================
Randomization Snippets
==========================================

Examples of randomization using USD and |isaac-sim_short| APIs. These examples demonstrate how to randomize scenes for synthetic data generation (SDG) in scenarios where default :doc:`replicator randomizers <extensions:ext_replicator/randomizer_details>` are not sufficient or applicable.

The snippets are designed to align with the structure and function names used in the replicator example snippets. In comparison they also have the option to write the data to disk by stetting ``write_data=True``.

Prerequisites:

- Familiarity with `USD <https://developer.nvidia.com/usd/tutorials>`__.
- Ability to execute code from the :ref:`Script Editor <script-editor>`.
- Understanding basic replicator concepts, such as :ref:`subframes <subframes examples>`.


Randomizing Light Sources
---------------------------

This snippet sets up a new environment containing a cube and a sphere. 
It then spawns a given number of lights and randomizes selected attributes for these lights over a specified number of frames.

.. image:: /images/isaac_tutorial_replicator_randomization_lights.gif
    :width: 32.5%
    :align: center

.. raw:: html

    <details open>
    <summary>Randomizing Light Sources</summary>

.. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_isaac_randomizers/randomizing_light_sources.py
    :language: python
    :lines: 16-

.. raw:: html

    </details>


Randomizing Textures
---------------------------

The snippet sets up an environment, spawns a given number of cubes and spheres, and randomizes their textures for the given number of frames. After the randomizations their original materials are reassigned. The snippet also showcases how to create a new material and assign it to a prim.

.. image:: /images/isaac_tutorial_replicator_randomization_textures.gif
    :width: 32.5%
    :align: center

.. raw:: html

    <details open>
    <summary>Randomizing Textures</summary>

.. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_isaac_randomizers/randomizing_textures.py
    :language: python
    :lines: 16-

.. raw:: html

    </details>


Sequential Randomizations
---------------------------

The snippet provides an example of more complex randomizations, where the results of the first randomization are used to determine the next randomization. It uses a custom sampler function to set the location of the camera by iterating over (almost) equidistant points on a sphere. The snippet starts by setting up the environment, a forklift, a pallet, a bin, and a dome light. For every randomization frame, it cycles through the dome light textures, moves the pallet to a random location, and then moves the bin so that it is fully on top of the pallet. Finally, it moves the camera to a new location on the sphere, ensuring it faces the bin.

.. image:: /images/isaac_tutorial_replicator_randomization_chained_persp.gif
    :width: 32.5%

.. image:: /images/isaac_tutorial_replicator_randomization_chained_sphere.gif
    :width: 32.5%

.. raw:: html

    <details open>
    <summary>Sequential Randomizations</summary>

.. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_isaac_randomizers/sequential_randomizations.py
    :language: python
    :lines: 16-

.. raw:: html

    </details>


Physics-based Randomized Volume Filling
----------------------------------------

The snippet randomizes the stacking of objects on multiple surfaces. It randomly spawns a given number of pallets in the selected areas and then spawns physically simulated boxes on top of them. A temporary collision box area is created around the pallets to prevent the boxes from falling off. After all the boxes have been dropped, they are moved in various directions and finally pulled towards the center of the pallet for more stable stacking. Finally, the collision area is removed, after which the boxes can also fall to the ground. To allow easier sliding of the boxes into more stable positions, their friction is temporarily reduced during the simulation.

.. image:: /images/isaac_tutorial_replicator_randomization_volume_fill.gif
    :width: 32.5%

.. image:: /images/isaac_tutorial_replicator_randomization_volume_fill_warehouse.gif
    :width: 32.5%

.. raw:: html

    <details open>
    <summary>Physics-based Randomized Volume Filling</summary>

.. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_isaac_randomizers/physics_based_randomized_volume_filling.py
    :language: python
    :lines: 16-

.. raw:: html

    </details>


Simready Assets SDG Example
----------------------------

Script editor example for using `SimReady Assets <https://developer.nvidia.com/omniverse/simready-assets>`_ to randomize the scene. SimReady Assets are physically accurate 3D objects with realistic properties, behavior, and data connections that are optimized for simulation.

.. note::

    The example can only run in async mode and requires the :doc:`SimReady Explorer <extensions:ext_core/ext_browser-extensions/simready-explorer>` window to be enabled to process the search requests.

The example script will create an SDG randomization and capture pipeline scenario with a table, a plate, and a number of items on top of the plate. The scene will be simulated for a while and then the captured images will be saved to disk.


The standalone example can also be run directly (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash
    
    ./python.sh standalone_examples/api/isaacsim.replicator.examples/simready_assets_sdg.py


.. image:: /images/isim_5.0_replicator_tut_viewport_randomization_simready_assets.jpg
    :align: center

.. tab-set::

    .. tab-item:: Script Editor

        .. raw:: html

            <details open>
            <summary>Simready Assets SDG Example</summary>

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_isaac_randomizers/simready_assets_sdg_example_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Standalone Application

        .. raw:: html

            <details open>
            <summary>Simready Assets SDG Example</summary>

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_isaac_randomizers/simready_assets_sdg_example.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>
