def _apply_behavior(self):
    target_location = self._get_target_location()
    for prim in self._valid_prims:
        eye = get_world_location(prim)
        look_at_rotation = calculate_look_at_rotation(eye, target_location, self._up_axis)
        set_rotation_with_ops(prim, look_at_rotation)
