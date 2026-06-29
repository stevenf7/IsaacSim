"""Replay recordings with a custom robot registered at runtime.

Use when replay_directory.py cannot find your robot class (KeyError).
Register the robot before calling load_scenario(), then run the render loop.
Run with $ISAAC_SIM_DIR/python.sh --enable isaacsim.replicator.mobility_gen.examples.
"""

import glob
import os

from isaacsim import SimulationApp


def replay_with_custom_robot(
    input_dir: str,
    custom_robot_class=None,
) -> None:
    """Replay all recordings in input_dir using a custom robot class.

    Args:
        input_dir: Directory containing MobilityGen recording subdirectories.
        custom_robot_class: A registered WheeledMobilityGenRobot or
            PolicyMobilityGenRobot subclass.  If None, only built-in robots
            from isaacsim.replicator.mobility_gen.examples are available.
    """
    simulation_app = SimulationApp(launch_config={"headless": True})

    import isaacsim.replicator.mobility_gen.examples  # noqa: F401 — registers built-in robots
    from isaacsim.replicator.mobility_gen.impl.build import load_scenario
    from isaacsim.replicator.mobility_gen.impl.robot import ROBOTS
    from isaacsim.replicator.mobility_gen.impl.utils.global_utils import get_world

    if custom_robot_class is not None:
        ROBOTS.register()(custom_robot_class)

    for recording_path in sorted(glob.glob(os.path.join(input_dir, "*"))):
        scenario = load_scenario(recording_path)  # KeyError if robot class missing
        world = get_world()
        world.reset()
        scenario.enable_rgb_rendering()
        # ... rest of render loop (mirrors replay_directory.py internals)

    simulation_app.close()
