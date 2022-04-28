# Copyright (c) 2021, NVIDIA  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from __future__ import print_function

import argparse
from collections import OrderedDict

"""
Convenient tools for creating command line programs that switch between multiple modes to run.

Example usage:

script.py:

    def opt1(args):
        print("option 1")

    def opt2(args):
        print("option 2")

    options = CliOptions()
    options["opt1"] = opt1
    options["opt2"] = opt2

    parser = argparse.ArgumentParser(node_name)
    options.setup_flags(parser)
    args = parser.parse_args()

    options.run_choice(args) 

Command line usage can be found:
    python script.py --help  # Show the command line flags.
    python script.py --list  # Lists available mode .
    python script.py --mode=<mode>  # Run the chosen mode.

Alternatively, to create a version with tests that can be run, use

    options = CliTests()

This creates a --test=<test> flag rather than a --mode flag.
"""


class CliOptions(OrderedDict):
    def __init__(self, tag="mode", tag_plaural="modes"):
        super(CliOptions, self).__init__()
        self.tags = [tag, tag_plaural]

    def setup_flags(self, parser):
        parser.add_argument("--list", action="store_true", help=("List all %s." % self.tags[1]))
        parser.add_argument("--%s" % self.tags[0], type=str, default=None, help=("Run a specific %s." % self.tags[0]))
        return parser

    def print_options(self):
        print("\nAvailable %s:" % self.tags[1])
        for i, name in enumerate(self.keys()):
            print("%d) %s" % (i, name))
        print()

    def run_choice(self, args):
        if args.list:
            self.print_options()
            return
        choice = getattr(args, self.tags[0])
        if choice is not None:
            run_cli_option(choice, self[choice])
        else:
            print(
                "ERROR ~ %s not secified. Use --%s=<mode> flag. To see available %s, use --list."
                % (self.tags[0], self.tags[0], self.tags[1])
            )


class CliTests(CliOptions):
    def __init__(self):
        super().__init__(tag="test", tag_plaural="tests")


def run_cli_option(name, func):
    print()
    print("=" * 80)
    print("= %s" % name)
    print("=" * 80)
    print()

    try:
        func()
    except Exception as e:
        print("~~")
        print("Problem detected %s" % name)
        print(e)
        import traceback

        traceback.print_exc()
        print("~~")
