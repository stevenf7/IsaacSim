# Start the SDG loop
env_cycle = cycle(env_urls)
capture_counter = 0
while capture_counter < total_captures:
    # Load the next environment
    env_url = next(env_cycle)
    print(f"[SDG] Loading environment: {env_url}")
    infinigen_utils.load_env(env_url, prim_path="/Environment")

    # Setup the environment (add collision, fix lights, etc.)
    infinigen_utils.setup_env(root_path="/Environment", hide_top_walls=debug_mode)
    simulation_app.update()

    # Get the working area location
    working_area_loc = infinigen_utils.get_matching_prim_location(match_string="TableDining", root_path="/Environment")

    # Randomize asset poses around the working area
    # (As shown in previous sections)

    # Trigger randomizations
    rep.utils.send_og_event(event_name="randomize_dome_lights")
    rep.utils.send_og_event(event_name="randomize_shape_distractor_colors")

    # Run physics and capture data
    # (As shown in previous sections - capture_counter increments inside capture loops)

# Wait until the data is written to disk
rep.orchestrator.wait_until_complete()

# Cleanup: detach writers and destroy render products
for writer in writers:
    writer.detach()
for rp in render_products:
    rp.destroy()
