def advance_timeline_by_duration(duration: float, max_updates: int = 1000):
    timeline = omni.timeline.get_timeline_interface()
    current_time = timeline.get_current_time()
    target_time = current_time + duration

    while current_time < target_time:
        simulation_app.update()
        current_time = timeline.get_current_time()


# This ensures the scene is fully initialized and the robot begins moving before data capture starts.
