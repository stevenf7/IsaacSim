# Load warehouse environment
stage_path = assets_root_path + STAGE_URL
omni.usd.get_context().open_stage(stage_path)

# Add Carter Nova robot with navigation
carter_nav_prim = add_reference_to_stage(usd_path=carter_url_path, prim_path=CARTER_NAV_PATH)
carter_nav_prim.GetAttribute("xformOp:translate").Set(CARTER_NAV_POSITION)

# Set navigation target
carter_navigation_target_prim.GetAttribute("xformOp:translate").Set(CARTER_NAV_TARGET_POSITION)

# Run SDG pipeline
run_sdg_pipeline(camera_path, num_clips, num_frames_per_clip, capture_interval)
