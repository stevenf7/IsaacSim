# Changelog

## [0.1.0] - 2026-04-14
### Added
- C++ tensor backend implementing `omni.physics.tensors` interfaces for Newton physics, with CPU and GPU (Warp/CUDA) implementations of `SimulationView`, `ArticulationView`, `RigidBodyView`, and `RigidContactView`. Supports three device configurations (CPU sim + CPU view, GPU sim + CPU view, GPU sim + GPU view) for articulation and rigid body state, force/torque application, and contact queries.
