# Run the simulation and capture data triggering randomizations and actions at custom frame intervals
for i in range(num_frames):
    # Cameras will be moved to a random position and look at a randomly selected labeled asset
    if i % 3 == 0:
        randomize_camera_poses()
        # Temporarily enable camera colliders and simulate for a few frames to push out any overlapping objects
        if camera_colliders:
            await simulate_camera_collision_async(num_frames=4)

    # Apply a random velocity towards the origin to the working area to pull the assets closer to the center
    if i % 10 == 0:
        apply_velocities_towards_target(list(chain(labeled_prims, shape_distractors, mesh_distractors)))

    # Randomize lights locations and colors
    if i % 5 == 0:
        rep.utils.send_og_event(event_name="randomize_lights")

    # Randomize the colors of the primitive shape distractors
    if i % 15 == 0:
        rep.utils.send_og_event(event_name="randomize_shape_distractor_colors")

    # Randomize the texture of the dome background
    if i % 25 == 0:
        rep.utils.send_og_event(event_name="randomize_dome_background")

    # Apply a random velocity on the floating distractors (shapes and meshes)
    if i % 17 == 0:
        apply_random_velocities(list(chain(floating_shape_distractors, floating_mesh_distractors)))

    # Enable render products only at capture time
    if disable_render_products_between_captures:
        set_render_products_updates(render_products, True, include_viewport=False)

    # Capture the current frame
    print(f"[SDG] Capturing frame {i}/{num_frames}, at simulation time: {timeline.get_current_time():.2f}")
    if i % 5 == 0:
        await capture_with_motion_blur_and_pathtracing_async(duration=0.025, num_samples=8, spp=128)
    else:
        await rep.orchestrator.step_async(delta_time=0.0, rt_subframes=rt_subframes, pause_timeline=False)

    # Disable render products between captures
    if disable_render_products_between_captures:
        set_render_products_updates(render_products, False, include_viewport=False)

    # Run the simulation for a given duration between frame captures
    if sim_duration_between_captures > 0:
        await run_simulation_loop_async(sim_duration_between_captures)
    else:
        await omni.kit.app.get_app().next_update_async()

# Wait for the data to be written to disk
await rep.orchestrator.wait_until_complete_async()
