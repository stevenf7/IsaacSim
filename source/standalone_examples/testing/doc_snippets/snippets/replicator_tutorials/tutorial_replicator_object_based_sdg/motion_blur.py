async def capture_with_motion_blur_and_pathtracing_async(
    duration: float = 0.05, num_samples: int = 8, spp: int = 64
) -> None:
    """Capture motion blur by combining pathtraced subframe samples simulated for the given duration."""
    orig_physics_fps = physx_scene.GetTimeStepsPerSecondAttr().Get()
    target_physics_fps = 1 / duration * num_samples
    if target_physics_fps > orig_physics_fps:
        physx_scene.GetTimeStepsPerSecondAttr().Set(target_physics_fps)

    # Enable motion blur (if not enabled)
    is_motion_blur_enabled = carb.settings.get_settings().get("/omni/replicator/captureMotionBlur")
    if not is_motion_blur_enabled:
        carb.settings.get_settings().set("/omni/replicator/captureMotionBlur", True)
    carb.settings.get_settings().set("/omni/replicator/pathTracedMotionBlurSubSamples", num_samples)

    # Set the render mode to PathTracing
    prev_render_mode = carb.settings.get_settings().get("/rtx/rendermode")
    carb.settings.get_settings().set("/rtx/rendermode", "PathTracing")
    carb.settings.get_settings().set("/rtx/pathtracing/spp", spp)
    carb.settings.get_settings().set("/rtx/pathtracing/totalSpp", spp)
    carb.settings.get_settings().set("/rtx/pathtracing/optixDenoiser/enabled", 0)

    # Make sure the timeline is playing
    if not timeline.is_playing():
        timeline.play()

    # Capture the frame by advancing the simulation for the given duration and combining the sub samples
    await rep.orchestrator.step_async(delta_time=duration, pause_timeline=False)

    # Restore the original physics FPS
    if target_physics_fps > orig_physics_fps:
        physx_scene.GetTimeStepsPerSecondAttr().Set(orig_physics_fps)

    # Restore the previous render and motion blur settings
    carb.settings.get_settings().set("/omni/replicator/captureMotionBlur", is_motion_blur_enabled)
    carb.settings.get_settings().set("/rtx/rendermode", prev_render_mode)


# ...

# Run the simulation and capture data triggering randomizations and actions at custom frame intervals
for i in range(num_frames):

    # ...

    # Capture the current frame
    print(f"[SDG] Capturing frame {i}/{num_frames}, at simulation time: {timeline.get_current_time():.2f}")
    if i % 5 == 0:
        await capture_with_motion_blur_and_pathtracing_async(duration=0.025, num_samples=8, spp=128)
    else:
        await rep.orchestrator.step_async(delta_time=0.0, rt_subframes=rt_subframes, pause_timeline=False)
