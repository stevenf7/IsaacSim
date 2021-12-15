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
    create_folder,
    delete_folder,
    check_server,
    download_assets_async,
    check_assets_version_async,
)
import carb
import json
import time
from omni.client._omniclient import Result, CopyBehavior


# This test is part of internal utils because it needs internal servers
class TestNucleusUtils(omni.kit.test.AsyncTestCaseFailOnLogError):
    async def setUp(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    async def test_download_isaac_assets(self):
        # carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://localhost")

        def progress_callback(progress, total_steps):
            pass

        default_server = carb.settings.get_settings().get("/isaac/nucleus/default")

        if default_server:
            print('Creating "/Test" on {}'.format(default_server))
            if check_server(default_server, "/Test"):
                print('Deleting existing "/Test" on {}'.format(default_server))
                result = delete_folder(default_server, "/Test")
                self.assertTrue(result)
            result = create_folder(default_server, "/Test")
            self.assertTrue(result)
            result = check_server(default_server, "/Test")
            self.assertTrue(result)

            print("Checking Isaac public mount version with existing folder on {}".format(default_server))
            result, mount_version = await check_assets_version_async(
                "https://ov-isaac.s3.us-west-1.amazonaws.com", default_server, "/Test"
            )
            self.assertNotEqual(mount_version, "")
            self.assertTrue(result == Result.OK_NOT_YET_FOUND)

            print("Checking Isaac public mount version with non-existing folder on {}".format(default_server))
            result, mount_version = await check_assets_version_async(
                "https://ov-isaac.s3.us-west-1.amazonaws.com", default_server, "/Test-non-exist"
            )
            self.assertNotEqual(mount_version, "")
            self.assertTrue(result == Result.OK_NOT_YET_FOUND)

            print("Checking Isaac staging mount version with existing folder on {}".format(default_server))
            result, mount_version = await check_assets_version_async(
                "https://ov-isaac-dev.s3.us-west-1.amazonaws.com", default_server, "/Test"
            )
            self.assertNotEqual(mount_version, "")
            self.assertTrue(result == Result.OK_NOT_YET_FOUND)

            print("Checking Isaac staging mount version with non-existing folder on {}".format(default_server))
            result, mount_version = await check_assets_version_async(
                "https://ov-isaac-dev.s3.us-west-1.amazonaws.com", default_server, "/Test-non-exist"
            )
            self.assertNotEqual(mount_version, "")
            self.assertTrue(result == Result.OK_NOT_YET_FOUND)

            print("Checking non-existent mount")
            self.assertNotEqual(mount_version, "")
            result, mount_version = await check_assets_version_async(
                "https://ov-isaac-non-exist.s3.us-west-1.amazonaws.com", default_server, "/Test-non-exist"
            )
            self.assertEqual(mount_version, "")
            self.assertTrue(result == Result.ERROR_BAD_VERSION)

            print('Copying S3 to "/Test/Isaac/Materials" on {}'.format(default_server))
            result = await download_assets_async(
                "https://ov-isaac.s3.us-west-1.amazonaws.com/Materials/Isaac/",
                default_server + "/Test/Isaac/Materials/Isaac",
                progress_callback,
                concurrency=3,
                copy_behaviour=CopyBehavior.OVERWRITE,
                copy_after_delete=True,
                timeout=600,
            )
            self.assertTrue(result == Result.OK)

            print('Deleting "/Test" on {}'.format(default_server))
            result = delete_folder(default_server, "/Test")
            self.assertTrue(result)
            result = check_server(default_server, "/Test")
            self.assertFalse(result)

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
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://does_not_exist")
        result, nucleus_server = find_nucleus_server()
        self.assertFalse(result)
        self.assertEqual(nucleus_server, "")
        # result should be false because no servers contain /Isaac
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "does_not_exist")
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
            self.assertTrue(result == Result.OK)
            self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
            carb.settings.get_settings().set("/persistent/app/omniverse/mountedDrives", "{}")

        # check if the "/isaac/nucleus/default" setting works, clear saved servers to force ov-isaac-dev.nvidia.com
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-isaac-dev.nvidia.com")
        result, nucleus_server = await find_nucleus_server_async()
        self.assertTrue(result == Result.OK)
        self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
        # result should be false because no servers are specified in default or saved
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = await find_nucleus_server_async()
        self.assertTrue(result == Result.ERROR_NOT_FOUND)
        self.assertEqual(nucleus_server, "")
        # specify default saved server that doesn't have /Isaac folder
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "ov-content.nvidia.com")
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = await find_nucleus_server_async()
        print(result)
        self.assertTrue(result == Result.ERROR_NOT_FOUND)
        # TOFIX self.assertTrue(result == Result.OK_NOT_YET_FOUND)
        self.assertEqual(nucleus_server, "")
        # specify default saved server does have /Isaac folder, and one that doesn't
        carb.settings.get_settings().set(
            "/persistent/app/omniverse/savedServers", "ov-content.nvidia.com;ov-isaac-dev.nvidia.com"
        )
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = await find_nucleus_server_async()
        self.assertTrue(result == Result.OK)
        self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
        # test if adding localhost messes anything up
        carb.settings.get_settings().set(
            "/persistent/app/omniverse/savedServers", "localhost;ov-content.nvidia.com;ov-isaac-dev.nvidia.com"
        )
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = await find_nucleus_server_async()
        print(result)
        self.assertTrue(result == Result.OK)
        self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
        # test if default server + saved servers that don't have /Isaac works
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "localhost;ov-content.nvidia.com")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-isaac-dev.nvidia.com")
        result, nucleus_server = await find_nucleus_server_async()
        self.assertTrue(result == Result.OK)
        self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
        # test if default server + saved servers that have /Isaac works
        carb.settings.get_settings().set(
            "/persistent/app/omniverse/savedServers", "localhost;ov-content.nvidia.com;ov-isaac-dev.nvidia.com"
        )
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-isaac-dev.nvidia.com")
        result, nucleus_server = await find_nucleus_server_async()
        self.assertTrue(result == Result.OK)
        self.assertEqual(nucleus_server, "omniverse://ov-isaac-dev.nvidia.com")
        # result should be false because no servers contain /Isaac
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-content.nvidia.com")
        result, nucleus_server = await find_nucleus_server_async()
        print(result)
        self.assertTrue(result == Result.ERROR_NOT_FOUND)
        # TOFIX self.assertTrue(result == Result.OK_NOT_YET_FOUND)
        self.assertEqual(nucleus_server, "")
        # result should be false because no servers contain /Isaac
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://does_not_exist")
        result, nucleus_server = await find_nucleus_server_async()
        self.assertTrue(result == Result.ERROR_NOT_FOUND)
        self.assertEqual(nucleus_server, "")
        # result should be false because no servers contain /Isaac
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "does_not_exist")
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = await find_nucleus_server_async()
        self.assertTrue(result == Result.ERROR_NOT_FOUND)
        self.assertEqual(nucleus_server, "")
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        # at this point there should be no servers found
        self.assertListEqual(build_server_list(), [])
        # This server is offline but will resolve, test to make sure timeout works and it doesn't hang
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-isaac-test-timeout.nvidia.com")
        timeout = 30.0
        start = time.time()
        result, nucleus_server = await find_nucleus_server_async(timeout=timeout)
        end = time.time()
        # Check that the expected amount of time passed
        self.assertAlmostEqual(end - start, timeout, delta=0.1)
        self.assertTrue(result == Result.ERROR_CONNECTION)
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
