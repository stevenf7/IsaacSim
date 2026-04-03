for i in range(self._num_scenarios):
    offset = np.array([0.0, (i - 1) * 2.0, 0.0])  # Spread along Y-axis
    scenario = RobotScenario(name=f"scenario_{i}", offset=offset, randomize=True)
    scenario.setup_scene()
    self._scenarios.append(scenario)
