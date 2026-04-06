# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

"""Isaac Kit XR Teleop Bridge.

This module provides OpenXR handle functions that may be missing from older versions
of omni.kit.xr.system.openxr. It polyfills missing functions into that module
so that OpenXRSessionHandles can be fully constructed for use with IsaacTeleop's DeviceIO.

Functions provided:
- get_instance_handle() - XrInstance handle (from Kit C++ interface).
- get_session_handle() - XrSession handle (from Kit C++ interface).
- get_stage_space_handle() - XrSpace handle (from Kit C++ interface).
- get_instance_proc_addr() - xrGetInstanceProcAddr function pointer (from Kit C++ interface).

Only functions that don't already exist in omni.kit.xr.system.openxr will be patched.

Example:
    >>> import omni.kit.xr.system.openxr as openxr
    >>> import isaacsim.kit.xr.teleop.bridge  # Patches missing functions into openxr
    >>> from teleopcore.oxr import OpenXRSessionHandles
    >>> from teleopcore.deviceio import DeviceIOSession, HandTracker
    >>>
    >>> # Now all 4 functions are available from openxr module
    >>> handles = OpenXRSessionHandles(
    ...     openxr.get_instance_handle(),
    ...     openxr.get_session_handle(),
    ...     openxr.get_stage_space_handle(),
    ...     openxr.get_instance_proc_addr()
    ... )
    >>> session = DeviceIOSession.run([HandTracker()], handles)
"""

from .bindings import _bridge  # noqa: F401
from .impl.teleop_bridge import *  # noqa: F401,F403
from .impl.teleop_bridge import __all__
