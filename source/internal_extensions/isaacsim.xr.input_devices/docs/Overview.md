# Overview

This extension provides XR input device support for a vendor hand-tracking library via a pluggable C API and for Vive trackers via `pysurvive` (libsurvive), with a unified Python integration API.

## Features

- **Hand tracking (C API)**: Real-time wrist and finger joint poses via a C shared library, accessed through a C++ plugin and Python bindings
- **Vive trackers**: 6DOF poses via `pysurvive`
- **Unified API**: Simple integration object exposes a consistent schema and device status

## Prerequisites

### Hardware
- **Manus Gloves**: Manus Prime/MetaGloves with license dongle
- **Vive Trackers**: Lighthouse tracking (SteamVR base stations + trackers)

### Software
- **Hand tracking library**: Shared library implementing the C API in `include/isaacsim/xr/input_devices/IsaacSimHandTrackerCAPI.h`
- **libsurvive / pysurvive**: Required for Vive tracking

## Setup

```bash
git clone https://github.com/cntools/libsurvive.git
cd libsurvive
sudo cp ./useful_files/81-vive.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger

# Replug Vive trackers (and dongles) after applying udev rules
```

## Building

```bash
# Build Isaac Sim (includes this extension)
./build.sh
```

## Usage

### Quickstart (interactive)
Launch Isaac Sim Python and poll once:

```bash
cd /path/to/IsaacSim
./_build/linux-x86_64/release/python.sh - <<'PY'
from isaacsim.xr.input_devices.impl.manus_vive_integration import get_manus_vive_integration
integration = get_manus_vive_integration()
integration.manus_tracker.update()
integration.vive_tracker.update()
print("status:", integration.device_status)
print("manus sample:", {k: integration.manus_tracker.get_data()[k] for k in list(integration.manus_tracker.get_data())[:2]})
print("vive sample:", {k: integration.vive_tracker.get_data()[k] for k in list(integration.vive_tracker.get_data())[:2]})
PY
```

### Python API

```python
from isaacsim.xr.input_devices.impl.manus_vive_integration import get_manus_vive_integration

# Obtain the shared integration instance from the extension
integration = get_manus_vive_integration()

# Update devices once (call periodically for real time)
integration.manus_tracker.update()
integration.vive_tracker.update()

manus_data = integration.manus_tracker.get_data()
vive_data = integration.vive_tracker.get_data()
status = integration.device_status

print(f"Manus connected: {status.get('manus_gloves', {}).get('connected', False)}")
print(f"Vive connected: {status.get('vive_trackers', {}).get('connected', False)}")
print(f"Left hand connected: {status.get('left_hand_connected', False)}")
print(f"Right hand connected: {status.get('right_hand_connected', False)}")
```

### Data Format

From `integration.manus_tracker.get_data()`:

```python
{
  'left_0': {
    'position': [x, y, z],
    'orientation': [w, x, y, z]
  },
  'left_1': { ... },
  ...
  'left_24': { ... },
  'right_0': { ... },
  ...
  'right_24': { ... }
}
```

From `integration.vive_tracker.get_data()`:

```python
{
  '<device_id>': {
    'position': [x, y, z],
    # orientation is [w, x, y, z]
    'orientation': [w, x, y, z]
  },
  # e.g., 'WM0', 'WM1', or device names from libsurvive
}
```

From `integration.device_status`:

```python
{
  'manus_gloves': {'connected': bool, 'last_data_time': float},
  'vive_trackers': {'connected': bool, 'last_data_time': float},
  'left_hand_connected': bool,
  'right_hand_connected': bool
}
```

## Troubleshooting

- Data not flowing in: replug the Manus license dongle, glove dongle, and Vive tracker dongles. Restart the gloves and Vive tracker devices.
- After adding udev rules: run `sudo udevadm control --reload-rules && sudo udevadm trigger`, then unplug/replug Vive trackers.
- Vive tracking unstable or no pose: check base stations are powered and visible; charge devices.
- pysurvive not available: check that `pysurvive` is installed successfully during build; verify `python -c "import pysurvive"` succeeds.
- Hand tracking library not found: set `ISAACSIM_HANDTRACKER_LIB` or `ISAACSIM_HANDTRACKER_NAME` (see below), or install your vendor library.

## Environment & configuration

- Override library path: `ISAACSIM_HANDTRACKER_LIB=/abs/path/to/libYourHandTracker.so`
- Override by name: `ISAACSIM_HANDTRACKER_NAME=YourHandTracker` (tries `libYourHandTracker.so` on Linux, `YourHandTracker.dll` on Windows)
- Programmatic override: `get_manus_vive_integration(handtracker_lib_override="/abs/path/to/lib.so")`

Positions are in meters. Orientation quaternions are normalized; quaternions are `[w, x, y, z]` right handed.

## Extension layout

```text
isaacsim.xr.input_devices/
├── bindings/                    # Pybind11 bindings
├── include/                     # C++ headers
├── plugins/                     # C++ implementations
├── python/
│   └── impl/
│       ├── extension.py                 # Extension lifecycle (register/cleanup)
│       └── manus_vive_integration.py    # Orchestrates hand-tracker plugin + Vive
│       └── vive_tracker.py              # Vive wrapper
└── docs/
    ├── README.md
    └── CHANGELOG.md
```

## License

Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES.

SPDX-License-Identifier: Apache-2.0
