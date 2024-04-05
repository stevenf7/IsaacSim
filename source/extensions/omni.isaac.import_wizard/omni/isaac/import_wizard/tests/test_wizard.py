# Copyright (c) 2018-2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import json

# NOTE:
#   omni.kit.test - std python's unittest module with additional wrapping to add suport for async/await tests
#   For most things refer to unittest docs: https://docs.python.org/3/library/unittest.html
import omni.kit.test


# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestImportWizard(omni.kit.test.AsyncTestCase):
    # Before running each test
    async def setUp(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    # After running each test
    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        pass

    # Run for 60 frames and make sure there were no errors loading
    async def test_wizard_wrapper(self):
        for frame in range(60):
            await omni.kit.app.get_app().next_update_async()
        pass

    # test links in the wizard to make sure they all still exist
    async def test_docs_links(self):
        from urllib.error import URLError
        from urllib.request import urlopen

        def is_website_online(url):
            try:
                res = urlopen(url, timeout=5)
                print(f"testing link url")
                return res.status == 200
            except URLError:
                return False

        def extract_key(data_dict, key, value_array=[]):
            if isinstance(data_dict, dict):
                for k, v in data_dict.items():
                    if k == key:
                        value_array.append(v)
                    extract_key(v, key)
            return value_array

        EXTENSION_FOLDER_PATH = omni.kit.app.get_app().get_extension_manager().get_extension_path_by_module(__name__)
        with open(EXTENSION_FOLDER_PATH + "/data/pipeline.json", "r") as file:
            data = json.load(file)

        links_all = []
        links_all = extract_key(data, "Documentation Link", links_all)
        links_all = extract_key(data, "API Link", links_all)
        links_all = extract_key(data, "Examples Link", links_all)

        print("links all", links_all)
        for url in links_all:
            print(f"testing link {url}")
            self.assertTrue(is_website_online(url))
