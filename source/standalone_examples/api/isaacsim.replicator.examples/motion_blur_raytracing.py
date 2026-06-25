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

"""Demonstrate motion blur capture with the RTX Real-Time (raytracing) render mode."""

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": False})

import argparse
import os

import carb.settings
import isaacsim.core.experimental.utils.stage as stage_utils
import omni.replicator.core as rep
import omni.timeline
import omni.usd
from isaacsim.core.experimental.prims import RigidPrim
from isaacsim.core.simulation_manager import PhysicsScene
from isaacsim.storage.native import get_assets_root_path

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


def parse_delta_time(value: str) -> float | None:
    """Convert string to float or None. Accepts 'None', -1, 0, or numeric values."""
    if value.lower() == "none":
        return None
    float_value = float(value)
    return None if float_value in (-1, 0) else float_value


parser = argparse.ArgumentParser()
parser.add_argument(
    "--delta_times",
    nargs="*",
    type=parse_delta_time,
    default=[None, 1 / 30, 1 / 60, 1 / 240],
    help="List of delta times (seconds per frame) to use for motion blur captures. Use 'None' for default stage time.",
)
parser.add_argument(
    "--max_blur_diameter_fraction",
    type=float,
    default=0.02,
    help="Fraction of the largest screen dimension to use as the maximum motion blur diameter.",
)
parser.add_argument(
    "--exposure_fraction",
    type=float,
    default=1.0,
    help="Exposure time fraction in frames (1.0 = one frame duration) to sample.",
)
parser.add_argument(
    "--num_samples",
    type=int,
    default=8,
    help="Number of samples to use in the motion blur filter. Higher values improve quality at the cost of performance.",
)
args, _ = parser.parse_known_args()
delta_times = args.delta_times
max_blur_diameter_fraction = args.max_blur_diameter_fraction
exposure_fraction = args.exposure_fraction
num_samples = args.num_samples


def setup_stage() -> None:
    """Create a new USD stage with animated and physics-enabled assets with synchronized motion."""
    stage_utils.create_new_stage()
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
    assets_root_path = get_assets_root_path()
    physics_asset_url = assets_root_path + PHYSICS_ASSET_URL
    for location, velocity in zip(ASSET_X_MIRRORED_LOCATIONS, ASSET_VELOCITIES):
        prim = rep.functional.create.reference(
            usd_path=physics_asset_url, parent="/World", name=f"physics_asset_{int(abs(velocity))}", position=location
        )
        rigid_prim = RigidPrim(str(prim.GetPrimPath()))
        rigid_prim.set_enabled_gravities([False])
        rigid_prim.set_velocities(linear_velocities=[(0, 0, -velocity)], angular_velocities=[(0, 0, 0)])

    # Setup animated assets maintaining the same velocity as the physics assets
    anim_asset_url = assets_root_path + ANIM_ASSET_URL
    for location, velocity in zip(ASSET_X_MIRRORED_LOCATIONS, ASSET_VELOCITIES):
        start_location = (-location[0], location[1], location[2])
        prim = rep.functional.create.reference(
            usd_path=anim_asset_url, parent="/World", name=f"anim_asset_{int(abs(velocity))}", position=start_location
        )
        animation_distance = velocity * ANIMATION_DURATION
        end_location = (start_location[0], start_location[1], start_location[2] - animation_distance)
        end_keyframe_time = timeline.get_time_codes_per_seconds() * ANIMATION_DURATION
        # Timesampled keyframe (animated) translation
        prim.GetAttribute("xformOp:translate").Set(start_location, time=0)
        prim.GetAttribute("xformOp:translate").Set(end_location, time=end_keyframe_time)


def run_motion_blur_example_rt(
    num_frames: int,
    delta_time: float | None = None,
    max_blur_diameter_fraction: float = 0.02,
    exposure_fraction: float = 1.0,
    num_samples: int = 8,
) -> None:
    """Capture motion blur frames with the given delta time step using RTX Real-Time rendering."""
    setup_stage()
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
        simulation_app.update()

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
        rep.orchestrator.step(delta_time=delta_time)

    if target_physics_dt < original_physics_dt:
        print(f"[MotionBlur] Restoring physics FPS from {target_physics_fps:.0f} to {1.0 / original_physics_dt:.0f}")
        physics_scene.set_dt(original_physics_dt)

    # Wait until the data is fully written
    rep.orchestrator.wait_until_complete()

    # Stop the timeline
    timeline.stop()
    timeline.commit()

    # Cleanup
    writer.detach()
    render_product.destroy()


def run_motion_blur_examples(
    num_frames: int,
    delta_times: list[float | None],
    max_blur_diameter_fraction: float,
    exposure_fraction: float,
    num_samples: int,
) -> None:
    """Run RTX Real-Time motion blur examples across all delta times."""
    print(
        f"[MotionBlur] Running with delta_times={delta_times}, "
        f"max_blur_diameter_fraction={max_blur_diameter_fraction}, "
        f"exposure_fraction={exposure_fraction}, num_samples={num_samples}"
    )
    for delta_time in delta_times:
        run_motion_blur_example_rt(
            num_frames=num_frames,
            delta_time=delta_time,
            max_blur_diameter_fraction=max_blur_diameter_fraction,
            exposure_fraction=exposure_fraction,
            num_samples=num_samples,
        )


run_motion_blur_examples(
    num_frames=NUM_FRAMES,
    delta_times=delta_times,
    max_blur_diameter_fraction=max_blur_diameter_fraction,
    exposure_fraction=exposure_fraction,
    num_samples=num_samples,
)

# <start-motion-blur-test>
import sys

from isaacsim.core.utils.extensions import enable_extension

enable_extension("isaacsim.test.utils")
from isaacsim.test.utils.file_validation import validate_folder_contents

test_parser = argparse.ArgumentParser()
test_parser.add_argument(
    "--test",
    action="store_true",
    help="Validate captured output files against expected counts and exit.",
)
test_args, _ = test_parser.parse_known_args()

if test_args.test:
    # Each run_motion_blur_example_rt call produces one output dir with NUM_FRAMES rgb pngs.
    # Mirror the iteration in run_motion_blur_examples to reconstruct the expected dir names.
    expected_out_dirs = []
    for dt in delta_times:
        dt_str = "None" if dt is None else f"{dt:.4f}"
        expected_out_dirs.append(os.path.join(os.getcwd(), f"_out_motion_blur_func_dt_{dt_str}_rt"))

    for out_dir in expected_out_dirs:
        if not validate_folder_contents(
            path=out_dir,
            recursive=True,
            expected_counts={"png": NUM_FRAMES},
            fail_on_empty_files=True,
        ):
            print(f"[SDG][Test][FAIL] Output validation failed for {out_dir}")
            sys.exit(1)
        print(f"[SDG][Test][PASS] Output validation succeeded for {out_dir}")
# <end-motion-blur-test>

simulation_app.close()
