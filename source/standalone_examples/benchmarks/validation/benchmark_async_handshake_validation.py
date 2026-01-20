#!/usr/bin/env python3

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

"""
Standalone script to validate async rendering with handshake mode.

This script runs a simple simulation with async rendering and handshake enabled,
then validates that the FrametimeStats contain both App_Update and Render stats
with reasonable values.

Usage:
    python benchmark_async_handshake_validation.py [--num-frames N]
"""

import argparse
import sys

# Parse arguments before SimulationApp initialization
parser = argparse.ArgumentParser(description="Validate async rendering with handshake mode")
parser.add_argument("--num-frames", type=int, default=100, help="Number of frames to simulate (default: 100)")
parser.add_argument("--non-headless", action="store_false", help="Run with GUI - nonheadless mode")
args, unknown = parser.parse_known_args()

headless = args.non_headless

from isaacsim import SimulationApp

# Launch SimulationApp with async rendering and handshake enabled
# Note: /renderer/asyncInit=false forces synchronous hydra engine initialization.
# This ensures the RTX engine attaches during startup (critical for framework test mode).
# This is separate from /app/asyncRendering which controls async render thread execution.
simulation_app = SimulationApp(
    {
        "headless": headless,
        "extra_args": [
            "--/app/asyncRendering=true",
            "--/app/omni.usd/asyncHandshake=true",
            "--/renderer/asyncInit=false",
        ],
    }
)

import carb

# Enable the benchmark services extension to access collectors
import omni.kit.app
import omni.usd

ext_manager = omni.kit.app.get_app().get_extension_manager()
ext_manager.set_extension_enabled_immediate("isaacsim.benchmark.services", True)

# Wait for extension to fully load
for _ in range(10):
    omni.kit.app.get_app().update()


from isaacsim.core.api import SimulationContext
from pxr import UsdGeom


def validate_async_handshake_behavior(num_frames: int = 100) -> bool:
    """Run a simulation with async rendering + handshake and validate behavior.

    Args:
        num_frames: Number of frames to simulate.

    Returns:
        True if validation passes, False otherwise.
    """
    # Verify async settings are actually enabled
    settings = carb.settings.get_settings()
    async_rendering = settings.get("/app/asyncRendering")
    async_handshake = settings.get("/app/omni.usd/asyncHandshake")
    replicator_async = settings.get("/omni/replicator/asyncRendering")

    print("=" * 60)
    print("ASYNC RENDERING SETTINGS")
    print("=" * 60)
    print(f"  /app/asyncRendering: {async_rendering}")
    print(f"  /app/omni.usd/asyncHandshake: {async_handshake}")
    print(f"  /omni/replicator/asyncRendering: {replicator_async}")
    print("=" * 60)
    print()

    if not async_rendering:
        print("✗ [error] Async rendering is NOT enabled!")
        return False
    if not async_handshake:
        print("✗ [error] Async handshake is NOT enabled!")
        return False

    # Create a new stage with simple scene
    omni.usd.get_context().new_stage()
    stage = omni.usd.get_context().get_stage()

    # Add simple geometry to trigger rendering
    sphere = UsdGeom.Sphere.Define(stage, "/World/Sphere")
    sphere.GetRadiusAttr().Set(1.0)

    # Create simulation context and initialize physics
    simulation_context = SimulationContext()
    simulation_context.initialize_physics()

    print(f"Starting simulation with async rendering + handshake enabled")
    print(f"Will simulate {num_frames} frames")
    print()

    # Import the frametime collector to measure stats
    from isaacsim.benchmark.services.collectors import IsaacUpdateFrametimeCollector

    collector = IsaacUpdateFrametimeCollector(gpu_frametime=True)
    collector.start_collecting()

    # Start simulation
    simulation_context.play()

    # Give render thread time to initialize
    for i in range(5):
        simulation_context.step()

    carb.log_info(
        f"After warmup - Render samples: {len(collector.render_frametimes_ms)}, App samples: {len(collector.app_frametimes_ms)}"
    )

    # Run simulation for N frames
    for frame in range(num_frames):
        simulation_context.step()
        if frame % 10 == 0:
            carb.log_info(
                f"Frame {frame}/{num_frames} - Render: {len(collector.render_frametimes_ms)}, App: {len(collector.app_frametimes_ms)}"
            )

    # Stop collecting
    collector.stop_collecting()

    carb.log_info(
        f"Collection stopped - Final counts: Render={len(collector.render_frametimes_ms)}, App={len(collector.app_frametimes_ms)}"
    )

    # Analyze results
    print()
    print("=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)

    validation_passed = True

    # Check App_Update stats
    app_frames = len(collector.app_frametimes_ms)
    if app_frames > 0:
        app_mean = sum(collector.app_frametimes_ms) / len(collector.app_frametimes_ms)
        print(f"✓ App_Update frames collected: {app_frames}")
        print(f"  Mean App_Update frametime: {app_mean:.2f} ms")
    else:
        print("✗ [fail] No App_Update frames collected!")
        validation_passed = False

    # Check Render stats (key validation for async + handshake)
    render_frames = len(collector.render_frametimes_ms)
    if render_frames > 0:
        render_mean = sum(collector.render_frametimes_ms) / len(collector.render_frametimes_ms)
        print(f"✓ Render frames collected: {render_frames}")
        print(f"  Mean Render frametime: {render_mean:.2f} ms")

        # Validate that render stats exist (they don't in sync mode)
        print("✓ Render stats present (confirms async rendering is active)")
    else:
        print("✗ [fail] No Render frames collected!")
        print("  This suggests async rendering may not be working correctly")
        validation_passed = False

    # Validate frame count similarity (key for handshake validation)
    if app_frames > 0 and render_frames > 0:
        frame_diff = abs(app_frames - render_frames)
        frame_tolerance = max(app_frames, render_frames) * 0.05  # 5% tolerance

        if frame_diff < frame_tolerance:
            print(f"✓ Frame counts similar: App={app_frames}, Render={render_frames}")
            print("  This confirms handshake is synchronizing threads")
        else:
            print(f"⚠ Frame count mismatch: App={app_frames}, Render={render_frames}")
            print(f"  Difference: {frame_diff}, tolerance: {frame_tolerance:.1f}")
            print("  Handshake may not be working as expected")
            validation_passed = False

        # Validate mean frametime similarity
        ratio = max(app_mean, render_mean) / min(app_mean, render_mean)
        if ratio < 1.25:
            print(f"✓ Frametime ratio reasonable: {ratio:.2f}x")
            print("  App and Render threads are in sync")
        else:
            print(f"⚠ Large frametime ratio: {ratio:.2f}x")
            print("  Threads may not be properly synchronized")
            validation_passed = False

    # Check GPU stats if available
    if len(collector.gpu_frametimes_ms) > 0:
        gpu_mean = sum(collector.gpu_frametimes_ms) / len(collector.gpu_frametimes_ms)
        print(f"  Mean GPU frametime: {gpu_mean:.2f} ms")

    # Check Physics stats if available
    if len(collector.physics_frametimes_ms) > 0:
        physics_mean = sum(collector.physics_frametimes_ms) / len(collector.physics_frametimes_ms)
        print(f"  Mean Physics frametime: {physics_mean:.2f} ms")

    print("=" * 60)

    if validation_passed:
        print("✓ VALIDATION PASSED")
        print("  Async rendering with handshake is working correctly!")
    else:
        print("✗ VALIDATION [fail] - Async rendering handshake test failed")
        print("  Issues detected with async rendering handshake mode")

    print("=" * 60)
    print()

    return validation_passed


def main():
    """Main function."""
    try:
        validation_passed = validate_async_handshake_behavior(args.num_frames)

        # Clean shutdown
        simulation_app.close()

        # Return appropriate exit code
        sys.exit(0 if validation_passed else 1)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback

        traceback.print_exc()
        simulation_app.close()
        sys.exit(1)


if __name__ == "__main__":
    main()
