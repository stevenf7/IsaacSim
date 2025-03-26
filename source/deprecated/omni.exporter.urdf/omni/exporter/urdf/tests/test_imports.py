# Import test file for omni.exporter.urdf
# This file was automatically generated to test imports from deprecated extensions
# Compiled from tests found in omni/exporter/urdf/tests

import omni.kit.test


class TestImports(omni.kit.test.AsyncTestCase):
    async def setUp(self):
        pass

    async def tearDown(self):
        pass

    async def test_imports_for_omni_exporter_urdf_extension(self):
        # Testing all imports from original extension tests
        import nvidia.srl.tools.logger as logger
        from nvidia.srl.from_usd.to_urdf import UsdToUrdf

        print("All imports successful for extension: omni.exporter.urdf")
