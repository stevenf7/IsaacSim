# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
import argparse
import logging
import os
import time

import numpy as np
from isaacsim import SimulationApp

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("tf_cam_sync_test")

# CLI args
parser = argparse.ArgumentParser()
parser.add_argument("--test-steps", type=int, default=30)
args, _ = parser.parse_known_args()

# Launch Isaac Sim in headless zero-delay mode
simulation_app = SimulationApp(
    {"headless": True}, experience=f'{os.environ["EXP_PATH"]}/isaacsim.exp.base.zero_delay.kit'
)

# Import post-launch modules
import omni.graph.core as og
import omni.usd
import usdrt.Sdf
from isaacsim.core.api import World
from isaacsim.core.api.objects import DynamicCuboid
from isaacsim.core.utils.extensions import enable_extension
from isaacsim.core.utils.viewports import set_camera_view

enable_extension("isaacsim.ros2.bridge")
simulation_app.update()

import rclpy
from sensor_msgs.msg import Image
from tf2_msgs.msg import TFMessage

rclpy.init()

# ROS state
tf_msg = None
img_msg = None
tf_recv_time = None
img_recv_time = None
tf_recv_count = 0
img_recv_count = 0


def tf_callback(msg):
    global tf_msg, tf_recv_time, tf_recv_count
    tf_msg = msg
    tf_recv_time = time.perf_counter()
    tf_recv_count += 1
    stamp = msg.transforms[0].header.stamp
    log.debug(
        f"  TF  callback #{tf_recv_count}: stamp={stamp.sec}.{stamp.nanosec:09d}, "
        f"frame_id='{msg.transforms[0].header.frame_id}', "
        f"child_frame_id='{msg.transforms[0].child_frame_id}'"
    )


def img_callback(msg):
    global img_msg, img_recv_time, img_recv_count
    img_msg = msg
    img_recv_time = time.perf_counter()
    img_recv_count += 1
    stamp = msg.header.stamp
    log.debug(
        f"  IMG callback #{img_recv_count}: stamp={stamp.sec}.{stamp.nanosec:09d}, "
        f"encoding='{msg.encoding}', size={msg.width}x{msg.height}"
    )


# Create ROS2 node + subscribers
node = rclpy.create_node("sync_test_node")
tf_sub = node.create_subscription(TFMessage, "/tf_test", tf_callback, 10)
img_sub = node.create_subscription(Image, "rgb", img_callback, 10)

# Create world and add cube
world = World(physics_dt=1.0 / 60.0, rendering_dt=1.0 / 60.0)
CUBE_PRIM_PATH = "/Cube"
cube = world.scene.add(DynamicCuboid(prim_path=CUBE_PRIM_PATH, scale=[0.5, 0.5, 0.5]))
world.scene.add_default_ground_plane()

# Add camera
CAMERA_PRIM_PATH = "/Camera"
CAMERA_EYE = [0, -2, 1]
CAMERA_TARGET = [0, 0, 0.1]

stage = omni.usd.get_context().get_stage()
stage.DefinePrim(CAMERA_PRIM_PATH, "Camera")
set_camera_view(eye=CAMERA_EYE, target=CAMERA_TARGET, camera_prim_path=CAMERA_PRIM_PATH)

world.reset()

# Create Action Graph
og.Controller.edit(
    {"graph_path": "/ActionGraph", "evaluator_name": "execution"},
    {
        og.Controller.Keys.CREATE_NODES: [
            ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
            ("ReadSimTime", "isaacsim.core.nodes.IsaacReadSimulationTime"),
            ("TfPublisher", "isaacsim.ros2.bridge.ROS2PublishTransformTree"),
            ("CameraPublisher", "isaacsim.ros2.bridge.ROS2CameraHelper"),
            ("CreateRenderProduct", "isaacsim.core.nodes.IsaacCreateRenderProduct"),
        ],
        og.Controller.Keys.SET_VALUES: [
            ("TfPublisher.inputs:targetPrims", [usdrt.Sdf.Path(CUBE_PRIM_PATH)]),
            ("TfPublisher.inputs:topicName", "/tf_test"),
            ("CameraPublisher.inputs:type", "rgb"),
            ("CameraPublisher.inputs:topicName", "rgb"),
            ("CreateRenderProduct.inputs:cameraPrim", [usdrt.Sdf.Path(CAMERA_PRIM_PATH)]),
            ("CreateRenderProduct.inputs:width", 1920),
            ("CreateRenderProduct.inputs:height", 1080),
        ],
        og.Controller.Keys.CONNECT: [
            ("OnPlaybackTick.outputs:tick", "TfPublisher.inputs:execIn"),
            ("OnPlaybackTick.outputs:tick", "CreateRenderProduct.inputs:execIn"),
            ("ReadSimTime.outputs:simulationTime", "TfPublisher.inputs:timeStamp"),
            ("CreateRenderProduct.outputs:execOut", "CameraPublisher.inputs:execIn"),
            ("CreateRenderProduct.outputs:renderProductPath", "CameraPublisher.inputs:renderProductPath"),
        ],
    },
)

simulation_app.update()
log.info("Action graph created, starting warmup...")

# Warmup
for i in range(20):
    world.step(render=True)
    rclpy.spin_once(node, timeout_sec=0.0)
    warmup_tf = tf_msg is not None
    warmup_img = img_msg is not None
    if i % 5 == 0 or warmup_tf or warmup_img:
        log.debug(f"  warmup step {i}: tf_received={warmup_tf}, img_received={warmup_img}")

log.info(f"Warmup complete. Total callbacks so far: tf={tf_recv_count}, img={img_recv_count}")

# Flush the render pipeline: the camera publisher has ~1 frame of latency, so after
# clearing warmup messages we need to step+spin once more to drain the stale render
# frame. Without this, the first test step receives an image stamped from the previous
# warmup frame while TF already carries the current frame's timestamp.
tf_msg = None
img_msg = None
world.step(render=True)
for _ in range(20):
    rclpy.spin_once(node, timeout_sec=0.05)
    if tf_msg is not None and img_msg is not None:
        break
log.info(f"Pipeline flush: tf_msg={'OK' if tf_msg else 'NONE'}, " f"img_msg={'OK' if img_msg else 'NONE'}")
tf_msg = None
img_msg = None

# Run sync test
log.info(f"Starting sync test with {args.test_steps} steps...")
deltas = []
missed_steps = []
for step in range(args.test_steps):
    step_start = time.perf_counter()
    new_pos = np.random.uniform(-1, 1, 3)
    cube.set_world_pose(position=new_pos)
    world.step(render=True)
    step_elapsed = time.perf_counter() - step_start

    # Block to make sure both messages are received
    MAX_WAIT_STEPS = 20
    wait_count = 0
    spin_start = time.perf_counter()
    while (tf_msg is None or img_msg is None) and wait_count < MAX_WAIT_STEPS:
        rclpy.spin_once(node, timeout_sec=0.05)
        wait_count += 1
    spin_elapsed = time.perf_counter() - spin_start

    if tf_msg and img_msg:
        tf_stamp = tf_msg.transforms[0].header.stamp
        img_stamp = img_msg.header.stamp
        tf_ns = tf_stamp.sec * 1e9 + tf_stamp.nanosec
        img_ns = img_stamp.sec * 1e9 + img_stamp.nanosec
        delta = abs(tf_ns - img_ns)
        deltas.append(delta)

        # Determine which message has the later timestamp
        behind = "TF" if tf_ns < img_ns else ("IMG" if img_ns < tf_ns else "EQUAL")

        log.info(
            f"Step {step:3d}: "
            f"tf_stamp={tf_stamp.sec}.{tf_stamp.nanosec:09d}  "
            f"img_stamp={img_stamp.sec}.{img_stamp.nanosec:09d}  "
            f"delta={delta / 1e6:8.3f} ms  "
            f"behind={behind}  "
            f"spins={wait_count}  "
            f"step_time={step_elapsed * 1000:.1f} ms  "
            f"spin_time={spin_elapsed * 1000:.1f} ms  "
            f"tf_recv_wall={tf_recv_time:.6f}  "
            f"img_recv_wall={img_recv_time:.6f}  "
            f"wall_recv_delta={(abs(tf_recv_time - img_recv_time)) * 1000:.3f} ms"
        )
    else:
        missed_steps.append(step)
        log.warning(
            f"Step {step:3d}: MISSED - tf_msg={'OK' if tf_msg else 'NONE'}, "
            f"img_msg={'OK' if img_msg else 'NONE'}, "
            f"spins={wait_count}, spin_time={spin_elapsed * 1000:.1f} ms"
        )

    # Reset messages
    tf_msg = None
    img_msg = None

# Print results
log.info("=" * 80)
log.info("SUMMARY")
log.info("=" * 80)
log.info(f"Total TF  callbacks received: {tf_recv_count}")
log.info(f"Total IMG callbacks received: {img_recv_count}")
log.info(f"Total test steps:             {args.test_steps}")
log.info(f"Steps with valid pair:        {len(deltas)}")
log.info(f"Missed steps:                 {len(missed_steps)} {missed_steps if missed_steps else ''}")

if deltas:
    avg_delay = np.mean(deltas) / 1e6
    max_delay = np.max(deltas) / 1e6
    min_delay = np.min(deltas) / 1e6
    median_delay = np.median(deltas) / 1e6
    std_delay = np.std(deltas) / 1e6

    # Classify the deltas
    zero_count = sum(1 for d in deltas if d == 0)
    one_frame_count = sum(1 for d in deltas if abs(d / 1e6 - 16.667) < 1.0)
    other_count = len(deltas) - zero_count - one_frame_count

    THRESHOLD_MS = 0.0
    passed = max_delay <= THRESHOLD_MS

    print("\nTF / CAMERA TIMESTAMP SYNC TEST")
    print(f"Steps:              {len(deltas)}")
    print(f"Average delay:      {avg_delay:.3f} ms")
    print(f"Median delay:       {median_delay:.3f} ms")
    print(f"Std dev:            {std_delay:.3f} ms")
    print(f"Min delay:          {min_delay:.3f} ms")
    print(f"Max delay:          {max_delay:.3f} ms  (threshold: {THRESHOLD_MS} ms)")
    print(f"Zero-delta steps:   {zero_count}/{len(deltas)}")
    print(f"One-frame (~16ms):  {one_frame_count}/{len(deltas)}")
    print(f"Other:              {other_count}/{len(deltas)}")
    print("Status:        ", "PASS ✅" if passed else "[fatal] ❌")

    if not passed:
        log.error(
            f"FAIL: max_delay={max_delay:.3f} ms >= {THRESHOLD_MS} ms threshold. "
            f"At least one frame had TF and camera timestamps from different "
            f"simulation frames. A delay of ~16.667 ms = exactly 1 frame at 60 FPS, "
            f"suggesting a pipeline ordering issue where one publisher reads the "
            f"sim time before the step and the other reads it after."
        )
else:
    print("\n[error] No messages received.")
    log.error(
        f"No message pairs received at all. "
        f"TF callbacks={tf_recv_count}, IMG callbacks={img_recv_count}. "
        f"Check that the action graph is wired correctly and ROS2 bridge is loaded."
    )

# Cleanup
node.destroy_node()
rclpy.shutdown()
simulation_app.close()
