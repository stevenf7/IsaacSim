# Overview

The isaacsim.asset.gen.conveyor extension provides utilities for authoring and simulating conveyor belts in Isaac Sim. It includes a C++ plugin for runtime conveyor physics, an OmniGraph node for controlling conveyor behavior during simulation, and Python commands for programmatic conveyor creation.

## Key Components

### Python Command — CreateConveyorBelt

The `CreateConveyorBelt` command creates an Action Graph containing the IsaacConveyor node and wires it to a target rigid body prim. If the selected prim does not already have a rigid body API, the command applies one.

```python
result, prim = omni.kit.commands.execute(
    "CreateConveyorBelt",
    prim_name="ConveyorActionGraph",
    conveyor_prim="/World/ConveyorBeltRigidBody",
)
```

### C++ Plugin

A native Carbonite plugin (`IOmniIsaacConveyor`) provides the runtime interface used by the OmniGraph node for conveyor physics computations.

## Usage

To add a conveyor belt interactively, use **Create > Isaac Sim > Warehouse Items > Conveyor**. For track-based conveyor systems built from Digital Twin Assets, see the companion extension `isaacsim.asset.gen.conveyor.ui` and its **Tools > Conveyor Track Builder** window.
