```{csv-table}
**Extension**: {{ extension_version }},**Documentation Generated**: {sub-ref}`today`
```

# Overview

The isaacsim.util.debug_draw extension provides persistent debug drawing helpers for visualizing points, lines, and splines in the Isaac Sim viewport. It includes both a Python API for programmatic drawing and OmniGraph nodes for node-based workflows.

## Functionality

- **Point drawing**: Render point clouds in the viewport with configurable colors and sizes
- **Line drawing**: Draw line segments between pairs of points for visualizing vectors, rays, and connections
- **Spline drawing**: Render smooth curves through control points

## OmniGraph Nodes

- **DebugDrawPointCloud**: Draws a set of 3D points in the viewport
- **DebugDrawRayCast**: Visualizes ray cast results as lines from origin to hit points
- **IsaacXPrimAxisVisualizer**: Draws coordinate axes on prims for orientation debugging
- **IsaacXPrimRadiusVisualizer**: Draws radius indicators on prims for spatial extent debugging
