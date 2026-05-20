..
   Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.


.. _isaac_sim_app_tutorial_replicator_infinigen_sdg:

==============================================================
Environment Based Synthetic Dataset Generation with Infinigen
==============================================================

This tutorial explains how to set up a synthetic data generation (SDG) pipeline in |isaac-sim_short| using the :doc:`omni.replicator <extensions:ext_replicator>` extension and procedurally generated environments from `Infinigen <https://infinigen.org/>`_. The example uses the :ref:`standalone <standalone-application>` workflow.

.. figure:: /images/isim_4.5_replicator_tut_viewport_infinigen_rooms.jpg
    :height: 200px
    :alt: Infinigen generated rooms
    :figclass: align-center

    Example of Infinigen generated rooms.

.. figure:: /images/isim_4.5_replicator_tut_viewport_infinigen_assets.jpg
    :height: 200px
    :alt: Data from the synthetic dataset generation pipeline
    :figclass: align-center

    Example data collected from the synthetic dataset generation pipeline.

Learning Objectives
-------------------

In this tutorial, you will learn how to:

- Load procedurally generated environments from Infinigen as background scenes.
- Prepare the environments for SDG and physics simulations.
- Load physics-enabled target assets (labeled) for data collection and distractor assets (unlabeled) for scene diversity.
- Use built-in Replicator randomizer graphs manually triggered at custom intervals, detached from the writing process.
- Use custom USD / Isaac Sim API functions for custom randomizers.
- Use multiple Replicator Writers and cameras (render products) to save different types of data from different viewpoints.
- Use config files to easily customize the simulation and data collection process.
- Understand and customize configuration parameters for flexibility.

Prerequisites
--------------

Before starting this tutorial, you should be familiar with:

- USD / |isaac-sim_short| APIs for creating and manipulating USD stages.
- :doc:`Rigid-body dynamics<kit-physics:dev_guide/rigid_bodies_articulations/rigid_bodies>` and physics simulation in |isaac-sim_short|. 
- Replicator :doc:`randomizers <extensions:ext_replicator/randomizer_details>` and :doc:`OmniGraph <extensions:ext_omnigraph>` for a better understanding of the Replicator randomization graphs pipeline.
- Running simulations as :ref:`Standalone Applications <standalone-application>`.
- Procedurally generating environments using `Infinigen <https://infinigen.org/>`_.

Generating Infinigen Environments
---------------------------------

1. **Install Infinigen**: Follow the installation instructions on the `Infinigen GitHub Repository <https://github.com/princeton-vl/infinigen/blob/main/docs/Installation.md>`_.

   .. note::

      The Infinigen scene generation step is only tested on Linux. Refer to the `Infinigen platform support matrix <https://github.com/princeton-vl/infinigen/blob/main/docs/Installation.md#installation-options--supported-platforms>`_ for the current platform status, as Infinigen is an external library maintained outside of |isaac-sim_short|.

2. **Generate Environments**: Use the `Hello Room <https://github.com/princeton-vl/infinigen/blob/main/docs/HelloRoom.md>`_ instructions to generate indoor scenes using various settings and parameters.

3. **Example Script**: Use the following example script (Linux) to generate multiple dining room environments with different seeds. The script can be run directly from the terminal.

   .. code-block:: bash

    # Loop from 1 to 10 to generate 10 scenes
    for i in {1..10}
    do
      # Create the output folders for both the Infinigen generation and the Omniverse export
      mkdir -p outputs/indoors/dining_room_$i
      mkdir -p outputs/omniverse/dining_room_$i

      # Step 1: Run Infinigen scene generation for a DiningRoom scene with a specific seed
      python -m infinigen_examples.generate_indoors \
        --seed $i \
        --task coarse \
        --output_folder outputs/indoors/dining_room_$i \
        -g fast_solve.gin singleroom.gin \
        -p compose_indoors.terrain_enabled=False restrict_solving.restrict_parent_rooms=\[\"DiningRoom\"\] &&

      # Step 2: Export the generated scene to Omniverse-compatible format
      python -m infinigen.tools.export \
        --input_folder outputs/indoors/dining_room_$i \
        --output_folder outputs/omniverse/dining_room_$i \
        -f usdc \
        -r 1024 \
        --omniverse
    done

   - This script generates 10 unique dining room environments by varying the seed value.
   - The ``infinigen_examples.generate_indoors`` command generates the environments and stores them in ``outputs/indoors/dining_room_$i``.
   - The ``infinigen.tools.export`` command exports the generated environments to the selected format, saving them to ``outputs/omniverse/dining_room_$i``.
   - The ``-f usdc`` flag specifies the format of the exported file to USD.
   - The ``--omniverse`` flag ensures compatibility with Omniverse applications.

Scenario Overview
------------------

In this tutorial, we will use procedurally generated environments as backdrops for synthetic data generation. These environments are then configured with colliders and physics properties, enabling physics-based simulations. Within each indoor environment, we define a "working area"—in this case, the dining table—where we will place both labeled target assets and unlabeled distractor assets.

The assets are divided into two categories:

- **Falling assets**: Physics-enabled objects that interact with the environment and settle onto surfaces, such as the ground or table.
- **Floating assets**: Objects equipped only with colliders that remain floating in the air.

For each background environment, we will capture frames in two scenarios:

1. Assets floating around the working area.
2. Physics-enabled assets that have settled on surfaces like the ground or table.

To capture these frames, we use multiple cameras (render products) configured with one or multiple writers. The cameras will be randomized for each frame, changing their positions around the working area and orienting toward randomly selected target assets.

Once the captures for one environment are complete, a new environment will be loaded, configured with colliders and physics properties, and the process will repeat until the desired number of captures is achieved.

During the capture process, we will apply randomizers at various frames to introduce variability into the scene. These randomizations include:

- Object poses.
- Lighting configurations, including dome light settings.
- Colors of shape distractors.

By incorporating these randomizations, we increase the diversity of the dataset, making it more robust for training machine learning models.

Getting Started
-------------------

The main script for this tutorial is located at:

``<install_path>/standalone_examples/replicator/infinigen/infinigen_sdg.py``

This script is designed to run as a **Standalone Application**. The default configurations are stored within the script itself in the form of a Python dictionary. You can override these defaults by providing custom configuration files in JSON or YAML format.

Helper functions are located in the ``infinigen_sdg_utils.py`` file. These functions help with loading environments, spawning assets, randomizing object poses, and running physics simulations.

To generate a synthetic dataset using the default configuration, run the following command (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/replicator/infinigen/infinigen_sdg.py

To use a custom configuration file that supports multiple writers and other custom settings, use the `--config` argument:

.. code-block:: bash

    ./python.sh standalone_examples/replicator/infinigen/infinigen_sdg.py \
        --config standalone_examples/replicator/infinigen/config/infinigen_multi_writers_pt.yaml

Implementation
---------------

The following sections provide an overview of the key steps involved in setting up and running the synthetic data generation pipeline.
The complete implementation consists of two files: the main script and a utilities module.

.. raw:: html

    <details closed>
    <summary>Main script</summary>

.. literalinclude:: ../../../source/standalone_examples/replicator/infinigen/infinigen_sdg.py
    :language: python
    :lines: 16-

.. raw:: html

    </details>

.. raw:: html

    <details closed>
    <summary>Utils module</summary>

.. literalinclude:: ../../../source/standalone_examples/replicator/infinigen/infinigen_sdg_utils.py
    :language: python
    :lines: 16-

.. raw:: html

    </details>

Configuration Files
###################

Example configuration files are provided in the ``infinigen/config`` directory. These files allow you to customize various aspects of the simulation, such as the number of captures, assets to include, randomization parameters, and writers to use.

Here's an example of a custom YAML configuration file that demonstrates the use of multiple writers:

.. raw:: html

    <details open>
    <summary>Custom YAML Configuration File</summary>

.. literalinclude:: ../../../source/standalone_examples/replicator/infinigen/config/infinigen_multi_writers_pt.yaml
    :language: yaml
    :lines: 16-

.. raw:: html

    </details>

Configuration Parameters
########################

Here is an explanation of the configuration parameters:

- **environments**:

  - **folders**: List of directories containing the Infinigen environments to be used.
  - **files**: Specific USD files of environments to be loaded.

- **capture**:

  - **total_captures**: Total number of captures to generate.
  - **num_floating_captures_per_env**: Number of captures to take before running the physics simulation (assets are floating).
  - **num_dropped_captures_per_env**: Number of captures to take after the physics simulation (assets have settled).
  - **num_cameras**: Number of cameras to use for capturing images.
  - **resolution**: Resolution of the rendered images (width, height).
  - **disable_render_products**: If `true`, render products are disabled between captures to improve performance.
  - **rt_subframes**: Number of subframes to render for each capture.
  - **path_tracing**: If `true`, uses path tracing for rendering (higher quality, slower).
  - **camera_look_at_target_offset**: Random offset applied when cameras look at target assets.
  - **camera_distance_to_target_range**: Range of distances for cameras from the target assets.
  - **num_scene_lights**: Number of additional lights to add to the scene.

- **writers**: List of writers to use for data output.

  - **type**: Type of writer (e.g., `BasicWriter`, `DataVisualizationWriter`).
  - **kwargs**: Arguments specific to each writer type.

- **labeled_assets**:

  - **auto_label**: Configuration for automatically labeled assets.

    - **num**: Number of assets to spawn.
    - **gravity_disabled_chance**: Probability that an asset will have gravity disabled (will float).
    - **folders** and **files**: Sources for the asset USD files.
    - **regex_replace_pattern** and **regex_replace_repl**: Used to generate labels from file names.

  - **manual_label**: List of assets with manually specified labels.

    - **url**: USD file path of the asset.
    - **label**: Semantic label to assign.
    - **num**: Number of instances to spawn.
    - **gravity_disabled_chance**: Probability of gravity being disabled.

- **distractors**:

  - **shape_distractors**: Configuration for primitive shape distractors.

    - **num**: Number of distractors to spawn.
    - **gravity_disabled_chance**: Probability of gravity being disabled.
    - **types**: List of primitive shapes to use.

  - **mesh_distractors**: Configuration for mesh distractors.

    - **num**: Number of distractors to spawn.
    - **gravity_disabled_chance**: Probability of gravity being disabled.
    - **folders** and **files**: Sources for the distractor USD files.

- **physics**:

  - **gpu_collision_stack_size**: GPU collision stack size in bytes. The PhysX default of 64 MB is insufficient for complex Infinigen scenes with many colliders (environment meshes, distractors, labeled assets). Defaults to 300 MB (``314572800``). If PhysX reports a ``collisionStackSize buffer overflow`` error, increase this value to at least the size recommended in the error message.
  - Additional GPU memory settings can be configured if needed: ``gpu_found_lost_pairs_capacity``, ``gpu_found_lost_aggregate_pairs_capacity``, ``gpu_total_aggregate_pairs_capacity``, ``gpu_max_rigid_contact_count``, ``gpu_max_rigid_patch_count``, ``gpu_heap_capacity``, ``gpu_temp_buffer_capacity``.

- **debug_mode**: When set to `true`, certain elements like ceilings are hidden to provide a better view of the scene during development and debugging.

Loading Infinigen Environments
###############################

We will load environments generated by Infinigen into the Isaac Sim stage. The environments are specified in the configuration file, either through folders or individual files.

.. raw:: html

    <details open>
    <summary>Loading Infinigen Environments</summary>

.. code-block:: python

    def run_sdg(config):
        # Load the config parameters
        env_config = config.get("environments", {})
        env_urls = infinigen_utils.get_usd_paths(
            files=env_config.get("files", []), folders=env_config.get("folders", []), skip_folder_keywords=[".thumbs"]
        )
        if not env_urls:
            print("[SDG] Error: No environment USD files found. Please check the 'environments' config.")
            return
        print(f"[SDG] Found {len(env_urls)} environment(s)")

.. code-block:: python

    # Start the SDG loop
    env_cycle = cycle(env_urls)
    capture_counter = 0
    while capture_counter < total_captures:
        # Load the next environment
        env_url = next(env_cycle)

        # Load the new environment
        print(f"[SDG] Loading environment: {env_url}")
        infinigen_utils.load_env(env_url, prim_path="/Environment")

.. raw:: html

    </details>

In the above code, we use the ``get_usd_paths`` utility function to collect all USD files from the specified folders and files in the configuration. The ``skip_folder_keywords`` parameter filters out directories containing specified keywords (e.g., ``.thumbs`` thumbnail folders). We then cycle through these environments to load them one by one.

Setting Up the Scene
#####################

After loading the environment, we set up the scene by:

- Hiding unnecessary elements (e.g., ceiling) for better visibility if the debugging mode is selected.
- Adding colliders to the environment for physics simulation.
- Loading labeled assets and distractors with physics properties.
- Randomizing asset poses within the working area.

.. raw:: html

    <details open>
    <summary>Loading Assets</summary>

.. code-block:: python

    # Load target assets with auto-labeling (e.g. 002_banana -> banana)
    auto_label_config = labeled_assets_config.get("auto_label", {})
    auto_floating_assets, auto_falling_assets = infinigen_utils.load_auto_labeled_assets(auto_label_config, rng)
    print(f"[SDG] Loaded {len(auto_floating_assets)} floating auto-labeled assets")
    print(f"[SDG] Loaded {len(auto_falling_assets)} falling auto-labeled assets")

    # Load target assets with manual labels
    manual_label_config = labeled_assets_config.get("manual_label", [])
    manual_floating_assets, manual_falling_assets = infinigen_utils.load_manual_labeled_assets(manual_label_config, rng)
    print(f"[SDG] Loaded {len(manual_floating_assets)} floating manual-labeled assets")
    print(f"[SDG] Loaded {len(manual_falling_assets)} falling manual-labeled assets")
    target_assets = auto_floating_assets + auto_falling_assets + manual_floating_assets + manual_falling_assets

    # Load the shape distractors
    shape_distractors_config = distractors_config.get("shape_distractors", {})
    floating_shapes, falling_shapes = infinigen_utils.load_shape_distractors(shape_distractors_config, rng)
    print(f"[SDG] Loaded {len(floating_shapes)} floating shape distractors")
    print(f"[SDG] Loaded {len(falling_shapes)} falling shape distractors")
    shape_distractors = floating_shapes + falling_shapes

    # Load the mesh distractors
    mesh_distractors_config = distractors_config.get("mesh_distractors", {})
    floating_meshes, falling_meshes = infinigen_utils.load_mesh_distractors(mesh_distractors_config, rng)
    print(f"[SDG] Loaded {len(floating_meshes)} floating mesh distractors")
    print(f"[SDG] Loaded {len(falling_meshes)} falling mesh distractors")
    mesh_distractors = floating_meshes + falling_meshes

.. raw:: html

    </details>

.. raw:: html

    <details open>
    <summary>Setting Up the Environment and Randomizing Poses</summary>

.. code-block:: python

        # Setup the environment (add collision, fix lights, etc.) and update the app once to apply the changes
        print(f"[SDG] Setting up the environment")
        infinigen_utils.setup_env(root_path="/Environment", hide_top_walls=debug_mode)
        simulation_app.update()

        # Get the location of the prim above which the assets will be randomized
        working_area_loc = infinigen_utils.get_matching_prim_location(
            match_string="TableDining", root_path="/Environment"
        )

        # Move viewport above the working area to get a top-down view of the scene
        if debug_mode:
            camera_loc = (working_area_loc[0], working_area_loc[1], working_area_loc[2] + 10)
            set_camera_view(eye=np.array(camera_loc), target=np.array(working_area_loc))

        # Get the spawn areas as offseted location ranges from the working area (min_x, min_y, min_z, max_x, max_y, max_z)
        print(f"[SDG] Randomizing {len(target_assets)} target assets around the working area")
        target_loc_range = infinigen_utils.offset_range((-0.5, -0.5, 1, 0.5, 0.5, 1.5), working_area_loc)
        infinigen_utils.randomize_poses(
            target_assets,
            location_range=target_loc_range,
            rotation_range=(0, 360),
            scale_range=(0.95, 1.15),
            rng=rng,
        )

        # Mesh distractors
        print(f"[SDG] Randomizing {len(mesh_distractors)} mesh distractors around the working area")
        mesh_loc_range = infinigen_utils.offset_range((-1, -1, 1, 1, 1, 2), working_area_loc)
        infinigen_utils.randomize_poses(
            mesh_distractors,
            location_range=mesh_loc_range,
            rotation_range=(0, 360),
            scale_range=(0.3, 1.0),
            rng=rng,
        )

        # Shape distractors
        print(f"[SDG] Randomizing {len(shape_distractors)} shape distractors around the working area")
        shape_loc_range = infinigen_utils.offset_range((-1.5, -1.5, 1, 1.5, 1.5, 2), working_area_loc)
        infinigen_utils.randomize_poses(
            shape_distractors,
            location_range=shape_loc_range,
            rotation_range=(0, 360),
            scale_range=(0.01, 0.1),
            rng=rng,
        )

.. raw:: html

    </details>

**Explanation:**

- **Loading Assets**: Assets are loaded once at the beginning of the pipeline. The ``load_auto_labeled_assets`` function automatically generates labels from file names using regex patterns (e.g., ``002_banana`` becomes ``banana``). The ``load_manual_labeled_assets`` function uses explicitly defined labels. Both functions return separate lists of floating (gravity disabled) and falling (gravity enabled) assets.
- **Environment Setup**: The ``setup_env`` utility function adds colliders to the environment and hides top walls if ``debug_mode`` is ``true``. Hiding the top walls provides a clear view of the scene during debugging.
- **Working Area Location**: We use ``get_matching_prim_location`` to find the location of the dining table, which serves as our working area.
- **Randomizing Poses**: The ``randomize_poses`` function takes explicit ``location_range``, ``rotation_range``, and ``scale_range`` parameters. The ``offset_range`` helper function creates location ranges relative to the working area location.

Creating Cameras and Render Products
#######################################

We create multiple cameras to capture images from different viewpoints. Each camera is assigned a render product, which is used by Replicator writers to save data.

.. raw:: html

    <details open>
    <summary>Creating Cameras and Render Products</summary>

.. code-block:: python

    # Create the cameras
    cameras = []
    num_cameras = capture_config.get("num_cameras", 0)
    rep.functional.create.scope(name="Cameras")
    for i in range(num_cameras):
        cam_prim = rep.functional.create.camera(parent="/Cameras", name=f"cam_{i}", clipping_range=(0.25, 1000))
        cameras.append(cam_prim)
    print(f"[SDG] Created {len(cameras)} cameras")

    # Create the render products for the cameras
    render_products = []
    resolution = capture_config.get("resolution", (1280, 720))
    disable_render_products = capture_config.get("disable_render_products", False)
    for cam in cameras:
        rp = rep.create.render_product(cam.GetPath(), resolution, name=f"rp_{cam.GetName()}")
        if disable_render_products:
            rp.hydra_texture.set_updates_enabled(False)
        render_products.append(rp)
    print(f"[SDG] Created {len(render_products)} render products")

.. raw:: html

    </details>

**Explanation:**

- We use Replicator's ``rep.functional.create.scope`` to create an organizational scope for cameras.
- Cameras are created using ``rep.functional.create.camera`` which provides a cleaner API for camera creation with configurable clipping range.
- Render products are created using Replicator's ``create.render_product`` function.
- If ``disable_render_products`` is set to ``true`` in the configuration, we disable the render products during creation. They will be enabled only during capture to save computational resources.

Setting Up Replicator Writers
##############################

We use multiple Replicator writers to collect and store different types of data generated during the simulation. Writers are specified in the configuration file and can include various types such as ``BasicWriter``, ``DataVisualizationWriter``, ``PoseWriter``, and custom writers.

.. raw:: html

    <details open>
    <summary>Setting Up Replicator Writers</summary>

.. code-block:: python

    # Only create the writers if there are render products to attach to
    writers = []
    if render_products:
        for writer_config in writers_config:
            writer = infinigen_utils.setup_writer(writer_config)
            if writer:
                writer.attach(render_products)
                writers.append(writer)
                print(
                    f"[SDG] {writer_config['type']}'s out dir: {writer_config.get('kwargs', {}).get('output_dir', '')}"
                )
    print(f"[SDG] Created {len(writers)} writers")

.. raw:: html

    </details>

**Explanation:**

- Writers are only created if there are render products available to attach to.
- The ``setup_writer`` utility function initializes writers based on the configuration, handling output directory paths and writer-specific arguments.
- Writers are attached to the render products (cameras) to capture data from the specified viewpoints.
- Multiple writers can be used simultaneously to generate different dataset types.

Domain Randomization
#####################

To enhance the diversity of the dataset, we apply domain randomization to various elements in the scene:

- **Randomizing Object Poses**: Positions, orientations, and scales of assets are randomized within specified ranges.
- **Randomizing Lights**: Scene lights are randomized in terms of position, intensity, and color.
- **Randomizing Dome Light**: The environment dome light is randomized to simulate different lighting conditions.
- **Randomizing Shape Distractor Colors**: Colors of shape distractors are randomized to increase visual diversity.

.. raw:: html

    <details open>
    <summary>Creating and Registering Randomizers</summary>

.. code-block:: python

    # Create lights to randomize in the working area
    scene_lights = []
    num_scene_lights = capture_config.get("num_scene_lights", 0)
    for i in range(num_scene_lights):
        light_prim = stage.DefinePrim(f"/Lights/SphereLight_scene_{i}", "SphereLight")
        scene_lights.append(light_prim)
    print(f"[SDG] Created {len(scene_lights)} scene lights")

    # Register replicator randomizers and trigger them once
    print("[SDG] Registering replicator graph randomizers")
    infinigen_utils.register_dome_light_randomizer()
    infinigen_utils.register_shape_distractors_color_randomizer(shape_distractors)

.. raw:: html

    </details>

.. raw:: html

    <details open>
    <summary>Triggering Randomizations</summary>

.. code-block:: python

        print(f"[SDG] Randomizing {len(scene_lights)} scene lights properties and locations around the working area")
        lights_loc_range = infinigen_utils.offset_range((-2, -2, 1, 2, 2, 3), working_area_loc)
        infinigen_utils.randomize_lights(
            scene_lights,
            location_range=lights_loc_range,
            intensity_range=(500, 2500),
            color_range=(0.1, 0.1, 0.1, 0.9, 0.9, 0.9),
            rng=rng,
        )

        print("[SDG] Randomizing dome lights")
        rep.utils.send_og_event(event_name="randomize_dome_lights")

        print("[SDG] Randomizing shape distractor colors")
        rep.utils.send_og_event(event_name="randomize_shape_distractor_colors")

.. raw:: html

    </details>

**Explanation:**

- **Scene Lights**: Additional sphere lights are created using the USD API (``stage.DefinePrim``) and stored for later randomization.
- **Randomizers Registration**: Custom Replicator graph randomizers for dome lights and shape distractor colors are registered once during setup.
- **Light Randomization**: The ``randomize_lights`` utility function randomizes light properties (location, intensity, color) within specified ranges.
- **Event-Based Triggering**: Randomizations are triggered using ``rep.utils.send_og_event`` which sends OmniGraph events to the registered randomizer graphs.

Configuring Physics GPU Memory
################################

Complex Infinigen scenes with many colliders (environment meshes, distractors, labeled assets) can exceed the default PhysX GPU collision stack size (64 MB), causing ``PxGpuDynamicsMemoryConfig::collisionStackSize buffer overflow`` errors and dropped contacts. To prevent this, we configure the PhysX scene GPU memory settings before running any simulation.

.. raw:: html

    <details open>
    <summary>Configuring Physics Scene GPU Memory</summary>

.. code-block:: python

    # Configure the PhysX scene GPU memory settings before running any simulation.
    # This prevents PxGpuDynamicsMemoryConfig::collisionStackSize buffer overflow errors
    # when simulating complex scenes with many colliders (distractors, assets, environment meshes).
    physics_config = config.get("physics", {})
    print("[SDG] Configuring physics scene GPU memory settings")
    infinigen_utils.configure_physics_scene(physics_config)

.. raw:: html

    </details>

**Explanation:**

- The ``configure_physics_scene`` utility function retrieves or creates a PhysX scene prim and sets the ``gpuCollisionStackSize`` attribute (and optionally other GPU memory attributes) based on values from the configuration.
- The default collision stack size is set to 300 MB (``314572800`` bytes), which provides a comfortable margin above the ~272 MB typically required by Infinigen scenes. This value can be overridden via the ``physics.gpu_collision_stack_size`` configuration parameter.

Running Physics Simulation
############################

We run physics simulations to allow objects to interact naturally within the environment. This involves:

- Running a short simulation to resolve any initial overlaps.
- Capturing images before objects have settled (floating captures).
- Running a longer simulation to let objects fall and settle.
- Capturing images after objects have settled (dropped captures).

.. raw:: html

    <details open>
    <summary>Running Physics Simulation</summary>

.. code-block:: python

        # Run the physics simulation for a few frames to solve any collisions
        print("[SDG] Fixing collisions through physics simulation")
        simulation_app.update()
        infinigen_utils.run_simulation(num_frames=4, render=True)

        # Check if the render products need to be enabled for the capture
        if disable_render_products:
            for rp in render_products:
                rp.hydra_texture.set_updates_enabled(True)

        # Check if the render mode needs to be switched to path tracing for the capture
        if use_path_tracing:
            print("[SDG] Switching to PathTracing render mode")
            carb.settings.get_settings().set("/rtx/rendermode", "PathTracing")

        # Capture frames with the objects in the air
        for i in range(num_floating_captures_per_env):
            # Check if the total captures have been reached
            if capture_counter >= total_captures:
                break
            # Randomize the camera poses
            print(f"[SDG] Randomizing camera poses ({len(cameras)} cameras)")
            infinigen_utils.randomize_camera_poses(
                cameras, target_assets, camera_distance_to_target_range, polar_angle_range=(0, 75), rng=rng
            )
            print(
                f"[SDG] Capturing floating assets {i+1}/{num_floating_captures_per_env} (total: {capture_counter+1}/{total_captures})"
            )
            rep.orchestrator.step(rt_subframes=rt_subframes, delta_time=0.0)
            capture_counter += 1

        # Check if the render products need to be disabled until the next capture
        if disable_render_products:
            for rp in render_products:
                rp.hydra_texture.set_updates_enabled(False)

        # Check if the render mode needs to be switched back to raytracing until the next capture
        if use_path_tracing:
            carb.settings.get_settings().set("/rtx/rendermode", "RealTimePathTracing")

        print("[SDG] Running the simulation")
        infinigen_utils.run_simulation(num_frames=200, render=False)

        # Check if the render products need to be enabled for the capture
        if disable_render_products:
            for rp in render_products:
                rp.hydra_texture.set_updates_enabled(True)

        # Check if the render mode needs to be switched to path tracing for the capture
        if use_path_tracing:
            carb.settings.get_settings().set("/rtx/rendermode", "PathTracing")

        for i in range(num_dropped_captures_per_env):
            # Check if the total captures have been reached
            if capture_counter >= total_captures:
                break
            # Spawn the cameras with a smaller polar angle to have mostly a top-down view of the objects
            print("[SDG] Randomizing camera poses")
            infinigen_utils.randomize_camera_poses(
                cameras,
                target_assets,
                distance_range=camera_distance_to_target_range,
                polar_angle_range=(0, 45),
                rng=rng,
            )
            print(
                f"[SDG] Capturing dropped assets {i+1}/{num_dropped_captures_per_env} (total: {capture_counter+1}/{total_captures})"
            )
            rep.orchestrator.step(rt_subframes=rt_subframes, delta_time=0.0)
            capture_counter += 1

        # Check if the render products need to be disabled until the next capture
        if disable_render_products:
            for rp in render_products:
                rp.hydra_texture.set_updates_enabled(False)

        # Check if the render mode needs to be switched back to raytracing until the next capture
        if use_path_tracing:
            carb.settings.get_settings().set("/rtx/rendermode", "RealTimePathTracing")

.. raw:: html

    </details>

**Explanation:**

- **Initial Simulation**: A short simulation resolves any initial overlaps among assets.
- **Render Product Management**: Render products are enabled only during capture and disabled during simulation to save computational resources.
- **Path Tracing**: When enabled, the render mode switches to PathTracing for higher quality captures and back to RealTimePathTracing during simulation.
- **Floating Captures**: We capture images while assets are still floating, with cameras positioned using larger polar angles (0-75°) for varied viewpoints.
- **Physics Simulation**: A longer simulation (200 frames) allows assets to fall and settle according to physics, without rendering for efficiency.
- **Dropped Captures**: We capture images after assets have settled, using smaller polar angles (0-45°) for mostly top-down views.
- **Capture Counter**: Each capture increments the counter, with early exit checks to respect the total capture limit.

Capturing Data
################

We capture data at specified intervals, ensuring that we have a diverse set of images covering various object states and viewpoints.

- **Randomizing Camera Poses**: Cameras are positioned randomly around target assets to capture images from different angles.
- **Triggering Randomizations**: Randomizations are applied at each environment to ensure diversity.

.. raw:: html

    <details open>
    <summary>Capturing Data Loop</summary>

.. code-block:: python

    # Configure PhysX GPU memory once before the loop (the /PhysicsScene prim persists across environments)
    physics_config = config.get("physics", {})
    infinigen_utils.configure_physics_scene(physics_config)

    # Start the SDG loop
    env_cycle = cycle(env_urls)
    capture_counter = 0
    while capture_counter < total_captures:
        # Load the next environment
        env_url = next(env_cycle)

        # Load the new environment
        print(f"[SDG] Loading environment: {env_url}")
        infinigen_utils.load_env(env_url, prim_path="/Environment")

        # Setup the environment (add collision, fix lights, etc.)
        infinigen_utils.setup_env(root_path="/Environment", hide_top_walls=debug_mode)
        simulation_app.update()

        # Get the location of the working area (e.g., dining table)
        working_area_loc = infinigen_utils.get_matching_prim_location(
            match_string="TableDining", root_path="/Environment"
        )

        # Randomize poses for target assets, mesh distractors, shape distractors
        # ... (randomization code as shown in previous snippets)

        # Trigger graph-based randomizers
        rep.utils.send_og_event(event_name="randomize_dome_lights")
        rep.utils.send_og_event(event_name="randomize_shape_distractor_colors")

        # Run physics simulation and capture floating assets
        infinigen_utils.run_simulation(num_frames=4, render=True)
        for i in range(num_floating_captures_per_env):
            if capture_counter >= total_captures:
                break
            infinigen_utils.randomize_camera_poses(cameras, target_assets, ...)
            rep.orchestrator.step(rt_subframes=rt_subframes, delta_time=0.0)
            capture_counter += 1

        # Run longer simulation for dropped assets
        infinigen_utils.run_simulation(num_frames=200, render=False)
        for i in range(num_dropped_captures_per_env):
            if capture_counter >= total_captures:
                break
            infinigen_utils.randomize_camera_poses(cameras, target_assets, ...)
            rep.orchestrator.step(rt_subframes=rt_subframes, delta_time=0.0)
            capture_counter += 1

    # Cleanup: wait for data, detach writers, destroy render products
    rep.orchestrator.wait_until_complete()
    for writer in writers:
        writer.detach()
    for rp in render_products:
        rp.destroy()
    print(f"[SDG] Finished, captured {capture_counter * num_cameras} frames")

.. raw:: html

    </details>

**Explanation:**

- We loop through the environments using ``cycle`` to repeat environments if needed.
- The ``capture_counter`` is incremented inside each capture loop (floating and dropped), not at the end of the environment iteration.
- After loading each environment, we call ``simulation_app.update()`` to apply changes before proceeding.
- Randomizations are triggered using OmniGraph events for each environment.
- After all captures are complete, we wait for the data to be written, then properly cleanup by detaching writers and destroying render products.

Summary
-------

In this tutorial, you learned how to generate synthetic datasets using Infinigen environments in NVIDIA Omniverse Isaac Sim. The key steps included:

1. **Generating Infinigen Environments**: Using Infinigen to create photorealistic indoor environments.
2. **Understanding Configuration Parameters**: Customizing the simulation and data generation process through configuration files.
3. **Setting Up the Simulation**: Running Isaac Sim as a standalone application and loading Infinigen environments.
4. **Spawning Assets**: Using the Isaac Sim API to place labeled assets and distractors in the environment.
5. **Configuring the SDG Pipeline**: Creating cameras, render products, and using multiple Replicator writers to generate different datasets.
6. **Applying Domain Randomization**: Enhancing dataset diversity through randomizations.
7. **Running Physics Simulations**: Simulating object interactions for realistic scenes.
8. **Capturing and Saving Data**: Collecting images and annotations using multiple Replicator writers.

By following this tutorial, you now have the foundation to create rich, diverse synthetic datasets using procedurally generated environments and advanced randomization techniques.

Next Steps
----------

With the generated datasets, you can proceed to train machine learning models for tasks like object detection, segmentation, and pose estimation. Consider exploring the `TAO Toolkit <https://docs.nvidia.com/tao/>`_ for training workflows and pre-trained models.

