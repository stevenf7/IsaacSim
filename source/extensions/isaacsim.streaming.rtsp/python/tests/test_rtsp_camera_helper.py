# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

from __future__ import annotations

from unittest.mock import patch

import omni.graph.core as og
import omni.kit.test
import omni.replicator.core as rep
import omni.timeline
import omni.usd
from isaacsim.core.nodes import BaseWriterNode
from isaacsim.streaming.rtsp.impl.rtsp_writer import WRITER_NAME, RTSPStreamWriter


class TestRTSPExtensionRegistration(omni.kit.test.AsyncTestCase):
    """Verify the RTSP streaming extension registers the writer correctly on startup."""

    async def setUp(self):
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()

    async def test_writer_is_registered(self):
        writers = rep.WriterRegistry.get_writers()
        self.assertIn(WRITER_NAME, writers)

    async def test_writer_get_returns_correct_type(self):
        writer = rep.writers.get(WRITER_NAME)
        self.assertIsInstance(writer, RTSPStreamWriter)

    async def test_writer_in_default_writers_list(self):
        self.assertIn(WRITER_NAME, rep.WriterRegistry._default_writers)

    async def test_registered_writer_exposes_writer_interface(self):
        writer = rep.writers.get(WRITER_NAME)
        self.assertTrue(callable(writer.write))
        self.assertTrue(callable(writer.detach))


class TestRTSPCameraHelperEncoding(omni.kit.test.AsyncTestCase):
    """Verify the OGN node passes the correct encoding based on useRawEncoding."""

    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()

    def _create_rtsp_graph(self, use_raw_encoding):
        """Build an action graph with an RTSPCameraHelper node."""
        stage = omni.usd.get_context().get_stage()
        stage.DefinePrim("/TestRenderProduct", "RenderProduct")

        keys = og.Controller.Keys
        og.Controller.edit(
            {"graph_path": "/TestGraph", "evaluator_name": "execution"},
            {
                keys.CREATE_NODES: [
                    ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                    ("RTSPHelper", "isaacsim.streaming.rtsp.RTSPCameraHelper"),
                ],
                keys.SET_VALUES: [
                    ("RTSPHelper.inputs:renderProductPath", "/TestRenderProduct"),
                    ("RTSPHelper.inputs:port", 8554),
                    ("RTSPHelper.inputs:mountPath", "/stream"),
                    ("RTSPHelper.inputs:useRawEncoding", use_raw_encoding),
                    ("RTSPHelper.inputs:enabled", True),
                ],
                keys.CONNECT: [
                    ("OnPlaybackTick.outputs:tick", "RTSPHelper.inputs:execIn"),
                ],
            },
        )

    async def _evaluate_graph(self):
        """Play the timeline for one tick to trigger the action graph."""
        timeline = omni.timeline.get_timeline_interface()
        timeline.play()
        await omni.kit.app.get_app().next_update_async()
        timeline.stop()
        await omni.kit.app.get_app().next_update_async()

    def _capture_writer_init(self):
        """Return (init_calls, context_manager) that intercepts RTSPStreamWriter construction.

        Does NOT call through to the real __init__ to avoid creating live
        annotators that would receive frames during timeline playback.
        """
        init_calls = []

        def stub_init(writer_self, *args, **kwargs):
            init_calls.append(kwargs)

        ctx = patch.object(RTSPStreamWriter, "__init__", stub_init)
        return init_calls, ctx

    async def test_use_raw_encoding_passes_raw(self):
        self._create_rtsp_graph(use_raw_encoding=True)
        init_calls, spy_ctx = self._capture_writer_init()

        with spy_ctx, patch.object(BaseWriterNode, "append_writer"), patch.object(BaseWriterNode, "attach_writers"):
            await self._evaluate_graph()

        self.assertGreaterEqual(len(init_calls), 1)
        self.assertEqual(init_calls[0]["port"], 8554)
        self.assertEqual(init_calls[0]["mountPath"], "/stream")
        self.assertEqual(init_calls[0]["encoding"], "raw")

    async def test_default_encoding_passes_h264(self):
        self._create_rtsp_graph(use_raw_encoding=False)
        init_calls, spy_ctx = self._capture_writer_init()

        with spy_ctx, patch.object(BaseWriterNode, "append_writer"), patch.object(BaseWriterNode, "attach_writers"):
            await self._evaluate_graph()

        self.assertGreaterEqual(len(init_calls), 1)
        self.assertEqual(init_calls[0]["port"], 8554)
        self.assertEqual(init_calls[0]["mountPath"], "/stream")
        self.assertEqual(init_calls[0]["encoding"], "h264")

    async def test_empty_render_product_path_skips_setup(self):
        keys = og.Controller.Keys
        og.Controller.edit(
            {"graph_path": "/TestGraph", "evaluator_name": "execution"},
            {
                keys.CREATE_NODES: [
                    ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                    ("RTSPHelper", "isaacsim.streaming.rtsp.RTSPCameraHelper"),
                ],
                keys.SET_VALUES: [
                    ("RTSPHelper.inputs:renderProductPath", ""),
                    ("RTSPHelper.inputs:enabled", True),
                ],
                keys.CONNECT: [
                    ("OnPlaybackTick.outputs:tick", "RTSPHelper.inputs:execIn"),
                ],
            },
        )
        init_calls, spy_ctx = self._capture_writer_init()

        with spy_ctx:
            await self._evaluate_graph()

        self.assertEqual(len(init_calls), 0)

    async def test_missing_render_product_prim_skips_setup(self):
        keys = og.Controller.Keys
        og.Controller.edit(
            {"graph_path": "/TestGraph", "evaluator_name": "execution"},
            {
                keys.CREATE_NODES: [
                    ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                    ("RTSPHelper", "isaacsim.streaming.rtsp.RTSPCameraHelper"),
                ],
                keys.SET_VALUES: [
                    ("RTSPHelper.inputs:renderProductPath", "/NonExistentPrim"),
                    ("RTSPHelper.inputs:enabled", True),
                ],
                keys.CONNECT: [
                    ("OnPlaybackTick.outputs:tick", "RTSPHelper.inputs:execIn"),
                ],
            },
        )
        init_calls, spy_ctx = self._capture_writer_init()

        with spy_ctx:
            await self._evaluate_graph()

        self.assertEqual(len(init_calls), 0)

    async def test_disabled_node_does_not_create_writer(self):
        keys = og.Controller.Keys
        og.Controller.edit(
            {"graph_path": "/TestGraph", "evaluator_name": "execution"},
            {
                keys.CREATE_NODES: [
                    ("OnPlaybackTick", "omni.graph.action.OnPlaybackTick"),
                    ("RTSPHelper", "isaacsim.streaming.rtsp.RTSPCameraHelper"),
                ],
                keys.SET_VALUES: [
                    ("RTSPHelper.inputs:renderProductPath", "/TestRenderProduct"),
                    ("RTSPHelper.inputs:enabled", False),
                ],
                keys.CONNECT: [
                    ("OnPlaybackTick.outputs:tick", "RTSPHelper.inputs:execIn"),
                ],
            },
        )
        init_calls, spy_ctx = self._capture_writer_init()

        with spy_ctx:
            await self._evaluate_graph()

        self.assertEqual(len(init_calls), 0)
