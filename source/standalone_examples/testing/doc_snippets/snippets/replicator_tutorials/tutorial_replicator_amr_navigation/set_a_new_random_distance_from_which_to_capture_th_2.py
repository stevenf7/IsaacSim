def start():
    # ...
    self._load_env()
    self._randomize_dolly_pose()
    self._randomize_dolly_light()
    self._randomize_prop_poses()
    self._setup_sdg()
    # ...
    self._timeline_sub = self._timeline.get_timeline_event_stream().create_subscription_to_pop_by_type(
        int(omni.timeline.TimelineEventType.CURRENT_TIME_TICKED), self._on_timeline_event
    )
    # ...


def _on_timeline_event(self, e: carb.events.IEvent) -> None:
    carter_loc = self._carter_chassis.GetAttribute("xformOp:translate").Get()
    dolly_loc = self._dolly.GetAttribute("xformOp:translate").Get()
    dist = (Gf.Vec2f(dolly_loc[0], dolly_loc[1]) - Gf.Vec2f(carter_loc[0], carter_loc[1])).GetLength()
    if dist < self._trigger_distance:
        print(f"[SDG] Starting SDG for frame no. {self._frame_counter}")
        self._timeline.pause()
        self._timeline_sub.unsubscribe()
        if self._is_running_in_script_editor():
            task = asyncio.ensure_future(self._run_sdg_async())
            task.add_done_callback(self._on_sdg_done)
        else:
            self._run_sdg()
            self._setup_next_frame()
