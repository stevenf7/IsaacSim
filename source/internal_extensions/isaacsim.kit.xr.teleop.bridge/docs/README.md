# Isaac Kit XR Teleop Bridge

This extension provides OpenXR handle functions that may be missing from older versions of `omni.kit.xr.system.openxr`. It polyfills missing functions into that module so that `OpenXRSessionHandles` can be fully constructed for use with IsaacTeleop's DeviceIO.

## Overview

Different Kit SDK versions provide different handle functions:
- **Older versions**: No handle getter functions ❌
- **Current versions**: `get_instance_handle()`, `get_session_handle()`, `get_stage_space_handle()` ✓
- **All versions**: Missing `get_instance_proc_addr()` ❌

This bridge extension provides all 4 functions and only patches the ones that don't already exist:
- `get_instance_handle()` - XrInstance (forwards to Kit if available)
- `get_session_handle()` - XrSession (forwards to Kit if available)
- `get_stage_space_handle()` - XrSpace (forwards to Kit if available)
- `get_instance_proc_addr()` - xrGetInstanceProcAddr function pointer (from OpenXR loader)

## Usage

```python
import omni.kit.xr.system.openxr as openxr
import isaacsim.kit.xr.teleop.bridge  # Adds get_instance_proc_addr to openxr

from teleopcore.oxr import OpenXRSessionHandles
from teleopcore.deviceio import DeviceIOSession, HandTracker

# Construct OpenXRSessionHandles from Kit's handles
handles = OpenXRSessionHandles(
    openxr.get_instance_handle(),
    openxr.get_session_handle(),
    openxr.get_stage_space_handle(),
    openxr.get_instance_proc_addr()  # <-- Added by this extension
)

# Create DeviceIO session with trackers
trackers = [HandTracker()]
with DeviceIOSession.run(trackers, handles) as session:
    while running:
        session.update()
```

## How It Works

1. The C++ plugin exposes `xrGetInstanceProcAddr` from the OpenXR loader
2. When the extension loads, it checks if `omni.kit.xr.system.openxr.get_instance_proc_addr` exists
3. If it doesn't exist, it adds the function as a polyfill
4. If it already exists (future Kit versions), nothing is patched

## Direct Usage

You can also use `get_instance_proc_addr` directly from this module:

```python
import isaacsim.kit.xr.teleop.bridge as bridge

proc_addr = bridge.get_instance_proc_addr()
```

## Future

Once `omni.kit.xr.system.openxr` natively supports `get_instance_proc_addr()`, this extension will detect it and skip the patch, becoming a no-op.
