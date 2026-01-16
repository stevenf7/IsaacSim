for i in range(shape_distractors_num):
    rand_loc, rand_rot, rand_scale = get_random_transform_values(
        loc_min=working_area_min, loc_max=working_area_max, scale_min_max=shape_distractors_scale_min_max
    )
    # ...
    rep.functional.modify.pose(prim, position_value=rand_loc, rotation_value=rand_rot, scale_value=rand_scale)

# ...
for cam in cameras:
    # ...
    # Get a random pose of the camera looking at the target asset from the given distance
    cam_loc, quat = get_random_pose_on_sphere(origin=target_loc, radius=distance)
    rep.functional.modify.pose(cam, position_value=cam_loc, rotation_value=quat)
