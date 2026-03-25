---
name: python-server-client
description: Connect to a running Isaac Sim instance via the python_server TCP socket to execute Python code remotely. Use when you need to launch Isaac Sim headless, send code for execution, create/modify USD stages, run simulations, or interact with the Kit runtime from an external process or LLM agent.
---

# Python Server Client — Remote Code Execution in Isaac Sim

Execute Python code inside a running Isaac Sim instance via the `isaacsim.code_editor.python_server` TCP socket. This is the foundational skill for any LLM agent workflow that needs to interact with a live sim.

## Launching Isaac Sim

Start Isaac Sim headless with the python server extension enabled:

```bash
cd _build/linux-x86_64/release

bash isaac-sim.sh --no-window --no-ros-env \
    --enable isaacsim.code_editor.python_server
```

Wait for `app ready` in the output before sending any commands. The TCP server listens on `127.0.0.1:8226` by default.

### Enabling additional extensions

Pass extra `--enable` flags for any extensions your workflow needs:

```bash
bash isaac-sim.sh --no-window --no-ros-env \
    --enable isaacsim.code_editor.python_server \
    --enable isaacsim.test.utils \
    --enable isaacsim.sensors.camera
```

## Sending Code

Use the helper script at `scripts/isaacsim_send.py` (relative to this skill directory):

```bash
# Inline code
python scripts/isaacsim_send.py 'print("hello")'

# Multi-line via heredoc
python scripts/isaacsim_send.py << 'PYEOF'
import isaacsim.core.experimental.utils.stage as stage_utils
stage = stage_utils.get_current_stage()
print(stage)
PYEOF

# Custom host/port
python scripts/isaacsim_send.py --host 127.0.0.1 --port 8226 'print("hello")'

# Longer timeout for heavy operations
python scripts/isaacsim_send.py --timeout 120 'app_utils.update_app(steps=500)'
```

### Response format

Success:
```json
{
  "status": "ok",
  "output": "hello",
  "result": null
}
```

Error:
```json
{
  "status": "error",
  "output": "",
  "ename": "NameError",
  "evalue": "name 'x' is not defined",
  "traceback": ["Traceback (most recent call last):\n  ..."]
}
```

### Exit codes

- `0` — execution succeeded (`status: "ok"`)
- `1` — execution failed (`status: "error"`) or connection error

## Async Code

The server supports top-level `await`. This is required for many Isaac Sim APIs:

```bash
python scripts/isaacsim_send.py '
import isaacsim.core.experimental.utils.stage as stage_utils
await stage_utils.create_new_stage_async(template="empty")
print("Stage created")
'
```

`print()` output from async code is captured in the `output` field of the JSON response.

## State Persistence

The server maintains a shared Python globals dictionary across all TCP connections within a session. Variables, imports, and functions defined in one request are available in subsequent requests:

```bash
# Request 1: import and define
python scripts/isaacsim_send.py '
import isaacsim.core.experimental.utils.stage as stage_utils
MY_PATHS = ["/World/A", "/World/B", "/World/C"]
'

# Request 2: use variables from request 1
python scripts/isaacsim_send.py '
for path in MY_PATHS:
    stage_utils.define_prim(path, "Xform")
print("Created", len(MY_PATHS), "prims")
'
```

This enables incremental scene construction across multiple agent turns.

## Common Patterns

### Create a new stage

```python
import isaacsim.core.experimental.utils.stage as stage_utils
await stage_utils.create_new_stage_async(template="empty")
stage_utils.define_prim("/World", "Xform")
```

### Add objects to the scene

```python
from isaacsim.core.experimental.objects import Cube, Sphere, DomeLight
from pxr import UsdLux

# Light (required for rendering — see lighting note below)
dome = DomeLight("/World/DomeLight")
stage = stage_utils.get_current_stage()
UsdLux.DomeLight(stage.GetPrimAtPath("/World/DomeLight")).GetIntensityAttr().Set(3000.0)

# Objects
Cube("/World/RedCube", sizes=1.0, colors="red", positions=(0, 0, 0.5))
Sphere("/World/GreenSphere", radii=0.5, colors="green", positions=(2, 0, 0.5))
```

### Step the renderer / simulation

```python
import isaacsim.core.experimental.utils.app as app_utils

# Render frames (required before capturing images)
app_utils.update_app(steps=120)

# Play/stop simulation
app_utils.play()
app_utils.update_app(steps=100)
app_utils.stop()
```

### Query the stage

```python
stage = stage_utils.get_current_stage()
prim = stage.GetPrimAtPath("/World/RedCube")
print(f"Valid: {prim.IsValid()}, Type: {prim.GetTypeName()}")
```

### Check expression results

For expressions (single-line evaluations), the result is returned in the `result` field:

```bash
python scripts/isaacsim_send.py 'len(stage_utils.get_current_stage().GetPrimAtPath("/World").GetChildren())'
# {"status": "ok", "output": "", "result": 3}
```

## Important Notes

### Lighting in headless mode

Headless rendering with no lights produces a black image. Always add a `DomeLight` with intensity 1000–5000 when you need to render or capture images.

### Renderer warm-up

The RTX path tracer needs frames to converge. After creating or loading a new stage, call `app_utils.update_app(steps=120)` before doing any rendering-dependent work. After minor scene changes, `steps=30` is usually sufficient.

### Connection errors

If the script reports `Cannot connect to Isaac Sim`, verify:
1. Isaac Sim is running and shows `app ready`
2. The python_server extension is enabled (check for `isaacsim.code_editor.python_server` in the startup log)
3. Host and port match (default: `127.0.0.1:8226`)

## Shutdown

```bash
python scripts/isaacsim_send.py '
import isaacsim.core.experimental.utils.app as app_utils
app_utils.stop()
'
# Then kill the Isaac Sim process
```

Or simply kill the process directly.
