def _create_bin_flip_graph(self):
    # Create new random lights using the color palette for the color attribute
    color_palette = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]

    def randomize_bin_flip_lights():
        lights = rep.create.light(
            light_type="Sphere",
            temperature=rep.distribution.normal(6500, 2000),
            intensity=rep.distribution.normal(45000, 15000),
            position=rep.distribution.uniform((0.25, 0.25, 0.5), (1, 1, 0.75)),
            scale=rep.distribution.uniform(0.5, 0.8),
            color=rep.distribution.choice(color_palette),
            count=3,
        )
        return lights.node

    rep.randomizer.register(randomize_bin_flip_lights)

    # Move the camera to the given location sequences and look at the predefined location
    camera_positions = [(1.96, 0.72, -0.34), (1.48, 0.70, 0.90), (0.79, -0.86, 0.12), (-0.49, 1.47, 0.58)]
    self._rep_camera = rep.create.camera()
    with rep.trigger.on_frame():
        rep.randomizer.randomize_bin_flip_lights()
        with self._rep_camera:
            rep.modify.pose(position=rep.distribution.sequence(camera_positions), look_at=(0.78, 0.72, -0.1))
