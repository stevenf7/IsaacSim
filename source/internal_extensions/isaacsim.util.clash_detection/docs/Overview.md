# Overview

The isaacsim.util.clash_detection extension provides mesh-level collision detection for USD assets. It uses PhysX overlap queries to identify intersecting geometry between prims, supporting both hard clashes (actual overlaps) and clearance checks with configurable tolerances.

## Functionality

- **Single prim detection**: Check whether a specific prim clashes with other geometry in the scene
- **Batch detection**: Detect clashes across multiple prims in a prim view with progress tracking
- **Configurable tolerance**: Set distance thresholds to distinguish hard clashes from soft clearance violations
- **Scoped queries**: Limit clash detection to specific USD scope paths for targeted analysis
- **JSON export**: Export clash detection results with details including overlap counts, affected frames, and object paths
