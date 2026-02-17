class BuildTowerContext(DfContext):
    ...

    def __init__(self, robot, tower_position):
        ...
        self.monitors = [
            BuildTowerContext.monitor_perception,
            BuildTowerContext.monitor_block_tower,
            BuildTowerContext.monitor_gripper_has_block,
            BuildTowerContext.monitor_suppression_requirements,
            BuildTowerContext.monitor_diagnostics,
        ]
