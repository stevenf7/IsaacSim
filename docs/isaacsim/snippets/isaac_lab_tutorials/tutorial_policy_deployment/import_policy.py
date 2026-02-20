def initialize(self, physics_sim_view=None) -> None:
    """
    Initialize the articulation interface and set up drive mode.

    Args:
        physics_sim_view: The physics simulation view
    """
    super().initialize(physics_sim_view=physics_sim_view, control_mode="effort")

    # Actuator network
    assets_root_path = get_assets_root_path()
    file_content = omni.client.read_file(
        assets_root_path + "/Isaac/IsaacLab/ActuatorNets/ANYbotics/anydrive_3_lstm_jit.pt"
    )[2]
    file = io.BytesIO(memoryview(file_content).tobytes())
    self._actuator_network = LstmSeaNetwork()
    self._actuator_network.setup(file, self.default_pos)
    self._actuator_network.reset()
