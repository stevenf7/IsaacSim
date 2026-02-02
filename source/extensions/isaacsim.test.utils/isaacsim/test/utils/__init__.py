# SPDX-FileCopyrightText: Copyright (c) 2018-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
import carb.settings

_COVERAGE_PATCH_APPLIED = False


def _is_pycoverage_enabled() -> bool:
    settings = carb.settings.get_settings()
    if settings is None:
        return False
    try:
        return bool(settings.get_as_bool("/exts/omni.kit.test/pyCoverageEnabled"))
    except Exception:
        return False


def _apply_numpy_coverage_patch() -> None:
    global _COVERAGE_PATCH_APPLIED
    if _COVERAGE_PATCH_APPLIED:
        return

    import numpy as np
    import numpy._core._methods as npm

    if getattr(npm, "_isaacsim_cov_patch_applied", False):
        _COVERAGE_PATCH_APPLIED = True
        return

    original_amax = npm._amax
    original_amin = npm._amin

    def _coverage_amax(a, axis=None, out=None, keepdims=False, initial=None, where=True):
        """Handle coverage.py _NoValueType sentinels in max operations."""
        try:
            result = original_amax(a, axis, out, keepdims, initial, where)
            if hasattr(result, "__class__") and result.__class__.__name__ == "_NoValueType":
                if axis is None:
                    return max(a.flat) if a.size > 0 else 0
                return np.array([max(row) for row in np.atleast_2d(a)])
            return result
        except TypeError as exc:
            if "_NoValueType" in str(exc):
                if axis is None:
                    return max(a.flat) if a.size > 0 else 0
                return np.array([max(row) for row in np.atleast_2d(a)])
            raise

    def _coverage_amin(a, axis=None, out=None, keepdims=False, initial=None, where=True):
        """Handle coverage.py _NoValueType sentinels in min operations."""
        try:
            result = original_amin(a, axis, out, keepdims, initial, where)
            if hasattr(result, "__class__") and result.__class__.__name__ == "_NoValueType":
                if axis is None:
                    return min(a.flat) if a.size > 0 else 0
                return np.array([min(row) for row in np.atleast_2d(a)])
            return result
        except TypeError as exc:
            if "_NoValueType" in str(exc):
                if axis is None:
                    return min(a.flat) if a.size > 0 else 0
                return np.array([min(row) for row in np.atleast_2d(a)])
            raise

    npm._amax = _coverage_amax
    npm._amin = _coverage_amin
    setattr(npm, "_isaacsim_cov_patch_applied", True)
    _COVERAGE_PATCH_APPLIED = True


if _is_pycoverage_enabled():
    _apply_numpy_coverage_patch()

from .file_validation import *
from .image_capture import *
from .image_comparison import *
from .image_io import *
from .menu_ui_test import *
from .menu_utils import *
from .timed_async_test import *
