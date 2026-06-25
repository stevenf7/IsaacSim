# SPDX-FileCopyrightText: Copyright (c) 2024-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import os

import carb.settings
import isaacsim.core.experimental.utils.stage as stage_utils
import omni.kit.app
import omni.replicator.core as rep
import omni.timeline
import omni.usd
from isaacsim.core.experimental.prims import RigidPrim
from isaacsim.core.simulation_manager import PhysicsScene
from isaacsim.storage.native import get_assets_root_path_async


async def run_motion_blur_examples_async():
    # Paths to the animated and physics-ready assets
    PHYSICS_ASSET_URL = "/Isaac/Props/YCB/Axis_Aligned_Physics/003_cracker_box.usd"
    ANIM_ASSET_URL = "/Isaac/Props/YCB/Axis_Aligned/003_cracker_box.usd"

    # -z velocities and start locations of the animated (left side) and physics (right side) assets (stage units/s)
    ASSET_VELOCITIES = [0, 5, 10]
    ASSET_X_MIRRORED_LOCATIONS = [(0.5, 0, 0.3), (0.3, 0, 0.3), (0.1, 0, 0.3)]

    # Used to calculate how many frames to animate the assets to maintain the same velocity as the physics assets
    ANIMATION_DURATION = 10

    # Number of frames to capture for each scenario
    NUM_FRAMES = 3

    # Configuration for RTX Real-Time motion blur examples
    DELTA_TIMES = [None, 1 / 30, 1 / 60, 1 / 240]
    MAX_BLUR_DIAMETER_FRACTION = 0.02
    EXPOSURE_FRACTION = 1.0
    NUM_SAMPLES = 8

    async def setup_stage_async():
        """Create a new USD stage with animated and physics-enabled assets with synchronized motion."""
        await stage_utils.create_new_stage_async()
        settings = carb.settings.get_settings()
        # Set DLSS to Quality mode (2) for best SDG results , options: 0 (Performance), 1 (Balanced), 2 (Quality), 3 (Auto)
        settings.set("rtx/post/dlss/execMode", 2)

        # Capture data only on request
        rep.orchestrator.set_capture_on_play(False)

        timeline = omni.timeline.get_timeline_interface()
        timeline.set_end_time(ANIMATION_DURATION)
        timeline.commit()

        # Create lights
        rep.functional.create.xform(name="World")
        rep.functional.create.dome_light(intensity=100, parent="/World", name="DomeLight")
        rep.functional.create.distant_light(intensity=2500, rotation=(315, 0, 0), parent="/World", name="DistantLight")

        # Setup the physics assets with gravity disabled and the requested velocity
        assets_root_path = await get_assets_root_path_async()
        physics_asset_url = assets_root_path + PHYSICS_ASSET_URL
        for location, velocity in zip(ASSET_X_MIRRORED_LOCATIONS, ASSET_VELOCITIES):
            prim = rep.functional.create.reference(
                usd_path=physics_asset_url,
                parent="/World",
                name=f"physics_asset_{int(abs(velocity))}",
                position=location,
            )
            rigid_prim = RigidPrim(str(prim.GetPrimPath()))
            rigid_prim.set_enabled_gravities([False])
            rigid_prim.set_velocities(linear_velocities=[(0, 0, -velocity)], angular_velocities=[(0, 0, 0)])

        # Setup animated assets maintaining the same velocity as the physics assets
        anim_asset_url = assets_root_path + ANIM_ASSET_URL
        for location, velocity in zip(ASSET_X_MIRRORED_LOCATIONS, ASSET_VELOCITIES):
            start_location = (-location[0], location[1], location[2])
            prim = rep.functional.create.reference(
                usd_path=anim_asset_url,
                parent="/World",
                name=f"anim_asset_{int(abs(velocity))}",
                position=start_location,
            )
            animation_distance = velocity * ANIMATION_DURATION
            end_location = (start_location[0], start_location[1], start_location[2] - animation_distance)
            end_keyframe_time = timeline.get_time_codes_per_seconds() * ANIMATION_DURATION
            # Timesampled keyframe (animated) translation
            prim.GetAttribute("xformOp:translate").Set(start_location, time=0)
            prim.GetAttribute("xformOp:translate").Set(end_location, time=end_keyframe_time)

    async def run_motion_blur_example_rt_async(
        num_frames=NUM_FRAMES,
        delta_time=None,
        max_blur_diameter_fraction=0.02,
        exposure_fraction=1.0,
        num_samples=8,
    ):
        """Capture motion blur frames with the given delta time step using RTX Real-Time rendering."""
        await setup_stage_async()
        stage = omni.usd.get_context().get_stage()
        settings = carb.settings.get_settings()

        # Enable motion blur capture
        settings.set("/omni/replicator/captureMotionBlur", True)

        # Set RTX Real-Time (raytracing) motion blur settings
        print("[MotionBlur] Setting RealTimePathTracing render mode motion blur settings")
        settings.set("/rtx/rendermode", "RealTimePathTracing")
        # 0: Disabled, 1: TAA, 2: FXAA, 3: DLSS, 4:RTXAA
        settings.set("/rtx/post/aa/op", 2)
        # (float): The fraction of the largest screen dimension to use as the maximum motion blur diameter.
        settings.set("/rtx/post/motionblur/maxBlurDiameterFraction", max_blur_diameter_fraction)
        # (float): Exposure time fraction in frames (1.0 = one frame duration) to sample.
        settings.set("/rtx/post/motionblur/exposureFraction", exposure_fraction)
        # (int): Number of samples to use in the filter. A higher number improves quality at the cost of performance.
        settings.set("/rtx/post/motionblur/numSamples", num_samples)

        # Setup backend
        delta_time_str = "None" if delta_time is None else f"{delta_time:.4f}"
        output_directory = os.path.join(os.getcwd(), f"_out_motion_blur_func_dt_{delta_time_str}_rt")
        print(f"[MotionBlur] Output directory: {output_directory}")
        backend = rep.backends.get("DiskBackend")
        backend.initialize(output_dir=output_directory)

        # Setup writer and render product
        camera = rep.functional.create.camera(
            position=(0, 1.5, 0), look_at=(0, 0, 0), parent="/World", name="MotionBlurCam"
        )
        render_product = rep.create.render_product(camera, (1280, 720))
        writer = rep.WriterRegistry.get("BasicWriter")
        writer.initialize(backend=backend, rgb=True)
        writer.attach(render_product)

        # Run a few updates to make sure all materials are fully loaded for capture
        for _ in range(5):
            await omni.kit.app.get_app().next_update_async()

        rep.functional.physics.create_physics_scene(path="/PhysicsScene")
        physics_scene = PhysicsScene("/PhysicsScene")

        stage_time_codes_per_second = stage.GetTimeCodesPerSecond()
        target_physics_fps = stage_time_codes_per_second if delta_time is None else 1 / delta_time

        target_physics_dt = 1.0 / target_physics_fps
        original_physics_dt = physics_scene.get_dt()

        if target_physics_dt < original_physics_dt:
            print(f"[MotionBlur] Changing physics FPS from {1.0 / original_physics_dt:.0f} to {target_physics_fps:.0f}")
            physics_scene.set_dt(target_physics_dt)

        # Start the timeline
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        timeline.commit()

        for i in range(num_frames):
            print(f"[MotionBlur] \tCapturing frame {i}")
            await rep.orchestrator.step_async(delta_time=delta_time)

        if target_physics_dt < original_physics_dt:
            print(
                f"[MotionBlur] Restoring physics FPS from {target_physics_fps:.0f} to {1.0 / original_physics_dt:.0f}"
            )
            physics_scene.set_dt(original_physics_dt)

        # Wait until the data is fully written
        await rep.orchestrator.wait_until_complete_async()

        # Stop the timeline
        timeline.stop()
        timeline.commit()

        # Cleanup
        writer.detach()
        render_product.destroy()

    for delta_time in DELTA_TIMES:
        await run_motion_blur_example_rt_async(
            num_frames=NUM_FRAMES,
            delta_time=delta_time,
            max_blur_diameter_fraction=MAX_BLUR_DIAMETER_FRACTION,
            exposure_fraction=EXPOSURE_FRACTION,
            num_samples=NUM_SAMPLES,
        )


asyncio.ensure_future(run_motion_blur_examples_async())
