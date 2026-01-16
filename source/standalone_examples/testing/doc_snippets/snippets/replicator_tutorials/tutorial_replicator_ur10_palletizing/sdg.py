def start(self, num_captures, bin_flip_frames, pallet_frames):
    self._num_captures = num_captures if 1 <= num_captures <= 36 else 36
    self._bin_flip_frames = bin_flip_frames
    self._pallet_frames = pallet_frames
    if self._init():
        self._start()


# ...


def _init(self):
    self._stage = omni.usd.get_context().get_stage()
    self._active_bin = self._stage.GetPrimAtPath(f"{self.BINS_FOLDER_PATH}/bin_{self._bin_counter}")

    if not self._active_bin:
        print("[PalletizingSDGDemo] Could not find bin, make sure the palletizing demo is loaded..")
        return False

    bb_cache = create_bbox_cache()
    half_ext = bb_cache.ComputeLocalBound(self._active_bin).GetRange().GetSize() * 0.5
    self._overlap_extent = carb.Float3(half_ext[0], half_ext[1], half_ext[2] * 1.1)


# ...


def _start(self):
    self._timeline_sub = carb.eventdispatcher.get_eventdispatcher().observe_event(
        event_name=omni.timeline.GLOBAL_EVENT_CURRENT_TIME_TICKED,
        on_event=self._on_timeline_event,
        observer_name="PalletizingSDGDemo._on_timeline_event",
    )


# ...
