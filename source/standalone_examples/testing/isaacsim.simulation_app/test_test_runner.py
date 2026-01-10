# SPDX-FileCopyrightText: Copyright (c) 2020-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test to verify that the Test Runner window can load and populate tests without errors."""

import asyncio
import os
import sys

from isaacsim import SimulationApp

# Create simulation app
kit = SimulationApp({"headless": True}, experience=f'{os.environ["EXP_PATH"]}/isaacsim.exp.full.kit')

import omni.kit.app
import omni.ui as ui

# Track any async task exceptions that occur
captured_exceptions = []


def custom_exception_handler(loop, context):
    """Custom exception handler to capture asyncio task exceptions."""
    exception = context.get("exception")
    message = context.get("message", "")
    if exception:
        captured_exceptions.append((message, exception))
        print(f"[ERROR] Asyncio task exception captured: {message}", file=sys.stderr)
        print(f"[ERROR] Exception: {type(exception).__name__}: {exception}", file=sys.stderr)
    else:
        captured_exceptions.append((message, None))
        print(f"[ERROR] Asyncio error captured: {message}", file=sys.stderr)


# Get the asyncio event loop and set our custom exception handler
loop = asyncio.get_event_loop()
original_handler = loop.get_exception_handler()
loop.set_exception_handler(custom_exception_handler)

# Enable the test window extension
manager = omni.kit.app.get_app().get_extension_manager()
manager.set_extension_enabled_immediate("isaacsim.test.utils", True)
manager.set_extension_enabled_immediate("omni.kit.window.tests", True)

# Allow a few frames for the extension to initialize
for _ in range(5):
    kit.update()

# Show the Test Runner window to force it to load and populate the test list
ui.Workspace.show_window("Test Runner", True)

# Keep updating to allow the window to populate
for _ in range(10):
    kit.update()

# Restore the original exception handler
loop.set_exception_handler(original_handler)


# Check if any exceptions were captured and fail the test if so
if captured_exceptions:
    print("\n" + "=" * 80, file=sys.stderr)
    print("TEST FAILED: Asyncio task exceptions occurred during test execution", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    for i, (msg, exc) in enumerate(captured_exceptions, 1):
        print(f"\nException {i}:", file=sys.stderr)
        print(f"  Message: {msg}", file=sys.stderr)
        if exc:
            print(f"  Type: {type(exc).__name__}", file=sys.stderr)
            print(f"  Details: {exc}", file=sys.stderr)
    print("=" * 80 + "\n", file=sys.stderr)
    sys.exit(1)

print("TEST PASSED: No asyncio task exceptions occurred")
kit.close()
