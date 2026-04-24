# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""Small helpers shared by built-in recordables."""

from __future__ import annotations

from typing import Any

import numpy as np


def to_numpy(value: Any) -> np.ndarray:
    """Convert warp / torch arrays (returned by experimental prim APIs) to a NumPy array."""
    if isinstance(value, np.ndarray):
        return value
    if hasattr(value, "numpy"):
        return value.numpy()
    if hasattr(value, "cpu"):
        return value.cpu().numpy()
    return np.asarray(value)


def to_numpy_f32(value: Any) -> np.ndarray:
    """Convert warp / torch / numpy arrays to a contiguous ``float32`` NumPy array.

    Combines :func:`to_numpy` with a single dtype cast. For arrays that are already
    ``float32``, the cast is a no-op and no copy is made.
    """
    arr = to_numpy(value)
    return arr.astype(np.float32, copy=False)


def get_stage() -> Any:
    """Return the current USD stage. Raises if no stage is loaded."""
    import omni.usd

    stage = omni.usd.get_context().get_stage()
    if stage is None:
        raise RuntimeError("No USD stage is currently loaded.")
    return stage
