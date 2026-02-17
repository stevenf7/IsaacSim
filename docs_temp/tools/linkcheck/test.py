"""A simple unittest suite for post_process."""

import unittest
from collections import namedtuple

from post_process import get_assignee


class TestGetAreaRectangle(unittest.TestCase):
    def runTest(self):
        print("Testing get_assignee()")

        TestCase = namedtuple("TestCase", ["url", "expected_assignee"])
        test_cases = [
            TestCase("https://docs.omniverse.nvidia.com/kit/docs/carbonite/latest/index.html", "Carbonite"),
            TestCase(
                "https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/tutorial_ros2_gazebosim.html", "IsaacSim"
            ),
            TestCase(
                "https://docs.omniverse.nvidia.com/kit/docs/kit-sdk/latest/source/extensions/omni.kit.registry.nucleus/docs/index.html",
                "Kit",
            ),
            TestCase(
                "https://docs.omniverse.nvidia.com/prod_materials-and-rendering/prod_materials-and-rendering/rtx_iray.html",
                "OmniDocs",
            ),
            TestCase("https://docs.omniverse.nvidia.com/kit/docs/omni.graph.docs/latest/index.html", "OmniGraph"),
            TestCase("https://docs.omniverse.nvidia.com/kit/docs/omni.kit.usd_docs/latest/Omni.USD.html", "USD"),
        ]

        for case in test_cases:
            assignee = get_assignee(case.url)
            self.assertEqual(assignee, case.expected_assignee)


if __name__ == "__main__":
    unittest.main()
