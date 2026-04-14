# SPDX-FileCopyrightText: Copyright (c) 2022-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Async helpers shared by cumotion examples GUI tests."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable

import numpy as np
import omni.kit.app


async def wait_until(
    predicate: Callable[[], bool],
    *,
    timeout_sec: float = 90.0,
    poll_sec: float = 0.05,
) -> bool:
    """Poll until ``predicate()`` is true or ``timeout_sec`` elapses.

    Args:
        predicate: Callable that returns True when the condition is met.
        timeout_sec: Maximum time to wait in seconds.
        poll_sec: Time between polling attempts in seconds.

    Returns:
        True if predicate returned True before timeout, False otherwise.

    Notes:
        ``next_update_async()`` resolves only when the Kit app completes a
        frame.  If the app's update loop is blocked (e.g. by a hanging GPU /
        physics step), ``next_update_async()`` never returns, the deadline
        check is never reached, and the test hangs forever.

        To keep the timeout enforceable we wrap each ``next_update_async()``
        call with ``asyncio.wait_for``.  If a single frame takes longer than
        the remaining budget, we abort and return False.  This only helps when
        the block is at the asyncio level; a true OS-level block of the Kit
        update thread will still stall everything.
    """
    deadline = time.monotonic() + timeout_sec
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        if predicate():
            return True
        try:
            await asyncio.wait_for(
                omni.kit.app.get_app().next_update_async(),
                timeout=remaining,
            )
        except asyncio.TimeoutError:
            return False
        await asyncio.sleep(poll_sec)


def assert_xyz_and_unit_quaternion_wxyz(position: object, orientation: object) -> None:
    """Assert ``position`` is a 3-vector and ``orientation`` is a unit quaternion in wxyz order.

    Args:
        position: Position as a 3-vector.
        orientation: Orientation as a unit quaternion in wxyz order.
    """
    p = np.asarray(position, dtype=np.float64).reshape(-1)
    if p.shape != (3,):
        raise AssertionError(f"expected position with shape (3,), got {p.shape}")
    q = np.asarray(orientation, dtype=np.float64).reshape(-1)
    if q.shape != (4,):
        raise AssertionError(f"expected quaternion wxyz with shape (4,), got {q.shape}")
    n = float(np.linalg.norm(q))
    np.testing.assert_allclose(n, 1.0, rtol=0.0, atol=1e-3)
