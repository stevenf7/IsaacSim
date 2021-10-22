# Copyright (c) 2018-2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.test

import omni.kit.usd
import omni.kit.commands
from omni.isaac.core.utils.nucleus import (
    find_nucleus_server,
    find_nucleus_server_async,
    get_server_path,
    build_server_list,
)
import carb
import json
import time

# This test is part of internal utils because it needs internal servers
class TestNucleusUtils(omni.kit.test.AsyncTestCaseFailOnLogError):
    async def setUp(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    async def test_find_nucleus_server(self):
        result = carb.settings.get_settings().get_settings_dictionary("/persistent/app/omniverse/mountedDrives")
        if result is not None:
            print(result)
            self.assertTrue("localhost" in result.get_dict())
            # Test mountedDrives
            # specify default saved server does have /Isaac folder, and one that doesn't
            carb.settings.get_settings().set(
                "/persistent/app/omniverse/mountedDrives",
                json.dumps(
                    {
                        "ov-isaac-dev.nvidia.com": "omniverse://ov-isaac-dev.nvidia.com",
                        "ov-content.nvidia.com": "omniverse://ov-content.nvidia.com",
                    }
                ),
            )
            carb.settings.get_settings().set("/isaac/nucleus/default", "")
            result, nucleus_server = find_nucleus_server()
            self.assertTrue(result)
            self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
            carb.settings.get_settings().set("/persistent/app/omniverse/mountedDrives", "{}")

        # check if the "/isaac/nucleus/default" setting works, clear saved servers to force ov-isaac-dev.nvidia.com
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-isaac-dev.nvidia.com")
        result, nucleus_server = find_nucleus_server()
        self.assertTrue(result)
        self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
        # result should be false because no servers are specified in default or saved
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = find_nucleus_server()
        self.assertFalse(result)
        self.assertEqual(nucleus_server, "")
        # specify default saved server that doesn't have /Isaac folder
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "ov-content.nvidia.com")
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = find_nucleus_server()
        self.assertFalse(result)
        self.assertEqual(nucleus_server, "")
        # specify default saved server does have /Isaac folder, and one that doesn't
        carb.settings.get_settings().set(
            "/persistent/app/omniverse/savedServers", "ov-content.nvidia.com;ov-isaac-dev.nvidia.com"
        )
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = find_nucleus_server()
        self.assertTrue(result)
        self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
        # test if adding localhost messes anything up
        carb.settings.get_settings().set(
            "/persistent/app/omniverse/savedServers", "localhost;ov-content.nvidia.com;ov-isaac-dev.nvidia.com"
        )
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = find_nucleus_server()
        self.assertTrue(result)
        self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
        # test if default server + saved servers that don't have /Isaac works
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "localhost;ov-content.nvidia.com")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-isaac-dev.nvidia.com")
        result, nucleus_server = find_nucleus_server()
        self.assertTrue(result)
        self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
        # test if default server + saved servers that have /Isaac works
        carb.settings.get_settings().set(
            "/persistent/app/omniverse/savedServers", "localhost;ov-content.nvidia.com;ov-isaac-dev.nvidia.com"
        )
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-isaac-dev.nvidia.com")
        result, nucleus_server = find_nucleus_server()
        self.assertTrue(result)
        self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
        # result should be false because no servers contain /Isaac
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-content.nvidia.com")
        result, nucleus_server = find_nucleus_server()
        self.assertFalse(result)
        self.assertEqual(nucleus_server, "")
        # result should be false because no servers contain /Isaac
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://does_not_exit")
        result, nucleus_server = find_nucleus_server()
        self.assertFalse(result)
        self.assertEqual(nucleus_server, "")
        # result should be false because no servers contain /Isaac
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "does_not_exit")
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = find_nucleus_server()
        self.assertFalse(result)
        self.assertEqual(nucleus_server, "")
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set(
            "/persistent/app/omniverse/mountedDrives", json.dumps({"localhost": "omniverse://localhost"})
        )

    async def test_find_nucleus_server_async(self):
        result = carb.settings.get_settings().get_settings_dictionary("/persistent/app/omniverse/mountedDrives")
        if result is not None:
            print(result)
            self.assertTrue("localhost" in result.get_dict())
            # Test mountedDrives
            # specify default saved server does have /Isaac folder, and one that doesn't
            carb.settings.get_settings().set(
                "/persistent/app/omniverse/mountedDrives",
                json.dumps(
                    {
                        "ov-isaac-dev.nvidia.com": "omniverse://ov-isaac-dev.nvidia.com",
                        "ov-content.nvidia.com": "omniverse://ov-content.nvidia.com",
                    }
                ),
            )
            self.assertTrue(len(build_server_list()) > 0)
            carb.settings.get_settings().set("/isaac/nucleus/default", "")
            result, nucleus_server = await find_nucleus_server_async()
            self.assertTrue(result)
            self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
            carb.settings.get_settings().set("/persistent/app/omniverse/mountedDrives", "{}")

        # check if the "/isaac/nucleus/default" setting works, clear saved servers to force ov-isaac-dev.nvidia.com
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-isaac-dev.nvidia.com")
        result, nucleus_server = await find_nucleus_server_async()
        self.assertTrue(result)
        self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
        # result should be false because no servers are specified in default or saved
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = await find_nucleus_server_async()
        self.assertFalse(result)
        self.assertEqual(nucleus_server, "")
        # specify default saved server that doesn't have /Isaac folder
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "ov-content.nvidia.com")
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = await find_nucleus_server_async()
        self.assertFalse(result)
        self.assertEqual(nucleus_server, "")
        # specify default saved server does have /Isaac folder, and one that doesn't
        carb.settings.get_settings().set(
            "/persistent/app/omniverse/savedServers", "ov-content.nvidia.com;ov-isaac-dev.nvidia.com"
        )
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = await find_nucleus_server_async()
        self.assertTrue(result)
        self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
        # test if adding localhost messes anything up
        carb.settings.get_settings().set(
            "/persistent/app/omniverse/savedServers", "localhost;ov-content.nvidia.com;ov-isaac-dev.nvidia.com"
        )
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = await find_nucleus_server_async()
        self.assertTrue(result)
        self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
        # test if default server + saved servers that don't have /Isaac works
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "localhost;ov-content.nvidia.com")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-isaac-dev.nvidia.com")
        result, nucleus_server = await find_nucleus_server_async()
        self.assertTrue(result)
        self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
        # test if default server + saved servers that have /Isaac works
        carb.settings.get_settings().set(
            "/persistent/app/omniverse/savedServers", "localhost;ov-content.nvidia.com;ov-isaac-dev.nvidia.com"
        )
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-isaac-dev.nvidia.com")
        result, nucleus_server = await find_nucleus_server_async()
        self.assertTrue(result)
        self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
        # result should be false because no servers contain /Isaac
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-content.nvidia.com")
        result, nucleus_server = await find_nucleus_server_async()
        self.assertFalse(result)
        self.assertEqual(nucleus_server, "")
        # result should be false because no servers contain /Isaac
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://does_not_exit")
        result, nucleus_server = await find_nucleus_server_async()
        self.assertFalse(result)
        self.assertEqual(nucleus_server, "")
        # result should be false because no servers contain /Isaac
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "does_not_exit")
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = await find_nucleus_server_async()
        self.assertFalse(result)
        self.assertEqual(nucleus_server, "")
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        # at this point there should be no servers found
        self.assertListEqual(build_server_list(), [])
        # This server is offline but will resolve, test to make sure timeout works and it doesn't hang
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-isaac-test-timeout.nvidia.com")
        timeout = 4.0
        start = time.time()
        result, nucleus_server = await find_nucleus_server_async(timeout=timeout)
        end = time.time()
        # Check that the expected amount of time passed
        self.assertAlmostEqual(end - start, timeout, delta=0.1)
        self.assertFalse(result)
        self.assertEqual(nucleus_server, "")

        # cleanup servers after test
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        carb.settings.get_settings().set(
            "/persistent/app/omniverse/mountedDrives", json.dumps({"localhost": "omniverse://localhost"})
        )

    async def test_get_server_path(self):
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-isaac-dev.nvidia.com")
        result = get_server_path("/Isaac")
        self.assertEqual(result, "omniverse://ov-isaac-dev.nvidia.com/Isaac")
        result = get_server_path("/Isaac/Robots")
        self.assertEqual(result, "omniverse://ov-isaac-dev.nvidia.com/Isaac/Robots")
        result = get_server_path("/Does/Not/Exist")
        self.assertIsNone(result)
