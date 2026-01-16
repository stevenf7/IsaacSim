def _on_timeline_event(self, e: carb.eventdispatcher.Event):
    self._check_bin_overlaps()


def _check_bin_overlaps(self):
    bin_pose = omni.usd.get_world_transform_matrix(self._active_bin)
    origin = bin_pose.ExtractTranslation()
    quat_gf = bin_pose.ExtractRotation().GetQuaternion()

    any_hit_flag = False
    hit_info = get_physx_scene_query_interface().overlap_box(
        carb.Float3(self._overlap_extent),
        carb.Float3(origin[0], origin[1], origin[2]),
        carb.Float4(quat_gf.GetImaginary()[0], quat_gf.GetImaginary()[1], quat_gf.GetImaginary()[2], quat_gf.GetReal()),
        self._on_overlap_hit,
        any_hit_flag,
    )


def _on_overlap_hit(self, hit):
    # Skip self-hits
    if hit.rigid_body == self._active_bin.GetPrimPath():
        return True

    # Handle flip scenario (only once per bin)
    if not self._bin_flip_scenario_done and hit.rigid_body.startswith(self.FLIP_HELPER_PATH):
        self._timeline.pause()
        if self._timeline_sub:
            self._timeline_sub.reset()
            self._timeline_sub = None
        asyncio.ensure_future(self._run_bin_flip_scenario())
        return False

    # Handle pallet landing scenario
    is_pallet_hit = hit.rigid_body.startswith(self.PALLET_PRIM_MESH_PATH)
    is_other_bin_hit = hit.rigid_body.startswith(f"{self.BINS_FOLDER_PATH}/bin_")
    if is_pallet_hit or is_other_bin_hit:
        self._timeline.pause()
        if self._timeline_sub:
            self._timeline_sub.reset()
            self._timeline_sub = None
        asyncio.ensure_future(self._run_pallet_scenario())

    return True  # No relevant hit, return True to continue the query
