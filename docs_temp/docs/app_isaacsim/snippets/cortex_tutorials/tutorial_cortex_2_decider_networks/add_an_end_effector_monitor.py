class FollowContext(DfContext):
    def __init__(self, robot):
        super().__init__(robot)
        self.reset()

        self.add_monitors([FollowContext.monitor_end_effector, FollowContext.monitor_diagnostics])

    def reset(self):
        self.is_target_reached = False

    def monitor_end_effector(self):
        eff_p = self.robot.arm.get_fk_p()
        target_p, _ = self.robot.follow_sphere.get_world_pose()
        self.is_target_reached = np.linalg.norm(target_p - eff_p) < 0.01

    def monitor_diagnostics(self):
        print("is_target_reached: {}".format(self.is_target_reached))
