# Copyright (c) 2018-2023, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import json

import carb
import omni.kit.commands
import omni.kit.test
import omni.kit.usd
from omni.isaac.core.utils.nucleus import build_server_list, get_assets_root_path, get_full_asset_path, get_server_path

# import json
# import time
# from omni.client._omniclient import Result, CopyBehavior


# This test is part of internal utils because it needs internal servers
class TestNucleusUtils(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    # async def test_download_isaac_assets(self):
    #     # carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "omniverse://localhost")

    #     def progress_callback(progress, total_steps):
    #         pass

    #     default_server = carb.settings.get_settings().get("/persistent/isaac/nucleus/default")

    #     if default_server:
    #         print('Creating "/Test/new_folder" on {}'.format(default_server))
    #         if check_server(default_server, "/Test/new_folder"):
    #             print('Deleting existing "/Test/new_folder" on {}'.format(default_server))
    #             result = delete_folder(default_server, "/Test/new_folder")
    #             self.assertTrue(result)
    #         result = create_folder(default_server, "/Test/new_folder")
    #         self.assertTrue(result)
    #         result = check_server(default_server, "/Test/new_folder")
    #         self.assertTrue(result)

    #         print('Copying S3 to "/Test/new_folder/Isaac/LICENSES" on {}'.format(default_server))
    #         result = await download_assets_async(
    #             "https://d28dzv1nop4bat.cloudfront.net/LICENSES/",
    #             default_server + "/Test/new_folder/Isaac/LICENSES/",
    #             progress_callback,
    #             concurrency=10,
    #             copy_behaviour=CopyBehavior.OVERWRITE,
    #             copy_after_delete=True,
    #             timeout=600,
    #         )
    #         self.assertTrue(result == Result.OK)

    #         print("Checking Isaac public mount version with existing folder on {}".format(default_server))
    #         result, mount_version = await check_assets_version_async(
    #             "https://d28dzv1nop4bat.cloudfront.net", default_server, "/Test/new_folder"
    #         )
    #         self.assertNotEqual(mount_version, "")
    #         self.assertTrue(result == Result.OK_NOT_YET_FOUND)

    #         print("Checking Isaac public mount version with non-existing folder on {}".format(default_server))
    #         result, mount_version = await check_assets_version_async(
    #             "https://d28dzv1nop4bat.cloudfront.net", default_server, "/Test/new_folder-non-exist"
    #         )
    #         self.assertNotEqual(mount_version, "")
    #         self.assertTrue(result == Result.OK_NOT_YET_FOUND)

    #         print("Checking Isaac staging mount version with existing folder on {}".format(default_server))
    #         result, mount_version = await check_assets_version_async(
    #             "https://dwtwnn5667tll.cloudfront.net", default_server, "/Test/new_folder"
    #         )
    #         self.assertNotEqual(mount_version, "")
    #         self.assertTrue(result == Result.OK_NOT_YET_FOUND)

    #         print("Checking Isaac staging mount version with non-existing folder on {}".format(default_server))
    #         result, mount_version = await check_assets_version_async(
    #             "https://dwtwnn5667tll.cloudfront.net", default_server, "/Test/new_folder-non-exist"
    #         )
    #         self.assertNotEqual(mount_version, "")
    #         self.assertTrue(result == Result.OK_NOT_YET_FOUND)

    #         print("Checking non-existent mount")
    #         self.assertNotEqual(mount_version, "")
    #         result, mount_version = await check_assets_version_async(
    #             "https://ov-isaac-non-exist.s3.us-west-1.amazonaws.com", default_server, "/Test/new_folder-non-exist"
    #         )
    #         self.assertEqual(mount_version, "")
    #         self.assertTrue(result == Result.ERROR_BAD_VERSION)

    #         print('Deleting "/Test/new_folder" on {}'.format(default_server))
    #         result = delete_folder(default_server, "/Test/new_folder")
    #         self.assertTrue(result)
    #         result = check_server(default_server, "/Test/new_folder")
    #         self.assertFalse(result)

    # async def test_find_nucleus_server(self):
    #     result = carb.settings.get_settings().get_settings_dictionary("/persistent/app/omniverse/mountedDrives")
    #     if result is not None:
    #         print(result)
    #         self.assertTrue("localhost" in result.get_dict())
    #         # Test mountedDrives
    #         # specify default saved server does have /Isaac folder, and one that doesn't
    #         carb.settings.get_settings().set(
    #             "/persistent/app/omniverse/mountedDrives",
    #             json.dumps(
    #                 {
    #                     "isaac-dev.ov.nvidia.com": "omniverse://isaac-dev.ov.nvidia.com",
    #                     "ov-content.nvidia.com": "omniverse://ov-content.nvidia.com",
    #                 }
    #             ),
    #         )
    #         carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "")
    #         result, nucleus_server = find_nucleus_server()
    #         self.assertTrue(result)
    #         self.assertEqual(nucleus_server, "omniverse://isaac-dev.ov.nvidia.com")
    #         carb.settings.get_settings().set("/persistent/app/omniverse/mountedDrives", "{}")

    #     # check if the "/persistent/isaac/nucleus/default" setting works, clear saved servers to force isaac-dev.ov.nvidia.com
    #     carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "omniverse://isaac-dev.ov.nvidia.com")
    #     result, nucleus_server = find_nucleus_server()
    #     self.assertTrue(result)
    #     self.assertEqual(nucleus_server, "omniverse://isaac-dev.ov.nvidia.com")
    #     # result should be false because no servers are specified in default or saved
    #     carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "")
    #     result, nucleus_server = find_nucleus_server()
    #     self.assertFalse(result)
    #     self.assertEqual(nucleus_server, "")
    #     # specify default saved server that doesn't have /Isaac folder
    #     carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "ov-content.nvidia.com")
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "")
    #     result, nucleus_server = find_nucleus_server()
    #     self.assertFalse(result)
    #     self.assertEqual(nucleus_server, "")
    #     # specify default saved server does have /Isaac folder, and one that doesn't
    #     carb.settings.get_settings().set(
    #         "/persistent/app/omniverse/savedServers", "ov-content.nvidia.com;isaac-dev.ov.nvidia.com"
    #     )
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "")
    #     result, nucleus_server = find_nucleus_server()
    #     self.assertTrue(result)
    #     self.assertEqual(nucleus_server, "omniverse://isaac-dev.ov.nvidia.com")
    #     # test if adding localhost messes anything up
    #     carb.settings.get_settings().set(
    #         "/persistent/app/omniverse/savedServers", "localhost;ov-content.nvidia.com;isaac-dev.ov.nvidia.com"
    #     )
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "")
    #     result, nucleus_server = find_nucleus_server()
    #     self.assertTrue(result)
    #     self.assertEqual(nucleus_server, "omniverse://isaac-dev.ov.nvidia.com")
    #     # test if default server + saved servers that don't have /Isaac works
    #     carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "localhost;ov-content.nvidia.com")
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "omniverse://isaac-dev.ov.nvidia.com")
    #     result, nucleus_server = find_nucleus_server()
    #     self.assertTrue(result)
    #     self.assertEqual(nucleus_server, "omniverse://isaac-dev.ov.nvidia.com")
    #     # test if default server + saved servers that have /Isaac works
    #     carb.settings.get_settings().set(
    #         "/persistent/app/omniverse/savedServers", "localhost;ov-content.nvidia.com;isaac-dev.ov.nvidia.com"
    #     )
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "omniverse://isaac-dev.ov.nvidia.com")
    #     result, nucleus_server = find_nucleus_server()
    #     self.assertTrue(result)
    #     self.assertEqual(nucleus_server, "omniverse://isaac-dev.ov.nvidia.com")
    #     # result should be false because no servers contain /Isaac
    #     carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "omniverse://ov-content.nvidia.com")
    #     result, nucleus_server = find_nucleus_server()
    #     self.assertFalse(result)
    #     self.assertEqual(nucleus_server, "")
    #     # result should be false because no servers contain /Isaac
    #     carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "omniverse://does_not_exist")
    #     result, nucleus_server = find_nucleus_server()
    #     self.assertFalse(result)
    #     self.assertEqual(nucleus_server, "")
    #     # result should be false because no servers contain /Isaac
    #     carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "does_not_exist")
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "")
    #     result, nucleus_server = find_nucleus_server()
    #     self.assertFalse(result)
    #     self.assertEqual(nucleus_server, "")
    #     carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
    #     carb.settings.get_settings().set(
    #         "/persistent/app/omniverse/mountedDrives", json.dumps({"localhost": "omniverse://localhost"})
    #     )

    # async def test_find_nucleus_server_async(self):
    #     result = carb.settings.get_settings().get_settings_dictionary("/persistent/app/omniverse/mountedDrives")
    #     if result is not None:
    #         print(result)
    #         self.assertTrue("localhost" in result.get_dict())
    #         # Test mountedDrives
    #         # specify default saved server does have /Isaac folder, and one that doesn't
    #         carb.settings.get_settings().set(
    #             "/persistent/app/omniverse/mountedDrives",
    #             json.dumps(
    #                 {
    #                     "isaac-dev.ov.nvidia.com": "omniverse://isaac-dev.ov.nvidia.com",
    #                     "ov-content.nvidia.com": "omniverse://ov-content.nvidia.com",
    #                 }
    #             ),
    #         )
    #         self.assertTrue(len(build_server_list()) > 0)
    #         carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "")
    #         result, nucleus_server = await find_nucleus_server_async()
    #         self.assertTrue(result == Result.OK)
    #         self.assertEqual(nucleus_server, "omniverse://isaac-dev.ov.nvidia.com")
    #         carb.settings.get_settings().set("/persistent/app/omniverse/mountedDrives", "{}")

    #     # check if the "/persistent/isaac/nucleus/default" setting works, clear saved servers to force isaac-dev.ov.nvidia.com
    #     carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "omniverse://isaac-dev.ov.nvidia.com")
    #     result, nucleus_server = await find_nucleus_server_async()
    #     self.assertTrue(result == Result.OK)
    #     self.assertEqual(nucleus_server, "omniverse://isaac-dev.ov.nvidia.com")
    #     # result should be false because no servers are specified in default or saved
    #     carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "")
    #     result, nucleus_server = await find_nucleus_server_async()
    #     self.assertTrue(result == Result.ERROR_NOT_FOUND)
    #     self.assertEqual(nucleus_server, "")
    #     # specify default saved server that doesn't have /Isaac folder
    #     carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "ov-content.nvidia.com")
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "")
    #     result, nucleus_server = await find_nucleus_server_async()
    #     self.assertTrue(result == Result.OK_NOT_YET_FOUND)
    #     self.assertEqual(nucleus_server, "omniverse://ov-content.nvidia.com")
    #     # specify default saved server does have /Isaac folder, and one that doesn't
    #     carb.settings.get_settings().set(
    #         "/persistent/app/omniverse/savedServers", "ov-content.nvidia.com;isaac-dev.ov.nvidia.com"
    #     )
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "")
    #     result, nucleus_server = await find_nucleus_server_async()
    #     self.assertTrue(result == Result.OK)
    #     self.assertEqual(nucleus_server, "omniverse://isaac-dev.ov.nvidia.com")
    #     # test if adding localhost messes anything up
    #     carb.settings.get_settings().set(
    #         "/persistent/app/omniverse/savedServers", "localhost;ov-content.nvidia.com;isaac-dev.ov.nvidia.com"
    #     )
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "")
    #     result, nucleus_server = await find_nucleus_server_async()
    #     print(result)
    #     self.assertTrue(result == Result.OK)
    #     self.assertEqual(nucleus_server, "omniverse://isaac-dev.ov.nvidia.com")
    #     # test if default server + saved servers that don't have /Isaac works
    #     carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "localhost;ov-content.nvidia.com")
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "omniverse://isaac-dev.ov.nvidia.com")
    #     result, nucleus_server = await find_nucleus_server_async()
    #     self.assertTrue(result == Result.OK)
    #     self.assertEqual(nucleus_server, "omniverse://isaac-dev.ov.nvidia.com")
    #     # test if default server + saved servers that have /Isaac works
    #     carb.settings.get_settings().set(
    #         "/persistent/app/omniverse/savedServers", "localhost;ov-content.nvidia.com;isaac-dev.ov.nvidia.com"
    #     )
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "omniverse://isaac-dev.ov.nvidia.com")
    #     result, nucleus_server = await find_nucleus_server_async()
    #     self.assertTrue(result == Result.OK)
    #     self.assertEqual(nucleus_server, "omniverse://isaac-dev.ov.nvidia.com")
    #     # result should be false because no servers contain /Isaac
    #     carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "omniverse://ov-content.nvidia.com")
    #     result, nucleus_server = await find_nucleus_server_async()
    #     self.assertTrue(result == Result.OK_NOT_YET_FOUND)
    #     self.assertEqual(nucleus_server, "omniverse://ov-content.nvidia.com")
    #     # result should be false because no servers contain /Isaac
    #     carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "omniverse://does_not_exist")
    #     result, nucleus_server = await find_nucleus_server_async()
    #     self.assertTrue(result == Result.ERROR_NOT_FOUND)
    #     self.assertEqual(nucleus_server, "")
    #     # result should be false because no servers contain /Isaac
    #     carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "does_not_exist")
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "")
    #     result, nucleus_server = await find_nucleus_server_async()
    #     self.assertTrue(result == Result.ERROR_NOT_FOUND)
    #     self.assertEqual(nucleus_server, "")
    #     carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
    #     # at this point there should be no servers found
    #     self.assertListEqual(build_server_list(), [])
    #     # This server is offline but will resolve, test to make sure timeout works and it doesn't hang
    #     carb.settings.get_settings().set(
    #         "/persistent/isaac/nucleus/default", "omniverse://ov-isaac-test-timeout.nvidia.com"
    #     )
    #     timeout = 30.0
    #     start = time.time()
    #     result, nucleus_server = await find_nucleus_server_async(timeout=timeout)
    #     end = time.time()
    #     # Check that the expected amount of time passed
    #     self.assertAlmostEqual(end - start, timeout, delta=0.2)
    #     self.assertTrue(result == Result.ERROR_CONNECTION)
    #     self.assertEqual(nucleus_server, "")

    #     # cleanup servers after test
    #     carb.settings.get_settings().set("/persistent/isaac/nucleus/default", "")
    #     carb.settings.get_settings().set(
    #         "/persistent/app/omniverse/mountedDrives", json.dumps({"localhost": "omniverse://localhost"})
    #     )

    async def test_get_server_path(self):
        carb.settings.get_settings().set("/persistent/isaac/asset_root/default", "")
        carb.settings.get_settings().set("/persistent/isaac/asset_root/default", "omniverse://isaac-dev.ov.nvidia.com")
        result = get_server_path("/Isaac")
        self.assertEqual(result, "omniverse://isaac-dev.ov.nvidia.com")
        result = get_server_path("/Isaac/Robots")
        self.assertEqual(result, "omniverse://isaac-dev.ov.nvidia.com")
        result = get_server_path("/Does/Not/Exist")
        self.assertIsNone(result)

    async def test_get_assets_root_path(self):
        # 1 - Check /persistent/isaac/asset_root/default setting
        carb.settings.get_settings().set("/persistent/isaac/asset_root/default", "")
        carb.settings.get_settings().set("/persistent/isaac/asset_root/default", "omniverse://isaac-dev.ov.nvidia.com")
        result = get_assets_root_path()
        self.assertEqual(result, "omniverse://isaac-dev.ov.nvidia.com")

        # 2 - Check root on mountedDrives setting
        # specify default saved server does have /Isaac folder, and one that doesn't
        carb.settings.get_settings().set(
            "/persistent/app/omniverse/mountedDrives",
            json.dumps(
                {"localhost": "omniverse://localhost", "isaac-dev.ov.nvidia.com": "omniverse://isaac-dev.ov.nvidia.com"}
            ),
        )
        self.assertTrue(len(build_server_list()) > 0)
        carb.settings.get_settings().set("/persistent/isaac/asset_root/default", "")
        result = get_assets_root_path()
        self.assertEqual(result, "omniverse://isaac-dev.ov.nvidia.com")

        # 3 - Check cloud for /Assets/Isaac/{version_major}.{version_minor} folder
        carb.settings.get_settings().set("/persistent/isaac/asset_root/default", "")
        carb.settings.get_settings().set("/persistent/app/omniverse/mountedDrives", "{}")
        cloud_assets_url = carb.settings.get_settings().get("/persistent/isaac/asset_root/cloud")
        result = get_assets_root_path()
        self.assertEqual(result, cloud_assets_url)

    async def test_get_full_asset_path(self):
        # 1 - Check /persistent/isaac/asset_root/default setting
        carb.settings.get_settings().set("/persistent/isaac/asset_root/default", "")
        carb.settings.get_settings().set("/persistent/isaac/asset_root/default", "omniverse://isaac-dev.ov.nvidia.com")
        result = get_full_asset_path("/Isaac")
        self.assertEqual(result, "omniverse://isaac-dev.ov.nvidia.com/Isaac")
        carb.settings.get_settings().set("/persistent/isaac/asset_root/default", "omniverse://ov-content.nvidia.com")
        result = get_full_asset_path("/Isaac")
        self.assertIsNone(result)

        # 2 - Check mountedDrives setting
        # specify default saved server does have /Isaac folder, and one that doesn't
        carb.settings.get_settings().set(
            "/persistent/app/omniverse/mountedDrives",
            json.dumps(
                {"localhost": "omniverse://localhost", "isaac-dev.ov.nvidia.com": "omniverse://isaac-dev.ov.nvidia.com"}
            ),
        )
        self.assertTrue(len(build_server_list()) > 0)
        carb.settings.get_settings().set("/persistent/isaac/asset_root/default", "")
        result = get_full_asset_path("/Isaac")
        self.assertEqual(result, "omniverse://isaac-dev.ov.nvidia.com/Isaac")
