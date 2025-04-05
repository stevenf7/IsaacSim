# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import carb
import omni.kit.test
import omni.usd
from omni.kit.ui_test.menu import *
from omni.kit.ui_test.query import *
from omni.ui.tests.test_base import OmniUiTest


class TestMenuUI(OmniUiTest):
    async def setUp(self):
        self._timeline = omni.timeline.get_timeline_interface()
        omni.usd.get_context().new_stage()
        # Make sure the stage loaded
        await omni.kit.app.get_app().next_update_async()

    # After running each test

    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        # In some cases the test will end before the asset is loaded, in this case wait for assets to load
        while omni.usd.get_context().get_stage_loading_status()[2] > 0:
            await omni.kit.app.get_app().next_update_async()
        await super().tearDown()

    async def test_physics_reference_link(self):
        # Allow the UI to update so that the main menu is populated
        from urllib.error import URLError
        from urllib.request import urlopen

        from isaacsim.gui.menu.help_menu import resolve_physics_ref_url

        await omni.kit.app.get_app().next_update_async()

        physics_ref_url = resolve_physics_ref_url()

        def is_website_online(url):
            try:
                res = urlopen(url, timeout=1.0)
                print(f"testing link url", url)
                return res.status == 200
            except URLError:
                print("URL failed", url)
                return False

        self.assertTrue(is_website_online(physics_ref_url))
