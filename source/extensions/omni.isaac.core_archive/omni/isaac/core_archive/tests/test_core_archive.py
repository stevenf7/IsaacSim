# Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import omni.kit.pipapi
import omni.kit.test


class TestPipArchive(omni.kit.test.AsyncTestCase):
    # import all packages to make sure dependencies were not missed
    async def test_import_all(self):
        import bezier
        import boto3
        import charset_normalizer
        import construct
        import cycler
        import jinja2
        import kiwisolver
        import llvmlite
        import markupsafe
        import matplotlib
        import nest_asyncio
        import numba
        import nvsmi
        import oauthlib
        import osqp
        import packaging
        import pint
        import pyparsing
        import qdldl
        import quaternion
        import requests
        import requests_oauthlib
        import s3transfer
        import scipy
        import selenium
        import urllib3
        import webbot
        import yaml

        self.assertIsNotNone(scipy)
        self.assertIsNotNone(quaternion)
        self.assertIsNotNone(numba)
        self.assertIsNotNone(webbot)
        self.assertIsNotNone(selenium)
        self.assertIsNotNone(urllib3)
        self.assertIsNotNone(requests)
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
        self.assertIsNotNone(packaging)
        self.assertIsNotNone(pint)
        self.assertIsNotNone(requests_oauthlib)
        self.assertIsNotNone(oauthlib)
        self.assertIsNotNone(yaml)
        self.assertIsNotNone(osqp)
        self.assertIsNotNone(qdldl)
        self.assertIsNotNone(nvsmi)
        self.assertIsNotNone(bezier)
        self.assertIsNotNone(boto3)
        self.assertIsNotNone(s3transfer)
