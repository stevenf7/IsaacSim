```{csv-table}
**Extension**: {{ extension_version }},**Documentation Generated**: {sub-ref}`today`
```

# Overview

The `isaacsim.core.api` extension provides APIs for controlling simulation state and physics scenes within Isaac Sim. This extension serves as the primary interface for managing simulation execution, physics interactions, and USD object manipulation in robotics and AI simulation workflows.

## Functionality

The extension integrates physics simulation capabilities through omni.physics and omni.physx.tensors, enabling precise control over physical interactions and dynamics. It provides wrappers for USD objects that simplify working with Universal Scene Description assets in simulation contexts. The extension also includes utilities for managing both physics and visual materials, allowing users to define realistic material properties that affect simulation behavior and rendering.

Additionally, the extension incorporates computational tools through omni.pip.compute for advanced mathematical operations and omni.warp.core for high-performance parallel computing tasks commonly required in robotics simulations.