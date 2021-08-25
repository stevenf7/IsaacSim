import omni.kit.test
import omni.kit.pipapi


class TestPipArchive(omni.kit.test.AsyncTestCase):
    async def test_pip_archive(self):
        # Take one of packages from deps/pip.toml, it should be prebundled and available without need for going into online index
        omni.kit.pipapi.install("numpy", version="1.19.0", use_online_index=False)
        import numpy

        self.assertIsNotNone(numpy)
