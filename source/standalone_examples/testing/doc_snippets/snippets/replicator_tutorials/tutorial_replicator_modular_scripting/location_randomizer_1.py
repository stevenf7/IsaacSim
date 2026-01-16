def _randomize_location(self, prim):
    # Generate random offset within bounds
    random_offset = Gf.Vec3d(
        random.uniform(self._min_position[0], self._max_position[0]),
        random.uniform(self._min_position[1], self._max_position[1]),
        random.uniform(self._min_position[2], self._max_position[2]),
    )

    # Calculate final location based on target prim and relative frame settings
    if self._target_prim:
        target_loc = get_world_location(self._target_prim)
        loc = (
            target_loc + self._target_offsets[prim] + random_offset
            if self._use_relative_frame
            else target_loc + random_offset
        )
    else:
        loc = self._initial_locations[prim] + random_offset if self._use_relative_frame else random_offset

    self._set_location(prim, loc)
