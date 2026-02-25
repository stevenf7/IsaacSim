..
   Copyright (c) 2022-2024, NVIDIA CORPORATION. All rights reserved.
   NVIDIA CORPORATION and its licensors retain all intellectual property
   and proprietary rights in and to this software, related documentation
   and any modifications thereto. Any use, reproduction, disclosure or
   distribution of this software and related documentation without an express
   license agreement from NVIDIA CORPORATION is strictly prohibited.



.. _isaac_sim_app_tutorial_replicator_scene_based_sdg:

==========================================
Scene Based Synthetic Dataset Generation
==========================================


This tutorial illustrates the process of generating synthetic datasets using the :doc:`omni.replicator <extensions:ext_replicator>` extension. The resulting data is stored `offline` (on disk), making it readily available for training deep neural networks. The examples can be executed within the |isaac-sim_short| Python :ref:`standalone <standalone-application>` environment. The example uses |isaac-sim_short| and Replicator to create synthetic datasets offline (on disk) for the training of machine learning models.

In this tutorial you:

* Utilize and set up external customizable config files (YAML/JSON) to adjust simulation and scenario parameters
* Load custom environments
* Spawn assets using the |isaac-sim_short| API
* Run randomized physics simulations
* Register various Replicator randomization :doc:`graphs <extensions:ext_omnigraph>`
* Create cameras and render products with the Replicator API
* Use Replicator writers to save data to disk

Prerequisites
-------------------

* Familiarity with the :doc:`omni.replicator <extensions:ext_replicator>` extension, including its :doc:`annotators <extensions:ext_replicator/annotators_details>` and :doc:`writers <extensions:ext_replicator/writer_examples>`.
* Basic understanding of |isaac-sim_short|'s :ref:`isaac_sim_glossary_stage` and :ref:`isaac_sim_glossary_world` concepts, further explained in the :ref:`Hello World <isaac_sim_app_tutorial_core_hello_world>` tutorial.
* Running simulations as :ref:`Standalone Applications <standalone-application>` or via the :ref:`Script Editor <script-editor>`.
* Familiarity with Replicator :doc:`randomizers <extensions:ext_replicator/randomizer_details>` and :doc:`OmniGraph <extensions:ext_omnigraph>` for a better understanding of the randomization pipeline.

Scenario
-------------------

By default, the scenario is executed in a warehouse environment. Within this setting, a forklift is randomly placed in a designated area. Based on the forklift's position, a pallet is placed in front of it at a randomized distance. Using Replicator's ``scatter_2d`` randomization function with the collision check argument ``check_for_collisions`` set to ``True``, the pallet is scattered with boxes, ensuring the boxes do not self-collide. The scatter graph node randomly scatters the boxes in each capture frame. Additionally, a traffic cone is randomly positioned at one of the bottom corners of the forklift's oriented bounding box (OBB). Before the synthetic data generation (SDG) pipeline starts, a short physics simulation is executed, during which several boxes are dropped onto a pallet situated behind the forklift.

.. image:: /images/isaac_tutorial_replicator_offline_data.png
    :align: center

Three camera views are used for the synthetic data generation (SDG). The first (``top_view_cam``) offers a top-down view of the scenario (left), the second (``pallet_cam``) captures a randomized view of the boxes scattered on the pallet (center), and the third is overlooking the pallet from the driver's place in the forklift using various heights (right).
The data is collected using Replicator writers with configurable backends. The default setup uses ``BasicWriter`` with a ``DiskBackend``. The writer's config parameters are loaded from the ``writer_config`` entry and used to initialize the writer with annotators including rgb, semantic_segmentation, and bounding_box_3d. The output directory is specified in ``backend_params``, which by default is ``<working_dir>/_out_scene_based_sdg``.

Getting Started
-------------------

The main script of the tutorial is located at ``<install_path>/standalone_examples/replicator/scene_based_sdg/scene_based_sdg.py`` and it is set to run as a standalone application. The default configurations are stored in the script itself in the form of a Python dictionary, there is no need to provide a config file.

To overwrite the default configuration parameters, you can provided custom config files as a command-line argument for the script by using ``--config <path/to/file.json/yaml>``. Example config files are stored in ``scene_based_sdg/config/*``. In the provided examples, the configuration files serve as templates to illustrate and showcase the configurability of the script.

Helper functions are located in the ``scene_based_sdg_utils.py`` file.

To generate a synthetic dataset, run the following command for the Standalone Application (on Windows use ``python.bat`` instead of ``python.sh``):

.. code-block:: bash

    ./python.sh standalone_examples/replicator/scene_based_sdg/scene_based_sdg.py


Implementation
-------------- 

The following section provides an implementation overview of the script. It includes details regarding the configuration parameters, scene generation helper functions, randomizations (|isaac-sim_short| and Replicator), and data capture loop. As standalone example the script is split into two files: the main script and a utilities module.

.. tab-set::

    .. tab-item:: Script Editor

        .. raw:: html

            <details closed>
            <summary>Utils module and main script</summary>

        .. literalinclude:: ../snippets/replicator_tutorials/tutorial_replicator_scene_based_sdg/scene_based_sdg_script_editor.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

    .. tab-item:: Standalone Application

        .. raw:: html

            <details closed>
            <summary>Main script</summary>

        .. literalinclude:: ../../../source/standalone_examples/replicator/scene_based_sdg/scene_based_sdg.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

        .. raw:: html

            <details closed>
            <summary>Utils module</summary>

        .. literalinclude:: ../../../source/standalone_examples/replicator/scene_based_sdg/scene_based_sdg_utils.py
            :language: python
            :lines: 16-

        .. raw:: html

            </details>

Config Scenarios
-------------------

The following provides details about the various config scenarios:

.. tab-set::

    .. tab-item:: Built-in

        Without an explicit config file, the script uses the default parameters stored in the script itself. The default parameters are the following:

        .. raw:: html

            <details open>
            <summary>Built-in (default) Config</summary>

        .. code-block:: python

            config = {
                "launch_config": {
                    "renderer": "RealTimePathTracing",
                    "headless": False,
                },
                "resolution": [512, 512],
                "rt_subframes": 32,
                "num_frames": 10,
                "env_url": "/Isaac/Environments/Simple_Warehouse/full_warehouse.usd",
                "writer": "BasicWriter",
                "backend_type": "DiskBackend",
                "backend_params": {
                    "output_dir": "_out_scene_based_sdg",
                },
                "writer_config": {
                    "rgb": True,
                    "bounding_box_2d_tight": True,
                    "semantic_segmentation": True,
                    "distance_to_image_plane": True,
                    "bounding_box_3d": True,
                    "occlusion": True,
                },
                "clear_previous_semantics": True,
                "forklift": {
                    "url": "/Isaac/Props/Forklift/forklift.usd",
                    "class": "forklift",
                },
                "cone": {
                    "url": "/Isaac/Environments/Simple_Warehouse/Props/S_TrafficCone.usd",
                    "class": "traffic_cone",
                },
                "pallet": {
                    "url": "/Isaac/Environments/Simple_Warehouse/Props/SM_PaletteA_01.usd",
                    "class": "pallet",
                },
                "cardbox": {
                    "url": "/Isaac/Environments/Simple_Warehouse/Props/SM_CardBoxD_04.usd",
                    "class": "cardbox",
                },
                "close_app_after_run": True,
            }

        .. raw:: html

            </details>

        The following command runs the script with the default parameters:

        .. code-block:: bash

            ./python.sh standalone_examples/replicator/scene_based_sdg/scene_based_sdg.py

    .. tab-item:: Basic Writer

        Using the ``config_basic_writer.yaml`` config file explictly chooses ``BasicWriter`` with the given ``writer_config`` configurations. It also changes the environment to ``/Isaac/Environments/Grid/default_environment.usd``.

        .. raw:: html

            <details open>
            <summary>Custom YAML Config</summary>

        .. literalinclude:: ../../../source/standalone_examples/replicator/scene_based_sdg/config/config_basic_writer.yaml
            :language: yaml
            :lines: 16-

        .. raw:: html

            </details>

        The following command runs the script with the custom parameters:

        .. code-block:: bash

            ./python.sh standalone_examples/replicator/scene_based_sdg/scene_based_sdg.py \
                --config standalone_examples/replicator/scene_based_sdg/config/config_basic_writer.yaml

    .. tab-item:: Default Writer

        The ``config_default_writer.json`` uses the default writer (which is still the ``BasicWriter``) and changes the ``writer_config`` values to **rgb** and **instance_segmentation** annotators.

        .. raw:: html

            <details open>
            <summary>Custom JSON Config</summary>

        .. literalinclude:: ../../../source/standalone_examples/replicator/scene_based_sdg/config/config_default_writer.json
            :language: json

        .. raw:: html

            </details>

        The following command runs the script with the custom parameters:

        .. code-block:: bash

            ./python.sh standalone_examples/replicator/scene_based_sdg/scene_based_sdg.py \
                --config standalone_examples/replicator/scene_based_sdg/config/config_default_writer.json

    .. tab-item:: Kitti Writer

        The ``config_kitti_writer.yaml`` config file uses ``KittiWriter`` with the given ``writer_config`` configurations.

        .. raw:: html

            <details open>
            <summary>Custom YAML Config using KittiWriter</summary>

        .. literalinclude:: ../../../source/standalone_examples/replicator/scene_based_sdg/config/config_kitti_writer.yaml
            :language: yaml
            :lines: 16-

        .. raw:: html

            </details>

        The following command runs the script with the custom parameters:

        .. code-block:: bash

            ./python.sh standalone_examples/replicator/scene_based_sdg/scene_based_sdg.py \
                --config standalone_examples/replicator/scene_based_sdg/config/config_kitti_writer.yaml


    .. tab-item:: Coco Writer

        The ``config_coco_writer.yaml`` config file uses ``CocoWriter`` with the given ``writer_config`` configurations.

        .. raw:: html

            <details open>
            <summary>Custom YAML Config using CocoWriter</summary>

        .. literalinclude:: ../../../source/standalone_examples/replicator/scene_based_sdg/config/config_coco_writer.yaml
            :language: yaml
            :lines: 16-

        .. raw:: html

            </details>

        The following command runs the script with the custom parameters:

        .. code-block:: bash

            ./python.sh standalone_examples/replicator/scene_based_sdg/scene_based_sdg.py \
                --config standalone_examples/replicator/scene_based_sdg/config/config_coco_writer.yaml


Loading the Environment
-----------------------------

The environment is a USD stage. Use ``get_assets_root_path_async`` to get the path to the nucleus server and then load the environment using ``omni.usd.get_context().open_stage()``.


.. raw:: html

    <details open>
    <summary>Load the Environment</summary>

.. code-block:: python

    # Get assets root path from nucleus server
    assets_root_path = get_assets_root_path()
    if assets_root_path is None:
        carb.log_error("Could not get nucleus server path, closing application..")
        simulation_app.close()

    # Load environment stage
    print(f"[SDG] Loading Stage {config['env_url']}")
    if not open_stage(assets_root_path + config["env_url"]):
        carb.log_error(f"Could not open stage{config['env_url']}, closing application..")
        simulation_app.close()

    # Initialize randomization
    rep.set_global_seed(42)
    rng = np.random.default_rng(42)

    # Configure replicator for manual triggering
    rep.orchestrator.set_capture_on_play(False)

    # Set DLSS to Quality mode for best SDG results
    carb.settings.get_settings().set("rtx/post/dlss/execMode", 2)

    # Clear previous semantic labels
    if config["clear_previous_semantics"]:
        for prim in get_current_stage().Traverse():
            remove_all_labels(prim, include_descendants=True)

.. raw:: html

    </details>

Creating the Cameras and the Writer
-------------------------------------

The example provides two ways (Replicator and |isaac-sim_short| API) of creating cameras ``rep.create.camera`` and ``prims.create_prim``. ``prims.create_prim``is used as render products to generate the data. The created render products are attached to the built-in ``BasicWriter`` to collect the data from the selected annotators (rgb, semantic_segmentation, bounding_box_3d) and to write it to the given output path. Use ``rep.get.prim_at_path``to access ``driver_cam_prim`` wrapped in an OmniGraph node so that it can be randomized by each step of the randomization graph generated by Replicator.


The cameras used in the examples are created using ``rep.functional.create.camera``, which create camera prims used by render products.

.. raw:: html

    <details open>
    <summary>Cameras</summary>

.. code-block:: python

    # Create cameras
    rep.functional.create.scope(name="Cameras", parent="/SDG")
    driver_cam = rep.functional.create.camera(
        focus_distance=400.0, focal_length=24.0, clipping_range=(0.1, 10000000.0), name="DriverCam", parent="/SDG/Cameras"
    )
    pallet_cam = rep.functional.create.camera(name="PalletCam", parent="/SDG/Cameras")
    top_view_cam = rep.functional.create.camera(clipping_range=(6.0, 1000000.0), name="TopCam", parent="/SDG/Cameras")

.. raw:: html

    </details>

From the cameras, render products are created and disabled until the SDG pipeline starts to improve performance by avoiding unnecessary rendering. The writer setup is handled by a helper function that supports optional backend configuration for flexible output handling.

.. raw:: html

    <details open>
    <summary>Writer and Render Products</summary>

.. code-block:: python

    # Setup render products
    resolution = config.get("resolution", (512, 512))
    forklift_rp = rep.create.render_product(top_view_cam, resolution, name="TopView")
    driver_rp = rep.create.render_product(driver_cam, resolution, name="DriverView")
    pallet_rp = rep.create.render_product(pallet_cam, resolution, name="PalletView")

    render_products = [forklift_rp, driver_rp, pallet_rp]
    for render_product in render_products:
        render_product.hydra_texture.set_updates_enabled(False)

    # Initialize writer and attach to render products
    writer = scene_based_sdg_utils.setup_writer(config)
    if not writer:
        carb.log_error("[SDG] Failed to setup writer, closing application.")
        simulation_app.close()

    writer.attach(render_products)

    for render_product in render_products:
        render_product.hydra_texture.set_updates_enabled(True)

The ``setup_writer`` helper function handles writer initialization with optional backend support:

.. code-block:: python

    def setup_writer(config: dict) -> rep.Writer | None:
        """Setup and initialize writer with optional backend support and error handling."""

        def normalize_output_dir(params):
            """Convert relative output_dir to absolute path."""
            if "output_dir" in params and not os.path.isabs(params["output_dir"]):
                params["output_dir"] = os.path.join(os.getcwd(), params["output_dir"])

        # Get writer from registry
        writer_type = config.get("writer", "BasicWriter")
        if writer_type not in rep.WriterRegistry.get_writers():
            carb.log_error(f"[SDG] Writer type '{writer_type}' not found in registry.")
            return None

        writer = rep.WriterRegistry.get(writer_type)
        writer_kwargs = dict(config.get("writer_config", {}))
        normalize_output_dir(writer_kwargs)

        # Initialize backend if specified
        backend_type = config.get("backend_type")
        backend = None
        if backend_type:
            try:
                backend = rep.backends.get(backend_type)
            except Exception as e:
                carb.log_error(f"[SDG] Backend '{backend_type}' not found: {e}")
                return None

            backend_params = dict(config.get("backend_params", {}))
            normalize_output_dir(backend_params)

            try:
                print(f"[SDG] Backend: {backend_type} | Params: {backend_params}")
                backend.initialize(**backend_params)
            except TypeError as e:
                carb.log_error(f"[SDG] Invalid backend params: {e}")
                return None

        # Initialize writer
        if "output_dir" in writer_kwargs:
            print(f"[SDG] Output: {writer_kwargs['output_dir']}")

        backend_info = f" + {backend_type}" if backend else ""
        print(f"[SDG] Writer: {writer_type}{backend_info} | Config: {writer_kwargs}")

        try:
            if backend:
                writer.initialize(backend=backend, **writer_kwargs)
            else:
                writer.initialize(**writer_kwargs)
        except TypeError as e:
            carb.log_error(f"[SDG] Invalid writer params: {e}")
            return None

        return writer

.. raw:: html

    </details>

Domain Randomization
----------------------

The following snippet provides examples of various randomization possibilities using |isaac-sim_short| and Replicator API. The example uses a seeded random number generator (``numpy.random.Generator``) for reproducible randomization. It starts by spawning a forklift using the |isaac-sim_short| API to a randomly generated pose. It then uses the forklift pose to place a pallet in front of it within the bounds of a random distance. Cardboxes and a traffic cone are also created upfront for later randomization.

.. raw:: html

    <details open>
    <summary>Isaac Sim API Asset Spawning</summary>

.. code-block:: python

    # Spawn forklift at random pose
    forklift_prim = prims.create_prim(
        prim_path="/SDG/Forklift",
        position=(rng.uniform(-20, -2), rng.uniform(-1, 3), 0),
        orientation=euler_angles_to_quat([0, 0, rng.uniform(0, math.pi)]),
        usd_path=assets_root_path + config["forklift"]["url"],
        semantic_label=config["forklift"]["class"],
    )

    # Spawn pallet in front of forklift with random offset
    forklift_tf = omni.usd.get_world_transform_matrix(forklift_prim)
    pallet_offset_tf = Gf.Matrix4d().SetTranslate(Gf.Vec3d(0, rng.uniform(-1.8, -1.2), 0))
    pallet_pos = (pallet_offset_tf * forklift_tf).ExtractTranslation()
    forklift_quat = forklift_tf.ExtractRotationQuat()
    forklift_quat_xyzw = (forklift_quat.GetReal(), *forklift_quat.GetImaginary())

    pallet_prim = prims.create_prim(
        prim_path="/SDG/Pallet",
        position=pallet_pos,
        orientation=forklift_quat_xyzw,
        usd_path=assets_root_path + config["pallet"]["url"],
        semantic_label=config["pallet"]["class"],
    )

    # Create cardboxes for pallet scattering
    cardboxes = []
    for i in range(5):
        cardbox = prims.create_prim(
            prim_path=f"/SDG/CardBox_{i}",
            usd_path=assets_root_path + config["cardbox"]["url"],
            semantic_label=config["cardbox"]["class"],
        )
        cardboxes.append(cardbox)

    # Create traffic cone for corner placement
    cone = prims.create_prim(
        prim_path="/SDG/Cone",
        usd_path=assets_root_path + config["cone"]["url"],
        semantic_label=config["cone"]["class"],
    )

.. raw:: html

    </details>

The new Replicator API uses ``rep.functional`` for direct randomization without graph registration. A scatter plane is created using a helper function, and boxes are scattered directly using ``rep.functional.randomizer.scatter_2d`` in the SDG loop. Material randomization is handled through a separate graph-based randomizer.

.. raw:: html

    <details open>
    <summary>Scatter Plane Setup</summary>

.. code-block:: python

    def create_scatter_plane_for_prim(
        prim: Usd.Prim, prim_tf: Gf.Matrix4d, parent_path: str, scale_factor: float = 0.8, visible: bool = False
    ) -> Usd.Prim:
        """Create scatter plane sized and aligned to prim surface."""
        bb_cache = create_bbox_cache()
        prim_bbox = bb_cache.ComputeLocalBound(prim)
        prim_bbox.Transform(prim_tf)
        prim_size = prim_bbox.GetRange().GetSize()

        prim_quat = prim_tf.ExtractRotation().GetQuaternion()
        prim_quat_xyzw = (prim_quat.GetReal(), *prim_quat.GetImaginary())
        prim_rotation_deg = quat_to_euler_angles(np.array(prim_quat_xyzw), degrees=True)

        prim_pos = prim_tf.ExtractTranslation()
        scatter_plane_scale = (prim_size[0] * scale_factor, prim_size[1] * scale_factor, 1)
        scatter_plane_pos = prim_pos + Gf.Vec3d(0, 0, prim_size[2])

        scatter_plane = rep.functional.create.plane(
            scale=scatter_plane_scale,
            position=tuple(scatter_plane_pos),
            rotation=tuple(prim_rotation_deg),
            visible=visible,
            parent=parent_path,
        )

        return scatter_plane

.. raw:: html

    </details>

Material randomization for cardboxes is registered as a graph-based randomizer triggered by custom events:

.. raw:: html

    <details open>
    <summary>Material Randomization Graph</summary>

.. code-block:: python

    def register_cardboxes_materials_graph_randomizer(
        cardboxes: list[Usd.Prim], cardbox_material_urls: list[str], event_name: str
    ) -> None:
        """Register graph randomizer to apply random materials to cardbox meshes."""
        cardbox_mesh_paths = []
        for cardbox in cardboxes:
            meshes = [child for child in cardbox.GetChildren() if child.IsA(UsdGeom.Mesh)]
            cardbox_mesh_paths.extend([mesh.GetPrimPath() for mesh in meshes])

        with rep.trigger.on_custom_event(event_name):
            cardbox_mesh_group_node = rep.create.group(cardbox_mesh_paths)
            with cardbox_mesh_group_node:
                rep.randomizer.materials(cardbox_material_urls)

.. raw:: html

    </details>

The traffic cone is positioned at one of the forklift's bounding box corners. A helper function calculates the corner positions:

.. raw:: html

    <details open>
    <summary>Cone Placement Setup</summary>

.. code-block:: python

    def setup_cone_placement_corners(
        forklift_prim: Usd.Prim, bb_cache=None, scale_factor: float = 1.3
    ) -> tuple[list[list[float]], tuple[float, float, float]]:
        """Calculate forklift OBB corners for cone placement, returns (corner_positions, rotation_degrees)."""
        if bb_cache is None:
            bb_cache = create_bbox_cache()

        forklift_obb_center, forklift_obb_axes, forklift_obb_extent = compute_obb(bb_cache, forklift_prim.GetPrimPath())
        enlarged_extent = (
            forklift_obb_extent[0] * scale_factor,
            forklift_obb_extent[1] * scale_factor,
            forklift_obb_extent[2],
        )
        forklift_obb_corners = get_obb_corners(forklift_obb_center, forklift_obb_axes, enlarged_extent)

        cone_placement_corners = [
            forklift_obb_corners[0].tolist(),
            forklift_obb_corners[2].tolist(),
            forklift_obb_corners[4].tolist(),
            forklift_obb_corners[6].tolist(),
        ]

        forklift_obb_quat = Gf.Matrix3d(forklift_obb_axes).ExtractRotation().GetQuaternion()
        forklift_obb_quat_xyzw = (forklift_obb_quat.GetReal(), *forklift_obb_quat.GetImaginary())
        forklift_rotation_deg = quat_to_euler_angles(np.array(forklift_obb_quat_xyzw), degrees=True)

        return cone_placement_corners, forklift_rotation_deg

.. raw:: html

    </details>

Light randomization is registered as a graph-based randomizer triggered by custom events:

.. raw:: html

    <details open>
    <summary>Light Randomization Graph</summary>

.. code-block:: python

    def register_lights_graph_randomizer(forklift_prim: Usd.Prim, pallet_prim: Usd.Prim, event_name: str) -> None:
        """Register graph randomizer to create sphere lights with varying color, intensity, and position."""
        bb_cache = create_bbox_cache()
        combined_bounds = compute_combined_aabb(bb_cache, [forklift_prim.GetPrimPath(), pallet_prim.GetPrimPath()])
        light_pos_min = (combined_bounds[0], combined_bounds[1], 6)
        light_pos_max = (combined_bounds[3], combined_bounds[4], 7)

        with rep.trigger.on_custom_event(event_name):
            rep.create.light(
                light_type="Sphere",
                color=rep.distribution.uniform((0.2, 0.1, 0.1), (0.9, 0.8, 0.8)),
                intensity=rep.distribution.uniform(2000, 4000),
                position=rep.distribution.uniform(light_pos_min, light_pos_max),
                scale=rep.distribution.uniform(1, 4),
                count=3,
            )

.. raw:: html

    </details>

Similar to the above examples, Replicator has support for many other randomizations. For more information, see Replicator's :doc:`randomizer examples tutorials <extensions:ext_replicator/randomizer_details>`.

Camera bounds are calculated using a helper function to determine the randomization ranges:

.. raw:: html

    <details open>
    <summary>Camera Bounds Setup</summary>

.. code-block:: python

    def setup_camera_bounds(
        pallet_prim: Usd.Prim, forklift_prim: Usd.Prim, pallet_tf: Gf.Matrix4d, forklift_tf: Gf.Matrix4d
    ) -> dict[str, dict[str, tuple[float, float, float]]]:
        """Calculate camera randomization bounds for pallet, top view, and driver cameras."""
        pallet_pos = pallet_tf.ExtractTranslation()
        pallet_cam_bounds = {
            "min": (pallet_pos[0] - 2, pallet_pos[1] - 2, 2),
            "max": (pallet_pos[0] + 2, pallet_pos[1] + 2, 4),
        }

        forklift_pos = forklift_tf.ExtractTranslation()
        top_cam_bounds = {
            "min": (forklift_pos[0], forklift_pos[1], 9),
            "max": (forklift_pos[0], forklift_pos[1], 11),
        }

        driver_cam_pos = forklift_pos + Gf.Vec3d(0.0, 0.0, 1.9)
        driver_cam_bounds = {
            "min": (driver_cam_pos[0], driver_cam_pos[1], driver_cam_pos[2] - 0.25),
            "max": (driver_cam_pos[0], driver_cam_pos[1], driver_cam_pos[2] + 0.25),
        }

        return {
            "pallet_cam": pallet_cam_bounds,
            "top_cam": top_cam_bounds,
            "driver_cam": driver_cam_bounds,
        }

.. raw:: html

    </details>

After setting up the randomizers and before running the data collection, a short physics simulation is run. The example drops several stacked boxes on a pallet behind the forklift using ``SimulationManager`` and the experimental ``GeomPrim`` and ``RigidPrim`` classes.

.. raw:: html

    <details open>
    <summary>Isaac Sim Simulation</summary>

.. code-block:: python

    def simulate_falling_objects(
        forklift_prim: Usd.Prim,
        assets_root_path: str,
        config: dict,
        max_sim_steps: int = 250,
        num_boxes: int = 8,
        rng: np.random.Generator | None = None,
    ) -> None:
        """Run physics simulation to drop boxes on pallet near forklift."""
        if rng is None:
            rng = np.random.default_rng()

        # Spawn pallet at random position relative to forklift
        forklift_transform = omni.usd.get_world_transform_matrix(forklift_prim)
        sim_pallet_offset = Gf.Matrix4d().SetTranslate(Gf.Vec3d(rng.uniform(-1, 1), rng.uniform(-4, -3.6), 0))
        sim_pallet_position = (sim_pallet_offset * forklift_transform).ExtractTranslation()
        sim_pallet_rotation = euler_angles_to_quat([0, 0, rng.uniform(0, math.pi)])

        sim_pallet = prims.create_prim(
            prim_path="/World/SimulatedPallet",
            position=sim_pallet_position,
            orientation=sim_pallet_rotation,
            usd_path=assets_root_path + config["pallet"]["url"],
            semantic_label=config["pallet"]["class"],
        )
        sim_pallet_geom = GeomPrim(f"{str(sim_pallet.GetPrimPath())}/.*", apply_collision_apis=True)
        sim_pallet_geom.set_collision_approximations("boundingCube")

        # Spawn boxes stacked above pallet
        bbox_cache = create_bbox_cache()
        current_height = bbox_cache.ComputeLocalBound(sim_pallet).GetRange().GetSize()[2] * 1.1

        sim_box_rigid_prims = []
        for box_index in range(num_boxes):
            box_xy_offset = Gf.Vec3d(rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2), current_height)
            sim_box = prims.create_prim(
                prim_path=f"/World/SimulatedCardbox_{box_index}",
                position=sim_pallet_position + box_xy_offset,
                orientation=sim_pallet_rotation,
                usd_path=assets_root_path + config["cardbox"]["url"],
                semantic_label=config["cardbox"]["class"],
            )
            current_height += bbox_cache.ComputeLocalBound(sim_box).GetRange().GetSize()[2] * 1.1

            sim_box_geom = GeomPrim(f"{str(sim_box.GetPrimPath())}/.*", apply_collision_apis=True)
            sim_box_geom.set_collision_approximations("convexHull")
            sim_box_rigid_prims.append(RigidPrim(str(sim_box.GetPrimPath())))

        # Run physics simulation
        SimulationManager.set_physics_dt(1.0 / 90.0)
        SimulationManager.initialize_physics()

        # Simulate until boxes settle or max steps reached
        velocity_threshold = 0.01
        for step in range(max_sim_steps):
            SimulationManager.step()
            if sim_box_rigid_prims:
                top_box_velocity = sim_box_rigid_prims[-1].get_velocities(indices=[0])[0].numpy()
                if np.linalg.norm(top_box_velocity) < velocity_threshold:
                    print(f"[SDG] Simulation settled at step {step}")
                    break

.. raw:: html

    </details>


Running the Script
---------------------

The SDG loop runs randomizations directly using ``rep.functional`` APIs, triggers graph-based randomizers via custom events, and captures frames. The loop uses the seeded random number generator for reproducible results.

.. raw:: html

    <details open>
    <summary>SDG Loop Execution</summary>

.. code-block:: python

    # SDG loop - generate frames with randomizations
    num_frames = config.get("num_frames", 0)
    print(f"[SDG] Running SDG for {num_frames} frames")
    for i in range(num_frames):
        print(f"[SDG] Frame {i}/{num_frames}")

        print(f"[SDG]  Randomizing boxes on pallet.")
        rep.functional.randomizer.scatter_2d(
            prims=cardboxes, surface_prims=scatter_plane, check_for_collisions=True, rng=rng
        )

        print(f"[SDG]  Randomizing boxes materials.")
        rep.utils.send_og_event(event_name="randomize_cardboxes_materials")
        print(f"[SDG]  Randomizing lights.")
        rep.utils.send_og_event(event_name="randomize_lights")

        print(f"[SDG]  Randomizing pallet camera.")
        rep.functional.modify.pose(
            pallet_cam,
            position_value=rng.uniform(pallet_cam_bounds_min, pallet_cam_bounds_max),
            look_at_value=pallet_prim,
            look_at_up_axis=(0, 0, 1),
        )

        print(f"[SDG]  Randomizing driver camera.")
        rep.functional.modify.pose(
            driver_cam,
            position_value=rng.uniform(driver_cam_bounds_min, driver_cam_bounds_max),
            look_at_value=pallet_prim,
            look_at_up_axis=(0, 0, 1),
        )

        if i % 2 == 0:
            print(f"[SDG]  Randomizing cone position.")
            selected_corner = cone_placement_corners[rng.integers(0, len(cone_placement_corners))]
            rep.functional.modify.pose(
                cone,
                position_value=selected_corner,
            )

        if i % 4 == 0:
            print(f"[SDG]  Randomizing top view camera.")
            roll_angle = rng.uniform(0, 2 * np.pi)
            rep.functional.modify.pose(
                top_view_cam,
                position_value=rng.uniform(top_cam_bounds_min, top_cam_bounds_max),
                look_at_value=forklift_prim,
                look_at_up_axis=(np.cos(roll_angle), np.sin(roll_angle), 0.0),
            )

        print(f"[SDG]  Capturing frame with rt_subframes={rt_subframes}")
        rep.orchestrator.step(delta_time=0.0, rt_subframes=rt_subframes)

.. raw:: html

    </details>

After the SDG loop completes, proper cleanup ensures all data is written and resources are released:

.. raw:: html

    <details open>
    <summary>Cleanup</summary>

.. code-block:: python

    # Cleanup
    rep.orchestrator.wait_until_complete()
    writer.detach()
    for render_product in render_products:
        render_product.destroy()

    # Check if the application should keep running after data generation
    close_app_after_run = config.get("close_app_after_run", True)
    if config["launch_config"]["headless"]:
        if not close_app_after_run:
            print("[SDG] 'close_app_after_run' is ignored when running headless. The application will be closed.")
    elif not close_app_after_run:
        print("[SDG] The application will not be closed after the run. Make sure to close it manually.")
        while simulation_app.is_running():
            simulation_app.update()
    simulation_app.close()

.. raw:: html

    </details>

Summary
---------------------

This tutorial covered the following topics:

#. Starting a ``SimulationApp`` instance of |isaac-sim_short| to work with Replicator
#. Loading a stage and custom assets at random locations using |isaac-sim_short| API with seeded randomization
#. Setting up cameras using ``rep.functional.create.camera`` with organized stage structure
#. Configuring writers with optional backend support for flexible output handling
#. Using ``rep.functional`` APIs for direct randomization (scatter, pose modification)
#. Creating graph-based randomizers for lights and materials triggered by custom events
#. Running physics simulations with ``SimulationManager`` and experimental ``GeomPrim``/``RigidPrim`` classes
#. Proper cleanup of writers and render products

Next Steps
---------------------

One possible use for the created data is with the TAO Toolkit. After the generated synthetic data is in Kitti format, you can use the TAO Toolkit to
train a model. TAO provides `segmentation, classification and object detection models <https://docs.nvidia.com/tao/tao-toolkit/text/overview.html#pre-trained-models>`_.
This example uses object detection with the `Detectnet V2 model <https://docs.nvidia.com/tao/tao-toolkit-archive/5.2.0/text/object_detection/detectnet_v2.html>`_
as a use case.

To get started with TAO, follow the `set-up instruction video <https://docs.nvidia.com/tao/tao-toolkit/text/quick_start_guide/index.html>`_.

TAO uses Jupyter notebooks to guide you through the training process.
In the folder `cv_samples_v1.3.0`, you can find notebooks for multiple models.
You can use any of the object detection networks for this use case, but this example uses `Detectnet_V2`.

In the `detectnet_v2` folder, you can find the Jupyter notebook and the specs folder.
The `TAO Detectnet V2 documentation <https://docs.nvidia.com/tao/tao-toolkit-archive/5.2.0/text/object_detection/detectnet_v2.html>`_
goes into more detail about this sample. TAO works with configuration files that can be found in the
specs folder. Here, you must modify the specs to refer to the generated synthetic data as the
input.

To prepare the data, you must run the following command.

.. code-block:: bash

    tao detectnet_v2 dataset-convert [-h] -d DATASET_EXPORT_SPEC -o OUTPUT_FILENAME [-f VALIDATION_FOLD]

This is in the Jupyter notebook with a sample configuration. Modify the spec file to match the folder
structure of your synthetic data. The data is in TFrecord format and is ready for training.
Again, you need to change the spec file for training to represent the path to the synthetic data and
the classes being detected.

.. code-block:: bash

    tao detectnet_v2 train [-h] -k <key>
                            -r <result directory>
                            -e <spec_file>
                            [-n <name_string_for_the_model>]
                            [--gpus <num GPUs>]
                            [--gpu_index <comma separate gpu indices>]
                            [--use_amp]
                            [--log_file <log_file>]

For any questions regarding the TAO Toolkit, refer to the `TAO documentation <https://docs.nvidia.com/tao/tao-toolkit/text/overview.html>`_.

Further Learning
---------------------

To learn how to use |isaac-sim| to create data sets in an interactive manner, see the
:ref:`isaac_sim_app_tutorial_replicator_recorder` and then visualize them with the :ref:`Synthetic Data Visualizer <the-synthetic-data-visualizer>`.

