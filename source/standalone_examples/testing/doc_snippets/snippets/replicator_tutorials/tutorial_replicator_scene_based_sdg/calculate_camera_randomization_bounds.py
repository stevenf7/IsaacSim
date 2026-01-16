async def simulate_falling_objects_async(
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
        await omni.kit.app.get_app().next_update_async()
