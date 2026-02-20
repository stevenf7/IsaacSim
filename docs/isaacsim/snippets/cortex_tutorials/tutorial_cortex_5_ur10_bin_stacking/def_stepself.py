class MoveWithNavObs(Move):
    def enter(self):
        super().enter()
        self.context.navigation_obs_monitor.activate_autotoggle()

    def exit(self):
        super().exit()
        self.context.navigation_obs_monitor.deactivate_autotoggle()
