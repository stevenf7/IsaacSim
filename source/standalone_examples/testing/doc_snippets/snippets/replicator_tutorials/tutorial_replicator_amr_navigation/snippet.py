def _randomize_dolly_pose(self) -> None:
    min_dist_from_carter = 4
    carter_loc = self._carter_chassis.GetAttribute("xformOp:translate").Get()
    for _ in range(100):
        x, y = random.uniform(-6, 6), random.uniform(-6, 6)
        dist = (Gf.Vec2f(x, y) - Gf.Vec2f(carter_loc[0], carter_loc[1])).GetLength()
        if dist > min_dist_from_carter:
            self._dolly.GetAttribute("xformOp:translate").Set((x, y, 0))
            self._carter_nav_target.GetAttribute("xformOp:translate").Set((x, y, 0))
            break
    self._dolly.GetAttribute("xformOp:rotateXYZ").Set((0, 0, random.uniform(-180, 180)))


def _randomize_dolly_light(self) -> None:
    dolly_loc = self._dolly.GetAttribute("xformOp:translate").Get()
    self._dolly_light.GetAttribute("xformOp:translate").Set(dolly_loc + (0, 0, 3))
    self._dolly_light.GetAttribute("inputs:color").Set(
        (random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1))
    )


def _randomize_prop_poses(self) -> None:
    spawn_loc = self._dolly.GetAttribute("xformOp:translate").Get()
    spawn_loc[2] = spawn_loc[2] + 0.5
    for prop in self._props:
        prop.GetAttribute("xformOp:translate").Set(spawn_loc + (random.uniform(-1, 1), random.uniform(-1, 1), 0))
        spawn_loc[2] = spawn_loc[2] + 0.2
