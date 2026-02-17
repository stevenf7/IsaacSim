class BinStackingContext(ObstacleMonitorContext):
    def __init__(self, robot):
        super().__init__()
        ...

        self.add_monitors(
            [
                BinStackingContext.monitor_bins,
                BinStackingContext.monitor_active_bin,
                BinStackingContext.monitor_active_bin_grasp_T,
                BinStackingContext.monitor_active_bin_grasp_reached,
                self.diagnostics_monitor.monitor,
            ]
        )

        def reset(self):
            super().reset()

            # Find the collection of bins in the world scene.
            self.bins = []
            i = 0
            while True:
                name = "bin_{}".format(i)
                bin_obj = self.world.scene.get_object(name)
                if bin_obj is None:
                    break
                self.bins.append(BinState(bin_obj))
                i += 1

            self.active_bin = None
            self.stacked_bins.clear()
