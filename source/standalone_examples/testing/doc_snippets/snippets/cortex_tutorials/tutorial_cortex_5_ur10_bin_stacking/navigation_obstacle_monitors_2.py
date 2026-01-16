class ReachToPick(MoveWithNavObs):
    ...

    def enter(self):
        super().enter()
        self.context.flip_station_obs_monitor.activate_autotoggle()

    def step(self): ...

    def exit(self):
        super().exit()
        self.context.flip_station_obs_monitor.deactivate_autotoggle()
