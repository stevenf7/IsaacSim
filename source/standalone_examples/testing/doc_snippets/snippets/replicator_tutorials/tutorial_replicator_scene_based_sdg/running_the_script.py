# Run physics simulation to settle boxes on pallet
await simulate_falling_objects_async(forklift_prim, assets_root_path, config, rng=rng)

# SDG loop - generate frames with randomizations
num_frames = config.get("num_frames", 10)
print(f"[SDG] Running SDG for {num_frames} frames")
for i in range(num_frames):
    # Scatter boxes on pallet using functional API
    rep.functional.randomizer.scatter_2d(
        prims=cardboxes, surface_prims=scatter_plane, check_for_collisions=True, rng=rng
    )

    # Trigger graph-based randomizers via events
    rep.utils.send_og_event(event_name="randomize_cardboxes_materials")
    rep.utils.send_og_event(event_name="randomize_lights")

    # Randomize pallet camera position
    rep.functional.modify.pose(
        pallet_cam,
        position_value=rng.uniform(pallet_cam_bounds_min, pallet_cam_bounds_max),
        look_at_value=pallet_prim,
        look_at_up_axis=(0, 0, 1),
    )

    # Randomize driver camera position
    rep.functional.modify.pose(
        driver_cam,
        position_value=rng.uniform(driver_cam_bounds_min, driver_cam_bounds_max),
        look_at_value=pallet_prim,
        look_at_up_axis=(0, 0, 1),
    )

    # Randomize cone position every 2 frames
    if i % 2 == 0:
        selected_corner = cone_placement_corners[rng.integers(0, len(cone_placement_corners))]
        rep.functional.modify.pose(
            cone,
            position_value=selected_corner,
        )

    # Randomize top view camera every 4 frames
    if i % 4 == 0:
        roll_angle = rng.uniform(0, 2 * np.pi)
        rep.functional.modify.pose(
            top_view_cam,
            position_value=rng.uniform(top_cam_bounds_min, top_cam_bounds_max),
            look_at_value=forklift_prim,
            look_at_up_axis=(np.cos(roll_angle), np.sin(roll_angle), 0.0),
        )

    # Capture frame
    await rep.orchestrator.step_async(delta_time=0.0, rt_subframes=rt_subframes)
