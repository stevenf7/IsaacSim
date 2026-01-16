while self._current_frame < num_frames:
    timeline = omni.timeline.get_timeline_interface()

    if self.control_timeline and not timeline.is_playing():
        timeline.play()
        timeline.commit()

    await rep.orchestrator.step_async(rt_subframes=self.rt_subframes, delta_time=None, pause_timeline=False)

    self._current_frame += 1
