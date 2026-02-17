class PeckContext(DfLogicalState):
    def __init__(self, robot):
        super().__init__()
        self.robot = robot

        self.monitors = [
            PeckContext.monitor_block_movement,
            PeckContext.monitor_active_target_p,
            PeckContext.monitor_active_block,
            PeckContext.monitor_eff_block_proximity,
            PeckContext.monitor_diagnostics,
        ]
