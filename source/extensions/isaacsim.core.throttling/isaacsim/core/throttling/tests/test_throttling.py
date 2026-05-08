# SPDX-FileCopyrightText: Copyright (c) 2022-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Test for throttling."""

import contextlib
import sys
import types

import carb
import carb.settings
import omni.ext
import omni.kit.test


@contextlib.contextmanager
def _fake_replicator_capture(status: str = "STARTED", has_attached_annotators: bool = True):
    module_names = [
        "omni.replicator",
        "omni.replicator.core",
        "omni.replicator.core.scripts",
        "omni.replicator.core.scripts.annotators",
    ]
    missing = object()
    previous_modules = {name: sys.modules.get(name, missing) for name in module_names}
    previous_replicator_attr = getattr(omni, "replicator", missing)

    class FakeStatus:
        STOPPED = "STOPPED"
        STOPPING = "STOPPING"
        STARTED = "STARTED"

    class FakeOrchestrator:
        Status = FakeStatus

        @staticmethod
        def get_status():
            return status

    class FakeAnnotatorRegistry:
        @staticmethod
        def has_attached_annotators():
            return has_attached_annotators

    replicator_module = types.ModuleType("omni.replicator")
    core_module = types.ModuleType("omni.replicator.core")
    scripts_module = types.ModuleType("omni.replicator.core.scripts")
    annotators_module = types.ModuleType("omni.replicator.core.scripts.annotators")

    core_module.orchestrator = FakeOrchestrator()
    core_module.AnnotatorRegistry = FakeAnnotatorRegistry
    annotators_module.AnnotatorRegistry = FakeAnnotatorRegistry
    replicator_module.core = core_module
    core_module.scripts = scripts_module
    scripts_module.annotators = annotators_module

    sys.modules["omni.replicator"] = replicator_module
    sys.modules["omni.replicator.core"] = core_module
    sys.modules["omni.replicator.core.scripts"] = scripts_module
    sys.modules["omni.replicator.core.scripts.annotators"] = annotators_module
    setattr(omni, "replicator", replicator_module)

    try:
        yield
    finally:
        for name, module in previous_modules.items():
            if module is missing:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
        if previous_replicator_attr is missing:
            if hasattr(omni, "replicator"):
                delattr(omni, "replicator")
        else:
            setattr(omni, "replicator", previous_replicator_attr)


class TestIsaacThrottling(omni.kit.test.AsyncTestCase):
    """Test isaac throttling."""

    async def setUp(self) -> None:
        """Set up test environment."""
        self._timeline = omni.timeline.get_timeline_interface()
        self._timeline.set_start_time(0)
        self._timeline.set_end_time(1)
        self._settings = carb.settings.get_settings()

        # Reset async rendering state to clean test environment
        self._settings.set("/app/asyncRendering", False)
        self._settings.set("/app/asyncRenderingLowLatency", False)

    async def tearDown(self) -> None:
        """Tear down test environment."""
        # Reset state after each test
        self._settings.set("/app/asyncRendering", False)
        self._settings.set("/app/asyncRenderingLowLatency", False)

    # async rendering always off
    async def test_on_stop_play_toggles_off(self) -> None:
        """Test on stop play toggles off."""
        self._settings.set("/rtx/ecoMode/enabled", True)
        self._settings.set("/app/asyncRendering", False)
        self._settings.set("/app/asyncRenderingLowLatency", False)

        self._settings.set("/exts/isaacsim.core.throttling/enable_async", False)
        self._settings.set("/exts/isaacsim.core.throttling/enable_manualmode", False)

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        self.assertEqual(self._settings.get("/rtx/ecoMode/enabled"), False)
        self.assertEqual(self._settings.get("/exts/omni.kit.hydra_texture/gizmos/enabled"), False)
        self.assertFalse(self._settings.get("/app/asyncRendering"))
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        self.assertEqual(self._settings.get("/rtx/ecoMode/enabled"), True)
        self.assertEqual(self._settings.get("/exts/omni.kit.hydra_texture/gizmos/enabled"), True)
        self.assertFalse(self._settings.get("/app/asyncRendering"))
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        self.assertEqual(self._settings.get("/rtx/ecoMode/enabled"), False)
        self.assertEqual(self._settings.get("/exts/omni.kit.hydra_texture/gizmos/enabled"), False)
        self.assertFalse(self._settings.get("/app/asyncRendering"))
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        self.assertEqual(self._settings.get("/rtx/ecoMode/enabled"), True)
        self.assertEqual(self._settings.get("/exts/omni.kit.hydra_texture/gizmos/enabled"), True)
        self.assertFalse(self._settings.get("/app/asyncRendering"))

    async def test_on_stop_play_callback(self) -> None:
        """Test on stop play callback."""
        self._settings.set("/rtx/ecoMode/enabled", True)
        self._settings.set("/app/asyncRendering", False)
        self._settings.set("/app/asyncRenderingLowLatency", False)

        self._settings.set("/exts/isaacsim.core.throttling/enable_async", True)
        self._settings.set("/exts/isaacsim.core.throttling/enable_manualmode", True)

        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        self.assertEqual(self._settings.get("/rtx/ecoMode/enabled"), False)
        self.assertEqual(self._settings.get("/exts/omni.kit.hydra_texture/gizmos/enabled"), False)
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        self.assertEqual(self._settings.get("/rtx/ecoMode/enabled"), True)
        self.assertEqual(self._settings.get("/exts/omni.kit.hydra_texture/gizmos/enabled"), True)
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        self.assertEqual(self._settings.get("/rtx/ecoMode/enabled"), False)
        self.assertEqual(self._settings.get("/exts/omni.kit.hydra_texture/gizmos/enabled"), False)
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        self.assertEqual(self._settings.get("/rtx/ecoMode/enabled"), True)
        self.assertEqual(self._settings.get("/exts/omni.kit.hydra_texture/gizmos/enabled"), True)

    async def test_async_rendering_10_frame_delay(self) -> None:
        """Test that async rendering is re-enabled after 10 frames when timeline stops."""
        # Enable async toggle
        self._settings.set("/exts/isaacsim.core.throttling/enable_async", True)

        # Start with timeline playing (async should be disabled)
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        self.assertFalse(self._settings.get("/app/asyncRendering"))

        # Stop timeline - start the 10-frame delay
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()

        # For frames 1-9, async rendering should be disabled
        for frame in range(1, 10):
            await omni.kit.app.get_app().next_update_async()
            self.assertFalse(
                self._settings.get("/app/asyncRendering"), f"Async rendering should be False at frame {frame}"
            )

        # On frame 10, async rendering should be enabled
        await omni.kit.app.get_app().next_update_async()
        self.assertTrue(self._settings.get("/app/asyncRendering"), "Async rendering should be True after 10 frames")

        await omni.kit.app.get_app().next_update_async()
        self.assertTrue(self._settings.get("/app/asyncRendering"))

    async def test_async_rendering_stays_disabled_while_replicator_is_capturing(self) -> None:
        """Test that timeline pause/stop does not re-enable async rendering during Replicator captures."""
        for action_name in ("pause", "stop"):
            with self.subTest(timeline_action=action_name):
                self._settings.set("/exts/isaacsim.core.throttling/enable_async", True)
                self._settings.set("/app/asyncRendering", False)
                self._settings.set("/app/asyncRenderingLowLatency", False)

                with _fake_replicator_capture(status="STARTED", has_attached_annotators=True):
                    self._timeline.play()
                    await omni.kit.app.get_app().next_update_async()
                    self.assertFalse(self._settings.get("/app/asyncRendering"))

                    getattr(self._timeline, action_name)()
                    await omni.kit.app.get_app().next_update_async()

                    for _ in range(12):
                        await omni.kit.app.get_app().next_update_async()

                self.assertFalse(self._settings.get("/app/asyncRendering"))
                self.assertFalse(self._settings.get("/app/asyncRenderingLowLatency"))
