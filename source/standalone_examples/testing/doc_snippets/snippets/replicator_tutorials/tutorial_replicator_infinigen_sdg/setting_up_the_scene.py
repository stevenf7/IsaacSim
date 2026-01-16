# Load target assets with auto-labeling (e.g., 002_banana -> banana)
auto_label_config = labeled_assets_config.get("auto_label", {})
auto_floating_assets, auto_falling_assets = infinigen_utils.load_auto_labeled_assets(auto_label_config, rng)

# Load target assets with manual labels
manual_label_config = labeled_assets_config.get("manual_label", [])
manual_floating_assets, manual_falling_assets = infinigen_utils.load_manual_labeled_assets(manual_label_config, rng)
target_assets = auto_floating_assets + auto_falling_assets + manual_floating_assets + manual_falling_assets

# Load the shape distractors
shape_distractors_config = distractors_config.get("shape_distractors", {})
floating_shapes, falling_shapes = infinigen_utils.load_shape_distractors(shape_distractors_config, rng)
shape_distractors = floating_shapes + falling_shapes

# Load the mesh distractors
mesh_distractors_config = distractors_config.get("mesh_distractors", {})
floating_meshes, falling_meshes = infinigen_utils.load_mesh_distractors(mesh_distractors_config, rng)
mesh_distractors = floating_meshes + falling_meshes
