# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
"""Demonstrate replaying a recorded teleoperation episode and generating synthetic data."""

import os

from isaacsim import SimulationApp

simulation_app = SimulationApp(
    launch_config={
        "headless": False,
        "extra_args": ["--enable", "isaacsim.replicator.episode_recorder"],
    }
)

import carb.settings
import omni.replicator.core as rep
import omni.usd
from isaacsim.replicator.episode_recorder import EpisodeReplayer
from isaacsim.storage.native import get_assets_root_path
from pxr import UsdGeom

# Path to the USD stage to replay against; every prim path in the HDF5 must resolve on this stage.
STAGE_URL = "/Isaac/Samples/Replicator/Teleop/teleop_scenario_floating_xarm_dex3.usd"
HDF5_PATH = "/tmp/demos/episode_20260417T120000Z.hdf5"
CAMERA_PATHS = [
    "/World/teleop_xarm_dex3/gripper_origin_xform/xarm_gripper_root_xform/xarm_gripper/xarm_gripper_base_link/xarm_view_cam",
    "/World/teleop_xarm_dex3/gripper_origin_xform/dex3_1_r_root_xform/dex3_1_r/right_hand_palm_link/dex3_view_cam",
]
EPISODE_INDEX = 0
RESOLUTION = (512, 512)


def run_example():
    print("[TeleopReplay] Starting replay example")
    if not HDF5_PATH:
        print("[TeleopReplay] HDF5 path not provided, exiting")
        return
    if not os.path.isfile(HDF5_PATH):
        print(f"[TeleopReplay] HDF5 session file does not exist: '{HDF5_PATH}', exiting")
        return
    print(f"[TeleopReplay] HDF5 session: {HDF5_PATH}")

    # Load the authored USD stage so every prim path in the HDF5 resolves.
    assets_root_path = get_assets_root_path()
    if assets_root_path is None:
        print("[TeleopReplay] Could not find Isaac Sim assets folder, exiting")
        return
    stage_path = assets_root_path + STAGE_URL
    print(f"[TeleopReplay] Opening stage: {stage_path}")
    omni.usd.get_context().open_stage(stage_path)
    print("[TeleopReplay] Stage opened")

    # Drive writers manually via rep.orchestrator.step, not via timeline play.
    rep.orchestrator.set_capture_on_play(False)

    # Set DLSS to Quality mode (2) for best SDG results (Options: 0 (Performance), 1 (Balanced), 2 (Quality), 3 (Auto)
    carb.settings.get_settings().set("rtx/post/dlss/execMode", 2)

    # Resolve CAMERA_PATHS to UsdGeom.Camera prims; fall back to a default (5,5,5)
    # camera looking at the origin when CAMERA_PATHS is empty or none resolve.
    stage = omni.usd.get_context().get_stage()
    valid_camera_paths: list[str] = []
    for path in CAMERA_PATHS:
        prim = stage.GetPrimAtPath(path) if path else None
        if prim is None or not prim.IsValid():
            print(f"[TeleopReplay] Camera path '{path}' not found in stage, skipping")
            continue
        if not prim.IsA(UsdGeom.Camera):
            print(f"[TeleopReplay] Prim at '{path}' is not a UsdGeom.Camera (type={prim.GetTypeName()}), skipping")
            continue
        valid_camera_paths.append(path)

    render_products = []
    if valid_camera_paths:
        print(f"[TeleopReplay] Using {len(valid_camera_paths)} scene camera(s): {valid_camera_paths}")
        for i, cam_path in enumerate(valid_camera_paths):
            render_products.append(rep.create.render_product(cam_path, RESOLUTION, name=f"ReplayRP_{i}"))
    else:
        if CAMERA_PATHS:
            print(
                "[TeleopReplay] No valid scene cameras found in CAMERA_PATHS, falling back to default (5,5,5) camera."
            )
        cam = rep.functional.create.camera(position=(5, 5, 5), look_at=(0, 0, 0), name="ReplayCamera")
        render_products.append(rep.create.render_product(cam, RESOLUTION, name="ReplayRP"))
    print(f"[TeleopReplay] Created {len(render_products)} render product(s) at resolution {RESOLUTION}")

    # BasicWriter for RGB PNGs with its own DiskBackend / output subdir.
    out_root = os.path.join(os.getcwd(), "_out_teleop_replay")
    print(f"[TeleopReplay] Output root: {out_root}")

    basic_backend = rep.backends.get("DiskBackend")
    basic_backend.initialize(output_dir=os.path.join(out_root, "basic"))
    basic_writer = rep.writers.get("BasicWriter")
    basic_writer.initialize(backend=basic_backend, rgb=True)
    basic_writer.attach(render_products)
    print(f"[TeleopReplay] BasicWriter attached -> {os.path.join(out_root, 'basic')}")

    # Prepare the episode and capture one RGB frame per recorded frame.
    print(f"[TeleopReplay] Preparing episode {EPISODE_INDEX}")
    try:
        replayer = EpisodeReplayer(HDF5_PATH)
        # Start replay with seek_timeline=True to match recorded sim_time, then pause to manually step and capture.
        replayer.start_replay(episode=EPISODE_INDEX, seek_timeline=True)
        replayer.pause_replay()
    except Exception as exc:
        print(f"[TeleopReplay] Could not start replay for episode {EPISODE_INDEX} from '{HDF5_PATH}': {exc}, exiting")
        return
    num_frames = replayer.num_frames(EPISODE_INDEX)
    if num_frames <= 0:
        print(f"[TeleopReplay] Episode {EPISODE_INDEX} has no frames in '{HDF5_PATH}', exiting")
        replayer.close()
        return
    print(f"[TeleopReplay] Replaying episode {EPISODE_INDEX} ({num_frames} frames)")

    progress_every = max(1, num_frames // 10)
    for f in range(num_frames):
        if f > 0:
            replayer.step_frame(1)
        rep.orchestrator.step(delta_time=0.0, pause_timeline=False)
        if (f + 1) % progress_every == 0 or (f + 1) == num_frames:
            print(f"[TeleopReplay] Captured frame {f + 1} / {num_frames}")

    # Wait for the data to be written to disk and clean up resources.
    print("[TeleopReplay] Waiting for writers to flush...")
    rep.orchestrator.wait_until_complete()
    basic_writer.detach()
    for rp in render_products:
        rp.destroy()
    replayer.close()
    print(f"[TeleopReplay] Done. Output: {out_root}")


# Run the example
run_example()

simulation_app.close()
