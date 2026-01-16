def _apply_behavior(self):
    for prim in self._valid_prims:
        rand_color = (
            random.uniform(self._min_color[0], self._max_color[0]),
            random.uniform(self._min_color[1], self._max_color[1]),
            random.uniform(self._min_color[2], self._max_color[2]),
        )
        prim.GetAttribute("inputs:color").Set(rand_color)

        rand_intensity = random.uniform(self._intensity_range[0], self._intensity_range[1])
        prim.GetAttribute("inputs:intensity").Set(rand_intensity)
