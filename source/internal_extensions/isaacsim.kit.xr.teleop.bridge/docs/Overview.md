# Overview

This extension provides OpenXR handle access for teleoperation integrations and fills API gaps across Kit versions.

It exposes a C++/Python bridge that:
- gives access to OpenXR handles needed by external libraries (for example IsaacTeleop DeviceIO),
- polyfills missing handle helpers into `omni.kit.xr.system.openxr`,
- and lets you configure or extend required OpenXR extension names.

## What It Provides

The bridge exposes these functions from `isaacsim.kit.xr.teleop.bridge`:
- `get_instance_handle()` -> `XrInstance` as `int` (`0` when unavailable)
- `get_session_handle()` -> `XrSession` as `int` (`0` when unavailable)
- `get_stage_space_handle()` -> `XrSpace` as `int` (`0` when unavailable)
- `get_instance_proc_addr()` -> `xrGetInstanceProcAddr` as `int` (`0` when unavailable)
- `subscribe_required_extensions(callback)` -> RAII subscription handle

On import, the extension also patches missing functions into `omni.kit.xr.system.openxr`
(only the missing ones, never overriding existing functions).

## Quick Start

```python
import isaacsim.kit.xr.teleop.bridge  # Triggers polyfill for missing openxr helpers
import omni.kit.xr.system.openxr as openxr

from teleopcore.oxr import OpenXRSessionHandles
from teleopcore.deviceio import DeviceIOSession, HandTracker

handles = OpenXRSessionHandles(
    openxr.get_instance_handle(),
    openxr.get_session_handle(),
    openxr.get_stage_space_handle(),
    openxr.get_instance_proc_addr(),
)

with DeviceIOSession.run([HandTracker()], handles) as session:
    while running:
        session.update()
```

## Required OpenXR Extensions

The bridge component resolves its required OpenXR extension names using settings and optional runtime callbacks.

### Settings keys

- `exts."isaacsim.kit.xr.teleop.bridge".openxr.requiredExtensions.set`
- `exts."isaacsim.kit.xr.teleop.bridge".openxr.requiredExtensions.add`
- `exts."isaacsim.kit.xr.teleop.bridge".openxr.requiredExtensions.remove`

### Resolution order

1. Start from `set`
2. Apply `add` (deduplicated)
3. Apply `remove`
4. Append all callback-provided extensions (deduplicated)

If settings are unavailable, the bridge falls back to:
- `XR_KHR_convert_timespec_time`
- `XR_NVX1_tensor_data`

### Example: replace/add/remove via settings

```toml
[settings]
exts."isaacsim.kit.xr.teleop.bridge".openxr.requiredExtensions.set = [
    "XR_KHR_convert_timespec_time",
]
exts."isaacsim.kit.xr.teleop.bridge".openxr.requiredExtensions.add = [
    "XR_FB_passthrough",
]
exts."isaacsim.kit.xr.teleop.bridge".openxr.requiredExtensions.remove = [
    "XR_KHR_convert_timespec_time",
]
```

### Example: explicitly clear the settings list

```toml
[settings]
exts."isaacsim.kit.xr.teleop.bridge".openxr.requiredExtensions.set = []
exts."isaacsim.kit.xr.teleop.bridge".openxr.requiredExtensions.add = []
exts."isaacsim.kit.xr.teleop.bridge".openxr.requiredExtensions.remove = []
```

## Runtime Callback Subscription (RAII)

You can append required extensions at runtime by subscribing a callback.

```python
import isaacsim.kit.xr.teleop.bridge as bridge

required_ext_subscription = bridge.subscribe_required_extensions(
    lambda: ["XR_FB_passthrough", "XR_EXT_hand_tracking"]
)

# Keep `required_ext_subscription` alive while you want callback active.
# Unsubscribe explicitly:
required_ext_subscription.reset()

# Or drop all references (for example: required_ext_subscription = None).
```

Behavior notes:
- Callback signature is `() -> list[str]` (or any iterable of strings).
- Callback results are deduplicated against the final extension list.
- Exceptions thrown by callbacks are caught and logged; resolution continues.
- Subscription lifetime is tied to the returned subscription handle object.

## Direct Function Usage

You can call bridge helpers directly without going through `openxr` polyfills:

```python
import isaacsim.kit.xr.teleop.bridge as bridge

proc_addr = bridge.get_instance_proc_addr()
```

## Compatibility Notes

- On newer Kit versions where some helpers already exist in `omni.kit.xr.system.openxr`,
  this extension only adds missing helpers.
- If/when `get_instance_proc_addr()` is provided natively, the bridge will not override it.
