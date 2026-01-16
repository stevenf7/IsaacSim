for i in range(shape_distractors_num):
    rand_loc, rand_rot, rand_scale = get_random_transform_values(
        loc_min=working_area_min, loc_max=working_area_max, scale_min_max=shape_distractors_scale_min_max
    )
    rand_shape = random.choice(shape_distractors_types)
    prim_path = omni.usd.get_stage_next_free_path(stage, f"/World/Distractors/{rand_shape}", False)
    prim = stage.DefinePrim(prim_path, rand_shape.capitalize())
    rep.functional.modify.pose(prim, position_value=rand_loc, rotation_value=rand_rot, scale_value=rand_scale)
