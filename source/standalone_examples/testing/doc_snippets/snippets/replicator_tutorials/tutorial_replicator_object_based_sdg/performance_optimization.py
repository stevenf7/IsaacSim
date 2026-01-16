def set_render_products_updates(render_products, enabled, include_viewport=False):
    """Enable or disable the render products and viewport rendering."""
    for rp in render_products:
        rp.hydra_texture.set_updates_enabled(enabled)
    if include_viewport:
        get_active_viewport().updates_enabled = enabled


# ...

# Run the simulation and capture data triggering randomizations and actions at custom frame intervals
for i in range(num_frames):
    # ...

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
