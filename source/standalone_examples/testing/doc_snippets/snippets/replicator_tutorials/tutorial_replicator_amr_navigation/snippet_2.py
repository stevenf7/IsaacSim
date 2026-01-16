def _setup_next_frame(self) -> None:
    self._frame_counter += 1
    if self._frame_counter >= self._num_frames:
        print(f"[SDG] Finished")
        if self._is_running_in_script_editor():
            task = asyncio.ensure_future(rep.orchestrator.wait_until_complete_async())
            task.add_done_callback(lambda t: self.clear())
        else:
            rep.orchestrator.wait_until_complete()
            self.clear()
        return

    self._randomize_dolly_pose()
    self._randomize_dolly_light()
    self._randomize_prop_poses()
    if self._frame_counter % self._env_interval == 0:
        self._load_next_env()
    # Set a new random distance from which to capture the next frame
    self._trigger_distance = random.uniform(1.75, 2.5)
    self._timeline.play()
    self._timeline_sub = self._timeline.get_timeline_event_stream().create_subscription_to_pop_by_type(
        int(omni.timeline.TimelineEventType.CURRENT_TIME_TICKED), self._on_timeline_event
    )
