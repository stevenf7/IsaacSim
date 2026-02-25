..
   Copyright (c) 2025, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_replicator_cosmos:

==========================================
Cosmos Synthetic Data Generation
==========================================

This tutorial demonstrates generating multi-modal synthetic data for `NVIDIA Cosmos <https://www.nvidia.com/en-us/ai/cosmos/>`_ using the ``CosmosWriter`` in |isaac-sim_short|. The writer captures synchronized RGB, depth, segmentation, and edge data from a robot navigating a warehouse environment.

The generated data serves as ground truth input for `Cosmos Transfer <https://docs.nvidia.com/cosmos/latest/>`_, which transforms low-resolution control signals into high-quality visual simulations through its Multi-ControlNet architecture.

.. image:: /images/isim_5.1_replicator_tut_viewport_cosmos_warehouse.webp
    :align: center
    :alt: Multi-modal data captured from robot perspective: RGB, depth, segmentation, shaded segmentation, and edge maps


Why Use the CosmosWriter?
--------------------------

The CosmosWriter bridges the gap between simulation and real-world robotics applications by generating rich, multi-modal datasets from synthetic environments. Key use cases include:

- **Sim-to-Real Transfer**: Transform synthetic simulation videos into photorealistic scenes with varied materials, lighting, and environmental conditions using Cosmos Transfer
- **Domain Adaptation**: Generate diverse training data from a single simulation, creating variations in scene styles, materials, and lighting without re-running expensive simulations or capturing real-world data
- **Data Augmentation**: Expand limited datasets by generating multiple visual variations while preserving robot motions, object positions, and scene structure

For examples of sim-to-real transformations in robotics, see the `Cosmos Cookbook Robotics Gallery <https://nvidia-cosmos.github.io/cosmos-cookbook/gallery/robotics_inference.html>`_, which showcases how synthetic kitchen scenes can be transformed into photorealistic environments with different cabinet styles, robot materials, and lighting conditions.


Prerequisites
-------------------

* Familiarity with the :doc:`omni.replicator <extensions:ext_replicator>` extension and its :doc:`writers <extensions:ext_replicator/writer_examples>`
* Basic understanding of |isaac-sim_short|'s SDG :ref:`isaac_sim_app_tutorial_replicator_getting_started`
* Running simulations as :ref:`Standalone Applications <standalone-application>` or via the :ref:`Script Editor <script-editor>`.

What the CosmosWriter Generates
--------------------------------

The writer outputs five synchronized modalities from the robot's camera:

- **RGB** - Color imagery (vis control)
- **Depth** - Distance-to-camera for spatial understanding
- **Segmentation** - Instance masks for object tracking
- **Shaded Segmentation** - Instance masks with realistic shading
- **Edges** - Canny edge detection for boundaries

These modalities correspond to `Cosmos Transfer's <https://docs.nvidia.com/cosmos/latest/#controlnet-specification>`_ control branches:

- **vis**: Uses RGB imagery with bilateral blurring
- **edge**: Applies Canny edge detection (tunable thresholds)
- **depth**: Depth maps for 3D structure understanding
- **seg**: Segmentation masks for object identification

Each control branch can be weighted (0.0-1.0) to balance adherence vs. creative freedom in the generated output.



Implementation
-------------------

This example demonstrates a Carter Nova robot autonomously navigating through a warehouse environment. As the robot moves from its starting position to a target location, the ``CosmosWriter`` captures synchronized multi-modal data (RGB, depth, segmentation, shaded segmentation, and edges) from the robot's front camera. The captured data is organized into clips, with each clip containing a sequence of frames that can be used as input for Cosmos Transfer.

.. tab-set::

    .. tab-item:: Standalone Application

        The example can be run as a standalone application using the following commands in the terminal (on Windows use ``python.bat`` instead of ``python.sh``):

        .. code-block:: bash

            ./python.sh standalone_examples/replicator/cosmos_writer_warehouse.py

        .. raw:: html

            <details closed>
            <summary>Full Standalone Script</summary>

        .. literalinclude:: ../../../source/standalone_examples/replicator/cosmos_writer_warehouse.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Script Editor

        .. raw:: html

            <details closed>
            <summary>Full Script Editor Script</summary>

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_cosmos/cosmos_writer_warehouse_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Code Explanation

        This tab explains how the warehouse navigation example works and how the CosmosWriter captures multi-modal data during robot movement.

        **Script Overview**

        The script simulates a Carter Nova robot navigating through a warehouse while capturing synchronized multi-modal data from its front camera. The robot moves from a starting position to a target location, and the CosmosWriter generates ground truth data for Cosmos Transfer.

        .. raw:: html

            <details open>
            <summary>Main Execution Flow</summary>

        .. code-block:: python

            # Setup the environment and run the example
            run_example(
                num_clips=NUM_CLIPS,
                num_frames_per_clip=NUM_FRAMES_PER_CLIP,
                capture_interval=CAPTURE_INTERVAL,
                start_delay=START_DELAY,
                use_instance_id=True,
            )

            simulation_app.close()

        .. raw:: html

            </details>

        **Key Configuration Parameters**

        .. raw:: html

            <details open>
            <summary>Capture Parameters</summary>

        - ``NUM_CLIPS = 2``: Generate 2 separate video clips
        - ``NUM_FRAMES_PER_CLIP = 10``: Each clip contains 10 frames  
        - ``CAPTURE_INTERVAL = 2``: Capture every 2nd simulation step
        - ``START_DELAY = 0.1``: Custom delay to start capturing at a specific time

        .. raw:: html

            </details>

        **Data Capture Pipeline**

        The ``run_sdg_pipeline`` function orchestrates the entire capture process:

        .. raw:: html

            <details open>
            <summary>SDG Pipeline Implementation</summary>

        .. code-block:: python

            def run_sdg_pipeline(
                camera_path, num_clips, num_frames_per_clip, capture_interval, use_instance_id=True, segmentation_mapping=None
            ):
                rp = rep.create.render_product(camera_path, (1280, 720))
                cosmos_writer = rep.WriterRegistry.get("CosmosWriter")
                backend = rep.backends.get("DiskBackend")
                out_dir = os.path.join(os.getcwd(), f"_out_cosmos_warehouse")
                print(f"output_directory: {out_dir}")
                backend.initialize(output_dir=out_dir)
                cosmos_writer.initialize(
                    backend=backend, use_instance_id=use_instance_id, segmentation_mapping=segmentation_mapping
                )
                cosmos_writer.attach(rp)

                # Make sure the timeline is playing
                timeline = omni.timeline.get_timeline_interface()
                if not timeline.is_playing():
                    timeline.play()

                print(
                    f"Starting SDG pipeline. Capturing {num_clips} clips with {num_frames_per_clip} frames each, every {capture_interval} simulation step(s)."
                )

                for clip_index in range(num_clips):
                    print(f"Starting clip {clip_index + 1}/{num_clips}")

                    frames_captured_count = 0
                    simulation_step_index = 0
                    while frames_captured_count < num_frames_per_clip:
                        print(f"Simulation step {simulation_step_index}")
                        if simulation_step_index % capture_interval == 0:
                            print(f"\t Capturing frame {frames_captured_count + 1}/{num_frames_per_clip} for clip {clip_index + 1}")
                            rep.orchestrator.step(pause_timeline=False)
                            frames_captured_count += 1
                        else:
                            simulation_app.update()
                        simulation_step_index += 1

                    print(f"Finished clip {clip_index + 1}/{num_clips}. Captured {frames_captured_count} frames")

                    # Move to next clip if not the last clip
                    if clip_index < num_clips - 1:
                        print(f"Moving to next clip...")
                        cosmos_writer.next_clip()

                print("Waiting to finish processing and writing the data")
                rep.orchestrator.wait_until_complete()
                print(f"Finished SDG pipeline. Captured {num_clips} clips with {num_frames_per_clip} frames each")
                cosmos_writer.detach()
                rp.destroy()
                timeline.pause()

        **Key aspects:**
        - The render product is created from the robot's front camera at 1280x720 resolution
        - ``pause_timeline=False`` allows the robot to continue moving during capture
        - The simulation advances between captures to show navigation progress

        .. raw:: html

            </details>

        **CosmosWriter Configuration**

        .. raw:: html

            <details open>
            <summary>Writer Modes and Parameters</summary>

        The CosmosWriter supports two segmentation modes:

        1. **Instance ID Mode** (default):

           .. code-block:: python

               cosmos_writer.initialize(
                   backend=backend, use_instance_id=use_instance_id, segmentation_mapping=segmentation_mapping
               )

        2. **Semantic Segmentation Mode**:

           .. code-block:: python

               segmentation_mapping = {
                   "floor": [255, 0, 0, 255],  # Red
                   "wall": [0, 255, 0, 255],  # Green
                   "rack": [0, 0, 255, 255],  # Blue
               }

               # Note: This overrides instance ID mode and requires semantic annotations
               cosmos_writer.initialize(backend=backend, segmentation_mapping=segmentation_mapping)

        .. raw:: html

            </details>

        **Timeline Management**

        The script uses a helper function to advance the timeline before starting capture:

            .. raw:: html

                <details open>
                <summary>Timeline Advancement</summary>

            .. code-block:: python

                def advance_timeline_by_duration(duration: float, max_updates: int = 1000):
                    timeline = omni.timeline.get_timeline_interface()
                    current_time = timeline.get_current_time()
                    target_time = current_time + duration

                    if timeline.get_end_time() < target_time:
                        timeline.set_end_time(1000000)

                    if not timeline.is_playing():
                        timeline.play()

                    print(f"Advancing timeline from {current_time:.4f}s to {target_time:.4f}s")
                    step_count = 0
                    while current_time < target_time:
                        if step_count >= max_updates:
                            print(f"Max updates reached: {step_count}, finishing timeline advance.")
                            break

                        prev_time = current_time
                        simulation_app.update()
                        current_time = timeline.get_current_time()
                        step_count += 1

                        if step_count % 10 == 0:
                            print(f"\tStep {step_count}, {current_time:.4f}s/{target_time:.4f}s")

                        if current_time <= prev_time:
                            print(f"Warning: Timeline did not advance at update {step_count} (time: {current_time:.4f}s).")
                    print(f"Finished advancing timeline to {current_time:.4f}s (target {target_time:.4f}s) in {step_count} steps")

            .. raw:: html

                </details>


Output Structure
-----------------

After running the script, an output folder (e.g., ``_out_cosmos_warehouse``) is created containing organized multi-modal data optimized for Cosmos Transfer and other foundation model training pipelines. Each clip represents a continuous sequence of frames captured during robot navigation:

.. code-block:: text

    _out_cosmos_warehouse/
      clip_0000/                    # First clip sequence
        rgb/                        # Standard color images
          rgb_0000.png, rgb_0001.png, ...
        depth/                      # Colorized depth visualization
          depth_0000.png, depth_0001.png, ...
        segmentation/              # Instance/semantic masks
          segmentation_0000.png, segmentation_0001.png, ...
        shaded_seg/                # Segmentation with realistic shading
          shaded_seg_0000.png, shaded_seg_0001.png, ...
        edges/                      # Canny edge detection results
          edges_0000.png, edges_0001.png, ...
        rgb.mp4                     # Combined RGB video
        depth.mp4                   # Combined depth video
        segmentation.mp4            # Combined segmentation video
        shaded_seg.mp4              # Combined shaded segmentation video
        edges.mp4                   # Combined edges video
      clip_0001/                    # Next clip sequence

**What Each Modality Provides:**

- **RGB (rgb.mp4)**: The visual input video used with Cosmos Transfer's ``vis`` control branch for preserving lighting and camera properties
- **Depth (depth.mp4)**: 3D spatial information used with the ``depth`` control branch to maintain perspective and spatial relationships
- **Segmentation (segmentation.mp4)**: Instance or semantic masks used with the ``seg`` control branch for object-level transformations
- **Shaded Segmentation (shaded_seg.mp4)**: Combines segmentation with realistic shading for enhanced visual coherence
- **Edges (edges.mp4)**: Structural boundaries used with the ``edge`` control branch to preserve object shapes while allowing material and lighting changes

These MP4 files can be directly passed to Cosmos Transfer as control inputs. The PNG sequences are provided for frame-level inspection or custom processing pipelines.

Advanced Usage
---------------

**Custom Segmentation Colors:**

Map specific semantic labels to custom colors when you need consistent class identification across datasets. Use this when training models that require specific object classes to maintain the same color/ID across all training data, ensuring Cosmos Transfer preserves class relationships.

.. code-block:: python

    segmentation_mapping = {
        "floor": [255, 0, 0, 255],  # Red
        "wall": [0, 255, 0, 255],  # Green
        "rack": [0, 0, 255, 255],  # Blue
    }

    # Note: This overrides instance ID mode and requires semantic annotations
    cosmos_writer.initialize(backend=backend, segmentation_mapping=segmentation_mapping)

**Edge Detection Tuning:**

Adjust Canny edge detection parameters for the hysteresis procedure when generating edge maps. The Canny algorithm uses two thresholds:

- **Low threshold**: Edges with gradient magnitude above this value are considered as potential edges
- **High threshold**: Edges with gradient magnitude above this value are definitely edges

Lower threshold values detect more edges (including noise), while higher values produce cleaner output with only strong edges. Values typically range from 10-200.

.. code-block:: python

    cosmos_writer.initialize(
        backend=backend,
        use_instance_id=True,
        canny_threshold_low=10,  # Low threshold for hysteresis
        canny_threshold_high=100,  # High threshold for hysteresis
    )

Using Data with Cosmos Transfer
---------------------------------

The generated data can be used with `Cosmos Transfer <https://docs.nvidia.com/cosmos/latest/>`_ to create high-quality visual simulations. This enables sim-to-real transfer where synthetic scenes are transformed into photorealistic environments while preserving robot motions and scene structure.

For real-world examples of this workflow, see the `Cosmos Cookbook Robotics Gallery <https://nvidia-cosmos.github.io/cosmos-cookbook/gallery/robotics_inference.html>`_, which demonstrates:

- **Edge-only control**: Transform simulation videos into diverse kitchen styles (white cabinets, red cabinets, wood tones) and robot materials (plastic, metal, gold) while preserving exact robot motions
- **Multi-control**: Combine depth, edge, and segmentation controls for precise scene manipulation

Here's how the modalities map to Transfer's control branches:

**Basic Single Control Example:**

.. code-block:: json

    {
        "prompt": "A modern warehouse with autonomous robots...",
        "input_video_path": "_out_cosmos_warehouse/clip_0000/rgb.mp4",
        "edge": {
            "control_weight": 1.0
        }
    }

**Multi-Modal Control Example:**

.. code-block:: json

    {
        "prompt": "High-quality warehouse simulation...",
        "input_video_path": "_out_cosmos_warehouse/clip_0000/rgb.mp4",
        "vis": {"control_weight": 0.25},
        "edge": {"control_weight": 0.25},
        "depth": {
            "input_control": "_out_cosmos_warehouse/clip_0000/depth.mp4",
            "control_weight": 0.25
        },
        "seg": {
            "input_control": "_out_cosmos_warehouse/clip_0000/segmentation.mp4",
            "control_weight": 0.25
        }
    }

**Key Considerations:**

- **Control Weights**: Values 0.0-1.0 control adherence (higher = stricter following, lower = more creative freedom)
- **Automatic Normalization**: If total weights > 1.0, they're normalized automatically
- **Prompting**: Focus on single scenes with rich descriptions; avoid camera control instructions
- **Safety**: Human faces are automatically blurred by Cosmos Guardrail

For advanced features like spatiotemporal control maps and prompt upsampling, refer to the `Cosmos Transfer documentation <https://docs.nvidia.com/cosmos/latest/>`_.

Summary
--------

This tutorial demonstrated using the CosmosWriter to generate synchronized multi-modal data from a robot navigating a warehouse. The output provides ground truth for Cosmos Transfer to create high-quality visual simulations for physical AI applications.

**Next Steps:**

1. **Explore your output**: Navigate to the generated output folder (e.g., ``_out_cosmos_warehouse``) to inspect the RGB, depth, segmentation, and edge data
2. **Use with Cosmos Transfer**: Pass the generated MP4 files to Cosmos `Transfer1 <https://docs.nvidia.com/cosmos/latest/transfer1/index.html>`_ or `Transfer2.5 <https://docs.nvidia.com/cosmos/latest/transfer2.5/index.html>`_ using the JSON configuration examples above
3. **See real examples**: Visit the `Cosmos Cookbook Robotics Gallery <https://nvidia-cosmos.github.io/cosmos-cookbook/gallery/robotics_inference.html>`_ for examples of sim-to-real transformations using similar data
4. **Customize for your use case**: Adjust capture parameters, segmentation mappings, and edge detection thresholds to optimize for your specific training pipeline
