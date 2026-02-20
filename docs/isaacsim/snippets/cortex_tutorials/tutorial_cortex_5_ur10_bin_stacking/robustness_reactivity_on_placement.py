class ReachToPlace(MoveWithNavObs):
    ...

    def step(self):
        if self.bin_under is not None:
            bin_under_p, _ = self.bin_under.bin_obj.get_world_pose()
            bin_grasped_p, _ = self.context.active_bin.bin_obj.get_world_pose()
            xy_err = bin_under_p[:2] - bin_grasped_p[:2]
            if np.linalg.norm(xy_err) < 0.02:
                self.target_p[:2] += 0.1 * (bin_under_p[:2] - bin_grasped_p[:2])

        target_pose = PosePq(self.target_p, math_util.matrix_to_quat(self.target_R))

        approach_params = ApproachParams(direction=0.15 * np.array([0.0, 0.0, -1.0]), std_dev=0.005)
        posture_config = self.context.robot.default_config
        self.update_command(
            MotionCommand(target_pose=target_pose, approach_params=approach_params, posture_config=posture_config)
        )
