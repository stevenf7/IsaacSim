# SPDX-FileCopyrightText: Copyright (c) 2022-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import carb
import carb.settings
import omni.ext
import omni.kit.test


class TestIsaacThrottling(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        self._timeline = omni.timeline.get_timeline_interface()
        self._timeline.set_start_time(0)
        self._timeline.set_end_time(1)
        pass

    async def tearDown(self):
        pass

    async def test_on_stop_play_callback(self):
        self._settings = carb.settings.get_settings()
        self._settings.set("/rtx/ecoMode/enabled", True)
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        self.assertEqual(self._settings.get("/rtx/ecoMode/enabled"), False)
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        self.assertEqual(self._settings.get("/rtx/ecoMode/enabled"), True)
        self._timeline.play()
        await omni.kit.app.get_app().next_update_async()
        self.assertEqual(self._settings.get("/rtx/ecoMode/enabled"), False)
        self._timeline.stop()
        await omni.kit.app.get_app().next_update_async()
        self.assertEqual(self._settings.get("/rtx/ecoMode/enabled"), True)
        pass
