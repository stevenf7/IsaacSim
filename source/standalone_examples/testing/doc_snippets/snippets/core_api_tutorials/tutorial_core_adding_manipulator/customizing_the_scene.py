self._controller = FrankaPickPlace()
self._controller.setup_scene(
    cube_initial_position=np.array([0.4, 0.2, 0.0258]),
    cube_size=np.array([0.05, 0.05, 0.05]),
    target_position=np.array([-0.4, 0.2, 0.12]),
)
