..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_replicator_isaac_snippets:

==========================================
Useful Snippets
==========================================

Various examples of |isaac-sim_short| Replicator snippets that can be run as :ref:`Standalone Applications <standalone-application>` or from the UI using the :ref:`Script Editor <script-editor>`.


Annotator and Custom Writer Data from Multiple Cameras
-------------------------------------------------------

Example on how to access data from multiple cameras in a scene using annotators or custom writers. The standalone example can also be run directly (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.replicator.examples/multi_camera.py

.. tab-set::

    .. tab-item:: Script Editor

        .. raw:: html

            <details open>
            <summary>Annotator and Custom Writer Data from Multiple Cameras</summary>

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_isaac_snippets/multi_camera_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Standalone Application

        .. raw:: html

            <details open>
            <summary>Annotator and Custom Writer Data from Multiple Cameras</summary>

        .. literalinclude:: ../../../source/standalone_examples/api/isaacsim.replicator.examples/multi_camera.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

Synthetic Data Access at Specific Simulation Timepoints
--------------------------------------------------------

Example on how to access synthetic data (RGB, semantic segmentation) from multiple cameras in a simulation scene at specific events using annotators or writers. The standalone example can also be run directly (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.replicator.examples/simulation_get_data.py


.. tab-set::

    .. tab-item:: Script Editor

        .. raw:: html

            <details open>
            <summary>Synthetic Data Access at Specific Simulation Timepoints</summary>

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_isaac_snippets/simulation_get_data_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Standalone Application

        .. raw:: html

            <details open>
            <summary>Synthetic Data Access at Specific Simulation Timepoints</summary>

        .. literalinclude:: ../../../source/standalone_examples/api/isaacsim.replicator.examples/simulation_get_data.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>


.. _replicator_isaac_snippets_custom_event:

Custom Event Randomization and Writing
---------------------------------------------

The following example showcases the use of custom events to trigger randomizations and data writing at various times throughout the simulation. The standalone example can also be run directly (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.replicator.examples/custom_event_and_write.py


.. tab-set::

    .. tab-item:: Script Editor

        .. raw:: html

            <details open>
            <summary>Custom Event Randomization and Writing</summary>

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_isaac_snippets/custom_event_and_write_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Standalone Application

        .. raw:: html

            <details open>
            <summary>Custom Event Randomization and Writing</summary>

        .. literalinclude:: ../../../source/standalone_examples/api/isaacsim.replicator.examples/custom_event_and_write.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>


Motion Blur
---------------------------------------------

This example demonstrates how to capture motion blur data using `RTX Real-Time <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/rtx-renderer_rt.html>`_ and `RTX Interactive (Path Tracing) <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/rtx-renderer_pt.html>`_ rendering modes. For the |real_time_render| mode, refer to `motion blur parameters <https://docs.omniverse.nvidia.com/materials-and-rendering/latest/rtx_post-processing.html#motion-blur>`_. For the |interactive_render| mode, motion blur is achieved by rendering multiple subframes (``/omni/replicator/pathTracedMotionBlurSubSamples``) and combining them to create the effect.

The example uses animated and physics-enabled assets with synchronized motion. Keyframe animated assets can be advanced at any custom delta time due to their interpolated motion, whereas physics-enabled assets require a custom physics FPS to ensure motion samples at any custom delta time. The example showcases how to compute the target physics FPS, change it if needed, and restore the original physics FPS after capturing the motion blur.

The standalone example can also be run directly (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.replicator.examples/motion_blur.py


.. tab-set::

    .. tab-item:: Script Editor

        .. raw:: html

            <details open>
            <summary>Motion Blur</summary>

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_isaac_snippets/motion_blur_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Standalone Application

        .. raw:: html

            <details open>
            <summary>Motion Blur</summary>

        .. literalinclude:: ../../../source/standalone_examples/api/isaacsim.replicator.examples/motion_blur.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>


Subscribers and Events at Custom FPS
---------------------------------------------

Examples of subscribing to various events (such as stage, physics, and render/app), setting custom update rates, and adjusting various related settings. The standalone example can also be run directly (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.replicator.examples/subscribers_and_events.py


.. tab-set::

    .. tab-item:: Script Editor

        .. raw:: html

            <details open>
            <summary>Subscribers and Events at Custom FPS</summary>

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_isaac_snippets/subscribers_and_events_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Standalone Application

        .. raw:: html

            <details open>
            <summary>Subscribers and Events at Custom FPS</summary>

        .. literalinclude:: ../../../source/standalone_examples/api/isaacsim.replicator.examples/subscribers_and_events.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>


Accessing Writer and Annotator Data at Custom FPS
--------------------------------------------------

Example of how to trigger a writer and access annotator data at a custom FPS, with product rendering disabled when the data is not needed. The standalone example can also be run directly (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.replicator.examples/custom_fps_writer_annotator.py


.. Note::
    It is currently not possible to change timeline (stage) FPS after the replicator graph creation as it causes a graph reset. This issue is being addressed. As a workaround make sure you are setting the timeline (stage) parameters before creating the replicator graph.

.. tab-set::

    .. tab-item:: Script Editor

        .. raw:: html

            <details open>
            <summary>Accessing Writer and Annotator Data at Custom FPS</summary>

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_isaac_snippets/custom_fps_writer_annotator_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Standalone Application

        .. raw:: html

            <details open>
            <summary>Accessing Writer and Annotator Data at Custom FPS</summary>

        .. literalinclude:: ../../../source/standalone_examples/api/isaacsim.replicator.examples/custom_fps_writer_annotator.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

Cosmos Writer Example
-------------------------

This example demonstrates the ``CosmosWriter`` for capturing multi-modal synthetic data compatible with `NVIDIA Cosmos <https://www.nvidia.com/en-us/ai/cosmos/>`_ world foundation models. It creates a simple falling box scene and captures synchronized RGB, segmentation, depth, and edge data (images and videos) that can be used with Cosmos Transfer to generate photorealistic variations.

For a more detailed tutorial please see :ref:`isaac_sim_app_tutorial_replicator_cosmos`.


The standalone example can also be run directly (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.replicator.examples/cosmos_writer_simple.py

.. tab-set::

    .. tab-item:: Script Editor

        .. raw:: html

            <details open>
            <summary>Cosmos Writer Example</summary>

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_isaac_snippets/cosmos_writer_simple_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Standalone Application

        .. raw:: html

            <details open>
            <summary>Cosmos Writer Example</summary>

        .. literalinclude:: ../../../source/standalone_examples/api/isaacsim.replicator.examples/cosmos_writer_simple.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>


Synthetic Data Generation with Deformables
------------------------------------------

This example demonstrates synthetic data generation (SDG) with deformable physics: deformable assets (e.g., bananas and markers) are dropped into a crate, and RGB plus semantic segmentation frames are captured when each asset’s lowest vertex crosses a trigger height. It uses ``VolumeDeformableMaterial``, ``DeformablePrim``, and the deformable tensor API (e.g., ``get_nodal_positions``) for trigger detection, with optional material color randomization per capture.

.. figure:: ../images/isim_6.0_replicator_tut_viewport_sdg_deformables.jpg

The standalone example can also be run directly (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/api/isaacsim.replicator.examples/sdg_deformables.py

.. tab-set::

    .. tab-item:: Script Editor

        .. raw:: html

            <details open>
            <summary>Synthetic Data Generation with Deformables</summary>

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_isaac_snippets/sdg_deformables_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Standalone Application

        .. raw:: html

            <details open>
            <summary>Synthetic Data Generation with Deformables</summary>

        .. literalinclude:: ../../../source/standalone_examples/api/isaacsim.replicator.examples/sdg_deformables.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

