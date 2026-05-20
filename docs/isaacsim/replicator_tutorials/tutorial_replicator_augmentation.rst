..
   Copyright (c) 2022-2026, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.




.. _isaac_sim_app_tutorial_replicator_augmentation:

====================
Data Augmentation
====================

Example of using |isaac-sim_short| and Replicator to capture augmented synthetic data.

Learning Objectives
-------------------

This tutorial provides examples on how to use omni.replicator :doc:`augmentations<extensions:ext_replicator/augmentation_examples>` on annotators or writers. The provided examples will showcase how to augment **rgb** and **depth** annotator data using warp (GPU) or NumPy (CPU) kernel/filters. The use of warp is particularly advantageous for executing parallelizable tasks, especially if the data already resides in the GPUs memory, thus avoiding memory copies from GPU to CPU.

* For a better understanding of the tutorial, familiarity with :doc:`omni.replicator <extensions:ext_replicator>`, :doc:`annotators <extensions:ext_replicator/annotators_details>`, :doc:`writers <extensions:ext_replicator/writer_examples>` and :doc:`warp <extensions:ext_warp>` is recommended.

.. * :ref:`isaac_sim_app_tutorial_ros_camera_noise` is a similar tutorial using augmentation to publish noisy camera images using ROS.

Scenario
---------

.. image:: /images/isaac_tutorial_replicator_augmentation.png
    :align: center

The depicted figure showcases the example augmentations used throughout the examples. The first image is an illustrative example switching the red and blue channels of the image. The second image is a composed augmentation of converting the rgb data to hsv, adding gaussian noise, and converting back to rgb. The third and forth image are results of applying gaussian noise filters with various sigma values to the depth data.

For the example scenario a red cube is spawned with a camera looking at it from a top view. For the cube a replicator randomization graph is created which will trigger a random rotation for every frame capture.

Implementation
---------------

The tutorial is split into two parts, the first example will showcase how to augment annotators directly, and secondly how to augment writers. Both examples can be run as :ref:`Standalone Applications <standalone-application>` or from the UI using the :ref:`Script Editor <script-editor>`.

Annotator Augmentation
######################

The annotator example will output rgb images with the red and blue channels switched, and two depth images with different gaussian noise levels (saved as grayscale PNGs). The example can switch between using warp or NumPy augmentations.

.. tab-set::

    .. tab-item:: Standalone Application

        The example can be run as a standalone application using the following commands in the terminal (on Windows use ``python.bat`` instead of ``python.sh``): 

        .. code-block:: bash

            ./python.sh standalone_examples/replicator/augmentation/annotator_augmentation.py --env_url /Isaac/Environments/Grid/default_environment.usd

        Optionally the following arguments can be used to change the default behavior:

        - ``--env_url`` -- USD environment path relative to the assets root (default: empty scene with dome light and ground plane)
        - ``--use_warp`` -- flag to use warp (GPU) instead of numpy (CPU) for the augmentation functions (default: False)  
        - ``--num_frames`` -- the number of frames to be captured (default: 25)

        .. code-block:: bash

            ./python.sh standalone_examples/replicator/augmentation/annotator_augmentation.py --use_warp --num_frames 25 --env_url /Isaac/Environments/Grid/default_environment.usd

        .. raw:: html

            <details closed>
            <summary>Full Standalone Script</summary>

        .. literalinclude:: ../../../source/standalone_examples/replicator/augmentation/annotator_augmentation.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Script Editor

        .. raw:: html

            <details closed>
            <summary>Full Script Editor Script</summary>

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_augmentation/annotator_augmentation_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Code Explanation

        To be able to run the augmentation functions, enable scripting in the settings:

        .. raw:: html

            <details open>
            <summary>Enable Scripting</summary>

        .. code-block:: python

            # Enable warp scripts
            carb.settings.get_settings().set_bool("/app/omni.graph.scriptnode/opt_in", True)

        .. raw:: html

            </details>            

        To augment the **rgb** data we provide for illustrative purposes a function that switches the red and blue channels in the rgb data using NumPy (CPU) and warp (GPU) kernels:

        .. raw:: html

            <details open>
            <summary>RGB to BGR using Warp and Numpy</summary>

        .. code-block:: python

            def rgb_to_bgr_np(data_in):
                """Swap RGBA red and blue channels using NumPy (CPU)."""
                data_in[:, :, [0, 2]] = data_in[:, :, [2, 0]]
                return data_in


            @wp.kernel
            def rgb_to_bgr_wp(data_in: wp.array3d(dtype=wp.uint8), data_out: wp.array3d(dtype=wp.uint8)):
                """Swap RGBA red and blue channels using Warp (GPU)."""
                i, j = wp.tid()
                data_out[i, j, 0] = data_in[i, j, 2]
                data_out[i, j, 1] = data_in[i, j, 1]
                data_out[i, j, 2] = data_in[i, j, 0]
                data_out[i, j, 3] = data_in[i, j, 3]

        .. raw:: html

            </details>

        For the **depth** data we use gaussian noise filters. Note that the functions are registered in the annotator registry for later access:

        .. raw:: html

            <details open>
            <summary>Depth Gaussian Noise using Warp and Numpy</summary>

        .. code-block:: python

            def gaussian_noise_depth_np(data_in, sigma: float, seed: int):
                """Add Gaussian noise to depth values using NumPy (CPU)."""
                np.random.seed(seed)
                result = data_in.astype(np.float32) + np.random.randn(*data_in.shape) * sigma
                return np.clip(result, 0, None).astype(data_in.dtype)


            rep.annotators.register_augmentation(
                "gn_depth_np", rep.annotators.Augmentation.from_function(gaussian_noise_depth_np, sigma=0.1, seed=SEED)
            )


            @wp.kernel
            def gaussian_noise_depth_wp(
                data_in: wp.array2d(dtype=wp.float32), data_out: wp.array2d(dtype=wp.float32), sigma: float, seed: int
            ):
                """Add Gaussian noise to depth values using Warp (GPU)."""
                i, j = wp.tid()
                # Unique ID for random seed per pixel
                scalar_pixel_id = i * data_in.shape[1] + j
                state = wp.rand_init(seed, scalar_pixel_id)
                data_out[i, j] = data_in[i, j] + sigma * wp.randn(state)


            rep.annotators.register_augmentation(
                "gn_depth_wp", rep.annotators.Augmentation.from_function(gaussian_noise_depth_wp, sigma=0.1, seed=SEED)
            )

        .. raw:: html

            </details>

        Create the augmentations (warp or NumPy) once using the function directly and once from the registry:

        .. raw:: html

            <details open>
            <summary>Augmentations using Warp or Numpy</summary>

        .. code-block:: python

            # Augment the RGB and depth annotators
            rgb_to_bgr_augm = rep.annotators.Augmentation.from_function(rgb_to_bgr_wp if use_warp else rgb_to_bgr_np)
            depth_aug = rep.annotators.get_augmentation("gn_depth_wp" if use_warp else "gn_depth_np")
            rgb_to_bgr_annot = rep.annotators.augment(
                source_annotator=rep.annotators.get("rgb"),
                augmentation=rgb_to_bgr_augm,
            )
            depth_annot_1 = rep.annotators.get("distance_to_camera")
            depth_annot_1.augment(depth_aug)
            depth_annot_2 = rep.annotators.get("distance_to_camera")
            depth_annot_2.augment(depth_aug, sigma=0.5)

        .. raw:: html

            </details>

        You can also register a new annotator together with its augmentation:

        .. raw:: html

            <details open>
            <summary>Register Augmentated Annotator</summary>

        .. code-block:: python

            rgb_to_bgr_annot = rep.annotators.augment(
                source_annotator=rep.annotators.get("rgb"),
                augmentation=rgb_to_bgr_augm,
            )
            depth_annot_1 = rep.annotators.get("distance_to_camera")
            depth_annot_1.augment(depth_aug)
            depth_annot_2 = rep.annotators.get("distance_to_camera")
            depth_annot_2.augment(depth_aug, sigma=0.5)

        .. raw:: html

            </details>

        Finally create the augmented annotators (1x **rgb**, 2x **depth**) and attach them to a render product to generate data:

        .. raw:: html

            <details open>
            <summary>Annotator Augmentation</summary>

        .. code-block:: python

            # Create the render product and attach the annotators to it
            cam = rep.functional.create.camera(position=(0, 0, 5), look_at=(0, 0, 0))
            rp = rep.create.render_product(cam, resolution)
            rgb_to_bgr_annot.attach(rp)
            depth_annot_1.attach(rp)
            depth_annot_2.attach(rp)

        .. raw:: html

            </details>


Writer Augmentation
####################

The **writer** example will output gaussian noise augmented RGB and depth annotator data from a writer.

.. tab-set::

    .. tab-item:: Standalone Application

       The example can be run as a standalone application using the following commands in the terminal (on Windows use ``python.bat`` instead of ``python.sh``): 

        .. code-block:: bash

            ./python.sh standalone_examples/replicator/augmentation/writer_augmentation.py --env_url /Isaac/Environments/Grid/default_environment.usd

        Optionally the following arguments can be used to change the default behavior:

        - ``--env_url`` -- USD environment path relative to the assets root (default: empty scene with dome light and ground plane)
        - ``--use_warp`` -- flag to use warp (GPU) instead of NumPy (CPU) for the augmentation functions (default: False)  
        - ``--num_frames`` -- the number of frames to be captured (default: 25)

        .. code-block:: bash

            ./python.sh standalone_examples/replicator/augmentation/writer_augmentation.py --use_warp --num_frames 25 --env_url /Isaac/Environments/Grid/default_environment.usd

        .. raw:: html

            <details closed>
            <summary>Full Standalone Script</summary>

        .. literalinclude:: ../../../source/standalone_examples/replicator/augmentation/writer_augmentation.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Script Editor

        .. raw:: html

            <details closed>
            <summary>Full Script Editor Script</summary>

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_augmentation/writer_augmentation_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Code Explanation

        To be able to run the augmentation functions one needs to enable scripting in the settings:

        .. raw:: html

            <details open>
            <summary>Enable Scripting</summary>

        .. code-block:: python

            # Enable warp scripts
            carb.settings.get_settings().set_bool("/app/omni.graph.scriptnode/opt_in", True)

        .. raw:: html

            </details>    

        For the **rgb** (**LdrColor**) annotator of the writer, we provide gaussian noise functions using NumPy (CPU) and warp (GPU) kernels, applied on the RGB channels of the RGBA provided data format.

        .. raw:: html

            <details open>
            <summary>RGB Gaussian Noise using Warp and Numpy</summary>

        .. code-block:: python

            def gaussian_noise_rgb_np(data_in, sigma: float, seed: int):
                """Add Gaussian noise to RGB data using NumPy (CPU)."""
                np.random.seed(seed)
                # Convert to float32 space
                data_in = data_in.astype(np.float32)
                # Add Gaussian noise to each channel
                data_in[:, :, 0] = data_in[:, :, 0] + np.random.randn(*data_in.shape[:-1]) * sigma
                data_in[:, :, 1] = data_in[:, :, 1] + np.random.randn(*data_in.shape[:-1]) * sigma
                data_in[:, :, 2] = data_in[:, :, 2] + np.random.randn(*data_in.shape[:-1]) * sigma
                # Clip to [0, 255] and convert to uint8
                data_in = np.clip(data_in, 0, 255).astype(np.uint8)
                return data_in


            @wp.kernel
            def gaussian_noise_rgb_wp(
                data_in: wp.array3d(dtype=wp.uint8), data_out: wp.array3d(dtype=wp.uint8), sigma: float, seed: int
            ):
                """Add Gaussian noise to RGB data using Warp (GPU)."""
                # Get thread coordinates and image dimensions to calculate unique pixel ID for random generation
                i, j = wp.tid()
                dim_i = data_in.shape[0]
                dim_j = data_in.shape[1]
                pixel_id = i * dim_i + j

                # Use pixel_id as offset to create unique seeds for each pixel and channel
                state_r = wp.rand_init(seed, pixel_id + (dim_i * dim_j * 0))
                state_g = wp.rand_init(seed, pixel_id + (dim_i * dim_j * 1))
                state_b = wp.rand_init(seed, pixel_id + (dim_i * dim_j * 2))

                # Apply noise to each channel independently using unique seeds
                val_r = wp.float32(data_in[i, j, 0]) + sigma * wp.randn(state_r)
                val_g = wp.float32(data_in[i, j, 1]) + sigma * wp.randn(state_g)
                val_b = wp.float32(data_in[i, j, 2]) + sigma * wp.randn(state_b)

                # Clip to [0, 255] and convert to uint8
                data_out[i, j, 0] = wp.uint8(wp.clamp(val_r, 0.0, 255.0))
                data_out[i, j, 1] = wp.uint8(wp.clamp(val_g, 0.0, 255.0))
                data_out[i, j, 2] = wp.uint8(wp.clamp(val_b, 0.0, 255.0))
                data_out[i, j, 3] = data_in[i, j, 3]

        .. raw:: html

            </details>  

        For the **depth** annotator of the writer, there are gaussian noise functions using NumPy (CPU) and warp (GPU) kernels, applied on the 2D array of float32 values. The functions are registered in the annotator registry for later access:

        .. raw:: html

            <details open>
            <summary>Depth Gaussian Noise using Warp and Numpy</summary>

        .. code-block:: python

            def gaussian_noise_depth_np(data_in, sigma: float, seed: int):
                """Add Gaussian noise to depth values using NumPy (CPU)."""
                np.random.seed(seed)
                result = data_in.astype(np.float32) + np.random.randn(*data_in.shape) * sigma
                return np.clip(result, 0, None).astype(data_in.dtype)


            rep.AnnotatorRegistry.register_augmentation(
                "gn_depth_np", rep.annotators.Augmentation.from_function(gaussian_noise_depth_np, sigma=0.1, seed=None)
            )


            @wp.kernel
            def gaussian_noise_depth_wp(
                data_in: wp.array2d(dtype=wp.float32), data_out: wp.array2d(dtype=wp.float32), sigma: float, seed: int
            ):
                """Add Gaussian noise to depth values using Warp (GPU)."""
                i, j = wp.tid()
                # Unique ID for random seed per pixel
                scalar_pixel_id = i * data_in.shape[1] + j
                state = wp.rand_init(seed, scalar_pixel_id)
                data_out[i, j] = data_in[i, j] + sigma * wp.randn(state)


            rep.AnnotatorRegistry.register_augmentation(
                "gn_depth_wp", rep.annotators.Augmentation.from_function(gaussian_noise_depth_wp, sigma=0.1, seed=None)
            )

        .. raw:: html

            </details>  

        Access the default (**rgb**) augmentations from replicator:

        .. raw:: html

            <details open>
            <summary>Built-in Replicator Augmentations</summary>

        .. code-block:: python

            # Augment the annotators
            rgb_to_hsv_augm = rep.annotators.Augmentation.from_function(rep.augmentations_default.aug_rgb_to_hsv)
            hsv_to_rgb_augm = rep.annotators.Augmentation.from_function(rep.augmentations_default.aug_hsv_to_rgb)

        .. raw:: html

            </details>  

        Furthermore the custom augmentations are created (warp or NumPy), after using the function directly and once from the registry:

        .. raw:: html

            <details open>
            <summary>Augmentations using Warp or Numpy</summary>

        .. code-block:: python

            # Augment the RGB and depth annotators
            gn_rgb_augm = rep.annotators.Augmentation.from_function(
                gaussian_noise_rgb_wp if use_warp else gaussian_noise_rgb_np, sigma=15.0, seed=SEED
            )
            gn_depth_augm = rep.annotators.get_augmentation("gn_depth_wp" if use_warp else "gn_depth_np")

        .. raw:: html

            </details>  

        Finally the writer is created and initialized to use the **rgb** and **depth** (**distance_to_camera**) annotators. The built-in ``rgb`` annotator is replaced by a new augmented one by using the same ``name="rgb"`` name and adding it to the writer (``add_annotator``). The augmented RGB annotator uses a composition by switching the data to hsv, adding gaussian noise, and switching back to RGB. The ``distance_to_camera`` annotator is augmented by using the built-in ``augment_annotator`` function:

        .. raw:: html

            <details open>
            <summary>Writer Augmentation</summary>

        .. code-block:: python

            # Create a writer and apply the augmentations to its corresponding annotators
            out_dir = os.path.join(os.getcwd(), f"_out_augm_writer_{'warp' if use_warp else 'numpy'}")
            backend = rep.backends.get("DiskBackend")
            backend.initialize(output_dir=out_dir)
            print(f"Writing data to: {out_dir}")
            writer = rep.writers.get("BasicWriter")
            writer.initialize(backend=backend, rgb=True, distance_to_camera=True, colorize_depth=True)

            # Apply the augmentations to the RGB and depth annotators
            augmented_rgb_annot = rep.annotators.get("rgb").augment_compose(
                [rgb_to_hsv_augm, gn_rgb_augm, hsv_to_rgb_augm], name="rgb"
            )
            writer.add_annotator(augmented_rgb_annot)
            writer.augment_annotator("distance_to_camera", gn_depth_augm)

            # Create a camera and a render product and attach them to the writer
            cam = rep.functional.create.camera(position=(0, 0, 5), look_at=(0, 0, 0))
            rp = rep.create.render_product(cam, resolution)
            writer.attach(rp)

        .. raw:: html

            </details>  