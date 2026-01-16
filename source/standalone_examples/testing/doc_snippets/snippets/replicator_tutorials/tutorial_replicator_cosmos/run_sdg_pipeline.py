def run_sdg_pipeline(camera_path, num_clips, num_frames_per_clip, capture_interval, use_instance_id=True):
    # Create render product from robot's camera
    rp = rep.create.render_product(camera_path, (1280, 720))

    # Initialize CosmosWriter
    cosmos_writer = rep.WriterRegistry.get("CosmosWriter")
    backend = rep.backends.get("DiskBackend")
    backend.initialize(output_dir="_out_cosmos_warehouse")
    cosmos_writer.initialize(backend=backend, use_instance_id=use_instance_id)
    cosmos_writer.attach(rp)

    # Capture multiple clips
    for clip_index in range(num_clips):
        # Capture frames for current clip
        frames_captured_count = 0
        while frames_captured_count < num_frames_per_clip:
            if simulation_step_index % capture_interval == 0:
                rep.orchestrator.step(pause_timeline=False)
                frames_captured_count += 1
            else:
                simulation_app.update()

        # Move to next clip
        if clip_index < num_clips - 1:
            cosmos_writer.next_clip()
