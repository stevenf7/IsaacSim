---
name: python-server-client
description: >
  Connect to a running Isaac Sim instance via the python_server TCP socket to execute Python code remotely.
  Use when you need to launch Isaac Sim, send code for execution, create/modify USD stages, run simulations,
  take viewport or full-app screenshots, click menu items, interact with UI widgets, inspect/modify prim
  properties and transforms, control the camera, step physics, read console logs, or execute Kit commands.
  All features work in --no-window headless mode. Requires Isaac Sim running with the python_server extension
  enabled on port 8226.
---

# Python Server Client — Remote Code Execution & UI Automation in Isaac Sim

Execute Python code inside a running Isaac Sim instance via the `isaacsim.code_editor.python_server` TCP socket. This skill covers both headless code execution and full UI automation (screenshots, menu clicks, widget interaction).

## Launching Isaac Sim

```bash
cd _build/linux-x86_64/release

# Headless — supports all features: code execution, viewport screenshots,
# full-app screenshots, menu clicks, and widget interaction
bash isaac-sim.sh --no-window --no-ros-env \
    --enable isaacsim.code_editor.python_server

# With display (optional — only needed if you want to visually observe the UI)
DISPLAY=:99 bash isaac-sim.sh --no-ros-env \
    --enable isaacsim.code_editor.python_server
```

Wait for `app ready` in the output before sending commands. The TCP server listens on `127.0.0.1:8226`.

**Note:** The extension requires `--enable`, not `--/exts/.../enabled=true`.

### Enabling additional extensions

```bash
bash isaac-sim.sh --no-window --no-ros-env \
    --enable isaacsim.code_editor.python_server \
    --enable isaacsim.test.utils \
    --enable isaacsim.sensors.camera
```

## Sending Code

Use `scripts/isaacsim_send.py` (relative to this skill directory):

```bash
# Inline code
python scripts/isaacsim_send.py 'print("hello")'

# From stdin
echo 'print("hello")' | python scripts/isaacsim_send.py

# Send a .py file
python scripts/isaacsim_send.py --file scripts/app_screenshot.py

# File with injected variables
python scripts/isaacsim_send.py --file scripts/app_screenshot.py \
    --arg output_path=/tmp/shot.png

# Custom host/port/timeout
python scripts/isaacsim_send.py --host 127.0.0.1 --port 8226 --timeout 120 'print("hello")'

# Raw JSON output
python scripts/isaacsim_send.py --raw 'print("hello")'
```

### Response format

```json
{"status": "ok", "output": "hello", "result": null}
```

```json
{"status": "error", "output": "", "ename": "NameError", "evalue": "name 'x' is not defined", "traceback": ["..."]}
```

### Exit codes

- `0` — execution succeeded (`status: "ok"`)
- `1` — execution failed (`status: "error"`) or connection error

## Async Code

The server supports top-level `await`:

```bash
python scripts/isaacsim_send.py '
import isaacsim.core.experimental.utils.stage as stage_utils
await stage_utils.create_new_stage_async(template="empty")
print("Stage created")
'
```

## State Persistence

The server maintains shared globals across TCP connections within a session:

```bash
# Request 1
python scripts/isaacsim_send.py 'MY_PATHS = ["/World/A", "/World/B"]'

# Request 2 — MY_PATHS still available
python scripts/isaacsim_send.py 'print(MY_PATHS)'
```

## Screenshots

### Viewport Screenshot (works headless)

Captures the 3D viewport render via replicator annotators. Does NOT include UI chrome.

```bash
python scripts/isaacsim_send.py --file scripts/viewport_screenshot.py \
    --arg output_path=/tmp/viewport.png
```

### Full-App Screenshot (works headless)

Captures the entire application window including menus, panels, and viewport — exactly what a user sees. Uses `omni.kit.renderer.capture` swapchain capture. Works in both `--no-window` and windowed modes.

```bash
python scripts/isaacsim_send.py --file scripts/app_screenshot.py \
    --arg output_path=/tmp/fullapp.png
```

### Annotator Data Capture

Capture depth, normals, segmentation, or any replicator annotator:

```bash
python scripts/isaacsim_send.py --file scripts/capture_annotator.py \
    --arg annotator=distance_to_camera --arg output_path=/tmp/depth.npy
```

## Menu Navigation and Clicking

Click any menu item by slash-separated path. Uses `omni.kit.ui_test.menu_click` (programmatic, works headless) with fallback to mouse-emulation navigation for slow submenus.

```bash
# Create a new stage
python scripts/isaacsim_send.py --file scripts/menu_click.py \
    --arg menu_path="File/New"

# Add a cube
python scripts/isaacsim_send.py --file scripts/menu_click.py \
    --arg menu_path="Create/Mesh/Cube"

# Open an Isaac example
python scripts/isaacsim_send.py --file scripts/menu_click.py \
    --arg menu_path="Isaac Examples/Robots/Franka"
```

Optional: `--arg window_name="Some Window"` to wait for a specific window after clicking.

### Discover available menus

```bash
python scripts/isaacsim_send.py --file scripts/list_menus.py
```

## Widget Interaction

Find and interact with UI widgets by name:

```bash
# Click a widget
python scripts/isaacsim_send.py --file scripts/widget_action.py \
    --arg action=click --arg query="Load"

# Read widget state
python scripts/isaacsim_send.py --file scripts/widget_action.py \
    --arg action=read --arg query="Play"

# List all visible windows
python scripts/isaacsim_send.py --file scripts/list_windows.py
```

Supported actions: `click`, `double_click`, `right_click`, `type` (with `--arg text=...`), `read`.

## Scene Inspection

### Stage Hierarchy

View the current stage as a tree or flat list, with optional type filtering and attribute display:

```bash
# Stage tree (default, excludes /Render subtree)
python scripts/isaacsim_send.py --file scripts/stage_info.py

# Flat list mode
python scripts/isaacsim_send.py --file scripts/stage_info.py --arg mode=list

# Detailed view of a specific prim (all attributes)
python scripts/isaacsim_send.py --file scripts/stage_info.py \
    --arg prim_path=/World/Cube

# Filter by prim type
python scripts/isaacsim_send.py --file scripts/stage_info.py \
    --arg filter_type=Camera

# Show all attributes for filtered prims
python scripts/isaacsim_send.py --file scripts/stage_info.py \
    --arg filter_type=Mesh --arg show_attrs=True
```

### Prim Properties

Read or write arbitrary USD attributes on any prim:

```bash
# List all attributes on a prim
python scripts/isaacsim_send.py --file scripts/prim_properties.py \
    --arg prim_path=/World/Cube --arg action=list

# Read a specific attribute
python scripts/isaacsim_send.py --file scripts/prim_properties.py \
    --arg prim_path=/World/Cube --arg attr_name=doubleSided

# Set an attribute
python scripts/isaacsim_send.py --file scripts/prim_properties.py \
    --arg prim_path=/World/Cube --arg action=set \
    --arg attr_name=visibility --arg 'attr_value="invisible"'
```

### Selection

Select prims in the stage (affects Property panel and context menus):

```bash
# Get current selection
python scripts/isaacsim_send.py --file scripts/select_prim.py

# Select a prim
python scripts/isaacsim_send.py --file scripts/select_prim.py \
    --arg action=set --arg prim_path=/World/Cube

# Select multiple
python scripts/isaacsim_send.py --file scripts/select_prim.py \
    --arg action=set --arg "prim_path=/World/Cube,/World/Sphere"

# Clear selection
python scripts/isaacsim_send.py --file scripts/select_prim.py --arg action=clear
```

## Transform Control

Get or set world-space position, orientation, and scale of any prim:

```bash
# Get current transform
python scripts/isaacsim_send.py --file scripts/prim_transform.py \
    --arg prim_path=/World/Cube

# Set position
python scripts/isaacsim_send.py --file scripts/prim_transform.py \
    --arg prim_path=/World/Cube --arg action=set --arg "position=3,0,1"

# Set orientation (quaternion w,x,y,z)
python scripts/isaacsim_send.py --file scripts/prim_transform.py \
    --arg prim_path=/World/Cube --arg action=set --arg "orientation=0.707,0,0.707,0"

# Set scale
python scripts/isaacsim_send.py --file scripts/prim_transform.py \
    --arg prim_path=/World/Cube --arg action=set --arg "scale=2,2,2"
```

## Camera Control

Control the viewport camera position, orientation, and look-at target:

```bash
# Get current camera pose
python scripts/isaacsim_send.py --file scripts/camera_control.py

# Move camera to a position
python scripts/isaacsim_send.py --file scripts/camera_control.py \
    --arg action=set --arg "position=10,10,10"

# Point camera at a target from a position
python scripts/isaacsim_send.py --file scripts/camera_control.py \
    --arg action=look_at --arg "target=0,0,0" --arg "position=5,5,5"

# List all cameras on stage
python scripts/isaacsim_send.py --file scripts/camera_control.py \
    --arg action=list_cameras

# Set focal length
python scripts/isaacsim_send.py --file scripts/camera_control.py \
    --arg action=set --arg focal_length=35
```

## Simulation Control

Play, pause, stop, step, or query the simulation:

```bash
# Check simulation status
python scripts/isaacsim_send.py --file scripts/simulation_control.py

# Start simulation
python scripts/isaacsim_send.py --file scripts/simulation_control.py --arg action=play

# Step N physics frames
python scripts/isaacsim_send.py --file scripts/simulation_control.py \
    --arg action=step --arg num_steps=100

# Stop simulation
python scripts/isaacsim_send.py --file scripts/simulation_control.py --arg action=stop

# Start with custom physics timestep
python scripts/isaacsim_send.py --file scripts/simulation_control.py \
    --arg action=play --arg dt=0.001
```

## Command Execution

Execute any of Isaac Sim's 370+ registered `omni.kit.commands`:

```bash
# List all commands (with optional filter)
python scripts/isaacsim_send.py --file scripts/execute_command.py \
    --arg action=list --arg filter=Physics

# Execute a command with arguments
python scripts/isaacsim_send.py --file scripts/execute_command.py \
    --arg command_name=CreateMeshPrimWithDefaultXform \
    --arg 'kwargs={"prim_type":"Cone"}'

# Add a ground plane
python scripts/isaacsim_send.py --file scripts/execute_command.py \
    --arg command_name=AddGroundPlane
```

## Console Log

Read the Kit session log for debugging:

```bash
# Show log file path and size
python scripts/isaacsim_send.py --file scripts/console_log.py --arg action=path

# Tail last 50 lines (default)
python scripts/isaacsim_send.py --file scripts/console_log.py

# Show only errors
python scripts/isaacsim_send.py --file scripts/console_log.py --arg action=errors

# Show warnings and errors
python scripts/isaacsim_send.py --file scripts/console_log.py \
    --arg action=errors --arg level=warn

# Search log for a keyword
python scripts/isaacsim_send.py --file scripts/console_log.py \
    --arg action=search --arg query=PhysX
```

## State Isolation

When using `--file`, scripts run in isolated function scope by default. This prevents variable leakage between calls. Use `--no-isolate` if you need state to persist:

```bash
# Isolated (default) — variables don't leak between calls
python scripts/isaacsim_send.py --file scripts/stage_info.py --arg prim_path=/World/Cube
python scripts/isaacsim_send.py --file scripts/stage_info.py  # prim_path is NOT set here

# Persistent state — use --no-isolate
python scripts/isaacsim_send.py --no-isolate --file setup_scene.py
python scripts/isaacsim_send.py 'print(my_setup_variable)'  # still available
```

## Common Patterns

### Create a new stage

```python
import isaacsim.core.experimental.utils.stage as stage_utils
await stage_utils.create_new_stage_async(template="empty")
stage_utils.define_prim("/World", "Xform")
```

### Add objects to the scene

```python
import numpy as np
from isaacsim.core.experimental.objects import Cube, Sphere, DomeLight

dl = DomeLight("/World/DomeLight")
dl.set_intensities(np.array([3000.0]))
Cube("/World/RedCube", sizes=1.0, colors="red", positions=(0, 0, 0.5))
Sphere("/World/GreenSphere", radii=0.5, colors="green", positions=(2, 0, 0.5))
```

### Step the renderer / simulation

```python
import isaacsim.core.experimental.utils.app as app_utils

app_utils.update_app(steps=120)     # Render frames
app_utils.play()                     # Start sim
app_utils.update_app(steps=100)
app_utils.stop()
```

### Run an Isaac Example from menu

```bash
# Open the example window
python scripts/isaacsim_send.py --file scripts/menu_click.py \
    --arg menu_path="Isaac Examples/Robots/Franka" --arg window_name="Franka"

# Click Load button
python scripts/isaacsim_send.py --file scripts/widget_action.py \
    --arg action=click --arg query="LOAD"

# Capture the result
python scripts/isaacsim_send.py --file scripts/viewport_screenshot.py \
    --arg output_path=/tmp/franka.png
```

### Create new stage and add objects via menus

```bash
python scripts/isaacsim_send.py --file scripts/menu_click.py --arg menu_path="File/New"
python scripts/isaacsim_send.py --file scripts/menu_click.py --arg menu_path="Create/Mesh/Cube"
python scripts/isaacsim_send.py --file scripts/viewport_screenshot.py --arg output_path=/tmp/cube.png
```

## Important Notes

### Lighting in headless mode

Headless rendering with no lights produces a black image. Always add a `DomeLight` with intensity 1000–5000.

### Renderer warm-up

After creating or loading a new stage, call `app_utils.update_app(steps=120)` before rendering. After minor changes, `steps=30` is usually sufficient.

### All features work in `--no-window` headless mode

Full-app screenshots (`capture_next_frame_swapchain`), menu clicks (`ui_test.menu_click`), widget finding, and viewport screenshots all work without a display. A `DISPLAY` is only needed if you want to visually observe the UI on screen.

### Connection errors

If the script reports connection refused:
1. Isaac Sim is running and shows `app ready`
2. The python_server extension is enabled (`--enable isaacsim.code_editor.python_server`)
3. Host and port match (default: `127.0.0.1:8226`)

## Key APIs Available Inside Isaac Sim

When writing code to send via inline or custom scripts, prefer the `isaacsim.core.experimental` APIs over raw Kit/omni calls. See `references/api-reference.md` for full details.

**Isaac Sim APIs (preferred):**
- **`isaacsim.core.experimental.utils.stage`** — `create_new_stage_async()`, `open_stage_async()`, `get_current_stage()`, `define_prim()`, `delete_prim()`
- **`isaacsim.core.experimental.utils.app`** — `update_app()`, `play()`, `stop()`, `is_playing()`, `enable_extension()`
- **`isaacsim.core.experimental.utils.prim`** — `get_prim_at_path()`, `find_matching_prim_paths()`, `get_prim_attribute_value()`
- **`isaacsim.core.experimental.objects`** — `Cube`, `Sphere`, `DomeLight`, `GroundPlane` and other scene objects
- **`isaacsim.test.utils.menu_utils`** — `menu_click_with_retry()`, `find_widget_with_retry()`
- **`isaacsim.test.utils.image_capture`** — `capture_rgb_data_async()`, `capture_viewport_annotator_data_async()`

**Kit APIs (use when no Isaac Sim equivalent exists):**
- **`omni.kit.ui_test`** — `find()`, `get_menubar()`, `menu_click()`, `emulate_mouse_move()`
- **`omni.kit.renderer.capture`** — `capture_next_frame_swapchain()` for full-app capture
- **`omni.kit.actions.core`** — `get_action_registry()` to execute registered actions directly
