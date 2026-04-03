# Overview

The ROS 2 Simulation Control extension bridges Isaac Sim with ROS 2 by implementing standard ROS 2 simulation control interfaces. It enables external ROS 2 nodes to control Isaac Sim's timeline, spawn entities, and manage simulation state through service-based communication.

## Functionality

### Timeline Control

The extension provides ROS 2 services to control Isaac Sim's simulation timeline:

- **Play/Pause/Stop**: Start, pause, or stop the simulation timeline
- **Step Simulation**: Advance the simulation by a specified number of frames
- **Reset Simulation**: Reset the simulation to its initial state

These services allow ROS 2 nodes to synchronize simulation execution with external processes or implement custom simulation workflows.

### Entity Management

The extension supports dynamic entity manipulation through ROS 2 services:

- **Spawn Entity**: Create new entities in the simulation by providing USD references or inline USD descriptions
- **Delete Entity**: Remove entities from the simulation by name
- **Set Entity State**: Modify entity poses and states during runtime

Entity operations enable procedural scene construction and runtime modifications from ROS 2 nodes, supporting use cases like automated testing or dynamic environment generation.

### Simulation State Queries

The extension provides services to query simulation information:

- **Get Entity State**: Retrieve current pose and state of entities
- **Get Model Properties**: Query properties of models in the simulation
- **Get World Properties**: Access simulation-wide properties and settings

These query services allow ROS 2 nodes to inspect the current simulation state and make informed decisions based on entity configurations.

## Integration

The extension integrates with `isaacsim.ros2.bridge` to establish ROS 2 communication channels, uses `isaacsim.core.experimental.prims` for USD prim operations, and `isaacsim.core.experimental.utils` for stage and prim utility functions. It translates between ROS 2 service messages and Isaac Sim's internal APIs, handling coordinate system conversions and data format transformations.

Service callbacks process incoming ROS 2 requests, execute the corresponding Isaac Sim operations, and return responses following the ROS 2 Simulation Interface standard. This allows Isaac Sim to participate in ROS 2-based simulation orchestration systems.
