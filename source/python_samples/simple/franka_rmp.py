# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.


import os
from omni.isaac.python_app import OmniKitHelper
import random
import argparse

# Default rendering parameters
CONFIG = {
    "renderer": "RaytracedLighting",
    "experience": f'{os.environ["EXP_PATH"]}/omni.isaac.sim.python.kit',
    "headless": False,
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Usd Load sample")
    parser.add_argument("--headless", default=False, action="store_true", help="Run stage headless")
    args, unknown = parser.parse_known_args()
    CONFIG["headless"] = args.headless
    # High level sample for how to use RMPs
    kit = OmniKitHelper(config=CONFIG)
    from pxr import Gf
    import omni
    from omni.isaac.samples.scripts.rmp_sample.sample import RMPSample

    stage = kit.get_stage()

    # Instantiate RMPSample
    sample = RMPSample()

    def _on_simulation_step(step):
        sample.step(step)

    sample.create_robot()
    viewport = omni.kit.viewport.get_default_viewport_window()
    viewport.set_camera_position("/OmniverseKit_Persp", 142, -127, 56, True)
    viewport.set_camera_target("/OmniverseKit_Persp", -180, 234, -27, True)
    kit.update()
    kit.update()

    # Start the timeline, subscribe to physics step
    kit.play()
    handle = omni.physx.acquire_physx_interface().subscribe_physics_step_events(_on_simulation_step)
    print("Loading assets")
    while kit.is_loading():
        kit.update()
    print("Asset loading complete")

    # Enable target following and set a random target
    sample.follow_target()
    sample.move_target(Gf.Vec3d(random.uniform(20, 50), random.uniform(-20, 20), random.uniform(10, 100)))
    # Start simulation
    kit.play()

    # simulate for 600 frames, 10 seconds of simulated time
    for frame in range(60 * 10):
        # collect joint commands and state
        sample.collect_action_state()
        # simulate one time step
        kit.update(1.0 / 60.0)
        # check if we have reached the target position and then:
        # - move the target randomly
        # - print the current set of joint states and commands
        # - reset recorded state
        if sample.has_arrived():
            print("arrived, moving target randomly")
            # printing for illustrative purposes
            print(sample.get_action_state_dict())
            sample.reset_action_state_dict()
            sample.move_target(
                Gf.Vec3d(random.uniform(20, 50), random.uniform(-20, 20), random.uniform(10, 50)),
                Gf.Matrix3d(Gf.Rotation(Gf.Vec3d(1, 0, 0), random.uniform(-90, 90))),
            )

    # cleanup
    kit.stop()
    kit.shutdown()
