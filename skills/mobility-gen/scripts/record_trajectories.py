"""Phase 1 trajectory recording for MobilityGen SDG.

Records N episodes of headless physics simulation using a RandomPathFollowingScenario.
Run with $ISAAC_SIM_DIR/python.sh --enable isaacsim.replicator.mobility_gen.examples.
"""

import datetime
import os
import tempfile

from isaacsim import SimulationApp


def record_trajectories(
    scene_usd: str,
    omap_yaml: str,
    robot_type: str = "CarterRobot",
    scenario: str = "RandomPathFollowingScenario",
    num_episodes: int = 5,
    max_steps: int = 2000,
    data_dir: str = None,
) -> None:
    """Record robot trajectories headlessly using MobilityGen.

    Args:
        scene_usd: Path to the warehouse/environment USD.
        omap_yaml: Path to the ROS-format occupancy map YAML.
        robot_type: One of JetbotRobot | CarterRobot | H1Robot | SpotRobot.
        scenario: One of RandomPathFollowingScenario | RandomAccelerationScenario.
        num_episodes: Number of episodes to record.
        max_steps: Maximum physics steps per episode.
        data_dir: Root data directory; defaults to $MOBILITY_GEN_DATA or ~/MobilityGenData.
    """
    simulation_app = SimulationApp(launch_config={"headless": True})

    import isaacsim.core.api.objects as objects
    import isaacsim.replicator.mobility_gen.examples  # noqa: F401 — registers robots/scenarios
    from isaacsim.core.utils.stage import open_stage, save_stage
    from isaacsim.replicator.mobility_gen.impl.config import Config
    from isaacsim.replicator.mobility_gen.impl.occupancy_map import OccupancyMap
    from isaacsim.replicator.mobility_gen.impl.robot import ROBOTS
    from isaacsim.replicator.mobility_gen.impl.scenario import SCENARIOS
    from isaacsim.replicator.mobility_gen.impl.utils.global_utils import get_world, new_world
    from isaacsim.replicator.mobility_gen.impl.writer import MobilityGenWriter

    if data_dir is None:
        data_dir = os.environ.get(
            "MOBILITY_GEN_DATA",
            os.path.join(os.environ.get("WORKSPACE_DIR", os.path.expanduser("~")), "MobilityGenData"),
        )

    robot_cls = ROBOTS.get(robot_type)
    scenario_cls = SCENARIOS.get(scenario)

    config = Config(scenario_type=scenario, robot_type=robot_type, scene_usd=scene_usd)
    occupancy_map = OccupancyMap.from_ros_yaml(omap_yaml)

    open_stage(scene_usd)
    cached_stage = os.path.join(tempfile.mkdtemp(), "stage.usd")
    save_stage(cached_stage, save_and_reload_in_place=False)

    world = new_world(physics_dt=robot_cls.physics_dt)
    world.initialize_simulation_context()
    objects.GroundPlane("/World/ground_plane", visible=False)

    robot = robot_cls.build("/World/robot")
    scenario_instance = scenario_cls.from_robot_occupancy_map(robot, occupancy_map)

    recordings_dir = os.path.join(data_dir, "recordings")
    os.makedirs(recordings_dir, exist_ok=True)

    for episode in range(num_episodes):
        world.reset()
        scenario_instance.reset()

        name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        path = os.path.join(recordings_dir, name)
        writer = MobilityGenWriter(path)
        writer.write_config(config)
        writer.write_occupancy_map(occupancy_map)
        writer.copy_stage(cached_stage)

        step = 0
        while True:
            world.step(render=False)
            is_alive = scenario_instance.step(step_size=robot_cls.physics_dt)
            writer.write_state_dict_common(scenario_instance.state_dict_common(), step)
            step += 1
            if not is_alive or step >= max_steps:
                break

        print(f"Episode {episode + 1}/{num_episodes}: {step} steps -> {path}")

    simulation_app.close()
