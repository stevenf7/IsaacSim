# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import os

import omni.kit
import omni.replicator.core as rep
import omni.timeline
import omni.usd

from .utils import validate_folder_contents


class TestSDGUsefulSnippets(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        await omni.kit.app.get_app().next_update_async()
        omni.usd.get_context().new_stage()
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self):
        omni.usd.get_context().close_stage()
        await omni.kit.app.get_app().next_update_async()
        # In some cases the test will end before the asset is loaded, in this case wait for assets to load
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await omni.kit.app.get_app().next_update_async()

    async def test_capture_data_with_timeline_running(self):
        await omni.kit.app.get_app().next_update_async()
        rep.orchestrator.set_capture_on_play(False)

        # Start timeline and run for a several frames
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        print(f"Running several app updates before writer initialization")
        for i in range(10):
            await omni.kit.app.get_app().next_update_async()

        # Create and attach the writer while the timeline is running
        out_dir = os.path.join(os.getcwd(), f"_out_timeline_running")
        print(f"output_directory: {out_dir}")
        basic_writer = rep.WriterRegistry.get("BasicWriter")
        basic_writer.initialize(output_dir=out_dir, rgb=True)
        rp = rep.create.render_product("/OmniverseKit_Persp", (1280, 720))
        basic_writer.attach(rp)

        # Run the simulation for a few frames (these frames should not be captured)
        for i in range(10):
            await omni.kit.app.get_app().next_update_async()

        # Capture frames
        num_frame_captures = 5
        print(f"Capturing {num_frame_captures} frames")
        for i in range(num_frame_captures):
            print(f"  Step {i}")
            await rep.orchestrator.step_async(delta_time=0.0, pause_timeline=False)

        # Wait for the writer to finish
        await rep.orchestrator.wait_until_complete_async()
        basic_writer.detach()
        rp.destroy()
        timeline.stop()

        # Validate the output directory contents
        folder_contents_success = validate_folder_contents(path=out_dir, expected_counts={"png": num_frame_captures})
        self.assertTrue(folder_contents_success, f"Output directory contents validation failed for {out_dir}")
