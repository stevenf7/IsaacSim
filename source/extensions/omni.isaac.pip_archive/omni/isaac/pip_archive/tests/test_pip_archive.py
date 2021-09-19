import omni.kit.test
import omni.kit.pipapi


class TestPipArchive(omni.kit.test.AsyncTestCase):
    async def test_pip_archive(self):
        # Take one of packages from deps/pip.toml, it should be prebundled and available without need for going into online index
        omni.kit.pipapi.install("scipy", version="1.5.4", use_online_index=False)
        import scipy

        self.assertIsNotNone(scipy)

    # import all packages to make sure dependencies were not missed
    async def test_import_all(self):
        import scipy
        import quaternion
        import numba
        import webbot
        import selenium
        import urllib3
        import requests
        import certifi
        import charset_normalizer
        import construct
        import llvmlite
        import nest_asyncio
        import jinja2
        import markupsafe
        import matplotlib
        import pyparsing
        import cycler
        import kiwisolver
        import torch
        import torchvision
        import packaging
        import pint
        import requests_oauthlib
        import oauthlib

        self.assertIsNotNone(scipy)
        self.assertIsNotNone(quaternion)
        self.assertIsNotNone(numba)
        self.assertIsNotNone(webbot)
        self.assertIsNotNone(selenium)
        self.assertIsNotNone(urllib3)
        self.assertIsNotNone(requests)
        self.assertIsNotNone(certifi)
        self.assertIsNotNone(charset_normalizer)
        self.assertIsNotNone(construct)
        self.assertIsNotNone(llvmlite)
        self.assertIsNotNone(nest_asyncio)
        self.assertIsNotNone(jinja2)
        self.assertIsNotNone(markupsafe)
        self.assertIsNotNone(matplotlib)
        self.assertIsNotNone(pyparsing)
        self.assertIsNotNone(cycler)
        self.assertIsNotNone(kiwisolver)
        self.assertIsNotNone(torch)
        self.assertIsNotNone(torchvision)
        self.assertIsNotNone(packaging)
        self.assertIsNotNone(pint)
        self.assertIsNotNone(requests_oauthlib)
        self.assertIsNotNone(oauthlib)
