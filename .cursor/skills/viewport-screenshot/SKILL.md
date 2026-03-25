---
name: viewport-screenshot
description: Capture screenshots of Isaac Sim viewports or render products for visual verification and LLM usage. Use when you need to see what the scene looks like, verify rendering output, capture RGB/depth/annotator images from cameras, or provide visual feedback during scene construction. Requires a running Isaac Sim instance with the python server — see the python-server-client skill.
---

# Viewport Screenshot Capture

Capture images from a running Isaac Sim instance for visual verification without a GUI. Requires the `isaacsim.test.utils` extension.

## Prerequisites

Isaac Sim must be running with the python server **and** test utils extensions enabled. See the `python-server-client` skill for how to launch and communicate with the sim. Add `--enable isaacsim.test.utils` when launching:

```bash
bash isaac-sim.sh --no-window --no-ros-env \
    --enable isaacsim.code_editor.python_server \
    --enable isaacsim.test.utils
```

Use `scripts/isaacsim_send.py` from the `python-server-client` skill to send code. All capture functions are async and require top-level `await`.

## Capture APIs

All capture functions are in `isaacsim.test.utils.image_capture`. Save utilities are in `isaacsim.test.utils.image_io`.

### 1. RGB with a temporary camera

Creates a temporary camera at the given position, captures one frame, and removes the camera.

```python
from isaacsim.test.utils.image_capture import capture_rgb_data_async
from isaacsim.test.utils.image_io import save_rgb_image

rgb_data = await capture_rgb_data_async(
    camera_position=(5, 5, 3),     # where the camera sits
    camera_look_at=(0, 0, 0.5),    # what it looks at
    resolution=(1280, 720)          # width x height
)
# rgb_data: numpy array, shape (720, 1280, 4), dtype uint8 (RGBA)

save_rgb_image(rgb_data, "/tmp/screenshots", "scene.png")
```

### 2. RGB from an existing camera prim

Uses a camera already in the stage. Does not remove it after capture.

```python
rgb_data = await capture_rgb_data_async(
    camera_prim_path="/World/MyCamera",
    resolution=(1920, 1080)
)
save_rgb_image(rgb_data, "/tmp/screenshots", "camera_view.png")
```

### 3. Active viewport capture

Captures from the active viewport's render product (uses whatever camera the viewport is looking through).

```python
from isaacsim.test.utils.image_capture import capture_viewport_annotator_data_async
import omni.kit.viewport.utility as viewport_utils

viewport_api = viewport_utils.get_active_viewport()
rgb_data = await capture_viewport_annotator_data_async(viewport_api, annotator_name="rgb")
save_rgb_image(rgb_data, "/tmp/screenshots", "viewport.png")
```

### 4. Depth capture

```python
from isaacsim.test.utils.image_capture import capture_depth_data_async
from isaacsim.test.utils.image_io import save_depth_image

depth_data = await capture_depth_data_async(
    depth_type="distance_to_camera",  # or "distance_to_image_plane"
    camera_position=(5, 5, 3),
    camera_look_at=(0, 0, 0.5),
    resolution=(1280, 720)
)
# depth_data: numpy array, shape (720, 1280, 1), dtype float32

# Normalized 8-bit grayscale visualization
save_depth_image(depth_data, "/tmp/screenshots", "depth_viz.png", normalize=True)

# Lossless float32 TIFF (metric depth values)
save_depth_image(depth_data, "/tmp/screenshots", "depth.tiff")
```

### 5. Any annotator (normals, segmentation, etc.)

```python
from isaacsim.test.utils.image_capture import capture_annotator_data_async

normals = await capture_annotator_data_async(
    "normals",
    camera_position=(5, 5, 3),
    camera_look_at=(0, 0, 0),
    resolution=(512, 512)
)
```

### 6. Capture from an existing render product

```python
import omni.replicator.core as rep

rp = rep.create.render_product("/World/MyCamera", (1920, 1080))
rgb_data = await capture_annotator_data_async("rgb", render_product=rp)
# NOTE: When passing render_product, the caller owns its lifecycle.
# The function will NOT destroy it.
```

## Complete Example: Scene → Screenshot → Verify

Full pattern for building a scene, rendering it, and capturing a screenshot:

```bash
# Step 1: Create the scene (see python-server-client skill for send script)
python .cursor/skills/python-server-client/scripts/isaacsim_send.py '
import isaacsim.core.experimental.utils.stage as stage_utils
import isaacsim.core.experimental.utils.app as app_utils
from isaacsim.core.experimental.objects import Cube, Sphere, DomeLight
from pxr import UsdLux

await stage_utils.create_new_stage_async(template="empty")
stage_utils.define_prim("/World", "Xform")

dome = DomeLight("/World/DomeLight")
stage = stage_utils.get_current_stage()
UsdLux.DomeLight(stage.GetPrimAtPath("/World/DomeLight")).GetIntensityAttr().Set(3000.0)

Cube("/World/RedCube", sizes=1.0, colors="red", positions=(0, 0, 0.5))
Sphere("/World/GreenSphere", radii=0.5, colors="green", positions=(2, 0, 0.5))

# CRITICAL: Render enough frames for RTX convergence
app_utils.update_app(steps=120)
'

# Step 2: Capture screenshot
python .cursor/skills/python-server-client/scripts/isaacsim_send.py '
from isaacsim.test.utils.image_capture import capture_rgb_data_async
from isaacsim.test.utils.image_io import save_rgb_image

rgb_data = await capture_rgb_data_async(
    camera_position=(5, 5, 3),
    camera_look_at=(0, 0, 0.5),
    resolution=(1280, 720)
)
save_rgb_image(rgb_data, "/tmp/isaacsim_screenshots", "scene.png")
'

# Step 3: View the image (from the agent/LLM side)
# Use your file-reading tool to view /tmp/isaacsim_screenshots/scene.png
```

## Critical Notes

### Renderer warm-up is mandatory

The first capture after creating or loading a stage needs **100+ render frames** for the RTX path tracer to converge. Without this, you get a black image.

```python
# After creating/loading a scene — always do this BEFORE capturing
app_utils.update_app(steps=120)
```

For subsequent captures after minor scene modifications, fewer frames suffice:

```python
# After moving a prim or changing a material
app_utils.update_app(steps=30)
```

### Lighting matters

Headless rendering with no lights produces a black image. Always add a `DomeLight` with intensity 1000–5000.

### File format guidance

| Format | Use case | Function |
|--------|----------|----------|
| PNG (RGBA) | RGB screenshots for LLM viewing | `save_rgb_image(data, dir, "name.png")` |
| PNG (grayscale) | Depth visualization | `save_depth_image(data, dir, "name.png", normalize=True)` |
| TIFF (float32) | Metric depth for computation | `save_depth_image(data, dir, "name.tiff")` |

### Temporary vs persistent cameras

- `capture_rgb_data_async(camera_position=..., camera_look_at=...)` — **temporary camera**, cleaned up after capture
- `capture_rgb_data_async(camera_prim_path="/World/MyCamera")` — **existing camera**, left in the stage
- `capture_viewport_annotator_data_async(viewport_api)` — **active viewport's** current camera

### Output directory

The save functions auto-create the output directory. Use any writable path.
