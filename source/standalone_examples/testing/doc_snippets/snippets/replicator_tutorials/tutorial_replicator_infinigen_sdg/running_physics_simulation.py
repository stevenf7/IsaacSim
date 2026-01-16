# Run a short simulation to resolve initial collisions
infinigen_utils.run_simulation(num_frames=4, render=True)

# Enable render products if they were disabled
if disable_render_products:
    for rp in render_products:
        rp.hydra_texture.set_updates_enabled(True)

# Optionally switch to path tracing for higher quality captures
if use_path_tracing:
    carb.settings.get_settings().set("/rtx/rendermode", "PathTracing")

# Capture frames with floating objects
for i in range(num_floating_captures_per_env):
    if capture_counter >= total_captures:
        break
    # Randomize camera poses
    infinigen_utils.randomize_camera_poses(
        cameras, target_assets, camera_distance_to_target_range, polar_angle_range=(0, 75), rng=rng
    )
    rep.orchestrator.step(rt_subframes=rt_subframes, delta_time=0.0)
    capture_counter += 1

# Disable render products and switch back to RealTimePathTracing during simulation
if disable_render_products:
    for rp in render_products:
        rp.hydra_texture.set_updates_enabled(False)
if use_path_tracing:
    carb.settings.get_settings().set("/rtx/rendermode", "RealTimePathTracing")

# Run physics simulation to let objects fall
infinigen_utils.run_simulation(num_frames=200, render=False)

# Re-enable render products and path tracing for dropped captures
if disable_render_products:
    for rp in render_products:
        rp.hydra_texture.set_updates_enabled(True)
if use_path_tracing:
    carb.settings.get_settings().set("/rtx/rendermode", "PathTracing")

# Capture frames with dropped objects
for i in range(num_dropped_captures_per_env):
    if capture_counter >= total_captures:
        break
    # Use smaller polar angle for mostly top-down view of dropped objects
    infinigen_utils.randomize_camera_poses(
        cameras, target_assets, distance_range=camera_distance_to_target_range, polar_angle_range=(0, 45), rng=rng
    )
    rep.orchestrator.step(rt_subframes=rt_subframes, delta_time=0.0)
    capture_counter += 1
