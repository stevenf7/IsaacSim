# Apply a random (mostly) upwards velocity to the objects overlapping the 'bounce' area
def on_overlap_hit(hit):
    prim = stage.GetPrimAtPath(hit.rigid_body)
    # Skip the camera collision spheres
    if prim not in camera_colliders:
        rand_vel = (random.uniform(-2, 2), random.uniform(-2, 2), random.uniform(4, 8))
        prim.GetAttribute("physics:velocity").Set(rand_vel)
    return True  # return True to continue the query


# Area to check for overlapping objects (above the bottom collision box)
overlap_area_thickness = 0.1
overlap_area_origin = (0, 0, (-working_area_size[2] / 2) + (overlap_area_thickness / 2))
overlap_area_extent = (
    working_area_size[0] / 2 * 0.99,
    working_area_size[1] / 2 * 0.99,
    overlap_area_thickness / 2 * 0.99,
)


# Triggered every physics update step to check for overlapping objects
def on_physics_step(dt: float):
    hit_info = get_physx_scene_query_interface().overlap_box(
        carb.Float3(overlap_area_extent),
        carb.Float3(overlap_area_origin),
        carb.Float4(0, 0, 0, 1),
        on_overlap_hit,
        False,  # pass 'False' to indicate an 'overlap multiple' query.
    )


# Subscribe to the physics step events to check for objects overlapping the 'bounce' area
physx_sub = get_physx_interface().subscribe_physics_step_events(on_physics_step)
