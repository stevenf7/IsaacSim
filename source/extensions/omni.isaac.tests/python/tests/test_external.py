import omni.kit.test
import gc
import omni

################################################################################
### !!!IMPORTANT!!!
### All of the tests below are for utility snippets from the isaac sim docs.
### If you fix an issue here make sure to update the code in the docs as well
### The idea is that we can catch any api changes and update the docs appropriately
################################################################################


class TestExternalDependencies(omni.kit.test.AsyncTestCaseFailOnLogError):
    async def setUp(self):
        await omni.usd.get_context().new_stage_async()
        await omni.kit.app.get_app().next_update_async()

    async def tearDown(self):
        await omni.kit.app.get_app().next_update_async()
        gc.collect()
        pass

    async def test_semantic_schema_editor(self):
        ext_manager = omni.kit.app.get_app().get_extension_manager()
        self.assertTrue(ext_manager.set_extension_enabled_immediate("semantics.schema.editor", True))
        await omni.kit.app.get_app().next_update_async()
        self.assertTrue(ext_manager.set_extension_enabled_immediate("semantics.schema.editor", False))
