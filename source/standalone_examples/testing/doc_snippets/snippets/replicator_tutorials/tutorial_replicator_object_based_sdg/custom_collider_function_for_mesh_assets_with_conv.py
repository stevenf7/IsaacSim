for i in range(shape_distractors_num):
    rand_shape = random.choice(shape_distractors_types)
    prim_path = omni.usd.get_stage_next_free_path(stage, f"/World/Distractors/{rand_shape}", False)
    prim = stage.DefinePrim(prim_path, rand_shape.capitalize())
    # ...
    add_colliders(prim)
    disable_gravity = random.choice([True, False])
    rep.functional.physics.apply_rigid_body(prim, disableGravity=disable_gravity)
