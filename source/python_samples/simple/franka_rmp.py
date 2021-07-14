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

    # Subscribe to physics step
    physx_interface = omni.physx.acquire_physx_interface()

    stage = kit.get_stage()

    # Instantiate RMPSample
    sample = RMPSample()

    def _on_simulation_step(step):
        sample.step(step)

    handle = physx_interface.subscribe_physics_step_events(_on_simulation_step)

    sample.create_robot()
    viewport = omni.kit.viewport.get_default_viewport_window()
    viewport.set_camera_position("/OmniverseKit_Persp", 142, -127, 56, True)
    viewport.set_camera_target("/OmniverseKit_Persp", -180, 234, -27, True)
    kit.update()
    kit.update()

    print("Loading assets")
    while kit.is_loading():
        kit.update()

    print("Asset loading complete")

    # Run and step physx manually so that we don't need to render each frame
    physx_interface.start_simulation()
    physx_interface.force_load_physics_from_usd()

    # Enable target following and set a random target
    sample.follow_target()
    sample.move_target(Gf.Vec3d(random.uniform(20, 50), random.uniform(-20, 20), random.uniform(10, 80)))

    dt = 1.0 / 60.0
    # simulate for 30 seconds of simulated time
    for frame in range(int(1.0 / dt) * 30):
        # collect joint commands and state
        sample.collect_action_state()
        # simulate one time step
        physx_interface.update_simulation(dt, frame * dt)
        # check if we have reached the target position and then:
        # - move the target randomly
        # - print the current set of joint states and commands
        # - reset recorded state
        # - render a new frame
        if sample.has_arrived():
            # update state from physx to usd so we can render it
            physx_interface.update_transformations(
                updateToFastCache=False, updateToUsd=True, updateVelocitiesToUsd=True, outputVelocitiesLocalSpace=False
            )
            # render a frame to show that we reached the target
            kit.update()
            print("arrived, moving target randomly")
            # printing for illustrative purposes
            print(sample.get_action_state_dict())
            sample.reset_action_state_dict()
            sample.move_target(
                Gf.Vec3d(random.uniform(20, 50), random.uniform(-20, 20), random.uniform(10, 50)),
                Gf.Matrix3d(Gf.Rotation(Gf.Vec3d(1, 0, 0), random.uniform(-90, 90))),
            )

    # Ensure that we reach the final target, even if we hit the frame limit

    while sample.has_arrived() is False:
        frame = frame + 1
        physx_interface.update_simulation(dt, frame * dt)
        # in case we cannot reach the goal, put a hard limit and exit
        if frame > 3000:
            break
    physx_interface.update_transformations(
        updateToFastCache=False, updateToUsd=True, updateVelocitiesToUsd=True, outputVelocitiesLocalSpace=False
    )
    # render final frame showing we reached the target
    kit.update(0)

    # cleanup
    kit.shutdown()
