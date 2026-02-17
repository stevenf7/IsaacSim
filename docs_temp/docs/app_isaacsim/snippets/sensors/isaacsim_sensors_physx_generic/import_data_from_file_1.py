def _on_editor_step(self, step):
    if not self._timeline.is_playing():
        return

    if self._timeline.is_playing():
        if self._generic:
            if self._pattern_set:
                if self._sensor.send_next_batch(
                    self._genericPath
                ):  # send_next_batch will turn True if the sensor is running out data and needs more
                    self._sensor.set_next_batch_rays(
                        self._genericPath, self.sensor_pattern
                    )  # set the next batch data using set_next_batch_rays()
                    self._sensor.set_next_batch_offsets(
                        self._genericPath, self.origin_offsets
                    )  # (Optional) add individual ray offsets if there are any
