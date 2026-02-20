class FlipStationObstacleMonitor(ObstacleMonitor):
    def __init__(self, context):
        super().__init__(context, [context.world.scene.get_object("flip_station_sphere")])

    def is_obstacle_required(self):
        eff_T = self.context.robot.arm.get_fk_T()
        eff_R, eff_p = math_util.unpack_T(eff_T)
        eff_ax, _, _ = math_util.unpack_R(eff_R)

        grasp_p = self.context.active_bin.grasp_T[:3, 3]
        grasp_ax = self.context.active_bin.grasp_T[:3, 0]
        v = eff_p - grasp_p
        dist = v.dot(grasp_ax)
        orth_dist = np.linalg.norm(v - dist * grasp_ax)
        return not (dist < 0.02 and grasp_ax.dot(eff_ax) > 0.75 and orth_dist < 0.03)


class NavigationObstacleMonitor(ObstacleMonitor):
    def __init__(self, context):
        obstacles = [
            context.world.scene.get_object("navigation_dome_obs"),
            context.world.scene.get_object("navigation_barrier_obs"),
            context.world.scene.get_object("navigation_flip_station_obs"),
        ]
        super().__init__(context, obstacles)

    def is_obstacle_required(self):
        target_p, _ = self.context.robot.arm.target_prim.get_world_pose()

        ref_p = np.array([0.6, 0.37, -0.99])
        eff_p = self.context.robot.arm.get_fk_p()

        ref_p[2] = 0.0
        eff_p[2] = 0.0
        target_p[2] = 0.0

        s_target = np.sign(np.cross(target_p, ref_p)[2])
        s_eff = np.sign(np.cross(eff_p, ref_p)[2])
        is_required = s_target * s_eff < 0.0
        return is_required
