# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

"""Teleop bridge implementation providing OpenXR handle access functions.

This module acquires the ITeleopBridge Carbonite interface and exposes its
methods as module-level Python functions. It also polyfills any missing
functions into ``omni.kit.xr.system.openxr`` so that OpenXRSessionHandles
can be fully constructed for use with IsaacTeleop's DeviceIO.
"""

from collections.abc import Callable

from ..bindings._bridge import acquire_teleop_bridge_interface

# Acquire the interface on import
_interface = acquire_teleop_bridge_interface()


def get_instance_handle() -> int:
    """Get the current OpenXR instance handle (XrInstance).

    Returns:
        The XrInstance handle, or 0 if no active OpenXR session.

    Example:

        .. code-block:: python

            import isaacsim.kit.xr.teleop.bridge as bridge

            instance = bridge.get_instance_handle()
    """
    return _interface.get_instance_handle()


def get_session_handle() -> int:
    """Get the current OpenXR session handle (XrSession).

    Returns:
        The XrSession handle, or 0 if no active OpenXR session.

    Example:

        .. code-block:: python

            import isaacsim.kit.xr.teleop.bridge as bridge

            session = bridge.get_session_handle()
    """
    return _interface.get_session_handle()


def get_stage_space_handle() -> int:
    """Get the OpenXR stage reference space handle (XrSpace).

    Returns:
        The XrSpace handle for the stage space, or 0 if no active session.

    Example:

        .. code-block:: python

            import isaacsim.kit.xr.teleop.bridge as bridge

            stage_space = bridge.get_stage_space_handle()
    """
    return _interface.get_stage_space_handle()


def get_instance_proc_addr() -> int:
    """Get the xrGetInstanceProcAddr function pointer from the OpenXR loader.

    Returns:
        The xrGetInstanceProcAddr function pointer as uint64, or 0 if not available.

    Example:

        .. code-block:: python

            import isaacsim.kit.xr.teleop.bridge as bridge

            proc_addr = bridge.get_instance_proc_addr()
    """
    return _interface.get_instance_proc_addr()


def subscribe_required_extensions(callback: Callable[[], list[str]]) -> object:
    """Subscribe a callback that can contribute OpenXR required extensions.

    The callback should return an iterable of extension strings. The C++ layer
    deduplicates values before appending them to the resolved extension list.
    Keep the returned subscription handle alive; releasing it unsubscribes.

    Args:
        callback: Callable with signature ``() -> list[str]``.

    Returns:
        RequiredExtensionsSubscription handle. Call ``reset()`` to unsubscribe.
    """
    return _interface.subscribe_required_extensions(callback)


# Polyfill missing functions into omni.kit.xr.system.openxr
try:
    import carb
    import omni.kit.xr.system.openxr as openxr

    # Only patch functions that don't already exist
    _functions_to_patch = [
        ("get_instance_handle", get_instance_handle),
        ("get_session_handle", get_session_handle),
        ("get_stage_space_handle", get_stage_space_handle),
        ("get_instance_proc_addr", get_instance_proc_addr),
    ]

    for func_name, func in _functions_to_patch:
        if not hasattr(openxr, func_name):
            carb.log_info(f"[isaacsim.kit.xr.teleop.bridge] Polyfilling omni.kit.xr.system.openxr.{func_name}()")
            setattr(openxr, func_name, func)
            # Also add to __all__ if it exists
            if hasattr(openxr, "__all__") and func_name not in openxr.__all__:
                openxr.__all__.append(func_name)

except ImportError:
    # omni.kit.xr.system.openxr not available - that's fine, user can still use
    # functions directly from this module
    pass

__all__ = [
    "get_instance_handle",
    "get_session_handle",
    "get_stage_space_handle",
    "get_instance_proc_addr",
    "subscribe_required_extensions",
]
