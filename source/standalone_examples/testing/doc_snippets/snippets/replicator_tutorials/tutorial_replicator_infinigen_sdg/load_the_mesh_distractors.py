# Setup the environment (add collision, fix lights, etc.)
infinigen_utils.setup_env(root_path="/Environment", hide_top_walls=debug_mode)

# Get the location of the prim above which the assets will be randomized
working_area_loc = infinigen_utils.get_matching_prim_location(match_string="TableDining", root_path="/Environment")

# Get the spawn areas as offset location ranges from the working area
target_loc_range = infinigen_utils.offset_range((-0.5, -0.5, 1, 0.5, 0.5, 1.5), working_area_loc)
infinigen_utils.randomize_poses(
    target_assets,
    location_range=target_loc_range,
    rotation_range=(0, 360),
    scale_range=(0.95, 1.15),
    rng=rng,
)

# Randomize mesh distractors
mesh_loc_range = infinigen_utils.offset_range((-1, -1, 1, 1, 1, 2), working_area_loc)
infinigen_utils.randomize_poses(
    mesh_distractors,
    location_range=mesh_loc_range,
    rotation_range=(0, 360),
    scale_range=(0.3, 1.0),
    rng=rng,
)

# Randomize shape distractors
shape_loc_range = infinigen_utils.offset_range((-1.5, -1.5, 1, 1.5, 1.5, 2), working_area_loc)
infinigen_utils.randomize_poses(
    shape_distractors,
    location_range=shape_loc_range,
    rotation_range=(0, 360),
    scale_range=(0.01, 0.1),
    rng=rng,
)
