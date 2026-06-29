"""Example holonomic (3-wheel) MobilityGenRobot subclass (Kaya).

Demonstrates overriding build() and write_action() for a holonomic drive robot
that uses HolonomicController instead of a differential drive controller.
"""


def make_kaya_robot_class():
    """Return KayaRobot class with MobilityGen + holonomic dependencies resolved.

    Call this at runtime when Isaac Sim is available, then pass the returned
    class to MobilityGen's recording/replay pipeline.
    """
    from isaacsim.core.prims import Articulation as _ArticulationView
    from isaacsim.replicator.mobility_gen.examples.misc import HawkCamera
    from isaacsim.replicator.mobility_gen.examples.robots import WheeledMobilityGenRobot
    from isaacsim.replicator.mobility_gen.impl.robot import ROBOTS
    from isaacsim.replicator.mobility_gen.impl.utils.global_utils import get_world, join_sdf_paths
    from isaacsim.robot.wheeled_robots.controllers.holonomic_controller import HolonomicController
    from isaacsim.robot.wheeled_robots.robots import WheeledRobot as _WheeledRobot
    from isaacsim.robot.wheeled_robots.robots.holonomic_robot_usd_setup import HolonomicRobotUsdSetup
    from isaacsim.storage.native import get_assets_root_path

    @ROBOTS.register()
    class KayaRobot(WheeledMobilityGenRobot):
        """Holonomic 3-wheel robot (NVIDIA Kaya) for MobilityGen SDG.

        Overrides build() to configure a HolonomicController and write_action()
        to map the 2D [lin, ang] action to the [forward, lateral, yaw] command.
        """

        physics_dt: float = 0.005
        z_offset: float = 0.02
        chase_camera_base_path = "base_link"
        chase_camera_x_offset: float = -0.5
        chase_camera_z_offset: float = 0.3
        chase_camera_tilt_angle: float = 60.0
        front_camera_base_path = "base_link/front_hawk"
        front_camera_rotation = (0.0, 0.0, 0.0)
        front_camera_translation = (0.1, 0.0, 0.05)
        front_camera_type = HawkCamera

        occupancy_map_radius: float = 0.2
        occupancy_map_z_min: float = 0.02
        occupancy_map_z_max: float = 0.3
        occupancy_map_cell_size: float = 0.05
        occupancy_map_collision_radius: float = 0.2
        random_action_linear_velocity_range = (-0.2, 0.4)
        random_action_angular_velocity_range = (-0.5, 0.5)
        random_action_linear_acceleration_std: float = 1.0
        random_action_angular_acceleration_std: float = 2.0
        random_action_grid_pose_sampler_grid_size: float = 5.0
        path_following_speed: float = 0.4
        path_following_angular_gain: float = 1.0
        path_following_stop_distance_threshold: float = 0.3
        path_following_forward_angle_threshold = 0.785
        path_following_target_point_offset_meters: float = 0.5
        keyboard_linear_velocity_gain: float = 0.4
        keyboard_angular_velocity_gain: float = 0.5
        gamepad_linear_velocity_gain: float = 0.4
        gamepad_angular_velocity_gain: float = 0.5

        wheel_dof_names = ["axle_0_joint", "axle_1_joint", "axle_2_joint"]
        usd_url: str = None  # set at runtime: get_assets_root_path() + "/Isaac/Robots/NVIDIA/Kaya/kaya.usd"
        chassis_subpath: str = "base_link"
        wheel_radius: float = 0.04
        wheel_base: float = 0.1
        com_prim_subpath: str = "base_link/control_offset"

        @classmethod
        def build(cls, prim_path: str):
            if cls.usd_url is None:
                cls.usd_url = get_assets_root_path() + "/Isaac/Robots/NVIDIA/Kaya/kaya.usd"
            world = get_world()
            robot = world.scene.add(
                _WheeledRobot(prim_path, wheel_dof_names=cls.wheel_dof_names, create_robot=True, usd_path=cls.usd_url)
            )
            view = _ArticulationView(join_sdf_paths(prim_path, cls.chassis_subpath))
            world.scene.add(view)
            kaya_setup = HolonomicRobotUsdSetup(
                robot_prim_path=prim_path,
                com_prim_path=join_sdf_paths(prim_path, cls.com_prim_subpath),
            )
            wheel_radius, wheel_positions, wheel_orientations, mecanum_angles, wheel_axis, up_axis = (
                kaya_setup.get_holonomic_controller_params()
            )
            controller = HolonomicController(
                name="kaya_controller",
                wheel_radius=wheel_radius,
                wheel_positions=wheel_positions,
                wheel_orientations=wheel_orientations,
                mecanum_angles=mecanum_angles,
                wheel_axis=wheel_axis,
                up_axis=up_axis,
            )
            camera = cls.build_front_camera(prim_path)
            return cls(
                prim_path=prim_path, robot=robot, articulation_view=view, controller=controller, front_camera=camera
            )

        def write_action(self, step_size: float):
            action = self.action.get_value()
            self.robot.apply_wheel_actions(self.controller.forward(command=[action[0], 0.0, action[1]]))

    return KayaRobot
