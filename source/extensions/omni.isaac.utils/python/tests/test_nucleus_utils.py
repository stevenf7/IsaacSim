import omni.kit.test

import omni.kit.usd
import omni.kit.commands
from omni.isaac.utils.scripts.nucleus_utils import find_nucleus_server
import carb

# Having a test class dervived from omni.kit.test.AsyncTestCase declared on the root of module will make it auto-discoverable by omni.kit.test
class TestNucleusUtils(omni.kit.test.AsyncTestCaseFailOnLogError):
    async def setUp(self):
        pass

    # After running each test
    async def tearDown(self):
        pass

    async def test_find_nucleus_server(self):
        # check if the "/isaac/nucleus/default" setting works, clear saved servers to force ov-isaac-dev
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-isaac-dev")
        result, nucleus_server = find_nucleus_server()
        self.assertTrue(result)
        # result should be false because no servers are specified in default or saved
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = find_nucleus_server()
        self.assertFalse(result)
        # specify default saved server that doesn't have /Isaac folder
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "ov-content")
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = find_nucleus_server()
        self.assertFalse(result)
        # specify default saved server does doesn't have /Isaac folder, and one that doesn't
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "ov-content;ov-isaac-dev")
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = find_nucleus_server()
        self.assertTrue(result)
        # test if adding localhost messes anything up
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "localhost;ov-content;ov-isaac-dev")
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = find_nucleus_server()
        self.assertTrue(result)
        # test if default server + saved servers that don't have /Isaac works
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "localhost;ov-content")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-isaac-dev")
        result, nucleus_server = find_nucleus_server()
        self.assertTrue(result)
        # test if default server + saved servers that have /Isaac works
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "localhost;ov-content;ov-isaac-dev")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-isaac-dev")
        result, nucleus_server = find_nucleus_server()
        self.assertTrue(result)
        # result should be false because no servers contain /Isaac
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://ov-content")
        result, nucleus_server = find_nucleus_server()
        self.assertFalse(result)
        # result should be false because no servers contain /Isaac
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
        carb.settings.get_settings().set("/isaac/nucleus/default", "omniverse://does_not_exit")
        result, nucleus_server = find_nucleus_server()
        self.assertFalse(result)
        # result should be false because no servers contain /Isaac
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "does_not_exit")
        carb.settings.get_settings().set("/isaac/nucleus/default", "")
        result, nucleus_server = find_nucleus_server()
        self.assertFalse(result)
        carb.settings.get_settings().set("/persistent/app/omniverse/savedServers", "")
