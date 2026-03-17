```{csv-table}
**Extension**: {{ extension_version }},**Documentation Generated**: {sub-ref}`today`
```

# Overview

The isaacsim.core.rendering_manager extension provides centralized control over rendering operations and viewport management within Isaac Sim. This extension offers programmatic APIs for executing rendering steps, managing rendering timing, and controlling viewport configurations including camera settings and window management.

## Key Components

### {class}`RenderingManager <isaacsim.core.rendering_manager.RenderingManager>`

**{class}`RenderingManager <isaacsim.core.rendering_manager.RenderingManager>` provides core rendering control and timing management.** The class handles synchronous and asynchronous rendering operations, allowing applications to trigger frame updates without advancing simulation or physics systems.

The rendering timing system allows precise control over frame rates through configurable delta time values. Applications can set custom rendering intervals to match specific performance requirements or synchronize with external systems.

```python
from isaacsim.core.rendering_manager import RenderingManager

# Set 120 Hz rendering rate
RenderingManager.set_dt(1 / 120.0)

# Trigger a single render frame
RenderingManager.render()
```

### Event System

**The callback registration system enables applications to subscribe to rendering events.** The {class}`RenderingEvent <isaacsim.core.rendering_manager.RenderingEvent>` enum defines available event types, with NEW_FRAME being the primary event for frame-based operations. Callbacks can be registered with specific execution order to ensure proper sequencing of dependent operations.

```python
from isaacsim.core.rendering_manager import RenderingEvent, RenderingManager

def frame_callback(event, *args, **kwargs):
    print(f"Frame rendered: {event}")

# Register callback for new frame events
callback_id = RenderingManager.register_callback(
    RenderingEvent.NEW_FRAME, 
    callback=frame_callback,
    order=10
)
```

### {class}`ViewportManager <isaacsim.core.rendering_manager.ViewportManager>`

**{class}`ViewportManager <isaacsim.core.rendering_manager.ViewportManager>` provides comprehensive viewport and camera control capabilities.** The manager handles viewport window creation, camera assignment, resolution management, and viewport synchronization operations.

Camera management supports both built-in Omniverse Kit cameras (Perspective, Top, Front, Right views) and custom USD Camera prims. The system maintains proper camera-to-viewport associations and handles camera view transformations.

```python
from isaacsim.core.rendering_manager import ViewportManager

# Create a custom viewport window
window = ViewportManager.create_viewport_window(
    title="Custom View",
    resolution=(1920, 1080),
    camera="/OmniverseKit_Top"
)

# Set camera view to look at specific target
ViewportManager.set_camera_view(
    camera=ViewportManager.get_camera(),
    eye=[5.0, 5.0, 5.0],
    target=[0.0, 0.0, 0.0]
)
```

### Viewport Synchronization

**The viewport waiting system ensures proper frame readiness before operations.** Both synchronous and asynchronous waiting methods allow applications to coordinate with viewport rendering cycles, preventing race conditions when capturing frames or performing viewport-dependent operations.

```python
# Wait for viewport to be ready for capture
ready, frames_waited = ViewportManager.wait_for_viewport(max_frames=60)
if ready:
    # Perform viewport-dependent operations
    pass
```

## Functionality

### Resolution and Display Control

{class}`ViewportManager <isaacsim.core.rendering_manager.ViewportManager>` handles dynamic resolution changes for both individual viewports and render products. The system supports programmatic resolution updates while maintaining proper aspect ratios and render target configurations.

### Multi-Viewport Management

The extension supports creating and managing multiple viewport windows simultaneously. Viewport windows can be filtered, destroyed, and configured independently, enabling complex multi-view applications and debugging scenarios.

### USD Integration

Deep integration with USD render products and camera prims enables seamless interaction with the USD stage pipeline. The system automatically handles USD prim relationships and maintains proper render product configurations.
