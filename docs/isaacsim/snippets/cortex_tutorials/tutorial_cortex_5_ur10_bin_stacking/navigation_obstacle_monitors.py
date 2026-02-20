class BinStackingContext(ObstacleMonitorContext):
    def __init__(self, robot):
        super().__init__()

        ...

        self.flip_station_obs_monitor = FlipStationObstacleMonitor(self)
        self.navigation_obs_monitor = NavigationObstacleMonitor(self)
        self.add_obstacle_monitors([self.flip_station_obs_monitor, self.navigation_obs_monitor])
